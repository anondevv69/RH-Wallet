"""API-level tests for auth and order guards (mocked Robinhood client)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.database import init_db
from app.deps import get_client
from app.main import app


GATEWAY_KEY = "test-gateway-key-please-change"
MASTER_KEY = "test-master-encryption-key-change-me"
PRIVATE_KEY = "xQnTJVeQLmw1/Mg2YimEViSpw/SdJcgNXZ5kQkAXNPU="
RH_HEADERS = {
    "X-RH-API-Key": "rh-api-test",
    "X-RH-Private-Key-Base64": PRIVATE_KEY,
}


def _settings(**overrides: Any) -> Settings:
    base = {
        "RH_API_KEY": "rh-api-test",
        "RH_PRIVATE_KEY_BASE64": PRIVATE_KEY,
        "RH_WALLET_API_KEY": GATEWAY_KEY,
        "MAX_ORDER_USD": "50",
        "REQUIRE_CONFIRMATION": "true",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def _auth_context(**overrides: Any) -> AuthContext:
    data = {
        "rh_api_key": "rh-api-test",
        "rh_private_key_base64": PRIVATE_KEY,
        "max_order_usd": 50.0,
        "require_confirmation": True,
        "mode": "legacy",
    }
    data.update(overrides)
    return AuthContext(**data)


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
    auth = _auth_context()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_auth_context] = lambda: auth
    app.dependency_overrides[get_client] = lambda: mock_client
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_no_auth(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "stateless"


def test_account_requires_rh_headers(client: TestClient):
    app.dependency_overrides.pop(get_auth_context, None)
    response = client.get("/v1/account")
    assert response.status_code == 401
    app.dependency_overrides[get_auth_context] = lambda: _auth_context()


def test_stateless_account_ok(mock_client: MagicMock):
    app.dependency_overrides.pop(get_auth_context, None)
    settings = _settings(RH_WALLET_API_KEY="", RH_API_KEY="", RH_PRIVATE_KEY_BASE64="")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_client] = lambda: mock_client

    with TestClient(app) as c:
        response = c.get("/v1/account", headers=RH_HEADERS)
        assert response.status_code == 200
        assert response.json()["account_number"] == "ACC1"

    app.dependency_overrides.clear()


def test_stateless_requires_gateway_secret(mock_client: MagicMock):
    app.dependency_overrides.pop(get_auth_context, None)
    settings = _settings(
        GATEWAY_SHARED_SECRET="host-secret",
        RH_WALLET_API_KEY="",
        RH_API_KEY="",
        RH_PRIVATE_KEY_BASE64="",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_client] = lambda: mock_client

    with TestClient(app) as c:
        no_secret = c.get("/v1/account", headers=RH_HEADERS)
        assert no_secret.status_code == 401

        with_secret = c.get(
            "/v1/account",
            headers={**RH_HEADERS, "Authorization": "Bearer host-secret"},
        )
        assert with_secret.status_code == 200

    app.dependency_overrides.clear()


def test_account_ok_legacy_override(client: TestClient, mock_client: MagicMock):
    response = client.get(
        "/v1/account", headers={"Authorization": f"Bearer {GATEWAY_KEY}"}
    )
    assert response.status_code == 200
    mock_client.get_account_summary.assert_called_once()


def test_connect_disabled_by_default(client: TestClient):
    app.dependency_overrides[get_settings] = lambda: _settings()
    response = client.post(
        "/v1/connect",
        json={"rh_api_key": "rh-api-u", "rh_private_key_base64": PRIVATE_KEY},
    )
    assert response.status_code == 410


def test_connect_when_enabled(client: TestClient):
    settings = _settings(
        ENABLE_CONNECT_STORAGE="true",
        MASTER_ENCRYPTION_KEY=MASTER_KEY,
        PUBLIC_BASE_URL="https://gateway.example.com",
        RH_WALLET_API_KEY="",
        RH_API_KEY="",
        RH_PRIVATE_KEY_BASE64="",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_client, None)
    init_db()

    with TestClient(app) as c:
        response = c.post(
            "/v1/connect",
            json={
                "rh_api_key": "rh-api-user-test",
                "rh_private_key_base64": PRIVATE_KEY,
            },
        )
        assert response.status_code == 201
        assert response.json()["rh_wallet_api_key"].startswith("rhw_")


def test_user_max_order_header_stricter_than_gateway(mock_client: MagicMock):
    app.dependency_overrides.pop(get_auth_context, None)
    settings = _settings(
        MAX_ORDER_USD="100",
        RH_WALLET_API_KEY="",
        RH_API_KEY="",
        RH_PRIVATE_KEY_BASE64="",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_client] = lambda: mock_client

    headers = {**RH_HEADERS, "X-Max-Order-USD": "25"}

    with TestClient(app) as c:
        ok = c.post(
            "/v1/orders",
            headers=headers,
            json={
                "side": "buy",
                "symbol": "BTC-USD",
                "quote_amount": "30.00",
                "confirm": True,
            },
        )
        assert ok.status_code == 400
        assert ok.json()["detail"]["error"] == "order_too_large"

        small = c.post(
            "/v1/orders",
            headers=headers,
            json={
                "side": "buy",
                "symbol": "BTC-USD",
                "quote_amount": "10.00",
                "confirm": True,
            },
        )
        assert small.status_code == 201

    app.dependency_overrides.clear()


def test_place_order_requires_confirm(client: TestClient):
    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
        json={"side": "buy", "symbol": "BTC-USD", "quote_amount": "10.00"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "confirmation_required"
