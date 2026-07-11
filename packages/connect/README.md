# @rhwallet/connect

One-time Robinhood Agentic OAuth for Bankr users.

## Recommended — one command

```bash
curl -fsSL https://raw.githubusercontent.com/anondevv69/RH-Wallet/main/scripts/rh-connect.sh | bash
```

Setup wizard: https://rh-wallet-production.up.railway.app/agentic/setup

## Manual

```bash
git clone https://github.com/anondevv69/RH-Wallet.git
cd RH-Wallet/packages/connect
node bin/cli.js
```

Run `bankr login` first so your token auto-saves to Bankr.

## Trust

Token is sent only to Bankr API (`api.bankr.bot/agent/env`). RH Wallet never stores it.
