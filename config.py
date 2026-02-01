"""Configuration loaded from .env and environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"

# Calendar
CALENDAR_IDS = [
    cid.strip()
    for cid in os.getenv("CALENDAR_IDS", "primary").split(",")
    if cid.strip()
]
TIMEZONE = (os.getenv("TIMEZONE") or "America/New_York").strip() or "America/New_York"

# Language and LLM
LANGUAGE = (os.getenv("LANGUAGE") or "cs").strip().lower() or "cs"
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()

# TTS (derive from language: cs -> Czech, en -> English)
TTS_LANG = "cs-CZ" if LANGUAGE == "cs" else "en-US"
TTS_VOICE = "cs-CZ-Wavenet-B" if LANGUAGE == "cs" else "en-US-Neural2-D"

# RSS
RSS_BASE_URL = os.getenv("RSS_BASE_URL", "").rstrip("/")
RSS_SHOW_TITLE = "My Weekly Brief"
RSS_SHOW_DESCRIPTION = "A private weekly brief of your upcoming calendar events."
