/**
 * rh-order — place, list, or cancel Robinhood Crypto orders
 *
 * POST {
 *   "rh_api_key": "...",
 *   "rh_private_key_b64": "...",
 *   "action": "place" | "list" | "cancel",
 *   // place: symbol, side, quote_amount|asset_quantity, confirm
 *   // list:  symbol?, side?, state?
 *   // cancel: order_id
 * }
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rhwallet-rhagent-production.up.railway.app";
const GATEWAY_SECRET = process.env.GATEWAY_SECRET ?? "";

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

async function gatewayFetch(url: string, opts: RequestInit): Promise<Response> {
  const res = await fetch(url, opts);
  return res;
}

export default async function handler(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));

    const rhApiKey = req.headers.get("x-rh-api-key") ?? body.rh_api_key ?? "";
    const rhPrivKey = req.headers.get("x-rh-private-key-b64") ?? body.rh_private_key_b64 ?? "";

    if (!rhApiKey || !rhPrivKey) {
      return json(
        { error: "rh_api_key and rh_private_key_b64 are required (in body or x-rh-* headers)" },
        400
      );
    }

    const action: string = body.action ?? "list";

    const authHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      "x-rh-api-key": rhApiKey,
      "x-rh-private-key-base64": rhPrivKey,
      "x-gateway-secret": GATEWAY_SECRET,
    };

    async function parseResponse(res: Response, successStatus = 200): Promise<Response> {
      const text = await res.text();
      let parsed: unknown;
      try {
        parsed = JSON.parse(text);
      } catch {
        return json({ error: "Gateway returned non-JSON", status: res.status, raw: text.slice(0, 200) }, 502);
      }
      return json(parsed, res.ok ? successStatus : res.status);
    }

    if (action === "place") {
      const { symbol, side, quote_amount, asset_quantity, confirm, client_order_id } = body;
      if (!symbol || !side) {
        return json({ error: "symbol and side are required for action=place" }, 400);
      }
      const res = await gatewayFetch(new URL("/v1/orders", GATEWAY_URL).toString(), {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ symbol, side, quote_amount, asset_quantity, confirm: confirm ?? false, client_order_id }),
      });
      return parseResponse(res, 201);
    }

    if (action === "cancel") {
      const { order_id } = body;
      if (!order_id) return json({ error: "order_id is required for action=cancel" }, 400);
      const res = await gatewayFetch(
        new URL(`/v1/orders/${order_id}/cancel`, GATEWAY_URL).toString(),
        { method: "POST", headers: authHeaders }
      );
      return parseResponse(res);
    }

    // list
    const upstream = new URL("/v1/orders", GATEWAY_URL);
    if (body.symbol) upstream.searchParams.set("symbol", body.symbol.toUpperCase());
    if (body.side) upstream.searchParams.set("side", body.side);
    if (body.state) upstream.searchParams.set("state", body.state);
    const res = await gatewayFetch(upstream.toString(), { headers: authHeaders });
    return parseResponse(res);

  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return json({ error: "Handler error", detail: msg }, 500);
  }
}
