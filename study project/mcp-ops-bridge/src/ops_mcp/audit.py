"""Audit every MCP tool call into SQLite audit_log."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from mock_itsm.db import connect


def args_hash(args: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()


def log_audit(
    db_path: str,
    tool: str,
    args: dict[str, object],
    target: str,
    result: str,
    success: bool,
    actor: str = "mcp-client",
) -> None:
    conn = connect(db_path)
    try:
        conn.execute(
            "INSERT INTO audit_log (ts, actor, tool, args_hash, target, result, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(UTC).isoformat(),
                actor,
                tool,
                args_hash(args),
                target,
                result[:2000],
                1 if success else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()
