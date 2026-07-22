"use strict";

/**
 * Bankr Partner API client — server-to-server wallet provisioning.
 * Docs: https://docs.bankr.bot/partnership/wallet-provisioning
 *
 * Partner key (bk_ptr_*) stays on your server only. Provisioned wallet keys (bk_usr_*)
 * are returned once at creation — store encrypted and use as X-API-Key for /agent/env etc.
 */

const BANKR_API_URL = process.env.BANKR_API_URL || "https://api.bankr.bot";

function partnerHeaders(partnerKey) {
  return {
    "Content-Type": "application/json",
    "X-Partner-Key": partnerKey,
  };
}

function walletHeaders(walletApiKey) {
  return {
    "Content-Type": "application/json",
    "X-API-Key": walletApiKey,
  };
}

/** @returns {boolean} True if this looks like a user wallet API key (existing Bankr terminal user). */
function isWalletApiKey(key) {
  return typeof key === "string" && key.startsWith("bk_usr_");
}

/** @returns {boolean} True if this looks like a partner provisioning key. */
function isPartnerApiKey(key) {
  return typeof key === "string" && key.startsWith("bk_ptr_");
}

/**
 * Create or fetch a provisioned wallet (idempotent).
 * @param {string} partnerKey bk_ptr_…
 * @param {object} opts
 * @param {string} opts.idempotencyKey Stable user id, e.g. "telegram:12345"
 * @param {boolean} [opts.generateApiKey=true]
 * @param {boolean} [opts.agentApiEnabled=true]
 * @param {object} [opts.fund] Optional { tokens, chain }
 */
async function provisionWallet(partnerKey, opts) {
  const body = {
    idempotencyKey: opts.idempotencyKey,
    apiKey: opts.generateApiKey !== false
      ? {
          permissions: {
            agentApiEnabled: opts.agentApiEnabled !== false,
            llmGatewayEnabled: !!opts.llmGatewayEnabled,
            tokenLaunchApiEnabled: !!opts.tokenLaunchApiEnabled,
            readOnly: false,
          },
        }
      : undefined,
    fund: opts.fund || undefined,
  };

  const res = await fetch(`${BANKR_API_URL}/partner/wallets`, {
    method: "POST",
    headers: partnerHeaders(partnerKey),
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Bankr provision failed (${res.status}): ${text}`);
  }
  if (!res.ok) {
    throw new Error(data.error || data.message || `Bankr provision failed (${res.status})`);
  }
  return {
    walletId: data.id,
    evmAddress: data.evmAddress?.toLowerCase?.() ?? data.evmAddress,
    solAddress: data.solAddress ?? null,
    idempotencyKey: data.idempotencyKey,
    apiKey: data.apiKey ?? null,
    created: res.status === 201,
    fund: data.fund ?? null,
  };
}

/** GET /partner/wallets/:identifier */
async function getProvisionedWallet(partnerKey, identifier) {
  const res = await fetch(`${BANKR_API_URL}/partner/wallets/${encodeURIComponent(identifier)}`, {
    headers: partnerHeaders(partnerKey),
  });
  if (res.status === 404) return null;
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    return null;
  }
  if (!res.ok) return null;
  return data;
}

/** POST /partner/wallets/:identifier/api-keys — issue a new wallet key if retry missed apiKey. */
async function generateWalletApiKey(partnerKey, identifier, permissions = {}) {
  const res = await fetch(`${BANKR_API_URL}/partner/wallets/${encodeURIComponent(identifier)}/api-keys`, {
    method: "POST",
    headers: partnerHeaders(partnerKey),
    body: JSON.stringify({
      permissions: {
        agentApiEnabled: permissions.agentApiEnabled !== false,
        readOnly: false,
        ...permissions,
      },
    }),
  });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Bankr api-key create failed (${res.status}): ${text}`);
  }
  if (!res.ok) {
    throw new Error(data.error || `Bankr api-key create failed (${res.status})`);
  }
  return data.apiKey;
}

