"""FastAPI entrypoint for the RH Wallet Gateway."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.database import init_db
from app.routes import account, connect, market, orders

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    init_db()
    logger.info(
        "RH Wallet Gateway v%s starting (multi_tenant=%s, max_order_usd=%s)",
        __version__,
        settings.is_multi_tenant(),
        settings.max_order_usd,
    )
    if settings.is_multi_tenant():
        logger.info("Multi-tenant connect enabled at /connect")
    elif not settings.has_rh_credentials():
        logger.warning("No RH credentials — use /connect or set legacy env vars")
    yield


app = FastAPI(
    title="RH Wallet Gateway",
    description=(
        "Robinhood Crypto Trading API gateway for Bankr agents. "
        "US customers only. Subject to Robinhood Crypto Customer Agreement."
    ),
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connect.router)
app.include_router(account.router)
app.include_router(market.router)
app.include_router(orders.router)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "multi_tenant": settings.is_multi_tenant(),
        "rh_credentials_configured": settings.has_rh_credentials(),
        "gateway_auth_configured": settings.has_gateway_auth() or settings.is_multi_tenant(),
        "public_base_url": settings.public_base_url or None,
        "max_order_usd": settings.max_order_usd,
        "require_confirmation": settings.require_confirmation,
        "connect_url": (
            f"{settings.public_base_url.rstrip('/')}/connect"
            if settings.public_base_url
            else "/connect"
        ),
        "disclaimer": (
            "Robinhood Crypto Trading API is available to US customers only "
            "and is subject to the Robinhood Crypto Customer Agreement."
        ),
    }
