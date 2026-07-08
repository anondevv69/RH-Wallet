# RH Wallet Gateway API reference

Base URL: `$RH_WALLET_API_URL`  
Auth (all `/v1/*`): `Authorization: Bearer $RH_WALLET_API_KEY`

Upstream: Robinhood Crypto Trading API **v2** at `https://trading.robinhood.com`.

## Endpoints

### `GET /health`

No auth. Liveness + config flags (`rh_credentials_configured`, `gateway_auth_configured`, `max_order_usd`, `require_confirmation`).

### `GET /v1/account`

Primary crypto account summary: `account_number`, `status`, `buying_power`, etc.

### `GET /v1/holdings`

Query: optional repeated `asset_code` (e.g. `BTC`, `ETH`).

### `GET /v1/trading-pairs`

Query: optional repeated `symbol` (e.g. `BTC-USD`). Returns flattened `{ results, count }`.

### `GET /v1/prices`

Query: optional repeated `symbol`. Best bid/ask from Robinhood partner exchanges.

### `GET /v1/estimate`

Query (required):

| Param | Values |
|-------|--------|
| `symbol` | e.g. `BTC-USD` |
| `side` | `bid` \| `ask` \| `both` |
| `quantity` | e.g. `0.1` or `0.1,1,1.999` (max 10) |

### `GET /v1/orders`

Query: optional `symbol`, `side`, `state`, `type`, `created_at_start`.

### `GET /v1/orders/{id}`

Normalized order summary + `raw`.

### `POST /v1/orders`

Body:

```json
{
  "side": "buy",
  "symbol": "BTC-USD",
  "type": "market",
  "quote_amount": "10.00",
  "confirm": true
}
```

or

```json
{
  "side": "sell",
  "symbol": "BTC-USD",
  "type": "market",
  "asset_quantity": "0.0001",
  "confirm": true
}
```

Rules:

- Exactly one of `quote_amount` / `asset_quantity`
- `type` must be `market` (MVP)
- `confirm` required when gateway `REQUIRE_CONFIRMATION=true`
- Notional must be ≤ `MAX_ORDER_USD`

### `POST /v1/orders/{id}/cancel`

Cancels an open order.

## Signing note (gateway internals)

Bankr does **not** sign Robinhood requests. The gateway builds:

```text
message = api_key + timestamp + path + method + body
```

and sets `x-api-key`, `x-signature`, `x-timestamp` per Robinhood docs.
