---
name: rh-wallet
description: >
  Manage a Robinhood Crypto wallet through the RH Wallet Gateway — check
  balances/holdings, query bid/ask and estimated prices, place market buy/sell
  orders, list and cancel orders. Use when the user mentions Robinhood, RH
  wallet, RH crypto, buy/sell on Robinhood, Robinhood holdings, BTC-USD on
  Robinhood, or similar. This is separate from Bankr's onchain wallet: always
  say "Robinhood Crypto (US)" when acting. Requires RH_WALLET_API_URL and
  RH_WALLET_API_KEY env vars pointing at a deployed gateway.
tags: [robinhood, crypto, trading, wallet, bankr, usd]
visibility: public
metadata:
  clawdbot:
    emoji: "🟩"
    homepage: "https://github.com/anondevv69/RH-Wallet"
    requires:
      bins: [curl, jq]
---

# Robinhood Crypto Wallet (via RH Wallet Gateway)

Trade and inspect a **Robinhood Crypto** account through your deployed **RH Wallet Gateway**. Bankr never sees the Robinhood Ed25519 private key — only a gateway Bearer token.

> **US only.** Robinhood Crypto Trading API is available to US customers and is subject to the Robinhood Crypto Customer Agreement.

For setup details see [references/setup.md](references/setup.md).  
For safety rules see [references/trading-safety.md](references/trading-safety.md).  
For the full endpoint map see [references/api-reference.md](references/api-reference.md).

## Prerequisites

1. User has deployed the RH Wallet Gateway (this repo’s `gateway/`) with:
   - `RH_API_KEY` / `RH_PRIVATE_KEY_BASE64` (Robinhood credentials)
   - `RH_WALLET_API_KEY` (Bearer token for this skill)
2. In **Bankr settings → Env Vars**, set:
   - `RH_WALLET_API_URL` — base URL, no trailing slash (e.g. `https://rh-wallet.example.com`)
   - `RH_WALLET_API_KEY` — same as the gateway’s `RH_WALLET_API_KEY`

If either env var is missing, stop and walk the user through [references/setup.md](references/setup.md). Do **not** ask the user to paste Robinhood private keys into chat.

## Agent rules

1. **Disambiguate wallets.** Bankr has its own onchain wallet. Only use this skill for Robinhood Crypto. Say “Robinhood Crypto (US)” in replies.
2. **Estimate before buy.** Call `/v1/estimate` (ask side for buys, bid for sells) before placing an order. Summarize expected cost to the user.
3. **Confirm size.** When the gateway has `REQUIRE_CONFIRMATION=true` (default), you must send `"confirm": true` only after the user clearly agrees to the size.
4. **Prefer USD for buys** (`quote_amount`). Prefer `asset_quantity` for sells.
5. **Never echo secrets.** Never print `RH_PRIVATE_KEY_BASE64`, Robinhood API keys, or gateway tokens.
6. **Respect max size.** Gateway rejects orders above `MAX_ORDER_USD` (default $50). If rejected, explain the limit — do not try to bypass it.
7. **Symbols** are uppercase pairs like `BTC-USD`, `ETH-USD`. Only USD pairs that Robinhood marks API-tradable.

## Base curl helper

```bash
rh() {
  local method="$1"; shift
  local path="$1"; shift
  curl -sS -X "$method" \
    "${RH_WALLET_API_URL}${path}" \
    -H "Authorization: Bearer ${RH_WALLET_API_KEY}" \
    -H "Content-Type: application/json" \
    "$@"
}
```

Always pipe JSON through `jq` when available.

## Workflows

### Health / connectivity

```bash
curl -sS "${RH_WALLET_API_URL}/health" | jq
```

If this fails, the gateway is down or `RH_WALLET_API_URL` is wrong. Do not place orders.

### Account + buying power

```bash
rh GET /v1/account | jq
```

Report account status, buying power, and currency.

### Holdings

```bash
rh GET /v1/holdings | jq
# filter one asset:
rh GET "/v1/holdings?asset_code=BTC" | jq
```

### Prices (best bid/ask)

```bash
rh GET "/v1/prices?symbol=BTC-USD" | jq
rh GET "/v1/prices?symbol=BTC-USD&symbol=ETH-USD" | jq
```

### Estimated price before trading

Buy estimate (ask):

```bash
rh GET "/v1/estimate?symbol=BTC-USD&side=ask&quantity=0.0001" | jq
```

Sell estimate (bid):

```bash
rh GET "/v1/estimate?symbol=BTC-USD&side=bid&quantity=0.0001" | jq
```

Multiple sizes: `quantity=0.001,0.01,0.1` (max 10).

### Market buy (USD amount)

1. Estimate if useful.
2. Confirm with the user.
3. Place:

```bash
rh POST /v1/orders --data '{
  "side": "buy",
  "symbol": "BTC-USD",
  "type": "market",
  "quote_amount": "10.00",
  "confirm": true
}' | jq
```

### Market sell (asset quantity)

```bash
rh POST /v1/orders --data '{
  "side": "sell",
  "symbol": "BTC-USD",
  "type": "market",
  "asset_quantity": "0.0001",
  "confirm": true
}' | jq
```

Provide **exactly one** of `quote_amount` or `asset_quantity`.

### List / get / cancel orders

```bash
rh GET /v1/orders | jq
rh GET /v1/orders/<order-id> | jq
rh POST /v1/orders/<order-id>/cancel | jq
```

### Trading pairs

```bash
rh GET /v1/trading-pairs | jq
rh GET "/v1/trading-pairs?symbol=BTC-USD" | jq
```

## Example natural language → action

| User says | You do |
|-----------|--------|
| “What’s my Robinhood buying power?” | `GET /v1/account` |
| “RH holdings” | `GET /v1/holdings` |
| “Price of BTC on Robinhood” | `GET /v1/prices?symbol=BTC-USD` |
| “Buy $10 of BTC on Robinhood” | Estimate → confirm → `POST /v1/orders` with `quote_amount` + `confirm: true` |
| “Sell 0.001 ETH on RH” | Estimate bid → confirm → `POST /v1/orders` with `asset_quantity` |
| “Cancel my open RH order …” | `POST /v1/orders/{id}/cancel` |

## Errors

- `401` — bad/missing `RH_WALLET_API_KEY`
- `400` `confirmation_required` — ask user to confirm, then retry with `confirm: true`
- `400` `order_too_large` — over `MAX_ORDER_USD`; reduce size or ask user to raise the gateway limit
- `503` — gateway missing RH credentials
- Robinhood `429` — rate limited; wait and retry

Never invent balances or fill prices. Surface gateway / Robinhood error JSON honestly.
