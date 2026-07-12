"""Public setup wizard — redirects to rhagents site (canonical setup lives there)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["setup"])

RHAGENTS_SETUP = "https://rhagent.bot/setup"


@router.get("/setup", include_in_schema=False)
@router.get("/helpsetup", include_in_schema=False)
def setup_wizard():
    """Redirect to canonical setup wizard on rhagents.bot."""
    return RedirectResponse(url=RHAGENTS_SETUP, status_code=302)


@router.get("/", include_in_schema=False)
def root_redirect():
    """Send first-time visitors to the setup wizard."""
    return RedirectResponse(url=RHAGENTS_SETUP, status_code=302)
