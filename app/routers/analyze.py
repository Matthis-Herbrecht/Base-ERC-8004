"""Token analysis endpoint."""

import logging
import re
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import TokenAnalysis, ErrorResponse
from services.token_analyzer import get_token_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis"])
limiter = Limiter(key_func=get_remote_address)

# Ethereum address regex
ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')


def validate_address(address: str) -> bool:
    """Validate Ethereum address format."""
    return bool(ADDRESS_PATTERN.match(address))


@router.get(
    "/analyze/{token_address}",
    response_model=TokenAnalysis,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid address"},
        404: {"model": ErrorResponse, "description": "Token not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Analysis failed"}
    },
    summary="Analyze a token",
    description="Analyze an ERC-20 token on Base and get a quality score, risk assessment, and metrics."
)
@limiter.limit("10/minute")
async def analyze_token(request: Request, token_address: str) -> TokenAnalysis:
    """
    Analyze a token on Base mainnet.

    - **token_address**: The ERC-20 token contract address (0x...)

    Returns comprehensive analysis including:
    - Quality score (0-100)
    - Risk level (scam, high_risk, moderate, quality)
    - Metrics (holders, liquidity, volume, age)
    - Red flags detected
    - AI-generated summary
    """
    # Validate address format
    if not validate_address(token_address):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_address",
                "message": f"Invalid Ethereum address format: {token_address}",
                "details": "Address must be a valid 40-character hex string starting with 0x"
            }
        )

    try:
        analyzer = get_token_analyzer()
        analysis = await analyzer.analyze(token_address)
        return analysis

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": str(e),
                "details": "The provided address may not be a valid ERC-20 token"
            }
        )
    except Exception as e:
        logger.exception(f"Analysis failed for {token_address}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_failed",
                "message": "Failed to analyze token",
                "details": str(e)
            }
        )
