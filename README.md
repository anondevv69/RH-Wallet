# RH Wallet

Robinhood **Crypto** + **Agentic** (stocks/options) for [Bankr](https://docs.bankr.bot/skills/overview).

**Public repo (skill install + scripts):** [github.com/rhagent69/rhwallet-rhagent](https://github.com/rhagent69/rhwallet-rhagent)

**→ Setup wizard: https://rhwallet-rhagent-production.up.railway.app/setup**  
(also: `/helpsetup` — same page)

## Bankr users — quick start

1. **Install skill** (Bankr chat):
   ```
   install the skill at https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill
   set up rh-wallet
   ```

2. **Crypto** (BTC, DOGE): add `RH_API_KEY` + `RH_PRIVATE_KEY_BASE64` to Bankr env — [skill/references/setup.md](skill/references/setup.md)

3. **Agentic** (stocks/options): one local command (~2 min):
   ```bash
   bankr login
   curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
   ```

4. **Ask Bankr:** *"What is my Robinhood Agentic buying power?"*

Full steps: [skill/references/GETTING-STARTED.md](skill/references/GETTING-STARTED.md)

---

# RH Wallet Gateway (developers)

Stateless Robinhood Crypto signing proxy + Bankr skill.

```
User → Bankr (RH keys in Agent env) → RH Wallet Gateway (sign only) → Robinhood
```

**Robinhood keys stay in Bankr — not on the gateway host by default.**

US customers only. Subject to Robinhood Crypto Customer Agreement.

## What’s in this repo

| Path | Purpose |
|------|---------|
| [`gateway/`](gateway/) | FastAPI signed proxy (`/v1/*`) |
| [`skill/`](skill/) | Bankr-installable `rh-wallet` skill |
| [`scripts/generate_rh_keypair.py`](scripts/generate_rh_keypair.py) | Ed25519 keypair helper |

## Quick start

### 1. Create Robinhood API credentials

1. Generate a keypair:

   ```bash
   pip install pynacl
   python scripts/generate_rh_keypair.py
   ```

2. In Robinhood **crypto account settings (web classic)**, create API credentials and paste the **public** key.
3. Save the returned **API key** (`rh-api-...`) and keep the **private** key offline.

### 2. Configure the gateway

```bash
cp .env.example .env
# Edit .env:
#   RH_API_KEY=...
#   RH_PRIVATE_KEY_BASE64=...
#   RH_WALLET_API_KEY=<long random token for Bankr>
```

### 3. Run

**Docker Compose (recommended):**

```bash
docker compose up --build
```

**Local:**

```bash
cd gateway
python3 -m pip install -e ".[dev]"
RH_API_KEY=... RH_PRIVATE_KEY_BASE64=... RH_WALLET_API_KEY=... \
  uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Health check (no auth):

```bash
curl http://localhost:8080/health
```

### 4. Install the Bankr skill

In Bankr (or any skills-compatible agent):

```text
install the skill at https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill
```

Set Bankr Env Vars (gear → Env Vars):

- `RH_WALLET_API_URL` — optional; defaults to `https://rhwallet-rhagent-production.up.railway.app` in the skill
- `RH_WALLET_API_KEY` — same value as gateway `RH_WALLET_API_KEY`

See [`skill/references/setup.md`](skill/references/setup.md).

## Gateway API

All `/v1/*` routes require `Authorization: Bearer $RH_WALLET_API_KEY`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness (no auth) |
| GET | `/v1/account` | Primary crypto account |
| GET | `/v1/holdings` | Holdings (`?asset_code=BTC`) |
| GET | `/v1/trading-pairs` | Tradable pairs |
| GET | `/v1/prices?symbol=BTC-USD` | Best bid/ask |
| GET | `/v1/estimate?symbol=BTC-USD&side=ask&quantity=0.001` | Estimated price |
| GET | `/v1/orders` | List orders |
| GET | `/v1/orders/{id}` | Get order |
| POST | `/v1/orders` | Place market order |
| POST | `/v1/orders/{id}/cancel` | Cancel order |

### Place a market order

```bash
curl -sS -X POST "$RH_WALLET_API_URL/v1/orders" \
  -H "Authorization: Bearer $RH_WALLET_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "side": "buy",
    "symbol": "BTC-USD",
    "quote_amount": "10.00",
    "confirm": true
  }'
```

Provide **exactly one** of `quote_amount` (USD, preferred for buys) or `asset_quantity` (preferred for sells).

## Safety defaults

| Env | Default | Meaning |
|-----|---------|---------|
| `MAX_ORDER_USD` | `50` | Reject orders above this notional |
| `REQUIRE_CONFIRMATION` | `true` | Require `"confirm": true` on POST `/v1/orders` |

Use a dedicated Robinhood API credential funded only with what the agent needs. Prefer small `MAX_ORDER_USD` in production.

## Tests

```bash
cd gateway
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

Includes a golden test against Robinhood’s documented Ed25519 sample signature.

## Deploy notes

- Deploy the gateway where Bankr can reach it (public HTTPS or VPN).
- **Railway:** see [RAILWAY.md](RAILWAY.md) for step-by-step deploy and env vars.
- Keep `RH_PRIVATE_KEY_BASE64` only on the gateway (KMS / platform secrets).
- Bankr never receives the Robinhood private key — only the gateway Bearer token.
- Robinhood timestamps are valid for ~30 seconds; keep host clocks accurate (NTP).
- Rate limits: ~100 requests/min per RH account (burst ~300).

### Bankr env vars (each user)

| Variable | Where |
|----------|--------|
| `RH_WALLET_API_URL` | Public gateway URL (skill default) |
| `RH_API_KEY` | User's Robinhood API key |
| `RH_PRIVATE_KEY_BASE64` | User's Ed25519 private key |
| `RH_GATEWAY_SECRET` | Public default in [skill/references/hosted-config.md](skill/references/hosted-config.md) |

### Railway host env (you)

| Variable | Purpose |
|----------|---------|
| `PUBLIC_BASE_URL` | Your HTTPS domain |
| `GATEWAY_SHARED_SECRET` | Must match [hosted-config.md](skill/references/hosted-config.md) |
| `MAX_ORDER_USD` | Order size cap |

See [RAILWAY.md](RAILWAY.md). **Do not** put user RH keys on Railway.

## Out of scope (MVP)

- Multi-tenant per-user credential vault
- Limit / stop-loss / stop-limit orders
- Bridging Robinhood balances to Bankr onchain wallets

## License / compliance

You are responsible for complying with Robinhood’s terms and US crypto regulations when using this software. This project is unaffiliated with Robinhood Markets, Inc.
