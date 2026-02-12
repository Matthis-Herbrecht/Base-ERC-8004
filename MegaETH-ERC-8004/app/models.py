"""Pydantic models for MegaETHTokenScout."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RedFlag(BaseModel):
    """A risk indicator for a token."""
    description: str
    severity: str  # "low", "medium", "high", "critical"


class TokenMetrics(BaseModel):
    """Detailed metrics for a token."""
    holders: int = Field(ge=0, description="Number of token holders")
    liquidity_usd: float = Field(ge=0, description="Total liquidity in USD")
    volume_24h_usd: float = Field(ge=0, description="24-hour trading volume in USD")
    contract_age_days: int = Field(ge=0, description="Age of the contract in days")
    is_verified: bool = Field(description="Whether the contract is verified")
    top_holder_percentage: float = Field(ge=0, le=100, description="Percentage held by top holder")


class TokenAnalysis(BaseModel):
    """Complete token analysis result."""
    contract_address: str
    name: str
    symbol: str
    score: int = Field(ge=0, le=100, description="Quality score from 0-100")
    risk_level: RiskLevel
    metrics: TokenMetrics
    red_flags: List[RedFlag] = []
    analysis: str = Field(description="Human-readable analysis summary")
    price_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class TrendingToken(BaseModel):
    """A trending token entry."""
    contract_address: str
    name: str
    symbol: str
    score: int
    volume_24h_usd: float


class TrendingResponse(BaseModel):
    """Response for trending tokens endpoint."""
    tokens: List[TrendingToken]
    updated_at: datetime


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[str] = None
