"""Robinhood Agentic MCP OAuth bridge + stateless proxy.

Architecture (zero server-side token storage):
  1. GET  /agentic/auth      — Start PKCE OAuth. Encodes code_verifier in
                               signed `state` parameter so no session needed.
  2. GET  /agentic/callback  — Exchange code → token. Displays token to user.
                               User copies it to Bankr env as AGENTIC_TOKEN.
  3. POST /v1/agentic/mcp    — Stateless proxy. Reads Authorization header
                               from caller (Bankr passes {{AGENTIC_TOKEN}}),
                               forwards every JSON-RPC call to Robinhood.
                               We never store the token.

Note: Robinhood's MCP OAuth may require a pre-approved client_id.
Set AGENTIC_CLIENT_ID + AGENTIC_CLIENT_SECRET in Railway env to use a
pre-registered client. Without them we attempt dynamic client registration
per the MCP OAuth spec (RFC 7591). If Robinhood blocks registration you
will see an error at /agentic/auth.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agentic"])

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

ROBINHOOD_MCP_BASE = "https://agent.robinhood.com"
ROBINHOOD_MCP_PATH = "/mcp/trading"
ROBINHOOD_MCP_URL = ROBINHOOD_MCP_BASE + ROBINHOOD_MCP_PATH

# Simple in-memory cache for dynamically registered client credentials.
_dynamic_client: dict = {}


def _state_secret() -> bytes:
    """HMAC key for signing OAuth state. Falls back to a boot-time random if unset."""
    key = os.environ.get("AGENTIC_STATE_SECRET", "")
    if not key:
        # This means state tokens don't survive restarts, which is fine —
        # OAuth flows complete in seconds.
        if not hasattr(_state_secret, "_fallback"):
            _state_secret._fallback = secrets.token_hex(32)  # type: ignore[attr-defined]
        key = _state_secret._fallback  # type: ignore[attr-defined]
    return key.encode()


def _callback_url(request: Request) -> str:
    public = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    if not public:
        public = str(request.base_url).rstrip("/")
    return f"{public}/agentic/callback"


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

def _pkce_pair() -> tuple[str, str]:
    """Generate (code_verifier, code_challenge) for PKCE S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


# ---------------------------------------------------------------------------
# State signing (stateless PKCE — no server session needed)
# ---------------------------------------------------------------------------

def _encode_state(code_verifier: str) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"cv": code_verifier, "ts": int(time.time())}).encode()
    ).decode()
    sig = hmac.new(_state_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _decode_state(state: str) -> Optional[str]:
    """Return code_verifier or None if state is invalid / expired (>10 min)."""
    try:
        payload, sig = state.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(_state_secret(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
    except Exception:
        return None
    if time.time() - data.get("ts", 0) > 600:
        return None
    return data.get("cv")


# ---------------------------------------------------------------------------
# OAuth metadata + dynamic client registration
# ---------------------------------------------------------------------------

async def _oauth_metadata() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{ROBINHOOD_MCP_BASE}/.well-known/oauth-authorization-server"
        )
        if r.status_code != 200:
            # Fallback: try MCP-spec discovery path
            r = await client.get(
                f"{ROBINHOOD_MCP_BASE}/.well-known/oauth-authorization-server{ROBINHOOD_MCP_PATH}"
            )
        r.raise_for_status()
        return r.json()


async def _get_client_credentials(callback_url: str) -> tuple[str, Optional[str]]:
    """Return (client_id, client_secret). Prefers env vars; falls back to dynamic registration."""
    client_id = os.environ.get("AGENTIC_CLIENT_ID", "")
    client_secret = os.environ.get("AGENTIC_CLIENT_SECRET", "")
    if client_id:
        return client_id, client_secret or None

    # Already registered this session?
    if _dynamic_client.get("client_id"):
        return _dynamic_client["client_id"], _dynamic_client.get("client_secret")

    # Try dynamic registration (RFC 7591 / MCP OAuth spec)
    meta = await _oauth_metadata()
    reg_endpoint = meta.get("registration_endpoint")
    if not reg_endpoint:
        raise HTTPException(
            status_code=503,
            detail=(
                "Robinhood's MCP OAuth server does not expose a registration endpoint "
                "and no AGENTIC_CLIENT_ID is configured. "
                "Set AGENTIC_CLIENT_ID in Railway environment variables."
            ),
        )

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            reg_endpoint,
            json={
                "client_name": "RH Wallet Gateway",
                "redirect_uris": [callback_url],
                "grant_types": ["authorization_code"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",  # public PKCE client
            },
        )
        if r.status_code not in (200, 201):
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Dynamic client registration failed ({r.status_code}): {r.text[:200]}. "
                    "Set AGENTIC_CLIENT_ID in Railway env."
                ),
            )
        reg = r.json()
        _dynamic_client["client_id"] = reg["client_id"]
        _dynamic_client["client_secret"] = reg.get("client_secret")
        logger.info("Dynamic OAuth client registered: %s", reg["client_id"])
        return _dynamic_client["client_id"], _dynamic_client.get("client_secret")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/agentic/auth", response_class=RedirectResponse)
