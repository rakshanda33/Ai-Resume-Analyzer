# api/middleware/errorhandler.py
"""
Global exception handlers for the AI Resume Analyzer API.

Problem this solves:
Without handlers: unhandled exception → FastAPI returns HTML 500 page
                  A mobile app or React frontend cannot parse HTML
                  The app breaks for the user with a confusing error

With handlers:    every exception → clean JSON response
                  {"error": "...", "detail": "...", "code": 429}
                  Any client can parse and handle this correctly

Three handlers are registered:
1. RuntimeError  → Gemini API failures (rate limit, bad key, server error)
2. ValueError    → PDF parsing failures (empty PDF, image-based PDF)
3. Exception     → catch-all for anything else (always returns JSON)
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from logger_config import get_logger

logger = get_logger(__name__)


async def handle_runtime_error(
    request: Request,
    exc: RuntimeError
) -> JSONResponse:
    """
    Handle RuntimeError raised by analyzer.py.

    analyzer.py raises RuntimeError for all Gemini API failures.
    We inspect the message to determine the correct HTTP status code.

    Mappings:
        "rate limit" / "429" / "⏱️"  → 429 Too Many Requests
        "api key" / "401" / "❌"      → 401 Unauthorized
        anything else                  → 500 Internal Server Error
    """
    error_message = str(exc)
    logger.warning(
        f"RuntimeError on {request.method} {request.url.path}: {error_message}"
    )

    # Determine correct HTTP status code from the error message content
    lower = error_message.lower()

    if any(keyword in lower for keyword in ["rate limit", "429", "quota", "⏱️"]):
        status_code = 429
    elif any(keyword in lower for keyword in ["api key", "401", "403", "❌", "invalid"]):
        status_code = 401
    else:
        status_code = 500

    return JSONResponse(
        status_code=status_code,
        content={
            "error":  error_message,
            "detail": "",
            "code":   status_code
        }
    )


async def handle_value_error(
    request: Request,
    exc: ValueError
) -> JSONResponse:
    """
    Handle ValueError raised by utils.py PDF extraction.

    utils.py raises ValueError when:
    - PDF is empty
    - PDF is image-based (scanned, cannot extract text)
    - PDF is corrupted

    These are all client errors → HTTP 400 Bad Request.
    The client sent us a bad file, not a server problem.
    """
    error_message = str(exc)
    logger.warning(
        f"ValueError on {request.method} {request.url.path}: {error_message}"
    )

    return JSONResponse(
        status_code=400,
        content={
            "error":  error_message,
            "detail": "Please upload a valid text-based PDF resume.",
            "code":   400
        }
    )


async def handle_generic_exception(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for any unhandled exception.

    This should rarely trigger in production.
    When it does, it means something unexpected happened.
    We log the full traceback (exc_info=True) for debugging
    but return a generic message to the client — never expose
    internal stack traces to users.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True  # logs full traceback to app_errors.log
    )

    return JSONResponse(
        status_code=500,
        content={
            "error":  "An internal server error occurred. Please try again.",
            "detail": str(exc),
            "code":   500
        }
    )