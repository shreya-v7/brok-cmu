'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        budget_engine.py
Purpose:     Provides financial estimation utilities for students, including
             automated monthly budget inference based on semester tuition data.
             Allocates expected spending across categories such as rent, food,
             transportation, utilities, leisure, and savings.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''


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
