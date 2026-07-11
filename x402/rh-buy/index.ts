/**
 * rh-buy — bundled flow: prices → account check → place order
 *
 * POST {
 *   "rh_api_key": "...",
 *   "rh_private_key_b64": "...",
 *   "symbol": "DOGE-USD",
 *   "side": "buy" | "sell",
 *   "quote_amount": "1",        // USD (use this OR asset_quantity)
 *   "asset_quantity": "13.5",   // asset units (use this OR quote_amount)
 *   "confirm": true             // required — gateway enforces confirmation
 * }
 */

const GATEWAY_URL = process.env.GATEWAY_URL ?? "https://rh-wallet-production.up.railway.app";
const GATEWAY_SECRET = process.env.GATEWAY_SECRET ?? "";

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

async function gatewayJson(
  path: string,
  authHeaders: Record<string, string>,
  init?: RequestInit
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const res = await fetch(new URL(path, GATEWAY_URL).toString(), {
    ...init,
    headers: { ...authHeaders, ...(init?.headers as Record<string, string> | undefined) },
  });
  const text = await res.text();
  try {
    return { ok: res.ok, status: res.status, data: JSON.parse(text) };
  } catch {
    return { ok: false, status: res.status, data: { error: "Gateway returned non-JSON", raw: text.slice(0, 200) } };
  }
}

export default async function handler(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));

    const rhApiKey = req.headers.get("x-rh-api-key") ?? body.rh_api_key ?? "";
    const rhPrivKey = req.headers.get("x-rh-private-key-b64") ?? body.rh_private_key_b64 ?? "";

    if (!rhApiKey || !rhPrivKey) {
      return json(
        {
          error: "rh_api_key and rh_private_key_b64 are required",
          hint: "Use straight ASCII quotes in JSON — smart quotes break parsing",
        },
        400
      );
    }

    const { symbol, side, quote_amount, asset_quantity, confirm, client_order_id } = body;

    const confirmed =
      confirm === true ||
      confirm === "true" ||
      confirm === 1 ||
      confirm === "1";

    if (!symbol || !side) {
      return json({ error: "symbol and side are required" }, 400);
    }
    if (!quote_amount && !asset_quantity) {
      return json({ error: "Provide quote_amount or asset_quantity" }, 400);
    }
    if (!confirmed) {
      return json(
        {
          error: "confirm must be true — this endpoint places a real order after showing prices and account",
          received_confirm: confirm,
        },
        400
      );
    }

    const authHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      "x-rh-api-key": rhApiKey,
      "x-rh-private-key-base64": rhPrivKey,
      "x-gateway-secret": GATEWAY_SECRET,
    };

    const sym = String(symbol).toUpperCase();

    // Step 1: prices for the symbol
    const pricesUrl = new URL("/v1/prices", GATEWAY_URL);
    pricesUrl.searchParams.append("symbol", sym);
    const prices = await gatewayJson(pricesUrl.pathname + pricesUrl.search, authHeaders);

    // Step 2: account summary (buying power)
    const account = await gatewayJson("/v1/account", authHeaders);

    // Optional: warn if buying power looks insufficient (don't block — gateway validates)
    let buyingPowerNote: string | undefined;
    if (account.ok && quote_amount && typeof account.data === "object" && account.data !== null) {
      const bp = parseFloat((account.data as { buying_power?: string }).buying_power ?? "0");
      const need = parseFloat(String(quote_amount));
      if (!Number.isNaN(bp) && !Number.isNaN(need) && bp < need) {
        buyingPowerNote = `Buying power ($${bp.toFixed(2)}) may be less than order size ($${need.toFixed(2)}).`;
      }
    }

    // Step 3: place order
    const order = await gatewayJson("/v1/orders", authHeaders, {
      method: "POST",
      body: JSON.stringify({
        symbol: sym,
        side: String(side).toLowerCase(),
        quote_amount: quote_amount != null ? String(quote_amount) : undefined,
        asset_quantity: asset_quantity != null ? String(asset_quantity) : undefined,
        confirm: true,
        client_order_id,
      }),
    });

    // Always return 200 when prices + account succeeded so caller gets full context
    return json(
      {
        flow: "prices → account → order",
        symbol: sym,
        side: String(side).toLowerCase(),
        buying_power_note: buyingPowerNote,
        order_ok: order.ok,
        prices: prices.data,
        account: account.data,
        order: order.data,
      },
      order.ok ? 201 : 200
    );
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return json({ error: "Handler error", detail: msg }, 500);
  }
}
