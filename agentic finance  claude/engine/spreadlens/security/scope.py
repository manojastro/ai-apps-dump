"""Signed tool-scope tokens for eve agent tools.

The coordinator gives each live agent session a short-lived token naming the workspace and run.
Agent tools pass it back to the engine; the engine derives the workspace from the signature, so a
model can never widen its own access by choosing a different workspace id.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi import Header, HTTPException

from spreadlens.config import get_settings


def _key() -> bytes:
    k = get_settings().agent_tool_token
    if not k:
        raise RuntimeError("SPREADLENS_AGENT_TOOL_TOKEN is not configured")
    return hashlib.sha256(("scope:" + k).encode()).digest()


def make_scope(workspace_id: str, run_id: str | None, ttl_s: int = 1800) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"ws": workspace_id, "run": run_id, "exp": int(time.time()) + ttl_s}).encode()).decode()
    sig = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_scope(token: str) -> dict:
    try:
        body, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(body.encode()))
        if data["exp"] < time.time():
            raise ValueError
        return data
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(403, "Invalid or expired tool scope") from exc


def scope_dependency(x_spreadlens_scope: str = Header(...)) -> dict:
    return verify_scope(x_spreadlens_scope)
