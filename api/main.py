# api/main.py
"""
FastAPI application entry point for AI Resume Analyzer.

This file wires together:
- CORS middleware        (allows Streamlit to call this API)
- Exception handlers     (all errors return clean JSON)
- Route modules          (analyze, ats, rewrite)
- Health check           (for deployment platforms)

Start the server with:
    uvicorn api.main:app --reload --port 8000

Then visit:
    http://localhost:8000/docs     ← interactive Swagger UI
    http://localhost:8000/health   ← health check
    http://localhost:8000/redoc    ← alternative API docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import analyze, ats, rewrite
from api.middleware.errorhandler import (
    handle_runtime_error,
    handle_value_error,
    handle_generic_exception,
)
from api.models.response import HealthResponse
from config import APP_VERSION
from logger_config import get_logger

logger = get_logger(__name__)


# ── Create FastAPI application ────────────────────────────────────────
# All parameters here appear in Swagger UI at /docs
app = FastAPI(
    title="AI Resume Analyzer API",
    description=(
        "## AI-Powered Resume Analysis\n\n"
        "REST API built with **FastAPI** and **Google Gemini 2.5 Flash**.\n\n"
        "### Available Features\n"
        "- 📊 Resume scoring and analysis (0–100)\n"
        "- 🎯 ATS keyword matching against job descriptions\n"
        "- ✏️ Resume bullet point rewriting\n\n"
        "### How to use\n"
        "1. Use `/analyze` to get full resume analysis\n"
        "2. Use `/ats-match` to compare resume against a job description\n"
        "3. Use `/rewrite-bullet` to improve weak bullet points\n\n"
        "*Built by Rakshanda Noor — 50-Day AI Engineering Bootcamp*"
    ),
    version=APP_VERSION,
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc UI (alternative)
    openapi_url="/openapi.json" # Raw OpenAPI schema
)


# ── CORS Middleware ───────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
#
# Problem without CORS:
#   Streamlit runs on http://localhost:8501
#   FastAPI runs on http://localhost:8000
#   Different ports = different "origins" in browser security model
#   Browser BLOCKS the request with: "CORS policy: No Access-Control-Allow-Origin"
#
# Solution: Tell FastAPI to allow requests from Streamlit's origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",      # Streamlit dev
        "http://127.0.0.1:8501",      # Streamlit dev (alternate)
        "http://localhost:8000",      # API self-calls
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],    # only methods we actually use
    allow_headers=["*"],
)


# ── Exception Handlers ────────────────────────────────────────────────
# Register global handlers from errorhandler.py
# Order matters — more specific exceptions first
app.add_exception_handler(RuntimeError, handle_runtime_error)
app.add_exception_handler(ValueError,   handle_value_error)
app.add_exception_handler(Exception,    handle_generic_exception)


# ── Include Route Modules ─────────────────────────────────────────────
# Each router brings its endpoints into the main app
# The prefix from each router file is preserved:
#   analyze.router has prefix="/analyze" → POST /analyze
#   ats.router has prefix="/ats-match"   → POST /ats-match
#   rewrite.router has prefix="/rewrite-bullet" → POST /rewrite-bullet
app.include_router(analyze.router)
app.include_router(ats.router)
app.include_router(rewrite.router)


# ── Health Check Endpoint ─────────────────────────────────────────────
# GET /health is a standard endpoint in every production API.
# It is used by:
# - Docker HEALTHCHECK instruction
# - Render / Railway deployment platforms
# - Load balancers to verify the service is alive
# - Your Streamlit sidebar to show API status indicator
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="API health check",
    description="Returns the current health status of the API. No authentication required."
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        message="AI Resume Analyzer API is running successfully."
    )


# ── Root Endpoint ─────────────────────────────────────────────────────
# Visiting http://localhost:8000 redirects to docs
@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse({
        "message": "AI Resume Analyzer API",
        "docs":    "http://localhost:8000/docs",
        "health":  "http://localhost:8000/health",
        "version": APP_VERSION
    })


# ── Startup + Shutdown Events ─────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"AI Resume Analyzer API v{APP_VERSION} started")
    logger.info("Swagger UI  → http://localhost:8000/docs")
    logger.info("Health check→ http://localhost:8000/health")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("AI Resume Analyzer API shutting down")