/**
 * rh-prices — real-time Robinhood Crypto best bid/ask
 *
 * GET ?symbol=BTC-USD,ETH-USD&rh_api_key=...&rh_private_key_b64=...
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rh-wallet-production.up.railway.app";
const GATEWAY_SECRET = process.env.GATEWAY_SECRET ?? "";

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export default async function handler(req: Request) {
  try {
    const url = new URL(req.url);

    // Parse body if POST
    const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};

    const symbol =
      url.searchParams.get("symbol") ??
      body.symbol ??
      "";

    const rhApiKey =
      req.headers.get("x-rh-api-key") ??
      url.searchParams.get("rh_api_key") ??
      body.rh_api_key ??
      "";
    const rhPrivKey =
      req.headers.get("x-rh-private-key-b64") ??
      url.searchParams.get("rh_private_key_b64") ??
      body.rh_private_key_b64 ??
      "";

    if (!rhApiKey || !rhPrivKey) {
      return json(
        { error: "rh_api_key and rh_private_key_b64 are required (query params or x-rh-* headers)" },
        400
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

    const text = await res.text();
    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch {
      return json({ error: "Gateway returned non-JSON", status: res.status, raw: text.slice(0, 200) }, 502);
    }

    return json(parsed, res.ok ? 200 : res.status);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return json({ error: "Handler error", detail: msg }, 500);
  }
}
