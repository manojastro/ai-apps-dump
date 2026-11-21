"""M2 tests: domain models, full schema, audit-event redaction."""

from __future__ import annotations

import sqlite3

EXPECTED_TABLES = {
    "schema_version", "users", "devices", "cases", "incidents", "evidence",
    "hypotheses", "scripts", "script_versions", "policies", "policy_decisions",
    "approvals", "remediation_runs", "workflows", "workflow_versions",
    "workflow_runs", "fleet_matches", "knowledge_documents",
    "knowledge_permissions", "audit_events", "metrics",
}


def test_schema_has_all_domain_tables(tmp_path) -> None:
    from database.bootstrap import get_connection, init_db

    db = tmp_path / "m2.db"
    init_db(db)
    init_db(db)
    conn = get_connection(db)
    try:
        tables = {r[0] for r in conn.execute(
            "select name from sqlite_master where type='table'")}
        assert EXPECTED_TABLES.issubset(tables)
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_models_defaults() -> None:
    from database.models import Evidence, Hypothesis, PolicyDecision, AuditEvent

    assert Evidence(evidence_id="E", case_id="C").confidence == 1.0
    assert Hypothesis(hypothesis_id="H", case_id="C", title="t").status == "INSUFFICIENT"
    assert PolicyDecision(decision_id="D").decision == "DENY"
    assert AuditEvent().success == 1


def test_fk_enforced(tmp_path) -> None:
    from database.bootstrap import get_connection, init_db

    db = tmp_path / "fk.db"
    init_db(db)
    conn = get_connection(db)
    try:
        try:
            conn.execute(
                "INSERT INTO evidence(evidence_id, case_id) VALUES ('E-1','NOPE')")
            conn.commit()
            raise AssertionError("FK should have rejected orphan evidence")
        except sqlite3.IntegrityError:
            conn.rollback()
    finally:
        conn.close()


def test_audit_redacts_secrets(tmp_path) -> None:
    from audit.logger import list_events, log_event
    from database.bootstrap import get_connection, init_db
    from database.models import AuditEvent

    db = tmp_path / "audit.db"
    init_db(db)
    conn = get_connection(db)
    try:
        conn.execute("INSERT INTO cases(case_id) VALUES ('C-9')")
        key = "AIza" + "Z" * 35
        eid = log_event(conn, AuditEvent(
            case_id="C-9", agent="commander", event_type="tool",
            tool="query_device_health", sanitized_input=f"key {key}",
            sanitized_output="ok"))
        assert eid > 0
        rows = list_events(conn, "C-9")
        assert len(rows) == 1
        assert key not in rows[0]["sanitized_input"]
        assert "[REDACTED]" in rows[0]["sanitized_input"]
    finally:
        conn.close()


def test_audit_timeline_ordered(tmp_path) -> None:
    from audit.logger import list_events, log_event
    from database.bootstrap import get_connection, init_db
    from database.models import AuditEvent

    db = tmp_path / "order.db"
    init_db(db)
    conn = get_connection(db)
    try:
        conn.execute("INSERT INTO cases(case_id) VALUES ('C-O')")
        log_event(conn, AuditEvent(case_id="C-O", event_type="start", timestamp="2026-01-01T00:00:00+00:00"))
        log_event(conn, AuditEvent(case_id="C-O", event_type="end", timestamp="2026-01-02T00:00:00+00:00"))
        rows = list_events(conn, "C-O")
        assert [r["event_type"] for r in rows] == ["start", "end"]
    finally:
        conn.close()


def test_no_real_secrets_in_repo() -> None:
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for rel in ("database/models.py", "database/schema.sql",
                "database/bootstrap.py", "audit/logger.py",
                "common/config.py", ".env.example"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "AIzaSy" not in text
        # No pasted credential fragments of key-like shape either.
        assert not re.search(r"AQ\.[A-Za-z0-9]{10,}", text)
