"""Token analysis service."""

import logging
from typing import List, Dict, Any
from datetime import datetime

from app.models import TokenAnalysis, TokenMetrics, RedFlag, RiskLevel
from services.blockchain import BlockchainService
from services.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class TokenAnalyzer:
    """Service for comprehensive token analysis."""

    def __init__(self):
        """Initialize token analyzer."""
        self.blockchain = BlockchainService()
        self.data_fetcher = DataFetcher()

        # Scoring weights (total = 100)
        self.weights = {
            "holders": 20,
            "liquidity": 25,
            "volume": 15,
            "age": 15,
            "verified": 10,
            "distribution": 15,
        }

    async def analyze(self, token_address: str) -> TokenAnalysis:
        """
        Perform comprehensive token analysis.

        Args:
            token_address: The token contract address

        Returns:
            TokenAnalysis with score, metrics, and red flags
        """
        # Get basic token info from blockchain
        token_info = self.blockchain.get_token_info(token_address)

        # Fetch additional data
        holder_count = await self.data_fetcher.get_holder_count(token_address)
        is_verified = await self.data_fetcher.is_contract_verified(token_address)
        contract_age = await self.data_fetcher.get_contract_age_days(token_address)
        top_holders = await self.data_fetcher.get_top_holders(token_address)
        dex_data = await self.data_fetcher.get_dex_data(token_address)
        price = await self.data_fetcher.get_token_price_coingecko(token_address)

        # Use DEX age as fallback if contract age is 0
        if contract_age == 0:
            contract_age = dex_data.get("age_days", 0)

        # Calculate top holder percentage
        top_holder_pct = self._calculate_top_holder_percentage(
            top_holders,
            token_info["total_supply"],
            token_info["decimals"]
        )

        # Build metrics
        metrics = TokenMetrics(
            holders=holder_count,
            volume_24h_usd=dex_data.get("volume_24h_usd", 0),
            liquidity_usd=dex_data.get("liquidity_usd", 0),
            contract_age_days=contract_age,
            is_verified=is_verified,
            top_holder_percentage=round(top_holder_pct, 2)
        )

        # Calculate score and detect red flags
        score, red_flags = self._calculate_score(metrics)

        # Determine risk level
        risk_level = self._get_risk_level(score)

        # Generate analysis summary
        analysis = self._generate_analysis(
            token_info["symbol"],
            score,
            risk_level,
            metrics,
            red_flags
        )

        # Calculate market cap if price available
        market_cap = None
        if price and price > 0:
            supply_float = token_info["total_supply"] / (10 ** token_info["decimals"])
            market_cap = price * supply_float

        return TokenAnalysis(
            address=token_address,
            name=token_info["name"],
            symbol=token_info["symbol"],
            decimals=token_info["decimals"],
            total_supply=token_info["total_supply_formatted"],
            score=score,
            risk_level=risk_level,
            metrics=metrics,
            red_flags=red_flags,
            analysis=analysis,
            price_usd=price or dex_data.get("price_usd"),
            market_cap_usd=market_cap,
            analyzed_at=datetime.utcnow()
        )

    def _calculate_top_holder_percentage(
        self, holders: List[dict], total_supply: int, decimals: int
    ) -> float:
        """Calculate percentage held by top holder."""
        if not holders or total_supply == 0:
            return 0.0

        try:
            # Blockscout returns 'value' as raw token amount string
            top_balance = int(holders[0].get("value", 0))
            if top_balance > 0 and total_supply > 0:
                return (top_balance / total_supply) * 100
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating top holder percentage: {e}")
            return 0.0

    def _calculate_score(self, metrics: TokenMetrics) -> tuple[int, List[RedFlag]]:
        """Calculate quality score and detect red flags."""
        score = 0
        red_flags = []

        # Holders score (20 points)
        if metrics.holders >= 10000:
            score += self.weights["holders"]
        elif metrics.holders >= 1000:
            score += int(self.weights["holders"] * 0.8)
        elif metrics.holders >= 100:
            score += int(self.weights["holders"] * 0.5)
        elif metrics.holders >= 10:
            score += int(self.weights["holders"] * 0.2)
        else:
            red_flags.append(RedFlag(
                code="VERY_FEW_HOLDERS",
                description=f"Only {metrics.holders} holders detected",
                severity="high"
            ))

        # Liquidity score (25 points)
        if metrics.liquidity_usd >= 1000000:
            score += self.weights["liquidity"]
        elif metrics.liquidity_usd >= 100000:
            score += int(self.weights["liquidity"] * 0.8)
        elif metrics.liquidity_usd >= 10000:
            score += int(self.weights["liquidity"] * 0.5)
        elif metrics.liquidity_usd >= 1000:
            score += int(self.weights["liquidity"] * 0.2)
        else:
            red_flags.append(RedFlag(
                code="LOW_LIQUIDITY",
                description=f"Liquidity only ${metrics.liquidity_usd:,.0f}",
                severity="high"
            ))

        # Volume score (15 points)
        if metrics.volume_24h_usd >= 100000:
            score += self.weights["volume"]
        elif metrics.volume_24h_usd >= 10000:
            score += int(self.weights["volume"] * 0.7)
        elif metrics.volume_24h_usd >= 1000:
            score += int(self.weights["volume"] * 0.4)
        else:
            red_flags.append(RedFlag(
                code="LOW_VOLUME",
                description=f"24h volume only ${metrics.volume_24h_usd:,.0f}",
                severity="medium"
            ))

        # Age score (15 points)
        if metrics.contract_age_days >= 365:
            score += self.weights["age"]
        elif metrics.contract_age_days >= 180:
            score += int(self.weights["age"] * 0.8)
        elif metrics.contract_age_days >= 30:
            score += int(self.weights["age"] * 0.5)
        elif metrics.contract_age_days >= 7:
            score += int(self.weights["age"] * 0.2)
        else:
            red_flags.append(RedFlag(
                code="VERY_NEW_TOKEN",
                description=f"Contract only {metrics.contract_age_days} days old",
                severity="medium"
            ))

        # Verification score (10 points)
        if metrics.is_verified:
            score += self.weights["verified"]
        else:
            red_flags.append(RedFlag(
                code="UNVERIFIED_CONTRACT",
                description="Contract source code is not verified",
                severity="medium"
            ))

        # Distribution score (15 points)
        if metrics.top_holder_percentage <= 5:
            score += self.weights["distribution"]
        elif metrics.top_holder_percentage <= 10:
            score += int(self.weights["distribution"] * 0.8)
        elif metrics.top_holder_percentage <= 20:
            score += int(self.weights["distribution"] * 0.5)
        elif metrics.top_holder_percentage <= 50:
            score += int(self.weights["distribution"] * 0.2)
            red_flags.append(RedFlag(
                code="HIGH_CONCENTRATION",
                description=f"Top holder owns {metrics.top_holder_percentage:.1f}%",
                severity="medium"
            ))
        else:
            red_flags.append(RedFlag(
                code="EXTREME_CONCENTRATION",
                description=f"Top holder owns {metrics.top_holder_percentage:.1f}%",
                severity="high"
            ))

        return min(100, max(0, score)), red_flags

    def _get_risk_level(self, score: int) -> RiskLevel:
        """Determine risk level from score."""
        if score < 30:
            return RiskLevel.SCAM
        elif score < 50:
            return RiskLevel.HIGH_RISK
        elif score < 70:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.QUALITY

    def _generate_analysis(
        self,
        symbol: str,
        score: int,
        risk_level: RiskLevel,
        metrics: TokenMetrics,
        red_flags: List[RedFlag]
    ) -> str:
        """Generate human-readable analysis summary."""
        risk_descriptions = {
            RiskLevel.SCAM: "This token shows numerous high-risk signs and could be a scam.",
            RiskLevel.HIGH_RISK: "This token shows several important risk indicators.",
            RiskLevel.MODERATE: "This token shows some risks but appears relatively established.",
            RiskLevel.QUALITY: "This token shows solid quality indicators."
        }

        analysis = f"{symbol} scored {score}/100. {risk_descriptions[risk_level]}"

        if metrics.holders > 0:
            analysis += f" The token has {metrics.holders:,} holders."

        if metrics.liquidity_usd > 0:
            analysis += f" Liquidity: ${metrics.liquidity_usd:,.0f}."

        if red_flags:
            high_severity = [f.description for f in red_flags if f.severity == "high"]
            if high_severity:
                analysis += f" Critical alerts: {'; '.join(high_severity)}"

        return analysis
