/**
 * rh-agentic-mcp — paid proxy for Robinhood Agentic MCP tools.
 *
 * Forwards a single MCP JSON-RPC call to the stateless gateway proxy,
 * which in turn forwards to Robinhood. The caller pays USDC per call.
 *
 * POST {
 *   "agentic_token": "...",   // Robinhood OAuth token (from /agentic/auth flow)
 *   "method": "tools/call",   // MCP method: tools/list, tools/call, etc.
 *   "params": { ... }         // MCP method params
 * }
 *
 * The token is passed straight through to Robinhood — never stored here.
 * Free methods (tools/list, initialize) are allowed without payment.
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rh-wallet-production.up.railway.app";

const FREE_METHODS = new Set(["initialize", "tools/list", "ping"]);

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export default async function handler(req: Request): Promise<Response> {
  if (req.method === "GET") {
    return json({
      service: "rh-agentic-mcp",
      description:
        "Paid proxy for Robinhood Agentic MCP (stocks & options). " +
        "Requires agentic_token from https://rh-wallet-production.up.railway.app/agentic/setup",
      pricing: "Free: tools/list, initialize. Paid: all tool calls.",
      setup: "https://github.com/anondevv69/RH-Wallet",
    });
  }

  if (req.method !== "POST") {
    return json({ error: "POST required" }, 405);
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  const agenticToken =
    (body.agentic_token as string) ||
    req.headers.get("X-Agentic-Token") ||
    "";

  if (!agenticToken) {
    return json(
      {
        error: "agentic_token required",
        detail:
          "Provide your Robinhood OAuth token — run rh-connect.sh from https://rh-wallet-production.up.railway.app/agentic/setup",
      },
      400
    );
  }

  const method = (body.method as string) || "";
  const params = (body.params as Record<string, unknown>) || {};
  const id = body.id ?? 1;

  const mcpPayload = {
    jsonrpc: "2.0",
    id,
    method,
    params,
  };

  const res = await fetch(`${GATEWAY_URL}/v1/agentic/mcp`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${agenticToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(mcpPayload),
  });

  let upstream: unknown;
  try {
    upstream = await res.json();
  } catch {
    upstream = await res.text();
  }

  if (!res.ok) {
    return json(
      {
        error: "Robinhood Agentic error",
        status: res.status,
        detail: upstream,
      },
      res.status
    );
  }

  return json(upstream);
}
