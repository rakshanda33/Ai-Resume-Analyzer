# analyzer.py

import time

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE, THINKING_BUDGET, MAX_TOKENS
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

    Two settings here exist specifically to prevent
    "AI returned no valid JSON":

    1. thinking_config=ThinkingConfig(thinking_budget=THINKING_BUDGET)
       gemini-2.5-flash is a hybrid reasoning model. By default it spends
       an invisible "thinking" pass before writing the visible answer,
       and those thinking tokens are subtracted from max_output_tokens —
       they are NOT a separate budget. On a non-trivial prompt (e.g. a
       4000-character resume + a 9-field JSON schema), thinking can
       consume the entire token budget, leaving response.text as None
       or a short truncated fragment with no JSON in it at all.
       Setting thinking_budget=0 disables that hidden phase, so the
       full max_output_tokens budget goes to the actual JSON answer.

    2. response_mime_type="application/json"
       This tells Gemini's API layer itself to constrain output to
       valid JSON, as a second line of defense independent of the
       prompt text ("Return ONLY JSON" can still be ignored by the
       model; response_mime_type is enforced by the API).

    On top of that, this function retries transient server-side failures
    (HTTP 503 UNAVAILABLE, internal errors, timeouts) with exponential
    backoff, since those are usually momentary and resolve on their own.
    It does NOT retry MAX_TOKENS, quota/rate-limit, or auth errors —
    those are deterministic and retrying won't help.
    """

    MAX_RETRIES = 5
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_TOKENS,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=THINKING_BUDGET
                    ),
                    response_mime_type="application/json",
                ),
            )

            # Inspect finish_reason BEFORE trusting response.text.
            # If generation stopped because of MAX_TOKENS, response.text
            # can be None (fully truncated) or a partial fragment with no
            # closing brace — either way, treat it as a distinct,
            # diagnosable failure instead of letting it fall through to a
            # generic "no JSON" error. This is NOT retried: a higher
            # token budget or shorter input is needed, not another try.
            candidates = getattr(response, "candidates", None)
            finish_reason = None
            if candidates:
                finish_reason = getattr(candidates[0], "finish_reason", None)

            finish_reason_name = getattr(finish_reason, "name", finish_reason)

            if finish_reason_name == "MAX_TOKENS":
                raise RuntimeError(
                    "Gemini ran out of output tokens before finishing the "
                    "JSON response (finish_reason=MAX_TOKENS). "
                    "This usually means max_output_tokens is too low for "
                    "this prompt. Increase MAX_TOKENS in config.py, or "
                    "shorten the resume/job description input."
                )

            text = response.text

            if not text or not text.strip():
                raise RuntimeError(
                    "Gemini returned an empty response "
                    f"(finish_reason={finish_reason_name}). "
                    "This can happen due to safety filtering or an "
                    "unexpected empty generation. Try again."
                )

            return text

        except RuntimeError:
            # Re-raise our own diagnosable RuntimeErrors above unchanged
            # — they are deterministic (bad config/empty output), not
            # transient, so retrying would not help.
            raise

        except Exception as e:
            error_msg = str(e).lower()
            last_error = e

            # Only retry transient, server-side issues. Quota and auth
            # errors are deterministic and retrying wastes time/quota.
            is_retryable = (
                "503" in error_msg
                or "unavailable" in error_msg
                or "service is currently unavailable" in error_msg
                or "internal" in error_msg
                or "deadline exceeded" in error_msg
                or "timeout" in error_msg
            )

            if is_retryable and attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s
                print(
                    f"Gemini temporarily unavailable (attempt "
                    f"{attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                continue

            # Quota / rate limit — not retryable, fail fast with a clear message
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

            # API key problems — not retryable
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

            # Retryable error type, but we've exhausted all attempts
            if is_retryable:
                raise RuntimeError(
                    "⚠️ The Gemini service is temporarily unavailable "
                    f"after {MAX_RETRIES} attempts. Please try again in "
                    f"a few moments. (Last error: {e})"
                )

            # Anything else: unrecognised, non-retryable error
            raise RuntimeError(f"Gemini API Error: {e}")

    # Defensive fallback — the loop above always returns or raises,
    # but this satisfies static analysis and guards against a logic
    # change that accidentally falls through the loop silently.
    raise RuntimeError(
        f"Gemini API call failed after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


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