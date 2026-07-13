"""Tests for response redaction."""

import json

from app.redact import redact_for_client, redact_mcp_response, redact_sensitive_text

_FAKE_ACCT = "123456789"
_FAKE_NICK = "user-nick"


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


def test_redact_removes_account_id_and_nickname():
    data = {
        "account_id": "uuid-123",
        "nickname": _FAKE_NICK,
        "account_nickname": _FAKE_NICK,
        "buying_power": "1.71",
    }
    out = redact_for_client(data)
    assert out == {"buying_power": "1.71"}


def test_redact_sensitive_text_full_number_and_slash_pair():
    text = f"your account ({_FAKE_ACCT} / {_FAKE_NICK}) doesn't have enough cash"
    out = redact_sensitive_text(text)
    assert _FAKE_ACCT not in out
    assert _FAKE_NICK not in out
    assert "Robinhood Agentic" in out


def test_redact_sensitive_text_masked_label():
    text = 'your "Agentic" account (••••6789) is the one i can trade through.'
    out = redact_sensitive_text(text)
    assert "6789" not in out
    assert "••••" not in out


def test_redact_mcp_response_json_rpc():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Robinhood Agentic portfolio:\n\n"
                        "Account value: $10.00\n"
                        f"your account ({_FAKE_ACCT} / {_FAKE_NICK}) — buying power: $1.71"
                    ),
                }
            ],
            "structuredContent": {
                "accounts": [
                    {"account_number": _FAKE_ACCT, "nickname": _FAKE_NICK}
                ],
                "buying_power": "1.71",
            },
        },
    }
    out = json.loads(
        redact_mcp_response(json.dumps(payload).encode(), "application/json")
    )
    text = out["result"]["content"][0]["text"]
    assert _FAKE_ACCT not in text
    assert _FAKE_NICK not in text
    accounts = out["result"]["structuredContent"]["accounts"]
    assert "account_number" not in accounts[0]
    assert "nickname" not in accounts[0]
    assert out["result"]["structuredContent"]["buying_power"] == "1.71"


def test_redact_mcp_response_invalid_json_passthrough():
    raw = b"not json"
    assert redact_mcp_response(raw, "application/json") == raw
