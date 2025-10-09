# 🎓 CMU Student Financial Advisor Dashboard

An intelligent, data-driven financial advisory dashboard built using **Streamlit** and **Google Gemini**, simulating real-world Carnegie Mellon University student financial management, including tuition breakdowns, scholarships, living costs, and AI-guided financial insights.

---

## 🧭 Overview

The **CMU Student Financial Advisor Dashboard** provides a unified interface for analyzing:
- Student tuition and scholarships  
- Monthly on/off-campus expenses  
- Pittsburgh cost-of-living comparisons  
- Personalized AI-powered budgeting advice  

The system combines **data preprocessing**, **Streamlit visualization**, and **Gemini model reasoning** into one cohesive ecosystem.

---

## 🏗️ Project Structure

```
brok/
│
├── data/
│   ├── cmu_mock_students.json              # Mock CMU student profiles (50)
│   ├── cmu_mock_expenses_audit.json        # Monthly student expenses (food, rent, fun, etc.)
│   ├── cmu_tuition_clean.xlsx              # Raw tuition data (input)
│   └── cmu_tuition_clean_processed.xlsx    # Cleaned tuition (output of preprocess.py)
│
├── scrapers/
│   ├── cmu_tuition.py                      # Tuition data extraction and transformation
│   ├── cost_of_living.py                   # Fetches Pittsburgh cost of living
│   ├── loans.py                            # Mock loan data or API integration
│   └── news.py                             # Fetches CMU and finance-related news
│
├── services/
│   ├── budget_engine.py                    # Handles financial optimization and summaries
│   └── gemini_client.py                    # Gemini API interface for AI chat
│
├── utils/
│   ├── caching.py                          # Caching utilities
│   ├── charts.py                           # Plotly chart creation helpers
│   ├── parsing.py                          # Regex and data extraction tools
│   ├── preprocess.py                       # Tuition preprocessing pipeline (run manually)
│   └── tuition.py                          # Tuition normalization, deduplication, and filtering
│
├── app.py                                  # Streamlit main app (UI, chat, dashboard)
├── config.py                               # Configuration constants and GEMINI_API_KEY
├── mock_genai.py                           # Offline Gemini test client
├── .env                                    # Environment variables (Gemini API key)
└── requirements.txt                        # Python dependencies
```

---

## 🔁 System Flow Diagram

```mermaid
flowchart TD
    A[Raw Tuition Excel<br>cmu_tuition_clean.xlsx] -->|Run preprocess.py| B[Processed Tuition Data<br>cmu_tuition_clean_processed.xlsx]
    C[Mock Students JSON<br>cmu_mock_students.json] --> D[Streamlit Dashboard<br>app.py]
    E[Expense Audit JSON<br>cmu_mock_expenses_audit.json] --> D
    B --> D
    D --> F[AI Chat Advisor<br>Gemini 2.5 Pro]
    D --> G[Visual Insights<br>Plotly Charts, Tabs, Metrics]
    F -->|Contextual Advice| D
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone <your_repo_url>
cd brok
```

### 2️⃣ Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# or
.venv\Scripts\activate       # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the project root and add your Gemini API key:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Alternatively, update `config.py` to include your key directly.

---

## 🧹 Data Preprocessing (Must Run Before Streamlit)

Before launching the app, **tuition data must be cleaned and saved** into `data/cmu_tuition_clean_processed.xlsx`.

### Run Preprocessing Script

```bash
python -m brok.utils.preprocess
```

✅ This will:
- Load the raw tuition file: `data/cmu_tuition_clean.xlsx`  
- Normalize and deduplicate units (e.g., per credit, per semester)  
- Save the cleaned version to:  
  `data/cmu_tuition_clean_processed.xlsx`  

Once done, this file becomes the primary tuition data source for `app.py`.

---

## 🚀 Running the Application

After preprocessing is complete, start the Streamlit dashboard:

```bash
streamlit run app.py
```

Then open the displayed URL (usually `http://localhost:8501`) in your browser.

---

## 🧩 Dashboard Features

| Section | Description |
|----------|-------------|
| **Overview Page** | Displays selected student details and academic info |
| **Scholarships & Invoices Tab** | Shows tuition per semester, scholarships, assistantships, and invoice summaries |
| **Cost of Living Tab** | Visual comparison of student vs. Pittsburgh expenses (on-campus vs. off-campus) |
| **Tuition Tab** | Displays program-specific tuition breakdown by unit (semester, year, etc.) |
| **AI Advisory Chat** | Context-aware Gemini chat offering budgeting and financial tips |
| **News Page** | Fetches CMU and financial news from online sources |

---

## 💬 Gemini AI Advisor

The **AI financial chat system** is powered by **Google Gemini 2.5 Pro** and uses contextual prompts built from:
- Student profile data  
- Monthly expense breakdown  
- Tuition and scholarship details  
- Pittsburgh cost-of-living averages  

Each student has an independent chat session.  
When a new student is selected, the chat history resets automatically.

If `GEMINI_API_KEY` is not configured, a warning will appear and the assistant will be disabled.

---

## 📊 Data Summary

| File | Purpose |
|------|----------|
| `cmu_mock_students.json` | Mock student dataset with demographics and academic details |
| `cmu_mock_expenses_audit.json` | Monthly breakdown of spending (rent, food, transport, etc.) |
| `cmu_tuition_clean.xlsx` | Raw tuition dataset (source) |
| `cmu_tuition_clean_processed.xlsx` | Cleaned tuition dataset (output of preprocessing) |

---

## 🧠 Workflow Summary

1. **Run tuition preprocessing:**  
   Clean and prepare tuition dataset.

2. **Start Streamlit app:**  
   Loads students, tuition, and expense JSONs.

3. **Select a student:**  
   View academic details and financial overview.

4. **Explore tabs:**  
   - Scholarships & invoices  
   - Cost of living comparison  
   - Tuition breakdown  

5. **Chat with AI:**  
   Ask financial questions — Gemini responds contextually using your data.

6. **View CMU News:**  
   Stay updated with CMU and Pittsburgh finance headlines.

---

## 🧰 Developer Notes

- You can test without an API key using `mock_genai.py`.  
- Extend budget optimization via `services/budget_engine.py`.  
- Adjust caching and plotting in `utils/` for performance.  
- Cost-of-living visualizations are built with Plotly (dynamic updates supported).

---

## 🧾 License

**MIT License © 2025 brok@CMU**
