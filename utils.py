# utils.py
import io
import json
import re
from PyPDF2 import PdfReader
from config import MAX_PDF_PAGES, MIN_RESUME_CHARS


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from an uploaded PDF file.

    Args:
        pdf_file: Streamlit UploadedFile object

    Returns:
        Extracted text string

    Raises:
        ValueError: If PDF is empty, unreadable, or image-based
    """
    try:
        reader = PdfReader(pdf_file)
    except Exception as e:
        raise ValueError(f"Could not read PDF. Is the file corrupted? ({e})")

    if len(reader.pages) == 0:
        raise ValueError("This PDF has no pages.")

    pages = reader.pages[:MAX_PDF_PAGES]
    text_parts = []

    for page in pages:
        extracted = page.extract_text()
        if extracted:
            text_parts.append(extracted.strip())

    full_text = "\n".join(text_parts).strip()

    if len(full_text) < MIN_RESUME_CHARS:
        raise ValueError(
            "Could not extract enough text. "
            "Your PDF may be image-based (scanned). "
            "Please use a text-based PDF."
        )

    return full_text


def parse_json_from_llm(raw_text: str) -> dict:
    """
    Robustly parse JSON from LLM output.

    Handles:
    - raw_text being None or empty (e.g. fully truncated by MAX_TOKENS)
    - markdown code fences (```json ... ``` or plain ``` ... ```)
    - leading/trailing commentary text around the JSON object
    - a truncated/incomplete JSON object (gives a distinct error so the
      caller can tell "no JSON at all" apart from "JSON cut off mid-way")

    Args:
        raw_text: Raw string response from LLM (may be None)

    Returns:
        Parsed dictionary

    Raises:
        ValueError: If no valid JSON object can be recovered
    """
    # Guard first: a None or empty/whitespace-only response (e.g. when
    # Gemini hits MAX_TOKENS before emitting any visible text) must not
    # blow up re.sub() with a TypeError — it's a normal, expected failure
    # mode that should produce a clear, specific error message instead.
    if not raw_text or not raw_text.strip():
        raise ValueError(
            "AI returned an empty response (no text at all). "
            "This usually means the model's output was cut off before "
            "writing any content — check finish_reason/MAX_TOKENS, or "
            "try again."
        )

    # Remove markdown code fences (```json ... ``` or bare ``` ... ```)
    cleaned = re.sub(r"```(?:json)?", "", raw_text, flags=re.IGNORECASE).strip()

    if "{" not in cleaned:
        raise ValueError(
            "AI returned no valid JSON. Try again. "
            f"(Raw response had no '{{' character. "
            f"First 200 chars of response: {cleaned[:200]!r})"
        )

    # Extract the JSON object using a brace-balance scan rather than a
    # naive find("{") / rfind("}") pair. The naive version breaks if the
    # model's commentary text (before/after the JSON) itself contains a
    # stray "{" or "}", e.g. "Note: curly braces like this { sometimes
    # appear in prose." A balance scan finds the first syntactically
    # complete object — and if that candidate brace turns out to be a
    # stray one with no match, we move on and try the NEXT "{" in the
    # string rather than giving up immediately.
    best_truncated_preview = None

    for start in (i for i, c in enumerate(cleaned) if c == "{"):
        depth = 0
        end_index = -1
        in_string = False
        escape_next = False

        for i, char in enumerate(cleaned[start:], start=start):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_index = i + 1
                    break

        if end_index == -1:
            # This "{" never finds its matching close. Remember the first
            # such case (most likely candidate for "truncated mid-object")
            # in case every other "{" in the string also fails, but keep
            # trying other opening braces first.
            if best_truncated_preview is None:
                best_truncated_preview = cleaned[start:start + 200]
            continue

        candidate = cleaned[start:end_index]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # This brace produced a balanced-but-invalid object (e.g. a
            # stray brace in prose like "{note}"). Try the next "{".
            continue

    # No "{" in the entire string produced valid JSON.
    if best_truncated_preview is not None:
        raise ValueError(
            "AI response contained an incomplete/truncated JSON object "
            "(no matching closing brace found). This usually means the "
            "response was cut off — try increasing max_output_tokens, "
            "shortening the input, or trying again. "
            f"Preview: {best_truncated_preview!r}"
        )

    raise ValueError(
        "AI response contained '{' characters but no valid JSON object "
        "could be parsed from any of them. "
        f"First 300 chars of response: {cleaned[:300]!r}"
    )


def score_to_color(score: int) -> str:
    """Return a colour label based on resume score."""
    if score >= 75:
        return "green"
    elif score >= 50:
        return "orange"
    return "red"


def score_to_emoji(score: int) -> str:
    if score >= 75: return "🟢"
    elif score >= 50: return "🟡"
    return "🔴"