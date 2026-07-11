# Connect Robinhood Agentic (stocks & options)

One-time setup for Bankr users. Robinhood requires OAuth on **your computer** (localhost). After this, trade through Bankr only.

## One command

```bash
curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
```

Requires **Node.js** and **git**. Run `bankr login` first so your token saves to Bankr automatically.

Setup wizard: https://rh-wallet-production.up.railway.app/setup

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

MCP proxy (auto-configured): `https://rh-wallet-production.up.railway.app/v1/agentic/mcp`

**What you can do once connected:** quotes, fundamentals, earnings, technicals, options, scans, watchlists, and trading — [AGENTIC-CAPABILITIES.md](AGENTIC-CAPABILITIES.md)

## Token expired?

Re-run the one-liner above.
