# analyzer.py

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE
from prompts import (
    RESUME_ANALYSIS_PROMPT,
    ATS_MATCH_PROMPT,
    BULLET_REWRITE_PROMPT,
)
from utils import parse_json_from_llm

# ──────────────────────────────────────────────────────────────
# Gemini Setup
# ──────────────────────────────────────────────────────────────

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY not found. "
        "Create a .env file with: GEMINI_API_KEY=your_key_here"
    )

client = genai.Client(api_key=GEMINI_API_KEY)


# ──────────────────────────────────────────────────────────────
# Gemini Helper
# ──────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    """
    Internal helper: call Gemini and return raw text.
    Centralises API call so error handling lives in one place.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=2048,
            ),
        )

        return response.text

    except Exception as e:
        error_msg = str(e).lower()

        if (
            "quota" in error_msg
            or "rate" in error_msg
            or "429" in error_msg
            or "resource_exhausted" in error_msg
        ):
            raise RuntimeError(
                """
⚠️ Gemini free quota exhausted.

Possible fixes:
• Wait 1-2 minutes and try again
• Create another Gemini API key
• Upgrade Gemini quota

The application is working correctly.
Google is temporarily blocking requests because the free limit was reached.
"""
            )

        if (
            "api key" in error_msg
            or "401" in error_msg
            or "403" in error_msg
            or "unauthenticated" in error_msg
            or "invalid" in error_msg
        ):
            raise RuntimeError(
                """
❌ Invalid Gemini API Key.

Check:
1. .env file exists
2. GEMINI_API_KEY is correct
3. Restart Streamlit after changing .env
"""
            )

        raise RuntimeError(f"Gemini API Error: {e}")


# ──────────────────────────────────────────────────────────────
# Resume Analysis
# ──────────────────────────────────────────────────────────────

def analyze_resume(resume_text: str) -> dict:
    """
    Analyze a resume using Gemini.
    """

    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_text=resume_text[:4000]
    )

    raw = _call_gemini(prompt)
    return parse_json_from_llm(raw)


# ──────────────────────────────────────────────────────────────
# ATS Matching
# ──────────────────────────────────────────────────────────────

def check_ats_match(
    resume_text: str,
    job_description: str
) -> dict:
    """
    Compare resume against a job description.
    """

    prompt = ATS_MATCH_PROMPT.format(
        resume_text=resume_text[:3000],
        job_description=job_description[:2000]
    )

    raw = _call_gemini(prompt)
    return parse_json_from_llm(raw)


# ──────────────────────────────────────────────────────────────
# Bullet Rewriter
# ──────────────────────────────────────────────────────────────

def rewrite_bullet(bullet: str) -> list[str]:
    """
    Rewrite a weak bullet into stronger versions.
    """

    prompt = BULLET_REWRITE_PROMPT.format(
        bullet=bullet
    )

    raw = _call_gemini(prompt)
    result = parse_json_from_llm(raw)

    return result.get("rewrites", [])