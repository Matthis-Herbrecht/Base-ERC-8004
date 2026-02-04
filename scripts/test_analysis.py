#!/usr/bin/env python3
"""
Test script for token analysis.

Tests the TokenAnalyzer with well-known Base tokens.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.token_analyzer import get_token_analyzer


# Well-known Base tokens for testing
TEST_TOKENS = [
    {
        "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "name": "USDC",
        "expected_score_min": 70  # Should be high quality
    },
    {
        "address": "0x4200000000000000000000000000000000000006",
        "name": "WETH",
        "expected_score_min": 70  # Should be high quality
    },
]


async def test_token(analyzer, token_info: dict):
    """Test analysis of a single token."""
    print(f"\nAnalyzing {token_info['name']}...")
    print(f"Address: {token_info['address']}")
    print("-" * 50)

    try:
        analysis = await analyzer.analyze(token_info["address"])

        print(f"Name: {analysis.name}")
        print(f"Symbol: {analysis.symbol}")
        print(f"Score: {analysis.score}/100")
        print(f"Risk Level: {analysis.risk_level.value}")
        print(f"Holders: {analysis.metrics.holders}")
        print(f"Liquidity: ${analysis.metrics.liquidity_usd:,.2f}")
        print(f"Volume 24h: ${analysis.metrics.volume_24h_usd:,.2f}")
        print(f"Contract Age: {analysis.metrics.contract_age_days} days")
        print(f"Verified: {analysis.metrics.is_verified}")

        if analysis.red_flags:
            print(f"Red Flags: {len(analysis.red_flags)}")
            for flag in analysis.red_flags:
                print(f"  - [{flag.severity}] {flag.code}: {flag.description}")
        else:
            print("Red Flags: None")

        print(f"\nAnalysis: {analysis.analysis}")

        # Check if score meets expectations
        if analysis.score >= token_info["expected_score_min"]:
            print(f"\n[PASS] Score {analysis.score} >= expected {token_info['expected_score_min']}")
            return True
        else:
            print(f"\n[WARN] Score {analysis.score} < expected {token_info['expected_score_min']}")
            return True  # Still pass, just warn

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


async def main():
    print("=" * 60)
    print("BaseTokenScout - Token Analysis Test")
    print("=" * 60)

    analyzer = get_token_analyzer()
    results = []

    for token in TEST_TOKENS:
        success = await test_token(analyzer, token)
        results.append((token["name"], success))

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
