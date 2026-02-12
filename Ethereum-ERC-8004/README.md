# EthereumTokenScout

Agent IA ERC-8004 pour l'analyse de tokens ERC-20 sur Ethereum mainnet.

## Fonctionnalites

- Analyse complete des tokens ERC-20 sur Ethereum
- Score de qualite de 0 a 100
- Detection des red flags et risques
- Classification du niveau de risque
- Interface web intuitive

## Installation

```bash
# Creer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dependances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Editer .env avec vos cles API
```

## Configuration

Editez le fichier `.env` :

- `ETH_RPC_URL` : URL RPC Ethereum (par defaut: https://eth.llamarpc.com)
- `ETHERSCAN_API_KEY` : Cle API Etherscan (gratuit sur etherscan.io)
- `PRIVATE_KEY` : Cle privee pour l'enregistrement ERC-8004 (optionnel)

## Lancement

```bash
# Mode developpement
uvicorn app.main:app --reload --port 8000

# Mode production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Interface web
- `GET /api/analyze/{token_address}` - Analyser un token
- `GET /api/trending` - Tokens tendance (placeholder)
- `GET /api/agent` - Informations sur l'agent
- `GET /docs` - Documentation Swagger

## Deploiement sur Render

1. Fork ce repository sur GitHub
2. Connectez votre compte Render a GitHub
3. Creez un nouveau "Web Service"
4. Configurez les variables d'environnement :
   - `ETHERSCAN_API_KEY`
5. Deployez

## Enregistrement ERC-8004

```bash
# Configurer la cle privee dans .env
# Puis executer :
python scripts/register_agent.py --endpoint https://votre-url.onrender.com
```

## Tokens de Test

- USDC: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
- WETH: `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`
- LINK: `0x514910771AF9Ca656af840dff83E8264EcF986CA`
- UNI: `0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984`

## Licence

MIT
