"""Main FastAPI application for EthereumTokenScout."""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime

from app.config import get_settings
from app.models import HealthResponse
from app.routers import analyze, trending, agent

# Get absolute paths
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="EthereumTokenScout",
    description="ERC-8004 AI Agent for analyzing ERC-20 tokens on Ethereum mainnet",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(trending.router, prefix="/api", tags=["Trending"])
app.include_router(agent.router, prefix="/api", tags=["Agent"])


@app.get("/", include_in_schema=False)
async def root():
    """Serve the web interface."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/api", tags=["Info"])
async def api_info():
    """API information endpoint."""
    return {
        "name": "EthereumTokenScout",
        "version": "1.0.0",
        "description": "ERC-8004 AI Agent for Ethereum token analysis",
        "chain": "ethereum",
        "chain_id": 1,
        "endpoints": {
            "analyze": "/api/analyze/{token_address}",
            "trending": "/api/trending",
            "agent": "/api/agent",
        },
        "erc8004": {
            "identity_registry": settings.identity_registry,
            "reputation_registry": settings.reputation_registry,
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": str(exc),
            "details": None
        }
    )
