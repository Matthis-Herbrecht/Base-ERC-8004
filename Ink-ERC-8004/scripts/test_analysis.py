#!/usr/bin/env python3
"""Test script for token analysis on Ink."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.token_analyzer import TokenAnalyzer


async def main():
    print("=" * 60)
    print("InkTokenScout - Token Analysis Test")
    print("=" * 60)

    analyzer = TokenAnalyzer()

    # Get token address from argument
    if len(sys.argv) > 1:
        token_address = sys.argv[1]
    else:
        print("\nUsage: python test_analysis.py <token_address>")
        print("Example: python test_analysis.py 0x...")
        sys.exit(1)

    print(f"\nAnalyzing token: {token_address}")
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
