import requests, re, statistics
from bs4 import BeautifulSoup
from ..utils.robots import robots_allowed

def fetch_rent_median(area: str="pittsburgh", query: str="1br") -> float | None:
    url = f"https://{area}.craigslist.org/search/apa?availabilityMode=0&query={query}"
    if not robots_allowed(url):
        return None
    r = requests.get(url, timeout=20, headers={"User-Agent": "steel-student-bot/1.0"})
    if r.status_code != 200: return None
    soup = BeautifulSoup(r.text, "html.parser")
    prices = []
    for el in soup.select(".result-price"):
        m = re.search(r"(\d[\d,]*)", el.text)
        if m:
            prices.append(float(m.group(1).replace(",","")))
    if prices:
        return float(statistics.median(prices))
    return None
