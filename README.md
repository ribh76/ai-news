AI News Digest: 
- A Python based automation pipeline that scrapes top AI and tech news sources, summarizes articles, and delivers a consice email newsletter

Problem: 
- Staying up to date on the latest AI news and technologies requires reading dozens of articles daily. This project automates that process by aggregating and summarizing the most relevant content in a concise and detialed manner.

Features: 
- Scraptes articles from the following tech sources: Hack News, TechCrunch, The verge, Wired, Ars Technica.
- Extractsthe full article text and generates summaries using an external API
- Formats content into an email newsletter
- sends notifcations via SMTP
- Modular pipeline design

Architecture: 
News Sources
→ Scraper
→ Article Extraction
→ Summarizer
→ JSON Storage
→ Email Formatter
→ Email Delivery

Tech Stack
	•	Python
	•	BeautifulSoup (web scraping)
	•	Requests
	•	SMTP (email delivery)
	•	JSON (data storage)
	•	Environment variables with .env

SETUP: 
1. Clone this repo:
git clone https://github.com/ribh76/ai-news-digest.git
cd ai-news-digest

2. Install dependencies:
pip install -r requirements.txt

3. Create an .env file
SMTP_EMAIL=your_email
SMTP_PASSWORD=your_password
SUMMARY_API_KEY=your_api_key

4. Run the pipeline
python src/main.py
