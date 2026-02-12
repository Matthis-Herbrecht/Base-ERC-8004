"""Token analysis router."""

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import TokenAnalysis, ErrorResponse
from services.token_analyzer import TokenAnalyzer

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/analyze/{token_address}",
    response_model=TokenAnalysis,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Analyze a token",
    description="Perform comprehensive analysis of an ERC-20 token on Ethereum"
)
@limiter.limit("10/minute")
async def analyze_token(request: Request, token_address: str):
    """
    Analyze an ERC-20 token and return quality score with risk assessment.

    - **token_address**: The Ethereum address of the ERC-20 token contract
    """
    # Validate address format
    if not token_address.startswith("0x") or len(token_address) != 42:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_address",
                "message": "Invalid Ethereum address format",
                "details": "Address must be 42 characters starting with 0x"
            }
        )

    try:
        analyzer = TokenAnalyzer()
        result = await analyzer.analyze(token_address)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "token_not_found",
                "message": str(e),
                "details": None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_failed",
                "message": "Failed to analyze token",
                "details": str(e)
            }
        )
