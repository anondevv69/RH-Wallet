"use strict";

/** Production telegram-agent base URL (Railway). Override with TELEGRAM_AGENT_URL. */
const DEFAULT_TELEGRAM_AGENT_URL =
  process.env.TELEGRAM_AGENT_URL || "https://rhagent-telegram-agent-production-d772.up.railway.app";

/**
 * Stage an Agentic token on the telegram-agent for one-time Telegram deep-link claim.
 * @param {{ accessToken: string, refreshToken?: string|null, agentBaseUrl?: string }} opts
 * @returns {Promise<{ code: string, deepLink: string, expiresAt: string, botUsername: string }>}
 */
async function stageTelegramHandoff({ accessToken, refreshToken = null, agentBaseUrl = DEFAULT_TELEGRAM_AGENT_URL }) {
  if (!accessToken) throw new Error("accessToken is required");
  const base = String(agentBaseUrl || DEFAULT_TELEGRAM_AGENT_URL).replace(/\/$/, "");
  const res = await fetch(`${base}/connect/agentic/stage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      agentic_token: accessToken,
      refresh_token: refreshToken || undefined,
    }),
  });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Telegram handoff failed (${res.status}): ${text}`);
  }
  if (!res.ok || !data.ok) {
    throw new Error(data.error || `Telegram handoff failed (${res.status})`);
  }
  return {
    code: data.code,
    deepLink: data.deep_link,
    expiresAt: data.expires_at,
    botUsername: data.bot_username,
  };
}

module.exports = { stageTelegramHandoff, DEFAULT_TELEGRAM_AGENT_URL };
