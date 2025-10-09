import re
_money = re.compile(r"\$[\s]*[\d,]+(?:\.\d{2})?")
_pct   = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%")

def find_money(text: str): return _money.findall(text or "")
def find_pct(text: str):   return _pct.findall(text or "")

def short(text, n=200):
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"
