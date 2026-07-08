"""Authentication context for legacy and multi-tenant modes."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.tenant_service import TenantCredentials, lookup_tenant_credentials

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    rh_api_key: str
    rh_private_key_base64: str
    max_order_usd: float
    tenant_id: Optional[str] = None
    mode: str = "legacy"


async def get_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolve Bearer token to Robinhood credentials (tenant DB or legacy env)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if settings.is_multi_tenant():
        tenant = lookup_tenant_credentials(db, settings, token)
        if tenant is not None:
            max_usd = tenant.max_order_usd if tenant.max_order_usd is not None else settings.max_order_usd
            return AuthContext(
                rh_api_key=tenant.rh_api_key,
                rh_private_key_base64=tenant.rh_private_key_base64,
                max_order_usd=max_usd,
                tenant_id=tenant.tenant_id,
                mode="tenant",
            )

    if settings.has_gateway_auth() and secrets.compare_digest(token, settings.rh_wallet_api_key):
        if not settings.has_rh_credentials():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Legacy gateway mode requires RH_API_KEY and RH_PRIVATE_KEY_BASE64."
                ),
            )
        return AuthContext(
            rh_api_key=settings.rh_api_key,
            rh_private_key_base64=settings.rh_private_key_base64,
            max_order_usd=settings.max_order_usd,
            mode="legacy",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )
