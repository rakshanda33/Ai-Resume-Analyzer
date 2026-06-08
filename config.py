# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str   = "gemini-2.5-flash"
TEMPERATURE: float  = 0.3    # low = consistent structured output
MAX_TOKENS: int     = 2048

# ── PDF ───────────────────────────────────────────────
MAX_PDF_PAGES: int      = 10   # cost + abuse protection
MIN_RESUME_CHARS: int   = 100  # catch empty/image PDFs

# ── App ───────────────────────────────────────────────
APP_TITLE: str   = "AI Resume Analyzer"
APP_ICON: str    = "📄"
APP_VERSION: str = "2.0.0"

# ── API ───────────────────────────────────────────────
API_HOST: str    = "0.0.0.0"
API_PORT: int    = 8000
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

