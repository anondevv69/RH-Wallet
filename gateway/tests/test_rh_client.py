"""Tests for Robinhood account selection."""

from app.rh_client import RobinhoodClient


def test_select_trading_account_prefers_api_tradable():
    results = [
        {"account_number": "NON_API", "is_api_tradable": False, "buying_power": "100.00"},
        {"account_number": "API_LOW", "is_api_tradable": True, "buying_power": "25.33"},
        {"account_number": "API_HIGH", "is_api_tradable": True, "buying_power": "50.00"},
    ]
    picked = RobinhoodClient._select_trading_account(results)
    assert picked["account_number"] == "API_HIGH"


def test_select_trading_account_falls_back_to_first_when_no_flag():
    results = [
        {"account_number": "ACC1", "buying_power": "10.00"},
        {"account_number": "ACC2", "buying_power": "20.00"},
    ]
    picked = RobinhoodClient._select_trading_account(results)
    assert picked["account_number"] == "ACC2"
