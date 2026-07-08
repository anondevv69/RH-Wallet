"""Order routes with safety guards."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.deps import estimate_order_usd, get_auth_settings, get_client, raise_rh_error
from app.models import PlaceOrderRequest
from app.rh_client import RobinhoodAPIError, RobinhoodClient

router = APIRouter(prefix="/v1", dependencies=[Depends(get_auth_context)])


@router.get("/orders")
def list_orders(
    symbol: Optional[str] = Query(default=None),
    side: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None, alias="type"),
    created_at_start: Optional[str] = Query(default=None),
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """List orders for the primary crypto account."""
    try:
        return client.get_orders(
            created_at_start=created_at_start,
            symbol=symbol,
            side=side,
            state=state,
            order_type=type,
        )
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.get("/orders/{order_id}")
def get_order(
    order_id: str,
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """Fetch a single order by id."""
    try:
        raw = client.get_order(order_id)
        return client.normalize_order(raw)
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def place_order(
    payload: PlaceOrderRequest,
    client: RobinhoodClient = Depends(get_client),
    auth_settings: tuple[AuthContext, Settings] = Depends(get_auth_settings),
) -> dict:
    auth, settings = auth_settings
    max_order_usd = auth.max_order_usd
    """Place a market order on Robinhood Crypto (v2).

    Safety:
    - When REQUIRE_CONFIRMATION=true, ``confirm`` must be true.
    - Orders above MAX_ORDER_USD are rejected.
    """
    if settings.require_confirmation and not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "confirmation_required",
                "message": (
                    "Set confirm=true after reviewing size/estimate. "
                    "Gateway has REQUIRE_CONFIRMATION enabled."
                ),
            },
        )

    usd = estimate_order_usd(
        quote_amount=payload.quote_amount,
        asset_quantity=payload.asset_quantity,
        side=payload.side,
        symbol=payload.symbol,
        client=client,
    )
    if usd is not None and usd > max_order_usd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "order_too_large",
                "message": (
                    f"Estimated order ${usd:.2f} exceeds MAX_ORDER_USD="
                    f"{max_order_usd}."
                ),
                "estimated_usd": usd,
                "max_order_usd": max_order_usd,
            },
        )

    try:
        raw = client.place_market_order(
            side=payload.side,
            symbol=payload.symbol,
            quote_amount=payload.quote_amount,
            asset_quantity=payload.asset_quantity,
            client_order_id=payload.client_order_id,
        )
        return client.normalize_order(raw)
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: str,
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """Cancel an open order."""
    try:
        raw = client.cancel_order(order_id)
        return client.normalize_order(raw)
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)
