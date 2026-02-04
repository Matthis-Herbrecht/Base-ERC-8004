# BaseTokenScout

An ERC-8004 AI agent that analyzes token quality and safety on Base L2.

## Features

- **Token Analysis**: Analyze any ERC-20 token on Base mainnet
- **Quality Scores**: Get a score from 0-100 based on multiple metrics
- **Risk Assessment**: Automatic classification (scam, high_risk, moderate, quality)
- **Red Flag Detection**: Identifies honeypots, low liquidity, concentration risks
- **Trending Tokens**: Track recently analyzed tokens sorted by volume
- **ERC-8004 Compliant**: Registered on-chain with the AI Agent registry

## Security

This agent is **READ-ONLY**:
- No automatic transactions
- No fund management capabilities
- No private key access (except for one-time registration)
- Rate limited to prevent abuse

## API Endpoints

### Analyze a Token

```bash
curl https://basetokenscout.onrender.com/analyze/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
```

Response:
```json
{
  "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "name": "USD Coin",
  "symbol": "USDC",
  "score": 95,
  "risk_level": "quality",
  "metrics": {
    "holders": 125000,
    "volume_24h_usd": 50000000,
    "liquidity_usd": 100000000,
    "contract_age_days": 365,
    "is_verified": true,
    "top_holder_percentage": 5.2
  },
  "red_flags": [],
  "analysis": "Quality token with score 95/100. Liquidity: $100,000,000. 125000 holders. Contract age: 365 days. Contract verified."
}
```

### Get Trending Tokens

```bash
curl https://basetokenscout.onrender.com/trending?limit=10
```

### Get Agent Info

```bash
curl https://basetokenscout.onrender.com/agent/info
```

### Health Check

```bash
curl https://basetokenscout.onrender.com/health
```

## Risk Levels

| Level | Score | Description |
|-------|-------|-------------|
| `scam` | 0-29 | Possible scam - avoid |
| `high_risk` | 30-49 | High risk - proceed with caution |
| `moderate` | 50-69 | Moderate risk - do your research |
| `quality` | 70-100 | Quality token - relatively safe |

## Scoring Criteria

The quality score (0-100) is calculated based on:

| Metric | Weight | Description |
|--------|--------|-------------|
| Holders | 20% | More holders = better distribution |
| Liquidity | 25% | More liquidity = safer to trade |
| Volume | 15% | More volume = more active market |
| Age | 15% | Older contracts = more established |
| Verified | 10% | Verified source = more transparent |
| Distribution | 15% | Lower concentration = less manipulation |

## Red Flags Detected

- `NO_LIQUIDITY` / `LOW_LIQUIDITY`: Insufficient liquidity for trading
- `VERY_FEW_HOLDERS` / `FEW_HOLDERS`: Concentrated ownership
- `HIGH_CONCENTRATION` / `MODERATE_CONCENTRATION`: Top holder owns too much
- `VERY_NEW_CONTRACT` / `NEW_CONTRACT`: Contract is recently deployed
- `UNVERIFIED_CONTRACT`: Source code not verified on Basescan
- `NO_VOLUME`: No significant trading activity

## Local Development

### Prerequisites

- Python 3.10+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/basetokenscout.git
cd basetokenscout
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration:
```bash
BASE_RPC_URL=https://mainnet.base.org
BASESCAN_API_KEY=your_api_key_here
```

6. Run the server:
```bash
uvicorn app.main:app --reload
```

7. Open http://localhost:8000/docs for the API documentation.

### Testing

Run the test script:
```bash
python scripts/test_analysis.py
```

## Deployment on Render.com

### 1. Create a Render Account

Go to [render.com](https://render.com) and sign up for a free account.

### 2. Connect Your Repository

1. Click "New +" and select "Web Service"
2. Connect your GitHub repository
3. Select the repository

### 3. Configure the Service

The `render.yaml` file in this repository will auto-configure:
- Runtime: Python 3.10
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4. Set Environment Variables

In the Render dashboard, add:
- `BASE_RPC_URL`: `https://mainnet.base.org`
- `BASESCAN_API_KEY`: Your Basescan API key
- `AGENT_ENDPOINT`: Your Render URL (e.g., `https://basetokenscout.onrender.com`)

### 5. Deploy

Click "Deploy" and wait for the build to complete.

## ERC-8004 Registration

### Register on Base Mainnet

1. Make sure your `.env` has:
   - `PRIVATE_KEY`: Your wallet private key (for signing the registration transaction)
   - Sufficient ETH in the wallet for gas fees

2. Run the registration script:
```bash
python scripts/register_agent.py --endpoint https://your-app.onrender.com
```

3. Follow the prompts to register on-chain.

4. Add the returned `AGENT_ID` to your `.env` file.

### Dry Run

To test without registering:
```bash
python scripts/register_agent.py --endpoint https://your-app.onrender.com --dry-run
```

## ERC-8004 Contracts

- **Identity Registry**: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- **Reputation Registry**: `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`

## Project Structure

```
basetokenscout/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration settings
│   ├── models.py         # Pydantic models
│   └── routers/
│       ├── analyze.py    # /analyze endpoint
│       ├── trending.py   # /trending endpoint
│       └── agent.py      # /agent endpoint
│
├── services/
│   ├── blockchain.py     # Web3 interactions
│   ├── token_analyzer.py # Core analysis logic
│   ├── erc8004.py        # ERC-8004 registration
│   └── data_fetcher.py   # External API calls
│
├── static/
│   └── agent_card.json   # ERC-8004 metadata
│
├── scripts/
│   ├── register_agent.py # Registration script
│   └── test_analysis.py  # Test script
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── render.yaml           # Render deployment config
```

## API Rate Limits

- `/analyze/{address}`: 10 requests per minute per IP
- `/health`: 60 requests per minute per IP
- Other endpoints: No specific limits

## Data Sources

- **Base RPC**: Token contract data
- **Basescan API**: Contract verification, holder data, transaction history
- **DexScreener**: DEX liquidity and volume data
- **CoinGecko**: Token prices (fallback)

## Roadmap

- [ ] Redis caching for improved performance
- [ ] Historical score tracking
- [ ] Webhook notifications for new tokens
- [ ] Frontend dashboard
- [ ] Multi-chain support (Arbitrum, Optimism)

## License

MIT

## Disclaimer

This tool provides informational analysis only. It is NOT financial advice. Always do your own research before trading any tokens. The creators are not responsible for any financial losses incurred from using this tool.
