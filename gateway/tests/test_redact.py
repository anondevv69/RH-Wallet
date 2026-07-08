"""Tests for response redaction."""

from app.redact import redact_for_client


def test_redact_removes_account_number_top_level():
    data = {"account_number": "311040298697", "buying_power": "65.62"}
    assert redact_for_client(data) == {"buying_power": "65.62"}


def test_redact_removes_account_number_nested():
    data = {
        "accounts": [{"account_number": "ACC1", "status": "active"}],
        "results": [{"account_number": "ACC2", "symbol": "BTC-USD"}],
    }
    out = redact_for_client(data)
    assert "account_number" not in out["accounts"][0]
    assert out["accounts"][0]["status"] == "active"
    assert "account_number" not in out["results"][0]
