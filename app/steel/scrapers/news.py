from ..utils.rss import fetch_rss_titles

DEFAULT_FEEDS = [
    "https://news.google.com/rss/search?q=Pittsburgh+rents&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Pittsburgh+grocery+prices&hl=en-US&gl=US&ceid=US:en"
]

def get_headlines(limit_per_feed: int = 3):
    out = []
    for feed in DEFAULT_FEEDS:
        out.extend(fetch_rss_titles(feed, limit=limit_per_feed))
    return out[:2*limit_per_feed]
