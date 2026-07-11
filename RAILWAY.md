# Deploy to Railway (stateless — recommended)

One public gateway. **Each user keeps their own Robinhood keys in Bankr.**

## Who holds what

| What | Where |
|------|--------|
| `RH_API_KEY` + private key | **User → Bankr Agent tool environment** |
| `RH_WALLET_API_URL` | Public gateway URL (default in skill) |
| `RH_GATEWAY_SECRET` | Public invite code (default in skill — see `skill/references/hosted-config.md`) |
| Signing code | Your Railway deploy |
| User RH keys in your DB | **No** (disabled by default) |

## Railway variables (host only — same for all users)

| Variable | Who sets | Purpose |
|----------|----------|---------|
| `PUBLIC_BASE_URL` | **You** | One URL everyone uses as `RH_WALLET_API_URL` |
| `GATEWAY_SHARED_SECRET` | **You** | Must match public value in `skill/references/hosted-config.md` |
| `MAX_ORDER_USD` | **You** | **Ceiling** — no user can trade above this |
| `REQUIRE_CONFIRMATION` | **You** | Default confirm rule for the gateway |

## Per-user limits (Bankr env — each user sets their own)

| Variable | Example | Purpose |
|----------|---------|---------|
| `RH_MAX_ORDER_USD` | `25` | User's stricter cap (must be ≤ host `MAX_ORDER_USD`) |
| `RH_REQUIRE_CONFIRMATION` | `true` | User always wants confirm step |

Users cannot exceed your Railway `MAX_ORDER_USD` ceiling.

**Do not set** (unless you explicitly want legacy modes):

- `RH_API_KEY` / `RH_PRIVATE_KEY_BASE64` — users put these in Bankr
- `MASTER_ENCRYPTION_KEY` / `ENABLE_CONNECT_STORAGE` — would store keys (off by default)

## Deploy

Public skill/docs URLs point at **`rhagent69/rhwallet-rhagent`** (agent mirror). Railway can deploy from your private fork or that mirror — same code.

1. Railway → New Project → GitHub → `anondevv69/RH-Wallet` (or `rhagent69/rhwallet-rhagent`)
2. Set variables — **`GATEWAY_SHARED_SECRET` must equal** the value in [skill/references/hosted-config.md](skill/references/hosted-config.md)
3. Generate domain → set `PUBLIC_BASE_URL=https://rhwallet-rhagent-production.up.railway.app`
4. Verify: `curl https://rhwallet-rhagent-production.up.railway.app/health` → `"mode": "stateless"`

## User setup (no coding)

1. Create RH API credentials (keygen script + Robinhood settings)
2. Bankr → **Agent tool environment** (only Robinhood keys required):
   - `RH_API_KEY` = theirs
   - `RH_PRIVATE_KEY_BASE64` = theirs
   - URL + gateway secret are built into the skill ([hosted-config.md](skill/references/hosted-config.md))
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
