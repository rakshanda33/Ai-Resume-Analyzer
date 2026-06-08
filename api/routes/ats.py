# api/routes/ats.py
"""
Route handler for POST /ats-match — ATS Keyword Match endpoint.

Compares a resume against a job description and returns:
- Match percentage (0-100)
- Keywords found in both documents
- Important keywords missing from the resume
- A recommendation on whether to tailor the resume
"""
from fastapi import APIRouter
from api.models.request import ATSRequest
from api.models.response import ATSResponse
from analyzer import check_ats_match
from logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ats-match",
    tags=["ATS Matching"]
)


@router.post(
    "",
    response_model=ATSResponse,
    summary="ATS keyword match score",
    description=(
        "Compare a resume against a job description. "
        "Returns a match percentage and identifies keywords present "
        "in the job description but missing from the resume. "
        "Use this to tailor your resume for a specific role."
    ),
    responses={
        200: {"description": "ATS match score calculated"},
        400: {"description": "Resume or job description too short"},
        429: {"description": "Gemini API rate limit reached"},
        500: {"description": "Internal server error"},
    }
)
async def ats_match(request: ATSRequest) -> ATSResponse:
    """
    ATS keyword matching endpoint.

    By the time this runs:
    - resume_text is validated (min 100 chars, max 3000)
    - job_description is validated (min 50 chars, max 2000)
    """
    logger.info(
        f"POST /ats-match | "
        f"resume_length={len(request.resume_text)} chars | "
        f"jd_length={len(request.job_description)} chars"
    )

    # check_ats_match() is unchanged from your existing analyzer.py
    result = check_ats_match(request.resume_text, request.job_description)

    return ATSResponse(**result)