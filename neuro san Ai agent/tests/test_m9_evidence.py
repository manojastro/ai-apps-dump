"""M9 tests: normalized evidence shape, units, confidence, store, persist."""

from __future__ import annotations

import sqlite3

import pytest

from evidence.normalize import normalize
from evidence.store import SPEC_FIELDS, ensure_case, list_evidence, save_evidence


def _db(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "ev.db"
    init_db(db)
    return get_connection(db)


def test_spec_shape_units_confidence() -> None:
    records = normalize("query_device_health",
                        {"cpu_pct": 94.0, "ram_pct": 91.0, "disk_pct": 42.0},
                        case_id="C-1", device_id="DEVICE_001")
    assert len(records) == 3
    first = records[0]
    assert list(first) == list(SPEC_FIELDS)  # exact spec order
    assert first["evidence_id"] == "E1" and first["case_id"] == "C-1"
    assert first["source_system"] == "nexthink" and first["tool"] == "query_device_health"
    assert first["timestamp"] and first["entity"] == "DEVICE_001"
    assert first["unit"] == "%" and first["confidence"] == 0.9
    assert first["raw_reference"] and first["sanitized_summary"] == "CPU 94.0%"

    mem = normalize("query_tanium", {"processes": [{"name": "Teams", "mem_mb": 4812.8}]})
    assert mem[0]["unit"] == "MB" and mem[0]["confidence"] == 0.95

    net = normalize("query_network_path", {"path_ok": True, "latency_ms": 35.0, "loss_pct": 0.1})
    assert net[0]["unit"] == "ms"

    catalog = normalize("query_software_catalog", {"items": []})
    assert catalog == []  # catalog listings are not telemetry evidence


def test_source_mapping_and_start_offset() -> None:
    vpn = normalize("query_vpn_state", {"connected": False, "last_error": "stale"},
                    device_id="DEVICE_002", start=5)
    assert vpn[0]["evidence_id"] == "E5"
    assert vpn[0]["source_system"] == "zscaler"
    assert vpn[0]["measurement"] == "vpn"
    ident = normalize("query_account_state",
                      {"account_state": "active", "locked": False, "user_id": "U"})
    assert ident[0]["source_system"] == "entra"


def test_hostile_values_redacted_everywhere() -> None:
    key = "AIza" + "Q" * 35
    records = normalize("query_processes",
                        {"processes": [{"name": f"evil {key}", "mem_mb": 10}]})
    assert len(records) == 1
    assert key not in records[0]["raw_reference"]
    assert key not in records[0]["sanitized_summary"]
    assert key not in records[0]["value"]
    assert "[REDACTED]" in records[0]["raw_reference"]


def test_store_roundtrip_idempotent(tmp_path) -> None:
    conn = _db(tmp_path)
    try:
        ensure_case(conn, "CASE-1", "USER_001", "DEVICE_001", "slow")
        records = normalize("query_device_health",
                            {"cpu_pct": 94.0, "ram_pct": 91.0, "disk_pct": 42.0},
                            case_id="CASE-1", device_id="DEVICE_001")
        ids = save_evidence(conn, "CASE-1", records)
        assert ids == ["CASE-1-E001", "CASE-1-E002", "CASE-1-E003"]
        rows = list_evidence(conn, "CASE-1")
        assert [r["evidence_id"] for r in rows] == ids
        assert rows[0]["measurement"] == "cpu" and rows[0]["unit"] == "%"
        assert rows[0]["source_system"] == "nexthink"
        rerun = save_evidence(conn, "CASE-1", records)  # deterministic rerun
        assert rerun == ids
        assert len(list_evidence(conn, "CASE-1")) == 3
    finally:
        conn.close()


def test_store_requires_parent_case(tmp_path) -> None:
    conn = _db(tmp_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            save_evidence(conn, "GHOST",
                           normalize("query_dns", {"dns_ok": True}, case_id="GHOST"))
    finally:
        conn.close()


def test_investigate_persists_normalized_batch(tmp_path) -> None:
    from database.bootstrap import get_connection
    from orchestration.investigate import investigate_sync

    db = tmp_path / "inv.db"
    inv = investigate_sync("My laptop is very slow and Teams keeps freezing.",
                           "DEVICE_001", "USER_001", case_id="CASE-9", db_path=str(db))
    assert inv.verdict == "PROCEED"
    assert inv.stored_ids and inv.stored_ids[0] == "CASE-9-E001"
    conn = get_connection(db)
    try:
        rows = list_evidence(conn, "CASE-9")
        assert len(rows) == len(inv.stored_ids)
        by_measure = {r["measurement"] for r in rows}
        assert {"cpu", "ram", "process_memory", "change"} <= by_measure
        assert all(r["case_id"] == "CASE-9" for r in rows)
    finally:
        conn.close()


def test_investigate_without_case_stores_nothing(tmp_path) -> None:
    from orchestration.investigate import investigate_sync

    inv = investigate_sync("My laptop is very slow and Teams keeps freezing.",
                           db_path=str(tmp_path / "nope.db"))
    assert inv.stored_ids == []
    assert not (tmp_path / "nope.db").exists()
