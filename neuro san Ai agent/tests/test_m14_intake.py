"""M14 tests: AI-generated script pipeline (validate → review → register)."""

from __future__ import annotations

import json

import pytest

from control_plane import registry as reg
from control_plane import script_intake as intake


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "intake.db"
    init_db(db)
    return get_connection(db)


def _stages(conn, proposal_id: str) -> list[dict]:
    return json.loads(intake.get_proposal(conn, proposal_id)["findings"])


def test_happy_path_registers(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        intake.propose(conn, "PROP-1", "SCR-CUSTOM-CACHE", "Custom cache clear",
                       primitives=["clear_temp"], risk_claimed="LOW",
                       autonomy_claimed="L3", rollback_available=True, owner="ops")
        validated = intake.validate_proposal(conn, "PROP-1")
        assert validated["status"] == "validated"
        assert all(s["passed"] for s in _stages(conn, "PROP-1"))
        assert intake.request_review(conn, "PROP-1")["status"] == "in_review"
        registered = intake.approve_review(conn, "PROP-1", "change-advisory-board")
        assert registered["status"] == "registered"
        row = reg.lookup_script(conn, "SCR-CUSTOM-CACHE")
        assert row["approved"] == 1 and row["version"] == "1.0"
        assert reg.verify_stored_hash(row)
        assert reg.get_approved_action(conn, "SCR-CUSTOM-CACHE") is not None
    finally:
        conn.close()


def test_forbidden_secret_privilege_risk_rejected(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        intake.propose(conn, "PROP-F", "SCR-BAD-CMD", "bad",
                       primitives=["disable_protection"])
        assert intake.validate_proposal(conn, "PROP-F")["status"] == "denied"
        intake.propose(conn, "PROP-S", "SCR-BAD-SEC", "bad",
                       description="leaked key AIza" + "Q" * 35,
                       primitives=["clear_temp"])
        assert intake.validate_proposal(conn, "PROP-S")["status"] == "denied"
        intake.propose(conn, "PROP-L", "SCR-BAD-L4", "bad",
                       primitives=["clear_temp"], autonomy_claimed="L4")
        assert intake.validate_proposal(conn, "PROP-L")["status"] == "denied"
        intake.propose(conn, "PROP-R", "SCR-BAD-RISK", "bad",
                       primitives=["reconnect_vpn"], risk_claimed="LOW",
                       autonomy_claimed="L2")
        assert intake.validate_proposal(conn, "PROP-R")["status"] == "denied"
    finally:
        conn.close()


def test_no_skip_no_self_register(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        intake.propose(conn, "PROP-9", "SCR-SKIP-1", "skip",
                       primitives=["clear_temp"])
        with pytest.raises(ValueError):
            intake.request_review(conn, "PROP-9")  # not validated yet
        intake.validate_proposal(conn, "PROP-9")
        with pytest.raises(ValueError):
            intake.approve_review(conn, "PROP-9", "cab")  # not in review
        assert reg.lookup_script(conn, "SCR-SKIP-1") is None  # never registered
        intake.request_review(conn, "PROP-9")
        rejected = intake.reject_review(conn, "PROP-9", "cab", "not needed")
        assert rejected["status"] == "denied"
        assert reg.lookup_script(conn, "SCR-SKIP-1") is None
    finally:
        conn.close()


def test_bad_ids_rejected_and_sandbox_untouched(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn = _conn(tmp_path)
    try:
        with pytest.raises(ValueError):
            intake.propose(conn, "P", "rm -rf /", "bad", primitives=["clear_temp"])
        intake.propose(conn, "P", "SCR-DUP-1", "bad", primitives=["nonsense"])
        assert intake.validate_proposal(conn, "P")["status"] == "denied"
        estate = generate_estate(seed=42)  # sandbox ran above; source estate intact
        assert estate.devices["DEVICE_001"].cpu_pct == 94.0
    finally:
        conn.close()
