# Robinhood Agentic Trading (stocks & options)

Robinhood's official agent product for **equities and options** — separate from **Robinhood Crypto** (rh-wallet).

**Bankr users:** do not connect `https://agent.robinhood.com/mcp/trading` directly. Use the RH Wallet proxy + one-time localhost OAuth — [agentic-connect.md](agentic-connect.md).

Robinhood docs: [Agentic overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)

**Full capability list (tools + example prompts):** [AGENTIC-CAPABILITIES.md](AGENTIC-CAPABILITIES.md)

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

When MCP is connected, map user intent to Robinhood MCP tools. Full catalog: [AGENTIC-CAPABILITIES.md](AGENTIC-CAPABILITIES.md).

| User says | MCP tools (typical flow) |
|-----------|--------------------------|
| "What's my Robinhood stock portfolio?" / buying power | `get_portfolio` (prefer on **public X** — avoid `get_accounts`) |
| "Find ticker for SpaceX ETF" | `search` |
| "Quote SPCX" / "price of GME" | `search` → `get_equity_quotes` (up to 20 symbols) |
| "NVDA RSI" / fundamentals / earnings | `get_equity_technical_indicators`, `get_equity_fundamentals`, `get_earnings_results` |
| "Earnings this week" | `get_earnings_calendar` |
| "Is SPCX fractional?" | `get_equity_tradability` |
| "100 most popular on Robinhood" | `get_popular_watchlists` |
| "Run a momentum scan" | `create_scan` / `run_scan` |
| "Buy $100 of SPCX" | `review_equity_order` → confirm → `place_equity_order` |
| "Buy a GME call" | `get_option_chains` → `get_option_quotes` → confirm → `place_option_order` |

**Account vs market:** quotes, fundamentals, earnings, and indexes are **not** your portfolio data — but they still use your MCP session. Positions, orders, and buying power **are** account-specific.

**Always confirm** before placing orders on public X — see [RESPONSE-SAFETY.md](RESPONSE-SAFETY.md).

**Public X:** never post account numbers or list non-Agentic accounts (margin, IRA). Use `get_portfolio`, one-line Agentic summary only.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "MCP not connected" | Run connect command in [agentic-connect.md](agentic-connect.md) |
| Allow button fails on website | Must use localhost script — not hosted OAuth |
| Stock order fails | Check Agentic account funded |
| Agent used crypto API for SPCX | Wrong route — [WALLET-ROUTING.md](WALLET-ROUTING.md) |
