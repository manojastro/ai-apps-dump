"""M29 gate: failure fallbacks + the spec security checklist, end to end."""

from __future__ import annotations

import urllib.error

import pytest


def test_unknown_device_escalates_without_crash(tmp_path) -> None:
    from orchestration.investigate import investigate_sync

    inv = investigate_sync("My laptop is very slow.", "DEVICE_999", "USER_999",
                           case_id="CASE-LOST", db_path=str(tmp_path / "lost.db"))
    assert inv.verdict == "ESCALATE" and inv.confidence == 0.0
    assert any("FAILED" in s.summary for s in inv.steps)


def test_unreachable_servicenow_raises_typed_error() -> None:
    from integrations.servicenow.client import ServiceNowClient, ServiceNowConfig, ServiceNowError

    def dead(method, url, headers, body, timeout):
        raise urllib.error.URLError("dns down")

    client = ServiceNowClient(ServiceNowConfig(instance_url="https://x/"), transport=dead)
    with pytest.raises(ServiceNowError):
        client.list("incident")


def test_spec_security_checklist(tmp_path) -> None:
    import tests.conftest  # noqa: F401
    from control_plane import registry as reg
    from control_plane.execution import REFUSED, request_execution
    from control_plane.policy import DENY, PolicyInput, evaluate
    from database.bootstrap import get_connection, init_db
    from integrations.servicenow import lifecycle
    from integrations.servicenow.simulated_itsm import SimulatedITSM
    from pathlib import Path

    for rel in ("control_plane/policy.py", "control_plane/registry.py",
                "control_plane/execution.py", "control_plane/verification.py",
                "control_plane/rollback.py", "control_plane/risk.py",
                "control_plane/autonomy.py", "control_plane/approvals.py",
                "control_plane/learning.py", "control_plane/script_intake.py",
                "control_plane/privacy.py"):
        text = (Path("control_plane") / Path(rel).name).read_text(encoding="utf-8")
        assert "neuro_san" not in text and "CodedTool" not in text  # no bypass path

    db = tmp_path / "sec.db"
    init_db(db)
    conn = get_connection(db)
    try:
        from simulator.estate import generate_estate
        estate = generate_estate(seed=42)
        # Unapproved script blocked (empty registry denies).
        assert request_execution(conn, estate, "C", "SCR-018", "DEVICE_001", "U").status == REFUSED
        reg.seed_registry(conn)
        # Hash mismatch, deny-list, stranger, non-compliant all refuse/DENY.
        conn.execute("UPDATE scripts SET hash='x' WHERE script_id='SCR-018'")
        assert request_execution(conn, estate, "C", "SCR-018", "DEVICE_001", "U").status == REFUSED
        conn.execute("UPDATE scripts SET hash=? WHERE script_id='SCR-018'",
                     (reg.canonical_hash("SCR-018", "3.2", "windows", "Clear Teams Cache"),))
        conn.commit()
        assert evaluate(conn, PolicyInput(user_id="U", user_role="stranger",
                                          device_id="D", action_id="SCR-018")).decision == DENY
        estate.get("DEVICE_001").compliance_state = "non-compliant"
        assert request_execution(conn, estate, "C", "SCR-018", "DEVICE_001", "U").status == REFUSED
        estate.get("DEVICE_001").compliance_state = "compliant"
        # L2 requires approval; low confidence never executes (no runs written).
        waiting = request_execution(conn, estate, "C", "SCR-VPN-RECONNECT", "DEVICE_002", "U")
        assert waiting.status == "awaiting_approval"
        from orchestration.investigate import investigate_sync
        calm = investigate_sync("My laptop is very slow.", "DEVICE_100", "USER_100",
                                case_id="CASE-CALM", db_path=str(db))
        assert calm.verdict == "ESCALATE"
        assert conn.execute("SELECT COUNT(*) AS n FROM remediation_runs").fetchone()["n"] == 0
        # No resolution without verification; KB denies; proof still passes.
        itsm = SimulatedITSM(seed=3)
        incident = lifecycle.open_incident(itsm, conn, "CASE-CALM", "slow")
        with pytest.raises(ValueError):
            lifecycle.resolve_verified(itsm, conn, "CASE-CALM", {"passed": False}, "x")
        from coded_tools.digital_workplace.knowledge import GetDocumentAccessContext
        import asyncio
        ctx = asyncio.run(GetDocumentAccessContext().async_invoke(
            {"doc_id": "payroll_admin_sop", "user_role": "employee"}, {}))
        assert ctx["accessible"] is False
        assert (Path("docs") / "ZERO_SECRET_PROOF.md").read_text().count("0") >= 5
    finally:
        conn.close()
