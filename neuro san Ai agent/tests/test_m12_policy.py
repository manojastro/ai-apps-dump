"""M12 tests: deterministic policy gate (ALLOW/DENY/REQUIRE_APPROVAL only)."""

from __future__ import annotations

import asyncio

import pytest

from control_plane.policy import (ALLOW, DENY, REQUIRE_APPROVAL, PolicyInput,
                                  evaluate, record_decision)

SCRIPTS = [
    ("SCR-018", "Clear Teams Cache", "LOW", "L3", 1, "abc123", "corporate-laptop"),
    ("SCR-INSTALL", "Install approved app", "MEDIUM", "L2", 1, "def456", "corporate-laptop"),
    ("SCR-VPN", "VPN reconnect", "MEDIUM", "L2", 1, "vpn789", "corporate-laptop"),
    ("SCR-FIREWALL", "Firewall change", "HIGH", "L1", 0, "fw000", "corporate-laptop"),
    ("SCR-DISABLE-PROTECTION", "Disable protection", "CRITICAL", "L0", 0, "bad000", "corporate-laptop"),
]


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "pol.db"
    init_db(db)
    conn = get_connection(db)
    for sid, name, risk, autonomy, rollback, digest, _group in SCRIPTS:
        conn.execute(
            "INSERT INTO scripts(script_id, name, risk, autonomy_level, "
            "rollback_available, hash, approved) VALUES (?,?,?,?,?,?,?)",
            (sid, name, risk, autonomy, rollback, digest, 1))
    conn.commit()
    return conn


def _base(action_id: str = "SCR-018", **kw) -> PolicyInput:
    defaults = dict(user_id="USER_001", user_role="employee",
                    device_id="DEVICE_038", device_group="corporate-laptop",
                    device_compliant=True, action_id=action_id)
    defaults.update(kw)
    return PolicyInput(**defaults)


def test_spec_example_allows(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        result = evaluate(conn, _base())
        assert result.decision == ALLOW
        names = [c.name for c in result.checks]
        assert names == ["user authorized", "allowed device group", "device compliant",
                         "approved script", "hash valid", "deny-list", "risk",
                         "autonomy", "business hours", "rollback support"]
        assert all(c.passed for c in result.checks)
    finally:
        conn.close()


def test_deny_paths(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        assert evaluate(conn, _base(action_id="SCR-NOPE")).decision == DENY
        assert evaluate(conn, _base(device_compliant=False)).decision == DENY
        assert evaluate(conn, _base(device_group="cafe-wifi")).decision == DENY
        assert evaluate(conn, _base(user_role="stranger")).decision == DENY
        assert evaluate(conn, _base(action_id="SCR-018", script_hash="tampered")).decision == DENY
        assert evaluate(conn, _base(action_id="SCR-DISABLE-PROTECTION")).decision == DENY
    finally:
        conn.close()


def test_approval_paths(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        assert evaluate(conn, _base(action_id="SCR-INSTALL")).decision == REQUIRE_APPROVAL
        assert evaluate(conn, _base(action_id="SCR-FIREWALL")).decision == REQUIRE_APPROVAL
        off_hours = evaluate(conn, _base(action_id="SCR-VPN", at_hour=23))
        assert off_hours.decision == REQUIRE_APPROVAL
        assert evaluate(conn, _base(action_id="SCR-VPN", at_hour=10)).decision == REQUIRE_APPROVAL
    finally:
        conn.close()


def test_deny_beats_approval_and_determinism(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        # Deny-listed AND low-autonomy: DENY wins, never softens to approval.
        result = evaluate(conn, _base(action_id="SCR-DISABLE-PROTECTION"))
        assert result.decision == DENY
        assert evaluate(conn, _base()).decision == evaluate(conn, _base()).decision == ALLOW
    finally:
        conn.close()


def test_decision_output_vocabulary_and_persistence(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        for action in ("SCR-018", "SCR-INSTALL", "SCR-NOPE"):
            assert evaluate(conn, _base(action_id=action)).decision in (
                ALLOW, DENY, REQUIRE_APPROVAL)
        decision_id = record_decision(conn, "CASE-P", _base(), evaluate(conn, _base()))
        assert decision_id.startswith("POL-CASE-P-")
        row = conn.execute("SELECT * FROM policy_decisions WHERE decision_id=?",
                           (decision_id,)).fetchone()
        assert row["decision"] == ALLOW and row["script_id"] == "SCR-018"
    finally:
        conn.close()


def test_wrapper_shape_and_no_bypass(tmp_path) -> None:
    import tests.conftest  # noqa: F401
    from coded_tools.digital_workplace.control import EvaluatePolicy

    out = asyncio.run(EvaluatePolicy().async_invoke(
        {"action_id": "SCR-NOPE", "user_id": "USER_001",
         "db_path": str(tmp_path / "wrap.db")}, {}))
    assert out["decision"] == DENY  # empty registry denies safely
    assert out["action_id"] == "SCR-NOPE" and len(out["checks"]) == 10

    # The engine must not depend on the agent framework at all: no LLM can
    # reach, influence, or bypass it. enforced by import-boundary test.
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for rel in ("control_plane/policy.py", "control_plane/registry.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "neuro_san" not in text
        assert "CodedTool" not in text
        assert "load_settings" not in text
        assert "os.environ" not in text
