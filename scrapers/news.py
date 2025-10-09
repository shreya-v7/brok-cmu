'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        news.py
Purpose:     Scrapes and parses the latest CMU, Pittsburgh, and education-related
             headlines from Google News RSS. Cleans and structures the data into
             a DataFrame for display and analysis within the Streamlit dashboard.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''


import requests
import pandas as pd
from bs4 import BeautifulSoup
from utils.caching import timed_lru_cache
from config import GOOGLE_NEWS_RSS, USER_AGENT, REQUESTS_TIMEOUT

HEADERS = {"User-Agent": USER_AGENT}

@timed_lru_cache(ttl=60*30, maxsize=8)
def fetch_news() -> pd.DataFrame:
    """
    Fetches latest CMU/Pittsburgh/education news from Google News RSS.
    Returns DataFrame with columns:
      ['title', 'link', 'pubDate', 'source', 'summary']
    """
    try:
        r = requests.get(GOOGLE_NEWS_RSS, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")

        items = []
        for it in soup.find_all("item")[:30]:  # grab top 30
            title = it.title.get_text(strip=True) if it.title else ""
            link = it.link.get_text(strip=True) if it.link else ""
            pubDate = it.pubDate.get_text(strip=True) if it.pubDate else ""
            source = it.source.get_text(strip=True) if it.source else "Google News"

            # Try to get summary/description
            desc = ""
            if it.description:
                desc = BeautifulSoup(it.description.get_text(), "html.parser").get_text(strip=True)
            elif it.find("content:encoded"):
                desc = BeautifulSoup(it.find("content:encoded").get_text(), "html.parser").get_text(strip=True)

            # Trim overly long text
            if len(desc) > 350:
                desc = desc[:347] + "..."

            items.append({
                "title": title,
                "link": link,
                "pubDate": pubDate,
                "source": source,
                "summary": desc
            })

        return pd.DataFrame(items, columns=["title", "link", "pubDate", "source", "summary"])

    except Exception as e:
        print(f"[fetch_news] Error: {e}")
        return pd.DataFrame(columns=["title", "link", "pubDate", "source", "summary"])
