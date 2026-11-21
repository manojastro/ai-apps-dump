"""M18 tests: lifecycle composer + full execute→verify→ITSM chains (sim ITSM)."""

from __future__ import annotations

import pytest

from control_plane.execution import EXECUTED, request_execution
from control_plane.rollback import ROLLED_BACK, VERIFIED, verify_and_recover
from integrations.servicenow import lifecycle
from integrations.servicenow.simulated_itsm import SimulatedITSM


def _conn(tmp_path):
    from control_plane import registry as reg
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "lc.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def test_open_idempotent_and_resolve_gated(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, itsm = _conn(tmp_path), SimulatedITSM(seed=9)
    estate = generate_estate(seed=42)
    try:
        first = lifecycle.open_incident(itsm, conn, "CASE-A", "slow laptop")
        second = lifecycle.open_incident(itsm, conn, "CASE-A", "slow laptop")
        assert first.number == second.number
        assert conn.execute("SELECT COUNT(*) AS n FROM incidents").fetchone()["n"] == 1
        lifecycle.note_investigation(itsm, first.sys_id, ["endpoint_agent"],
                                     ["query_device_health"], [], 0.0)
        with pytest.raises(ValueError):
            lifecycle.resolve_verified(itsm, conn, "CASE-A", {"passed": False,
                                                              "failed": ["cpu"]}, "x")
        assert itsm.get_incident(first.sys_id).state == "New"
    finally:
        conn.close()


def test_happy_chain_resolves(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate, itsm = _conn(tmp_path), generate_estate(seed=42), SimulatedITSM(seed=9)
    try:
        incident = lifecycle.open_incident(itsm, conn, "CASE-H", "Teams freezing")
        executed = request_execution(conn, estate, "CASE-H", "SCR-018", "DEVICE_001", "USER_001")
        assert executed.status == EXECUTED
        recovered = verify_and_recover(conn, estate, executed.run_id, "CASE-H")
        assert recovered["outcome"] == VERIFIED
        resolved = lifecycle.resolve_verified(
            itsm, conn, "CASE-H", {"passed": True, "checks": []}, "cache cleared, telemetry healthy")
        assert resolved.state == "6"
        row = conn.execute("SELECT state FROM incidents WHERE case_id='CASE-H'").fetchone()
        assert row["state"] == "6"
    finally:
        conn.close()


def test_fail_chain_rolls_back_and_escalates(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate, itsm = _conn(tmp_path), generate_estate(seed=42), SimulatedITSM(seed=9)
    try:
        incident = lifecycle.open_incident(itsm, conn, "CASE-F", "Teams freezing")
        executed = request_execution(conn, estate, "CASE-F", "SCR-018", "DEVICE_001", "USER_001")
        broken = estate.get("DEVICE_001")
        broken.cpu_pct = 97.0
        broken.ram_pct = 96.0
        next(p for p in broken.processes if p.name == "Teams").mem_mb = 4600.0
        recovered = verify_and_recover(conn, estate, executed.run_id, "CASE-F")
        assert recovered["outcome"] == ROLLED_BACK
        escalated = lifecycle.escalate_recovery(
            itsm, conn, "CASE-F", "verification failed after rollback",
            recovered["failed"], str(recovered.get("rollback_run_id")))
        row = conn.execute("SELECT state, priority FROM incidents WHERE case_id='CASE-F'").fetchone()
        assert row["priority"] == "1"
        assert escalated.number == incident.number
    finally:
        conn.close()


def test_problem_links_incidents(tmp_path) -> None:
    conn, itsm = _conn(tmp_path), SimulatedITSM(seed=9)
    try:
        a = lifecycle.open_incident(itsm, conn, "CASE-1", "slow a")
        b = lifecycle.open_incident(itsm, conn, "CASE-2", "slow b")
        problem = lifecycle.open_problem(itsm, conn, "Teams 3.8.4 regression",
                                         "fleet pattern", [a.sys_id, b.sys_id])
        assert problem.number.startswith("PRB")
    finally:
        conn.close()
