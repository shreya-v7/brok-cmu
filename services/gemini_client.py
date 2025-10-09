'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        gemini_client.py
Purpose:     Integrates Google's Gemini Generative AI API to provide personalized
             financial and academic advice for CMU students. Uses the configured
             GEMINI_API_KEY to generate contextualized recommendations based on
             student data, objectives, and cost-of-living insights.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''


import google.generativeai as genai
from config import GEMINI_API_KEY

def generate_budget_advice(student, objective, context):
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key missing."
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f"""
    You are a CMU finance advisor. Given the student profile:
    {student}
    Objective: {objective}
    Context: {context}
    Provide detailed financial and academic advice in bullet form.
    """
    try:
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        return f"Error generating advice: {e}"
