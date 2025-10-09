import requests, pandas as pd, re
from bs4 import BeautifulSoup
from utils.caching import timed_lru_cache
from config import USER_AGENT, REQUESTS_TIMEOUT, STUDENTAID_SITE, CREDIBLE_STUDENT_LOANS, SOFI_STUDENT_LOANS

HEADERS = {"User-Agent": USER_AGENT}
MONEY = re.compile(r"\$[\s]*[\d,]+(?:\.\d{2})?")
PCT   = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%")

def parse_page(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        money = ", ".join(MONEY.findall(text)[:3]) or "—"
        pcts  = ", ".join(PCT.findall(text)[:3]) or "—"
        title = soup.title.get_text(" ", strip=True) if soup.title else url
        # tiny snippet
        snippet = text[:240] + "…" if len(text) > 240 else text
        return {"title": title, "sample_money": money, "sample_pcts": pcts, "snippet": snippet, "link": url}
    except Exception:
        return {"title": "—", "sample_money": "—", "sample_pcts": "—", "snippet": "Fetch error", "link": url}

@timed_lru_cache(ttl=60*60, maxsize=8)
def fetch_loans_overview() -> pd.DataFrame:
    urls = [STUDENTAID_SITE, CREDIBLE_STUDENT_LOANS, SOFI_STUDENT_LOANS]
    rows = [parse_page(u) for u in urls]
    return pd.DataFrame(rows)
