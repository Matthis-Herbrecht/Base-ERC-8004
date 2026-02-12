"""Data fetching service for external APIs (Blockscout, CoinGecko, DEX)."""

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
        # Blockscout API for Ink (free, no API key needed)
        self.blockscout_base_url = "https://explorer.inkonchain.com/api/v2"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"

    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key."""
        return f"{prefix}:{':'.join(str(a) for a in args)}"

    async def get_holder_count(self, token_address: str) -> int:
        """
        Get token holder count from Blockscout API.
        """
        cache_key = self._get_cache_key("holders", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/tokens/{token_address}"
                logger.info(f"Fetching holder count from Blockscout for {token_address}")
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    # Blockscout uses "holders_count" (string) in TokenInfo
                    raw = data.get("holders_count") or data.get("holders") or 0
                    count = int(raw)
                    logger.info(f"Blockscout holder count: {count}")
                    _cache[cache_key] = count
                    return count
                else:
                    logger.warning(f"Blockscout API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Blockscout holder count failed: {e}")

        return 0

    async def get_contract_creation_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get contract creation info from Blockscout."""
        cache_key = self._get_cache_key("creation", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/addresses/{token_address}"
                logger.info(f"Fetching contract info for {token_address}")
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    _cache[cache_key] = data
                    return data
                else:
                    logger.warning(f"Blockscout address API returned status {response.status_code}")

            return None
        except Exception as e:
            logger.error(f"Failed to get contract creation info: {e}")
            return None

    async def is_contract_verified(self, token_address: str) -> bool:
        """Check if contract is verified on Blockscout."""
        cache_key = self._get_cache_key("verified", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/smart-contracts/{token_address}"
                logger.info(f"Checking verification for {token_address}")
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    is_verified = data.get("is_verified", False)
                    logger.info(f"Contract verified: {is_verified}")
                    _cache[cache_key] = is_verified
                    return is_verified
                elif response.status_code == 404:
                    # Not verified
                    _cache[cache_key] = False
                    return False

            return False
        except Exception as e:
            logger.error(f"Failed to check contract verification: {e}")
            return False

    async def get_contract_age_days(self, token_address: str) -> int:
        """Get contract age in days from Blockscout."""
        cache_key = self._get_cache_key("age", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/addresses/{token_address}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    # Try to get creation timestamp
                    creation_tx = data.get("creation_tx_hash")
                    if creation_tx:
                        # Get transaction details
                        tx_url = f"{self.blockscout_base_url}/transactions/{creation_tx}"
                        tx_response = await client.get(tx_url)
                        if tx_response.status_code == 200:
                            tx_data = tx_response.json()
                            timestamp_str = tx_data.get("timestamp")
                            if timestamp_str:
                                # Parse ISO timestamp
                                creation_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                age = (datetime.utcnow().replace(tzinfo=creation_date.tzinfo) - creation_date).days
                                logger.info(f"Contract age: {age} days")
                                _cache[cache_key] = max(0, age)
                                return max(0, age)

            return 0
        except Exception as e:
            logger.error(f"Failed to get contract age: {e}")
            return 0

    async def get_top_holders(self, token_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top token holders from Blockscout API.
        Returns list of dicts with 'address' and 'value' keys.
        """
        cache_key = self._get_cache_key("top_holders", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/tokens/{token_address}/holders"
                logger.info(f"Fetching top holders from Blockscout for {token_address}")
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    holders = []
                    for item in items[:limit]:
                        # Blockscout uses "address_hash" (or "address") object with "hash" field
                        addr_obj = item.get("address_hash") or item.get("address") or {}
                        holder = {
                            "address": addr_obj.get("hash", ""),
                            "value": item.get("value", "0"),
                        }
                        holders.append(holder)

                    logger.info(f"Got {len(holders)} top holders from Blockscout")
                    _cache[cache_key] = holders
                    return holders
                else:
                    logger.warning(f"Blockscout holders API returned status {response.status_code}")

            return []
        except Exception as e:
            logger.error(f"Failed to get top holders: {e}")
            return []

    async def get_token_price_coingecko(self, token_address: str) -> Optional[float]:
        """Get token price from CoinGecko (if listed)."""
        cache_key = self._get_cache_key("price", token_address)
        if cache_key in _cache:
            return _cache[cache_key]

        # Ink is a new chain, tokens may not be listed on CoinGecko yet
        # Try with ink chain ID
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try with ink asset platform
                url = f"{self.coingecko_base_url}/simple/token_price/ink"
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
        Get DEX data (liquidity, volume, age) for token.
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
                        oldest_pair_timestamp = None

                        for pair in pairs:
                            # Filter for Ink chain pairs (chainId might be "ink" or "57073")
                            chain_id = pair.get("chainId", "")
                            if chain_id in ["ink", "57073"]:
                                total_liquidity += float(pair.get("liquidity", {}).get("usd", 0) or 0)
                                total_volume_24h += float(pair.get("volume", {}).get("h24", 0) or 0)
                                if price_usd is None:
                                    price_usd = float(pair.get("priceUsd", 0) or 0)

                                # Get pair creation timestamp (in milliseconds)
                                pair_created = pair.get("pairCreatedAt")
                                if pair_created:
                                    if oldest_pair_timestamp is None or pair_created < oldest_pair_timestamp:
                                        oldest_pair_timestamp = pair_created

                        # Calculate age in days from oldest pair
                        age_days = 0
                        if oldest_pair_timestamp:
                            creation_date = datetime.fromtimestamp(oldest_pair_timestamp / 1000)
                            age_days = (datetime.utcnow() - creation_date).days
                            logger.info(f"Token age from DEX: {age_days} days")

                        result = {
                            "liquidity_usd": total_liquidity,
                            "volume_24h_usd": total_volume_24h,
                            "price_usd": price_usd,
                            "pairs_count": len([p for p in pairs if p.get("chainId") in ["ink", "57073"]]),
                            "age_days": age_days
                        }
                        _cache[cache_key] = result
                        logger.info(f"DEX data: liquidity=${total_liquidity}, volume=${total_volume_24h}, age={age_days}d")
                        return result

                return {
                    "liquidity_usd": 0,
                    "volume_24h_usd": 0,
                    "price_usd": None,
                    "pairs_count": 0,
                    "age_days": 0
                }
        except Exception as e:
            logger.error(f"Failed to get DEX data: {e}")
            return {
                "liquidity_usd": 0,
                "volume_24h_usd": 0,
                "price_usd": None,
                "pairs_count": 0,
                "age_days": 0
            }


def get_data_fetcher() -> DataFetcher:
    """Get data fetcher instance."""
    return DataFetcher()
