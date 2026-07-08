"""Connect flow for universal multi-tenant hosting."""

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

CONNECT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Connect Robinhood Crypto — RH Wallet</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 560px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.4rem; }
    label { display: block; margin-top: 1rem; font-weight: 600; }
    input, textarea { width: 100%; box-sizing: border-box; margin-top: 0.25rem; padding: 0.5rem; }
    button { margin-top: 1.25rem; padding: 0.6rem 1rem; font-size: 1rem; cursor: pointer; }
    .note { background: #f4f4f5; padding: 0.75rem; border-radius: 6px; font-size: 0.9rem; }
    .ok { background: #ecfdf5; border: 1px solid #10b981; padding: 1rem; border-radius: 6px; }
    code { word-break: break-all; }
  </style>
</head>
<body>
  <h1>Connect Robinhood Crypto</h1>
  <p class="note">US customers only. Your private key is encrypted at rest on this gateway. Never paste keys into Bankr chat — only here.</p>
  <form id="connect-form">
    <label>Label (optional)<input name="label" placeholder="My Bankr agent" /></label>
    <label>RH API Key<input name="rh_api_key" required placeholder="rh-api-..." /></label>
    <label>Private Key (Base64)<textarea name="rh_private_key_base64" required rows="3" placeholder="from generate_rh_keypair.py"></textarea></label>
    <button type="submit">Connect</button>
  </form>
  <div id="result"></div>
  <script>
    document.getElementById('connect-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = Object.fromEntries(fd.entries());
      const res = await fetch('/v1/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      const el = document.getElementById('result');
      if (!res.ok) {
        el.innerHTML = '<p style="color:#b91c1c">' + (data.detail || JSON.stringify(data)) + '</p>';
        return;
      }
      el.innerHTML = '<div class="ok"><p><strong>Connected.</strong> Copy these into Bankr → Agent tool environment:</p>'
        + '<p><strong>RH_WALLET_API_URL</strong><br><code>' + data.rh_wallet_api_url + '</code></p>'
        + '<p><strong>RH_WALLET_API_KEY</strong><br><code>' + data.rh_wallet_api_key + '</code></p>'
        + '<p>' + data.message + '</p></div>';
      e.target.reset();
    });
  </script>
</body>
</html>"""


@router.get("/connect", response_class=HTMLResponse)
def connect_page() -> str:
    """Simple browser UI for non-coders to link Robinhood credentials."""
    return CONNECT_HTML


@router.post("/v1/connect", response_model=ConnectResponse, status_code=status.HTTP_201_CREATED)
def connect_robinhood(
    payload: ConnectRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> ConnectResponse:
    """Register a user's Robinhood credentials and issue a personal gateway API key."""
    if not settings.is_multi_tenant():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Multi-tenant connect is not enabled. Set MASTER_ENCRYPTION_KEY on the gateway."
            ),
        )

    public_url = settings.effective_public_url(str(request.base_url).rstrip("/"))

    try:
        result = create_tenant(
            db,
            settings,
            rh_api_key=payload.rh_api_key.strip(),
            rh_private_key_base64=payload.rh_private_key_base64.strip(),
            label=payload.label,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

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
    """Revoke the current tenant connection (tenant API keys only)."""
    if not auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only per-user connect keys can be revoked. Legacy env keys are not revocable here.",
        )
    if not revoke_tenant_by_id(db, auth.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
