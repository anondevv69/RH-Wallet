# Setup — RH Wallet + Bankr

## Universal hosting (one Railway, many users)

**Host (you) on Railway:**

1. Deploy repo — see [RAILWAY.md](../../RAILWAY.md)
2. Set only:
   - `MASTER_ENCRYPTION_KEY` (`openssl rand -hex 32`)
   - `DATABASE_URL` (Railway Postgres)
   - `PUBLIC_BASE_URL` (`https://your-app.up.railway.app`)
3. Do **not** put user Robinhood keys in Railway env

**Each user:**

1. Open `https://your-app.up.railway.app/connect`
2. Paste RH API key + private key
3. Copy issued credentials into **Bankr → Agent tool environment**:
   - `RH_WALLET_API_URL` = your public Railway URL
   - `RH_WALLET_API_KEY` = personal `rhw_...` key

4. Install skill:
   ```text
   install the skill at https://github.com/anondevv69/RH-Wallet/tree/main/skill
   ```

## Self-hosted (single user / dev)

### 1. Robinhood credentials

```bash
pip install pynacl
python scripts/generate_rh_keypair.py
```

Register public key in Robinhood crypto settings → copy API key.

### 2. Local gateway

```bash
cp .env.example .env
# fill RH_API_KEY, RH_PRIVATE_KEY_BASE64, RH_WALLET_API_KEY
docker compose up --build -d
```

Or enable multi-tenant locally with `MASTER_ENCRYPTION_KEY` and use `/connect`.

### 3. Bankr env vars

| Variable | Value |
|----------|--------|
| `RH_WALLET_API_URL` | Public or `http://127.0.0.1:8080` (local Bankr only) |
| `RH_WALLET_API_KEY` | From `/connect` or gateway `.env` |

## Smoke test

- “What’s my Robinhood buying power?”
- “Robinhood bid/ask for BTC-USD”

## Security

- Never paste RH private keys into Bankr chat
- Use `/connect` or your own `.env` only
- Revoke: `DELETE /v1/connect` with Bearer token (tenant keys only)
