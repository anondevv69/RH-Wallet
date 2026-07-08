"""Strip account identifiers from gateway responses shown to agents/users."""

from __future__ import annotations

from typing import Any

_REDACTED_KEYS = frozenset({"account_number"})


def redact_for_client(data: Any) -> Any:
    """Remove Robinhood account numbers from API payloads."""
    if isinstance(data, dict):
        return {
            key: redact_for_client(value)
            for key, value in data.items()
            if key not in _REDACTED_KEYS
        }
    if isinstance(data, list):
        return [redact_for_client(item) for item in data]
    return data
