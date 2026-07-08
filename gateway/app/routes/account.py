"""Account and holdings routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import get_auth_context
from app.deps import get_client, raise_rh_error
from app.rh_client import RobinhoodAPIError, RobinhoodClient
from app.redact import redact_for_client

router = APIRouter(prefix="/v1", dependencies=[Depends(get_auth_context)])


@router.get("/account")
def get_account(client: RobinhoodClient = Depends(get_client)) -> dict:
    """Return primary Robinhood crypto account summary."""
    try:
        return redact_for_client(client.get_account_summary())
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)


@router.get("/holdings")
def get_holdings(
    asset_code: Optional[list[str]] = Query(default=None),
    client: RobinhoodClient = Depends(get_client),
) -> dict:
    """Return crypto holdings for the primary account."""
    try:
        codes = tuple(asset_code) if asset_code else ()
        return redact_for_client(client.get_holdings(*codes))
    except RobinhoodAPIError as exc:
        raise_rh_error(exc)
