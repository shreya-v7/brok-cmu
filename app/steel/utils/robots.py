import requests
from urllib.parse import urlparse, urlunparse
from time import time

def robots_allowed(url: str, user_agent: str = "steel-student-bot/1.0") -> bool:
    parts = urlparse(url)
    robots_url = urlunparse((parts.scheme, parts.netloc, "/robots.txt", "", "", ""))
    try:
        r = requests.get(robots_url, timeout=10, headers={"User-Agent": user_agent})
        if r.status_code != 200:
            return True
        from urllib import robotparser
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(r.text.splitlines())
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True