async def agentic_auth_start(request: Request):
    """Start Robinhood Agentic OAuth PKCE flow. Redirects to Robinhood login."""
    callback = _callback_url(request)
    verifier, challenge = _pkce_pair()
    state = _encode_state(verifier)

    try:
        client_id, _ = await _get_client_credentials(callback)
        meta = await _oauth_metadata()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    auth_endpoint = meta.get("authorization_endpoint")
    if not auth_endpoint:
        raise HTTPException(
            status_code=503,
            detail="Could not discover Robinhood OAuth authorization endpoint.",
        )

    params = {
        "client_id": client_id,
        "redirect_uri": callback,
        "response_type": "code",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "scope": "trading",
    }
    from urllib.parse import urlencode
    auth_url = f"{auth_endpoint}?{urlencode(params)}"
    logger.info("Redirecting to Robinhood OAuth: %s", auth_endpoint)
    return RedirectResponse(url=auth_url)


@router.get("/agentic/callback", response_class=HTMLResponse)
async def agentic_auth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    """OAuth callback. Exchanges code for token, shows it to user. Nothing stored."""
    if error:
        return _html_error(f"Robinhood OAuth error: {error}")

    if not code or not state:
        return _html_error("Missing code or state in callback.")

    verifier = _decode_state(state)
    if not verifier:
        return _html_error("Invalid or expired OAuth state. Please restart the flow.")

    callback = _callback_url(request)

    try:
        client_id, client_secret = await _get_client_credentials(callback)
        meta = await _oauth_metadata()
    except HTTPException as exc:
        return _html_error(str(exc.detail))
    except Exception as exc:
        return _html_error(str(exc))

    token_endpoint = meta.get("token_endpoint")
    if not token_endpoint:
        return _html_error("Could not discover Robinhood token endpoint.")

    payload: dict = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": callback,
        "client_id": client_id,
        "code_verifier": verifier,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(token_endpoint, data=payload)

    if r.status_code != 200:
        return _html_error(f"Token exchange failed ({r.status_code}): {r.text[:300]}")

    token_data = r.json()
    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", "unknown")

    if not access_token:
        return _html_error(f"No access_token in response: {r.text[:300]}")

    return _html_success(access_token, refresh_token, str(expires_in))


