"""M27 tests: every KPI computed from rows (nothing staged)."""

from __future__ import annotations

from audit.timeline import build_final_card
from metrics.compute import compute_metrics, render_markdown


def _story(tmp_path):
    from control_plane import learning, registry as reg
    from control_plane.execution import request_execution
    from control_plane.rollback import verify_and_recover
    from database.bootstrap import get_connection, init_db
    from integrations.servicenow import lifecycle
    from integrations.servicenow.simulated_itsm import SimulatedITSM
    from orchestration.heal import heal_fleet
    from orchestration.investigate import investigate_sync
    from simulator.estate import generate_estate

    db = tmp_path / "kpi.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    estate = generate_estate(seed=42)
    itsm = SimulatedITSM(seed=9)
    inv = investigate_sync("My laptop is very slow and Teams keeps freezing.",
                           "DEVICE_001", "USER_001", case_id="CASE-A", db_path=str(db))
    assert inv.verdict == "PROCEED"
    incident = lifecycle.open_incident(itsm, conn, "CASE-A", "Teams freezing")
    executed = request_execution(conn, estate, "CASE-A", "SCR-018", "DEVICE_001", "USER_001")
    assert verify_and_recover(conn, estate, executed.run_id, "CASE-A")["outcome"] == "verified"
    lifecycle.resolve_verified(itsm, conn, "CASE-A", {"passed": True}, "healthy")
    investigate_sync("How do I claim internet reimbursement?",
                     "DEVICE_001", "USER_001", case_id="CASE-K", db_path=str(db))
    heal_fleet(conn, estate, itsm, "CASE-FLEET", "Teams excessive memory after update",
               "SCR-018", [{"measurement": "software_version", "entity": "Teams", "value": "3.8.4"}],
               originating_device="DEVICE_001")
    learning.record_resolution(conn, "CASE-A", "teams_memory", ["ram"], "Teams memory",
                               "SCR-018", success=True)
    learning.record_resolution(conn, "CASE-OLD", "teams_memory", ["ram"], "Teams memory",
                               "SCR-018", success=True, reopen=True)
    return conn


def test_metrics_match_reality(tmp_path) -> None:
    conn = _story(tmp_path)
    try:
        metrics = compute_metrics(conn)
        assert metrics["requests_handled"] == 3  # CASE-A, CASE-K, CASE-FLEET
        assert metrics["technical_cases"] == 1 and metrics["knowledge_cases"] == 1
        assert metrics["incidents_resolved"] == 1 and metrics["auto_resolved"] == 1
        assert metrics["automation_rate"] == 1.0
        # CASE-A already fixed DEVICE_001, so the fleet finds 26 affected to
        # heal plus the originator itself sitting at-risk (approval watch).
        assert metrics["healed_devices"] == 26 and metrics["tickets_prevented"] == 26
        assert metrics["policy_denies"] == 0
        assert metrics["reopened"] == 1
        assert metrics["remediation_success_rate"] == 1.0
        assert metrics["verification_rate"] == 1.0
        assert metrics["engineer_minutes_saved_estimate"] == 26 * 20 + 1 * 30
        text = render_markdown(metrics)
        assert "- healed_devices: 26" in text and "- tickets_prevented: 26" in text
    finally:
        conn.close()


def test_metrics_move_with_data(tmp_path) -> None:
    from integrations.servicenow import lifecycle
    from integrations.servicenow.simulated_itsm import SimulatedITSM

    conn = _story(tmp_path)
    try:
        before = compute_metrics(conn)["requests_handled"]
        lifecycle.open_incident(SimulatedITSM(seed=1), conn, "CASE-NEW", "other")
        assert compute_metrics(conn)["requests_handled"] == before + 1
    finally:
        conn.close()


def test_final_card_fleet_fields(tmp_path) -> None:
    conn = _story(tmp_path)
    try:
        card = build_final_card(conn, "CASE-FLEET")
        assert card["fleet_matching"] == 27 and card["fleet_healed"] == 26
        assert card["fleet_prevented"] == 26
    finally:
        conn.close()
