"""Agent information router."""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import AgentInfo
from app.config import get_settings
from services.erc8004 import ERC8004Service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()


@router.get(
    "/agent",
    response_model=AgentInfo,
    summary="Get agent information",
    description="Get ERC-8004 agent metadata and status"
)
@limiter.limit("30/minute")
async def get_agent_info(request: Request):
    """
    Get information about this ERC-8004 AI agent.

    Returns agent metadata, reputation score, and operational statistics.
    """
    erc8004 = ERC8004Service()

    # Get reputation if agent is registered
    reputation = "N/A"
    if settings.agent_id:
        try:
            rep_data = await erc8004.get_reputation(int(settings.agent_id))
            reputation = str(rep_data.get("score", 0))
        except Exception:
            pass

    return AgentInfo(
        agent_id=settings.agent_id or None,
        name="EthereumTokenScout",
        description="AI agent for analyzing ERC-20 token quality and risk on Ethereum mainnet",
        registry_address=settings.identity_registry,
        reputation_score=reputation,
        total_analyses=0,
        uptime="99.9%",
        version="1.0.0"
    )


@router.get(
    "/agent/card",
    summary="Get agent card",
    description="Get ERC-8004 agent card metadata"
)
async def get_agent_card():
    """Get the agent's ERC-8004 metadata card."""
    erc8004 = ERC8004Service()
    return erc8004.generate_agent_card()
