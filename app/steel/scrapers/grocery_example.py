import re
import requests
from bs4 import BeautifulSoup

from ..utils.robots import robots_allowed


def fetch_grocery_basket_monthly(url: str | None=None) -> float:
    # If a public weekly-ad URL is provided, estimate basket cost; else fallback.
    if url and robots_allowed(url):
        r = requests.get(url, timeout=20, headers={"User-Agent": "steel-student-bot/1.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            prices = []
            for el in soup.find_all(string=True):
                if "$" in el:
                    m = re.search(r"(\d+(?:\.\d{2})?)", el)
                    if m:
                        try: prices.append(float(m.group(1)))
                        except: pass
            if prices:
                avg = sum(prices)/len(prices)
                return round(avg*20, 2)  # ~20 items basket
    # fallback
    return 320.0
