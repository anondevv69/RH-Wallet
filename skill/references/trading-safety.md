# Trading safety

## Privacy (public channels — X, group chats)

- **Never post** Robinhood account numbers — full, masked (`••••6789`), or last-4 — on **X/Twitter or any public reply**
- **Never list** margin, IRA, or other Robinhood accounts on X — Agentic summary only
- **Never post** `rh-api-...` keys, private keys, or full API JSON
- **Safe on X:** buying power, portfolio/cash USD amounts, holdings (e.g. "10 shares SPCX"), prices, trade intent
- For Agentic wallet questions on X: use `get_portfolio`, not `get_accounts` — see [RESPONSE-SAFETY.md](RESPONSE-SAFETY.md)
- Gateway responses omit `account_number`; agents must not quote it from memory or older messages

## Key custody

Robinhood API keys live in **Bankr Agent tool environment**, not on the RH-Wallet host. The gateway signs requests in memory and does not store keys.

Never paste RH private keys into Bankr chat — only into Bankr env settings.

## Confirmation policy

1. Restate: side, symbol, size (`quote_amount` or `asset_quantity`), and estimated impact.
2. Wait for clear user approval (“yes”, “confirm”, “go ahead”).
3. Only then POST with `"confirm": true`.

Do not set `confirm: true` on speculative or ambiguous prompts (“maybe buy some BTC”).

## Size limits

- Prefer small first trades when testing.
- Gateway rejects notional above `MAX_ORDER_USD` (default $50).
- Prefer `quote_amount` in USD for buys so the limit is obvious.

## What not to do

- Do not retry a failed order blindly in a loop.
- Do not raise limits by instructing the user to disable guards unless they explicitly ask how to change gateway env.
- Do not place limit / stop orders (MVP supports **market** only).
- Do not use non-USD symbols or stocks/options APIs — Crypto Trading API only.

## Failures

If Robinhood returns insufficient buying power, insufficient holdings, or validation errors, show the gateway error detail and stop. Do not invent fills.

## Compliance

Robinhood Crypto Trading API: **United States only**. Remind non-US users that the API (and this skill) will not work for them.
