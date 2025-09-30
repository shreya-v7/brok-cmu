import json, os, pandas as pd

REQUIRED_FIELDS = ["student_id","name","program","financials"]

def load_students(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected a list of student objects")
    # light validation
    out = []
    for i, s in enumerate(data, 1):
        if not all(k in s for k in REQUIRED_FIELDS):
            raise ValueError(f"Student #{i} missing required fields")
        out.append(s)
    return out

def as_dataframe(students: list[dict]) -> pd.DataFrame:
    rows = []
    for s in students:
        fin = s.get("financials", {})
        prog = s.get("program", {})
        aid = (fin.get("scholarship") or {}).get("amount", 0) if fin.get("scholarship") else 0
        asst = fin.get("assistantship") or {}
        stipend = asst.get("stipend", 0) or 0
        rows.append({
            "student_id": s.get("student_id"),
            "name": s.get("name"),
            "level": prog.get("level"),
            "dept": prog.get("department"),
            "gpa": prog.get("gpa"),
            "tuition_per_sem": fin.get("tuition_per_semester", 0),
            "scholarship_amt": aid,
            "assistantship_role": asst.get("role"),
            "stipend": stipend,
            "status": s.get("status", "active")
        })
    return pd.DataFrame(rows)
