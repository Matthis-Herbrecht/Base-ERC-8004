"""Data fetching service for external APIs (Etherscan V2, CoinGecko, DEX)."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from cachetools import TTLCache

from app.config import get_settings

logger = logging.getLogger(__name__)

# Cache for API responses
_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute TTL


class DataFetcher:
    """Service for fetching token data from external APIs."""

    def __init__(self):
        """Initialize data fetcher."""
        self.settings = get_settings()
        # Use Etherscan V2 API with chainid for Base
        self.etherscan_v2_url = "https://api.etherscan.io/v2/api"
        self.chain_id = "8453"  # Base mainnet
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"

    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key."""
        return f"{prefix}:{':'.join(str(a) for a in args)}"

    async def _make_etherscan_request(self, params: dict) -> dict:
        """Make a request to Etherscan V2 API."""
        params["chainid"] = self.chain_id
        params["apikey"] = self.settings.basescan_api_key or ""

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(self.etherscan_v2_url, params=params)
            return response.json()

    async def get_holder_count(self, token_address: str) -> int:
        """
        Get token holder count estimate from transfer events.
        """
        cache_key = self._get_cache_key("holders", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            params = {
                "module": "account",
                "action": "tokentx",
                "contractaddress": token_address,
                "page": 1,
                "offset": 1000,
                "sort": "desc",
            }

            logger.info(f"Fetching transfers for {token_address}")
            data = await self._make_etherscan_request(params)

            logger.info(f"Transfer response status: {data.get('status')}, message: {data.get('message')}")

            if data.get("status") == "1" and data.get("result"):
                # Count unique addresses from transfers
                addresses = set()
                for tx in data.get("result", []):
                    to_addr = tx.get("to", "").lower()
                    from_addr = tx.get("from", "").lower()
                    if to_addr and to_addr != "0x0000000000000000000000000000000000000000":
                        addresses.add(to_addr)
                    if from_addr and from_addr != "0x0000000000000000000000000000000000000000":
                        addresses.add(from_addr)

                count = len(addresses)
                logger.info(f"Estimated {count} holders from transfers")
                _cache[cache_key] = count
                return count
            else:
                logger.warning(f"No transfer data: {data.get('message', 'Unknown error')}")

            return 0
        except Exception as e:
            logger.error(f"Failed to get holder count: {e}")
            return 0

    async def get_contract_creation_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get contract creation info."""
        cache_key = self._get_cache_key("creation", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            params = {
                "module": "contract",
                "action": "getcontractcreation",
                "contractaddresses": token_address,
            }

            logger.info(f"Fetching contract creation for {token_address}")
            data = await self._make_etherscan_request(params)

            logger.info(f"Contract creation response: {data.get('status')}, message: {data.get('message')}")

            if data.get("status") == "1" and data.get("result"):
                result = data["result"][0]
                _cache[cache_key] = result
                return result
            else:
                logger.warning(f"No contract creation data: {data.get('message', 'Unknown')}")

            return None
        except Exception as e:
            logger.error(f"Failed to get contract creation info: {e}")
            return None

    async def is_contract_verified(self, token_address: str) -> bool:
        """Check if contract is verified."""
        cache_key = self._get_cache_key("verified", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            params = {
                "module": "contract",
                "action": "getsourcecode",
                "address": token_address,
            }

            logger.info(f"Checking verification for {token_address}")
            data = await self._make_etherscan_request(params)

            logger.info(f"Verification response status: {data.get('status')}")

            if data.get("status") == "1" and data.get("result"):
                result = data["result"][0]
                source_code = result.get("SourceCode", "")
                is_verified = source_code != "" and source_code != "0"
                logger.info(f"Contract verified: {is_verified}")
                _cache[cache_key] = is_verified
                return is_verified

            return False
        except Exception as e:
            logger.error(f"Failed to check contract verification: {e}")
            return False

    async def get_contract_age_days(self, token_address: str) -> int:
        """Get contract age in days using first transfer."""
        cache_key = self._get_cache_key("age", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            # Get first transfer to estimate contract age
            params = {
                "module": "account",
                "action": "tokentx",
                "contractaddress": token_address,
                "page": 1,
                "offset": 1,
                "sort": "asc",
            }

            data = await self._make_etherscan_request(params)

            if data.get("status") == "1" and data.get("result"):
                first_tx = data["result"][0]
                timestamp = int(first_tx.get("timeStamp", 0))
                if timestamp > 0:
                    creation_date = datetime.fromtimestamp(timestamp)
                    age = (datetime.utcnow() - creation_date).days
                    logger.info(f"Contract age: {age} days (from first transfer)")
                    _cache[cache_key] = age
                    return max(0, age)

            # Fallback: try contract creation info
            creation_info = await self.get_contract_creation_info(token_address)
            if creation_info and creation_info.get("txHash"):
                # Get transaction details
                params = {
                    "module": "proxy",
                    "action": "eth_getTransactionByHash",
                    "txhash": creation_info.get("txHash"),
                }
                data = await self._make_etherscan_request(params)

                if data.get("result") and data["result"].get("blockNumber"):
                    block_hex = data["result"]["blockNumber"]
                    block_number = int(block_hex, 16)

                    # Get block info
                    params = {
                        "module": "block",
                        "action": "getblockreward",
                        "blockno": block_number,
                    }
                    block_data = await self._make_etherscan_request(params)

                    if block_data.get("status") == "1" and block_data.get("result"):
                        timestamp = int(block_data["result"].get("timeStamp", 0))
                        if timestamp > 0:
                            creation_date = datetime.fromtimestamp(timestamp)
                            age = (datetime.utcnow() - creation_date).days
                            logger.info(f"Contract age: {age} days (from creation)")
                            _cache[cache_key] = age
                            return max(0, age)

            return 0
        except Exception as e:
            logger.error(f"Failed to get contract age: {e}")
            return 0

    async def get_top_holders(self, token_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top token holders - requires PRO API."""
        return []

    async def get_token_price_coingecko(self, token_address: str) -> Optional[float]:
        """Get token price from CoinGecko."""
        cache_key = self._get_cache_key("price", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.coingecko_base_url}/simple/token_price/base"
                params = {
                    "contract_addresses": token_address.lower(),
                    "vs_currencies": "usd"
                }
                if self.settings.coingecko_api_key:
                    params["x_cg_demo_api_key"] = self.settings.coingecko_api_key

                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    price = data.get(token_address.lower(), {}).get("usd")
                    if price:
                        _cache[cache_key] = price
                        return price

                return None
        except Exception as e:
            logger.error(f"Failed to get token price: {e}")
            return None

    async def get_dex_data(self, token_address: str) -> Dict[str, Any]:
        """
        Get DEX data (liquidity, volume) for token.
        Uses DexScreener API for DEX data.
        """
        cache_key = self._get_cache_key("dex", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])

                    if pairs:
                        total_liquidity = 0
                        total_volume_24h = 0
                        price_usd = None

                        for pair in pairs:
                            if pair.get("chainId") == "base":
                                total_liquidity += float(pair.get("liquidity", {}).get("usd", 0) or 0)
                                total_volume_24h += float(pair.get("volume", {}).get("h24", 0) or 0)
                                if price_usd is None:
                                    price_usd = float(pair.get("priceUsd", 0) or 0)

                        result = {
                            "liquidity_usd": total_liquidity,
                            "volume_24h_usd": total_volume_24h,
                            "price_usd": price_usd,
                            "pairs_count": len([p for p in pairs if p.get("chainId") == "base"])
                        }
                        _cache[cache_key] = result
                        logger.info(f"DEX data: liquidity=${total_liquidity}, volume=${total_volume_24h}")
                        return result

                return {
                    "liquidity_usd": 0,
                    "volume_24h_usd": 0,
                    "price_usd": None,
                    "pairs_count": 0
                }
        except Exception as e:
            logger.error(f"Failed to get DEX data: {e}")
            return {
                "liquidity_usd": 0,
                "volume_24h_usd": 0,
                "price_usd": None,
                "pairs_count": 0
            }


def get_data_fetcher() -> DataFetcher:
    """Get data fetcher instance."""
    return DataFetcher()
