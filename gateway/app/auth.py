"""Authentication — stateless (Bankr env) preferred; legacy/tenant optional."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.tenant_service import lookup_tenant_credentials

_bearer = HTTPBearer(auto_error=False)

RH_API_KEY_HEADER = "x-rh-api-key"
RH_PRIVATE_KEY_HEADER = "x-rh-private-key-base64"
GATEWAY_SECRET_HEADER = "x-gateway-secret"


@dataclass(frozen=True)
class AuthContext:
    rh_api_key: str
    rh_private_key_base64: str
    max_order_usd: float
    require_confirmation: bool
    tenant_id: Optional[str] = None
    mode: str = "stateless"


def _parse_user_max_order_usd(request: Request, gateway_ceiling: float) -> float:
    """Per-user cap from X-Max-Order-USD (Bankr env RH_MAX_ORDER_USD). Cannot exceed host ceiling."""
    raw = request.headers.get("x-max-order-usd", "").strip()
    if not raw:
        return gateway_ceiling
    try:
        user_cap = float(raw)
    except ValueError:
        return gateway_ceiling
    if user_cap <= 0:
        return gateway_ceiling
    return min(user_cap, gateway_ceiling)


def _parse_user_require_confirmation(
    request: Request, gateway_default: bool
) -> bool:
    """Per-user stricter confirm from X-Require-Confirmation (Bankr RH_REQUIRE_CONFIRMATION)."""
    raw = request.headers.get("x-require-confirmation", "").strip().lower()
    if raw in ("true", "1", "yes"):
        return True
    if raw in ("false", "0", "no"):
        return gateway_default
    return gateway_default


def _verify_gateway_secret(
    request: Request,
    settings: Settings,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> None:
    """Optional shared secret so a public signer cannot be abused as an open proxy."""
    if not settings.has_gateway_shared_secret():
        return

    token: Optional[str] = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    elif request.headers.get(GATEWAY_SECRET_HEADER):
        token = request.headers.get(GATEWAY_SECRET_HEADER)

    if not token or not secrets.compare_digest(token, settings.gateway_shared_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing gateway secret (RH_GATEWAY_SECRET).",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolve Robinhood credentials for this request.

    Priority:
    1. **Stateless** — ``X-RH-API-Key`` + ``X-RH-Private-Key-Base64`` (from Bankr env)
    2. **Tenant** — ``rhw_...`` Bearer (only if ``ENABLE_CONNECT_STORAGE=true``)
    3. **Legacy** — single ``RH_WALLET_API_KEY`` + gateway env RH keys
    """
    rh_api_key = request.headers.get(RH_API_KEY_HEADER, "").strip()
    rh_private_key = request.headers.get(RH_PRIVATE_KEY_HEADER, "").strip()

    if rh_api_key and rh_private_key:
        _verify_gateway_secret(request, settings, credentials)
        return AuthContext(
            rh_api_key=rh_api_key,
            rh_private_key_base64=rh_private_key,
            max_order_usd=_parse_user_max_order_usd(request, settings.max_order_usd),
            require_confirmation=_parse_user_require_confirmation(
                request, settings.require_confirmation
            ),
            mode="stateless",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Missing Robinhood credentials. Set RH_API_KEY and "
                "RH_PRIVATE_KEY_BASE64 in Bankr Agent tool environment, "
                "or send X-RH-API-Key and X-RH-Private-Key-Base64 headers."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if settings.enable_connect_storage and settings.is_multi_tenant():
        tenant = lookup_tenant_credentials(db, settings, token)
        if tenant is not None:
            max_usd = (
                tenant.max_order_usd
                if tenant.max_order_usd is not None
                else settings.max_order_usd
            )
            return AuthContext(
                rh_api_key=tenant.rh_api_key,
                rh_private_key_base64=tenant.rh_private_key_base64,
                max_order_usd=min(
                    max_usd,
                    _parse_user_max_order_usd(request, settings.max_order_usd),
                ),
                require_confirmation=_parse_user_require_confirmation(
                    request, settings.require_confirmation
                ),
                tenant_id=tenant.tenant_id,
                mode="tenant",
            )

    if settings.has_gateway_auth() and secrets.compare_digest(
        token, settings.rh_wallet_api_key
    ):
        if not settings.has_rh_credentials():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Legacy gateway mode requires RH_API_KEY and "
                    "RH_PRIVATE_KEY_BASE64 in gateway env."
                ),
            )
        return AuthContext(
            rh_api_key=settings.rh_api_key,
            rh_private_key_base64=settings.rh_private_key_base64,
            max_order_usd=_parse_user_max_order_usd(request, settings.max_order_usd),
            require_confirmation=_parse_user_require_confirmation(
                request, settings.require_confirmation
            ),
            mode="legacy",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )
