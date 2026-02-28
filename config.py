"""
Citizenship Quiz Buddy - Global Configuration
Loads all keys from .env with fallback defaults to prevent crashes.
"""
from dotenv import load_dotenv
import os

load_dotenv()

# ----- API Keys -----
XAI_API_KEY = os.getenv("XAI_API_KEY", "TEST_XAI_API_KEY_123456")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4")

# ----- Path Configuration -----
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PDF_PATH = os.path.join(DATA_DIR, "discover_canada.pdf")
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vectorstore")
SCORE_LOG_PATH = os.path.join(DATA_DIR, "score_log.json")
WRONG_ANSWERS_PATH = os.path.join(DATA_DIR, "wrong_answers.json")

# ----- Quiz Configuration -----
QUESTIONS_PER_QUIZ = 20
PASSING_SCORE = 0.75  # 75% to pass
MAX_ATTEMPTS = 5

# ----- Sandbox Mode -----
SANDBOX_MODE = XAI_API_KEY.startswith("TEST_")

def is_sandbox():
    """Returns True when using mock keys — tool modules should return mock data."""
    return SANDBOX_MODE
