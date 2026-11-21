"""Single-use, scoped, expiring approval tokens stored hashed.

Flow: POST /approvals -> plaintext token (shown once) -> write tools send it
back -> verify_approval() hashes, scope-checks, expiry-checks, marks used
in ONE transaction. Uses hmac.compare_digest to avoid timing leaks.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta

from mock_itsm.models import ApprovalCheck


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_approval(
    conn: sqlite3.Connection,
    tool: str,
    target: str,
    action: str = "write",
    expires_minutes: int = 10,
) -> tuple[str, str]:
    """Create a token. Returns (plaintext_token, expires_at_iso)."""
    token = secrets.token_urlsafe(32)
    digest = hash_token(token)
    now = datetime.now(UTC)
    expires_at = (now + timedelta(minutes=expires_minutes)).isoformat()
    conn.execute(
        "INSERT INTO approvals (token_hash, tool, target, action, created_at, expires_at, used)"
        " VALUES (?, ?, ?, ?, ?, ?, 0)",
        (digest, tool, target, action, now.isoformat(), expires_at),
    )
    conn.commit()
    return token, expires_at


def verify_approval(conn: sqlite3.Connection, token: str, tool: str, target: str) -> ApprovalCheck:
    """Check scope + expiry + single-use, then mark used atomically."""
    digest = hash_token(token)
    # One write transaction: lock early so two concurrent uses can't both pass.
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            "SELECT token_hash, tool, target, expires_at, used FROM approvals WHERE token_hash = ?",
            (digest,),
        )
        row = cur.fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="unknown token")
        stored = str(row["token_hash"])
        if not hmac.compare_digest(stored, digest):
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="token mismatch")
        if str(row["tool"]) != tool:
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="wrong tool scope")
        if str(row["target"]) != target:
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="wrong target scope")
        if int(row["used"]) == 1:
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="token already used")
        try:
            exp = datetime.fromisoformat(str(row["expires_at"]))
        except ValueError:
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="bad expiry")
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if datetime.now(UTC) > exp:
            conn.execute("ROLLBACK")
            return ApprovalCheck(ok=False, reason="token expired")
        conn.execute(
            "UPDATE approvals SET used = 1, used_at = ? WHERE token_hash = ?",
            (_now_iso(), digest),
        )
        conn.execute("COMMIT")
        return ApprovalCheck(ok=True, reason="ok")
    except Exception as e:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        return ApprovalCheck(ok=False, reason=f"verify error: {e}")
