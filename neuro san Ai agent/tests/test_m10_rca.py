"""M10 tests: refutation, conflicts, missing evidence, temporal links, persistence."""

from __future__ import annotations

from orchestration.rca import (diagnose, find_conflicts, missing_evidence,
                               refuting_for, temporal_links)


def _ev(eid: str, measurement: str, value: str, summary: str, entity: str = "DEVICE_001") -> dict:
    return {"evidence_id": eid, "measurement": measurement, "value": value,
            "sanitized_summary": summary, "entity": entity, "tool": "t"}


def test_refutation_rejects_red_herrings() -> None:
    disk_ok = [_ev("E1", "disk", "42.0", "Disk 42.0%")]
    assert refuting_for("Disk exhaustion", disk_ok) == ["E1"]
    teams_ok = [_ev("E1", "process_memory", "640.0", "Teams 640.0MB", entity="Teams"),
                _ev("E2", "software_version", "3.7.9", "Teams 3.7.9", entity="Teams")]
    assert sorted(refuting_for("Teams excessive memory after update", teams_ok)) == ["E1", "E2"]
    vpn_up = [_ev("E1", "vpn", "True", "VPN up: no error")]
    assert refuting_for("Stale secure-access token", vpn_up) == ["E1"]
    assert refuting_for("Teams excessive memory after update", vpn_up) == []


def test_conflict_between_performance_hypotheses() -> None:
    evidence = [_ev("E1", "process_memory", "4500.0", "Teams 4500.0MB", entity="Teams"),
                _ev("E2", "disk", "92.0", "Disk 92.0%")]
    result = diagnose(evidence)
    assert result.verdict == "ESCALATE"
    assert result.conflicts == [["Disk exhaustion", "Teams excessive memory after update"]]
    assert {h["status"] for h in result.hypotheses} == {"SUPPORTED"}


def test_vpn_does_not_conflict_with_performance() -> None:
    evidence = [_ev("E1", "process_memory", "4500.0", "Teams 4500.0MB", entity="Teams"),
                _ev("E2", "vpn", "False", "VPN DOWN: stale cached token")]
    result = diagnose(evidence)
    assert result.conflicts == []
    assert find_conflicts(result.hypotheses) == []


def test_missing_mandatory_evidence_blocks() -> None:
    pressured = [_ev("E1", "ram", "91.0", "RAM 91.0%")]
    assert missing_evidence(pressured) == ["process breakdown"]
    # No candidate yet AND a named gap: abstain (maps to ESCALATE upstream).
    abstained = diagnose(pressured)
    assert abstained.verdict == "INSUFFICIENT"
    assert abstained.missing == ["process breakdown"]
    vpn_only = [_ev("E1", "vpn", "False", "VPN DOWN: stale")]
    assert missing_evidence(vpn_only) == ["identity correlation"]
    complete = [_ev("E1", "vpn", "False", "VPN DOWN: stale"),
                _ev("E2", "signin", "success", "password_reset success")]
    assert missing_evidence(complete) == []


def test_temporal_links_change_to_symptom() -> None:
    evidence = [_ev("E1", "change", "Teams updated 3.7.9 to 3.8.4",
                    "Change: Teams updated 3.7.9 to 3.8.4", entity="Teams"),
                _ev("E2", "process_memory", "4812.8", "Teams 4812.8MB", entity="Teams"),
                _ev("E3", "disk", "42.0", "Disk 42.0%")]
    links = temporal_links(evidence)
    assert len(links) == 1
    assert links[0]["change_id"] == "E1" and "E2" in links[0]["symptom_ids"]
    assert "E3" not in links[0]["symptom_ids"]


def test_empty_evidence_abstains() -> None:
    result = diagnose([])
    assert result.verdict == "INSUFFICIENT"
    assert result.hypotheses == [] and result.top_confidence == 0.0


def test_hypotheses_persist_ranked(tmp_path) -> None:
    from database.bootstrap import get_connection, init_db
    from evidence.store import ensure_case, list_hypotheses, save_hypotheses

    db = tmp_path / "hyp.db"
    init_db(db)
    conn = get_connection(db)
    try:
        ensure_case(conn, "CASE-H")
        result = diagnose([_ev("E1", "process_memory", "4812.8", "Teams 4812.8MB", entity="Teams")])
        ids = save_hypotheses(conn, "CASE-H", result.hypotheses)
        assert ids == ["CASE-H-H01"]
        rows = list_hypotheses(conn, "CASE-H")
        assert rows[0]["title"] == "Teams excessive memory after update"
        assert rows[0]["confidence"] == 100.0 and rows[0]["status"] == "SUPPORTED"
        rerun = save_hypotheses(conn, "CASE-H", result.hypotheses)
        assert rerun == ids and len(list_hypotheses(conn, "CASE-H")) == 1
    finally:
        conn.close()


def test_investigate_stores_hypotheses(tmp_path) -> None:
    from database.bootstrap import get_connection
    from evidence.store import list_hypotheses
    from orchestration.investigate import investigate_sync

    db = tmp_path / "rca.db"
    inv = investigate_sync("My laptop is very slow and Teams keeps freezing.",
                           "DEVICE_001", "USER_001",
                           case_id="CASE-R", db_path=str(db))
    assert inv.verdict == "PROCEED"
    conn = get_connection(db)
    try:
        rows = list_hypotheses(conn, "CASE-R")
        assert len(rows) == 1 and rows[0]["status"] == "SUPPORTED"
    finally:
        conn.close()
