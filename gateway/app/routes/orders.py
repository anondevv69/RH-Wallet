"""Order routes with safety guards."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.deps import estimate_order_usd, get_auth_settings, get_client, raise_rh_error
from app.models import PlaceOrderRequest
from app.rh_client import RobinhoodAPIError, RobinhoodClient, RHCredentials
from app.rhagents import RHAGENTS_DEFAULT_BASE, poll_and_post_rhagents_trade
from app.redact import redact_for_client

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
        return redact_for_client(
            client.get_orders(
            created_at_start=created_at_start,
            symbol=symbol,
            side=side,
            state=state,
            order_type=type,
            )
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
        return redact_for_client(client.normalize_order(raw))
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def place_order(
    payload: PlaceOrderRequest,
    background_tasks: BackgroundTasks,
    client: RobinhoodClient = Depends(get_client),
    auth_settings: tuple[AuthContext, Settings] = Depends(get_auth_settings),
    rhagents_agent_key: Optional[str] = Header(default=None, alias="X-RHAGENTS-Agent-Key"),
    rhagents_base_url: Optional[str] = Header(default=None, alias="X-RHAGENTS-Base-Url"),
    rhagents_comment: Optional[str] = Header(default=None, alias="X-RHAGENTS-Comment"),
    rhagents_thesis: Optional[str] = Header(default=None, alias="X-RHAGENTS-Thesis"),
) -> dict:
    auth, settings = auth_settings
    max_order_usd = auth.max_order_usd
    """Place a market order on Robinhood Crypto (v2).

    Safety:
    - When confirmation is required, ``confirm`` must be true.
    - Orders above effective MAX_ORDER_USD are rejected.
    """
    if auth.require_confirmation and not payload.confirm:
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
        normalized = client.normalize_order(raw)
        result = redact_for_client(normalized)

        if rhagents_agent_key and normalized.get("id"):
            comment = (payload.rhagents_comment or rhagents_thesis or rhagents_comment or "").strip() or None
            background_tasks.add_task(
                poll_and_post_rhagents_trade,
                credentials=RHCredentials(
                    api_key=auth.rh_api_key,
                    private_key_base64=auth.rh_private_key_base64,
                    base_url=settings.rh_base_url,
                ),
                order_id=str(normalized["id"]),
                agent_key=rhagents_agent_key.strip(),
                base_url=(rhagents_base_url or RHAGENTS_DEFAULT_BASE).strip(),
                symbol=payload.symbol,
                side=payload.side,
                product="crypto",
                comment=comment,
            )
            result["rhagents_auto_post"] = True

        return result
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
        return redact_for_client(client.normalize_order(raw))
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)
