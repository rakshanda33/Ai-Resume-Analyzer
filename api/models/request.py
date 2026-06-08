# api/models/request.py
"""
Pydantic request models for the AI Resume Analyzer API.

These models define exactly what input each endpoint accepts.
FastAPI reads these automatically — if the request does not match,
it returns a 422 error before your route handler runs.

Why this matters:
- Invalid data never reaches Gemini (saves API credits)
- Every validation error has a clear, user-readable message
- Zero manual if/else validation code in your routes
"""
from pydantic import BaseModel, field_validator


class AnalyzeRequest(BaseModel):
    """
    Input model for POST /analyze

    Fields:
        resume_text: Plain text extracted from the resume PDF.
                     Minimum 100 characters to ensure meaningful content.
                     Capped at 4000 characters to control Gemini token usage.
    """
    resume_text: str

    @field_validator("resume_text")
    @classmethod
    def validate_resume_text(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 100:
            raise ValueError(
                "Resume text is too short. "
                "Minimum 100 characters required. "
                "Your PDF may be image-based (scanned) or empty."
            )

        # Hard cap — never send more than 4000 characters to Gemini
        # Prevents accidental large requests and controls cost
        return value[:4000]


class ATSRequest(BaseModel):
    """
    Input model for POST /ats-match

    Fields:
        resume_text:      Plain text of the resume (same rules as above)
        job_description:  The job posting text to compare against.
                          Minimum 50 characters to be meaningful.
                          Capped at 2000 characters.
    """
    resume_text: str
    job_description: str

    @field_validator("resume_text")
    @classmethod
    def validate_resume(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 100:
            raise ValueError(
                "Resume text too short. Minimum 100 characters required."
            )
        return value[:3000]

    @field_validator("job_description")
    @classmethod
    def validate_job_description(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 50:
            raise ValueError(
                "Job description too short. "
                "Minimum 50 characters required. "
                "Please paste the full job posting."
            )
        return value[:2000]


class BulletRequest(BaseModel):
    """
    Input model for POST /rewrite-bullet

    Fields:
        bullet: A single resume bullet point to be rewritten.
                Cannot be empty. Max 300 characters.
    """
    bullet: str

    @field_validator("bullet")
    @classmethod
    def validate_bullet(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Bullet point cannot be empty.")

        if len(value) > 300:
            raise ValueError(
                "Bullet point too long. "
                "Keep it under 300 characters for best results."
            )
        return value