@router.post("/v1/agentic/mcp")
async def agentic_mcp_proxy(request: Request):
    """Stateless MCP proxy. Reads the caller's OAuth token from Authorization header,
    forwards every JSON-RPC call to Robinhood. We never store the token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=(
                "Authorization: Bearer <token> required. "
                "Set AGENTIC_TOKEN in Bankr env vars, then add MCP server "
                "https://rh-wallet-production.up.railway.app/v1/agentic/mcp "
                "with header Authorization: Bearer {{AGENTIC_TOKEN}}"
            ),
        )

    body = await request.body()
    forward_headers = {
        "Authorization": auth,
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Accept": request.headers.get("Accept", "application/json, text/event-stream"),
    }
    # Pass through MCP session headers if present
    for h in ("Mcp-Session-Id", "Last-Event-Id"):
        if h in request.headers:
            forward_headers[h] = request.headers[h]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            rr = await client.post(
                ROBINHOOD_MCP_URL,
                content=body,
                headers=forward_headers,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream error: {exc}") from exc

    from fastapi.responses import Response
    return Response(
        content=rr.content,
        status_code=rr.status_code,
        media_type=rr.headers.get("content-type", "application/json"),
    )


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

_PAGE_STYLE = """
  body { background: #0d0d0f; color: #f0f0f0; font-family: system-ui, sans-serif;
         display: flex; align-items: center; justify-content: center;
         min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
  .card { background: #18181b; border: 1px solid #27272a; border-radius: 16px;
          padding: 40px; max-width: 580px; width: 100%; }
  h1 { margin: 0 0 8px; font-size: 22px; }
  p { color: #a1a1aa; margin: 0 0 24px; line-height: 1.5; }
  .token-box { background: #09090b; border: 1px solid #3f3f46; border-radius: 8px;
               padding: 14px 16px; font-family: monospace; font-size: 13px;
               word-break: break-all; color: #86efac; margin: 0 0 16px; }
  .copy-btn { background: #22c55e; color: #000; border: none; border-radius: 8px;
              padding: 10px 20px; font-size: 14px; font-weight: 600; cursor: pointer;
              transition: opacity .15s; }
  .copy-btn:hover { opacity: .85; }
  .copy-btn.copied { background: #4ade80; }
  .steps { background: #09090b; border: 1px solid #27272a; border-radius: 8px;
           padding: 16px 20px; margin: 0; }
  .steps li { color: #a1a1aa; margin: 8px 0; line-height: 1.6; }
  .steps code { background: #27272a; padding: 2px 6px; border-radius: 4px;
                color: #f0f0f0; font-size: 12px; }
  .err { color: #f87171; }
  .badge { display: inline-block; background: #15803d; color: #bbf7d0;
           font-size: 12px; padding: 2px 8px; border-radius: 99px; margin-left: 8px; }
"""


def _html_success(access_token: str, refresh_token: str, expires_in: str) -> str:
    refresh_section = ""
    if refresh_token:
        refresh_section = f"""
        <p style="margin:24px 0 6px;font-size:13px;color:#71717a;">
          Refresh token (optional — for future re-auth):
        </p>
        <div class="token-box" id="refresh">{refresh_token}</div>
        <button class="copy-btn" onclick="copyToken('refresh', this)" style="margin-bottom:24px;">
          Copy Refresh Token
        </button>
        """

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Robinhood Agentic — Connected</title>
<style>{_PAGE_STYLE}</style></head>
<body><div class="card">
  <h1>Connected <span class="badge">✓</span></h1>
  <p>Your Robinhood Agentic account is authorized. Copy the token below and
     save it to Bankr — we never store it.</p>

  <p style="margin:0 0 6px;font-size:13px;color:#71717a;">
    Access token (expires in {expires_in}s):
  </p>
  <div class="token-box" id="access">{access_token}</div>
  <button class="copy-btn" onclick="copyToken('access', this)" style="margin-bottom:24px;">
    Copy Access Token
  </button>

  {refresh_section}

  <p style="margin:0 0 12px;font-weight:600;">Next steps:</p>
  <ol class="steps">
    <li>In Bankr: <b>Settings → Env Vars → + Add</b><br>
      Key: <code>AGENTIC_TOKEN</code> &nbsp; Value: <em>paste token above</em></li>
    <li>Add MCP server in Bankr settings:<br>
      Name: <code>robinhood-agentic</code><br>
      URL: <code>https://rh-wallet-production.up.railway.app/v1/agentic/mcp</code><br>
      Transport: <code>Streamable HTTP</code><br>
      Header: <code>Authorization</code> → <code>Bearer {{{{AGENTIC_TOKEN}}}}</code></li>
    <li>Ask Bankr: <em>"What is my Robinhood Agentic buying power?"</em></li>
  </ol>
</div>
<script>
async function copyToken(id, btn) {{
  const text = document.getElementById(id).textContent.trim();
  await navigator.clipboard.writeText(text);
  btn.textContent = 'Copied!';
  btn.classList.add('copied');
  setTimeout(() => {{ btn.textContent = id === 'access' ? 'Copy Access Token' : 'Copy Refresh Token'; btn.classList.remove('copied'); }}, 2000);
}}
</script>
</body></html>"""


def _html_error(message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Robinhood Agentic — Error</title>
<style>{_PAGE_STYLE}</style></head>
<body><div class="card">
  <h1>Connection failed</h1>
  <p class="err">{message}</p>
  <p>Go back to your Bankr terminal and try again, or check the
     <a href="https://github.com/anondevv69/RH-Wallet" style="color:#60a5fa">
     RH Wallet docs</a> for setup help.</p>
</div></body></html>"""
