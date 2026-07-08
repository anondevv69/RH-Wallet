# Deploy to Railway

One-click style deploy for the **RH Wallet Gateway** so Bankr (cloud / X) can reach it over HTTPS.

## Who sets what

| Where | Who | Variables |
|-------|-----|-----------|
| **Railway** (host) | You (operator) | `RH_API_KEY`, `RH_PRIVATE_KEY_BASE64`, `RH_WALLET_API_KEY`, optional limits |
| **Bankr → Agent tool env** | Each Bankr user | `RH_WALLET_API_URL`, `RH_WALLET_API_KEY` |

### Important: Railway env is **not** empty

The gateway needs Robinhood credentials and a gateway Bearer token in **Railway’s** environment. Empty Railway env = `/health` works but all trading routes return 503.

### Important: single-tenant (current MVP)

This deploy uses **one** Robinhood API credential set on Railway. Every Bankr user who shares the same `RH_WALLET_API_KEY` trades against **that same RH account**.

| Goal | What to do |
|------|------------|
| **You** use Bankr with **your** RH account | Deploy once, set your RH keys on Railway, use that URL + key in Bankr |
| **Others** use **their own** RH accounts on your host | Not supported yet — needs Phase 2 (multi-tenant connect + per-user API keys) |
| **Others** self-host | They fork repo, deploy their own Railway, set **their** env vars |

Do **not** publish your `RH_WALLET_API_KEY` publicly if it controls real funds.

---

## Steps

### 1. Push this repo to GitHub

Already at: `https://github.com/anondevv69/RH-Wallet`

### 2. Create Railway project

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Select `anondevv69/RH-Wallet`
3. Railway detects the root `Dockerfile` / `railway.toml`

### 3. Set Railway variables

In the service → **Variables**:

| Variable | Required | Example |
|----------|----------|---------|
| `RH_API_KEY` | Yes | `rh-api-...` from Robinhood |
| `RH_PRIVATE_KEY_BASE64` | Yes | from `scripts/generate_rh_keypair.py` |
| `RH_WALLET_API_KEY` | Yes | `openssl rand -hex 32` |
| `MAX_ORDER_USD` | No | `50` |
| `REQUIRE_CONFIRMATION` | No | `true` |
| `PORT` | No | Railway sets this automatically |

Do **not** commit `.env` to git.

### 4. Generate public URL

1. Service → **Settings** → **Networking** → **Generate Domain**
2. Copy URL, e.g. `https://rh-wallet-production.up.railway.app`

### 5. Verify

```bash
curl -sS https://YOUR-RAILWAY-URL.up.railway.app/health | jq
```

Expect `rh_credentials_configured: true` and `gateway_auth_configured: true`.

```bash
curl -sS https://YOUR-RAILWAY-URL.up.railway.app/v1/account \
  -H "Authorization: Bearer YOUR_RH_WALLET_API_KEY" | jq
```

### 6. Bankr

**Agent tool environment** (not x402):

| Key | Value |
|-----|--------|
| `RH_WALLET_API_URL` | `https://YOUR-RAILWAY-URL.up.railway.app` |
| `RH_WALLET_API_KEY` | same as Railway `RH_WALLET_API_KEY` |

Install skill:

```text
install the skill at https://github.com/anondevv69/RH-Wallet/tree/main/skill
```

---

## Optional: default URL in skill

After you have a stable Railway domain, you can document it in `skill/SKILL.md` as the recommended `RH_WALLET_API_URL` for your hosted instance. Users still need their own `RH_WALLET_API_KEY` once multi-tenant exists; today they share yours if you give it to them.

---

## Phase 2 (others, no coding)

To let strangers connect **their** Robinhood keys to **your** Railway host:

- Postgres + encrypted credential vault
- `/connect` web UI
- Per-user `RH_WALLET_API_KEY` issued at connect time

Until then, each person either uses **your** RH account (not recommended for public) or deploys **their own** Railway.
