"""Ed25519 request signing for the Robinhood Crypto Trading API."""

from __future__ import annotations

import base64
import json
from typing import Any, Mapping, Optional, Union

from nacl.signing import SigningKey


def serialize_body(body: Optional[Mapping[str, Any]] = None) -> str:
    """Serialize a request body for signing and for the HTTP wire.

    Matches Robinhood's official sample clients which use ``json.dumps(body)``
    (default separators with spaces) as the signed payload, then send that
    same JSON string.
    """
    if not body:
        return ""
    return json.dumps(body)


def build_signing_message(
    api_key: str,
    timestamp: Union[str, int],
    path: str,
    method: str,
    body: str = "",
) -> str:
    """Build the exact message Robinhood expects for x-signature.

    message = f"{api_key}{timestamp}{path}{method}{body}"
    For requests without a body, omit the body from the message.
    """
    return f"{api_key}{timestamp}{path}{method}{body}"


def sign_message(private_key_base64: str, message: str) -> str:
    """Sign a message with an Ed25519 private key; return base64 signature."""
    private_key_seed = base64.b64decode(private_key_base64)
    private_key = SigningKey(private_key_seed)
    signed = private_key.sign(message.encode("utf-8"))
    return base64.b64encode(signed.signature).decode("utf-8")


def create_signature(
    private_key_base64: str,
    api_key: str,
    timestamp: Union[str, int],
    path: str,
    method: str,
    body: str = "",
) -> str:
    """Create the x-signature header value for a Robinhood API request."""
    message = build_signing_message(api_key, timestamp, path, method, body)
    return sign_message(private_key_base64, message)


def authorization_headers(
    api_key: str,
    private_key_base64: str,
    timestamp: int,
    path: str,
    method: str,
    body: str = "",
) -> dict[str, str]:
    """Build the three Robinhood auth headers."""
    signature = create_signature(
        private_key_base64, api_key, timestamp, path, method, body
    )
    return {
        "x-api-key": api_key,
        "x-signature": signature,
        "x-timestamp": str(timestamp),
    }
