"""Strip account identifiers from gateway responses shown to agents/users."""

from __future__ import annotations

import json
import re
from typing import Any

_REDACTED_KEYS = frozenset(
    {
        "account_number",
        "account_id",
        "nickname",
        "account_nickname",
        "account_name",
        "rh_account_number",
    }
)

# Full Robinhood account numbers (typically 9–12 digits).
_ACCT_NUM = re.compile(r"\b\d{9,12}\b")

# Masked fragments: ••••6789, ****6789, (••••6789)
_MASKED = re.compile(
    r"[•*]{3,4}\s?\d{4}|"
    r"\(\s*[•*]{3,4}\s*\d{4}\s*\)|"
    r"\(\s*[•*]{3,4}\d{4}\s*\)",
    re.IGNORECASE,
)

# "123456789 / user-nick" or "account (123456789 / user-nick)"
_SLASH_PAIR = re.compile(
    r"(?:your\s+)?account\s*\(\s*\d{9,12}\s*/\s*[\w.-]+\s*\)|"
    r"\b\d{9,12}\s*/\s*[\w.-]+\b",
    re.IGNORECASE,
)

# Agentic Account (••••6789) — individual cash account
_ACCT_LABEL = re.compile(
    r'(?:your\s+)?"?Agentic"?\s+(?:Account|account)\s*\([^)]+\)|'
    r"(?:Margin|Traditional\s+IRA)\s+individual\s*\([^)]+\)",
    re.IGNORECASE,
)

_REPLACEMENT = "Robinhood Agentic"


def redact_sensitive_text(text: str) -> str:
    """Scrub account numbers, masked digits, and nicknames from prose."""
    if not text:
        return text
    out = _SLASH_PAIR.sub(_REPLACEMENT, text)
    out = _ACCT_LABEL.sub(_REPLACEMENT, out)
    out = _MASKED.sub(_REPLACEMENT, out)
    out = _ACCT_NUM.sub(_REPLACEMENT, out)
    return out


def redact_for_client(data: Any) -> Any:
    """Remove Robinhood account identifiers from structured API payloads."""
    if isinstance(data, dict):
        return {
            key: redact_for_client(value)
            for key, value in data.items()
            if key not in _REDACTED_KEYS
        }
    if isinstance(data, list):
        return [redact_for_client(item) for item in data]
    if isinstance(data, str):
        return redact_sensitive_text(data)
    return data


def _redact_mcp_json(data: Any) -> Any:
    """Redact structured fields and MCP text content blocks."""
    data = redact_for_client(data)
    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, dict):
            content = result.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        block["text"] = redact_sensitive_text(block["text"])
            structured = result.get("structuredContent")
            if structured is not None:
                result["structuredContent"] = redact_for_client(structured)
    return data


def redact_mcp_response(body: bytes, content_type: str = "") -> bytes:
    """Parse JSON-RPC MCP response and strip account identifiers before agents see it."""
    if not body:
        return body
    ct = (content_type or "").lower()
    if "text/event-stream" in ct:
        return _redact_mcp_sse(body)
    if "json" not in ct and body[:1] not in (b"{", b"["):
        return body
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body
    redacted = _redact_mcp_json(data)
    return json.dumps(redacted, separators=(",", ":")).encode()


def _redact_mcp_sse(body: bytes) -> bytes:
    """Best-effort redaction for SSE MCP streams."""
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return body
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload and payload != "[DONE]":
                try:
                    data = json.loads(payload)
                    payload = json.dumps(_redact_mcp_json(data), separators=(",", ":"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    payload = redact_sensitive_text(payload)
                lines.append(f"data: {payload}\n")
                continue
        lines.append(line)
    return "".join(lines).encode("utf-8")
