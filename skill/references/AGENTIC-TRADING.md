# Robinhood Agentic Trading (stocks & options)

Robinhood's official agent product for **equities and options** — separate from **Robinhood Crypto** (rh-wallet).

**Bankr users:** do not connect `https://agent.robinhood.com/mcp/trading` directly. Use the RH Wallet proxy + one-time localhost OAuth — [agentic-connect.md](agentic-connect.md).

Robinhood docs: [Agentic overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)

## Two products, two setups

| | **Robinhood Crypto** (rh-wallet) | **Robinhood Agentic** (stocks/options) |
|--|-----------------------------------|----------------------------------------|
| **Buy** | BTC-USD, DOGE-USD, … | SPCX, GME, AAPL, options calls/puts |
| **Auth** | `RH_API_KEY` + `RH_PRIVATE_KEY_BASE64` in Bankr env | `AGENTIC_TOKEN` in Bankr env (one-time OAuth) |
| **Account** | Crypto account | Dedicated **Agentic** account |
| **API** | RH Wallet gateway / x402 | MCP via `https://rh-wallet-production.up.railway.app/v1/agentic/mcp` |

## Bankr setup (Agentic)

1. Install rh-wallet skill
2. Run one command on your computer — [agentic-connect.md](agentic-connect.md)
3. Ask Bankr: *"What is my Robinhood Agentic buying power?"*

There is **no** `RH_API_KEY` for stocks.

## Natural language → Agentic routing

When MCP is connected, map user intent to Robinhood MCP tools:

| User says | MCP tools (typical flow) |
|-----------|--------------------------|
| "What's my Robinhood stock portfolio?" | `get_portfolio`, `get_accounts` |
| "Quote on SPCX" / "price of GME" | `search` → `get_equity_quotes` |
| "Buy $100 of SPCX" | `review_equity_order` → confirm → `place_equity_order` |
| "Buy a GME call" | option chain tools → confirm → `place_option_order` |

**Always confirm** before placing orders on public X — see [RESPONSE-SAFETY.md](RESPONSE-SAFETY.md).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "MCP not connected" | Run connect command in [agentic-connect.md](agentic-connect.md) |
| Allow button fails on website | Must use localhost script — not hosted OAuth |
| Stock order fails | Check Agentic account funded |
| Agent used crypto API for SPCX | Wrong route — [WALLET-ROUTING.md](WALLET-ROUTING.md) |
