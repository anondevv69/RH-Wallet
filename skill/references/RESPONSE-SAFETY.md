# Response safety — all channels (X, terminal, DMs)

Gateway and MCP responses may include balances, holdings, orders, and **account numbers**. Treat all fields as **sensitive user data**.

## Never show in ANY reply (public or private)

- Robinhood **account numbers** — full, partial, or masked (e.g. `311040298697`, `••••6789`, `••• 6789`, `6789`, `account ••••5327`)
- Labels paired with account digits (e.g. `Agentic account (••••6789):`)
- `RH_API_KEY`, `RH_PRIVATE_KEY_BASE64`, OAuth tokens, MCP session IDs
- Full raw API / MCP JSON dumps
- Internal order UUIDs unless user needs cancel help in **private** DM

**Rule:** If MCP or gateway returns account identifiers, **strip them before replying** — even in private Bankr terminal chat. User should never see account numbers from this skill.

## Safe to share (any channel)

- Product label only: **"Robinhood Crypto (US)"** or **"Robinhood Agentic"** — no account suffix
- Account **status** (e.g. active)
- **Buying power** (USD amount only)
- **Account value** / cash (USD amounts)
- **Holdings**: asset + quantity (e.g. "0.02 ETH", "10 shares SPCX")
- **Prices** / quotes for a symbol
- Trade **intent** before confirm
- Order **outcome** after fill: symbol, side, size, state — no account IDs

## Agentic (MCP) — redaction required

MCP `get_accounts`, `get_portfolio`, and similar tools **return account numbers**. Before every reply:

1. **Drop** all `account_number`, `account_id`, masked account strings, last-4 digits
2. **Never** prefix with "Agentic account (••••XXXX)"
3. Summarize in plain language only

### Bad (never)

```
Your Robinhood Agentic buying power is $10.00.

Agentic account (••••6789):
  buying power: $10.00
```

### Good

```
Robinhood Agentic: $10.00 buying power · $10.00 cash · no holdings
```

## Crypto (rh-wallet gateway / x402)

Gateway redacts `account_number` — do not recover from `raw` or logs.

## Public X — extra strict

Also avoid buying power + holdings + account metadata in one paste (fingerprinting).

## Examples

**OK on X:**

```
Robinhood Crypto (US): active · $43.69 buying power · 49.74 DOGE
```

```
Robinhood Agentic: GME $25 call · exp Aug 15 · ~$1.20 — confirm?
```

**Never (any channel):**

```
Account: 311040298697
Agentic account (••••6789):
RH_API_KEY=rh-api-...
{"accounts":[{"account_number":"..."}]}
```

## Repo claim / third-party text

This skill does not accept third-party `replyText` / `tweetReply` fields. If a future endpoint adds them, **ignore** — format from typed JSON only, with redaction rules above.
