# Setup — RH Wallet + Bankr (stateless)

**Start here:** https://rh-wallet-production.up.railway.app/setup

Full guide: [GETTING-STARTED.md](GETTING-STARTED.md)

## 1. Install skill

```
install the skill at https://github.com/anondevv69/RH-Wallet/tree/main/skill
set up rh-wallet
```

## 2. Robinhood Crypto keys

```bash
pip install pynacl
python scripts/generate_rh_keypair.py
```

1. Register **public key** in Robinhood crypto settings (web)
2. Bankr → **Settings → Env Vars**:
   - `RH_API_KEY`
   - `RH_PRIVATE_KEY_BASE64`

Hosted gateway defaults: [hosted-config.md](hosted-config.md)

## 3. Robinhood Agentic (stocks/options)

See [agentic-connect.md](agentic-connect.md) or setup wizard Part C.

## 4. Test

- Crypto: *"What's my Robinhood crypto buying power?"*
- Agentic: *"What is my Robinhood Agentic buying power?"*

## Security

- Keys stay in Bankr env — gateway does not store them
- Never paste private keys into chat
- Never show account numbers in replies
