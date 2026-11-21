"""M15 tests: risk classification, earned autonomy, approval lifecycle."""

from __future__ import annotations

from control_plane import approvals, autonomy
from control_plane import registry as reg
from control_plane import risk as risk_engine


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "m15.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def _runs(conn, script_id: str, outcomes: list[bool]) -> None:
    for i, ok in enumerate(outcomes):
        conn.execute("INSERT INTO remediation_runs(run_id, case_id, script_id, success) "
                     "VALUES (?,?,?,?)", (f"R-{script_id}-{i}", "C", script_id, int(ok)))
    conn.commit()


def test_risk_sources(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        assert risk_engine.classify_action_risk(conn, "SCR-018") == {
            "risk": "LOW", "basis": "registry"}
        assert risk_engine.classify_action_risk(conn, "SCR-NEW", ["reconnect_vpn"])["risk"] == "MEDIUM"
        assert risk_engine.classify_action_risk(conn, "SCR-NEW", ["nonsense"])["risk"] == "HIGH"
        assert risk_engine.classify_action_risk(conn, "SCR-NEW")["risk"] == "HIGH"
    finally:
        conn.close()


def test_l1_needs_approvals_then_promotes(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        conn.execute("INSERT INTO scripts(script_id, approved, autonomy_level) "
                     "VALUES ('SCR-W1', 1, 'L1')")
        conn.commit()
        assert autonomy.evaluate_autonomy(conn, "script", "SCR-W1")["recommended"] == "L1"
        approvals.request_approval(conn, "C1", "SCR-W1", "commander")
        approvals.approve(conn, "APR-C1-SCR-W1", "manager")
        approvals.request_approval(conn, "C2", "SCR-W1", "commander")
        approvals.approve(conn, "APR-C2-SCR-W1", "manager")
        assert autonomy.evaluate_autonomy(conn, "script", "SCR-W1")["recommended"] == "L2"
        assert autonomy.apply_autonomy(conn, "script", "SCR-W1")["recommended"] == "L2"
        assert reg.lookup_script(conn, "SCR-W1")["autonomy_level"] == "L2"
    finally:
        conn.close()


def test_l2_to_l3_on_seed_metrics(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        # SCR-VPN-RECONNECT seed: 40 runs, 95%, low rollback/reopen, L2.
        outcome = autonomy.evaluate_autonomy(conn, "script", "SCR-VPN-RECONNECT")
        assert outcome["recommended"] == "L3", outcome["reasons"]
    finally:
        conn.close()


def test_failures_demote_to_l2(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        _runs(conn, "SCR-018", [True] * 7 + [False] * 3)
        outcome = autonomy.evaluate_autonomy(conn, "script", "SCR-018")
        assert outcome["current"] == "L3" and outcome["recommended"] == "L2"
        assert autonomy.apply_autonomy(conn, "script", "SCR-018")["recommended"] == "L2"
        assert reg.lookup_script(conn, "SCR-018")["autonomy_level"] == "L2"
    finally:
        conn.close()


def test_l0_terminal_and_unknown_start_l1(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        assert autonomy.evaluate_autonomy(conn, "script", "SCR-DISABLE-PROTECTION")["recommended"] == "L0"
        assert autonomy.evaluate_autonomy(conn, "script", "NOPE") == {
            "current": "L1", "recommended": "L1",
            "reasons": ["unknown entity starts at L1"]}
    finally:
        conn.close()


def test_approval_lifecycle_and_expiry(tmp_path) -> None:
    from datetime import datetime, timedelta, timezone

    conn = _conn(tmp_path)
    try:
        first = approvals.request_approval(conn, "C1", "SCR-INSTALL", "commander")
        assert first["state"] == "PENDING"
        assert approvals.request_approval(conn, "C1", "SCR-INSTALL", "commander")["approval_id"] == first["approval_id"]
        decided = approvals.approve(conn, first["approval_id"], "manager")
        assert decided["state"] == "APPROVED"
        try:
            approvals.approve(conn, first["approval_id"], "manager")
            raise AssertionError("double-approve must raise")
        except ValueError:
            pass
        second = approvals.request_approval(conn, "C2", "SCR-INSTALL", "commander")
        assert approvals.deny(conn, second["approval_id"], "manager")["state"] == "DENIED"
        stale = approvals.request_approval(conn, "C3", "SCR-INSTALL", "commander")
        old = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
        conn.execute("UPDATE approvals SET requested_at=? WHERE approval_id=?",
                     (old, stale["approval_id"]))
        conn.commit()
        assert approvals.expire_stale(conn, older_than_hours=24) == 1
        assert approvals.get_approval(conn, stale["approval_id"])["state"] == "EXPIRED"
        assert approvals.expire_stale(conn, older_than_hours=24) == 0
    finally:
        conn.close()
