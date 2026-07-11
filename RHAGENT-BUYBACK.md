# RHAGENT Buyback Automation

Revenue from the x402 endpoints settles as **USDC on Base** into your Bankr wallet. This guide explains how to auto-convert that revenue into **RHAGENT** on Robinhood Chain.

## Token info

| Field | Value |
|-------|-------|
| Token | RHAGENT |
| Contract | `0x894fac757250f8e02180e1856957274d84ac4ba3` |
| Chain | Robinhood Chain (chain ID `4663`) |
| Decimals | 18 |
| Bankr wallet (pays to) | `0x374d91a5674fa7cf86e725093b5848b97e1e13b4` |

## Current architecture

```
Caller pays USDC (Base)
    ↓
x402.bankr.bot → your Bankr wallet (Base USDC)
    ↓  [automation below]
Bankr swap: Base USDC → RHAGENT on Robinhood Chain
```

## Tell Bankr to automate

Say this to Bankr once you want to activate the buyback:

```
When my Base USDC balance hits $10, swap all of it to RHAGENT 
(0x894fac757250f8e02180e1856957274d84ac4ba3) on Robinhood Chain.
Keep $1 in USDC for gas. Set max slippage 3%.
```

Adjust the `$10` threshold and `3%` slippage to your preference.

## Manual swap (one-time)

```
bankr wallet swap \
  --from-chain base \
  --from-token USDC \
  --to-chain robinhood \
  --to-token 0x894fac757250f8e02180e1856957274d84ac4ba3 \
  --amount 10
```

## Future: native RHAGENT payment (when supported)

When Bankr adds token resolution for Robinhood Chain, update `bankr.x402.json`:

```json
{
  "network": "robinhood",
  "currency": "RHAGENT",
  "tokenAddress": "0x894fac757250f8e02180e1856957274d84ac4ba3"
}
```

Then redeploy: `bankr x402 deploy`

At that point callers pay RHAGENT directly — no buyback step needed.

## Pricing reference

| Endpoint | Price/req | Notes |
|----------|-----------|-------|
| rh-prices | $0.25 USDC | Real-time prices |
| rh-account | $0.25 USDC | Account/holdings read |
| rh-order | $0.25 USDC | Order placement |
| rh-buy | $0.50 USDC | Bundled: prices + account + order |
