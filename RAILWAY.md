# Deploy to Railway (universal hosting)

One Railway project can serve **many users**, each with their own Robinhood account.

## How it works

| Who | What they set |
|-----|----------------|
| **You (Railway host)** | `MASTER_ENCRYPTION_KEY`, `DATABASE_URL`, `PUBLIC_BASE_URL` |
| **Each user** | Connect at `/connect` → get personal `RH_WALLET_API_KEY` |
| **Each user (Bankr)** | `RH_WALLET_API_URL` (same for everyone) + their own `RH_WALLET_API_KEY` |

Robinhood keys (`RH_API_KEY`, private key) are **not** in Railway env for universal mode. Users submit them once at `/connect`; they are encrypted in Postgres.

## Railway variables (host only)

| Variable | Required | How to generate |
|----------|----------|-----------------|
| `MASTER_ENCRYPTION_KEY` | Yes | `openssl rand -hex 32` |
| `DATABASE_URL` | Yes (prod) | Railway → **Add Postgres** → copy `DATABASE_URL` |
| `PUBLIC_BASE_URL` | Yes | `https://your-app.up.railway.app` (after Generate Domain) |
| `MAX_ORDER_USD` | No | `50` (default per new connection) |
| `REQUIRE_CONFIRMATION` | No | `true` |

**Leave empty for universal mode:**

- `RH_API_KEY`
- `RH_PRIVATE_KEY_BASE64`
- `RH_WALLET_API_KEY`

(Legacy single-tenant mode still works if you set all three RH vars + `RH_WALLET_API_KEY` instead of multi-tenant.)

## Deploy steps

1. **New Project** → Deploy from GitHub → `anondevv69/RH-Wallet`
2. **Add Postgres** plugin to the project
3. Set variables above on the **gateway service**
4. **Generate Domain** → set `PUBLIC_BASE_URL` to that URL
5. Redeploy if needed

### Verify

```bash
curl -sS https://YOUR-URL.up.railway.app/health | jq
```

Expect `"multi_tenant": true`.

## User onboarding (no coding)

1. User opens `https://YOUR-URL.up.railway.app/connect`
2. Pastes Robinhood API key + private key (from Robinhood crypto settings + keygen script)
3. Copies the issued `RH_WALLET_API_URL` + `RH_WALLET_API_KEY`
4. In Bankr → **Agent tool environment** → paste both
5. Installs skill:
   ```text
   install the skill at https://github.com/anondevv69/RH-Wallet/tree/main/skill
   ```

Or tell Bankr: **“Set up my Robinhood wallet”** → skill should send them to `/connect`.

## Bankr env vars (every user)

| Key | Value |
|-----|--------|
| `RH_WALLET_API_URL` | `https://YOUR-URL.up.railway.app` (same for all users) |
| `RH_WALLET_API_KEY` | Personal key from `/connect` (starts with `rhw_`) |

## Security notes

- You custody encrypted RH keys — treat this as a vault product
- Use Railway Postgres (not SQLite) in production — SQLite resets on ephemeral disks
- Never commit `MASTER_ENCRYPTION_KEY` or user keys to git
- Users can revoke at `DELETE /v1/connect` with their Bearer token

## Legacy single-tenant (just you)

If you only want your own account without `/connect`:

Set on Railway: `RH_API_KEY`, `RH_PRIVATE_KEY_BASE64`, `RH_WALLET_API_KEY`  
Skip `MASTER_ENCRYPTION_KEY` and Postgres.
