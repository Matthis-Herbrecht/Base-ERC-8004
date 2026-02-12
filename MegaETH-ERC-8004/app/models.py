"""Pydantic models for MegaETHTokenScout API."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification for tokens."""
    SCAM = "scam"           # Score < 30
    HIGH_RISK = "high_risk"  # Score 30-50
    MODERATE = "moderate"    # Score 50-70
    QUALITY = "quality"      # Score > 70


class TokenMetrics(BaseModel):
    """Metrics for token analysis."""
    holders: int = Field(description="Number of token holders")
    volume_24h_usd: float = Field(description="24-hour trading volume in USD")
    liquidity_usd: float = Field(description="Total liquidity in USD")
    contract_age_days: int = Field(description="Age of contract in days")
    is_verified: bool = Field(description="Whether contract is verified on MegaETH Explorer")
    top_holder_percentage: float = Field(description="Percentage held by top holder")


class RedFlag(BaseModel):
    """Red flag detected during analysis."""
    code: str = Field(description="Red flag code")
    description: str = Field(description="Human-readable description")
    severity: str = Field(description="Severity: low, medium, high")


class TokenAnalysis(BaseModel):
    """Complete token analysis response."""
    address: str = Field(description="Token contract address")
    name: str = Field(description="Token name")
    symbol: str = Field(description="Token symbol")
    decimals: int = Field(description="Token decimals")
    total_supply: str = Field(description="Total token supply")
    score: int = Field(ge=0, le=100, description="Quality score 0-100")
    risk_level: RiskLevel = Field(description="Risk level classification")
    metrics: TokenMetrics = Field(description="Token metrics")
    red_flags: List[RedFlag] = Field(default=[], description="Detected red flags")
    analysis: str = Field(description="AI-generated analysis summary")
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    market_cap_usd: Optional[float] = Field(None, description="Market cap in USD")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class TrendingToken(BaseModel):
    """Token in trending list."""
    address: str
    name: str
    symbol: str
    score: int
    risk_level: RiskLevel
    volume_24h_usd: float
    price_change_24h: Optional[float] = None


class TrendingResponse(BaseModel):
    """Response for trending tokens endpoint."""
    tokens: List[TrendingToken]
    updated_at: datetime


class AgentInfo(BaseModel):
    """ERC-8004 agent information."""
    agent_id: Optional[str] = Field(description="On-chain agent ID")
    name: str = Field(description="Agent name")
    description: str = Field(description="Agent description")
    registry_address: str = Field(description="Identity registry address")
    reputation_score: str = Field(description="Agent reputation score")
    total_analyses: int = Field(description="Total number of analyses performed")
    uptime: str = Field(description="Agent uptime percentage")
    version: str = Field(description="Agent version")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[str] = Field(None, description="Additional details")
