from google import genai
import os

# --- SETUP YOUR API KEY ---
# Option 1: Store directly (quick test)
API_KEY = ""

# Option 2 (recommended): set environment variable instead
# export GEMINI_API_KEY="YOUR_API_KEY_HERE"
# Then just do:
# API_KEY = os.getenv("GEMINI_API_KEY")

# --- INITIALIZE CLIENT ---
client = genai.Client(api_key=API_KEY)

# --- GENERATE TEXT FROM GEMINI ---
response = client.models.generate_content(
    model="gemini-2.0-flash",     # or "gemini-1.5-flash", "gemini-1.5-pro", etc.
    contents="what do you think about carnegie mellon university"
)

# --- PRINT RESPONSE ---
print(response.text)
