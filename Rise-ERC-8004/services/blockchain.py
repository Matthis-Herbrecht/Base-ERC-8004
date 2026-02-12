"""Blockchain interaction service for Rise."""

import logging
from typing import Dict, Any
from web3 import Web3
from web3.exceptions import ContractLogicError
from app.config import get_settings, ERC20_ABI

logger = logging.getLogger(__name__)


class BlockchainService:
    def __init__(self):
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.rise_rpc_url))

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def get_checksum_address(self, address: str) -> str:
        return self.w3.to_checksum_address(address)

    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        try:
            checksum_address = self.get_checksum_address(token_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=ERC20_ABI)
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()
            return {
                "name": name, "symbol": symbol, "decimals": decimals,
                "total_supply": total_supply,
                "total_supply_formatted": str(total_supply / (10 ** decimals))
            }
        except ContractLogicError as e:
            raise ValueError(f"Invalid token contract: {token_address}")
        except Exception as e:
            raise ValueError(f"Failed to read token contract: {str(e)}")


def get_blockchain_service() -> BlockchainService:
    return BlockchainService()
