# Trading safety

## Scope

This skill controls **Robinhood Crypto** funds, not Bankr’s onchain wallet. Say so in every trading reply.

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
