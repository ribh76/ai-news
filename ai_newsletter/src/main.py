import sys
import os
from datetime import date
from dotenv import load_dotenv
from config import ENV_PATH

load_dotenv(ENV_PATH)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
import news_scraper, summarizer, data_manager, notification_manager
from config import DEFAULT_SUBJECT

def run():
    print("\n" + "═" * 52)
    print("  AI NEWSLETTER — starting pipeline")
    print("═" * 52 + "\n")
    print("── Step 1/7: Scraping articles ──")
    articles = news_scraper.fetch_articles()
 
    if not articles:
        print("\n[main] No articles scraped — aborting pipeline.")
        return
    
    print("\n── Step 2/7: Saving to articles.json ──")
    news_scraper.save_to_json(articles)

    print("\n── Step 3/7: Summarizing articles ──")
    articles = summarizer.summarize_batch(articles)

    print("\n── Step 4/7: Saving articles to Sheety ──")
    data_manager.save_articles(articles)
    
    print("\n── Step 5/7: Fetching active subscribers ──")
    users = data_manager.get_active_users()
 
    if not users:
        print("[main] No active subscribers — skipping send.")
        _log_empty_digest(articles)
        return
    
    print("\n── Step 6/7: Logging digest to Sheety ──")
    today   = str(date.today())
    subject = DEFAULT_SUBJECT
 
    digest = {
        "date":          today,
        "subject":       subject,
        "articles":      articles,
        "article_count": len(articles),
    }
 
    data_manager.create_digest(
        date          = today,
        subject       = subject,
        article_count = len(articles),
    )

    print("\n── Step 7/7: Sending newsletter ──")
    result = notification_manager.send_bulk(users, digest)

    print("\n" + "═" * 52)
    print(f"  Pipeline complete")
    print(f"  Articles:   {len(articles)}")
    print(f"  Recipients: {len(users)}")
    print(f"  Sent:       {result['sent']}")
    print(f"  Failed:     {result['failed']}")
    if result["failed_emails"]:
        print(f"  Failed addresses:")
        for addr in result["failed_emails"]:
            print(f"    - {addr}")
    print("═" * 52 + "\n")


def _log_empty_digest(articles: list) -> None:
    try:
        data_manager.create_digest(
            date          = str(date.today()),
            subject       = DEFAULT_SUBJECT,
            article_count = len(articles),
        )
    except Exception as e:
        print(f"[main] Could not log empty digest: {e}")

if __name__ == "__main__":
    run()
 
