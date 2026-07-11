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
  const rhApiKey = req.headers.get("x-rh-api-key") ?? "";
  const rhPrivKey = req.headers.get("x-rh-private-key-b64") ?? "";

  if (!rhApiKey || !rhPrivKey) {
    return new Response(
      JSON.stringify({ error: "x-rh-api-key and x-rh-private-key-b64 headers are required" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
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
