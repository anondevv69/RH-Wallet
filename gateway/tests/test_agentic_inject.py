"""Tests for Agentic MCP request enrichment."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from app.agentic_inject import (
    enrich_mcp_request,
    extract_account_number,
    normalize_order_arguments,
    parse_tool_call,
)


def test_parse_tool_call():
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "place_equity_order",
            "arguments": {
                "symbol": "GRAB",
                "side": "buy",
                "order_type": "market",
                "quantity": 1,
                "time_in_force": "day",
            },
        },
    }
    name, args = parse_tool_call(body)
    assert name == "place_equity_order"
    assert args["symbol"] == "GRAB"


def test_normalize_time_in_force_day_to_gfd():
    args = normalize_order_arguments({"time_in_force": "day"})
    assert args["time_in_force"] == "gfd"


def test_extract_account_number_nested():
    payload = {
        "result": {
            "structuredContent": {
                "accounts": [{"account_number": "123456789", "buying_power": "10"}]
            }
        }
    }
    assert extract_account_number(payload) == "123456789"


def test_normalize_market_hours_alldayhours():
    args = normalize_order_arguments({"market_hours": "alldayhours"})
    assert args["market_hours"] == "all_day_hours"


def test_normalize_market_hours_24_hour():
    args = normalize_order_arguments({"market_hours": "24_hour"})
    assert args["market_hours"] == "all_day_hours"


def test_enrich_injects_account_number():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jsonrpc": "2.0",
        "id": 0,
        "result": {
            "structuredContent": {
                "account_number": "987654321",
            }
        },
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "place_equity_order",
            "arguments": {
                "symbol": "GRAB",
                "side": "buy",
                "order_type": "market",
                "quantity": 1,
                "time_in_force": "day",
            },
        },
    }
    headers = {"Authorization": "Bearer test-token"}

    out = asyncio.run(
        enrich_mcp_request(json.dumps(req).encode(), headers, client=mock_client)
    )

    data = json.loads(out)
    args = data["params"]["arguments"]
    assert args["account_number"] == "987654321"
    assert args["time_in_force"] == "gfd"
    assert "account_number" not in json.dumps(req)
