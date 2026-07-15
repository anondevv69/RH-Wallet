# Connect Robinhood Agentic (stocks & options)

Robinhood requires OAuth on **your computer** (localhost). Phone browser alone cannot finish Allow.

## Telegram — one-click desktop app (recommended)

Download **RH Agentic Connect** (Mac/Windows):  
https://github.com/rhagent69/rhwallet-rhagent/releases/latest

Double-click → Connect Robinhood → Allow → Open Telegram. No Terminal.

Setup page: https://rhwallet-rhagent-production.up.railway.app/agentic/setup?for=telegram

## Bankr — one command

```bash
curl -fsSL https://rhagent.bot/scripts/rh-connect.sh | bash
```

Requires **Node.js** and **git**. Run `bankr login` first so your token saves to Bankr automatically.

Setup wizard: https://rhagent.bot/setup

## What happens

1. Script downloads the connect tool (temp folder, deleted after)
2. Browser opens → Robinhood login → tap **Allow**
3. `AGENTIC_TOKEN` saves to your Bankr wallet
4. MCP proxy server is requested via Bankr agent

## Manual alternative

```bash
git clone https://github.com/rhagent69/rhwallet-rhagent.git
cd RH-Wallet/packages/connect
node bin/cli.js
```

## After setup

Ask Bankr: *"What is my Robinhood Agentic buying power?"*

MCP proxy (auto-configured): `https://rhwallet-rhagent-production.up.railway.app/v1/agentic/mcp`

**What you can do once connected:** quotes, fundamentals, earnings, technicals, options, scans, watchlists, and trading — [AGENTIC-CAPABILITIES.md](AGENTIC-CAPABILITIES.md)

## Token expired?

Re-run the one-liner above.
