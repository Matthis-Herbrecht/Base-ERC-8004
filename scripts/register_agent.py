#!/usr/bin/env python3
"""
ERC-8004 Agent Registration Script

This script registers the BaseTokenScout agent on Base mainnet.

IMPORTANT: This script performs an ON-CHAIN TRANSACTION.
Only run this once to register the agent.

Usage:
    python scripts/register_agent.py --endpoint https://your-render-app.onrender.com

Requirements:
    - PRIVATE_KEY set in .env file
    - Sufficient ETH in wallet for gas fees
    - Agent card hosted at {endpoint}/static/agent_card.json
"""

import argparse
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.erc8004 import get_erc8004_service
from app.config import get_settings


def main():
    parser = argparse.ArgumentParser(description="Register BaseTokenScout agent on ERC-8004")
    parser.add_argument(
        "--endpoint",
        type=str,
        required=True,
        help="Base URL of the deployed agent (e.g., https://basetokenscout.onrender.com)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate agent card without registering on-chain"
    )
    args = parser.parse_args()

    settings = get_settings()
    erc8004 = get_erc8004_service()

    print("=" * 60)
    print("BaseTokenScout - ERC-8004 Registration")
    print("=" * 60)
    print()

    # Step 1: Generate and save agent card
    print("[1/4] Generating agent card...")
    agent_card_path = "static/agent_card.json"
    os.makedirs("static", exist_ok=True)
    erc8004.save_agent_card(agent_card_path, args.endpoint)
    print(f"      Agent card saved to: {agent_card_path}")

    # Display agent card
    agent_card = erc8004.generate_agent_card(args.endpoint)
    print()
    print("Agent Card Contents:")
    print("-" * 40)
    print(json.dumps(agent_card, indent=2))
    print("-" * 40)
    print()

    if args.dry_run:
        print("[DRY RUN] Skipping on-chain registration.")
        print()
        print("To register on-chain, run without --dry-run flag.")
        print("Make sure your wallet has enough ETH for gas fees.")
        return

    # Step 2: Verify configuration
    print("[2/4] Verifying configuration...")
    if not settings.private_key:
        print("      ERROR: PRIVATE_KEY not set in .env file")
        print("      Please add your private key to register on-chain.")
        sys.exit(1)

    print(f"      Owner address: {settings.agent_owner_address or 'Will be derived from private key'}")
    print(f"      Identity Registry: {settings.identity_registry}")
    print()

    # Step 3: Confirm registration
    print("[3/4] Ready to register on Base mainnet")
    print()
    print("WARNING: This will execute an ON-CHAIN TRANSACTION")
    print("         Make sure you have enough ETH for gas fees.")
    print()

    confirm = input("Type 'REGISTER' to proceed: ")
    if confirm != "REGISTER":
        print("Registration cancelled.")
        sys.exit(0)

    print()

    # Step 4: Register on-chain
    print("[4/4] Registering agent on-chain...")
    metadata_uri = f"{args.endpoint}/static/agent_card.json"
    print(f"      Metadata URI: {metadata_uri}")

    try:
        agent_id = erc8004.register_agent(metadata_uri)

        if agent_id:
            print()
            print("=" * 60)
            print("SUCCESS! Agent registered on Base mainnet")
            print("=" * 60)
            print()
            print(f"Agent ID: {agent_id}")
            print()
            print("Add this to your .env file:")
            print(f"AGENT_ID={agent_id}")
            print()
            print(f"View on Basescan:")
            print(f"https://basescan.org/address/{settings.identity_registry}")
        else:
            print("ERROR: Registration may have failed. Check transaction on Basescan.")

    except Exception as e:
        print(f"ERROR: Registration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
