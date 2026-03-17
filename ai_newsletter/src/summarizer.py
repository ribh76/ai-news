import os
import time
 
import requests
from dotenv import load_dotenv
 
from config import SUMMARY_MAX_WORDS, SUMMARY_FALLBACK_CHARS, ENV_PATH 
 
load_dotenv(ENV_PATH)
 
_API_KEY  = os.getenv("FREEAPI_KEY")
_API_URL  = "https://freeapitools.dev/api/summarize"   # update if endpoint differs
_DELAY    = 1.0



def summarize_article(text: str) -> str:
    if not _API_KEY:
        print("[summarizer] ⚠ FREEAPI_KEY not set — using fallback truncation.")
        return _fallback_summary(text)
    
    if not text or not text.strip():
        return "No article text available."
    
    payload = {
        "text":      text,
        "maxWords":  SUMMARY_MAX_WORDS,
    }
    
    headers = {
        "Authorization": f"Bearer {_API_KEY}",
        "Content-Type":  "application/json",
    }
    
    try:
        response = requests.post(_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
    
        data    = response.json()
        summary = (
            data.get("summary")
            or data.get("result")
            or data.get("data", {}).get("summary")
            or ""
        )
    
        if summary:
            return summary.strip()
        else:
            print("[summarizer] ⚠ API returned no summary field — using fallback.")
            return _fallback_summary(text)
    
    except requests.RequestException as e:
        print(f"[summarizer] ⚠ API request failed: {e} — using fallback.")
        return _fallback_summary(text)

def summarize_batch(articles: list[dict]) -> list[dict]:
    print(f"\n[summarizer] Summarising {len(articles)} article(s)...")
    
    for i, article in enumerate(articles, start=1):
        raw_text = article.get("raw_text", "")
        title    = article.get("title", "?")[:50]

        print(f"[summarizer] ({i}/{len(articles)}) {title}...")
        article["summary"] = summarize_article(raw_text)

        if i < len(articles):
            time.sleep(_DELAY)   # respect free-tier rate limits

    print(f"[summarizer] Done — {len(articles)} summaries ready.")
    return articles

def _fallback_summary(text: str) -> str:
    snippet = text.strip()[:SUMMARY_FALLBACK_CHARS]
    return snippet + ("..." if len(text) > SUMMARY_FALLBACK_CHARS else "")
