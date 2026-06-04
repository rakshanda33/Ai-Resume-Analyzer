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
    Handles markdown code fences and extra whitespace.

    Args:
        raw_text: Raw string response from LLM

    Returns:
        Parsed dictionary

    Raises:
        ValueError: If no valid JSON found
    """
    # Remove markdown code fences
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()

    # Extract first complete JSON object
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("AI returned no valid JSON. Try again.")

    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse AI response as JSON: {e}")


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