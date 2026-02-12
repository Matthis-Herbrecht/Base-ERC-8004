"""ERC-8004 agent service for MegaETH."""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from web3 import Web3
from app.config import get_settings, IDENTITY_REGISTRY_ABI, REPUTATION_REGISTRY_ABI


class ERC8004Service:
    def __init__(self):
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.megaeth_rpc_url))

    def generate_agent_card(self) -> Dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareAgent",
            "name": "MegaETHTokenScout",
            "description": "AI agent for analyzing ERC-20 token quality and risk on MegaETH blockchain",
            "version": "1.0.0",
            "capabilities": [
                {"name": "token_analysis", "endpoint": f"{self.settings.agent_endpoint}/api/analyze/{{token_address}}", "method": "GET"},
                {"name": "trending_tokens", "endpoint": f"{self.settings.agent_endpoint}/api/trending", "method": "GET"}
            ],
            "pricing": {"model": "free", "rateLimit": "10 requests/minute"},
            "chain": {"name": "MegaETH", "chainId": 6342}
        }

    def save_agent_card(self, path: Optional[str] = None) -> str:
        if path is None:
            path = Path(__file__).parent.parent / "static" / "agent_card.json"
        with open(path, "w") as f:
            json.dump(self.generate_agent_card(), f, indent=2)
        return str(path)

    async def register_agent(self, metadata_uri: str) -> Dict[str, Any]:
        if not self.settings.private_key:
            raise ValueError("Private key not configured")
        account = self.w3.eth.account.from_key(self.settings.private_key)
        registry = self.w3.eth.contract(address=self.w3.to_checksum_address(self.settings.identity_registry), abi=IDENTITY_REGISTRY_ABI)
        tx = registry.functions.register(metadata_uri).build_transaction({
            "from": account.address, "nonce": self.w3.eth.get_transaction_count(account.address),
            "gasPrice": self.w3.eth.gas_price, "gas": 200000, "chainId": 6342
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.settings.private_key)
        raw_tx = getattr(signed_tx, 'raw_transaction', None) or signed_tx.rawTransaction
        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return {"tx_hash": tx_hash.hex(), "block_number": receipt["blockNumber"], "status": "success" if receipt["status"] == 1 else "failed"}

    async def get_reputation(self, agent_id: int) -> Dict[str, Any]:
        registry = self.w3.eth.contract(address=self.w3.to_checksum_address(self.settings.reputation_registry), abi=REPUTATION_REGISTRY_ABI)
        score, total = registry.functions.getReputation(agent_id).call()
        return {"agent_id": agent_id, "score": score, "total_interactions": total}


def get_erc8004_service() -> ERC8004Service:
    return ERC8004Service()
