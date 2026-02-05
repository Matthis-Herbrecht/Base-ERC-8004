"""ERC-8004 Agent Registration Service."""

import json
import logging
from typing import Optional, Dict, Any

from web3 import Web3
from eth_account import Account

from app.config import get_settings, IDENTITY_REGISTRY_ABI, REPUTATION_REGISTRY_ABI

logger = logging.getLogger(__name__)


class ERC8004Service:
    """
    Service for ERC-8004 agent registration and management.

    IMPORTANT: This service only performs the one-time registration.
    All other operations are READ-ONLY.
    """

    def __init__(self):
        """Initialize ERC-8004 service."""
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.base_rpc_url))

        # Contract instances
        self.identity_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.settings.identity_registry),
            abi=IDENTITY_REGISTRY_ABI
        )
        self.reputation_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.settings.reputation_registry),
            abi=REPUTATION_REGISTRY_ABI
        )

    def generate_agent_card(self, endpoint_url: str) -> Dict[str, Any]:
        """
        Generate the agent card JSON for ERC-8004 registration.

        Args:
            endpoint_url: The base URL where the agent API is hosted

        Returns:
            Agent card dictionary
        """
        return {
            "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
            "name": "BaseTokenScout",
            "description": (
                "AI agent analyzing token quality and safety on Base L2. "
                "Provides risk scores, detects scams, and tracks trending tokens. "
                "Read-only, no fund management."
            ),
            "image": f"{endpoint_url}/static/logo.png",
            "services": [
                {
                    "name": "api",
                    "endpoint": f"{endpoint_url}/analyze"
                },
                {
                    "name": "docs",
                    "endpoint": f"{endpoint_url}/docs"
                },
                {
                    "name": "health",
                    "endpoint": f"{endpoint_url}/health"
                }
            ],
            "capabilities": [
                "token-analysis",
                "risk-assessment",
                "trend-detection"
            ],
            "tags": ["defi", "security", "analytics", "base"],
            "version": "1.0.0",
            "chain": {
                "id": 8453,
                "name": "Base"
            }
        }

    def save_agent_card(self, filepath: str, endpoint_url: str) -> str:
        """
        Save agent card to a JSON file.

        Args:
            filepath: Path to save the file
            endpoint_url: The base URL for the agent

        Returns:
            Path to the saved file
        """
        agent_card = self.generate_agent_card(endpoint_url)

        with open(filepath, 'w') as f:
            json.dump(agent_card, f, indent=2)

        logger.info(f"Agent card saved to {filepath}")
        return filepath

    def register_agent(self, metadata_uri: str) -> Optional[int]:
        """
        Register agent on the Identity Registry.

        IMPORTANT: This is the ONLY transaction this service can make.
        It requires explicit user confirmation before execution.

        Args:
            metadata_uri: URI pointing to the agent card JSON

        Returns:
            Agent ID if successful, None otherwise
        """
        if not self.settings.private_key:
            raise ValueError("Private key not configured. Cannot register agent.")

        try:
            # Get account from private key
            account = Account.from_key(self.settings.private_key)

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(account.address)
            gas_price = self.w3.eth.gas_price

            tx = self.identity_registry.functions.register(metadata_uri).build_transaction({
                'chainId': 8453,  # Base mainnet
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.settings.private_key)
            # Compatible with both old (rawTransaction) and new (raw_transaction) web3.py
            raw_tx = getattr(signed_tx, 'raw_transaction', None) or signed_tx.rawTransaction
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                # Parse logs to get agent ID
                # The exact log parsing depends on the contract implementation
                logger.info(f"Agent registered successfully. TX: {tx_hash.hex()}")
                return self._parse_agent_id_from_receipt(receipt)
            else:
                logger.error(f"Registration transaction failed. TX: {tx_hash.hex()}")
                return None

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise

    def _parse_agent_id_from_receipt(self, receipt) -> Optional[int]:
        """Parse agent ID from transaction receipt logs."""
        try:
            # Try to find the Registration event in logs
            for log in receipt.logs:
                # The exact topic depends on the contract implementation
                # This is a simplified version
                if len(log.topics) > 1:
                    # Agent ID is typically in the first indexed parameter
                    agent_id = int(log.topics[1].hex(), 16)
                    return agent_id
            return None
        except Exception as e:
            logger.error(f"Failed to parse agent ID: {e}")
            return None

    def get_agent_info(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Get agent information from the registry (READ-ONLY).

        Args:
            agent_id: The agent's on-chain ID

        Returns:
            Agent info dictionary or None
        """
        try:
            owner, metadata_uri, registered_at = self.identity_registry.functions.getAgent(
                agent_id
            ).call()

            return {
                "agent_id": agent_id,
                "owner": owner,
                "metadata_uri": metadata_uri,
                "registered_at": registered_at
            }
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return None

    def get_reputation(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Get agent reputation from the registry (READ-ONLY).

        Args:
            agent_id: The agent's on-chain ID

        Returns:
            Reputation info dictionary or None
        """
        try:
            score, total_interactions = self.reputation_registry.functions.getReputation(
                agent_id
            ).call()

            return {
                "score": score,
                "total_interactions": total_interactions
            }
        except Exception as e:
            logger.error(f"Failed to get reputation: {e}")
            return None

    def get_agents_by_owner(self, owner_address: str) -> list:
        """
        Get all agent IDs owned by an address (READ-ONLY).

        Args:
            owner_address: The owner's wallet address

        Returns:
            List of agent IDs
        """
        try:
            checksum_address = Web3.to_checksum_address(owner_address)
            agent_ids = self.identity_registry.functions.getAgentsByOwner(
                checksum_address
            ).call()
            return list(agent_ids)
        except Exception as e:
            logger.error(f"Failed to get agents by owner: {e}")
            return []


def get_erc8004_service() -> ERC8004Service:
    """Get ERC-8004 service instance."""
    return ERC8004Service()
