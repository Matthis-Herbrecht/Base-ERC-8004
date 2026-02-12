#!/usr/bin/env python3
"""Test script for token analysis."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.token_analyzer import TokenAnalyzer

# Well-known Ethereum tokens for testing
TEST_TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "DAI": "0x6B175474E89094C44Da98b954EescdeCB5BE3830",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
}


async def main():
    print("=" * 60)
    print("EthereumTokenScout - Token Analysis Test")
    print("=" * 60)

    analyzer = TokenAnalyzer()

    # Default to USDC if no argument provided
    if len(sys.argv) > 1:
        token_address = sys.argv[1]
        token_name = "Custom"
    else:
        token_name = "USDC"
        token_address = TEST_TOKENS[token_name]

    print(f"\nAnalyzing {token_name}: {token_address}")
    print("-" * 60)

    try:
        result = await analyzer.analyze(token_address)

        print(f"\nToken: {result.name} ({result.symbol})")
        print(f"Score: {result.score}/100")
        print(f"Risk Level: {result.risk_level.value}")

        print(f"\nMetrics:")
        print(f"  Holders: {result.metrics.holders:,}")
        print(f"  Liquidity: ${result.metrics.liquidity_usd:,.2f}")
        print(f"  24h Volume: ${result.metrics.volume_24h_usd:,.2f}")
        print(f"  Age: {result.metrics.contract_age_days} days")
        print(f"  Verified: {result.metrics.is_verified}")
        print(f"  Top Holder: {result.metrics.top_holder_percentage:.2f}%")

        if result.red_flags:
            print(f"\nRed Flags:")
            for flag in result.red_flags:
                print(f"  [{flag.severity.upper()}] {flag.description}")

        print(f"\nAnalysis: {result.analysis}")

        if result.price_usd:
            print(f"\nPrice: ${result.price_usd:.6f}")
        if result.market_cap_usd:
            print(f"Market Cap: ${result.market_cap_usd:,.0f}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
