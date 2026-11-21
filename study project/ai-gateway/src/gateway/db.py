"""SQLite storage: tenants, usage_ledger, audit_log.

Mock-first slice uses SQLite. Postgres is a stub (see docker-compose + docs/).
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    key_hash TEXT NOT NULL,
    monthly_budget_usd REAL NOT NULL DEFAULT 10.0,
    rpm INTEGER NOT NULL DEFAULT 60,
    tpm INTEGER NOT NULL DEFAULT 20000,
    allowed_models TEXT NOT NULL DEFAULT '[]',
    guardrail_profile TEXT NOT NULL DEFAULT 'standard',
    deleted INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS usage_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant TEXT NOT NULL,
    request_id TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    cache_hit INTEGER NOT NULL DEFAULT 0,
    blocked INTEGER NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    tenant TEXT NOT NULL,
    event TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    request_id TEXT NOT NULL DEFAULT ''
);
"""


def get_conn(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def create_tenant(
    conn: sqlite3.Connection,
    *,
    name: str,
    key_hash: str,
    monthly_budget_usd: float = 10.0,
    rpm: int = 60,
    tpm: int = 20000,
    allowed_models: list[str] | None = None,
    guardrail_profile: str = "standard",
) -> int:
    allowed_models = allowed_models or []
    cur = conn.execute(
        """INSERT INTO tenants
        (name, key_hash, monthly_budget_usd, rpm, tpm, allowed_models,
         guardrail_profile, deleted, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (
            name,
            key_hash,
            monthly_budget_usd,
            rpm,
            tpm,
            json.dumps(allowed_models),
            guardrail_profile,
            time.time(),
        ),
    )
    conn.commit()
    tid = cur.lastrowid
    assert tid is not None
    return tid


def find_tenant_by_hash(conn: sqlite3.Connection, key_hash: str) -> sqlite3.Row | None:
    # NOTE: hash lookup by equality is fine; per-candidate constant-time
    # verify happens in the auth layer when needed. We compare against all
    # non-deleted rows with hmac.compare_digest in app code for the demo.
    row = conn.execute(
        "SELECT * FROM tenants WHERE key_hash = ? AND deleted = 0", (key_hash,)
    ).fetchone()
    return row  # type: ignore[no-any-return]


def find_tenant_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM tenants WHERE name = ?", (name,)).fetchone()
    return row  # type: ignore[no-any-return]


def soft_delete_tenant(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("UPDATE tenants SET deleted = 1 WHERE name = ?", (name,))
    conn.commit()


def record_usage(
    conn: sqlite3.Connection,
    *,
    tenant: str,
    request_id: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    cache_hit: bool = False,
    blocked: bool = False,
    reason: str = "",
    ts: float | None = None,
) -> None:
    conn.execute(
        """INSERT INTO usage_ledger
        (tenant, request_id, model, tokens_in, tokens_out, cost_usd,
         cache_hit, blocked, reason, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            tenant,
            request_id,
            model,
            tokens_in,
            tokens_out,
            cost_usd,
            1 if cache_hit else 0,
            1 if blocked else 0,
            reason,
            ts if ts is not None else time.time(),
        ),
    )
    conn.commit()


def record_audit(
    conn: sqlite3.Connection, *, tenant: str, event: str, reason: str = "",
    request_id: str = "",
) -> None:
    conn.execute(
        "INSERT INTO audit_log (ts, tenant, event, reason, request_id)"
        " VALUES (?, ?, ?, ?, ?)",
        (time.time(), tenant, event, reason, request_id),
    )
    conn.commit()
