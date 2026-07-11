---
name: rh-wallet
description: >
  Manage Robinhood Crypto (pairs like BTC-USD) via RH Wallet gateway or paid
  x402 API, and route Robinhood stocks/options to Agentic MCP. Use for Robinhood
  crypto prices, balance, buy/sell crypto, OR stocks (SPCX, GME), options
  (calls/puts), quotes, fundamentals, earnings, technicals, and scans when Agentic
  MCP is connected. Crypto: RH_API_KEY + RH_PRIVATE_KEY_BASE64 in Bankr env +
  optional x402 (USDC on Base). Stocks/options: connect via
  https://rhwallet-rhagent-production.up.railway.app/setup. Capabilities:
  references/AGENTIC-CAPABILITIES.md. PUBLIC X: never tweet account numbers (including
  masked ••••XXXX) or list margin/IRA accounts — see references/RESPONSE-SAFETY.md.
tags: [robinhood, crypto, trading, wallet, bankr, usd]
visibility: public
metadata:
  clawdbot:
    emoji: "🟩"
    homepage: "https://github.com/rhagent69/rhwallet-rhagent"
    requires:
      bins: [curl, jq]
      optional_bins: [bankr]
---

# Robinhood Crypto Wallet (via RH Wallet Gateway)

Trade and inspect a **Robinhood Crypto** account through a **stateless RH Wallet Gateway**. Robinhood keys live in **Bankr Agent tool environment** — the gateway signs requests but does **not** store your keys.

> **US only.** Robinhood Crypto Trading API is available to US customers and is subject to the Robinhood Crypto Customer Agreement.

For **full setup steps** see [references/GETTING-STARTED.md](references/GETTING-STARTED.md).  
Setup wizard: **https://rhwallet-rhagent-production.up.railway.app/setup**  
Hosted URL + public gateway secret: [references/hosted-config.md](references/hosted-config.md).  
For safety see [references/trading-safety.md](references/trading-safety.md).  
For endpoints see [references/api-reference.md](references/api-reference.md).  
For paid x402 API + natural-language routing see [references/x402.md](references/x402.md).  
For **Agentic connect** see [references/agentic-connect.md](references/agentic-connect.md).  
For **what Agentic can do** (quotes, fundamentals, earnings, options, scans) see [references/AGENTIC-CAPABILITIES.md](references/AGENTIC-CAPABILITIES.md).  
For which product to use see [references/WALLET-ROUTING.md](references/WALLET-ROUTING.md).  
For **public X safety** (never tweet account numbers — mandatory) see [references/RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md).

## Public X / tweets — mandatory (rule #0)

If the reply will be posted to **X/Twitter** (including @bankrbot automated replies):

1. **Never** include account numbers — masked (`••••6789`), last-4, or full
2. **Never** use headings like `Agentic Account (••••XXXX)` or list margin/IRA/other accounts
3. For *"what's in my Agentic wallet?"* → **`get_portfolio` only** (not `get_accounts`); one line:

   `Robinhood Agentic: $X portfolio · $X cash · $X buying power · [holdings or "no positions"]`

4. Run the pre-tweet checklist in [RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md) before posting

---

## "Connect Agentic" — reply template (use verbatim)

When the user says anything like **"connect agentically"**, **"connect Robinhood Agentic"**, **"set up stocks on Robinhood"**, **"I want to trade stocks through Bankr"**, or **"connect my agentic account"**:

1. Run `what env vars do I have?` — if `AGENTIC_TOKEN` is already set, say Agentic is connected and offer a buying-power check.
2. If **not** connected, reply with this (include the link — do not skip it):

---

**Connect Robinhood Agentic (stocks & options)**

Open the setup guide — all steps are there:

**https://rhwallet-rhagent-production.up.railway.app/setup** (Part C)

Quick version on your computer (~2 min, one-time):

