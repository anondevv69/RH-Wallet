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
| **API** | RH Wallet gateway / x402 | MCP via `https://rhwallet-rhagent-production.up.railway.app/v1/agentic/mcp` |

## Bankr setup (Agentic)

1. Install rh-wallet skill
2. Run one command on your computer — [agentic-connect.md](agentic-connect.md)
3. Ask Bankr: *"What is my Robinhood Agentic buying power?"*

There is **no** `RH_API_KEY` for stocks.

## Bankr `call_mcp_tool` — mandatory format

Stocks and options **must** use Bankr's `call_mcp_tool` against the **`robinhood-agentic`** MCP server. **Never** use `executecli` or skill file staging for market data or trades — this skill has no `scripts/` to stage; instructions load via `useskill` / `useskillfile` only.

### Rules

1. **Server:** `robinhood-agentic` (URL `https://rhwallet-rhagent-production.up.railway.app/v1/agentic/mcp`, header `Authorization: Bearer {{AGENTIC_TOKEN}}`).
2. **`arguments_json` must be a JSON string**, not an object. Bankr rejects `arguments_json: {"symbol": "GME"}` — stringify it.
3. **Tool names:** exact snake_case (`get_option_chains`, not `getoptionchains`).
4. **Skip `tools/list`** — call tools by name directly.

### Wrong vs right

```json
// WRONG — arguments_json as object (schema validation fails before MCP)
{
  "server": "robinhood-agentic",
  "toolName": "get_option_chains",
  "arguments_json": { "symbol": "GME" }
}

// RIGHT — arguments_json as a stringified JSON object
{
  "server": "robinhood-agentic",
  "toolName": "get_option_chains",
  "arguments_json": "{\"symbol\": \"GME\"}"
}
```

### Example calls (copy format exactly)

**GME option chain (this week / nearest expiry):**

```json
{
  "server": "robinhood-agentic",
  "toolName": "get_option_chains",
  "arguments_json": "{\"symbol\": \"GME\"}"
}
```

**GME stock quote:**

```json
{
  "server": "robinhood-agentic",
  "toolName": "get_equity_quotes",
  "arguments_json": "{\"symbols\": [\"GME\"]}"
}
```

**Filter calls for a specific expiry and strike** (after chain returns instrument IDs):

```json
{
  "server": "robinhood-agentic",
  "toolName": "get_option_instruments",
  "arguments_json": "{\"symbol\": \"GME\", \"expiration_date\": \"2026-07-17\", \"type\": \"call\"}"
}
```

**Quote specific option contracts** (use `instrument_id` values from chain/instruments):

```json
{
  "server": "robinhood-agentic",
  "toolName": "get_option_quotes",
  "arguments_json": "{\"instrument_ids\": [\"<id-from-chain>\"]}"
}
```

**Agentic buying power / portfolio (public X — one line, no account numbers):**

```json
{
  "server": "robinhood-agentic",
  "toolName": "get_portfolio",
  "arguments_json": "{}"
}
```

**Typical options research flow:** `get_option_chains` → `get_option_instruments` (filter expiry/type/strike) → `get_option_quotes` → summarize strikes, premiums, IV. For orders: `review_option_order` → user confirms → `place_option_order`.

## MCP tool calls — do not rely on `tools/list`

Bankr may fail `tools/list` when `refresh` is serialized wrong. **Skip listing.** Call Robinhood tools **by exact name** (snake_case):

| Step | Tool name |
|------|-----------|
| Resolve ticker | `search` |
| Price | `get_equity_quotes` |
| Preview buy/sell | `review_equity_order` |
| Execute | `place_equity_order` |

Example equity buy (1 share GRAB): `search` → `get_equity_quotes` (symbol GRAB) → `review_equity_order` → user confirms → `place_equity_order`.

Never guess tool names like `getequityquotes` — use underscores.

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
| `executecli` / "no resource files to stage" / `rhagent-trader` | Wrong tool — use `call_mcp_tool` on `robinhood-agentic`, not CLI or skill staging |
| `arguments_json` expected string, received object | Stringify arguments: `"arguments_json": "{\"symbol\": \"GME\"}"` |
| "MCP not connected" | Run connect command in [agentic-connect.md](agentic-connect.md) |
| Allow button fails on website | Must use localhost script — not hosted OAuth |
| Stock order fails | Check Agentic account funded |
| Agent used crypto API for SPCX | Wrong route — [WALLET-ROUTING.md](WALLET-ROUTING.md) |
