#!/usr/bin/env python3
"""Robinhood Agentic OAuth — local loopback helper for Bankr.

Robinhood only completes OAuth when redirect_uri is localhost/127.0.0.1.
Hosted callbacks (Railway, etc.) reach the consent screen but fail on Allow.

This script:
  1. Registers an OAuth client with redirect http://127.0.0.1:<port>/callback
  2. Opens your browser to Robinhood login
  3. Listens locally for the callback
  4. Prints your access token — paste into Bankr as AGENTIC_TOKEN

Usage:
  python3 scripts/agentic_oauth.py

We never send your token anywhere. It prints to your terminal only.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

MCP_BASE = "https://agent.robinhood.com"
REGISTER_URL = f"{MCP_BASE}/oauth/trading/register"
METADATA_URL = f"{MCP_BASE}/.well-known/oauth-authorization-server"
DEFAULT_PORT = 9876
PROXY_MCP_URL = "https://rh-wallet-production.up.railway.app/v1/agentic/mcp"


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _http_json(method: str, url: str, body: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode() if exc.fp else str(exc)
        raise RuntimeError(f"HTTP {exc.code} {url}: {detail}") from exc


def main() -> int:
    port = DEFAULT_PORT
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    print("RH Wallet — Robinhood Agentic OAuth (local)")
    print("=" * 50)
    print(f"Redirect URI: {redirect_uri}")
    print()

    meta = _http_json("GET", METADATA_URL)
    auth_endpoint = meta["authorization_endpoint"]
    token_endpoint = meta["token_endpoint"]

    reg = _http_json(
        "POST",
        REGISTER_URL,
        {
            "client_name": "RH Wallet Local",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
    )
    client_id = reg["client_id"]
    print(f"Registered OAuth client: {client_id[:12]}...")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)

    auth_params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "internal",
        }
    )
    auth_url = f"{auth_endpoint}?{auth_params}"

    result: dict = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:
            return

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            params = urllib.parse.parse_qs(parsed.query)
            if params.get("error"):
                result["error"] = params["error"][0]
                self._respond("Authorization failed. You can close this tab.")
                done.set()
                return

            code = params.get("code", [None])[0]
            returned_state = params.get("state", [None])[0]
            if not code or returned_state != state:
                result["error"] = "Missing code or state mismatch"
                self._respond("Invalid callback. You can close this tab.")
                done.set()
                return

            result["code"] = code
            self._respond(
                "Connected! Return to your terminal to copy your token. "
                "You can close this tab."
            )
            done.set()

        def _respond(self, message: str) -> None:
            body = f"<html><body style='font-family:system-ui;padding:40px'>"
            body += f"<h2>{message}</h2></body></html>"
            encoded = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print("Opening Robinhood login in your browser...")
    print("Sign in, select your Agentic account, then tap Allow.")
    print()
    webbrowser.open(auth_url)

    if not done.wait(timeout=300):
        print("Timed out waiting for OAuth callback (5 min).", file=sys.stderr)
        server.shutdown()
        return 1

    server.shutdown()

    if result.get("error"):
        print(f"OAuth error: {result['error']}", file=sys.stderr)
        return 1

    token_payload = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": verifier,
        }
    ).encode()

    req = urllib.request.Request(
        token_endpoint,
        data=token_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            token_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        print(f"Token exchange failed ({exc.code}): {detail}", file=sys.stderr)
        return 1

    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", "?")

    if not access_token:
        print(f"No access_token in response: {token_data}", file=sys.stderr)
        return 1

    print()
    print("SUCCESS — copy this token into Bankr:")
    print("=" * 50)
    print(access_token)
    print("=" * 50)
    if refresh_token:
        print()
        print("Refresh token (optional, for re-auth later):")
        print(refresh_token)
    print()
    print(f"Expires in: {expires_in} seconds")
    print()
    print("Next steps:")
    print("  1. Bankr → Settings → Env Vars → AGENTIC_TOKEN = <token above>")
    print("  2. MCP server:")
    print(f"     URL: {PROXY_MCP_URL}")
    print("     Header: Authorization → Bearer {{AGENTIC_TOKEN}}")
    print("  3. Ask Bankr: What is my Robinhood Agentic buying power?")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