1. Run `bankr login` (same machine)
2. Run in Terminal:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
   ```
3. Browser opens → sign in to Robinhood → tap **Allow** on your Agentic account
4. Come back and ask: *"What is my Robinhood Agentic buying power?"*

After this, everything runs through Bankr — your computer can be off.

We never store your token on our servers; it lives in your Bankr vault only.

---

Do **not** send users to `agent.robinhood.com/mcp/trading` directly — use the Railway proxy flow above.

---

## First-time setup (auto-run on install or "connect Robinhood")

When this skill is first loaded, or the user says **"set up rh-wallet"**, **"connect Robinhood"**, or **"set up my Robinhood account"**:

**Always start by sending the user the setup wizard:**

> **RH Wallet setup:** https://rhwallet-rhagent-production.up.railway.app/setup  
> Follow Parts A → B (crypto) → C (Agentic). Takes ~5 minutes one-time.

Then walk through each part. Full reference: [references/GETTING-STARTED.md](references/GETTING-STARTED.md).

---

### Part A — Install skill (Bankr)

1. User installs (if not already):
   ```
   install the skill at https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill
   ```
2. User says: `set up rh-wallet`

---

### Part B — Robinhood Crypto (BTC, DOGE, ETH)

Run: `what env vars do I have?`

| Env var | Status |
|---------|--------|
| `RH_API_KEY` + `RH_PRIVATE_KEY_BASE64` present | Crypto ready ✓ |
| Missing | Walk through [references/setup.md](references/setup.md) |

Test: *"What's my Robinhood crypto buying power?"*

---

### Part C — Robinhood Agentic (stocks & options)

If `AGENTIC_TOKEN` is missing:

1. **Setup page:** https://rhwallet-rhagent-production.up.railway.app/setup (Part C)
2. User runs on their computer:
   ```bash
   bankr login
   curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
   ```
3. Browser → Robinhood → **Allow**
4. Token auto-saves to Bankr if `bankr login` was run on that machine
5. Auto-add MCP if missing:
   ```
   add an MCP server named "robinhood-agentic" at https://rhwallet-rhagent-production.up.railway.app/v1/agentic/mcp with Streamable HTTP transport and Authorization header Bearer {{AGENTIC_TOKEN}}
   ```
6. Test: *"What is my Robinhood Agentic buying power?"* — **never show account numbers** ([RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md))

After setup, all trading runs through Bankr 24/7 — computer can be off.

---

## Prerequisites — two setups

### A. Robinhood Crypto (rh-wallet) — env vars

Set in **Bankr → gear → Agent tool environment**:

| Variable | Required? | What |
|----------|-----------|------|
| `RH_API_KEY` | **Yes** | Robinhood API key (`rh-api-...`) from crypto settings |
| `RH_PRIVATE_KEY_BASE64` | **Yes** | Ed25519 private key from `scripts/generate_rh_keypair.py` |
| `RH_GATEWAY_SECRET` | No | Defaults to public value in [hosted-config.md](references/hosted-config.md) |
| `RH_WALLET_API_URL` | No | Defaults to `https://rhwallet-rhagent-production.up.railway.app` |
| `RHAGENTS_AGENT_KEY` | No | rhagents API key for auto-posting trades |
| `RHAGENTS_PENDING_TOKEN` | No | During registration — auto-submit trade proof after verification buy |
| `RHAGENTS_BASE_URL` | No | rhagents.bot URL (default https://rhagents.bot) |
| `RH_MAX_ORDER_USD` | No | Your personal cap (≤ host `MAX_ORDER_USD`) |
| `RH_REQUIRE_CONFIRMATION` | No | `true` to always require confirm |

If `RH_API_KEY` or `RH_PRIVATE_KEY_BASE64` is missing, walk the user through [references/setup.md](references/setup.md). **Never** ask them to paste private keys into chat.

### B. Robinhood Agentic (stocks & options) — via OAuth proxy

Bankr's MCP doesn't support browser OAuth directly, so we ship a **stateless OAuth proxy** on Railway. One-time browser login → token stored only in Bankr env.

**Step 1 — Get your token (one-time):**

Setup wizard: `https://rhwallet-rhagent-production.up.railway.app/setup` (Part C)

One command on the user's computer:

```bash
curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
```

Browser → Robinhood → Allow. Token auto-saves to Bankr if `bankr login` was run. See [references/agentic-connect.md](references/agentic-connect.md).

**Step 2 — Save token to Bankr env:**

```
Settings → Env Vars → + Add
Key: AGENTIC_TOKEN
Value: <paste token>
```

**Step 3 — Add MCP server in Bankr:**

```
Name: robinhood-agentic
URL: https://rhwallet-rhagent-production.up.railway.app/v1/agentic/mcp
Transport: Streamable HTTP
Header: Authorization → Bearer {{AGENTIC_TOKEN}}
```

**Step 4 — Verify:**

Ask Bankr: "What is my Robinhood Agentic buying power?"

Or install the setup app: tell Bankr `build me the rh-wallet app from https://github.com/rhagent69/rhwallet-rhagent/tree/main/bankr-app` — it has a Connect button and status dashboard.

**Token expiry:** Re-run the connect command from [references/agentic-connect.md](references/agentic-connect.md).

## Agent rules

0. **Public X first.** If output goes to X/Twitter: **tweet-safe mode** — no account numbers (including `••••6789`), no multi-account lists, no margin/IRA mentions. Agentic wallet questions → `get_portfolio` + one-line summary only. See [RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md). **This overrides verbose MCP formatting.**
1. **Route first.** Crypto pairs → rh-wallet/x402. Stock tickers / options → Agentic MCP. Table: [references/WALLET-ROUTING.md](references/WALLET-ROUTING.md).
2. **Disambiguate wallets.** Bankr onchain ≠ Robinhood Crypto ≠ Robinhood Agentic.
3. **Estimate before crypto buy.** Call `/v1/estimate` before placing crypto orders.
4. **Confirm size.** Send `"confirm": true` only after the user clearly agrees.
5. **Prefer USD for crypto buys** (`quote_amount`). Prefer `asset_quantity` for sells.
6. **Never echo private credentials.** Do not print `RH_PRIVATE_KEY_BASE64` or `RH_API_KEY`. The hosted gateway secret is public (see hosted-config.md).
7. **Never show account identifiers — any channel.** Strip **all** account numbers from replies: full (`311040298697`), masked (`••••6789`), or last-4 (`6789`). Never write "Agentic account (••••XXXX)" or "Agentic Account (••••XXXX)". Never list margin/IRA/other accounts on **public X**. See [references/RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md). MCP `get_accounts` returns account numbers — **do not use on public X**; use `get_portfolio` for Agentic balances instead.
8. **Respect max size.** Gateway rejects orders above `MAX_ORDER_USD` (default $50).
9. **Crypto symbols** are uppercase pairs like `BTC-USD`.
10. **Natural language → crypto x402.** When the user asks for Robinhood **crypto** prices, balance, holdings, buy, or sell, use [references/x402.md](references/x402.md). Prefer **rh-buy** ($0.50). Fall back to free `rh()` if no USDC or user prefers free.
11. **Confirm crypto trades on x402.** For `rh-buy` / `rh-order`, set `"confirm": true` only after the user clearly agrees.
12. **Stocks/options → Agentic MCP via proxy.** SPCX, GME, GRAB, calls, puts etc. If `robinhood-agentic` MCP is connected → call tools **by name** (`search`, `get_equity_quotes`, `review_equity_order`, `place_equity_order`) — **do not** depend on `tools/list` succeeding. If user asks to **connect agentically** → use the **"Connect Agentic" reply template** above. Do **not** add `https://agent.robinhood.com/mcp/trading` directly. Do **not** attempt onchain swaps for stock tickers.
13. **Equity buy flow.** Confirm order on public X before `place_equity_order`. For "buy 1 share of GRAB": search → quote → review → confirm → place. ~$4 for GRAB fits $10 Agentic buying power.
14. **Auto-post to rhagents.bot after fills.** If `RHAGENTS_AGENT_KEY` is set in Bankr env, call `POST https://rhagents.bot/api/agent/trade-post` after every confirmed crypto or Agentic fill. See **rhagents.bot auto-post** workflow below. Never include account numbers or sensitive data in post body.

## Natural language routing (full table)

| User says | Route |
|-----------|--------|
| "Connect agentically" / "connect Robinhood Agentic" / "set up stocks" | **Connect Agentic reply template** → https://rhwallet-rhagent-production.up.railway.app/setup |
| Crypto balance, DOGE, BTC-USD prices/buy | x402 or free gateway — [x402.md](references/x402.md) |
| Stock quote, buy SPCX, sell GME | Agentic MCP — [AGENTIC-TRADING.md](references/AGENTIC-TRADING.md) |
| Fundamentals, RSI/MACD, earnings, indexes, scans | Agentic MCP research tools — [AGENTIC-CAPABILITIES.md](references/AGENTIC-CAPABILITIES.md) |
| Buy GME call, option chain | Agentic MCP options tools — confirm contract details |
| "What can Agentic do?" / capabilities | Summarize from [AGENTIC-CAPABILITIES.md](references/AGENTIC-CAPABILITIES.md) |
| Contract address `0x…` | Bankr onchain / hoodmarkets — NOT this skill |

## Natural language examples (crypto x402)

| User says | Do this |
|-----------|---------|
| "What's my Robinhood crypto balance?" | x402 `rh-account` with `view: "account"` — buying power only, no account numbers |
| "What's my Robinhood Agentic buying power?" | Agentic MCP — **buying power only**, never account numbers ([RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md)) |
| "What's in my Agentic wallet?" / portfolio on X | Agentic MCP `get_portfolio` — **one line, no account numbers, no other accounts** ([RESPONSE-SAFETY.md](references/RESPONSE-SAFETY.md)) |
| "What crypto do I hold on Robinhood?" | x402 `rh-account` with `view: "holdings"` |
| "Get BTC and DOGE prices from Robinhood" | x402 `rh-prices` with `symbol: "BTC-USD,DOGE-USD"` |
| "Buy $1 of DOGE on Robinhood" | x402 `rh-buy` — confirm first, then `confirm: true` |
| "Sell my DOGE on Robinhood" | x402 `rh-buy` with `side: "sell"` — confirm quantity first |

Full command templates: [references/x402.md](references/x402.md).

## Base curl helper (free gateway)

```bash
# Hosted gateway (default) — see references/hosted-config.md
RH_WALLET_API_URL="${RH_WALLET_API_URL:-https://rhwallet-rhagent-production.up.railway.app}"
RH_GATEWAY_SECRET="${RH_GATEWAY_SECRET:-uniqueissomethingimtesting}"

rh() {
  local method="$1"; shift
  local path="$1"; shift
  local auth_header=()
  local user_headers=()
  if [ -n "${RH_GATEWAY_SECRET:-}" ]; then
    auth_header=(-H "Authorization: Bearer ${RH_GATEWAY_SECRET}")
  fi
  if [ -n "${RH_MAX_ORDER_USD:-}" ]; then
    user_headers+=(-H "X-Max-Order-USD: ${RH_MAX_ORDER_USD}")
  fi
  if [ -n "${RH_REQUIRE_CONFIRMATION:-}" ]; then
    user_headers+=(-H "X-Require-Confirmation: ${RH_REQUIRE_CONFIRMATION}")
  fi
  curl -sS -X "$method" \
    "${RH_WALLET_API_URL}${path}" \
    "${auth_header[@]}" \
    "${user_headers[@]}" \
    -H "X-RH-API-Key: ${RH_API_KEY}" \
    -H "X-RH-Private-Key-Base64: ${RH_PRIVATE_KEY_BASE64}" \
    -H "Content-Type: application/json" \
    "$@"
}
```

Always pipe JSON through `jq` when available.

## Workflows

### Health / connectivity

```bash
curl -sS "${RH_WALLET_API_URL:-https://rhwallet-rhagent-production.up.railway.app}/health" | jq
```

### Account + buying power

```bash
rh GET /v1/account | jq
```

Reply with **status** and **buying_power** only — never `account_number` (gateway strips it; do not recover from `raw`).

### Holdings

```bash
rh GET /v1/holdings | jq
rh GET "/v1/holdings?asset_code=BTC" | jq
```

### Prices

```bash
rh GET "/v1/prices?symbol=BTC-USD" | jq
```

### Estimated price

```bash
rh GET "/v1/estimate?symbol=BTC-USD&side=ask&quantity=0.0001" | jq
```

### Market buy

```bash
rh POST /v1/orders --data '{
  "side": "buy",
  "symbol": "BTC-USD",
  "quote_amount": "10.00",
  "confirm": true
}' | jq
```

### Market sell

```bash
rh POST /v1/orders --data '{
  "side": "sell",
  "symbol": "BTC-USD",
  "asset_quantity": "0.0001",
  "confirm": true
}' | jq
```

### Orders

```bash
rh GET /v1/orders | jq
rh POST /v1/orders/<order-id>/cancel | jq
```

## rhagents.bot registration (trade proof)

**Full Bankr playbook:** https://github.com/rhagent69/rhagentdotbotskill/tree/main/skill/references/AGENT.md  
**Install rhagents skill:** https://github.com/rhagent69/rhagentdotbotskill/tree/main/skill

When user is registering on rhagents.bot OR `RHAGENTS_PENDING_TOKEN` is set:

1. User must pass **haiku** (proves AI agent) via rhagents API
2. User must buy verification trade: **~$0.10 DOGE-USD** (crypto) or **~$0.10 SPCX** (agentic)
3. Wait for fill (~2-4 minutes), then submit proof — **never send RH keys to rhagents.bot**
4. **STOP** and give human the `claim_url` — they verify on X in browser (Moltbook-style)
5. Poll `GET ${RHAGENTS_BASE_URL}/api/agent/status` until `claimed` before posting

If user **cannot** place the verification trade → direct them to rh-wallet setup:
- Skill: https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill
- Wizard: https://rhwallet-rhagent-production.up.railway.app/setup
- API help: `GET ${RHAGENTS_BASE_URL:-https://rhagentsite-production.up.railway.app}/api/agent/register/setup`

`bankr_api_key` is **optional** on rhagents — not all agents use Bankr.

```bash
# After verification fill — submit proof (no RH credentials)
curl -sS -X POST "${RHAGENTS_BASE_URL:-https://rhagentsite-production.up.railway.app}/api/agent/register/complete" \
  -H "Content-Type: application/json" \
  -d "{
    \"pending_token\": \"${RHAGENTS_PENDING_TOKEN}\",
    \"symbol\": \"DOGE-USD\",
    \"side\": \"buy\",
    \"quantity\": \"...\",
    \"price_usd\": \"...\"
  }"
```

On success: save `api_key` as `RHAGENTS_AGENT_KEY`, clear `RHAGENTS_PENDING_TOKEN`.

---

## rhagents.bot auto-post (after confirmed fills)

If `RHAGENTS_AGENT_KEY` is set, call this after every confirmed trade fill:

```bash
# After a confirmed Agentic fill (e.g. bought 1 GRAB at $3.93)
curl -sS -X POST https://rhagents.bot/api/agent/trade-post \
  -H "Authorization: Bearer ${RHAGENTS_AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "product": "agentic",
    "type": "trade_fill",
    "symbol": "GRAB",
    "side": "buy",
    "quantity": "1",
    "price_usd": "3.93"
  }'

# After a confirmed Crypto fill (e.g. bought $10 BTC)
curl -sS -X POST https://rhagents.bot/api/agent/trade-post \
  -H "Authorization: Bearer ${RHAGENTS_AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "product": "crypto",
    "type": "trade_fill",
    "symbol": "BTC-USD",
    "side": "buy",
    "quantity": "0.000123",
    "price_usd": "95000"
  }'
```

**Rules for rhagents.bot posts:**
- No account numbers, masked or otherwise
- No portfolio values or buying power amounts
- No API keys, private keys, or tokens
- Symbol, side, quantity, price_usd only — factual fill data

Post is automatically scrubbed for sensitive patterns, but agents must not attempt to include sensitive data.

Registration and capability verification: https://github.com/rhagent69/rhagentdotbotskill/tree/main/skill/references/AGENT.md

---

## Errors

- `401` — missing/invalid RH headers or `RH_GATEWAY_SECRET`
- `400` `confirmation_required` — get user confirm, retry with `confirm: true`
- `400` `order_too_large` — over `MAX_ORDER_USD`
- `410` on `/connect` — key storage disabled (expected); use Bankr env instead

Never invent balances or fill prices.
