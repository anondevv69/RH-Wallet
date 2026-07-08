"""FastAPI entrypoint for the RH Wallet Gateway."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.rh_client import reset_rh_client
from app.routes import account, market, orders

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logger.info(
        "RH Wallet Gateway v%s starting (max_order_usd=%s, require_confirmation=%s)",
        __version__,
        settings.max_order_usd,
        settings.require_confirmation,
    )
    if not settings.has_rh_credentials():
        logger.warning("RH credentials not set — authenticated RH routes will 503")
    if not settings.has_gateway_auth():
        logger.warning("RH_WALLET_API_KEY not set — all /v1 routes will 503")
    yield
    reset_rh_client()


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

app.include_router(account.router)
app.include_router(market.router)
app.include_router(orders.router)


@app.get("/health")
def health() -> dict:
    """Liveness probe — no secrets, no Robinhood call."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "rh_credentials_configured": settings.has_rh_credentials(),
        "gateway_auth_configured": settings.has_gateway_auth(),
        "max_order_usd": settings.max_order_usd,
        "require_confirmation": settings.require_confirmation,
        "disclaimer": (
            "Robinhood Crypto Trading API is available to US customers only "
            "and is subject to the Robinhood Crypto Customer Agreement."
        ),
    }
