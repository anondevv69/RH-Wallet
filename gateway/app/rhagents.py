"""Post confirmed Robinhood fills to rhagents.bot."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from app.rh_client import RobinhoodClient, RHCredentials

logger = logging.getLogger(__name__)

RHAGENTS_DEFAULT_BASE = "https://rhagentsite-production.up.railway.app"
FILLED_STATES = {"filled", "confirmed", "executed"}
POLL_INTERVAL_SEC = 15
POLL_MAX_ATTEMPTS = 20  # ~5 minutes


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def post_trade_to_rhagents(
    *,
    agent_key: str,
    base_url: str,
    product: str,
    symbol: str,
    side: str,
    quantity: str,
    price_usd: str,
) -> bool:
    url = f"{base_url.rstrip('/')}/api/agent/trade-post"
    payload = {
        "product": product,
        "type": "trade_fill",
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price_usd": price_usd,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {agent_key}"},
            )
        if res.status_code >= 400:
            logger.warning(
                "rhagents trade-post failed (%s): %s",
                res.status_code,
                res.text[:300],
            )
            return False
        data = res.json()
        logger.info("rhagents trade-post ok: %s", data.get("post_id"))
        return True
    except Exception:
        logger.exception("rhagents trade-post error")
        return False


def _extract_fill(order: dict[str, Any]) -> Optional[tuple[str, str]]:
    quantity = _as_str(order.get("filled_asset_quantity"))
    price = _as_str(order.get("average_price"))
    if not quantity or not price:
        return None
    return quantity, price


def poll_and_post_rhagents_trade(
    *,
    credentials: RHCredentials,
    order_id: str,
    agent_key: str,
    base_url: str,
    symbol: str,
    side: str,
    product: str = "crypto",
) -> None:
    """Background task: poll order until filled, then post to rhagents."""
    client = RobinhoodClient(credentials)
    try:
        for attempt in range(POLL_MAX_ATTEMPTS):
            try:
                raw = client.get_order(order_id)
                order = client.normalize_order(raw)
            except Exception:
                logger.exception("rhagents poll: failed to fetch order %s", order_id)
                time.sleep(POLL_INTERVAL_SEC)
                continue

            state = (_as_str(order.get("state")) or "").lower()
            if state in FILLED_STATES:
                fill = _extract_fill(order)
                if not fill:
                    logger.warning("rhagents poll: order %s filled but missing qty/price", order_id)
                    return
                quantity, price_usd = fill
                post_trade_to_rhagents(
                    agent_key=agent_key,
                    base_url=base_url,
                    product=product,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price_usd=price_usd,
                )
                return

            if state in {"canceled", "cancelled", "rejected", "failed"}:
                logger.info("rhagents poll: order %s ended in state=%s — skip post", order_id, state)
                return

            if attempt == 0:
                logger.info("rhagents poll: waiting for fill on order %s (state=%s)", order_id, state)
            time.sleep(POLL_INTERVAL_SEC)

        logger.warning("rhagents poll: timed out waiting for fill on order %s", order_id)
    finally:
        client.close()
