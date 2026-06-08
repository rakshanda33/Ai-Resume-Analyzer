# api/models/response.py
"""
Pydantic response models for the AI Resume Analyzer API.

These models define exactly what each endpoint returns.

Benefits:
1. Auto-generates Swagger documentation (visible at /docs)
2. FastAPI validates outgoing data matches the schema
3. Clients know exactly what fields to expect — always
4. Extra fields from Gemini are automatically filtered out
"""
from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    """
    Response model for POST /analyze

    Every field here maps to a key in the dict returned by analyze_resume()
    in analyzer.py. If analyzer.py returns extra keys, they are ignored.
    If it is missing a key, FastAPI raises a 500 error caught by our handler.
    """
    score:            int          # 0–100 resume quality score
    verdict:          str          # "Hire" / "Strong Maybe" / "Maybe" / "No Hire"
    summary:          str          # 2–3 sentence overall assessment
    strengths:        list[str]    # specific evidence-based strengths
    weaknesses:       list[str]    # specific weaknesses
    improvements:     list[str]    # actionable improvement tips
    missing_sections: list[str]    # sections absent from the resume
    skills_found:     list[str]    # detected technical/soft skills
    ats_issues:       list[str]    # ATS compatibility problems
    cached:           bool = False # True if result came from cache, not Gemini


class ATSResponse(BaseModel):
    """
    Response model for POST /ats-match
    """
    ats_score:        int          # 0–100 match percentage
    matched_keywords: list[str]    # keywords in both resume and JD
    missing_keywords: list[str]    # important JD keywords absent from resume
    match_summary:    str          # 2-sentence fit assessment
    recommendation:   str          # e.g. "Tailor resume" / "Strong match"


class BulletResponse(BaseModel):
    """
    Response model for POST /rewrite-bullet
    """
    rewrites: list[str]            # 3 stronger versions of the bullet


class HealthResponse(BaseModel):
    """
    Response model for GET /health
    Used by Docker, deployment platforms, and load balancers
    to verify the API is alive before routing traffic.
    """
    status:  str    # always "healthy" if the API is running
    version: str    # app version from config.py
    message: str    # human-readable status description


class ErrorResponse(BaseModel):
    """
    Standardised error response.
    Every error in the API returns this same shape — never a raw Python
    exception or HTML page.

    Used in:
    - api/middleware/errorhandler.py
    - Swagger docs (shown as possible error responses)
    """
    error:  str       # human-readable error message
    detail: str = ""  # optional technical detail for debugging
    code:   int = 500 # HTTP status code mirrored in the body