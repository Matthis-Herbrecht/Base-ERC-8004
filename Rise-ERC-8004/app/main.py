"""Main FastAPI application for RiseTokenScout."""

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

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="RiseTokenScout",
    description="ERC-8004 AI Agent for analyzing ERC-20 tokens on Rise blockchain",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(trending.router, prefix="/api", tags=["Trending"])
app.include_router(agent.router, prefix="/api", tags=["Agent"])


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="ok", timestamp=datetime.utcnow(), version="1.0.0")


@app.get("/api", tags=["Info"])
async def api_info():
    return {"name": "RiseTokenScout", "version": "1.0.0", "chain": "rise", "chain_id": 11155931}
