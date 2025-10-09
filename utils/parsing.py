'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        parsing.py
Purpose:     Provides text parsing utilities for extracting monetary and
             percentage values from raw HTML or text content using regex.
             Also includes helper functions for shortening text snippets
             for clean display in the Streamlit interface.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''

import re
_money = re.compile(r"\$[\s]*[\d,]+(?:\.\d{2})?")
_pct   = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%")

def find_money(text: str): return _money.findall(text or "")
def find_pct(text: str):   return _pct.findall(text or "")

def short(text, n=200):
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"
