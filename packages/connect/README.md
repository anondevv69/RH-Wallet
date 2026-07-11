# @rhwallet/connect

One-time Robinhood Agentic OAuth for Bankr users.

Robinhood requires a **localhost** OAuth callback. This CLI runs that on your machine, then saves `AGENTIC_TOKEN` to your Bankr wallet (if you ran `bankr login`).

## Quick start

```bash
npx @rhwallet/connect
```

Before npm publish, run from this repo:

```bash
node bin/cli.js
```

Or:

```bash
npx github:anondevv69/RH-Wallet/packages/connect
```

Setup wizard: https://rh-wallet-production.up.railway.app/agentic/setup

## What it does

1. Opens Robinhood login in your browser
2. Listens on `127.0.0.1` for the OAuth callback
3. Saves `AGENTIC_TOKEN` (+ refresh token if provided) to Bankr via API
4. Optionally asks Bankr to add the MCP proxy server

After that, trade stocks/options through Bankr only — computer can be off.

## Options

- `--no-bankr` — print token only, don't call Bankr API
- `--no-mcp` — skip MCP auto-setup prompt
- `--bankr-api-key sk_...` — explicit API key (else reads `~/.bankr/config.json`)

## Trust

Your token is sent **only to Bankr's API** (`api.bankr.bot/agent/env`) using your API key. RH Wallet Railway proxy never stores it.
