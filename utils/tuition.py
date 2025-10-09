import pandas as pd
import re
import difflib

# ----------------------------
#  Tuition Utilities
# ----------------------------

def load_tuition_excel(path: str) -> pd.DataFrame:
    """
    Load your manually preprocessed tuition Excel (can contain multiple sheets).
    """
    try:
        xls = pd.ExcelFile(path)
        frames = []
        for sn in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sn)
            df["sheet"] = sn
            frames.append(df)
        df = pd.concat(frames, ignore_index=True)
    except Exception:
        df = pd.read_excel(path)

    # Normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["level","school","program","item","amount","unit","academic_year","source_url"]:
        if col not in df.columns:
            df[col] = None
    return df


def normalize_tuition_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize unit text into consistent categories."""
    if df.empty:
        return df

    def norm_unit(x):
        s = str(x).lower().strip()
        if any(k in s for k in ["per year", "annual", "yearly"]): return "per_year"
        if "semester" in s: return "per_semester"
        if "unit" in s: return "per_unit"
        if "credit" in s: return "per_credit"
        if "course" in s: return "per_course"
        if "term" in s: return "per_term"
        return "unknown"

    df["unit"] = df["unit"].apply(norm_unit)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def dedupe_tuition(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates."""
    if df.empty:
        return df
    keys = ["school","program","item","amount","unit","academic_year"]
    return df.drop_duplicates(subset=keys)


# ----------------------------
#  Matching logic
# ----------------------------

def normalize_school_name(name: str) -> str:
    """Clean and standardize school names for fuzzy matching."""
    if not isinstance(name, str):
        return ""
    s = name.lower().strip()
    s = re.sub(r"(college of|school of|faculty of)", "", s)
    s = s.replace("&", "and")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def filter_by_school_and_known_units(df: pd.DataFrame, school: str, department: str = None):
    """
    Match tuition data by student's school (robust fuzzy match, fallback to department).
    """
    if df.empty or not school:
        return pd.DataFrame(columns=df.columns)

    df["school_norm"] = df["school"].astype(str).apply(normalize_school_name)
    school_norm = normalize_school_name(school)

    # 1️⃣ Exact normalized match
    subset = df[df["school_norm"] == school_norm]

    # 2️⃣ Fuzzy fallback
    if subset.empty:
        all_schools = df["school_norm"].dropna().unique().tolist()
        best_match = difflib.get_close_matches(school_norm, all_schools, n=1, cutoff=0.4)
        if best_match:
            subset = df[df["school_norm"] == best_match[0]]

    # 3️⃣ Department fallback
    if subset.empty and department:
        subset = df[df["program"].astype(str).str.contains(department, case=False, na=False)]

    # 4️⃣ Filter by known units
    subset = subset[subset["unit"].isin([
        "per_year","per_semester","per_unit","per_credit","per_course","per_term"
    ])]

    subset = subset.drop_duplicates()
    subset = subset.sort_values(by=["unit","amount"], ascending=[True, False])

    return subset