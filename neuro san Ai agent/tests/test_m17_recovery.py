"""M17 tests: fresh-telemetry verification, rollback, escalation."""

from __future__ import annotations

import json

from control_plane import registry as reg
from control_plane.execution import EXECUTED, request_execution
from control_plane.rollback import (ESCALATE, ROLLED_BACK, VERIFIED,
                                    verify_and_recover)
from control_plane.verification import capture_state, verify_remediation
from simulator.estate import generate_estate


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "rec.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def _executed(tmp_path):
    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    result = request_execution(conn, estate, "CASE-V", "SCR-018", "DEVICE_001", "USER_001")
    assert result.status == EXECUTED
    return conn, estate, result.run_id


def test_verify_passes_on_fresh_telemetry(tmp_path) -> None:
    conn, estate, run_id = _executed(tmp_path)
    try:
        outcome = verify_and_recover(conn, estate, run_id, "CASE-V")
        assert outcome["outcome"] == VERIFIED and outcome["failed"] == []
        row = conn.execute("SELECT verification_result FROM remediation_runs "
                           "WHERE run_id=?", (run_id,)).fetchone()
        assert json.loads(row["verification_result"])["passed"] is True
        # Two independent sources behind the verdict.
        after = capture_state(estate, "DEVICE_001", "SCR-018")
        assert after["health"]["cpu_pct"] == 22.0
        assert after["teams"]["mem_mb"] == 640.0
    finally:
        conn.close()


def test_failed_verify_rolls_back_and_reproves(tmp_path) -> None:
    conn, estate, run_id = _executed(tmp_path)
    try:
        before = json.loads(conn.execute("SELECT before_state FROM remediation_runs "
                                         "WHERE run_id=?", (run_id,)).fetchone()["before_state"])
        sabotaged = estate.get("DEVICE_001")
        sabotaged.cpu_pct = 97.0
        sabotaged.ram_pct = 96.0
        next(p for p in sabotaged.processes if p.name == "Teams").mem_mb = 4600.0
        outcome = verify_and_recover(conn, estate, run_id, "CASE-V")
        assert outcome["outcome"] == ROLLED_BACK
        assert set(outcome["failed"]) == {"cpu_recovered", "ram_recovered", "teams_healthy"}
        live = json.loads(__import__("simulator.actions", fromlist=["snapshot"]).snapshot("DEVICE_001", estate))
        assert live["cpu_pct"] == before["cpu_pct"] and live["teams_mb"] == before["teams_mb"]
        row = conn.execute("SELECT rollback_run_id FROM remediation_runs WHERE run_id=?",
                           (run_id,)).fetchone()
        assert row["rollback_run_id"] == outcome["rollback_run_id"]
        script = reg.lookup_script(conn, "SCR-018")
        assert script["failure_count"] == 2 and script["rollback_count"] == 2
        kinds = {r["event_type"] for r in
                 conn.execute("SELECT event_type FROM audit_events").fetchall()}
        assert {"verification", "rollback"} <= kinds
    finally:
        conn.close()


def test_no_rollback_means_escalate(tmp_path) -> None:
    conn, estate, run_id = _executed(tmp_path)
    try:
        conn.execute("UPDATE scripts SET rollback_available=0 WHERE script_id='SCR-018'")
        conn.commit()
        sabotaged = estate.get("DEVICE_001")
        sabotaged.cpu_pct = 97.0
        sabotaged.ram_pct = 96.0
        next(p for p in sabotaged.processes if p.name == "Teams").mem_mb = 4600.0
        outcome = verify_and_recover(conn, estate, run_id, "CASE-V")
        assert outcome["outcome"] == ESCALATE
        assert outcome["escalation_target"] == "support-queue"
        assert "rollback" in outcome["reason"]
    finally:
        conn.close()


def test_unknown_run_and_install_params(tmp_path) -> None:
    import pytest

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    try:
        with pytest.raises(LookupError):
            verify_and_recover(conn, estate, "RUN-NOPE")
        ok = verify_remediation({}, {"apps": [{"app_id": "APP-VideoEditor", "healthy": True}]},
                                "SCR-INSTALL", {"app": "VideoEditor"})
        assert ok.passed
        missing = verify_remediation({}, {"apps": [{"app_id": "APP-Other", "healthy": True}]},
                                     "SCR-INSTALL", {"app": "VideoEditor"})
        assert not missing.passed
    finally:
        conn.close()
