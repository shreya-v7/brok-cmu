import os
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
