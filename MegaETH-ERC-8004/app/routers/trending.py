"""Trending tokens router."""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime

from app.models import TrendingResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/trending",
    response_model=TrendingResponse,
    summary="Get trending tokens",
    description="Get list of trending tokens on MegaETH (placeholder)"
)
@limiter.limit("10/minute")
async def get_trending(request: Request):
    """
    Get trending tokens on MegaETH.

    Note: This is a placeholder endpoint. Full implementation requires
    additional data sources for trending token discovery.
    """
    return TrendingResponse(
        tokens=[],
        updated_at=datetime.utcnow()
    )
