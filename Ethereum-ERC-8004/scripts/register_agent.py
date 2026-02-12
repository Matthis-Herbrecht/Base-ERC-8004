#!/usr/bin/env python3
"""Script to register EthereumTokenScout as an ERC-8004 agent."""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from services.erc8004 import ERC8004Service


async def main():
    parser = argparse.ArgumentParser(description="Register EthereumTokenScout as ERC-8004 agent")
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Public endpoint URL for the agent (e.g., https://ethereumtokenscout.onrender.com)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate agent card without registering on-chain"
    )
    args = parser.parse_args()

    settings = get_settings()
    erc8004 = ERC8004Service()

    print("=" * 60)
    print("EthereumTokenScout - ERC-8004 Agent Registration")
    print("=" * 60)

    # Step 1: Generate and save agent card
    print("\n[1/4] Generating agent card...")
    settings.agent_endpoint = args.endpoint
    card_path = erc8004.save_agent_card()
    print(f"      Agent card saved to: {card_path}")

    # Step 2: Display agent card
    print("\n[2/4] Agent card preview:")
    card = erc8004.generate_agent_card()
    print(f"      Name: {card['name']}")
    print(f"      Description: {card['description']}")
    print(f"      Endpoint: {args.endpoint}")
    print(f"      Chain: Ethereum (chainId: 1)")

    if args.dry_run:
        print("\n[DRY RUN] Skipping on-chain registration")
        return

    # Step 3: Verify configuration
    print("\n[3/4] Verifying configuration...")
    if not settings.private_key:
        print("      ERROR: PRIVATE_KEY not set in .env")
        print("      Please add your wallet private key to register on-chain")
        sys.exit(1)

    print(f"      Identity Registry: {settings.identity_registry}")
    print(f"      Reputation Registry: {settings.reputation_registry}")

    # Step 4: Register on-chain
    print("\n[4/4] Ready to register on-chain")
    metadata_uri = f"{args.endpoint}/static/agent_card.json"
    print(f"      Metadata URI: {metadata_uri}")

    confirm = input("\n      Type 'REGISTER' to proceed: ")
    if confirm != "REGISTER":
        print("      Registration cancelled")
        sys.exit(0)

    print("\n      Submitting transaction...")
    try:
        result = await erc8004.register_agent(metadata_uri)
        print(f"\n      SUCCESS!")
        print(f"      Transaction: {result['tx_hash']}")
        print(f"      Block: {result['block_number']}")
        print(f"      Gas used: {result['gas_used']}")
        print(f"\n      Your agent is now registered on Ethereum!")
        print(f"      View on Etherscan: https://etherscan.io/tx/{result['tx_hash']}")
    except Exception as e:
        print(f"\n      ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
