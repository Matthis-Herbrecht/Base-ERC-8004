"""Blockchain interaction service for Ink."""

import logging
from typing import Optional, Dict, Any
from web3 import Web3
from web3.exceptions import ContractLogicError

from app.config import get_settings, ERC20_ABI

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for interacting with Ink blockchain."""

    def __init__(self):
        """Initialize blockchain service."""
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.ink_rpc_url))

    def is_connected(self) -> bool:
        """Check if connected to Ink."""
        return self.w3.is_connected()

    def get_checksum_address(self, address: str) -> str:
        """Convert address to checksum format."""
        return self.w3.to_checksum_address(address)

    def is_valid_address(self, address: str) -> bool:
        """Check if address is valid."""
        return self.w3.is_address(address)

    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Get basic token information from contract.

        Returns:
            dict with name, symbol, decimals, totalSupply
        """
        try:
            checksum_address = self.get_checksum_address(token_address)
            contract = self.w3.eth.contract(
                address=checksum_address,
                abi=ERC20_ABI
            )

            # Get token info
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()

            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "total_supply_formatted": str(total_supply / (10 ** decimals))
            }
        except ContractLogicError as e:
            logger.error(f"Contract error for {token_address}: {e}")
            raise ValueError(f"Invalid token contract: {token_address}")
        except Exception as e:
            logger.error(f"Failed to get token info for {token_address}: {e}")
            raise ValueError(f"Failed to read token contract: {str(e)}")

    def get_balance(self, token_address: str, holder_address: str) -> int:
        """Get token balance for an address."""
        try:
            checksum_token = self.get_checksum_address(token_address)
            checksum_holder = self.get_checksum_address(holder_address)

            contract = self.w3.eth.contract(
                address=checksum_token,
                abi=ERC20_ABI
            )

            return contract.functions.balanceOf(checksum_holder).call()
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0


def get_blockchain_service() -> BlockchainService:
    """Get blockchain service instance."""
    return BlockchainService()
