# Getting started — RH Wallet + Bankr

**Setup wizard (start here):** https://rh-wallet-production.up.railway.app/setup

US only. Two products: **Robinhood Crypto** (BTC, DOGE) and **Robinhood Agentic** (stocks, options).

---

## Step 1 — Install the skill

In Bankr terminal chat:

```
install the skill at https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill
```

Then:

```
set up rh-wallet
```

Bankr will walk you through what's missing.

---

## Step 2 — Robinhood Crypto (optional)

Skip if you only want stocks/options.

1. Generate keys:
   ```bash
   pip install pynacl
   python3 scripts/generate_rh_keypair.py
   ```
   (Clone repo first, or use the setup wizard on Railway.)

2. Register the **public key** in Robinhood crypto API settings (Robinhood web).

3. Bankr → **Settings → Env Vars** → add:
   - `RH_API_KEY` = your `rh-api-...`
   - `RH_PRIVATE_KEY_BASE64` = your private key

4. Test: *"What's my Robinhood crypto buying power?"*

Details: [setup.md](setup.md)

---

## Step 3 — Robinhood Agentic (stocks & options)

One-time on your Mac/PC (~2 min). After this, everything runs in Bankr 24/7.

1. Open: https://rh-wallet-production.up.railway.app/setup

2. Run locally:
   ```bash
   bankr login
   curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
   ```

3. Browser → Robinhood → tap **Allow** on your Agentic account.

4. Token saves to Bankr as `AGENTIC_TOKEN` (if `bankr login` was run).

5. Test: *"What is my Robinhood Agentic buying power?"*

Details: [agentic-connect.md](agentic-connect.md)

---

## Step 4 — Use Bankr

| You want | Say |
|----------|-----|
| Crypto balance | "What's my Robinhood crypto buying power?" |
| Buy DOGE | "Buy $1 of DOGE on Robinhood" |
| Agentic buying power | "What is my Robinhood Agentic buying power?" |
| Stock quote | "Quote SPCX on Robinhood Agentic" |
| Fundamentals / technicals | "What's NVDA's P/E and RSI on Agentic?" |
| Earnings | "When does AAPL report earnings?" |
| Tradability | "Is SPCX fractional on Robinhood Agentic?" |
| Buy stock | "Buy $5 of SPCX on my Agentic account" |
| Options | "Show GME option chain" / "Buy a GME call" |

Full Agentic tool list and prompts: [AGENTIC-CAPABILITIES.md](AGENTIC-CAPABILITIES.md)

---

## Security

- Keys and tokens live in **your Bankr vault only** — not on Railway
- Never share account numbers — skill redacts them from replies
- Revoke: Robinhood Security settings · delete `AGENTIC_TOKEN` in Bankr env

---

## Token refresh

Agentic token expires ~every 9 days. Re-run:

```bash
curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash
```
