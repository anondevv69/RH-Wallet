# Setup — RH Wallet + Bankr (stateless)

**Robinhood keys stay in Bankr — not on the gateway host.**

## 1. Create Robinhood API credentials

```bash
pip install pynacl
python scripts/generate_rh_keypair.py
```

1. Register the **public** key in Robinhood crypto settings (web classic)
2. Copy the **API key** (`rh-api-...`)
3. Keep the **private key** for Bankr env only

## 2. Host gateway (you or community)

Deploy to Railway — see [RAILWAY.md](../../RAILWAY.md). Host sets only:

- `PUBLIC_BASE_URL`
- `GATEWAY_SHARED_SECRET` (recommended)
- `MAX_ORDER_USD`, `REQUIRE_CONFIRMATION`

Host does **not** need users' `RH_API_KEY` or private keys.

## 3. Bankr Agent tool environment

**Gear → Agent tool environment** (not x402):

| Variable | Value |
|----------|--------|
| `RH_WALLET_API_URL` | `https://your-gateway.up.railway.app` |
| `RH_API_KEY` | Your `rh-api-...` |
| `RH_PRIVATE_KEY_BASE64` | Your private key |
| `RH_GATEWAY_SECRET` | Same as host's `GATEWAY_SHARED_SECRET` (if set) |
| `RH_MAX_ORDER_USD` | Optional — your personal cap (cannot exceed host `MAX_ORDER_USD`) |
| `RH_REQUIRE_CONFIRMATION` | Optional — `true` to always require confirm on your orders |

## 4. Install skill

```text
install the skill at https://github.com/anondevv69/RH-Wallet/tree/main/skill
```

## 5. Test

- “What’s my Robinhood buying power?”
- “Robinhood price of BTC-USD”

## Local dev (optional)

Run gateway locally; use `http://127.0.0.1:8080` as `RH_WALLET_API_URL` only if Bankr runs on the same machine.

## Security

- Keys in Bankr env = user ↔ Bankr trust (same as Shopify skill tokens)
- Gateway does not store RH keys by default
- Do not use `/connect` — disabled unless host explicitly enables storage
