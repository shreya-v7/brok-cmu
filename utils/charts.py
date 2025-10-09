'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        charts.py
Purpose:     Provides charting utilities for visualizing financial data.
             Includes Plotly-based rendering functions such as `budget_pie`
             for displaying monthly budget distributions interactively within
             the Streamlit dashboard.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''


import plotly.graph_objects as go

def budget_pie(monthly_dict: dict):
    labels, values = list(monthly_dict.keys()), list(monthly_dict.values())
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.45)])
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), title="Monthly Budget Breakdown")
    return fig
