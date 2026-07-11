/**
 * rh-prices — real-time Robinhood Crypto best bid/ask
 *
 * GET ?symbol=BTC-USD,ETH-USD
 *
 * Caller must include their RH credentials in headers:
 *   x-rh-api-key: <api key>
 *   x-rh-private-key-b64: <base64 private key>
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rh-wallet-production.up.railway.app";
const GATEWAY_SECRET = process.env.GATEWAY_SECRET ?? "";

export default async function handler(req: Request) {
  const url = new URL(req.url);
  const symbol = url.searchParams.get("symbol") ?? "";

  const rhApiKey = req.headers.get("x-rh-api-key") ?? "";
  const rhPrivKey = req.headers.get("x-rh-private-key-b64") ?? "";

  if (!rhApiKey || !rhPrivKey) {
    return new Response(
      JSON.stringify({ error: "x-rh-api-key and x-rh-private-key-b64 headers are required" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const upstream = new URL("/v1/prices", GATEWAY_URL);
  if (symbol) {
    for (const s of symbol.split(",")) {
      upstream.searchParams.append("symbol", s.trim().toUpperCase());
    }
  }

  const res = await fetch(upstream.toString(), {
    headers: {
      "x-rh-api-key": rhApiKey,
      "x-rh-private-key-base64": rhPrivKey,
      "x-gateway-secret": GATEWAY_SECRET,
    },
  });

  const body = await res.json();

  if (!res.ok) {
    return new Response(JSON.stringify(body), {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  return body;
}
