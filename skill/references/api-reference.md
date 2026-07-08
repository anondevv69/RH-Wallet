# RH Wallet Gateway API reference

Base URL: `$RH_WALLET_API_URL`

## Authentication (stateless — default)

Every `/v1/*` request sends Robinhood credentials via headers (from Bankr env):

| Header | Bankr env var |
|--------|----------------|
| `X-RH-API-Key` | `RH_API_KEY` |
| `X-RH-Private-Key-Base64` | `RH_PRIVATE_KEY_BASE64` |

If the host set `GATEWAY_SHARED_SECRET`, also send:

| Header | Bankr env var |
|--------|----------------|
| `Authorization: Bearer ...` | `RH_GATEWAY_SECRET` |

The gateway signs and proxies to Robinhood. **Keys are not stored.**

## Endpoints

Same as before: `/v1/account`, `/v1/holdings`, `/v1/prices`, `/v1/estimate`, `/v1/orders`, etc.

See gateway README for full table.

## `/connect` (disabled by default)

Returns `410 Gone` unless host sets `ENABLE_CONNECT_STORAGE=true`. Do not use for normal setup.
