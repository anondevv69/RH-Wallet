"""API-level tests for auth and order guards (mocked Robinhood client)."""

from __future__ import annotations

from typing import Any, Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.deps import get_client
from app.main import app
from app.rh_client import RobinhoodAPIError, reset_rh_client


GATEWAY_KEY = "test-gateway-key-please-change"


def _settings(**overrides: Any) -> Settings:
    base = {
        "RH_API_KEY": "rh-api-test",
        "RH_PRIVATE_KEY_BASE64": "xQnTJVeQLmw1/Mg2YimEViSpw/SdJcgNXZ5kQkAXNPU=",
        "RH_WALLET_API_KEY": GATEWAY_KEY,
        "MAX_ORDER_USD": "50",
        "REQUIRE_CONFIRMATION": "true",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.get_account_summary.return_value = {
        "account_number": "ACC1",
        "status": "active",
        "buying_power": "100.00",
    }
    client.get_holdings.return_value = {"results": []}
    client.get_best_bid_ask.return_value = {"results": [{"symbol": "BTC-USD"}]}
    client.get_estimated_price.return_value = {
        "results": [{"price": "50000", "total_amount": "50"}]
    }
    client.place_market_order.return_value = {
        "id": "ord-1",
        "symbol": "BTC-USD",
        "side": "buy",
        "state": "open",
        "type": "market",
    }
    client.normalize_order.side_effect = lambda raw: {
        "id": raw.get("id"),
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "state": raw.get("state"),
        "type": raw.get("type"),
        "raw": raw,
    }
    client.cancel_order.return_value = {"id": "ord-1", "state": "canceled"}
    return client


@pytest.fixture
def client(mock_client: MagicMock):
    settings = _settings()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_client] = lambda: mock_client
    reset_rh_client()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    reset_rh_client()


def test_health_no_auth(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_account_requires_bearer(client: TestClient):
    response = client.get("/v1/account")
    assert response.status_code == 401


def test_account_rejects_bad_token(client: TestClient):
    response = client.get(
        "/v1/account", headers={"Authorization": "Bearer wrong"}
    )
    assert response.status_code == 401


def test_account_ok(client: TestClient, mock_client: MagicMock):
    response = client.get(
        "/v1/account", headers={"Authorization": f"Bearer {GATEWAY_KEY}"}
    )
    assert response.status_code == 200
    assert response.json()["account_number"] == "ACC1"
    mock_client.get_account_summary.assert_called_once()


def test_place_order_requires_confirm(client: TestClient):
    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
        json={
            "side": "buy",
            "symbol": "BTC-USD",
            "quote_amount": "10.00",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "confirmation_required"


def test_place_order_rejects_over_max(client: TestClient, mock_client: MagicMock):
    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
        json={
            "side": "buy",
            "symbol": "BTC-USD",
            "quote_amount": "100.00",
            "confirm": True,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "order_too_large"
    mock_client.place_market_order.assert_not_called()


def test_place_order_success(client: TestClient, mock_client: MagicMock):
    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
        json={
            "side": "buy",
            "symbol": "btc-usd",
            "quote_amount": "10.00",
            "confirm": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "ord-1"
    mock_client.place_market_order.assert_called_once()
    kwargs = mock_client.place_market_order.call_args.kwargs
    assert kwargs["symbol"] == "BTC-USD"
    assert kwargs["quote_amount"] == "10.00"


def test_prices(client: TestClient):
    response = client.get(
        "/v1/prices",
        params=[("symbol", "BTC-USD")],
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
    )
    assert response.status_code == 200
