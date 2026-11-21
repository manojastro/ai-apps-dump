"""Approved Script Registry (M12 reads, M13 seeds + governs).

Governance rule: agents request execute_remote_action(action_id=...) — never
raw shell. Every row carries hash/version/rollback/autonomy + live metrics.
Hash = sha256 over the canonical descriptor, recomputable from the row alone;
any stored-hash tampering fails verify_stored_hash (M29 security tests lean
on this). AI-generated-script intake lands in M14.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

APPROVED_BY = "change-advisory-board"
APPROVAL_TS = "2026-09-01T00:00:00+00:00"

# script_id, name, description, version, owner, platform, groups, risk,
# autonomy, rollback, approved, exec, success, failure, rollbacks, reopens
_SEED: tuple[tuple[Any, ...], ...] = (
    ("SCR-018", "Clear Teams Cache", "Clears Teams cache + restarts client",
     "3.2", "workplace-ops", "windows", ["corporate-laptop"], "LOW", "L3",
     1, 1, 95, 94, 1, 1, 1),
    ("SCR-VPN-RECONNECT", "VPN reconnect + token refresh",
     "Reconnects VPN client with fresh SSO token", "1.4", "network-ops",
     "windows", ["corporate-laptop"], "MEDIUM", "L2", 1, 1, 40, 38, 2, 1, 1),
    ("SCR-INSTALL", "Install approved software",
     "Installs a catalog app via Intune/Company Portal", "2.0", "workplace-ops",
     "windows", ["corporate-laptop"], "MEDIUM", "L2", 1, 1, 60, 57, 3, 0, 2),
    ("SCR-RESTART-APP", "Restart user application",
     "Graceful restart of a named user application", "1.1", "workplace-ops",
     "windows", ["corporate-laptop"], "LOW", "L3", 1, 1, 80, 79, 1, 0, 0),
    ("SCR-CLEAR-TEMP", "Clear approved temp cache",
     "Clears OS temp locations on an allowlist", "1.0", "workplace-ops",
     "windows", ["corporate-laptop"], "LOW", "L3", 1, 1, 70, 69, 1, 0, 1),
    ("SCR-DISK-CLEANUP", "Disk cleanup approved targets",
     "Frees approved caches/logs when disk is pressured", "1.2", "workplace-ops",
     "windows", ["corporate-laptop"], "LOW", "L3", 1, 1, 30, 29, 1, 0, 0),
    ("SCR-FIREWALL", "Firewall rule change",
     "Modifies host firewall rules (human approval always)", "1.0", "netsec",
     "windows", ["corporate-laptop"], "HIGH", "L1", 0, 1, 5, 4, 1, 0, 1),
    ("SCR-DISABLE-PROTECTION", "Disable endpoint protection",
     "DENY-listed: never executable", "1.0", "netsec",
     "windows", ["corporate-laptop"], "CRITICAL", "L0", 0, 0, 0, 0, 0, 0, 0),
)

# root-cause keyword -> approved action (remediation selection starts here; M16 executes)
_ACTION_MAP = (
    (("teams", "memory"), "SCR-018"),
    (("vpn", "token", "stale"), "SCR-VPN-RECONNECT"),
    (("disk",), "SCR-DISK-CLEANUP"),
)


def canonical_hash(script_id: str, version: str, platform: str, name: str) -> str:
    payload = json.dumps({"script_id": script_id, "version": version,
                          "platform": platform, "name": name}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_stored_hash(script: dict[str, Any]) -> bool:
    """Recompute from the row; False means the registry row was tampered with."""
    return canonical_hash(str(script.get("script_id", "")), str(script.get("version", "")),
                          str(script.get("platform", "")), str(script.get("name", ""))) == \
        str(script.get("hash", ""))


def seed_registry(conn: sqlite3.Connection) -> list[str]:
    """Idempotent governed seed. Returns all script ids present afterwards."""
    for row in _SEED:
        (sid, name, desc, version, owner, platform, groups, risk, autonomy,
         rollback, approved, execs, wins, fails, rollbacks, reopens) = row
        rate = round(100 * wins / execs, 1) if execs else 0.0
        conn.execute(
            "INSERT OR IGNORE INTO scripts(script_id, name, description, version, hash, "
            "owner, platform, supported_device_groups, risk, approved, "
            "approval_timestamp, approved_by, rollback_available, autonomy_level, "
            "execution_count, success_count, failure_count, rollback_count, "
            "reopen_count, success_rate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, name, desc, version, canonical_hash(sid, version, platform, name),
             owner, platform, json.dumps(groups), risk, approved, APPROVAL_TS,
             APPROVED_BY, rollback, autonomy, execs, wins, fails, rollbacks,
             reopens, rate))
    conn.commit()
    return [r[0] for r in conn.execute("SELECT script_id FROM scripts ORDER BY script_id")]


def lookup_script(conn: sqlite3.Connection, script_id: str) -> dict[str, Any] | None:
    """Return the scripts row for action_id, or None when unknown."""
    row = conn.execute("SELECT * FROM scripts WHERE script_id=?", (script_id,)).fetchone()
    return dict(row) if row else None


def is_approved(script: dict[str, Any] | None) -> bool:
    return bool(script and script.get("approved") == 1)


def verify_hash(script: dict[str, Any], provided_hash: str = "") -> bool:
    """Tamper gate: mismatch DENIES. Empty provided hash defers to execution (M16)."""
    if not provided_hash:
        return True
    expected = str(script.get("hash", ""))
    return bool(expected) and provided_hash == expected


def get_approved_action(conn: sqlite3.Connection, script_id: str) -> dict[str, Any] | None:
    """Approved + hash-intact row, else None (never trust blindly)."""
    script = lookup_script(conn, script_id)
    if not is_approved(script) or not verify_stored_hash(script or {}):
        return None
    assert script is not None
    return script


def find_approved_action(conn: sqlite3.Connection, root_cause: str) -> dict[str, Any] | None:
    """Map a root-cause title to an approved, hash-intact action (or None)."""
    lowered = root_cause.lower()
    for keywords, script_id in _ACTION_MAP:
        if any(kw in lowered for kw in keywords):
            return get_approved_action(conn, script_id)
    return None


def record_execution(conn: sqlite3.Connection, script_id: str, success: bool,
                     rollback: bool = False, reopen: bool = False) -> dict[str, Any]:
    """Account one execution + recompute success_rate. Returns the fresh row."""
    script = lookup_script(conn, script_id)
    if script is None:
        raise LookupError(f"script {script_id} not in registry")
    execs = int(script.get("execution_count", 0)) + 1
    wins = int(script.get("success_count", 0)) + (1 if success else 0)
    fails = int(script.get("failure_count", 0)) + (0 if success else 1)
    rollbacks = int(script.get("rollback_count", 0)) + (1 if rollback else 0)
    reopens = int(script.get("reopen_count", 0)) + (1 if reopen else 0)
    rate = round(100 * wins / execs, 1)
    conn.execute(
        "UPDATE scripts SET execution_count=?, success_count=?, failure_count=?, "
        "rollback_count=?, reopen_count=?, success_rate=? WHERE script_id=?",
        (execs, wins, fails, rollbacks, reopens, rate, script_id))
    conn.commit()
    fresh = lookup_script(conn, script_id)
    assert fresh is not None
    return fresh
