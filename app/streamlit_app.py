import json
import os

import streamlit as st

from steel.core.analysis import analyze_student, PriceSignals, DEFAULTS
from steel.core.loader import load_students, as_dataframe
from steel.scrapers.grocery_example import fetch_grocery_basket_monthly
from steel.scrapers.loan_rates import fetch_federal_rates
from steel.scrapers.news import get_headlines
from steel.scrapers.rent_pgh_craigslist import fetch_rent_median

st.set_page_config(page_title="Steel Student Finance (Pittsburgh)", page_icon="🏗️", layout="wide")
st.title("Steel Student Finance — CMU Mock Students (Pittsburgh)")

with st.sidebar:
    st.header("Student dataset")
    default_path = os.environ.get("CMU_STUDENTS_JSON", "cmu_mock_students.json")
    json_path = st.text_input("Path to cmu_mock_students.json", value=default_path)
    uploaded = st.file_uploader("...or upload JSON", type=["json"])
    students = []
    if uploaded:
        students = json.load(uploaded)
    else:
        if os.path.exists(json_path):
            try:
                students = load_students(json_path)
            except Exception as e:
                st.error(f"Failed to load {json_path}: {e}")
        else:
            st.warning("Provide a JSON path or upload the file to proceed.")

    st.divider()
    st.header("Live signals")
    colA, colB = st.columns(2)
    with colA:
        do_scrape = st.button("Fetch latest signals")
    with colB:
        grocery_url = st.text_input("Optional: Weekly-ad URL for basket estimate", value="")

    st.caption("Signals include: 1BR rent median (Craigslist), grocery basket, federal loan rates, and local headlines (RSS).")

# Fetch signals (with fallbacks)
@st.cache_data(ttl=3600)
def get_signals(grocery_url: str=""):
    rent = fetch_rent_median() or DEFAULTS["rent_usd_month"]
    groceries = fetch_grocery_basket_monthly(grocery_url) if grocery_url else DEFAULTS["groceries_usd_month"]
    rates = fetch_federal_rates()
    headlines = get_headlines()
    return {"rent": rent, "groceries": groceries, "rates": rates, "headlines": headlines}

signals = get_signals(grocery_url if (uploaded or os.path.exists(json_path)) else "")
if do_scrape:
    signals = get_signals.clear() or get_signals(grocery_url)

# Display signals
sig_col1, sig_col2, sig_col3 = st.columns(3)
with sig_col1:
    st.metric("Rent (1BR median)", f"${signals['rent']:.0f}/mo")
with sig_col2:
    st.metric("Groceries (basket)", f"${signals['groceries']:.0f}/mo")
with sig_col3:
    st.metric("Loan APR (UG/M/PhD)", f"{signals['rates']['undergrad']:.2f}% / {signals['rates']['grad']:.2f}% / {signals['rates']['phd']:.2f}%")

if signals["headlines"]:
    with st.expander("Latest local headlines"):
        for h in signals["headlines"]:
            st.markdown(f"- [{h['title']}]({h['link']})")

st.divider()

if not students:
    st.stop()

df = as_dataframe(students)
st.subheader("Students")
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Analyze a student")

# choose student
sid = st.selectbox("Pick student_id", options=df["student_id"].tolist())
objective_type = st.selectbox("Objective", options=["None","Save per month","Pay off loan in X months","Cut spending by %"])
obj = {}
if objective_type == "Save per month":
    amt = st.number_input("Amount to save per month (USD)", min_value=0.0, value=200.0, step=50.0)
    obj = {"type": "save_per_month", "amount": amt}
elif objective_type == "Pay off loan in X months":
    months = st.number_input("Months", min_value=6, value=24, step=6)
    obj = {"type": "payoff_in_months", "months": months}
elif objective_type == "Cut spending by %":
    pct = st.number_input("Percent to cut (%)", min_value=5, max_value=50, value=15, step=5)
    # translate into per-month savings target
    obj = {"type": "save_per_month", "amount": pct/100.0 * (signals['rent']+signals['groceries']+DEFAULTS['utilities_usd_month']+DEFAULTS['transit_usd_month']+DEFAULTS['misc_usd_month'])}

if st.button("Run analysis"):
    st.write("Running...")
    student = next(s for s in students if s.get("student_id") == sid)
    prices = PriceSignals(rent=signals["rent"], groceries=signals["groceries"],
                          utilities=DEFAULTS["utilities_usd_month"], transit=DEFAULTS["transit_usd_month"])
    res = analyze_student(student, prices, obj or None)
    st.json(res)
    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Cost", f"${res['monthly_cost']:.2f}")
    c2.metric("After Stipend", f"${res['net_after_stipend']:.2f}")
    c3.metric("Loan Payment", f"${res['loan_projection']['payment']:.2f}")
    st.markdown("**Suggested actions:**")
    for a in res["suggested_plan"]["actions"]:
        st.markdown(f"- **{a['category']}**: {a['tip']} — *save about ${a['potential_savings']:.0f}/mo*")
