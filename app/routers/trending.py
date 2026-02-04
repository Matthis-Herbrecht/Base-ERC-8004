"""Trending tokens endpoint."""

import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Query

from app.models import TrendingResponse, TrendingToken, RiskLevel
from cachetools import TTLCache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Trending"])

# Cache for analyzed tokens (used for trending)
_analyzed_tokens_cache: TTLCache = TTLCache(maxsize=100, ttl=3600)  # 1 hour TTL


def add_to_trending_cache(analysis: dict) -> None:
    """Add an analyzed token to the trending cache."""
    key = analysis.get("address", "").lower()
    if key:
        _analyzed_tokens_cache[key] = {
            "address": analysis.get("address"),
            "name": analysis.get("name"),
            "symbol": analysis.get("symbol"),
            "score": analysis.get("score"),
            "risk_level": analysis.get("risk_level"),
            "volume_24h_usd": analysis.get("metrics", {}).get("volume_24h_usd", 0),
            "price_change_24h": None,  # Would need historical data
            "analyzed_at": datetime.utcnow()
        }


def get_trending_from_cache(limit: int = 10) -> List[TrendingToken]:
    """Get trending tokens from cache, sorted by volume."""
    tokens = list(_analyzed_tokens_cache.values())

    # Sort by volume (most active first)
    tokens.sort(key=lambda x: x.get("volume_24h_usd", 0), reverse=True)

    # Convert to TrendingToken models
    result = []
    for token in tokens[:limit]:
        try:
            result.append(TrendingToken(
                address=token["address"],
                name=token["name"],
                symbol=token["symbol"],
                score=token["score"],
                risk_level=RiskLevel(token["risk_level"]) if isinstance(token["risk_level"], str) else token["risk_level"],
                volume_24h_usd=token["volume_24h_usd"],
                price_change_24h=token.get("price_change_24h")
            ))
        except Exception as e:
            logger.error(f"Error creating TrendingToken: {e}")
            continue

    return result


# Well-known Base tokens for initial trending list
KNOWN_BASE_TOKENS = [
    {
        "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "name": "USD Coin",
        "symbol": "USDC",
        "score": 95,
        "risk_level": RiskLevel.QUALITY,
        "volume_24h_usd": 50000000,
    },
    {
        "address": "0x4200000000000000000000000000000000000006",
        "name": "Wrapped Ether",
        "symbol": "WETH",
        "score": 95,
        "risk_level": RiskLevel.QUALITY,
        "volume_24h_usd": 30000000,
    },
    {
        "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "name": "Dai Stablecoin",
        "symbol": "DAI",
        "score": 92,
        "risk_level": RiskLevel.QUALITY,
        "volume_24h_usd": 10000000,
    },
    {
        "address": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        "name": "Coinbase Wrapped Staked ETH",
        "symbol": "cbETH",
        "score": 90,
        "risk_level": RiskLevel.QUALITY,
        "volume_24h_usd": 5000000,
    },
]


@router.get(
    "/trending",
    response_model=TrendingResponse,
    summary="Get trending tokens",
    description="Get a list of recently analyzed tokens sorted by trading volume."
)
async def get_trending_tokens(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of tokens to return")
) -> TrendingResponse:
    """
    Get trending tokens on Base.

    Returns tokens that have been recently analyzed, sorted by 24h trading volume.
    If no tokens have been analyzed recently, returns well-known Base tokens.

    - **limit**: Maximum number of tokens to return (1-50, default 10)
    """
    # Get from cache first
    cached_tokens = get_trending_from_cache(limit)

    # If cache is empty, use known tokens
    if not cached_tokens:
        cached_tokens = [
            TrendingToken(**token) for token in KNOWN_BASE_TOKENS[:limit]
        ]

    return TrendingResponse(
        tokens=cached_tokens,
        updated_at=datetime.utcnow()
    )
