"""Token analyzer service - core analysis logic."""

import logging
from datetime import datetime
from typing import List, Optional

from app.models import (
    TokenAnalysis,
    TokenMetrics,
    RedFlag,
    RiskLevel
)
from services.blockchain import get_blockchain_service
from services.data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)


class TokenAnalyzer:
    """
    Analyzes ERC-20 tokens on Base and provides quality scores.

    This is a READ-ONLY analyzer - no transactions are ever made.
    """

    # Scoring weights (total = 100)
    WEIGHTS = {
        "holders": 20,       # More holders = more distributed
        "liquidity": 25,     # More liquidity = safer to trade
        "volume": 15,        # More volume = more active
        "age": 15,           # Older = more established
        "verified": 10,      # Verified contract = more transparent
        "distribution": 15,  # Better distribution = less manipulation risk
    }

    def __init__(self):
        """Initialize analyzer."""
        self.blockchain = get_blockchain_service()
        self.data_fetcher = get_data_fetcher()

    async def analyze(self, token_address: str) -> TokenAnalysis:
        """
        Analyze a token and return comprehensive analysis.

        Args:
            token_address: The token contract address

        Returns:
            TokenAnalysis object with scores and metrics
        """
        # Validate address
        if not self.blockchain.is_valid_address(token_address):
            raise ValueError(f"Invalid address: {token_address}")

        checksum_address = self.blockchain.to_checksum_address(token_address)

        # Get basic token info from blockchain
        token_info = self.blockchain.get_token_info(checksum_address)
        if not token_info:
            raise ValueError(f"Could not fetch token info. May not be a valid ERC-20 token.")

        # Fetch additional data
        holder_count = await self.data_fetcher.get_holder_count(checksum_address)
        is_verified = await self.data_fetcher.is_contract_verified(checksum_address)
        contract_age = await self.data_fetcher.get_contract_age_days(checksum_address)
        dex_data = await self.data_fetcher.get_dex_data(checksum_address)
        top_holders = await self.data_fetcher.get_top_holders(checksum_address, limit=10)

        # Use DEX age as fallback if contract age is 0
        if contract_age == 0:
            contract_age = dex_data.get("age_days", 0)

        # Calculate top holder percentage
        top_holder_percentage = self._calculate_top_holder_percentage(
            top_holders, token_info["total_supply"], token_info["decimals"]
        )

        # Build metrics
        metrics = TokenMetrics(
            holders=holder_count,
            volume_24h_usd=dex_data.get("volume_24h_usd", 0),
            liquidity_usd=dex_data.get("liquidity_usd", 0),
            contract_age_days=contract_age,
            is_verified=is_verified,
            top_holder_percentage=top_holder_percentage
        )

        # Detect red flags
        red_flags = self._detect_red_flags(metrics, token_info)

        # Calculate score
        score = self._calculate_score(metrics, red_flags)

        # Determine risk level
        risk_level = self._get_risk_level(score)

        # Get price info
        price_usd = dex_data.get("price_usd")
        if not price_usd:
            price_usd = await self.data_fetcher.get_token_price_coingecko(checksum_address)

        # Calculate market cap
        market_cap = None
        if price_usd and token_info["total_supply"] > 0:
            supply_formatted = token_info["total_supply"] / (10 ** token_info["decimals"])
            market_cap = price_usd * supply_formatted

        # Generate analysis summary
        analysis_summary = self._generate_summary(
            token_info, metrics, red_flags, score, risk_level
        )

        return TokenAnalysis(
            address=checksum_address,
            name=token_info["name"],
            symbol=token_info["symbol"],
            decimals=token_info["decimals"],
            total_supply=token_info["total_supply_formatted"],
            score=score,
            risk_level=risk_level,
            metrics=metrics,
            red_flags=red_flags,
            analysis=analysis_summary,
            price_usd=price_usd,
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

    def _detect_red_flags(self, metrics: TokenMetrics, token_info: dict) -> List[RedFlag]:
        """Detect potential red flags for the token."""
        red_flags = []

        # No liquidity
        if metrics.liquidity_usd < 1000:
            red_flags.append(RedFlag(
                code="NO_LIQUIDITY",
                description="Very low or no liquidity (< $1,000). Trading may be impossible or result in high slippage.",
                severity="high"
            ))
        elif metrics.liquidity_usd < 10000:
            red_flags.append(RedFlag(
                code="LOW_LIQUIDITY",
                description="Low liquidity (< $10,000). High slippage risk.",
                severity="medium"
            ))

        # Few holders
        if metrics.holders < 10:
            red_flags.append(RedFlag(
                code="VERY_FEW_HOLDERS",
                description="Less than 10 holders. Extremely concentrated ownership.",
                severity="high"
            ))
        elif metrics.holders < 50:
            red_flags.append(RedFlag(
                code="FEW_HOLDERS",
                description="Less than 50 holders. Low distribution.",
                severity="medium"
            ))

        # High concentration
        if metrics.top_holder_percentage > 50:
            red_flags.append(RedFlag(
                code="HIGH_CONCENTRATION",
                description=f"Top holder owns {metrics.top_holder_percentage:.1f}% of supply. Rug pull risk.",
                severity="high"
            ))
        elif metrics.top_holder_percentage > 20:
            red_flags.append(RedFlag(
                code="MODERATE_CONCENTRATION",
                description=f"Top holder owns {metrics.top_holder_percentage:.1f}% of supply.",
                severity="medium"
            ))

        # New contract
        if metrics.contract_age_days < 7:
            red_flags.append(RedFlag(
                code="VERY_NEW_CONTRACT",
                description=f"Contract is only {metrics.contract_age_days} days old. Higher risk.",
                severity="medium"
            ))
        elif metrics.contract_age_days < 30:
            red_flags.append(RedFlag(
                code="NEW_CONTRACT",
                description=f"Contract is {metrics.contract_age_days} days old. Relatively new.",
                severity="low"
            ))

        # Unverified contract
        if not metrics.is_verified:
            red_flags.append(RedFlag(
                code="UNVERIFIED_CONTRACT",
                description="Contract source code is not verified on Basescan.",
                severity="medium"
            ))

        # No trading volume
        if metrics.volume_24h_usd < 100:
            red_flags.append(RedFlag(
                code="NO_VOLUME",
                description="No significant trading volume in 24h.",
                severity="medium"
            ))

        return red_flags

    def _calculate_score(self, metrics: TokenMetrics, red_flags: List[RedFlag]) -> int:
        """
        Calculate quality score (0-100) based on metrics.

        Higher score = better quality/safer token.
        """
        score = 0

        # Holders score (0-20 points)
        if metrics.holders >= 1000:
            score += self.WEIGHTS["holders"]
        elif metrics.holders >= 500:
            score += int(self.WEIGHTS["holders"] * 0.8)
        elif metrics.holders >= 100:
            score += int(self.WEIGHTS["holders"] * 0.6)
        elif metrics.holders >= 50:
            score += int(self.WEIGHTS["holders"] * 0.4)
        elif metrics.holders >= 10:
            score += int(self.WEIGHTS["holders"] * 0.2)

        # Liquidity score (0-25 points)
        if metrics.liquidity_usd >= 1000000:
            score += self.WEIGHTS["liquidity"]
        elif metrics.liquidity_usd >= 100000:
            score += int(self.WEIGHTS["liquidity"] * 0.8)
        elif metrics.liquidity_usd >= 50000:
            score += int(self.WEIGHTS["liquidity"] * 0.6)
        elif metrics.liquidity_usd >= 10000:
            score += int(self.WEIGHTS["liquidity"] * 0.4)
        elif metrics.liquidity_usd >= 1000:
            score += int(self.WEIGHTS["liquidity"] * 0.2)

        # Volume score (0-15 points)
        if metrics.volume_24h_usd >= 100000:
            score += self.WEIGHTS["volume"]
        elif metrics.volume_24h_usd >= 50000:
            score += int(self.WEIGHTS["volume"] * 0.8)
        elif metrics.volume_24h_usd >= 10000:
            score += int(self.WEIGHTS["volume"] * 0.6)
        elif metrics.volume_24h_usd >= 1000:
            score += int(self.WEIGHTS["volume"] * 0.4)
        elif metrics.volume_24h_usd >= 100:
            score += int(self.WEIGHTS["volume"] * 0.2)

        # Age score (0-15 points)
        if metrics.contract_age_days >= 365:
            score += self.WEIGHTS["age"]
        elif metrics.contract_age_days >= 180:
            score += int(self.WEIGHTS["age"] * 0.8)
        elif metrics.contract_age_days >= 90:
            score += int(self.WEIGHTS["age"] * 0.6)
        elif metrics.contract_age_days >= 30:
            score += int(self.WEIGHTS["age"] * 0.4)
        elif metrics.contract_age_days >= 7:
            score += int(self.WEIGHTS["age"] * 0.2)

        # Verified score (0-10 points)
        if metrics.is_verified:
            score += self.WEIGHTS["verified"]

        # Distribution score (0-15 points)
        if metrics.top_holder_percentage <= 5:
            score += self.WEIGHTS["distribution"]
        elif metrics.top_holder_percentage <= 10:
            score += int(self.WEIGHTS["distribution"] * 0.8)
        elif metrics.top_holder_percentage <= 20:
            score += int(self.WEIGHTS["distribution"] * 0.6)
        elif metrics.top_holder_percentage <= 30:
            score += int(self.WEIGHTS["distribution"] * 0.4)
        elif metrics.top_holder_percentage <= 50:
            score += int(self.WEIGHTS["distribution"] * 0.2)

        # Penalty for high severity red flags
        high_severity_count = sum(1 for rf in red_flags if rf.severity == "high")
        score = max(0, score - (high_severity_count * 10))

        return min(100, max(0, score))

    def _get_risk_level(self, score: int) -> RiskLevel:
        """Get risk level based on score."""
        if score < 30:
            return RiskLevel.SCAM
        elif score < 50:
            return RiskLevel.HIGH_RISK
        elif score < 70:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.QUALITY

    def _generate_summary(
        self,
        token_info: dict,
        metrics: TokenMetrics,
        red_flags: List[RedFlag],
        score: int,
        risk_level: RiskLevel
    ) -> str:
        """Generate human-readable analysis summary."""
        parts = []

        # Risk assessment
        risk_emoji = {
            RiskLevel.SCAM: "Possible scam",
            RiskLevel.HIGH_RISK: "High risk",
            RiskLevel.MODERATE: "Moderate",
            RiskLevel.QUALITY: "Quality"
        }
        parts.append(f"{risk_emoji[risk_level]} token with score {score}/100.")

        # Key metrics
        if metrics.liquidity_usd > 0:
            parts.append(f"Liquidity: ${metrics.liquidity_usd:,.0f}.")
        else:
            parts.append("No liquidity found.")

        if metrics.holders > 0:
            parts.append(f"{metrics.holders} holders.")

        if metrics.contract_age_days > 0:
            parts.append(f"Contract age: {metrics.contract_age_days} days.")

        if metrics.is_verified:
            parts.append("Contract verified.")
        else:
            parts.append("Contract NOT verified.")

        # Red flags summary
        high_flags = [rf for rf in red_flags if rf.severity == "high"]
        if high_flags:
            flag_descriptions = [rf.description.split(".")[0] for rf in high_flags[:2]]
            parts.append(f"Warnings: {'; '.join(flag_descriptions)}.")

        return " ".join(parts)


def get_token_analyzer() -> TokenAnalyzer:
    """Get token analyzer instance."""
    return TokenAnalyzer()
