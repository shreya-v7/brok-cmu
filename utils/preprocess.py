'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        preprocess.py
Purpose:     Cleans and consolidates CMU tuition data from undergraduate and
             graduate sheets into a single unified dataset. Standardizes column
             formats, removes duplicates, and exports a processed Excel file
             for downstream analysis and visualization within the dashboard.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''


import pandas as pd

INPUT = "data/cmu_tuition_clean.xlsx"
OUTPUT = "data/cmu_tuition_clean_processed.xlsx"

dfu = pd.read_excel(INPUT, sheet_name="Undergraduate")
dfg = pd.read_excel(INPUT, sheet_name="Graduate")

def clean(df):
    df = df.copy()
    df["school"] = df["school"].fillna("").str.strip()
    df["program"] = df["program"].fillna("").str.strip()
    df["label"] = df["label"].fillna("Fee")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["level"] = df["level"].fillna("Unknown")
    df["academic_year"] = df["academic_year"].fillna("2025-26")
    df = df.drop_duplicates()
    return df

dfu, dfg = clean(dfu), clean(dfg)
dfu["is_graduate"] = False
dfg["is_graduate"] = True
final = pd.concat([dfu, dfg], ignore_index=True)

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as w:
    final.to_excel(w, sheet_name="All_Tuition", index=False)

print(f"✅ Saved clean file → {OUTPUT}, rows={len(final)}")
