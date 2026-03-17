import os

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(_SRC_DIR, os.pardir))
ENV_PATH = os.path.join(PROJECT_DIR, ".env")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
MODELS_DIR = os.path.join(PROJECT_DIR, "models")

NEWS_SOURCES = [
    {
        "source":             "TechCrunch",
        "URL":                "https://techcrunch.com/category/artificial-intelligence/",
        "headline_selector":  "a.post-block__title__link",   # <a> tag wrapping each headline
        "body_selector":      "div.article-content",         # article body container
        "max_articles":       3,
        "base_url":           "https://techcrunch.com",
        "js_required":        False,
    },
    {
        "source":             "Hacker News",
        "URL":                "https://news.ycombinator.com/",
        "headline_selector":  "tr.athing .titleline > a",    # first <a> inside .titleline
        "body_selector":      "article, div#article, div.post-body, div.article-body, div#content",
        "max_articles":       3,
        "base_url":           "https://news.ycombinator.com",
        "js_required":        False,   # HN itself is static; linked articles vary
    },
    {
        "source":             "The Verge",
        "URL":                "https://www.theverge.com/ai-artificial-intelligence",
        "headline_selector":  "h2.font-polysans a, h3.font-polysans a, a.group",  # try in order
        "body_selector":      "div.duet--article--article-body-component",
        "max_articles":       3,
        "base_url":           "https://www.theverge.com",
        "js_required":        True,    # JS-heavy; body may need fallback
    },
    {
        "source":             "Wired",
        "URL":                "https://www.wired.com/tag/artificial-intelligence/",
        "headline_selector":  "a.CondenserItem-hHEAtq, a[data-testid='SummaryItemHed'], h3 a",
        "body_selector":      "div.body__inner-container",
        "max_articles":       3,
        "base_url":           "https://www.wired.com",
        "js_required":        True,    # JS-heavy; body may need fallback
    },
    {
        "source":             "Ars Technica",
        "URL":                "https://arstechnica.com/ai/",
        "headline_selector":  "h2 a",                        # clean, reliable
        "body_selector":      "div.article-content, section.article-body",
        "max_articles":       3,
        "base_url":           "https://arstechnica.com",
        "js_required":        False,
    },
]

SHEETY_USER_EP      = "SHEETY_USER_EP"
SHEETY_ARTICLES_EP  = "SHEETY_ARTICLES_EP"
SHEETY_DIGESTS_EP   = "SHEETY_DIGESTS_EP"
SHEETY_SEND_LOG_EP  = "SHEETY_SEND_LOG_EP"

ARTICLES_JSON_PATH  = os.path.join(DATA_DIR, "articles.json")
EMAIL_TEMPLATE_PATH = os.path.join(MODELS_DIR, "email_format.html")

MAX_ARTICLES_TOTAL  = 15          # hard cap across all sources combined
REQUEST_TIMEOUT     = 12          # seconds per HTTP request
REQUEST_HEADERS     = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

SUMMARY_MAX_WORDS   = 120  
SUMMARY_FALLBACK_CHARS = 400 

DEFAULT_SUBJECT     = "Your Daily AI News Digest 🤖"
SEND_DELAY_SECONDS  = 0.5 
