"""Golden tests for Robinhood Ed25519 request signing."""

from __future__ import annotations

import json

from app.signing import (
    build_signing_message,
    create_signature,
    serialize_body,
)


# Values from Robinhood Crypto Trading API docs — Example Signature table.
PRIVATE_KEY = "xQnTJVeQLmw1/Mg2YimEViSpw/SdJcgNXZ5kQkAXNPU="
API_KEY = "rh-api-6148effc-c0b1-486c-8940-a1d099456be6"
METHOD = "POST"
PATH = "/api/v1/crypto/trading/orders/"
TIMESTAMP = "1698708981"
EXPECTED_SIGNATURE = (
    "q/nEtxp/P2Or3hph3KejBqnw5o9qeuQ+hYRnB56FaHbjDsNUY9KhB1asMxohDnzdVFSD7StaTqjSd9U9HvaRAw=="
)

# The docs Python snippet builds `body` as a dict then interpolates it into the
# message via f-string, which uses Python's str(dict) (single quotes). That is
# what produces EXPECTED_SIGNATURE.
DOCS_BODY_DICT = {
    "client_order_id": "131de903-5a9c-4260-abc1-28d562a5dcf0",
    "side": "buy",
    "symbol": "BTC-USD",
    "type": "market",
    "market_order_config": {"asset_quantity": "0.1"},
}


def test_docs_example_signature_matches_str_dict():
    """Reproduce the documented x-signature using str(dict) body."""
    body = str(DOCS_BODY_DICT)
    signature = create_signature(
        PRIVATE_KEY, API_KEY, TIMESTAMP, PATH, METHOD, body
    )
    assert signature == EXPECTED_SIGNATURE


def test_build_signing_message_includes_body():
    message = build_signing_message(API_KEY, TIMESTAMP, PATH, METHOD, "x")
    assert message == f"{API_KEY}{TIMESTAMP}{PATH}{METHOD}x"


def test_build_signing_message_omits_empty_body():
    message = build_signing_message(API_KEY, TIMESTAMP, PATH, "GET", "")
    assert message == f"{API_KEY}{TIMESTAMP}{PATH}GET"


def test_serialize_body_matches_official_client_json_dumps():
    """Official RH samples sign json.dumps(body), not str(dict)."""
    assert serialize_body(DOCS_BODY_DICT) == json.dumps(DOCS_BODY_DICT)


def test_serialize_body_empty():
    assert serialize_body(None) == ""
    assert serialize_body({}) == ""


def test_signature_is_deterministic():
    body = serialize_body(DOCS_BODY_DICT)
    a = create_signature(PRIVATE_KEY, API_KEY, TIMESTAMP, PATH, METHOD, body)
    b = create_signature(PRIVATE_KEY, API_KEY, TIMESTAMP, PATH, METHOD, body)
    assert a == b
    assert a != EXPECTED_SIGNATURE  # json.dumps != str(dict)
