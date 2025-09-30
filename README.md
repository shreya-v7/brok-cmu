# Steel Student Finance — CMU (Pittsburgh) Analyzer

End-to-end Streamlit app:
- Load your `cmu_mock_students.json`
- (Optional) scrape Pittsburgh price signals (robots-aware) for rent & groceries
- Fetch current federal student loan rates & headlines (RSS) with safe fallbacks
- Run per-student affordability with personalized suggestions based on a target objective

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Notes
- Scrapers honor `robots.txt` and have fallbacks to synthetic medians.
- Use the sidebar to point to your **cmu_mock_students.json** (or upload it in the UI).
- Objectives supported (examples): "save $200/month", "pay off $5000 in 24 months", "cut spending by 15%".
