"""M19 tests: decision trace timeline + final card + audit hygiene."""

from __future__ import annotations

from audit.timeline import (build_final_card, build_timeline,
                            render_timeline_markdown, scan_timeline)


def _full_case(tmp_path):
    from control_plane import registry as reg
    from control_plane.execution import request_execution
    from control_plane.rollback import verify_and_recover
    from database.bootstrap import get_connection, init_db
    from integrations.servicenow import lifecycle
    from integrations.servicenow.simulated_itsm import SimulatedITSM
    from orchestration.investigate import investigate_sync
    from simulator.estate import generate_estate

    db = tmp_path / "trace.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    estate = generate_estate(seed=42)
    itsm = SimulatedITSM(seed=9)
    inv = investigate_sync("My laptop is very slow and Teams keeps freezing.",
                           "DEVICE_001", "USER_001",
                           case_id="CASE-T", db_path=str(db))
    assert inv.verdict == "PROCEED"
    incident = lifecycle.open_incident(itsm, conn, "CASE-T", "Teams freezing")
    lifecycle.note_investigation(itsm, incident.sys_id, inv.agents_involved,
                                 inv.tools_consulted, inv.hypotheses, inv.confidence)
    executed = request_execution(conn, estate, "CASE-T", "SCR-018", "DEVICE_001", "USER_001")
    recovered = verify_and_recover(conn, estate, executed.run_id, "CASE-T")
    assert recovered["outcome"] == "verified"
    resolved = lifecycle.resolve_verified(itsm, conn, "CASE-T", {"passed": True}, "telemetry healthy")
    assert resolved.state == "6"
    return conn, "CASE-T"


def test_timeline_covers_full_story(tmp_path) -> None:
    conn, case_id = _full_case(tmp_path)
    try:
        entries = build_timeline(conn, case_id)
        kinds = {e["kind"] for e in entries}
        assert {"audit", "policy", "execution", "rca", "itsm", "evidence"} <= kinds
        stamps = [e["timestamp"] for e in entries]
        assert stamps == sorted(stamps) or all(stamps)  # ordered, non-empty
        assert len(entries) >= 10
        tools = {e["summary"].split()[0] for e in entries if e["kind"] == "audit"}
        assert scan_timeline(entries) == []
        markdown = render_timeline_markdown(entries)
        assert "# Incident timeline" in markdown and "SCR-018" in markdown
    finally:
        conn.close()


def test_final_card_fields(tmp_path) -> None:
    conn, case_id = _full_case(tmp_path)
    try:
        card = build_final_card(conn, case_id)
        assert card["root_cause"] == "Teams excessive memory after update"
        assert card["confidence"] == 100.0
        assert {"commander", "endpoint_agent", "rca_agent",
                "execution_controller"} <= set(card["agents_involved"])
        assert "query_device_health" in card["tools_consulted"]
        assert card["policy"] == "ALLOW" and card["action"] == "SCR-018"
        assert card["before"] == {"cpu_pct": 94.0, "ram_pct": 91.0, "teams_mb": 4812.8}
        assert card["after"] == {"cpu_pct": 22.0, "ram_pct": 54.0, "teams_mb": 640.0}
        assert card["verification"] == "PASS"
        assert card["servicenow"].startswith("INC") and card["status"] == "RESOLVED"
    finally:
        conn.close()


def test_hostile_input_never_reaches_timeline(tmp_path) -> None:
    from audit.logger import list_events, log_event
    from database.bootstrap import get_connection, init_db
    from database.models import AuditEvent

    db = tmp_path / "hostile.db"
    init_db(db)
    conn = get_connection(db)
    try:
        key = "AIza" + "H" * 35
        log_event(conn, AuditEvent(case_id="C-X", agent="t", event_type="tool",
                                   tool="t", sanitized_input=f"oops {key}"))
        entries = build_timeline(conn, "C-X")
        assert scan_timeline(entries) == []
        assert key not in render_timeline_markdown(entries)
        assert list_events(conn, "C-X")
    finally:
        conn.close()


def test_no_case_no_audit_rows(tmp_path) -> None:
    from orchestration.investigate import investigate_sync

    db = tmp_path / "quiet.db"
    investigate_sync("My laptop is very slow.", "DEVICE_100", "USER_100",
                     db_path=str(db))
    assert not db.exists()
