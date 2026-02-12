"""Data fetching service for Rise blockchain."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from cachetools import TTLCache
from app.config import get_settings

logger = logging.getLogger(__name__)
_cache = TTLCache(maxsize=1000, ttl=300)


class DataFetcher:
    def __init__(self):
        self.settings = get_settings()
        self.blockscout_base_url = "https://explorer.testnet.riselabs.xyz/api/v2"

    def _get_cache_key(self, prefix: str, *args) -> str:
        return f"{prefix}:{':'.join(str(a) for a in args)}"

    async def get_holder_count(self, token_address: str) -> int:
        cache_key = self._get_cache_key("holders", token_address)
        if cache_key in _cache:
            return _cache[cache_key]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/tokens/{token_address}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    count = int(data.get("holders_count") or data.get("holders") or 0)
                    _cache[cache_key] = count
                    return count
        except Exception as e:
            logger.error(f"Holder count failed: {e}")
        return 0

    async def is_contract_verified(self, token_address: str) -> bool:
        cache_key = self._get_cache_key("verified", token_address)
        if cache_key in _cache:
            return _cache[cache_key]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/smart-contracts/{token_address}"
                response = await client.get(url)
                if response.status_code == 200:
                    is_verified = response.json().get("is_verified", False)
                    _cache[cache_key] = is_verified
                    return is_verified
                _cache[cache_key] = False
                return False
        except:
            return False

    async def get_contract_age_days(self, token_address: str) -> int:
        cache_key = self._get_cache_key("age", token_address)
        if cache_key in _cache:
            return _cache[cache_key]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/addresses/{token_address}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    creation_tx = data.get("creation_tx_hash")
                    if creation_tx:
                        tx_url = f"{self.blockscout_base_url}/transactions/{creation_tx}"
                        tx_response = await client.get(tx_url)
                        if tx_response.status_code == 200:
                            timestamp_str = tx_response.json().get("timestamp")
                            if timestamp_str:
                                creation_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                age = (datetime.utcnow().replace(tzinfo=creation_date.tzinfo) - creation_date).days
                                _cache[cache_key] = max(0, age)
                                return max(0, age)
        except Exception as e:
            logger.error(f"Contract age failed: {e}")
        return 0

    async def get_top_holders(self, token_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = self._get_cache_key("top_holders", token_address)
        if cache_key in _cache:
            return _cache[cache_key]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.blockscout_base_url}/tokens/{token_address}/holders"
                response = await client.get(url)
                if response.status_code == 200:
                    items = response.json().get("items", [])
                    holders = []
                    for item in items[:limit]:
                        addr_obj = item.get("address_hash") or item.get("address") or {}
                        holders.append({"address": addr_obj.get("hash", ""), "value": item.get("value", "0")})
                    _cache[cache_key] = holders
                    return holders
        except:
            pass
        return []

    async def get_token_price_coingecko(self, token_address: str) -> Optional[float]:
        return None  # Rise not yet on CoinGecko

    async def get_dex_data(self, token_address: str) -> Dict[str, Any]:
        cache_key = self._get_cache_key("dex", token_address)
        if cache_key in _cache:
            return _cache[cache_key]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                response = await client.get(url)
                if response.status_code == 200:
                    pairs = response.json().get("pairs", [])
                    if pairs:
                        total_liquidity = total_volume = 0
                        price_usd = None
                        oldest_ts = None
                        for pair in pairs:
                            if pair.get("chainId") in ["rise", "11155931"]:
                                total_liquidity += float(pair.get("liquidity", {}).get("usd", 0) or 0)
                                total_volume += float(pair.get("volume", {}).get("h24", 0) or 0)
                                if price_usd is None:
                                    price_usd = float(pair.get("priceUsd", 0) or 0)
                                pc = pair.get("pairCreatedAt")
                                if pc and (oldest_ts is None or pc < oldest_ts):
                                    oldest_ts = pc
                        age_days = 0
                        if oldest_ts:
                            age_days = (datetime.utcnow() - datetime.fromtimestamp(oldest_ts / 1000)).days
                        result = {"liquidity_usd": total_liquidity, "volume_24h_usd": total_volume, "price_usd": price_usd, "age_days": age_days}
                        _cache[cache_key] = result
                        return result
        except:
            pass
        return {"liquidity_usd": 0, "volume_24h_usd": 0, "price_usd": None, "age_days": 0}


def get_data_fetcher() -> DataFetcher:
    return DataFetcher()
