"""Inject Agentic account_number on MCP calls — agents never see it.

Robinhood MCP (v15+) requires `account_number` on portfolio/positions/orders/trades
as well as place/review/cancel. The gateway redacts account numbers from responses,
so agents cannot discover them — we resolve + inject server-side instead.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"

# account_number rarely changes mid-session — cache per-token to avoid an extra
# upstream get_accounts round-trip on every portfolio/positions/orders call.
_ACCOUNT_CACHE_TTL_S = 10 * 60
_account_cache: dict[str, tuple[str, float]] = {}


def _cache_key(headers: dict[str, str]) -> Optional[str]:
    auth = headers.get("Authorization", "")
    if not auth:
        return None
    # Hash rather than store the raw bearer token in memory.
    return hashlib.sha256(auth.encode()).hexdigest()

# Do NOT include get_accounts — that remains the discovery tool (no account_number needed).
# Tool names must match Robinhood's actual MCP catalog exactly — see
# skill/references/AGENTIC-CAPABILITIES.md. There is no generic get_positions/get_orders/
# get_trades; Robinhood splits everything by equity vs option.
_TOOLS_NEEDING_ACCOUNT = frozenset(
    {
        # Portfolio / P&L (required since MCP schema v15)
        "get_portfolio",
        "get_realized_pnl",
        "get_pnl_trade_history",
        # Equity positions / orders
        "get_equity_positions",
        "get_equity_orders",
        "place_equity_order",
        "review_equity_order",
        "cancel_equity_order",
        # Option positions / orders
        "get_option_positions",
        "get_option_orders",
        "place_option_order",
        "review_option_order",
        "cancel_option_order",
    }
)

# Values agents sometimes pass after reading redacted get_accounts responses.
_REDACTED_ACCOUNT_PLACEHOLDERS = frozenset(
    {
        "robinhood agentic",
        "agentic",
        "redacted",
        "[redacted]",
        "••••",
        "****",
    }
)

_TIME_IN_FORCE_ALIASES = {
    "day": "gfd",
    "Day": "gfd",
    "DAY": "gfd",
    "good for day": "gfd",
    "gtc": "gtc",
    "opg": "opg",
    "ioc": "ioc",
}

# Robinhood MCP market_hours — agents often guess wrong (24_hour, alldayhours).
_MARKET_HOURS_ALIASES = {
    "regular": "regular_hours",
    "regular_hours": "regular_hours",
    "extended": "extended_hours",
    "extended_hours": "extended_hours",
    "all_day_hours": "all_day_hours",
    "alldayhours": "all_day_hours",
    "all_day": "all_day_hours",
    "24_hour": "all_day_hours",
    "24-hour": "all_day_hours",
    "24hour": "all_day_hours",
    "overnight": "all_day_hours",
}


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def parse_tool_call(data: dict[str, Any]) -> tuple[Optional[str], dict[str, Any]]:
    """Return (tool_name, arguments) from an MCP tools/call JSON-RPC body."""
    if data.get("method") != "tools/call":
        return None, {}
    params = data.get("params")
    if not isinstance(params, dict):
        return None, {}
    name = params.get("name")
    if not isinstance(name, str):
        return None, {}
    return name, _parse_arguments(params.get("arguments"))


def normalize_order_arguments(args: dict[str, Any]) -> dict[str, Any]:
    """Map common agent mistakes (e.g. time_in_force 'day') before upstream."""
    out = dict(args)
    tif = out.get("time_in_force")
    if isinstance(tif, str) and tif in _TIME_IN_FORCE_ALIASES:
        out["time_in_force"] = _TIME_IN_FORCE_ALIASES[tif]
    mh = out.get("market_hours")
    if isinstance(mh, str):
        key = mh.strip().lower().replace(" ", "_")
        if key in _MARKET_HOURS_ALIASES:
            out["market_hours"] = _MARKET_HOURS_ALIASES[key]
    return out


def extract_account_number(data: Any) -> Optional[str]:
    """Pull the first account_number from an upstream MCP JSON-RPC response."""
    if isinstance(data, dict):
        if data.get("account_number"):
            return str(data["account_number"])
        for value in data.values():
            found = extract_account_number(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = extract_account_number(item)
            if found:
                return found
    return None


def is_usable_account_number(value: Any) -> bool:
    """True if value looks like a real Robinhood account number (not a redaction label)."""
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    if not cleaned:
        return False
    lower = cleaned.lower()
    if lower in _REDACTED_ACCOUNT_PLACEHOLDERS:
        return False
    if "robinhood" in lower and "agentic" in lower:
        return False
    if re.fullmatch(r"[•*xX]+", cleaned):
        return False
    # Real RH account numbers are numeric (often 9–12 digits).
    if re.fullmatch(r"\d{6,20}", cleaned):
        return True
    # Allow alphanumeric account ids if Robinhood ever returns them — reject labels.
    if re.search(r"[a-zA-Z]", cleaned) and not re.search(r"\d", cleaned):
        return False
    return bool(re.search(r"\d", cleaned))


async def lookup_agentic_account_number(
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> Optional[str]:
    """Resolve Agentic account_number via upstream MCP (never returned to the agent).

    Prefer get_accounts — get_portfolio/positions now require account_number upstream,
    so they cannot be used for discovery. Cached briefly per-token since this adds an
    extra upstream round-trip on every account-scoped call otherwise.
    """
    cache_key = _cache_key(headers)
    if cache_key:
        cached = _account_cache.get(cache_key)
        if cached and cached[1] > time.monotonic():
            return cached[0]

    for tool in ("get_accounts",):
        payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "tools/call",
            "params": {"name": tool, "arguments": {}},
        }
        try:
            res = await client.post(ROBINHOOD_MCP_URL, json=payload, headers=headers)
            if res.status_code >= 400:
                continue
            body = res.json()
        except (httpx.RequestError, json.JSONDecodeError, ValueError):
            continue
        account = extract_account_number(body)
        if account and is_usable_account_number(account):
            if cache_key:
                _account_cache[cache_key] = (account, time.monotonic() + _ACCOUNT_CACHE_TTL_S)
            return account
    return None


def apply_tool_arguments(data: dict[str, Any], args: dict[str, Any]) -> None:
    params = data.get("params")
    if isinstance(params, dict):
        params["arguments"] = args


async def enrich_mcp_request(
    body: bytes,
    headers: dict[str, str],
    *,
    client: httpx.AsyncClient,
) -> bytes:
    """Inject account_number and normalize order args on tools/call requests."""
    if not body:
        return body
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body
    if not isinstance(data, dict):
        return body

    tool_name, args = parse_tool_call(data)
    if not tool_name:
        return body

    changed = False
    if tool_name in _TOOLS_NEEDING_ACCOUNT:
        args = normalize_order_arguments(args)
        changed = True
        existing = args.get("account_number")
        if not is_usable_account_number(existing):
            account = await lookup_agentic_account_number(client, headers)
            if account:
                args["account_number"] = account
                logger.info("Injected account_number for MCP tool %s", tool_name)
            else:
                logger.warning("Could not resolve account_number for %s", tool_name)

    if changed:
        apply_tool_arguments(data, args)
        return json.dumps(data, separators=(",", ":")).encode()
    return body
