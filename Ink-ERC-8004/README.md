# InkTokenScout

Agent IA ERC-8004 pour l'analyse de tokens ERC-20 sur la blockchain Ink.

## A propos d'Ink

Ink est une blockchain Layer 2 Ethereum basee sur l'OP Stack, concue pour la DeFi sur le Superchain.

- **Chain ID**: 57073
- **RPC**: https://rpc-gel.inkonchain.com
- **Explorer**: https://explorer.inkonchain.com

## Fonctionnalites

- Analyse complete des tokens ERC-20 sur Ink
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
# Editer .env si necessaire
```

## Configuration

Editez le fichier `.env` :

- `INK_RPC_URL` : URL RPC Ink (par defaut: https://rpc-gel.inkonchain.com)
- `PRIVATE_KEY` : Cle privee pour l'enregistrement ERC-8004 (optionnel)

Note: Ink utilise Blockscout comme explorateur, donc pas besoin de cle API pour les donnees on-chain.

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
4. Deployez (pas de variables d'environnement obligatoires)

## Enregistrement ERC-8004

```bash
# Configurer la cle privee dans .env
# Puis executer :
python scripts/register_agent.py --endpoint https://votre-url.onrender.com
```

## Ressources

- [Ink Docs](https://docs.inkonchain.com/)
- [Ink Explorer](https://explorer.inkonchain.com/)
- [ChainList - Ink](https://chainlist.org/chain/57073)

## Licence

MIT
