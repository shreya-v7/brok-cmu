import os
from dotenv import load_dotenv
load_dotenv()

# Optional — put your Gemini key in .env as GEMINI_API_KEY=xxxx
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Scraper constants
USER_AGENT = "Mozilla/5.0 (compatible; Brok-CMU/2.0)"
REQUESTS_TIMEOUT = 12

# External sources
NUMBEO_PITTSBURGH = "https://www.numbeo.com/cost-of-living/in/Pittsburgh"
STUDENTAID_SITE = "https://studentaid.gov/"
CREDIBLE_STUDENT_LOANS = "https://www.credible.com/student-loans/"
SOFI_STUDENT_LOANS = "https://www.sofi.com/student-loans/"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q=Carnegie+Mellon+University+OR+CMU+finance+OR+tuition+OR+scholarship+OR+Pittsburgh&hl=en-US&gl=US&ceid=US:en"
