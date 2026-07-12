"""Public symbol catalog — validate Robinhood Crypto + Agentic tradables."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.rh_client import RHCredentials, RobinhoodClient, RobinhoodAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])

ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"

STATIC_CRYPTO_PAIRS = [
    "BTC-USD",
    "ETH-USD",
    "DOGE-USD",
    "SHIB-USD",
    "PEPE-USD",
    "SOL-USD",
    "ADA-USD",
    "XRP-USD",
    "AVAX-USD",
    "LINK-USD",
    "LTC-USD",
    "BCH-USD",
    "ETC-USD",
    "XLM-USD",
    "XTZ-USD",
    "UNI-USD",
    "AAVE-USD",
    "COMP-USD",
    "MATIC-USD",
    "DOT-USD",
    "NEAR-USD",
    "APT-USD",
    "ARB-USD",
    "OP-USD",
    "BONK-USD",
    "WIF-USD",
    "FLOKI-USD",
]

_CACHE: dict[str, Any] = {"fetched_at": 0.0, "pairs": set(STATIC_CRYPTO_PAIRS), "bases": set(), "source": "static"}
_AGENTIC_OK: dict[str, float] = {}
_AGENTIC_NO: dict[str, float] = {}
_TTL_SECONDS = 3600
_LOOKUP_TTL = 86400


def _bases_from_pairs(pairs: set[str]) -> set[str]:
    bases: set[str] = set()
    for pair in pairs:
        upper = pair.upper()
        if upper.endswith("-USD"):
            bases.add(upper[:-4])
        else:
            bases.add(upper)
    return bases


def _refresh_crypto_cache() -> None:
    global _CACHE
    pairs = set(STATIC_CRYPTO_PAIRS)
    source = "static"
    settings = get_settings()

    if settings.has_rh_credentials():
        try:
            client = RobinhoodClient(
                RHCredentials(
                    api_key=settings.rh_api_key,
                    private_key_base64=settings.rh_private_key_base64,
                    base_url=settings.rh_base_url,
                )
            )
            raw = client.get_trading_pairs()
            live = {
                str(row.get("symbol", "")).upper()
                for row in raw
                if isinstance(row, dict) and row.get("symbol")
            }
            if live:
                pairs = live
                source = "robinhood"
        except (RobinhoodAPIError, ValueError) as exc:
            logger.warning("crypto catalog refresh failed: %s", exc)

    _CACHE = {
        "fetched_at": time.time(),
        "pairs": pairs,
        "bases": _bases_from_pairs(pairs),
        "source": source,
    }


def _ensure_crypto_cache() -> None:
    if time.time() - float(_CACHE.get("fetched_at", 0)) > _TTL_SECONDS:
        _refresh_crypto_cache()


def _normalize_crypto(raw: str) -> Optional[str]:
    _ensure_crypto_cache()
    pairs: set[str] = _CACHE["pairs"]
    sym = raw.strip().upper()
    if not sym:
        return None

    if sym.endswith("-USD"):
        return sym if sym in pairs else None

    pair = f"{sym}-USD"
    if pair in pairs:
        return pair
    return None


def _walk_text(node: Any) -> str:
    chunks: list[str] = []

    def walk(v: Any) -> None:
        if v is None:
            return
        if isinstance(v, str):
            chunks.append(v)
            return
        if isinstance(v, dict):
            for val in v.values():
                walk(val)
            return
        if isinstance(v, list):
            for item in v:
                walk(item)

    walk(node)
    return "\n".join(chunks)


def _equity_quote_valid(payload: Any, symbol: str) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("error"):
        return False
    result = payload.get("result")
    if isinstance(result, dict) and result.get("isError"):
        return False

    text = _walk_text(payload).upper()
    sym = symbol.upper()
    if sym not in text:
        return False

    bad = (
        "NOT FOUND",
        "INVALID SYMBOL",
        "UNKNOWN SYMBOL",
        "NO QUOTE",
        "UNRECOGNIZED",
        "COULD NOT FIND",
        "DOES NOT EXIST",
    )
    if any(b in text for b in bad):
        return False

    # Expect some market-ish signal alongside the symbol
    if re.search(r"\$?\d+\.?\d*", text):
        return True
    if any(k in text for k in ("LAST", "PRICE", "QUOTE", "BID", "ASK", "CLOSE")):
        return True
    return False


async def _validate_agentic_symbol(symbol: str) -> bool:
    sym = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z]{1,5}", sym):
        return False

    now = time.time()
    if sym in _AGENTIC_OK and now - _AGENTIC_OK[sym] < _LOOKUP_TTL:
        return True
    if sym in _AGENTIC_NO and now - _AGENTIC_NO[sym] < _LOOKUP_TTL:
        return False

    token = get_settings().agentic_catalog_token.strip()
    if not token:
        logger.warning("AGENTIC_CATALOG_TOKEN unset — cannot validate agentic symbol %s", sym)
        return False

    payload = {
        "jsonrpc": "2.0",
        "id": int(now),
        "method": "tools/call",
        "params": {
            "name": "get_equity_quotes",
            "arguments": {"symbols": [sym]},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                ROBINHOOD_MCP_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        body = res.json()
        ok = res.status_code < 400 and _equity_quote_valid(body, sym)
    except Exception as exc:
        logger.warning("agentic quote check failed for %s: %s", sym, exc)
        return False

    if ok:
        _AGENTIC_OK[sym] = now
        _AGENTIC_NO.pop(sym, None)
    else:
        _AGENTIC_NO[sym] = now
    return ok


async def resolve_tradable_symbol(raw: str) -> Optional[dict[str, str]]:
    sym = raw.strip().upper()
    if not sym:
        return None

    crypto = _normalize_crypto(sym)
    if crypto:
        return {"product": "crypto", "symbol": crypto}

    ticker = sym[:-4] if sym.endswith("-USD") else sym
    if not re.fullmatch(r"[A-Z]{1,5}", ticker):
        return None

    if await _validate_agentic_symbol(ticker):
        return {"product": "agentic", "symbol": ticker}
    return None


@router.get("/symbols")
def catalog_symbols() -> dict:
    """Tradable crypto pairs from Robinhood API (cached). Agentic uses /resolve per symbol."""
    _ensure_crypto_cache()
    pairs = sorted(_CACHE["pairs"])
    bases = sorted(_CACHE.get("bases") or _bases_from_pairs(set(pairs)))
    return {
        "ok": True,
        "source": _CACHE.get("source", "static"),
        "crypto": {"pairs": pairs, "bases": bases},
        "agentic_note": (
            "Agentic channels open on first post when Robinhood validates the stock "
            "(GET /v1/catalog/resolve with AGENTIC_CATALOG_TOKEN)."
        ),
    }


@router.get("/resolve")
async def catalog_resolve(symbol: str = Query(..., min_length=1, max_length=16)) -> dict:
    """Return product + canonical symbol if tradable on Robinhood; 404 if not."""
    resolved = await resolve_tradable_symbol(symbol)
    if not resolved:
        raise HTTPException(
            status_code=404,
            detail={
                "ok": False,
                "error": "not_tradable",
                "message": f"{symbol.upper()} is not a tradable Robinhood Crypto or Agentic symbol",
            },
        )
    return {"ok": True, "input": symbol.upper(), **resolved}
