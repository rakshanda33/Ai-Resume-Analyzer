# api/routes/rewrite.py
"""
Route handler for POST /rewrite-bullet — Bullet Point Rewriter endpoint.

Takes a single weak resume bullet point and returns 3 stronger versions
using strong action verbs and quantified impact where possible.
"""
from fastapi import APIRouter
from api.models.request import BulletRequest
from api.models.response import BulletResponse
from analyzer import rewrite_bullet
from logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/rewrite-bullet",
    tags=["Bullet Rewriter"]
)


@router.post(
    "",
    response_model=BulletResponse,
    summary="Rewrite a resume bullet point",
    description=(
        "Submit a weak resume bullet point and receive 3 stronger "
        "AI-generated alternatives. Each version uses strong action verbs "
        "and quantified impact where possible. "
        "Example: 'Worked on website' → "
        "'Engineered responsive web application serving 5,000+ monthly users'"
    ),
    responses={
        200: {"description": "Rewrites generated successfully"},
        400: {"description": "Bullet point empty or too long"},
        429: {"description": "Gemini API rate limit reached"},
        500: {"description": "Internal server error"},
    }
)
async def rewrite(request: BulletRequest) -> BulletResponse:
    """
    Bullet point rewriter endpoint.

    By the time this runs:
    - bullet is validated (not empty, max 300 chars)
    """
    logger.info(
        f"POST /rewrite-bullet | "
        f"bullet='{request.bullet[:60]}{'...' if len(request.bullet) > 60 else ''}'"
    )

    # rewrite_bullet() is unchanged from your existing analyzer.py
    # It returns a list[str] of 3 rewritten versions
    rewrites = rewrite_bullet(request.bullet)

    return BulletResponse(rewrites=rewrites)