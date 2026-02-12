# MegaETHTokenScout

ERC-8004 AI Agent for analyzing ERC-20 tokens on MegaETH blockchain.

## Features

- Token quality scoring (0-100)
- Risk factor identification
- Holder distribution analysis
- Liquidity and volume metrics
- ERC-8004 compliant agent card

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run locally
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /api/analyze/{token_address}` - Analyze a token
- `GET /api/trending` - Get trending tokens
- `GET /docs` - API documentation

## Deployment

Deploy to Render using the included `render.yaml` configuration.

## Chain Info

- **Network**: MegaETH
- **Chain ID**: 6342
- **RPC**: https://carrot.megaeth.com/rpc
- **Explorer**: https://megaeth.blockscout.com
