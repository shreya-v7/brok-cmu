# brok@cmu — Intelligent Student Advisory

A Streamlit app that helps CMU students plan budgets:
- Select a student → see profile, GPA, tuition invoices, etc.
- Live context: CMU tuition pages, Pittsburgh cost of living (Numbeo), student aid & loan sites, and relevant news.
- Gemini generates a tailored budget and 30/60/90 day plan.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add GEMINI_API_KEY
streamlit run app.py
