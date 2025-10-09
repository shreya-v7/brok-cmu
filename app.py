import os, json, re
import pandas as pd
import streamlit as st
import plotly.express as px
import google.generativeai as genai

from config import GEMINI_API_KEY
from utils.tuition import (
    load_tuition_excel,
    normalize_tuition_units,
    dedupe_tuition,
    filter_by_school_and_known_units
)
from scrapers.cost_of_living import fetch_pittsburgh_cost_of_living
from scrapers.loans import fetch_loans_overview
from scrapers.news import fetch_news

# NEW IMPORTS for student expense audit + comparison
from scrapers.cost_of_living import (
    summarize_student_expenses,
    summarize_city_costs,
    render_cost_of_living_comparison
)


# ------------------------------------
#  Streamlit Setup
# ------------------------------------
st.set_page_config(page_title="🎓 CMU Student Financial Advisor", layout="wide")
st.markdown(
    "<h1 style='text-align:center; color:#A40000;'>CMU Student Financial Advisor Dashboard</h1>",
    unsafe_allow_html=True
)

# ------------------------------------
#  Load Data
# ------------------------------------
STUDENTS_PATH = "data/cmu_mock_students.json"
TUITION_PATH  = "data/cmu_tuition_clean_processed.xlsx"

students = json.load(open(STUDENTS_PATH))
tuition_raw = load_tuition_excel(TUITION_PATH)
tuition_clean = dedupe_tuition(normalize_tuition_units(tuition_raw))

# NEW: Load student expense audit data
EXPENSES_PATH = "data/cmu_mock_expenses_audit.json"
student_expenses = json.load(open(EXPENSES_PATH))


# ------------------------------------
#  Sidebar Navigation
# ------------------------------------
st.sidebar.header("🎓 Select Student")
student_names = [s.get("name", "Unknown") for s in students]
selected_name = st.sidebar.selectbox("Choose Student", student_names)
student = next(s for s in students if s.get("name") == selected_name)
expense_record = next((e for e in student_expenses if e.get("name") == selected_name), None)
page = st.sidebar.radio("Navigate", ["Overview", "Finances & Living", "News"])

# ------------------------------------
#  Helper Functions
# ------------------------------------
def fmt_money(x):
    try:
        return f"${float(x):,.0f}"
    except:
        return "—"

def extract_numeric(val):
    """Extract numeric value from strings like '$1,200' or '58.8 miles'."""
    if pd.isna(val):
        return None
    s = re.sub(r"[\$,]", "", str(val))
    match = re.search(r"(\d+(\.\d+)?)", s)
    return float(match.group(1)) if match else None

def get_student_keywords(student):
    """Return keywords for tuition filtering."""
    p = student.get("program", {})
    kws = set()
    for key in ["school", "department", "level"]:
        v = p.get(key)
        if v:
            kws.add(v.lower())
    for c in p.get("courses", []):
        kws.add(re.sub(r"\W+", " ", c.lower()))
    return list(kws)

def get_tuition_for_student(df, student):
    """Match by school, department, or course name."""
    p = student.get("program", {})
    school, dept = p.get("school", ""), p.get("department", "")
    subset = filter_by_school_and_known_units(df, school, dept)
    if not subset.empty:
        return subset, school
    for kw in get_student_keywords(student):
        match = df[df["program"].astype(str).str.contains(kw, case=False, na=False)]
        if not match.empty:
            return match, kw
    return pd.DataFrame(columns=df.columns), "—"

