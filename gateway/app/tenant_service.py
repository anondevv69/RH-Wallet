"""Tenant lifecycle: connect, lookup, revoke."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import Settings
from app.tenant_models import Tenant
from app.vault import decrypt_value, encrypt_value, hash_api_key


@dataclass(frozen=True)
class TenantCredentials:
    tenant_id: str
    rh_api_key: str
    rh_private_key_base64: str
    max_order_usd: Optional[float] = None


@dataclass(frozen=True)
class ConnectResult:
    tenant_id: str
    rh_wallet_api_key: str
    rh_wallet_api_url: str
    api_key_prefix: str


def create_tenant(
    db: Session,
    settings: Settings,
    *,
    rh_api_key: str,
    rh_private_key_base64: str,
    label: Optional[str] = None,
) -> ConnectResult:
    if not settings.has_master_key():
        raise ValueError("MASTER_ENCRYPTION_KEY is not configured on the gateway.")

    api_key = f"rhw_{secrets.token_urlsafe(32)}"
    tenant = Tenant(
        label=label,
        api_key_hash=hash_api_key(api_key),
        api_key_prefix=api_key[:12],
        rh_api_key_encrypted=encrypt_value(settings.master_encryption_key, rh_api_key),
        rh_private_key_encrypted=encrypt_value(
            settings.master_encryption_key, rh_private_key_base64
        ),
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return ConnectResult(
        tenant_id=tenant.id,
        rh_wallet_api_key=api_key,
        rh_wallet_api_url=settings.public_base_url.rstrip("/"),
        api_key_prefix=tenant.api_key_prefix,
    )


def lookup_tenant_credentials(
    db: Session, settings: Settings, bearer_token: str
) -> Optional[TenantCredentials]:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.api_key_hash == hash_api_key(bearer_token))
        .filter(Tenant.revoked_at.is_(None))
        .one_or_none()
    )
    if tenant is None:
        return None

    return TenantCredentials(
        tenant_id=tenant.id,
        rh_api_key=decrypt_value(settings.master_encryption_key, tenant.rh_api_key_encrypted),
        rh_private_key_base64=decrypt_value(
            settings.master_encryption_key, tenant.rh_private_key_encrypted
        ),
        max_order_usd=tenant.max_order_usd,
    )


def revoke_tenant(db: Session, bearer_token: str) -> bool:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.api_key_hash == hash_api_key(bearer_token))
        .filter(Tenant.revoked_at.is_(None))
        .one_or_none()
    )
    if tenant is None:
        return False
    tenant.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def revoke_tenant_by_id(db: Session, tenant_id: str) -> bool:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == tenant_id)
        .filter(Tenant.revoked_at.is_(None))
        .one_or_none()
    )
    if tenant is None:
        return False
    tenant.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True
