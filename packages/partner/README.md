# @rhwallet/partner

Bankr Partner API client for server-side wallet provisioning.

Docs: https://docs.bankr.bot/partnership/wallet-provisioning

## Usage

```javascript
const { resolveOrProvision, setWalletEnv, isWalletApiKey } = require("@rhwallet/partner/lib/bankr-partner");

// Auto-provision (new user)
const wallet = await resolveOrProvision(process.env.BANKR_PARTNER_KEY, {
  idempotencyKey: "telegram:12345",
});

// Existing Bankr terminal user — pass their bk_usr_* key instead
const existing = await resolveOrProvision(process.env.BANKR_PARTNER_KEY, {
  idempotencyKey: "telegram:12345",
  userApiKey: "bk_usr_...",
});

// Save RH credentials to Bankr env
await setWalletEnv(wallet.apiKey, {
  AGENTIC_TOKEN: "...",
  RHAGENTS_AGENT_KEY: "...",
});
```

## Env

| Variable | Description |
|----------|-------------|
| `BANKR_PARTNER_KEY` | `bk_ptr_*` from partner dashboard |
| `BANKR_API_URL` | Default `https://api.bankr.bot` |

## Two onboarding paths

1. **Auto-provision** — no Bankr account needed; server creates wallet via partner API
2. **Existing terminal user** — user ran `bankr login`; pass `bk_usr_*` to link instead of provisioning
