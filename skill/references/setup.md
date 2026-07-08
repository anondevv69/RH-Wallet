# Setup — RH Wallet + Bankr

## 1. Robinhood credentials

1. Generate an Ed25519 keypair:

   ```bash
   pip install pynacl
   python scripts/generate_rh_keypair.py
   ```

2. In Robinhood **crypto account settings on web classic**, create API credentials and paste the **public** key.
3. Copy the issued **API key** (`rh-api-...`).
4. Store the **private** key only for the gateway (`RH_PRIVATE_KEY_BASE64`). Never put it in Bankr.

## 2. Deploy the gateway

From the repo root:

```bash
cp .env.example .env
# fill RH_API_KEY, RH_PRIVATE_KEY_BASE64, RH_WALLET_API_KEY
docker compose up --build -d
```

**Or deploy to Railway** (for Bankr cloud / X): see [RAILWAY.md](../../RAILWAY.md).

Confirm:

```bash
curl -sS https://YOUR_HOST/health | jq
```

`rh_credentials_configured` and `gateway_auth_configured` should be `true`.

## 3. Bankr env vars

In Bankr Terminal: **gear → Env Vars** (or your host’s equivalent):

| Variable | Value |
|----------|--------|
| `RH_WALLET_API_URL` | `https://YOUR_HOST` (no trailing slash) |
| `RH_WALLET_API_KEY` | Same as gateway `RH_WALLET_API_KEY` |

## 4. Install the skill

Tell Bankr:

```text
install the skill at https://github.com/anondevv69/RH-Wallet/tree/main/skill
```

## 5. Smoke test

Ask Bankr:

- “What’s my Robinhood account status?”
- “What’s the Robinhood bid/ask for BTC-USD?”

If those work, try a tiny market buy with an amount under `MAX_ORDER_USD` only after explicit confirmation.

## Security checklist

- [ ] Dedicated Robinhood API credential (not your primary day-trading key if possible)
- [ ] Gateway funded only with amounts you can afford to lose via agent
- [ ] `MAX_ORDER_USD` set low (e.g. 25–50)
- [ ] `REQUIRE_CONFIRMATION=true`
- [ ] Gateway HTTPS + long random `RH_WALLET_API_KEY`
- [ ] Private key never in Bankr, chat, or git
