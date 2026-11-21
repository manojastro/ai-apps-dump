"""M23 tests: fleet signature, search states, per-device classification."""

from __future__ import annotations

from orchestration.fleet import (classify_fleet, derive_failure_signature,
                                 scan_fleet, search_fleet_for_signature)


def _conn(tmp_path):
    from control_plane import registry as reg
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "fleet.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def test_derive_signatures() -> None:
    assert derive_failure_signature("Teams excessive memory after update")["signature"] == "teams_memory"
    assert derive_failure_signature("Stale secure-access token")["signature"] == "vpn_stale_token"
    assert derive_failure_signature("Disk exhaustion")["signature"] == "disk_pressure"
    assert derive_failure_signature("Printer on fire")["signature"] == "unknown_cause"
    derived = derive_failure_signature("Teams excessive memory after update",
                                       [{"measurement": "software_version", "entity": "Teams",
                                         "value": "3.8.4"}])
    assert derived["version"] == "3.8.4"


def test_search_teams_cohort(tmp_path) -> None:
    from simulator.estate import generate_estate

    estate = generate_estate(seed=42)
    matches = search_fleet_for_signature(estate, "teams_memory", "3.8.4")
    assert len(matches) == 27
    assert all(m["match_state"] == "affected" for m in matches)
    assert matches[0]["device_id"] == "DEVICE_001"
    healthy = search_fleet_for_signature(generate_estate(seed=42), "teams_memory", "3.8.4")
    assert "DEVICE_100" not in {m["device_id"] for m in healthy}
    again = search_fleet_for_signature(generate_estate(seed=42), "teams_memory", "3.8.4")
    assert [m["device_id"] for m in again] == [m["device_id"] for m in matches]


def test_search_vpn_states(tmp_path) -> None:
    from simulator.estate import generate_estate

    estate = generate_estate(seed=42)
    matches = {m["device_id"]: m["match_state"]
               for m in search_fleet_for_signature(estate, "vpn_stale_token")}
    assert matches["DEVICE_002"] == "affected"
    assert set(matches.values()) <= {"affected", "early"}


def test_classify_partitions_and_blocks_noncompliant(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    try:
        matches = search_fleet_for_signature(estate, "teams_memory", "3.8.4")
        scan = classify_fleet(conn, estate, "CASE-F", "teams_memory", "SCR-018", matches)
        assert scan.matching == 27 and scan.scanned == 500
        assert len(scan.auto) + len(scan.approval) + len(scan.blocked) == 27
        assert not set(scan.auto) & set(scan.blocked)
        for device_id in scan.blocked:
            assert estate.get(device_id).compliance_state != "compliant"
        rows = conn.execute("SELECT * FROM fleet_matches WHERE case_id='CASE-F'").fetchall()
        assert len(rows) == 27
        # Per-device evaluation: flipping posture moves the bucket.
        target = scan.auto[0]
        estate.get(target).compliance_state = "non-compliant"
        rescan = classify_fleet(conn, estate, "CASE-F2", "teams_memory", "SCR-018", matches)
        assert target in rescan.blocked and target not in rescan.auto
    finally:
        conn.close()


def test_scan_entry_point(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    try:
        scan = scan_fleet(conn, estate, "CASE-S", "Teams excessive memory after update",
                          "SCR-018", [{"measurement": "software_version", "entity": "Teams",
                                       "value": "3.8.4"}])
        assert scan.signature == "teams_memory" and scan.matching == 27
    finally:
        conn.close()
