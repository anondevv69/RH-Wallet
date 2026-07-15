# RH Agentic Connect (desktop)

One-click Mac/Windows app for Robinhood Agentic OAuth — **no Terminal**.

1. Double-click **Connect Robinhood**
2. Sign in to Robinhood → Allow
3. Tap **Open Telegram** — the bot claims a one-time code and stores your token

## Dev

```bash
cd packages/connect-desktop
npm install
npm start
```

## Build

```bash
npm run dist:mac   # .dmg / .zip
npm run dist:win   # .exe (NSIS + portable)
```

Artifacts land in `release/`. CI publishes them to GitHub Releases on `rhagent69/rhwallet-rhagent`.

## Handoff

After OAuth the app POSTs the token to the telegram-agent:

`POST https://rhagent-telegram-agent-production-d772.up.railway.app/connect/agentic/stage`

Override with env `TELEGRAM_AGENT_URL` when packaging/testing.