/** Resolve EVM address from an existing user wallet key (terminal Bankr user). */
async function resolveWalletAddress(walletApiKey) {
  const res = await fetch(`${BANKR_API_URL}/wallet/me`, {
    headers: walletHeaders(walletApiKey),
  });
  if (!res.ok) return null;
  const data = await res.json();
  const addr = data.wallets?.find((w) => w.chain === "evm")?.address;
  return addr ? addr.toLowerCase() : null;
}

/** Save env vars to a provisioned (or existing) Bankr wallet. */
async function setWalletEnv(walletApiKey, vars) {
  const res = await fetch(`${BANKR_API_URL}/agent/env`, {
    method: "POST",
    headers: walletHeaders(walletApiKey),
    body: JSON.stringify({ vars }),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`Bankr env save failed (${res.status}): ${text}`);
  }
}

/** List env var keys configured on a wallet (values never returned). */
async function listWalletEnvKeys(walletApiKey) {
  const res = await fetch(`${BANKR_API_URL}/agent/env`, {
    headers: walletHeaders(walletApiKey),
  });
  if (!res.ok) return [];
  const data = await res.json();
  if (Array.isArray(data)) {
    return data.map((x) => (typeof x === "string" ? x : x?.key)).filter(Boolean);
  }
  if (data?.keys) return data.keys;
  return [];
}

/**
 * Resolve existing wallet OR provision a new one.
 * If userApiKey is provided and valid → link existing (terminal Bankr user path).
 * Otherwise → provision via partner key with idempotencyKey.
 */
async function resolveOrProvision(partnerKey, { idempotencyKey, userApiKey, fund }) {
  if (userApiKey && isWalletApiKey(userApiKey)) {
    const evmAddress = await resolveWalletAddress(userApiKey);
    if (!evmAddress) {
      throw new Error("Invalid bankr_api_key — could not resolve wallet");
    }
    return {
      evmAddress,
      walletId: null,
      apiKey: userApiKey,
      provisioned: false,
      existing: true,
    };
  }

  const result = await provisionWallet(partnerKey, { idempotencyKey, fund });
  let apiKey = result.apiKey;
  if (!apiKey && result.walletId) {
    apiKey = await generateWalletApiKey(partnerKey, result.walletId);
  }
  return {
    evmAddress: result.evmAddress,
    walletId: result.walletId,
    apiKey,
    provisioned: true,
    existing: false,
    created: result.created,
  };
}

const DEFAULT_SKILL_INSTALLS = [
  "install the skill at https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill",
  "install the skill at https://github.com/rhagent69/rhagentdotbotskill/tree/main/skill",
];

/** Queue default RH skills on a provisioned wallet (best-effort). */
async function installDefaultSkills(walletApiKey) {
  for (const prompt of DEFAULT_SKILL_INSTALLS) {
    try {
      await fetch(`${BANKR_API_URL}/agent/prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": walletApiKey,
        },
        body: JSON.stringify({ prompt }),
      });
    } catch {
      /* non-fatal */
    }
  }
}

/** Resolve or provision, then install default skills on new wallets. */
async function resolveOrProvisionAndSetup(partnerKey, opts) {
  const result = await resolveOrProvision(partnerKey, opts);
  if (result.apiKey && result.provisioned && !result.existing) {
    await installDefaultSkills(result.apiKey).catch(() => undefined);
  }
  return result;
}

module.exports = {
  BANKR_API_URL,
  DEFAULT_SKILL_INSTALLS,
  isWalletApiKey,
  isPartnerApiKey,
  provisionWallet,
  getProvisionedWallet,
  generateWalletApiKey,
  resolveWalletAddress,
  setWalletEnv,
  listWalletEnvKeys,
  resolveOrProvision,
  installDefaultSkills,
  resolveOrProvisionAndSetup,
};
