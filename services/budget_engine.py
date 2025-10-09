def infer_monthly_budget(tuition_semester: float):
    base = tuition_semester / 4 if tuition_semester else 6000
    budget = {
        "Rent": base * 0.35,
        "Food": base * 0.2,
        "Transportation": base * 0.1,
        "Utilities": base * 0.1,
        "Leisure": base * 0.1,
        "Savings": base * 0.15
    }
    total = sum(budget.values())
    return budget, total
