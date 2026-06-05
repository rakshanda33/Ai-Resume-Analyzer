# analyzer.py
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE
from prompts import RESUME_ANALYSIS_PROMPT, ATS_MATCH_PROMPT, BULLET_REWRITE_PROMPT
from utils import parse_json_from_llm

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY not found. "
        "Create a .env file with: GEMINI_API_KEY=your_key_here"
    )

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    generation_config={"temperature": TEMPERATURE}
)


def _call_gemini(prompt: str) -> str:
    """
    Internal helper: call Gemini and return raw text.
    Centralises API call so error handling lives in one place.
    """
    try:
        response = model.generate_content(prompt)
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

        if "api key" in error_msg or "invalid" in error_msg:
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

def analyze_resume(resume_text: str) -> dict:
    """
    Analyze a resume using Gemini.

    Args:
        resume_text: Plain text content of the resume

    Returns:
        dict with keys: score, verdict, summary, strengths,
                        weaknesses, improvements, missing_sections,
                        skills_found, ats_issues
    """
    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_text=resume_text[:4000]   # token cap
    )
    raw = _call_gemini(prompt)
    return parse_json_from_llm(raw)


def check_ats_match(resume_text: str, job_description: str) -> dict:
    """
    Compare resume against a job description using ATS logic.

    Returns:
        dict with ats_score, matched_keywords,
              missing_keywords, match_summary, recommendation
    """
    prompt = ATS_MATCH_PROMPT.format(
        resume_text=resume_text[:3000],
        job_description=job_description[:2000]
    )
    raw = _call_gemini(prompt)
    return parse_json_from_llm(raw)


def rewrite_bullet(bullet: str) -> list[str]:
    """
    Rewrite a weak resume bullet into 3 stronger versions.

    Returns:
        List of 3 rewritten bullet strings
    """
    prompt = BULLET_REWRITE_PROMPT.format(bullet=bullet)
    raw = _call_gemini(prompt)
    result = parse_json_from_llm(raw)
    return result.get("rewrites", [])