"""
╔══════════════════════════════════════════════════════════════╗
║   config.py  —  Central settings for the Healthcare AI Agent  ║
╚══════════════════════════════════════════════════════════════╝

Everything configurable lives HERE so you never have to hunt through
the code. API keys are loaded from a `.env` file (never hard-code keys!).

Create a `.env` file next to this one:

    GROQ_API_KEY=your_groq_key_here
    SERPER_API_KEY=your_serper_key_here

The agent still works WITHOUT keys — it falls back to an offline
knowledge base + built-in calculators. Keys just unlock the LLM brain
and live web search.
"""

import os
import sys
from dotenv import load_dotenv

# ── Windows fix: make the console speak UTF-8 so emojis (🏥 ✅ 🚨) don't crash.
# Python on Windows defaults to cp1252 which can't encode emoji. Reconfigure
# stdout/stderr to UTF-8 the moment anything imports config.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load variables from .env into the environment
load_dotenv()

# ─────────────────────────────────────────────
# API KEYS  (read from environment — safe!)
# ─────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "").strip()
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "").strip()

# New APIs (all optional — features gracefully fall back if a key is missing)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()   # weather + air quality
USDA_API_KEY        = os.getenv("USDA_API_KEY", "").strip()          # nutrition data
NEWSAPI_KEY         = os.getenv("NEWSAPI_KEY", "").strip()           # health news

# Twilio — SMS medicine reminders & emergency alerts
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()
TWILIO_TO_NUMBER   = os.getenv("TWILIO_TO_NUMBER", "").strip()       # your/emergency contact number

# Feature flags — auto-detected from whether keys exist.
# Missing key -> feature runs in a safe offline/demo mode instead of crashing.
HAS_LLM        = bool(GROQ_API_KEY)                                   # smart AI answers
HAS_WEB_SEARCH = bool(SERPER_API_KEY)                                 # live web search
HAS_WEATHER    = bool(OPENWEATHER_API_KEY)                            # weather + AQI alerts
HAS_NUTRITION  = bool(USDA_API_KEY)                                   # live nutrition lookup
HAS_NEWS       = bool(NEWSAPI_KEY)                                    # health news feed
HAS_SMS        = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER)  # SMS

# Default city used for weather/AQI when the user doesn't specify one
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Delhi")

# ─────────────────────────────────────────────
# MODEL SETTINGS
# ─────────────────────────────────────────────
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ─────────────────────────────────────────────
# APP SETTINGS
# ─────────────────────────────────────────────
APP_NAME    = "MediMate AI"
APP_TAGLINE = "Your friendly, always-on health companion"
VERSION     = "3.0"

# Local data files
HISTORY_FILE   = os.getenv("HISTORY_FILE", "consultations.json")
REMINDERS_FILE = os.getenv("REMINDERS_FILE", "reminders.json")

# Supported languages the agent can reply in
SUPPORTED_LANGUAGES = ["English", "Hindi", "Hinglish", "Spanish", "French", "Arabic"]

# ─────────────────────────────────────────────
# EMERGENCY NUMBERS  (by country)
# 112 is the universal EU/India emergency number.
# ─────────────────────────────────────────────
EMERGENCY_NUMBERS = {
    "India":         {"ambulance": "108", "general": "112", "women": "1091", "mental_health": "1800-599-0019 (KIRAN)"},
    "USA":           {"ambulance": "911", "general": "911", "poison": "1-800-222-1222", "mental_health": "988"},
    "UK":            {"ambulance": "999", "general": "999", "non_emergency": "111", "mental_health": "116 123 (Samaritans)"},
    "Australia":     {"ambulance": "000", "general": "000", "mental_health": "13 11 14 (Lifeline)"},
    "Canada":        {"ambulance": "911", "general": "911", "mental_health": "988"},
    "UAE":           {"ambulance": "998", "general": "999", "police": "999"},
    "International": {"ambulance": "112", "general": "112"},
}

DEFAULT_COUNTRY = os.getenv("DEFAULT_COUNTRY", "India")


def emergency_numbers_for(country: str = DEFAULT_COUNTRY) -> dict:
    """Return the emergency numbers dict for a country (falls back to International)."""
    return EMERGENCY_NUMBERS.get(country, EMERGENCY_NUMBERS["International"])


def status_banner() -> str:
    """A short human-readable line describing which features are live."""
    def dot(on: bool) -> str:
        return "🟢" if on else "⚪"
    return (f"{dot(HAS_LLM)} AI  {dot(HAS_WEB_SEARCH)} Web  "
            f"{dot(HAS_WEATHER)} Weather  {dot(HAS_NUTRITION)} Nutrition  "
            f"{dot(HAS_NEWS)} News  {dot(HAS_SMS)} SMS")


def feature_status() -> dict:
    """Detailed on/off map of every optional feature (for a status table)."""
    # ML models = trained files on disk (no API key needed — real local ML!)
    _ml_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models")
    has_ml = (os.path.exists(os.path.join(_ml_dir, "diabetes_model.joblib"))
              and os.path.exists(os.path.join(_ml_dir, "heart_model.joblib")))
    # v2 models (stroke + breast cancer) — alag flag taaki purane trained
    # setups me bhi status sahi dikhe
    has_ml_v2 = (os.path.exists(os.path.join(_ml_dir, "stroke_model.joblib"))
                 and os.path.exists(os.path.join(_ml_dir, "breast_model.joblib")))
    return {
        "AI brain (Groq)":       HAS_LLM,
        "Web search (Serper)":   HAS_WEB_SEARCH,
        "Weather + AQI":         HAS_WEATHER,
        "Nutrition (USDA)":      HAS_NUTRITION,
        "Health news":           HAS_NEWS,
        "SMS reminders (Twilio)": HAS_SMS,
        "ML risk models 🧠":     has_ml,
        "ML v2 (stroke+cancer) 🧠": has_ml_v2,
    }
