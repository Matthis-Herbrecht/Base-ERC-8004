"""Data fetching service for MegaETH tokens."""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime


class DataFetcher:
    """Fetches token data from various sources."""

    def __init__(self):
        self.blockscout_base_url = "https://megaeth.blockscout.com/api/v2"
        self.dexscreener_base_url = "https://api.dexscreener.com/latest/dex"

    async def get_token_from_blockscout(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token info from Blockscout."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.blockscout_base_url}/tokens/{token_address}",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Blockscout error: {e}")
        return None

    async def get_token_holders(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token holder information from Blockscout."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.blockscout_base_url}/tokens/{token_address}/counters",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Blockscout holders error: {e}")
        return None

    async def get_top_holders(self, token_address: str) -> List[Dict[str, Any]]:
        """Get top token holders from Blockscout."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.blockscout_base_url}/tokens/{token_address}/holders",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
            except Exception as e:
                print(f"Blockscout top holders error: {e}")
        return []

    async def get_contract_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get contract info from Blockscout."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.blockscout_base_url}/smart-contracts/{address}",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Blockscout contract error: {e}")
        return None

    async def get_dex_data(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get DEX trading data from DexScreener."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.dexscreener_base_url}/tokens/{token_address}",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    # Filter for MegaETH pairs
                    megaeth_pairs = [p for p in pairs if p.get("chainId") in ["megaeth", "4326"]]
                    if megaeth_pairs:
                        return megaeth_pairs[0]  # Return the most liquid pair
                    elif pairs:
                        return pairs[0]  # Fallback to any pair
            except Exception as e:
                print(f"DexScreener error: {e}")
        return None

    async def get_token_age_days(self, token_address: str) -> int:
        """Estimate token age from DexScreener pair creation."""
        dex_data = await self.get_dex_data(token_address)
        if dex_data and "pairCreatedAt" in dex_data:
            created_at = datetime.fromtimestamp(dex_data["pairCreatedAt"] / 1000)
            age = (datetime.utcnow() - created_at).days
            return max(0, age)
        return 0


def get_data_fetcher() -> DataFetcher:
    """Get data fetcher instance."""
    return DataFetcher()
