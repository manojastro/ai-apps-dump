"""M16 tests: policy-gated execution (refuse-first, execute-last)."""

from __future__ import annotations

import json

from control_plane import approvals
from control_plane import registry as reg
from control_plane.execution import AWAITING, EXECUTED, REFUSED, request_execution
from simulator.actions import snapshot
from simulator.estate import generate_estate


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "ex.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn, generate_estate(seed=42)


def test_l3_executes_and_mutates_demo_state(tmp_path) -> None:
    conn, estate = _conn(tmp_path)
    before = snapshot("DEVICE_001", estate)
    result = request_execution(conn, estate, "CASE-EX", "SCR-018", "DEVICE_001", "USER_001")
    assert result.status == EXECUTED and result.policy_decision == "ALLOW"
    assert result.effect == {"cpu_pct": 22.0, "ram_pct": 54.0, "teams_mb": 640.0}
    after = json.loads(snapshot("DEVICE_001", estate))
    assert (after["cpu_pct"], after["ram_pct"], after["teams_mb"]) == (22.0, 54.0, 640.0)
    assert after["issues"] == []
    run = conn.execute("SELECT * FROM remediation_runs WHERE run_id=?",
                       (result.run_id,)).fetchone()
    assert json.loads(run["before_state"]) == json.loads(before)
    assert run["success"] == 1 and run["verification_result"] == ""
    assert reg.lookup_script(conn, "SCR-018")["execution_count"] == 96
    audit = conn.execute("SELECT * FROM audit_events WHERE action='SCR-018'").fetchall()
    assert len(audit) == 1 and audit[0]["tool"] == "execute_remote_action"
    assert conn.execute("SELECT COUNT(*) AS n FROM policy_decisions").fetchone()["n"] >= 1
    conn.close()


def test_refusals_touch_nothing(tmp_path) -> None:
    conn, estate = _conn(tmp_path)
    try:
        pristine = snapshot("DEVICE_001", generate_estate(seed=42))
        assert snapshot("DEVICE_001", estate) == pristine
        assert request_execution(conn, estate, "C", "SCR-NOPE", "DEVICE_001", "U").status == REFUSED
        assert request_execution(conn, estate, "C", "SCR-FIREWALL", "DEVICE_001", "U").status == REFUSED  # L1
        assert request_execution(conn, estate, "C", "SCR-DISABLE-PROTECTION", "DEVICE_001", "U").status == REFUSED
        assert request_execution(conn, estate, "C", "SCR-018", "DEVICE_999", "U").status == REFUSED
        assert snapshot("DEVICE_001", estate) == pristine
        conn.execute("UPDATE scripts SET hash='forged' WHERE script_id='SCR-018'")
        assert request_execution(conn, estate, "C", "SCR-018", "DEVICE_001", "U").status == REFUSED
        conn.execute("UPDATE scripts SET hash=? WHERE script_id='SCR-018'",
                     (reg.canonical_hash("SCR-018", "3.2", "windows", "Clear Teams Cache"),))
        conn.commit()
        estate.devices["DEVICE_001"].compliance_state = "non-compliant"
        assert request_execution(conn, estate, "C", "SCR-018", "DEVICE_001", "U").status == REFUSED
        assert conn.execute("SELECT COUNT(*) AS n FROM remediation_runs").fetchone()["n"] == 0
    finally:
        conn.close()


def test_l2_approval_flow(tmp_path) -> None:
    conn, estate = _conn(tmp_path)
    try:
        waiting = request_execution(conn, estate, "CASE-L2", "SCR-VPN-RECONNECT",
                                    "DEVICE_002", "USER_002")
        assert waiting.status == AWAITING and waiting.approval_id
        assert estate.devices["DEVICE_002"].vpn_connected is False  # untouched
        approvals.deny(conn, waiting.approval_id, "manager")
        assert request_execution(conn, estate, "CASE-L2", "SCR-VPN-RECONNECT",
                                 "DEVICE_002", "USER_002").status == REFUSED
        conn.execute("DELETE FROM approvals WHERE approval_id=?", (waiting.approval_id,))
        conn.commit()
        waiting2 = request_execution(conn, estate, "CASE-L2", "SCR-VPN-RECONNECT",
                                     "DEVICE_002", "USER_002")
        approvals.approve(conn, waiting2.approval_id, "manager")
        done = request_execution(conn, estate, "CASE-L2", "SCR-VPN-RECONNECT",
                                 "DEVICE_002", "USER_002")
        assert done.status == EXECUTED
        assert estate.devices["DEVICE_002"].vpn_connected is True
    finally:
        conn.close()


def test_effect_params_and_wrapper(tmp_path) -> None:
    import tests.conftest  # noqa: F401
    from coded_tools.digital_workplace.control import ExecuteRemoteAction
    import asyncio

    conn, estate = _conn(tmp_path)
    try:
        missing = request_execution(conn, estate, "C", "SCR-RESTART-APP",
                                    "DEVICE_001", "U", params={})
        assert missing.status == REFUSED and "app" in missing.reasons[0]
        out = asyncio.run(ExecuteRemoteAction().async_invoke(
            {"action_id": "SCR-018", "device_id": "DEVICE_001",
             "user_id": "USER_001", "db_path": str(tmp_path / "wrap.db")}, {}))
        assert out["status"] == EXECUTED and out["effect"]["teams_mb"] == 640.0
    finally:
        conn.close()
