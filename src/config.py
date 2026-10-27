"""Configuration and constants for the Tamil Reel Script Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Spoken speed calibration (~2.2 words per second for spoken Tamil/Tanglish)
WORD_COUNT_LIMITS = {
    30: {"min": 60, "max": 75, "target": 68},
    45: {"min": 95, "max": 110, "target": 102},
    60: {"min": 125, "max": 145, "target": 135},
}

# Standard Prompt Defaults
DEFAULT_PLATFORM = "Instagram Reels"
DEFAULT_DURATION = 30
DEFAULT_TONE = "conversational spoken Tamil"
DEFAULT_OBJECTIVE = "awareness"
DEFAULT_MODE = "full_script"

def _get_setting(key: str, default: str = "") -> str:
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default

# Model Configurations
LLM_PROVIDER = _get_setting("LLM_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = _get_setting("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = _get_setting("OPENAI_API_KEY", "")
GEMINI_API_KEY = _get_setting("GEMINI_API_KEY", "")

ANTHROPIC_MODEL = _get_setting("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
OPENAI_MODEL = _get_setting("OPENAI_MODEL", "gpt-4o")
GEMINI_MODEL = _get_setting("GEMINI_MODEL", "gemini-3.8-flash")

DELIVERABLES_DIR = ROOT_DIR / "deliverables"
DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
