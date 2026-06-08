# api/routes/analyze.py
from fastapi import APIRouter
from api.models.request import AnalyzeRequest
from api.models.response import AnalysisResponse
from analyzer import analyze_resume
from logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["Resume Analysis"]
)


@router.post(
    "",
    response_model=AnalysisResponse,
    summary="Analyze a resume",
    description=(
        "Send resume text extracted from a PDF. "
        "Returns score (0-100), verdict, strengths, weaknesses, "
        "improvement tips, and ATS issues."
    ),
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Resume text too short or empty"},
        429: {"description": "Gemini API rate limit reached"},
        500: {"description": "Internal server error"},
    }
)
async def analyze(request: AnalyzeRequest) -> AnalysisResponse:
    logger.info(f"POST /analyze | text_length={len(request.resume_text)} chars")

    result = analyze_resume(request.resume_text)
    return AnalysisResponse(**result)