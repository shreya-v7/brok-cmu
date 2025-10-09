import requests
import pandas as pd
from bs4 import BeautifulSoup
from utils.caching import timed_lru_cache
from config import USER_AGENT, REQUESTS_TIMEOUT, NUMBEO_PITTSBURGH

HEADERS = {"User-Agent": USER_AGENT}

@timed_lru_cache(ttl=60 * 60, maxsize=4)
def fetch_pittsburgh_cost_of_living() -> pd.DataFrame:
    """
    Returns DataFrame with columns ['label','value'] (robust to minor layout changes).
    """
    try:
        r = requests.get(NUMBEO_PITTSBURGH, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        rows = []
        for tr in soup.select("table tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                label = tds[0].get_text(" ", strip=True)
                val = tds[1].get_text(" ", strip=True)
                if label and val:
                    rows.append((label, val))
        df = pd.DataFrame(rows, columns=["label", "value"])
        df = df[df["value"].str.contains(r"\d", na=False)]
        return df.reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["label", "value"])


# ------------- Enhanced Comparison Utils -------------

import re, json
import plotly.express as px
import streamlit as st

def extract_numeric(val):
    if pd.isna(val):
        return None
    s = re.sub(r"[\$,]", "", str(val))
    match = re.search(r"(\d+(\.\d+)?)", s)
    return float(match.group(1)) if match else None


def summarize_student_expenses(exp):
    if not exp:
        return None
    m = exp["expenses"]["monthly"]
    on_total = sum(m["on_campus"].values())
    off_total = sum(m["off_campus"].values())
    utilities = m["utilities"]
    transport = m["transportation"]
    fun_total = sum(m["fun"].values())
    total = m["total"]
    return {
        "On-Campus": on_total,
        "Off-Campus": off_total,
        "Utilities": utilities,
        "Transportation": transport,
        "Fun": fun_total,
        "Total": total,
    }


def summarize_city_costs(df):
    cat_map = {
        "Food": ["restaurant", "meal", "groceries"],
        "Rent": ["apartment", "rent", "housing"],
        "Transport": ["transport", "taxi", "bus"],
        "Utilities": ["electricity", "internet"],
        "Fun": ["cinema", "fitness", "gym"],
    }
    df["category"] = "Other"
    for cat, kws in cat_map.items():
        mask = df["label"].str.contains("|".join(kws), case=False, na=False)
        df.loc[mask, "category"] = cat
    df["value_num"] = df["value"].apply(extract_numeric)
    avg_df = df.groupby("category", as_index=False)["value_num"].mean()
    return avg_df.set_index("category")["value_num"].to_dict()


def render_cost_of_living_comparison(student, expense_record, col_df):
    expense_summary = summarize_student_expenses(expense_record)
    if not expense_summary:
        st.warning("No expense data available for this student.")
        return

    city_summary = summarize_city_costs(col_df)
    compare_df = pd.DataFrame([
        {"Category": "Food", "You": expense_summary["Off-Campus"] + expense_summary["On-Campus"],
         "Pittsburgh Avg": city_summary.get("Food", 0)},
        {"Category": "Utilities", "You": expense_summary["Utilities"], "Pittsburgh Avg": city_summary.get("Utilities", 0)},
        {"Category": "Transportation", "You": expense_summary["Transportation"], "Pittsburgh Avg": city_summary.get("Transport", 0)},
        {"Category": "Fun", "You": expense_summary["Fun"], "Pittsburgh Avg": city_summary.get("Fun", 0)},
    ])

    fig = px.bar(
        compare_df.melt(id_vars="Category", var_name="Source", value_name="USD"),
        x="Category",
        y="USD",
        color="Source",
        barmode="group",
        title=f"Monthly Cost Comparison — {student.get('name')}",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(yaxis_title="USD", height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Spending Insights")
    for cat in compare_df["Category"]:
        row = compare_df[compare_df["Category"] == cat].iloc[0]
        your_val, city_val = row["You"], row["Pittsburgh Avg"]
        if city_val == 0:
            continue
        diff_pct = ((your_val - city_val) / city_val) * 100
        if diff_pct > 15:
            st.warning(f"**{cat}:** You’re spending {diff_pct:.1f}% above the city average — consider cost-saving options.")
        elif diff_pct < -15:
            st.success(f"**{cat}:** You’re spending {abs(diff_pct):.1f}% below the city average — great budgeting!")
        else:
            st.info(f"**{cat}:** Spending roughly aligns with city average.")

    st.metric("💰 Total Monthly Spending", f"${expense_summary['Total']:,.2f}")

    if st.button("🧾 Audit or Add Monthly Expenses"):
        st.info("Expense audit feature coming soon — will let you add or adjust your costs dynamically.")
