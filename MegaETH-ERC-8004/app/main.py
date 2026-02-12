"""MegaETHTokenScout - ERC-8004 AI Agent for MegaETH token analysis."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.routers import analyze, trending

app = FastAPI(
    title="MegaETHTokenScout",
    description="ERC-8004 AI Agent for analyzing ERC-20 token quality and risk on MegaETH",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(trending.router, prefix="/api", tags=["Trending"])


@app.get("/", include_in_schema=False)
async def root():
    """Serve the landing page."""
    return FileResponse(static_path / "index.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "MegaETHTokenScout", "chain": "MegaETH"}
