"""Salesforce session for Playwright — via `sf` CLI, never password automation.

Why no username+password scripting: Salesforce enforces MFA, so a login form
script breaks on the verification step and trains the agent to handle
credentials — both bad. Instead the human runs `sf org login web` once
(browser MFA, 2 minutes), and we reuse that session:

1. `sf org display --json` -> accessToken + instanceUrl (subprocess, timeout).
2. Production block: refuse unless sandbox / Dev Edition / scratch.
3. Inject `sid=<token>` cookie + frontdoor URL into a fresh Playwright context.
4. On expiry (401/invalid session), re-run step 1 — `refresh_session()`.

Live verification against a real org is still pending (no org in this
environment); everything parseable offline is unit-tested in
tests/test_session.py.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse

from sentinel.config import assert_sandbox_or_dev

logger = logging.getLogger("sentinel.session")

SF_DISPLAY_TIMEOUT_SECS = 60


class SalesforceAuthError(RuntimeError):
    """Raised for every auth failure — never fall through to password scripting."""


@dataclass(frozen=True)
class SalesforceSession:
    access_token: str
    instance_url: str  # e.g. https://acme.develop.my.salesforce.com

    @property
    def frontdoor_url(self) -> str:
        return f"{self.instance_url.rstrip('/')}/secur/frontdoor.jsp?sid={self.access_token}"


def parse_sf_display_json(raw: str) -> SalesforceSession:
    """Parse `sf org display --json` output. Raises SalesforceAuthError on any problem."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SalesforceAuthError(f"`sf org display` returned non-JSON output: {exc}") from exc
    result = payload.get("result", {})
    token = result.get("accessToken", "")
    instance = result.get("instanceUrl", "")
    if not token or not instance:
        raise SalesforceAuthError(
            "`sf org display` JSON lacks accessToken/instanceUrl. "
            "Is an org authenticated? Run: sf org login web --alias sentinel-dev"
        )
    return SalesforceSession(access_token=token, instance_url=instance)


def get_salesforce_session(alias: str = "sentinel-dev") -> SalesforceSession:
    """Fetch a session via the sf CLI and enforce the production block."""
    sf = shutil.which("sf")
    if sf is None:
        raise SalesforceAuthError(
            "Salesforce CLI (`sf`) not found on PATH. Install it, then run: "
            "sf org login web --alias sentinel-dev"
        )
    try:
        proc = subprocess.run(
            [sf, "org", "display", "--target-org", alias, "--json"],
            capture_output=True,
            text=True,
            timeout=SF_DISPLAY_TIMEOUT_SECS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SalesforceAuthError(f"`sf org display` timed out after {SF_DISPLAY_TIMEOUT_SECS}s") from exc
    if proc.returncode != 0:
        raise SalesforceAuthError(
            f"`sf org display` failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )
    session = parse_sf_display_json(proc.stdout)
    try:
        assert_sandbox_or_dev(session.instance_url)
    except ValueError as exc:
        raise SalesforceAuthError(str(exc)) from exc
    logger.info("Salesforce session acquired for %s", urlparse(session.instance_url).hostname)
    return session


def build_storage_state(session: SalesforceSession) -> dict:
    """Playwright storage_state injecting the session cookie.

    The cookie domain is derived from the instance URL — never hard-coded —
    so sandbox, Dev, and scratch orgs all work. Verified offline (cookie lands
    in a fresh context); frontdoor navigation is verified live in Phase 2.
    """
    hostname = urlparse(session.instance_url).hostname or ""
    if not hostname:
        raise SalesforceAuthError(f"Cannot derive cookie domain from {session.instance_url!r}")
    return {
        "cookies": [
            {
                "name": "sid",
                "value": session.access_token,
                "domain": "." + hostname.lstrip("."),
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax",
            }
        ],
        "origins": [],
    }


def refresh_session(alias: str = "sentinel-dev") -> SalesforceSession:
    """Re-authenticate after expiry. Same checks as initial acquisition."""
    logger.info("Refreshing expired Salesforce session.")
    return get_salesforce_session(alias)