# ------------------------------------
#  Overview Page
# ------------------------------------
if page == "Overview":
    prog = student.get("program", {})
    fin = student.get("financials", {})

    st.subheader(f"👤 {student.get('name','—')}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**ID:** {student.get('student_id','—')}")
        st.markdown(f"**Email:** {student.get('email','—')}")
        st.markdown(f"**Nationality:** {student.get('nationality','—')}")
    with c2:
        st.markdown(f"**School:** {prog.get('school','—')}")
        st.markdown(f"**Department:** {prog.get('department','—')}")
        st.markdown(f"**Level:** {prog.get('level','—')}")
    with c3:
        st.markdown(f"**GPA:** {prog.get('gpa','—')}")
        st.markdown(f"**Expected Grad:** {prog.get('expected_grad_year','—')}")
        st.markdown(f"**Status:** {student.get('status','—')}")
    st.markdown("**Courses:** " + ", ".join(prog.get("courses", []) or ["—"]))
    st.divider()

    # --------------------------------------------------
    # 💬 Interactive Advisory Chat (after AI Advisory)
    # --------------------------------------------------

    st.subheader("💬 Student Advisory Chat")

    # Initialize chat session
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Student objective input
    if prompt := st.chat_input("Ask about your finances, tuition, or CMU life..."):
        # Show user message
        st.chat_message("user").markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Build context dynamically
        prog = student.get("program", {})
        fin = student.get("financials", {})

        student_context = f"""
        Student: {student.get('name')}
        ID: {student.get('student_id')}
        Level: {prog.get('level')}
        Department: {prog.get('department')}
        School: {prog.get('school')}
        GPA: {prog.get('gpa')}
        Tuition per semester: {fin.get('tuition_per_semester')}
        Scholarship: {fin.get('scholarship')}
        Assistantship: {fin.get('assistantship')}
        Invoices: {fin.get('invoices')}
        """

        tuition_df, matched_key = get_tuition_for_student(tuition_clean, student)
        col_df = fetch_pittsburgh_cost_of_living()

        tuition_context = tuition_df.head(5).to_dict(orient="records") if not tuition_df.empty else "N/A"
        col_context = col_df.head(5).to_dict(orient="records") if not col_df.empty else "N/A"

        if expense_record:
            expense_context = expense_record["expenses"]["monthly"]
        else:
            expense_context = "N/A"

        # Full LLM prompt with expenses added
        full_prompt = f"""
        You are Brok, an academic and financial advisor for Carnegie Mellon students.
        Use the student's data and context to give clear, factual advice.

        Student context:
        {student_context}

        Monthly Expense context (from audit data):
        {json.dumps(expense_context, indent=2)}

        Tuition context:
        {tuition_context}

        Cost of living (Pittsburgh averages):
        {col_context}

        Student's input:
        {prompt}

        Please respond with structured, helpful advice — use short paragraphs, clear comparisons,
        and provide actionable financial recommendations (budgeting, housing, food, or transport tips).
        """

        # Generate model response
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    model = genai.GenerativeModel("gemini-2.5-pro")
                    res = model.generate_content(full_prompt)
                    response_text = res.text or "No response generated."
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        else:
            st.warning("⚠️ Please configure your GEMINI_API_KEY to enable the chat advisor.")


