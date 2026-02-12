"""Token analysis service for MegaETH."""

from typing import Optional
from datetime import datetime

from app.models import TokenAnalysis, TokenMetrics, RiskLevel, RedFlag
from services.blockchain import BlockchainService
from services.data_fetcher import DataFetcher


class TokenAnalyzer:
    """Analyzes ERC-20 tokens on MegaETH."""

    def __init__(self):
        self.blockchain = BlockchainService()
        self.data_fetcher = DataFetcher()

    async def analyze(self, token_address: str) -> TokenAnalysis:
        """Perform comprehensive token analysis."""
        # Get on-chain data
        token_info = self.blockchain.get_token_info(token_address)
        if not token_info:
            raise ValueError(f"Token not found: {token_address}")

        # Get off-chain data
        blockscout_data = await self.data_fetcher.get_token_from_blockscout(token_address)
        holders_data = await self.data_fetcher.get_token_holders(token_address)
        top_holders = await self.data_fetcher.get_top_holders(token_address)
        contract_info = await self.data_fetcher.get_contract_info(token_address)
        dex_data = await self.data_fetcher.get_dex_data(token_address)
        token_age = await self.data_fetcher.get_token_age_days(token_address)

        # Extract metrics
        holders = 0
        if holders_data:
            holders = int(holders_data.get("token_holders_count") or holders_data.get("holders_count") or 0)

        liquidity_usd = 0.0
        volume_24h = 0.0
        price_usd = None
        market_cap = None

        if dex_data:
            liquidity_usd = float(dex_data.get("liquidity", {}).get("usd", 0) or 0)
            volume_24h = float(dex_data.get("volume", {}).get("h24", 0) or 0)
            price_usd = float(dex_data.get("priceUsd", 0) or 0) if dex_data.get("priceUsd") else None
            if dex_data.get("fdv"):
                market_cap = float(dex_data.get("fdv", 0) or 0)

        is_verified = False
        if contract_info:
            is_verified = contract_info.get("is_verified", False)

        # Calculate top holder percentage
        top_holder_pct = 0.0
        if top_holders and len(top_holders) > 0:
            top_holder = top_holders[0]
            value = top_holder.get("value")
            if value and token_info.get("total_supply", 0) > 0:
                decimals = token_info.get("decimals", 18)
                holder_balance = int(value) / (10 ** decimals)
                top_holder_pct = (holder_balance / token_info["total_supply"]) * 100

        # Build metrics
        metrics = TokenMetrics(
            holders=holders,
            liquidity_usd=liquidity_usd,
            volume_24h_usd=volume_24h,
            contract_age_days=token_age,
            is_verified=is_verified,
            top_holder_percentage=min(top_holder_pct, 100)
        )

        # Identify red flags
        red_flags = []

        if holders < 10:
            red_flags.append(RedFlag(description="Very few holders (<10)", severity="high"))
        elif holders < 50:
            red_flags.append(RedFlag(description="Low holder count (<50)", severity="medium"))

        if liquidity_usd < 1000:
            red_flags.append(RedFlag(description="Very low liquidity (<$1,000)", severity="critical"))
        elif liquidity_usd < 10000:
            red_flags.append(RedFlag(description="Low liquidity (<$10,000)", severity="high"))

        if not is_verified:
            red_flags.append(RedFlag(description="Contract not verified", severity="medium"))

        if top_holder_pct > 50:
            red_flags.append(RedFlag(description=f"High concentration: top holder owns {top_holder_pct:.1f}%", severity="critical"))
        elif top_holder_pct > 20:
            red_flags.append(RedFlag(description=f"Moderate concentration: top holder owns {top_holder_pct:.1f}%", severity="medium"))

        if token_age < 7:
            red_flags.append(RedFlag(description="Very new token (<7 days)", severity="high"))
        elif token_age < 30:
            red_flags.append(RedFlag(description="New token (<30 days)", severity="low"))

        # Calculate score
        score = self._calculate_score(metrics, red_flags)
        risk_level = self._determine_risk_level(score, red_flags)

        # Generate analysis
        analysis = self._generate_analysis(token_info, metrics, red_flags, score)

        return TokenAnalysis(
            contract_address=token_address,
            name=token_info["name"],
            symbol=token_info["symbol"],
            score=score,
            risk_level=risk_level,
            metrics=metrics,
            red_flags=red_flags,
            analysis=analysis,
            price_usd=price_usd,
            market_cap_usd=market_cap,
            analyzed_at=datetime.utcnow()
        )

    def _calculate_score(self, metrics: TokenMetrics, red_flags: list) -> int:
        """Calculate quality score from 0-100."""
        score = 50  # Base score

        # Holder score (max +20)
        if metrics.holders >= 1000:
            score += 20
        elif metrics.holders >= 100:
            score += 10
        elif metrics.holders >= 10:
            score += 5

        # Liquidity score (max +20)
        if metrics.liquidity_usd >= 100000:
            score += 20
        elif metrics.liquidity_usd >= 10000:
            score += 10
        elif metrics.liquidity_usd >= 1000:
            score += 5

        # Verification bonus
        if metrics.is_verified:
            score += 10

        # Age bonus (max +10)
        if metrics.contract_age_days >= 365:
            score += 10
        elif metrics.contract_age_days >= 90:
            score += 5

        # Red flag penalties
        for flag in red_flags:
            if flag.severity == "critical":
                score -= 25
            elif flag.severity == "high":
                score -= 15
            elif flag.severity == "medium":
                score -= 5

        return max(0, min(100, score))

    def _determine_risk_level(self, score: int, red_flags: list) -> RiskLevel:
        """Determine risk level from score and flags."""
        critical_flags = [f for f in red_flags if f.severity == "critical"]
        if critical_flags or score < 20:
            return RiskLevel.CRITICAL
        elif score < 40:
            return RiskLevel.HIGH
        elif score < 60:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _generate_analysis(self, token_info: dict, metrics: TokenMetrics, red_flags: list, score: int) -> str:
        """Generate human-readable analysis."""
        name = token_info["name"]
        parts = []

        if score >= 60:
            parts.append(f"{name} shows reasonable metrics for a MegaETH token.")
        elif score >= 40:
            parts.append(f"{name} has some concerning indicators that warrant caution.")
        else:
            parts.append(f"{name} shows multiple high-risk indicators.")

        if metrics.holders < 50:
            parts.append(f"Limited holder base ({metrics.holders} holders).")

        if metrics.liquidity_usd < 10000:
            parts.append(f"Low liquidity (${metrics.liquidity_usd:,.0f}).")

        if not metrics.is_verified:
            parts.append("Contract source code is not verified.")

        if metrics.top_holder_percentage > 20:
            parts.append(f"Top holder concentration is {metrics.top_holder_percentage:.1f}%.")

        return " ".join(parts)


def get_token_analyzer() -> TokenAnalyzer:
    """Get token analyzer instance."""
    return TokenAnalyzer()
