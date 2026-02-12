"""ERC-8004 agent registration and management service."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from web3 import Web3

from app.config import get_settings, IDENTITY_REGISTRY_ABI, REPUTATION_REGISTRY_ABI

logger = logging.getLogger(__name__)


class ERC8004Service:
    """Service for ERC-8004 agent operations."""

    def __init__(self):
        """Initialize ERC-8004 service."""
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.ink_rpc_url))

    def generate_agent_card(self) -> Dict[str, Any]:
        """Generate ERC-8004 agent card metadata."""
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareAgent",
            "name": "InkTokenScout",
            "description": "AI agent for analyzing ERC-20 token quality and risk on Ink blockchain",
            "version": "1.0.0",
            "capabilities": [
                {
                    "name": "token_analysis",
                    "description": "Analyze ERC-20 tokens for quality and risk assessment",
                    "endpoint": f"{self.settings.agent_endpoint}/api/analyze/{{token_address}}",
                    "method": "GET",
                    "parameters": {
                        "token_address": {
                            "type": "string",
                            "description": "Ink address of the ERC-20 token",
                            "required": True
                        }
                    }
                },
                {
                    "name": "trending_tokens",
                    "description": "Get list of trending tokens",
                    "endpoint": f"{self.settings.agent_endpoint}/api/trending",
                    "method": "GET"
                }
            ],
            "pricing": {
                "model": "free",
                "rateLimit": "10 requests/minute"
            },
            "contact": {
                "url": self.settings.agent_endpoint
            },
            "chain": {
                "name": "Ink",
                "chainId": 57073
            }
        }

    def save_agent_card(self, path: Optional[str] = None) -> str:
        """Save agent card to file."""
        if path is None:
            path = Path(__file__).parent.parent / "static" / "agent_card.json"

        card = self.generate_agent_card()
        with open(path, "w") as f:
            json.dump(card, f, indent=2)

        return str(path)

    async def register_agent(self, metadata_uri: str) -> Dict[str, Any]:
        """
        Register agent on-chain in the Identity Registry.

        Args:
            metadata_uri: URI pointing to agent metadata (e.g., IPFS or HTTPS)

        Returns:
            Transaction receipt with agent ID
        """
        if not self.settings.private_key:
            raise ValueError("Private key not configured")

        account = self.w3.eth.account.from_key(self.settings.private_key)

        # Get Identity Registry contract
        registry = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.settings.identity_registry),
            abi=IDENTITY_REGISTRY_ABI
        )

        # Build transaction
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_price = self.w3.eth.gas_price

        tx = registry.functions.register(metadata_uri).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gasPrice": gas_price,
            "gas": 200000,
            "chainId": 57073  # Ink mainnet
        })

        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.settings.private_key)

        # Handle web3.py version compatibility
        raw_tx = getattr(signed_tx, 'raw_transaction', None) or signed_tx.rawTransaction

        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        logger.info(f"Agent registered! TX: {tx_hash.hex()}")

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
            "status": "success" if receipt["status"] == 1 else "failed"
        }

    async def get_agent_info(self, agent_id: int) -> Dict[str, Any]:
        """Get agent information from registry."""
        registry = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.settings.identity_registry),
            abi=IDENTITY_REGISTRY_ABI
        )

        owner, metadata_uri, registered_at = registry.functions.getAgent(agent_id).call()

        return {
            "agent_id": agent_id,
            "owner": owner,
            "metadata_uri": metadata_uri,
            "registered_at": registered_at
        }

    async def get_reputation(self, agent_id: int) -> Dict[str, Any]:
        """Get agent reputation from registry."""
        registry = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.settings.reputation_registry),
            abi=REPUTATION_REGISTRY_ABI
        )

        score, total_interactions = registry.functions.getReputation(agent_id).call()

        return {
            "agent_id": agent_id,
            "score": score,
            "total_interactions": total_interactions
        }


def get_erc8004_service() -> ERC8004Service:
    """Get ERC-8004 service instance."""
    return ERC8004Service()
