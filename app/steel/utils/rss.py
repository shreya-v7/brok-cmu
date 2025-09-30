import requests
from xml.etree import ElementTree as ET

def fetch_rss_titles(url: str, limit: int = 5):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "steel-student-bot/1.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall('.//item')
        out = []
        for it in items[:limit]:
            title = (it.findtext('title') or '').strip()
            link = (it.findtext('link') or '').strip()
            out.append({"title": title, "link": link})
        return out
    except Exception:
        return []
