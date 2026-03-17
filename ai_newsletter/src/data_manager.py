import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from config import ENV_PATH
 
load_dotenv(ENV_PATH)

API_KEY  = os.getenv("SHEETY_API_KEY")
_BASE_URL = os.getenv("SHEETY_BASE_URL", "").rstrip("/")
 
_AUTH = (API_KEY or "").strip()
if _AUTH and not _AUTH.lower().startswith("bearer "):
    _AUTH = f"Bearer {_AUTH}"

_HEADERS = {
    "Authorization": _AUTH,
    "Content-Type":  "application/json",
}

def _ep(name: str) -> str:
    """Build a full endpoint URL from the env-var endpoint name."""
    ep = os.getenv(name, "")
    if not ep:
        raise EnvironmentError(f"Missing env variable: {name}")
    return ep

def get_active_users() -> list[dict]:
    """
    Fetch all rows from the 'users' sheet and return only those
    where status == 'active'.
 
    Returns:
        list[dict]: Each dict has keys: email, status, created_at
    """
    url      = _ep("SHEETY_USER_EP")
    response = requests.get(url, headers=_HEADERS, timeout=10)
    response.raise_for_status()
 
    all_users = response.json().get("users", [])
    active    = [u for u in all_users if u.get("status", "").lower() == "active"]
 
    print(f"[data_manager] get_active_users → {len(active)} active user(s)")
    return active

def add_user(email: str) -> dict:
    email = email.strip().lower()

    url = _ep("SHEETY_USER_EP")
    response = requests.get(url, headers=_HEADERS, timeout=10)
    response.raise_for_status()
 
    existing_emails = [
        u.get("email", "").lower()
        for u in response.json().get("users", [])
    ]
    if email in existing_emails:
        raise ValueError(f"[data_manager] Email already subscribed: {email}")
    
    payload  = {"user": {"email": email, "status": "active", "createdAt": datetime.now().isoformat()}}
    response = requests.post(url, headers=_HEADERS, json=payload, timeout=10)
    response.raise_for_status()
 
    new_row = response.json().get("user", {})
    print(f"[data_manager] add_user → added {email}")
    return new_row

def save_articles(articles: list[dict]) -> None:
    url      = _ep("SHEETY_ARTICLES_EP")
    response = requests.get(url, headers=_HEADERS, timeout=10)
    response.raise_for_status()
 
    existing_urls = {
        row.get("url", "")
        for row in response.json().get("articles", [])
    }
 
    saved = 0
    for article in articles:
        if article.get("url") in existing_urls:
            print(f"[data_manager] Skipping duplicate: {article.get('url')}")
            continue
 
        payload = {
            "article": {
                "url":       article.get("url", ""),
                "title":     article.get("title", ""),
                "source":    article.get("source", ""),
                "scrapedAt": article.get("scraped_at", ""),
                "summary":   article.get("summary", ""),
            }
        }
        r = requests.post(url, headers=_HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        saved += 1
 
    print(f"[data_manager] save_articles → saved {saved} new article(s)")

def create_digest(date: str, subject: str, article_count: int) -> dict:
    url     = _ep("SHEETY_DIGESTS_EP")
    payload = {
        "digest": {
            "date":         date,
            "subject":      subject,
            "articleCount": article_count,
        }
    }
    response = requests.post(url, headers=_HEADERS, json=payload, timeout=10)
    response.raise_for_status()
 
    new_row = response.json().get("digest", {})
    print(f"[data_manager] create_digest → logged digest for {date} ({article_count} articles)")
    return new_row

def log_send(email: str, status: str) -> None:
    url     = _ep("SHEETY_SEND_LOG_EP")
    payload = {
        "sendLog": {
            "date":   datetime.now().isoformat(),
            "email":  email,
            "status": status,
        }
    }
    response = requests.post(url, headers=_HEADERS, json=payload, timeout=10)
    response.raise_for_status()
 
    print(f"[data_manager] log_send → {email} → {status}")
