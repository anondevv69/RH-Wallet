/**
 * rh-account — Robinhood Crypto account summary + holdings
 *
 * POST { "rh_api_key": "...", "rh_private_key_b64": "...", "view": "account" | "holdings", "asset_codes": ["BTC"] }
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
    const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};

    const rhApiKey = req.headers.get("x-rh-api-key") ?? body.rh_api_key ?? "";
    const rhPrivKey = req.headers.get("x-rh-private-key-b64") ?? body.rh_private_key_b64 ?? "";

    if (!rhApiKey || !rhPrivKey) {
      return json(
        { error: "rh_api_key and rh_private_key_b64 are required (in body or x-rh-* headers)" },
        400
      );
    }

    const view: string = body.view ?? "account";
    const assetCodes: string[] = body.asset_codes ?? [];

    const authHeaders: Record<string, string> = {
      "x-rh-api-key": rhApiKey,
      "x-rh-private-key-base64": rhPrivKey,
      "x-gateway-secret": GATEWAY_SECRET,
    };

    let upstreamUrl: string;
    if (view === "holdings") {
      const u = new URL("/v1/holdings", GATEWAY_URL);
      for (const code of assetCodes) u.searchParams.append("asset_code", code.toUpperCase());
      upstreamUrl = u.toString();
    } else {
      upstreamUrl = new URL("/v1/account", GATEWAY_URL).toString();
    }

    const res = await fetch(upstreamUrl, { headers: authHeaders });
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
