# Deploy to Railway (stateless — recommended)

One public gateway. **Each user keeps their own Robinhood keys in Bankr.**

## Who holds what

| What | Where |
|------|--------|
| `RH_API_KEY` + private key | **User → Bankr Agent tool environment** |
| `RH_WALLET_API_URL` | Same public URL for everyone |
| `RH_GATEWAY_SECRET` | User copies from host (optional anti-abuse) |
| Signing code | Your Railway deploy |
| User RH keys in your DB | **No** (disabled by default) |

## Railway variables (host only)

| Variable | Required | Notes |
|----------|----------|--------|
| `PUBLIC_BASE_URL` | Yes | `https://your-app.up.railway.app` |
| `GATEWAY_SHARED_SECRET` | Recommended | `openssl rand -hex 32` — users set as `RH_GATEWAY_SECRET` in Bankr |
| `MAX_ORDER_USD` | No | Default `50` |
| `REQUIRE_CONFIRMATION` | No | Default `true` |

**Do not set** (unless you explicitly want legacy modes):

- `RH_API_KEY` / `RH_PRIVATE_KEY_BASE64` — users put these in Bankr
- `MASTER_ENCRYPTION_KEY` / `ENABLE_CONNECT_STORAGE` — would store keys (off by default)

## Deploy

1. Railway → New Project → GitHub → `anondevv69/RH-Wallet`
2. Set variables above
3. Generate domain → set `PUBLIC_BASE_URL`
4. Verify: `curl https://YOUR-URL/health` → `"mode": "stateless"`

## User setup (no coding)

1. Create RH API credentials (keygen script + Robinhood settings)
2. Bankr → **Agent tool environment**:
   - `RH_WALLET_API_URL` = your Railway URL
   - `RH_API_KEY` = theirs
   - `RH_PRIVATE_KEY_BASE64` = theirs
   - `RH_GATEWAY_SECRET` = yours (if set)
3. Install skill from GitHub
4. Ask: “What’s my Robinhood buying power?”

## Experimental: `/connect` key storage

Only enable if you accept custody liability:

```
ENABLE_CONNECT_STORAGE=true
MASTER_ENCRYPTION_KEY=...
DATABASE_URL=...  # Railway Postgres
```

Not recommended for public launch.
