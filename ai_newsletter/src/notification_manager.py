import os
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
 
import smtplib
from dotenv import load_dotenv
 
import data_manager
from config import DEFAULT_SUBJECT, SEND_DELAY_SECONDS, EMAIL_TEMPLATE_PATH, ENV_PATH
 
load_dotenv(ENV_PATH)
 
_SMTP_EMAIL    = os.getenv("SMTP_EMAIL")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
_SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))

def _load_template() -> str:


    if os.path.exists(EMAIL_TEMPLATE_PATH):
        with open(EMAIL_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    # Inline fallback so the newsletter can still send without the template file
    print(f"[notification_manager] ⚠ Template not found at {EMAIL_TEMPLATE_PATH} — using fallback.")
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body  { font-family: Arial, sans-serif; background:#f4f4f4; padding:20px; }
        .wrap { max-width:680px; margin:auto; background:#fff; border-radius:8px; overflow:hidden; }
        .hdr  { background:#1A56DB; color:#fff; padding:24px 32px; }
        .hdr h1 { margin:0; font-size:22px; }
        .hdr p  { margin:4px 0 0; font-size:14px; opacity:0.85; }
        .body { padding:24px 32px; }
        .article { border-left:4px solid #1A56DB; padding:12px 16px; margin-bottom:20px; background:#f8fafc; border-radius:0 6px 6px 0; }
        .article h3 { margin:0 0 6px; font-size:16px; }
        .article h3 a { color:#1A56DB; text-decoration:none; }
        .source { font-size:12px; color:#64748b; margin-bottom:8px; }
        .summary { font-size:14px; color:#334155; line-height:1.6; }
        .ftr { background:#1e293b; color:#94a3b8; font-size:12px; padding:16px 32px; text-align:center; }
    </style>
    </head>
    <body>
    <div class="wrap">
    <div class="hdr">
        <h1>AI News Digest</h1>
        <p>{{DATE}} — {{ARTICLE_COUNT}} articles</p>
    </div>
    <div class="body">
        {{ARTICLE_BLOCK}}
    </div>
    <div class="ftr">You're receiving this because you subscribed. To unsubscribe, reply to this email.</div>
    </div>
    </body>
    </html>
    """

def _build_article_block(articles: list[dict]) -> str:
    blocks = []
    for article in articles:
        title   = article.get("title",   "Untitled")
        source  = article.get("source",  "Unknown source")
        url     = article.get("url",     "#")
        summary = article.get("summary", "No summary available.")
 
        block = f"""
                    <div class="article">
                    <h3><a href="{url}">{title}</a></h3>
                    <div class="source">{source}</div>
                    <div class="summary">{summary}</div>
                    </div>
                """
        blocks.append(block)
 
    return "\n".join(blocks)

def build_email_body(digest: dict) -> str:
    template      = _load_template()
    article_block = _build_article_block(digest.get("articles", []))
 
    html = template
    html = html.replace("{{DATE}}",          digest.get("date",    ""))
    html = html.replace("{{SUBJECT}}",       digest.get("subject", DEFAULT_SUBJECT))
    html = html.replace("{{ARTICLE_COUNT}}", str(len(digest.get("articles", []))))
    html = html.replace("{{ARTICLE_BLOCK}}", article_block)
 
    return html

def send_email(to_address: str, subject: str, html_body: str) -> bool:
    if not _SMTP_EMAIL or not _SMTP_PASSWORD:
        print("[notification_manager] ✗ SMTP_EMAIL or SMTP_PASSWORD not set in .env")
        return False
 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = _SMTP_EMAIL
    msg["To"]      = to_address
 
    msg.attach(MIMEText(html_body, "html", "utf-8"))
 
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, context=context) as server:
            server.login(_SMTP_EMAIL, _SMTP_PASSWORD)
            server.sendmail(_SMTP_EMAIL, to_address, msg.as_string())
        return True
 
    except smtplib.SMTPAuthenticationError:
        print("[notification_manager] ✗ SMTP authentication failed — check SMTP_EMAIL and SMTP_PASSWORD.")
        return False
    except smtplib.SMTPException as e:
        print(f"[notification_manager] ✗ SMTP error sending to {to_address}: {e}")
        return False
    except Exception as e:
        print(f"[notification_manager] ✗ Unexpected error sending to {to_address}: {e}")
        return False

def send_bulk(users: list[dict], digest: dict) -> dict:
    if not users:
        print("[notification_manager] No active users — nothing to send.")
        return {"sent": 0, "failed": 0, "failed_emails": []}
 
    subject       = digest.get("subject", DEFAULT_SUBJECT)
    html_body     = build_email_body(digest)
    sent_count    = 0
    failed_count  = 0
    failed_emails = []
 
    print(f"\n[notification_manager] Sending to {len(users)} user(s)...")
 
    for user in users:
        email = user.get("email", "")
        if not email:
            continue
 
        success = send_email(email, subject, html_body)
 
        if success:
            sent_count += 1
            print(f"[notification_manager]   ✓ Sent → {email}")
            data_manager.log_send(email, "sent")
        else:
            failed_count += 1
            failed_emails.append(email)
            print(f"[notification_manager]   ✗ Failed → {email}")
            data_manager.log_send(email, "failed")
 
        time.sleep(SEND_DELAY_SECONDS)
 
    print(f"\n[notification_manager] Done — ✓ {sent_count} sent  ✗ {failed_count} failed")
    return {
        "sent":          sent_count,
        "failed":        failed_count,
        "failed_emails": failed_emails,
    }
