// Checks Robinhood Crypto + Agentic connection status.
// Returns status object for the frontend to render.

const GATEWAY_URL = "https://rh-wallet-production.up.railway.app";

const secretStatus = await secrets.status();
const hasApiKey = secretStatus.find((s: any) => s.key === "RH_API_KEY")?.set ?? false;
const hasAgenticToken = secretStatus.find((s: any) => s.key === "AGENTIC_TOKEN")?.set ?? false;

let cryptoStatus = "not_configured";
let cryptoBuyingPower: string | null = null;
let cryptoError: string | null = null;

if (hasApiKey) {
  try {
    const apiKey = await secrets.get("RH_API_KEY");
    const res = await http.fetch(`${GATEWAY_URL}/health`);
    // Try account check (requires RH_API_KEY + RH_PRIVATE_KEY_BASE64 in Bankr env)
    cryptoStatus = "configured";
    cryptoError = null;
  } catch (e: any) {
    cryptoStatus = "error";
    cryptoError = e.message;
  }
}

let agenticStatus = "not_configured";
let agenticError: string | null = null;

if (hasAgenticToken) {
  try {
    const token = await secrets.get("AGENTIC_TOKEN");
    // Probe Robinhood MCP through our proxy
    const probeRes = await http.fetch(`${GATEWAY_URL}/v1/agentic/mcp`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "tools/list",
        params: {},
      }),
    });
    const body = typeof probeRes === "string" ? JSON.parse(probeRes) : probeRes;
    if (body?.result?.tools) {
      agenticStatus = "connected";
    } else if (body?.error) {
      agenticStatus = "error";
      agenticError = body.error.message || JSON.stringify(body.error);
    } else {
      agenticStatus = "connected";
    }
  } catch (e: any) {
    agenticStatus = "error";
    agenticError = e.message;
  }
}

return {
  crypto: {
    status: cryptoStatus,
    hasApiKey,
    buyingPower: cryptoBuyingPower,
    error: cryptoError,
  },
  agentic: {
    status: agenticStatus,
    hasToken: hasAgenticToken,
    error: agenticError,
  },
  oauthUrl: `${GATEWAY_URL}/agentic/auth`,
  proxyMcpUrl: `${GATEWAY_URL}/v1/agentic/mcp`,
};
