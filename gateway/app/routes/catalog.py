"""Public symbol catalog — Robinhood crypto pairs (+ static fallback)."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter

from app.config import get_settings
from app.rh_client import RHCredentials, RobinhoodClient, RobinhoodAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])

# Robinhood Crypto pairs commonly tradable via API (fallback if gateway has no RH keys)
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

_CACHE: dict[str, Any] = {"fetched_at": 0.0, "pairs": list(STATIC_CRYPTO_PAIRS), "source": "static"}
_TTL_SECONDS = 3600


def _bases_from_pairs(pairs: list[str]) -> list[str]:
    bases: set[str] = set()
    for pair in pairs:
        upper = pair.upper()
        if upper.endswith("-USD"):
            bases.add(upper[:-4])
        else:
            bases.add(upper)
    return sorted(bases)


def _refresh_cache() -> None:
    global _CACHE
    settings = get_settings()
    pairs = list(STATIC_CRYPTO_PAIRS)
    source = "static"

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
            live = sorted(
                {
                    str(row.get("symbol", "")).upper()
                    for row in raw
                    if isinstance(row, dict) and row.get("symbol")
                }
            )
            if live:
                pairs = live
                source = "robinhood"
        except (RobinhoodAPIError, ValueError) as exc:
            logger.warning("catalog refresh failed, using static fallback: %s", exc)

    _CACHE = {
        "fetched_at": time.time(),
        "pairs": pairs,
        "bases": _bases_from_pairs(pairs),
        "source": source,
    }


@router.get("/symbols")
def catalog_symbols() -> dict:
    """Tradable crypto pairs from Robinhood API (cached) — used by rhagents for product routing."""
    if time.time() - float(_CACHE.get("fetched_at", 0)) > _TTL_SECONDS:
        _refresh_cache()

    pairs = _CACHE["pairs"]
    bases = _CACHE.get("bases") or _bases_from_pairs(pairs)
    return {
        "ok": True,
        "source": _CACHE.get("source", "static"),
        "crypto": {
            "pairs": pairs,
            "bases": bases,
        },
        "agentic_note": "Agentic tickers are US equities (e.g. SPCX, AAPL). If not in crypto.bases, treat as agentic.",
    }
