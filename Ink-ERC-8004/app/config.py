"""Configuration settings for InkTokenScout."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Blockchain - Ink Mainnet
    ink_rpc_url: str = "https://rpc-gel.inkonchain.com"

    # No separate API key needed - Ink uses Blockscout which is free
    blockscout_api_key: str = ""

    # Agent Owner
    private_key: str = ""
    agent_owner_address: str = ""

    # ERC-8004 Contracts (Ink mainnet - placeholder addresses)
    identity_registry: str = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
    reputation_registry: str = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"

    # Optional APIs
    coingecko_api_key: str = ""

    # Agent Configuration
    agent_name: str = "InkTokenScout"
    agent_endpoint: str = "https://inktokenscout.onrender.com"
    agent_id: str = ""

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # Cache TTL (seconds)
    cache_ttl: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


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

# Identity Registry ABI (ERC-8004)
IDENTITY_REGISTRY_ABI = [
    {
        "inputs": [
            {"name": "metadataURI", "type": "string"}
        ],
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
            {"name": "registeredAt", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "getAgentsByOwner",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Reputation Registry ABI (ERC-8004)
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
