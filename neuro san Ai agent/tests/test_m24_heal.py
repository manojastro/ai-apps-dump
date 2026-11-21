"""M24 tests: proactive healing, approval queues, problem records."""

from __future__ import annotations

from orchestration.heal import heal_fleet

TEAMS_EVIDENCE = [{"measurement": "software_version", "entity": "Teams", "value": "3.8.4"}]


def _conn(tmp_path):
    from control_plane import registry as reg
    from database.bootstrap import get_connection, init_db
    from integrations.servicenow.simulated_itsm import SimulatedITSM
    from simulator.estate import generate_estate
    db = tmp_path / "heal.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn, generate_estate(seed=42), SimulatedITSM(seed=9)


def test_full_heal_and_problem(tmp_path) -> None:
    from integrations.servicenow import lifecycle

    conn, estate, itsm = _conn(tmp_path)
    try:
        incident = lifecycle.open_incident(itsm, conn, "CASE-FLEET", "Teams freezing")
        report = heal_fleet(conn, estate, itsm, "CASE-FLEET",
                            "Teams excessive memory after update", "SCR-018",
                            TEAMS_EVIDENCE, originating_device="DEVICE_001",
                            originating_incident_sys_id=incident.sys_id)
        assert report.matching == 27 and len(report.healed) == 27
        assert report.failed == [] and report.prevented == 26
        assert report.problem_number.startswith("PRB")
        teams = next(p.mem_mb for p in estate.get("DEVICE_005").processes if p.name == "Teams")
        assert teams == 640.0
        verified = conn.execute("SELECT COUNT(*) AS n FROM fleet_matches "
                                "WHERE case_id='CASE-FLEET' AND verified=1").fetchone()["n"]
        assert verified == 27
        assert itsm._incidents[incident.sys_id]["problem_id"] == report.problem_sys_id
    finally:
        conn.close()


def test_l2_queues_approvals_without_touching(tmp_path) -> None:
    conn, estate, itsm = _conn(tmp_path)
    try:
        report = heal_fleet(conn, estate, itsm, "CASE-VPN",
                            "Stale secure-access token", "SCR-VPN-RECONNECT")
        assert report.healed == [] and report.prevented == 0
        # Real distribution: 15 approval + 1 non-compliant blocked.
        assert report.matching == 16
        assert len(report.approval) == 15 and len(report.blocked) == 1
        assert estate.get("DEVICE_002").vpn_connected is False  # untouched
        pending = conn.execute("SELECT COUNT(*) AS n FROM approvals WHERE state='PENDING'").fetchone()["n"]
        assert pending == len(report.approval)
        assert report.problem_number.startswith("PRB")
    finally:
        conn.close()


def test_blocked_devices_reported_untouched(tmp_path) -> None:
    conn, estate, itsm = _conn(tmp_path)
    try:
        estate.get("DEVICE_003").compliance_state = "non-compliant"
        estate.get("DEVICE_004").compliance_state = "non-compliant"
        report = heal_fleet(conn, estate, itsm, "CASE-B",
                            "Teams excessive memory after update", "SCR-018", TEAMS_EVIDENCE)
        assert set(report.blocked) == {"DEVICE_003", "DEVICE_004"}
        assert len(report.healed) == 25
        assert report.prevented == 25  # no originating device in this run
        mem = next(p.mem_mb for p in estate.get("DEVICE_003").processes if p.name == "Teams")
        assert mem > 3000  # still broken, never forced
    finally:
        conn.close()


def test_tampered_registry_fails_safe(tmp_path) -> None:
    conn, estate, itsm = _conn(tmp_path)
    try:
        conn.execute("UPDATE scripts SET hash='forged' WHERE script_id='SCR-018'")
        conn.commit()
        report = heal_fleet(conn, estate, itsm, "CASE-T",
                            "Teams excessive memory after update", "SCR-018", TEAMS_EVIDENCE)
        assert report.healed == [] and len(report.failed) == 27
        assert report.prevented == 0
        assert report.problem_number.startswith("PRB")  # pattern still recorded
    finally:
        conn.close()


def test_heal_deterministic(tmp_path) -> None:
    from integrations.servicenow.simulated_itsm import SimulatedITSM
    from simulator.estate import generate_estate

    def run(case: str, path: str):
        from database.bootstrap import get_connection, init_db
        from control_plane import registry as reg
        init_db(path)
        conn = get_connection(path)
        reg.seed_registry(conn)
        try:
            return heal_fleet(conn, generate_estate(seed=42), SimulatedITSM(seed=9),
                              case, "Teams excessive memory after update", "SCR-018",
                              TEAMS_EVIDENCE, originating_device="DEVICE_001")
        finally:
            conn.close()

    first = run("CASE-D1", str(tmp_path / "d1.db"))
    second = run("CASE-D2", str(tmp_path / "d2.db"))
    assert first.healed == second.healed and first.prevented == 26
