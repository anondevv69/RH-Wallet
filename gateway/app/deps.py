"""Shared FastAPI helpers."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings
from app.rh_client import RobinhoodAPIError, RobinhoodClient, get_rh_client


def get_client(settings: Settings = Depends(get_settings)) -> RobinhoodClient:
    if not settings.has_rh_credentials():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Robinhood credentials are not configured. "
                "Set RH_API_KEY and RH_PRIVATE_KEY_BASE64."
            ),
        )
    try:
        return get_rh_client(settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def raise_rh_error(exc: RobinhoodAPIError) -> None:
    code = exc.status_code or status.HTTP_502_BAD_GATEWAY
    # Don't leak unexpected 5xx codes as client errors
    if code < 400 or code > 599:
        code = status.HTTP_502_BAD_GATEWAY
    raise HTTPException(
        status_code=code,
        detail={
            "error": str(exc),
            "robinhood": exc.payload,
        },
    )


def estimate_order_usd(
    *,
    quote_amount: Optional[str],
    asset_quantity: Optional[str],
    side: str,
    symbol: str,
    client: RobinhoodClient,
) -> Optional[float]:
    """Best-effort USD notional for the max-order guard.

    Prefer quote_amount. For asset_quantity, use estimated ask (buy) or bid (sell).
    Returns None if USD cannot be determined.
    """
    if quote_amount is not None and str(quote_amount).strip() != "":
        return float(quote_amount)

    if asset_quantity is None:
        return None

    # Use estimated price to convert asset qty → USD
    book_side = "ask" if side.lower() == "buy" else "bid"
    try:
        estimate = client.get_estimated_price(symbol, book_side, str(asset_quantity))
    except RobinhoodAPIError:
        return None

    results = estimate.get("results") if isinstance(estimate, dict) else None
    if not results:
        return None

    first = results[0]
    # RH may return total_cost / price / estimated_price depending on version
    for key in ("total_amount", "total_cost", "price", "estimated_price"):
        value = first.get(key) if isinstance(first, dict) else None
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

    # Fallback: price * quantity
    price = first.get("price") if isinstance(first, dict) else None
    if price is not None:
        try:
            return float(price) * float(asset_quantity)
        except (TypeError, ValueError):
            return None
    return None
