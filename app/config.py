"""
config.py
Loads all secrets and settings from the .env file.
Nothing else in the project should call os.getenv() directly — import from here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Twilio ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")          # e.g. +1415XXXXXXX (your Twilio voice number)
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Twilio sandbox default

# --- LLM ---
# LLM_PROVIDER selects which API to call: "groq" (free) or "openai" (paid).
# Groq uses the same OpenAI-compatible client, just with a different
# base_url and model name — that's the only real difference.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Groq's tool-calling-capable free model. Good balance of speed/quality.
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile" if LLM_PROVIDER == "groq" else "gpt-4o-mini")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# --- Server ---
# BASE_URL must be your public ngrok URL, e.g. https://abcd-1234.ngrok-free.app
# Twilio needs a public URL to fetch the generated audio files for <Play>.
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# --- Business info file ---
BUSINESS_INFO_PATH = os.getenv("BUSINESS_INFO_PATH", "business_info.json")

# --- Booking rules ---
BUSINESS_OPEN_HOUR = int(os.getenv("BUSINESS_OPEN_HOUR", "9"))    # 9 AM
BUSINESS_CLOSE_HOUR = int(os.getenv("BUSINESS_CLOSE_HOUR", "18")) # 6 PM
SLOT_MINUTES = int(os.getenv("SLOT_MINUTES", "30"))

DB_PATH = os.getenv("DB_PATH", "appointments.db")
