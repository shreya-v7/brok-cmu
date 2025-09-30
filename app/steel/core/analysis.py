from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from .loan import LoanInput, amortize

DEFAULTS = {
    "rent_usd_month": 1200.0,
    "groceries_usd_month": 320.0,
    "utilities_usd_month": 120.0,
    "transit_usd_month": 25.0,
    "misc_usd_month": 150.0,
    "apr_undergrad": 5.0,
    "apr_masters": 6.0,
    "apr_phd": 4.0,
    "loan_term_months": 120
}

def pick_apr(level: str) -> float:
    if level == "Undergraduate": return DEFAULTS["apr_undergrad"]
    if level == "PhD": return DEFAULTS["apr_phd"]
    return DEFAULTS["apr_masters"]

@dataclass
class PriceSignals:
    rent: float
    groceries: float
    utilities: float
    transit: float

def analyze_student(student: Dict[str, Any], prices: PriceSignals, objective: Dict[str, Any] | None = None):
    prog = student.get("program", {})
    fin = student.get("financials", {})
    level = prog.get("level")
    stipend = (fin.get("assistantship") or {}).get("stipend", 0) or 0
    scholarship = (fin.get("scholarship") or {}).get("amount", 0) or 0
    tuition = fin.get("tuition_per_semester", 0) or 0

    monthly_cost = prices.rent + prices.groceries + prices.utilities + prices.transit + DEFAULTS["misc_usd_month"]
    net_after_stipend = max(monthly_cost - stipend, 0.0)

    # Nominal principal for non-fully-funded programs (9-month academic year)
    principal = 0.0 if (level == "PhD" and (stipend > 0 or scholarship > 0)) else max(0.0, monthly_cost*9 - scholarship)
    apr = pick_apr(level or "")
    loan_out = amortize(LoanInput(principal=principal, apr_pct=apr, term_months=DEFAULTS["loan_term_months"]))

    plan = recommend_cuts(monthly_cost, stipend, prices, objective or {})
    return {
        "student": {"id": student.get("student_id"), "name": student.get("name"), "level": level, "dept": prog.get("department")},
        "prices": {"rent": prices.rent, "groceries": prices.groceries, "utilities": prices.utilities, "transit": prices.transit},
        "monthly_cost": round(monthly_cost,2),
        "stipend": stipend,
        "tuition_per_semester": tuition,
        "scholarship": scholarship,
        "net_after_stipend": round(net_after_stipend,2),
        "loan_apr": apr,
        "loan_projection": loan_out,
        "suggested_plan": plan
    }

def recommend_cuts(monthly_cost: float, stipend: float, prices: PriceSignals, objective: Dict[str, Any]) -> Dict[str, Any]:
    target_savings = 0.0
    if objective.get("type") == "save_per_month":
        target_savings = float(objective.get("amount", 0))
    elif objective.get("type") == "payoff_in_months":
        # Minimal heuristic: try to free up additional amount equal to 5-10% of monthly_cost
        target_savings = 0.1 * monthly_cost

    # baseline allocations
    alloc = {
        "rent": prices.rent, "groceries": prices.groceries, "utilities": prices.utilities, "transit": prices.transit, "misc": 150.0
    }
    # heuristics
    recs = []
    # rent: roommate/1BR->2BR split
    recs.append({"category": "rent", "tip": "Consider shared housing around Squirrel Hill, Bloomfield, or Shadyside to cut ~20–35% versus solo 1BR.", "potential_savings": round(0.25*alloc["rent"],2)})
    # groceries: meal planning
    recs.append({"category": "groceries", "tip": "Shift 25% of meals to planned batch-cook items; swap 3 premium items for store brands.", "potential_savings": round(0.18*alloc["groceries"],2)})
    # utilities: LED/thermostat habits
    recs.append({"category": "utilities", "tip": "Lower thermostat 2°F and switch to LED/task lighting.", "potential_savings": round(0.1*alloc["utilities"],2)})
    # transit: bus pass vs ride-hail
    recs.append({"category": "transit", "tip": "Use Port Authority student pass and group errands; avoid 2 ride-hails/week.", "potential_savings": round(0.2*alloc["transit"],2)})
    # misc: cap coffees/eating out
    recs.append({"category": "misc", "tip": "Cap coffees/eating-out to 1–2/week.", "potential_savings": 40.0})

    recs_sorted = sorted(recs, key=lambda x: -x["potential_savings"])
    accumulated = 0.0
    chosen = []
    for r in recs_sorted:
        if accumulated >= target_savings: break
        chosen.append(r); accumulated += r["potential_savings"]
    return {"target_savings": round(target_savings,2), "estimated_savings": round(accumulated,2), "actions": chosen}
