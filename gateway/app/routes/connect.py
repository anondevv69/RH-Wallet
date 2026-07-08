"""Connect flow — disabled by default (keys belong in Bankr env, not our DB)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.database import get_db
from app.models import ConnectRequest, ConnectResponse
from app.tenant_service import create_tenant, revoke_tenant_by_id

router = APIRouter()

DISABLED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>RH Wallet — Connect disabled</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 560px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    .note { background: #fef3c7; padding: 1rem; border-radius: 6px; }
    code { background: #f4f4f5; padding: 0.1rem 0.3rem; }
  </style>
</head>
<body>
  <h1>Key storage disabled</h1>
  <p class="note">This gateway does <strong>not</strong> store Robinhood keys. Add these to <strong>Bankr → Agent tool environment</strong> instead:</p>
  <ul>
    <li><code>RH_API_KEY</code></li>
    <li><code>RH_PRIVATE_KEY_BASE64</code></li>
    <li><code>RH_WALLET_API_URL</code> (this gateway URL)</li>
    <li><code>RH_GATEWAY_SECRET</code> (if the host enabled one)</li>
  </ul>
  <p>See <a href="https://github.com/anondevv69/RH-Wallet">RH-Wallet docs</a>.</p>
</body>
</html>"""


def _require_connect_enabled(settings: Settings) -> None:
    if not settings.enable_connect_storage:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=(
                "Connect storage is disabled. Put RH_API_KEY and "
                "RH_PRIVATE_KEY_BASE64 in Bankr Agent tool environment instead."
            ),
        )
    if not settings.is_multi_tenant():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Connect storage requires MASTER_ENCRYPTION_KEY and DATABASE_URL.",
        )


@router.get("/connect", response_class=HTMLResponse)
def connect_page(settings: Settings = Depends(get_settings)) -> str:
    if not settings.enable_connect_storage:
        return DISABLED_HTML
    return DISABLED_HTML  # replaced below if enabled — keep single import path


@router.post("/v1/connect", response_model=ConnectResponse, status_code=status.HTTP_201_CREATED)
def connect_robinhood(
    payload: ConnectRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> ConnectResponse:
    _require_connect_enabled(settings)
    public_url = settings.effective_public_url(str(request.base_url).rstrip("/"))
    result = create_tenant(
        db,
        settings,
        rh_api_key=payload.rh_api_key.strip(),
        rh_private_key_base64=payload.rh_private_key_base64.strip(),
        label=payload.label,
    )
    return ConnectResponse(
        tenant_id=result.tenant_id,
        rh_wallet_api_url=public_url,
        rh_wallet_api_key=result.rh_wallet_api_key,
        api_key_prefix=result.api_key_prefix,
    )


@router.delete("/v1/connect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_robinhood(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> None:
    _require_connect_enabled(get_settings())
    if not auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only tenant connect keys can be revoked here.",
        )
    if not revoke_tenant_by_id(db, auth.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
