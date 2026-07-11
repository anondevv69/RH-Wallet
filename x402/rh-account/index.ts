/**
 * rh-account — Robinhood Crypto account summary + holdings
 *
 * POST { "view": "account" | "holdings", "asset_codes": ["BTC","ETH"] }
 *   + headers: x-rh-api-key, x-rh-private-key-b64
 *
 * Returns redacted account summary or holdings list.
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rh-wallet-production.up.railway.app";
const GATEWAY_SECRET = process.env.GATEWAY_SECRET ?? "";

export default async function handler(req: Request) {
  const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};

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
  const view: string = body.view ?? "account";
  const assetCodes: string[] = body.asset_codes ?? [];

  const authHeaders = {
    "x-rh-api-key": rhApiKey,
    "x-rh-private-key-base64": rhPrivKey,
    "x-gateway-secret": GATEWAY_SECRET,
  };

  if (view === "holdings") {
    const upstream = new URL("/v1/holdings", GATEWAY_URL);
    for (const code of assetCodes) {
      upstream.searchParams.append("asset_code", code.toUpperCase());
    }
    const res = await fetch(upstream.toString(), { headers: authHeaders });
    const data = await res.json();
    if (!res.ok) return new Response(JSON.stringify(data), { status: res.status, headers: { "Content-Type": "application/json" } });
    return data;
  }

  const res = await fetch(new URL("/v1/account", GATEWAY_URL).toString(), {
    headers: authHeaders,
  });
  const data = await res.json();
  if (!res.ok) return new Response(JSON.stringify(data), { status: res.status, headers: { "Content-Type": "application/json" } });
  return data;
}
