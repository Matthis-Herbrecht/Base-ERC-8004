"""Configuration for MegaETHTokenScout."""

import json
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # MegaETH RPC
    megaeth_rpc_url: str = "https://carrot.megaeth.com/rpc"

    # ERC-8004 Registry addresses
    identity_registry: str = "0x0000000000000000000000000000000000000000"
    reputation_registry: str = "0x0000000000000000000000000000000000000000"

    # Agent configuration
    agent_endpoint: str = "https://megaethtokenscout.onrender.com"

    # Private key for on-chain registration (optional)
    private_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# ERC-8004 ABIs
IDENTITY_REGISTRY_ABI = [
    {
        "inputs": [{"name": "metadataURI", "type": "string"}],
        "name": "register",
        "outputs": [{"name": "agentId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "name": "getAgent",
        "outputs": [
            {"name": "owner", "type": "address"},
            {"name": "metadataURI", "type": "string"},
            {"name": "isActive", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

REPUTATION_REGISTRY_ABI = [
    {
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "name": "getReputation",
        "outputs": [
            {"name": "score", "type": "uint256"},
            {"name": "totalInteractions", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ERC-20 ABI for basic token interactions
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]
