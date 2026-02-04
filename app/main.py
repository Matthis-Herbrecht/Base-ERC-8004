"""
BaseTokenScout - ERC-8004 Token Analysis Agent

A read-only AI agent that analyzes token quality and safety on Base L2.
Provides risk scores, detects scams, and tracks trending tokens.

SECURITY: This agent is READ-ONLY. No automatic transactions.
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

# Get the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.models import HealthResponse
from app.routers import analyze, trending, agent
from app.routers.agent import increment_analysis_count
from app.routers.trending import add_to_trending_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("BaseTokenScout starting up...")
    settings = get_settings()
    logger.info(f"Connected to Base RPC: {settings.base_rpc_url}")
    logger.info(f"Identity Registry: {settings.identity_registry}")
    yield
    logger.info("BaseTokenScout shutting down...")


# Create FastAPI app
app = FastAPI(
    title="BaseTokenScout",
    description=(
        "ERC-8004 AI Agent for analyzing token quality and safety on Base L2.\n\n"
        "**Features:**\n"
        "- Token analysis with quality scores (0-100)\n"
        "- Risk level assessment (scam, high_risk, moderate, quality)\n"
        "- Red flag detection (honeypots, low liquidity, concentration)\n"
        "- Trending tokens tracking\n\n"
        "**Security:**\n"
        "- READ-ONLY agent - no automatic transactions\n"
        "- No fund management capabilities\n"
        "- Rate limited to prevent abuse"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Analysis", "description": "Token analysis endpoints"},
        {"name": "Trending", "description": "Trending tokens endpoints"},
        {"name": "Agent", "description": "ERC-8004 agent information"},
        {"name": "Health", "description": "Health check endpoints"},
    ]
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["GET"],  # Read-only API
    allow_headers=["*"],
)


# Middleware to track analyses and add to trending
@app.middleware("http")
async def track_analyses(request: Request, call_next):
    """Track successful analyses and add to trending cache."""
    response = await call_next(request)

    # Track successful analyses
    if (
        request.url.path.startswith("/analyze/")
        and response.status_code == 200
    ):
        increment_analysis_count()
        # Note: To add to trending cache, we'd need to capture the response body
        # which requires more complex middleware. For simplicity, trending is
        # populated separately.

    return response


# Mount static files
try:
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
except Exception as e:
    logger.warning(f"Static files directory not found: {e}")


# Include routers
app.include_router(analyze.router)
app.include_router(trending.router)
app.include_router(agent.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check if the API is healthy and running."
)
@limiter.limit("60/minute")
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
    description="Web interface for token analysis.",
    include_in_schema=False
)
async def root():
    """Serve the web interface."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get(
    "/api",
    tags=["Health"],
    summary="API info",
    description="API information and endpoints."
)
async def api_info():
    """API info endpoint."""
    settings = get_settings()
    return {
        "name": "BaseTokenScout",
        "description": "ERC-8004 AI Agent for token analysis on Base L2",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "/analyze/{token_address}",
            "trending": "/trending",
            "agent_info": "/agent/info",
            "agent_card": "/agent/card"
        },
        "registry": {
            "identity": settings.identity_registry,
            "reputation": settings.reputation_registry
        },
        "security": "READ-ONLY - No automatic transactions"
    }


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": str(exc.detail) if isinstance(exc.detail, str) else exc.detail.get("message", str(exc.detail)),
            "details": exc.detail.get("details") if isinstance(exc.detail, dict) else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
