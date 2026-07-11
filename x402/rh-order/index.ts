/**
 * rh-order — place, list, or cancel Robinhood Crypto orders
 *
 * POST {
 *   "action": "place" | "list" | "cancel",
 *
 *   // for "place":
 *   "symbol": "BTC-USD",
 *   "side": "buy" | "sell",
 *   "quote_amount": "10.00",   // USD amount  (use this OR asset_quantity)
 *   "asset_quantity": "0.001", // asset units (use this OR quote_amount)
 *   "confirm": true,           // required when gateway has REQUIRE_CONFIRMATION
 *
 *   // for "list":
 *   "symbol": "BTC-USD",  // optional filter
 *   "side": "buy",        // optional filter
 *   "state": "filled",    // optional filter
 *
 *   // for "cancel":
 *   "order_id": "uuid"
 * }
 *
 * Required headers: x-rh-api-key, x-rh-private-key-b64
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rh-wallet-production.up.railway.app";
const GATEWAY_SECRET = process.env.GATEWAY_SECRET ?? "";

export default async function handler(req: Request) {
  const body = await req.json().catch(() => ({}));

  // Accept credentials from headers (curl/SDK) or body (bankr x402 call -d)
  const rhApiKey =
    req.headers.get("x-rh-api-key") ??
    body.rh_api_key ??
    "";
  const rhPrivKey =
    req.headers.get("x-rh-private-key-b64") ??
    body.rh_private_key_b64 ??
    "";

  if (!rhApiKey || !rhPrivKey) {
    return new Response(
      JSON.stringify({ error: "Provide rh_api_key and rh_private_key_b64 in the request body (or x-rh-api-key / x-rh-private-key-b64 headers)" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }
  const action: string = body.action ?? "list";

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    "x-rh-api-key": rhApiKey,
    "x-rh-private-key-base64": rhPrivKey,
    "x-gateway-secret": GATEWAY_SECRET,
  };

  if (action === "place") {
    const { symbol, side, quote_amount, asset_quantity, confirm, client_order_id } = body;

    if (!symbol || !side) {
      return new Response(
        JSON.stringify({ error: "symbol and side are required for action=place" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const res = await fetch(new URL("/v1/orders", GATEWAY_URL).toString(), {
      method: "POST",
      headers: authHeaders,
      body: JSON.stringify({ symbol, side, quote_amount, asset_quantity, confirm: confirm ?? false, client_order_id }),
    });

    const data = await res.json();
    if (!res.ok) return new Response(JSON.stringify(data), { status: res.status, headers: { "Content-Type": "application/json" } });
    return new Response(JSON.stringify(data), { status: 201, headers: { "Content-Type": "application/json" } });
  }

  if (action === "cancel") {
    const { order_id } = body;
    if (!order_id) {
      return new Response(
        JSON.stringify({ error: "order_id is required for action=cancel" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }
    const res = await fetch(new URL(`/v1/orders/${order_id}/cancel`, GATEWAY_URL).toString(), {
      method: "POST",
      headers: authHeaders,
    });
    const data = await res.json();
    if (!res.ok) return new Response(JSON.stringify(data), { status: res.status, headers: { "Content-Type": "application/json" } });
    return data;
  }

  // action === "list"
  const upstream = new URL("/v1/orders", GATEWAY_URL);
  if (body.symbol) upstream.searchParams.set("symbol", body.symbol.toUpperCase());
  if (body.side) upstream.searchParams.set("side", body.side);
  if (body.state) upstream.searchParams.set("state", body.state);

  const res = await fetch(upstream.toString(), { headers: authHeaders });
  const data = await res.json();
  if (!res.ok) return new Response(JSON.stringify(data), { status: res.status, headers: { "Content-Type": "application/json" } });
  return data;
}
