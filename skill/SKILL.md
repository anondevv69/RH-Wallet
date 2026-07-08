---
name: rh-wallet
description: >
  Manage a Robinhood Crypto wallet through the RH Wallet Gateway — check
  balances/holdings, query bid/ask and estimated prices, place market buy/sell
  orders, list and cancel orders. Use when the user mentions Robinhood, RH
  wallet, RH crypto, buy/sell on Robinhood, Robinhood holdings, BTC-USD on
  Robinhood, or similar. This is separate from Bankr's onchain wallet: always
  say "Robinhood Crypto (US)" when acting. Requires RH_WALLET_API_URL,
  RH_API_KEY, and RH_PRIVATE_KEY_BASE64 in Bankr Agent tool environment.
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

Trade and inspect a **Robinhood Crypto** account through a **stateless RH Wallet Gateway**. Robinhood keys live in **Bankr Agent tool environment** — the gateway signs requests but does **not** store your keys.

> **US only.** Robinhood Crypto Trading API is available to US customers and is subject to the Robinhood Crypto Customer Agreement.

For setup see [references/setup.md](references/setup.md).  
For safety see [references/trading-safety.md](references/trading-safety.md).  
For endpoints see [references/api-reference.md](references/api-reference.md).

## Prerequisites — Bankr Agent tool environment

Set these in **Bankr → gear → Agent tool environment** (not x402):

| Variable | What |
|----------|------|
| `RH_WALLET_API_URL` | Public gateway URL, no trailing slash (e.g. `https://rh-wallet.up.railway.app`) |
| `RH_API_KEY` | Robinhood API key (`rh-api-...`) from crypto settings |
| `RH_PRIVATE_KEY_BASE64` | Ed25519 private key from `scripts/generate_rh_keypair.py` |
| `RH_GATEWAY_SECRET` | Optional — only if the host set `GATEWAY_SHARED_SECRET` on Railway |

If any required var is missing, walk the user through [references/setup.md](references/setup.md). **Never** ask them to paste private keys into chat — only into Bankr env settings.

## Agent rules

1. **Disambiguate wallets.** Bankr has its own onchain wallet. Only use this skill for Robinhood Crypto. Say “Robinhood Crypto (US)” in replies.
2. **Estimate before buy.** Call `/v1/estimate` before placing orders.
3. **Confirm size.** Send `"confirm": true` only after the user clearly agrees.
4. **Prefer USD for buys** (`quote_amount`). Prefer `asset_quantity` for sells.
5. **Never echo secrets.** Do not print `RH_PRIVATE_KEY_BASE64`, `RH_API_KEY`, or `RH_GATEWAY_SECRET`.
6. **Respect max size.** Gateway rejects orders above `MAX_ORDER_USD` (default $50).
7. **Symbols** are uppercase pairs like `BTC-USD`.

## Base curl helper

```bash
rh() {
  local method="$1"; shift
  local path="$1"; shift
  local auth_header=()
  if [ -n "${RH_GATEWAY_SECRET:-}" ]; then
    auth_header=(-H "Authorization: Bearer ${RH_GATEWAY_SECRET}")
  fi
  curl -sS -X "$method" \
    "${RH_WALLET_API_URL}${path}" \
    "${auth_header[@]}" \
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
curl -sS "${RH_WALLET_API_URL}/health" | jq
```

### Account + buying power

```bash
rh GET /v1/account | jq
```

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

## Errors

- `401` — missing/invalid RH headers or `RH_GATEWAY_SECRET`
- `400` `confirmation_required` — get user confirm, retry with `confirm: true`
- `400` `order_too_large` — over `MAX_ORDER_USD`
- `410` on `/connect` — key storage disabled (expected); use Bankr env instead

Never invent balances or fill prices.
