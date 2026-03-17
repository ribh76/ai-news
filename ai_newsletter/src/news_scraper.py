from __future__ import annotations

import json
import os
import time
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
 
import requests

from config import NEWS_SOURCES, ARTICLES_JSON_PATH, MAX_ARTICLES_TOTAL, REQUEST_TIMEOUT, REQUEST_HEADERS

try:
    from bs4 import BeautifulSoup  # type: ignore[import-not-found]
except Exception:
    BeautifulSoup = None  # type: ignore[assignment]


def _fetch_html(url: str) -> str | None:
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[news_scraper] ⚠ Request failed for {url}: {e}")
        return None

def _get_soup(html: str):
    if BeautifulSoup is None:
        return None
    try:
        # Use the stdlib parser for portability (no external lxml dependency).
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"[news_scraper] ⚠ BeautifulSoup parse failed: {e}")
        return None

def _is_external_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme) and "ycombinator.com" not in parsed.netloc

class _LinkHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = ""
        for k, v in attrs:
            if k == "href" and v:
                href = v.strip()
                break
        if href:
            self.hrefs.append(href)

class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._capture_p = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "p":
            self._capture_p = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if tag == "p":
            self._capture_p = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if not self._capture_p:
            return
        s = (data or "").strip()
        if s:
            self._buf.append(s)

    def text(self) -> str:
        return " ".join(self._buf)

def _get_article_links(source: dict) -> list[str]:
    listing_url = source["URL"]
    selector    = source["headline_selector"]
    base_url    = source["base_url"]
    max_count   = source.get("max_articles", 3)
 
    html = _fetch_html(listing_url)
    if not html:
        return []

    soup = _get_soup(html)
 
    # Try each comma-separated selector in order (for sources with fallback selectors)
    hrefs: list[str] = []
    if soup is not None:
        links = []
        for sel in [s.strip() for s in selector.split(",")]:
            try:
                tags = soup.select(sel)
            except Exception:
                tags = []
            if tags:
                links = tags
                break
        for tag in links[: max_count * 3]:
            href = tag.get("href", "") if tag else ""
            if href:
                hrefs.append(href)
    else:
        # Fallback: no bs4 available; grab all anchors and apply URL heuristics.
        p = _LinkHTMLParser()
        try:
            p.feed(html)
        except Exception:
            return []
        hrefs = p.hrefs
 
    if not hrefs:
        print(f"[news_scraper] ⚠ No links found for {source['source']}")
        return []
 
    urls = []
    for href in hrefs[: max_count * 8]:   # grab extras to account for dupes/skips
        if not href:
            continue
 
        # Build absolute URL
        if href.startswith("http"):
            absolute = href
        else:
            absolute = urljoin(base_url, href)
 
        # Hacker News: only follow external article links, not HN comment pages
        if source["source"] == "Hacker News":
            if not _is_external_url(absolute):
                continue
        else:
            # Non-HN: prefer on-domain links.
            if base_url and urlparse(absolute).netloc and urlparse(base_url).netloc:
                if urlparse(absolute).netloc != urlparse(base_url).netloc:
                    continue
 
        if absolute not in urls:
            urls.append(absolute)
 
        if len(urls) >= max_count:
            break
 
    print(f"[news_scraper] {source['source']} → found {len(urls)} article link(s)")
    return urls

def _scrape_article(url: str, source_name: str, body_selector: str) -> dict | None:
    html = _fetch_html(url)
    if not html:
        return None

    soup = _get_soup(html)
    title = ""
    if soup is not None:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        else:
            title = soup.title.get_text(strip=True) if soup.title else "No title"
    else:
        # Fallback: naive extraction.
        m = None
        try:
            m = __import__("re").search(r'<meta[^>]+property=["\\\']og:title["\\\'][^>]+content=["\\\']([^"\\\']+)', html, flags=__import__("re").I)
        except Exception:
            m = None
        if m:
            title = (m.group(1) or "").strip()
        else:
            title = "No title"

    raw_text = ""

    if soup is not None:
        for sel in [s.strip() for s in body_selector.split(",")]:
            try:
                body_tag = soup.select_one(sel)
            except Exception:
                body_tag = None
            if body_tag:
                raw_text = body_tag.get_text(separator=" ", strip=True)
                break

        if not raw_text:
            article_tag = soup.find("article")
            if article_tag:
                raw_text = article_tag.get_text(separator=" ", strip=True)

        if not raw_text:
            main_tag = soup.find("main")
            if main_tag:
                paragraphs = main_tag.find_all("p")
                raw_text = " ".join(p.get_text(strip=True) for p in paragraphs)

        if not raw_text:
            raw_text = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))
    else:
        p = _TextHTMLParser()
        try:
            p.feed(html)
        except Exception:
            raw_text = ""
        else:
            raw_text = p.text()

    raw_text = " ".join(raw_text.split())

    if not raw_text:
        print(f"[news_scraper] ⚠ No body text extracted from: {url}")
        return None
    
    return {
        "url":        url,
        "title":      title,
        "source":     source_name,
        "scraped_at": datetime.now().isoformat(),
        "raw_text":   raw_text[:8000],  
        "summary":    "",               
    }
   
def fetch_articles() -> list[dict]:
    all_articles = []
 
    for source in NEWS_SOURCES:
        print(f"\n[news_scraper] ── Scraping {source['source']} ──")
        try:
            links = _get_article_links(source)
        except Exception as e:
            print(f"[news_scraper] ⚠ Failed to extract links for {source['source']}: {e}")
            links = []
 
        for link in links:
            if len(all_articles) >= MAX_ARTICLES_TOTAL:
                print("[news_scraper] Max article limit reached.")
                break
 
            try:
                article = _scrape_article(
                    url           = link,
                    source_name   = source["source"],
                    body_selector = source["body_selector"],
                )
            except Exception as e:
                print(f"[news_scraper] ⚠ Failed to scrape {link}: {e}")
                article = None
 
            if article:
                all_articles.append(article)
                print(f"[news_scraper]   ✓ '{article['title'][:60]}...'")
 
            time.sleep(0.5)   # be polite to servers
 
        if len(all_articles) >= MAX_ARTICLES_TOTAL:
            break
 
    print(f"\n[news_scraper] Done — {len(all_articles)} article(s) scraped.")
    return all_articles

def save_to_json(articles: list[dict]) -> None:
    os.makedirs(os.path.dirname(ARTICLES_JSON_PATH), exist_ok=True)
 
    with open(ARTICLES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
 
    print(f"[news_scraper] Saved {len(articles)} article(s) → {ARTICLES_JSON_PATH}")

def parse_articles() -> list[dict]:
    if not os.path.exists(ARTICLES_JSON_PATH):
        raise FileNotFoundError(
            f"[news_scraper] {ARTICLES_JSON_PATH} not found. "
            "Run fetch_articles() and save_to_json() first."
        )
 
    with open(ARTICLES_JSON_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)
 
    print(f"[news_scraper] Loaded {len(articles)} article(s) from {ARTICLES_JSON_PATH}")
    return articles
