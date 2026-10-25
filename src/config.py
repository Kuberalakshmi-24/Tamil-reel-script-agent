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

# Model Configurations
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

DELIVERABLES_DIR = ROOT_DIR / "deliverables"
DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
