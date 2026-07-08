"""Shared FastAPI helpers."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.rh_client import RobinhoodAPIError, RobinhoodClient, RHCredentials


def get_client(auth: AuthContext = Depends(get_auth_context)) -> RobinhoodClient:
    settings = get_settings()
    try:
        return RobinhoodClient(
            RHCredentials(
                api_key=auth.rh_api_key,
                private_key_base64=auth.rh_private_key_base64,
                base_url=settings.rh_base_url,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def get_auth_settings(
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> tuple[AuthContext, Settings]:
    return auth, settings


def raise_rh_error(exc: RobinhoodAPIError) -> None:
    code = exc.status_code or status.HTTP_502_BAD_GATEWAY
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
    if quote_amount is not None and str(quote_amount).strip() != "":
        return float(quote_amount)

    if asset_quantity is None:
        return None

    book_side = "ask" if side.lower() == "buy" else "bid"
    try:
        estimate = client.get_estimated_price(symbol, book_side, str(asset_quantity))
    except RobinhoodAPIError:
        return None

    results = estimate.get("results") if isinstance(estimate, dict) else None
    if not results:
        return None

    first = results[0]
    for key in ("total_amount", "total_cost", "price", "estimated_price"):
        value = first.get(key) if isinstance(first, dict) else None
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

    price = first.get("price") if isinstance(first, dict) else None
    if price is not None:
        try:
            return float(price) * float(asset_quantity)
        except (TypeError, ValueError):
            return None
    return None
