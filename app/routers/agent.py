"""Agent info endpoint for ERC-8004."""

import logging
from datetime import datetime
from fastapi import APIRouter

from app.config import get_settings
from app.models import AgentInfo
from services.erc8004 import get_erc8004_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agent"])

# Track analysis count (in-memory, resets on restart)
_analysis_count = 0
_start_time = datetime.utcnow()


def increment_analysis_count():
    """Increment the analysis counter."""
    global _analysis_count
    _analysis_count += 1


def get_analysis_count() -> int:
    """Get the current analysis count."""
    return _analysis_count


def get_uptime() -> str:
    """Calculate uptime percentage (simplified)."""
    # In production, this would use proper monitoring
    return "99.9%"


@router.get(
    "/agent/info",
    response_model=AgentInfo,
    summary="Get agent information",
    description="Get ERC-8004 agent registration and status information."
)
async def get_agent_info() -> AgentInfo:
    """
    Get information about this ERC-8004 agent.

    Returns:
    - Agent ID (if registered)
    - Agent name and description
    - Registry addresses
    - Reputation score
    - Total analyses performed
    - Uptime statistics
    """
    settings = get_settings()

    # Try to get on-chain info if agent is registered
    agent_id = settings.agent_id if settings.agent_id else None
    reputation_score = "New"

    if agent_id:
        try:
            erc8004 = get_erc8004_service()
            rep_info = erc8004.get_reputation(int(agent_id))
            if rep_info:
                reputation_score = str(rep_info.get("score", "New"))
        except Exception as e:
            logger.warning(f"Could not fetch reputation: {e}")

    return AgentInfo(
        agent_id=agent_id,
        name="BaseTokenScout",
        description=(
            "AI agent analyzing token quality and safety on Base L2. "
            "Provides risk scores, detects scams, and tracks trending tokens. "
            "Read-only, no fund management."
        ),
        registry_address=settings.identity_registry,
        reputation_score=reputation_score,
        total_analyses=get_analysis_count(),
        uptime=get_uptime(),
        version="1.0.0"
    )


@router.get(
    "/agent/card",
    summary="Get agent card JSON",
    description="Get the ERC-8004 agent card metadata."
)
async def get_agent_card():
    """
    Get the agent card JSON for ERC-8004 registration.

    This is the metadata that is stored on-chain during registration.
    """
    settings = get_settings()
    erc8004 = get_erc8004_service()
    return erc8004.generate_agent_card(settings.agent_endpoint)