# ------------------------------------
#  Finances & Living
# ------------------------------------
elif page == "Finances & Living":
    prog = student.get("program", {})
    fin = student.get("financials", {})
    tuition_df, matched_key = get_tuition_for_student(tuition_clean, student)

    tab1, tab2, tab3 = st.tabs(["🎓 Scholarships & Invoices", "🏙️ Cost of Living", "📊 Tuition"])

    # ---- Tuition ----
    with tab3:
        st.markdown(f"#### Tuition Data (matched with: <span style='color:green;font-weight:600'>{matched_key}</span>)", unsafe_allow_html=True)
        if tuition_df.empty:
            st.warning("No tuition info found for this program.")
        else:
            # Clean + filter noise
            tuition_df["amount"] = pd.to_numeric(tuition_df["amount"], errors="coerce")
            exclude_words = ["search", "office of enrollment", "financial services", "student financial", "university —"]
            mask = ~tuition_df["item"].astype(str).str.lower().str.contains("|".join(exclude_words))
            tuition_df = tuition_df[mask]
            tuition_df = tuition_df.dropna(subset=["amount"])

            # Categorize
            def classify(x):
                x = str(x).lower()
                if "tuition" in x: return "Tuition"
                if "fee" in x: return "Fees"
                if any(k in x for k in ["living", "meal", "housing", "food"]): return "Living"
                return "Other"

            tuition_df["category"] = tuition_df["item"].apply(classify)
            tuition_df["unit_clean"] = tuition_df["unit"].str.title().fillna("Per Year")

            # Filter by toggle
            unit_filter = "per"
            tuition_df = tuition_df[tuition_df["unit_clean"].str.lower().str.contains(unit_filter)]

            # Deduplicate
            tuition_df = (
                tuition_df.sort_values("amount", ascending=False)
                .drop_duplicates(subset=["school", "unit_clean", "category"])
            )
            tuition_df["amount_fmt"] = tuition_df["amount"].apply(fmt_money)

            st.dataframe(tuition_df[["school", "category", "item", "amount_fmt", "unit_clean"]], use_container_width=True)

            # Visuals
            chart_df = tuition_df.groupby(["unit_clean", "category"], as_index=False)["amount"].mean()
            fig = px.bar(
                chart_df,
                x="unit_clean",
                y="amount",
                color="category",
                barmode="group",
                text_auto=".2s",
                title=f"Average Tuition & Fee Breakdown — {prog.get('school','')}",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(yaxis_title="USD", height=420)
            st.plotly_chart(fig, use_container_width=True)

    # ---- Scholarships ----
    with tab1:
        st.markdown("#### Financial Summary")
        tuition_sem = fin.get("tuition_per_semester", 0)
        schol = fin.get("scholarship") or {}
        schol_amt = schol.get("amount", 0)
        schol_type = schol.get("type", "—")
        schol_pct = round((schol_amt / tuition_sem) * 100, 2) if tuition_sem else 0
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Tuition / Semester", fmt_money(tuition_sem))
        with c2: st.metric("Scholarship", f"{fmt_money(schol_amt)} ({schol_pct}%)", schol_type)
        with c3:
            assistantship = fin.get("assistantship")

            if isinstance(assistantship, dict):
                role = assistantship.get("role", "—")
                stipend = assistantship.get("stipend", 0)
                st.metric("Assistantship", fmt_money(stipend), role)
            elif assistantship:
                # if it's just a string like "TA" or "RA"
                st.metric("Assistantship", assistantship)
            else:
                st.metric("Assistantship", "—")

        inv_df = pd.DataFrame(fin.get("invoices", []))
        if not inv_df.empty:
            inv_df["due"] = inv_df["due"].apply(fmt_money)
            inv_df["paid"] = inv_df["paid"].apply(fmt_money)
            inv_df["balance"] = inv_df["balance"].apply(fmt_money)
            st.dataframe(inv_df, use_container_width=True)

    # ---- Cost of Living ----
    with tab2:

        col_df = fetch_pittsburgh_cost_of_living()

        st.markdown("### 💵 Your Monthly Spending vs. Pittsburgh Average")

        if expense_record:
            render_cost_of_living_comparison(student, expense_record, col_df)
        else:
            st.warning("No expense data found for this student.")

        if not col_df.empty:
            col_df.columns = [c.lower().strip() for c in col_df.columns]
            col_df.rename(columns={"item": "label", "cost": "value"}, inplace=True)
            col_df["value_num"] = col_df["value"].apply(extract_numeric)
            col_df = col_df.dropna(subset=["value_num"])

            # Group categories
            group_keywords = {
                "Food": ["meal", "restaurant", "groceries"],
                "Rent": ["apartment", "rent", "housing"],
                "Transport": ["transport", "bus", "taxi"],
                "Utilities": ["electricity", "internet"]
            }
            col_df["category"] = "Other"
            for cat, kws in group_keywords.items():
                mask = col_df["label"].str.contains("|".join(kws), case=False, na=False)
                col_df.loc[mask, "category"] = cat

            avg_df = col_df.groupby("category", as_index=False)["value_num"].mean()

            fig2 = px.pie(
                avg_df,
                names="category",
                values="value_num",
                title="Average Monthly Expenses — Pittsburgh",
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(col_df[["label", "value", "category"]], use_container_width=True)
            st.divider()

# ------------------------------------
#  News Page
# ------------------------------------
elif page == "News":
    st.markdown("### 🗞️ CMU & Pittsburgh Updates")
    news_df = fetch_news()
    if news_df.empty:
        st.info("No recent news found.")
    else:
        news_df.columns = [c.lower().strip() for c in news_df.columns]
        mask = news_df["title"].str.contains(
            r"(Carnegie Mellon|CMU|Pittsburgh|tuition|scholarship|student|financial aid)",
            case=False, na=False
        )
        subset = news_df[mask].head(12)
        for _, row in subset.iterrows():
            st.markdown(f"**[{row['title']}]({row['link']})**  \n*{row.get('pubdate','')} — {row.get('source','')}*")
            st.markdown(f"<p style='color:gray'>{row.get('summary','')}</p>", unsafe_allow_html=True)
            st.markdown("---")
