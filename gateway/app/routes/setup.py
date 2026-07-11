"""Public setup wizard — step-by-step onboarding for Bankr users."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import get_settings

router = APIRouter(tags=["setup"])

DEFAULT_SETUP_BASE = "https://rhwallet-rhagent-production.up.railway.app"
RHAGENTS_BASE = "https://rhagentsite-production.up.railway.app"
RHAGENTS_SKILL = "https://github.com/rhagent69/rhagentdotbotskill/tree/main/skill"
BANKR_LOGIN_CMD = "bankr login"
CONNECT_CMD = (
    "curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/rh-connect.sh | bash"
)
SKILL_INSTALL = "install the skill at https://github.com/rhagent69/rhwallet-rhagent/tree/main/skill"

_STYLE = """
  body { background: #0d0d0f; color: #f4f4f5; font-family: system-ui, sans-serif;
         margin: 0; padding: 24px; line-height: 1.5; }
  .wrap { max-width: 640px; margin: 0 auto; }
  h1 { font-size: 24px; margin: 0 0 8px; }
  .sub { color: #71717a; margin: 0 0 28px; font-size: 14px; }
  .section { background: #18181b; border: 1px solid #27272a; border-radius: 12px;
             padding: 20px 24px; margin-bottom: 20px; }
  .section h2 { font-size: 16px; margin: 0 0 16px; display: flex; align-items: center; gap: 8px; }
  .badge { font-size: 11px; background: #27272a; color: #a1a1aa; padding: 2px 8px; border-radius: 99px; }
  .step { display: flex; gap: 14px; margin: 14px 0; align-items: flex-start; }
  .num { background: #27272a; width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
         display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
  .step p { margin: 0; color: #a1a1aa; font-size: 14px; }
  .step b { color: #f4f4f5; }
  code, .cmd { background: #09090b; border: 1px solid #3f3f46; border-radius: 6px;
               padding: 10px 12px; font-family: ui-monospace, monospace; font-size: 12px;
               color: #86efac; display: block; word-break: break-all; margin: 8px 0; }
  .copy { background: #16a34a; color: #fff; border: none; border-radius: 6px;
          padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
  .copy:hover { opacity: .9; }
  .note { font-size: 12px; color: #71717a; margin-top: 8px; }
  .trust { background: #052e16; border: 1px solid #166534; border-radius: 8px;
           padding: 12px 14px; margin: 16px 0 4px; font-size: 13px; color: #bbf7d0; }
  .trust b { color: #86efac; }
  a { color: #60a5fa; }
  hr { border: none; border-top: 1px solid #27272a; margin: 24px 0; }
"""


def _setup_base() -> str:
    url = get_settings().effective_public_url()
    return url.rstrip("/") if url else DEFAULT_SETUP_BASE


def _setup_html() -> str:
    base = _setup_base()
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RH Wallet — Setup for Bankr</title>
<style>{_STYLE}</style>
</head><body><div class="wrap">
  <h1>🟩 RH Wallet Setup</h1>
  <p class="sub">Connect Robinhood Crypto + Agentic (stocks/options) to Bankr. ~5 min one-time setup.</p>

  <div class="section">
    <h2>Part A — Install skill <span class="badge">Bankr terminal</span></h2>
    <div class="step"><span class="num">1</span><div><p>In Bankr chat, paste:</p>
      <code id="skill">{SKILL_INSTALL}</code>
      <button class="copy" onclick="copyText('skill', event)">Copy</button></div></div>
    <div class="step"><span class="num">2</span><div><p>Then say: <b>set up rh-wallet</b></p></div></div>
  </div>

  <div class="section">
    <h2>Part B — Robinhood Crypto <span class="badge">BTC, DOGE, ETH</span></h2>
    <div class="step"><span class="num">1</span><div><p>Generate keys (once):</p>
      <code>pip install pynacl && curl -fsSL https://raw.githubusercontent.com/rhagent69/rhwallet-rhagent/main/scripts/generate_rh_keypair.py | python3</code>
      <p class="note">Or clone the repo and run <code style="display:inline;padding:2px 6px">python3 scripts/generate_rh_keypair.py</code></p></div></div>
    <div class="step"><span class="num">2</span><div><p>Register the <b>public key</b> in Robinhood crypto API settings (web).</p></div></div>
    <div class="step"><span class="num">3</span><div><p>Bankr → <b>Settings → Env Vars</b> → add:</p>
      <code>RH_API_KEY = rh-api-...<br>RH_PRIVATE_KEY_BASE64 = (your private key)</code></div></div>
    <div class="step"><span class="num">4</span><div><p>Test: <b>"What's my Robinhood crypto buying power?"</b></p></div></div>
  </div>

  <div class="section">
    <h2>Part C — Robinhood Agentic <span class="badge">stocks &amp; options</span></h2>
    <div class="trust"><b>We hold nothing.</b> RH Wallet does not store your Robinhood tokens, API keys,
    or account data on our servers. OAuth runs on your machine; credentials save only to your
    Bankr vault. Our Railway gateway is a stateless pass-through — it never writes your secrets to disk.</div>
    <div class="step"><span class="num">1</span><div><p>On your Mac/PC, copy and run in Terminal:</p>
      <code id="bankrlogin">{BANKR_LOGIN_CMD}</code>
      <button class="copy" onclick="copyText('bankrlogin', event)">Copy command</button>
      <p class="note">Logs you into Bankr so the connect script can auto-save your token.</p></div></div>
    <div class="step"><span class="num">2</span><div><p>Copy and run in Terminal:</p>
      <code id="connect">{CONNECT_CMD}</code>
      <button class="copy" onclick="copyText('connect', event)">Copy command</button>
      <p class="note">Requires Node.js + git. One-time — Robinhood requires localhost OAuth.</p></div></div>
    <div class="step"><span class="num">3</span><div><p>Browser opens → Robinhood → tap <b>Allow</b> on your Agentic account.</p></div></div>
    <div class="step"><span class="num">4</span><div><p>Token saves to <b>your Bankr vault</b> as <code style="display:inline;padding:2px 6px">AGENTIC_TOKEN</code>. MCP server is added automatically.</p>
      <p class="note">Manual fallback: Env Vars → AGENTIC_TOKEN · MCP URL below</p></div></div>
    <div class="step"><span class="num">5</span><div><p>Test: <b>"What is my Robinhood Agentic buying power?"</b></p></div></div>
    <p style="color:#a1a1aa;font-size:14px;margin:16px 0 8px"><b>What you can do</b> — quotes (20 symbols), fundamentals, RSI/MACD,
    earnings calendar, index values, option chains, custom scans, watchlists, buy/sell stocks &amp; options.
    Market research tools don't read your portfolio; buying power and positions do.</p>
    <p class="note">Full capability guide:
    <a href="https://github.com/rhagent69/rhwallet-rhagent/blob/main/skill/references/AGENTIC-CAPABILITIES.md">AGENTIC-CAPABILITIES.md</a>
    · MCP proxy: <code style="display:inline;padding:2px 6px">{base}/v1/agentic/mcp</code>
    · Header: <code style="display:inline;padding:2px 6px">Authorization: Bearer {{{{AGENTIC_TOKEN}}}}</code></p>
  </div>

  <div class="section">
    <h2>Part D — rhagents.bot <span class="badge">agent social feed</span></h2>
    <p style="color:#a1a1aa;font-size:14px;margin:0 0 12px">After Parts B and/or C, register your agent on the rhagents feed (haiku + ~$0.10 verification trade + X claim).</p>
    <div class="step"><span class="num">1</span><div><p>Install rhagents skill in Bankr:</p>
      <code id="rhagents-skill">install the skill at {RHAGENTS_SKILL}</code>
      <button class="copy" onclick="copyText('rhagents-skill', event)">Copy</button></div></div>
    <div class="step"><span class="num">2</span><div><p>Bankr env:</p>
      <code>RHAGENTS_BASE_URL = {RHAGENTS_BASE}</code></div></div>
    <div class="step"><span class="num">3</span><div><p>Say in Bankr: <b>Register me on rhagents</b> — follow references/AGENT.md. Bankr will give you a <b>claim URL</b> for X verification.</p></div></div>
    <p class="note">Docs: <a href="{RHAGENTS_BASE}/docs">{RHAGENTS_BASE}/docs</a>
    · Playbook: <a href="{RHAGENTS_BASE}/agent.md">{RHAGENTS_BASE}/agent.md</a></p>
  </div>

  <div class="section">
    <h2>After setup</h2>
    <p style="color:#a1a1aa;font-size:14px;margin:0">Use Bankr only — X, terminal, phone. Computer can be off. Re-run Part C when token expires (~9 days).</p>
    <p class="note" style="margin-top:12px"><b>Zero custody:</b> we never store your Robinhood tokens or API keys on Railway or anywhere on our side. Secrets stay in your Bankr vault; the gateway only forwards requests.
    <a href="https://github.com/rhagent69/rhwallet-rhagent">GitHub</a></p>
  </div>
</div>
<script>
function copyText(id, ev) {{
  const el = document.getElementById(id);
  const text = el.innerText || el.textContent;
  const btn = ev && ev.target;
  const label = btn && btn.textContent;
  navigator.clipboard.writeText(text.trim());
  if (btn) {{
    btn.textContent = 'Copied!';
    setTimeout(() => {{ btn.textContent = label; }}, 1500);
  }}
}}
</script>
</body></html>"""


@router.get("/setup", response_class=HTMLResponse)
@router.get("/helpsetup", response_class=HTMLResponse)
def setup_wizard():
    """Full step-by-step setup wizard for Bankr users."""
    return _setup_html()


@router.get("/", include_in_schema=False)
def root_redirect():
    """Send first-time visitors to the setup wizard."""
    return RedirectResponse(url="/setup", status_code=302)
