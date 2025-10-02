import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from io import StringIO
import re
import time

ROOT = "https://www.cmu.edu"
START = "https://www.cmu.edu/sfs/tuition/index.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CMUTuitionScraper/1.0)"}


def is_internal(href):
    if not href:
        return False
    parsed = urlparse(href)
    if parsed.scheme and parsed.netloc and parsed.netloc != "www.cmu.edu":
        return False
    return True


def normalize_url(base, href):
    return urljoin(base, href).split("#")[0]


def detect_category(soup, url):
    txt = (soup.get_text(" ") or "").lower()
    if "undergraduate" in txt:
        return "Undergraduate"
    if "graduate" in txt or "phd" in txt or "doctoral" in txt:
        return "Graduate"
    if "fee" in txt:
        return "Fee/University Fees"
    if "tuition" in txt:
        return "Tuition"
    return "Other"


def detect_program(soup, url):
    if soup.find("h1"):
        return soup.find("h1").get_text(strip=True)
    if soup.title:
        return soup.title.string.strip()
    return url.split("/")[-1]


def parse_table(tbl):
    """Convert one <table> into DataFrame if possible."""
    try:
        dfs = pd.read_html(StringIO(str(tbl)), flavor="bs4")
        if dfs:
            return dfs[0]
    except ValueError:
        return None
    return None


def extract_key_values(soup):
    """Extract lines like 'Technology Fee: $240' outside of tables."""
    data = {}
    dollar = r"\$[0-9,\.\/\s]+"
    pattern = re.compile(r"([A-Za-z &\-\(\)]+?)[:\s–—]+(" + dollar + r")", re.IGNORECASE)
    for tag in soup.find_all(["p", "li", "div", "span"]):
        text = tag.get_text(" ", strip=True)
        for m in pattern.finditer(text):
            key = m.group(1).strip()
            val = m.group(2).strip()
            data[key] = val
    return data


def process_page(url, visited, results):
    if url in visited:
        return
    visited.add(url)
    print("Scraping:", url)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("  → Error:", e)
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    cat = detect_category(soup, url)
    prog = detect_program(soup, url)

    # Parse tables
    for idx, tbl in enumerate(soup.find_all("table")):
        df = parse_table(tbl)
        if df is not None and not df.empty:
            df["__Category"] = cat
            df["__Program"] = prog
            df["__SourceURL"] = url
            df["__TableIndex"] = idx
            results.append((prog, df))

    # Parse key-value fees
    kv = extract_key_values(soup)
    if kv:
        df2 = pd.DataFrame([kv])
        df2["__Category"] = cat
        df2["__Program"] = prog
        df2["__SourceURL"] = url
        df2["__TableIndex"] = -1
        results.append((prog, df2))

    # Recurse
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if is_internal(href):
            new = normalize_url(url, href)
            if "/sfs/tuition/" in new:
                process_page(new, visited, results)
                time.sleep(0.2)


def main():
    visited = set()
    results = []
    process_page(START, visited, results)

    print("Visited", len(visited), "pages")
    print("Extracted", len(results), "dataframes")

    # Save to Excel
    with pd.ExcelWriter("cmu_all_tuition_info.xlsx", engine="openpyxl") as writer:
        for i, (prog, df) in enumerate(results):
            sheet = re.sub(r"[^A-Za-z0-9]+", "_", prog)[:25] or f"Sheet{i}"
            if sheet in writer.sheets:
                sheet = f"{sheet}_{i}"
            df.to_excel(writer, sheet_name=sheet, index=False)

    print("✅ Saved cmu_all_tuition_info.xlsx")


if __name__ == "__main__":
    main()
