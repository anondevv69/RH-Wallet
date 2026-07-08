"""Market data routes."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_auth_context
from app.deps import get_client, raise_rh_error
from app.rh_client import RobinhoodAPIError, RobinhoodClient

router = APIRouter(prefix="/v1", dependencies=[Depends(get_auth_context)])


@router.get("/trading-pairs")
def get_trading_pairs(
    symbol: Optional[list[str]] = Query(default=None),
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """List tradable crypto pairs (paginated upstream, flattened)."""
    try:
        symbols = tuple(symbol) if symbol else ()
        results = client.get_trading_pairs(*symbols)
        return {"results": results, "count": len(results)}
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.get("/prices")
def get_prices(
    symbol: Optional[list[str]] = Query(default=None),
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """Best bid/ask for one or more symbols."""
    try:
        symbols = tuple(s.upper() for s in symbol) if symbol else ()
        return client.get_best_bid_ask(*symbols)
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.get("/estimate")
def get_estimate(
    symbol: str = Query(..., description="Trading pair, e.g. BTC-USD"),
    side: Literal["bid", "ask", "both"] = Query(...),
    quantity: str = Query(..., description="Comma-separated quantities"),
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """Estimated execution price for hypothetical order size(s)."""
    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="symbol is required",
        )
    try:
        return client.get_estimated_price(symbol, side, quantity)
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)
