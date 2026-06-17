# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str   = "gemini-2.5-flash"
TEMPERATURE: float  = 0.3    # low = consistent structured output

# gemini-2.5-flash is a "thinking" model: by default it spends an internal,
# invisible reasoning budget BEFORE writing the visible answer, and those
# thinking tokens are deducted from max_output_tokens (not separate from it).
# If max_output_tokens is too low, thinking alone can consume the entire
# budget, leaving response.text empty/None/truncated -> "no valid JSON".
# THINKING_BUDGET = 0 disables that hidden reasoning phase entirely for this
# task (resume scoring doesn't need multi-step reasoning), so the full token
# budget goes to the actual JSON output.
THINKING_BUDGET: int = 0
MAX_TOKENS: int      = 4096   # raised: headroom for the full 9-field schema

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