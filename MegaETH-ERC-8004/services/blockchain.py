"""Blockchain service for MegaETH."""

from web3 import Web3
from typing import Optional, Dict, Any
from app.config import get_settings

# Standard ERC-20 ABI for basic token info
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
]


class BlockchainService:
    """Service for interacting with MegaETH blockchain."""

    def __init__(self):
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.megaeth_rpc_url))

    def is_connected(self) -> bool:
        """Check if connected to MegaETH."""
        return self.w3.is_connected()

    def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get basic token information from contract."""
        try:
            address = self.w3.to_checksum_address(token_address)
            contract = self.w3.eth.contract(address=address, abi=ERC20_ABI)

            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()

            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply / (10 ** decimals)
            }
        except Exception as e:
            print(f"Error getting token info: {e}")
            return None

    def get_contract_creation_block(self, address: str) -> Optional[int]:
        """Get the block number when a contract was created."""
        # This would require archive node or indexer
        # For now, return None
        return None


def get_blockchain_service() -> BlockchainService:
    """Get blockchain service instance."""
    return BlockchainService()
