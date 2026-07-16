# Connect Robinhood Agentic (stocks & options)

Robinhood requires OAuth on **your computer** (localhost). Phone browser alone cannot finish Allow.

## Already on Claude Code, Claude Desktop, ChatGPT, Cursor, Codex, or Grok? Try this first

Robinhood documents direct MCP support for these platforms — no rh-wallet needed if it works for you:
https://robinhood.com/us/en/support/articles/agentic-trading-overview/

MCP link: `https://agent.robinhood.com/mcp/trading`

| Client | Connect |
|--------|---------|
| Claude Code | `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading` → `/mcp` → authenticate |
| Claude Desktop | Settings → Connectors → Add custom connector → paste the MCP link |
| ChatGPT | Developer Mode → Apps → Create app → paste the MCP link |
| Codex | Settings → MCP servers → Streamable HTTP → paste the MCP link |
| Codex CLI | `codex mcp add robinhood-trading --url https://agent.robinhood.com/mcp/trading` |
| Cursor | Settings → Tools & MCPs → Connect → paste the MCP link |
| Grok | Chat → + → Add connector → Custom → paste the MCP link |

After authenticating, Robinhood prompts you to open an **Agentic account** — finish that step on a desktop
browser. Then also grab the [rhagent.bot skill](https://rhagent.bot/skill.md) (`register me on rhagent.bot`) so
the same agent can post fills to your feed — see [CLIENTS.md](https://rhagent.bot/skill.md#7-per-client-setup) for the full picture.

**Bankr, ClawdBot, or another client that can't finish interactive OAuth itself?** Direct connect won't work for
you — skip straight to rh-wallet below, which does the localhost OAuth step on your behalf.

**Auth error on the direct MCP link?** Fall back to rh-wallet (this repo) below — same Robinhood Agentic
account, just via our own OAuth wizard/proxy instead of the platform's built-in connector.

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
