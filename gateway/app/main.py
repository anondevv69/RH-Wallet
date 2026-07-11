"""FastAPI entrypoint for the RH Wallet Gateway."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.database import init_db
from app.routes import account, agentic, connect, market, orders, setup

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    if settings.enable_connect_storage:
        init_db()
        logger.warning("ENABLE_CONNECT_STORAGE=true — gateway will store user RH keys")
    logger.info(
        "RH Wallet Gateway v%s (stateless default, connect_storage=%s)",
        __version__,
        settings.enable_connect_storage,
    )
    yield


app = FastAPI(
    title="RH Wallet Gateway",
    description=(
        "Stateless Robinhood Crypto signing proxy for Bankr agents. "
        "RH keys stay in Bankr env — not stored on this server by default. "
        "US customers only."
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

app.include_router(setup.router)
app.include_router(connect.router)
app.include_router(account.router)
app.include_router(market.router)
app.include_router(orders.router)
app.include_router(agentic.router)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "mode": "stateless",
        "connect_storage_enabled": settings.enable_connect_storage,
        "requires_gateway_secret": settings.has_gateway_shared_secret(),
        "public_base_url": settings.public_base_url or None,
        "max_order_usd": settings.max_order_usd,
        "require_confirmation": settings.require_confirmation,
        "bankr_env_vars": [
            "RH_WALLET_API_URL",
            "RH_API_KEY",
            "RH_PRIVATE_KEY_BASE64",
            "RH_GATEWAY_SECRET",
            "RH_MAX_ORDER_USD",
            "RH_REQUIRE_CONFIRMATION",
        ],
        "disclaimer": (
            "Robinhood Crypto Trading API is available to US customers only "
            "and is subject to the Robinhood Crypto Customer Agreement."
        ),
    }
