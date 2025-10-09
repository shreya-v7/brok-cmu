#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CMU Tuition & Fees Scraper (Undergrad + Graduate, program-wise, no hardcoding)

Outputs: cmu_tuition_clean.xlsx
Sheets:
  - Undergraduate: complete tuition + fees across undergraduate subtree
  - Graduate: program-wise tuition + fees across graduate subtree

Design:
- Discover links dynamically (no hardcoded college/program lists)
- Parse both tables and inline fee lines
- Normalize $ amounts → floats; detect unit (per_year/semester/unit/credit/course/term/unknown)
- Robust against layout noise: skips bad tables, 404s, and archives (configurable)
"""

import re
import time
from io import StringIO
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# =======================
# CONFIG
# =======================
ROOT = "https://www.cmu.edu"
UG_START = "https://www.cmu.edu/sfs/tuition/undergraduate/index.html"
GR_START = "https://www.cmu.edu/sfs/tuition/graduate/index.html"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; brok-cmu/2.0)"}
TIMEOUT = 15
SLEEP = 0.25

OUT_XLSX = "../data/cmu_tuition_clean.xlsx"

# Crawl settings
INCLUDE_ARCHIVES = False          # set True to include older archived pages
MAX_PAGES = 500                   # safety cap

# =======================
# REGEX / HELPERS
# =======================
MONEY_RX = re.compile(r"\$[\s]*[\d,]+(?:\.\d{2})?")
UNIT_RX = re.compile(r"per\s*(year|semester|unit|credit|course|term)", re.I)
ACADEMIC_TOKEN_RX = re.compile(r"\b(\d{2})(\d{2})\b")  # e.g., 2526 → AY 2025–26

def safe_sleep():
    time.sleep(SLEEP)

def fetch_soup(url):
    try:
        safe_sleep()
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 404:
            print(f" ⚠️  404: {url}")
            return None
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f" ⚠️  Fetch error {url}: {e}")
        return None

def is_internal(href: str) -> bool:
    if not href:
        return False
    p = urlparse(href)
    if p.scheme and p.netloc and p.netloc != "www.cmu.edu":
        return False
    return True

def normalize_url(base, href):
    return urljoin(base, href).split("#")[0]

def extract_money(text: str):
    m = MONEY_RX.search(text or "")
    if not m:
        return None, None
    raw = m.group(0)
    try:
        amt = float(raw.replace("$", "").replace(",", "").strip())
    except Exception:
        amt = None
    return raw, amt

def detect_unit(text: str):
    m = UNIT_RX.search(text or "")
    if not m:
        return "unknown"
    unit = m.group(1).lower()
    return f"per_{unit}"

def text_clean(s):
    return re.sub(r"\s+", " ", (s or "").strip())

def looks_like_fee_label(s):
    s = (s or "").lower()
    return any(k in s for k in ["tuition", "fee", "fees", "health", "activity", "technology", "program"])

def detect_academic_year(url_or_text: str) -> str:
    """
    Try to infer academic year, e.g., token '2526' → '2025-26'
    """
    for token in ACADEMIC_TOKEN_RX.findall(url_or_text or ""):
        a, b = token
        # sanity: expect consecutive years (25, 26), rough heuristic
        try:
            a_i, b_i = int(a), int(b)
        except:
            continue
        if 0 <= a_i <= 99 and 0 <= b_i <= 99:
            return f"20{a}-{b}"
    return ""

def page_title_or_h1(soup, fallback):
    for tag in ["h1", "h2", "title"]:
        node = soup.find(tag)
        if node and node.get_text(strip=True):
            return text_clean(node.get_text(strip=True))
    return fallback

# =======================
# TABLE & TEXT EXTRACTORS
# =======================
def parse_tables_generic(soup, context, url):
    """
    Parse every <table>, seeking rows that contain a dollar amount.
    Builds rows with label, amount, unit, and note.
    """
    rows = []
    tables = soup.find_all("table")
    for tbl in tables:
        try:
            dfs = pd.read_html(StringIO(str(tbl)), flavor="bs4")
        except ValueError:
            continue
        except Exception as e:
            print(f"  ⚠️  Skipping bad table on {url}: {e}")
            continue

        for df in dfs:
            if df is None or df.empty:
                continue
            df = df.fillna("")

            # Prefer 2-4 column tables with label/value semantics, but accept any
            for _, r in df.iterrows():
                parts = [text_clean(str(x)) for x in r.values if str(x).strip()]
                if not parts:
                    continue
                line = " | ".join(parts)
                raw, amt = extract_money(line)
                if amt is None:
                    continue

                # Heuristic for label: first non-money-ish cell with fee-ish words
                label = None
                for p in parts:
                    if MONEY_RX.search(p):
                        continue
                    if looks_like_fee_label(p):
                        label = p
                        break
                if not label:
                    # fallback: use the entire row as label
                    label = parts[0]

                unit = detect_unit(line)

                rows.append({
                    "level": context["level"],
                    "school": context["school"],
                    "program": context["program"],
                    "label": "Tuition" if "tuition" in line.lower() else "Fee",
                    "item": label,
                    "amount": amt,
                    "unit": unit,
                    "notes": line,
                    "academic_year": context["academic_year"] or detect_academic_year(url + " " + line),
                    "source_url": url
                })

    return rows

def parse_inline_fees(soup, context, url):
    """
    Parse <p>/<li>/<div> blocks for lines like "Technology Fee: $240 per semester".
    """
    rows = []
    for tag in soup.find_all(["p", "li", "div", "span"]):
        line = text_clean(tag.get_text(" ", strip=True))
        if not line or "$" not in line:
            continue
        raw, amt = extract_money(line)
        if amt is None:
            continue

        # Try to find item text before the dollar string
        item = None
        # split around the first money token
        parts = MONEY_RX.split(line, maxsplit=1)
        before = parts[0].strip() if parts else ""
        if looks_like_fee_label(before):
            item = before
        else:
            # fallback: short snippet as item
            item = before[:60] or "Amount"

        rows.append({
            "level": context["level"],
            "school": context["school"],
            "program": context["program"],
            "label": "Tuition" if "tuition" in line.lower() else "Fee",
            "item": item,
            "amount": amt,
            "unit": detect_unit(line),
            "notes": line,
            "academic_year": context["academic_year"] or detect_academic_year(url + " " + line),
            "source_url": url
        })
    return rows

# =======================
# UNDERGRAD CRAWLER
# =======================
def crawl_undergrad():
    """
    Crawl the entire undergraduate tuition subtree:
      /sfs/tuition/undergraduate/
    """
    start = UG_START
    visited, to_visit = set(), [start]
    rows = []

    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        soup = fetch_soup(url)
        if not soup:
            continue

        # Context for this page
        school = page_title_or_h1(soup, "Undergraduate Programs")
        context = {
            "level": "Undergraduate",
            "school": school,
            "program": None,
            "academic_year": detect_academic_year(url)
        }

        # Extract data
        rows += parse_tables_generic(soup, context, url)
        rows += parse_inline_fees(soup, context, url)

        # Discover more undergrad links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not is_internal(href):
                continue
            new = normalize_url(url, href)
            if "/sfs/tuition/undergraduate/" in new and new.endswith(".html"):
                if not INCLUDE_ARCHIVES and "archive" in new.lower():
                    continue
                if new not in visited and new not in to_visit:
                    to_visit.append(new)

    return rows

# =======================
# GRADUATE CRAWLER
# =======================
def crawl_graduate():
    """
    Crawl the entire graduate tuition subtree:
      /sfs/tuition/graduate/
    Follow every program page. Extract school name from h1/h2/title.
    Program name is inferred from strong headings (h2/h3/strong) near money lines.
    """
    start = GR_START
    visited, to_visit = set(), [start]
    rows = []

    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        soup = fetch_soup(url)
        if not soup:
            continue

        # Page-derived school / page name
        school = page_title_or_h1(soup, "Graduate Programs")

        # Pre-collect candidate program headings on the page
        candidate_programs = []
        for tag in soup.find_all(["h2", "h3", "strong", "b"]):
            txt = text_clean(tag.get_text(strip=True))
            if len(txt) < 3:
                continue
            # Keep diverse program-like signals
            if re.search(r"\b(MSCF|MISM|MSIT|MBA|MS|M\.S\.|Master|PhD|Doctor|Program|Track|Concentration)\b", txt, re.I):
                candidate_programs.append(txt)

        # Default context (program may be set row-by-row using local context)
        base_context = {
            "level": "Graduate",
            "school": school,
            "program": None,
            "academic_year": detect_academic_year(url)
        }

        # 1) Tables: For each table, attempt to find a nearby heading to annotate program
        for tbl in soup.find_all("table"):
            # Try to find heading siblings above the table for program context
            program_hint = None
            h = tbl.find_previous(lambda tag: tag.name in ["h2", "h3", "strong", "b"] and text_clean(tag.get_text(strip=True)))
            if h:
                t = text_clean(h.get_text(strip=True))
                if re.search(r"\b(MSCF|MISM|MSIT|MBA|MS|M\.S\.|Master|PhD|Doctor|Program|Track)\b", t, re.I):
                    program_hint = t

            context = dict(base_context)
            context["program"] = program_hint

            rows += parse_tables_generic(soup=BeautifulSoup(str(tbl), "html.parser"),
                                         context=context, url=url)

        # 2) Inline fees: we also try to anchor program by last seen heading
        last_program = None
        for tag in soup.find_all(["h2", "h3", "strong", "b", "p", "li", "div"]):
            if tag.name in ["h2", "h3", "strong", "b"]:
                t = text_clean(tag.get_text(strip=True))
                if re.search(r"\b(MSCF|MISM|MSIT|MBA|MS|M\.S\.|Master|PhD|Doctor|Program|Track)\b", t, re.I):
                    last_program = t
                continue

            # paragraphs/lists/divs with money lines
            t = text_clean(tag.get_text(" ", strip=True))
            if "$" not in t:
                continue
            raw, amt = extract_money(t)
            if amt is None:
                continue

            context = dict(base_context)
            context["program"] = last_program

            rows.append({
                "level": context["level"],
                "school": context["school"],
                "program": context["program"],
                "label": "Tuition" if "tuition" in t.lower() else "Fee",
                "item": (t.split(raw)[0].strip() or "Amount"),
                "amount": amt,
                "unit": detect_unit(t),
                "notes": t,
                "academic_year": context["academic_year"] or detect_academic_year(url + " " + t),
                "source_url": url
            })

        # 3) Discover more graduate links (program pages)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not is_internal(href):
                continue
            new = normalize_url(url, href)
            if "/sfs/tuition/graduate/" in new and new.endswith(".html"):
                if not INCLUDE_ARCHIVES and "archive" in new.lower():
                    continue
                if new not in visited and new not in to_visit:
                    to_visit.append(new)

    return rows

# =======================
# MAIN
# =======================
def main():
    print("Scraping Undergraduate…")
    ug_rows = crawl_undergrad()
    print(f" UG pages captured: rows={len(ug_rows)}")

    print("Scraping Graduate…")
    gr_rows = crawl_graduate()
    print(f" GR pages captured: rows={len(gr_rows)}")

    # Build DataFrames, normalize, and save
    ug_df = pd.DataFrame(ug_rows, columns=[
        "level", "school", "program", "label", "item", "amount",
        "unit", "notes", "academic_year", "source_url"
    ])
    gr_df = pd.DataFrame(gr_rows, columns=[
        "level", "school", "program", "label", "item", "amount",
        "unit", "notes", "academic_year", "source_url"
    ])

    # Coerce and tidy
    for df in (ug_df, gr_df):
        if "amount" in df.columns:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        # Clean duplicates
        df.drop_duplicates(subset=["level","school","program","label","item","amount","unit","source_url"], inplace=True)
        # Sort for readability
        df.sort_values(by=["level","school","program","label","item"], inplace=True, na_position="last")

    # Save Excel
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xw:
        ug_df.to_excel(xw, sheet_name="Undergraduate", index=False)
        gr_df.to_excel(xw, sheet_name="Graduate", index=False)

    print(f"✅ Saved {OUT_XLSX}")
    print("   Undergraduate rows:", len(ug_df))
    print("   Graduate rows     :", len(gr_df))


if __name__ == "__main__":
    main()
