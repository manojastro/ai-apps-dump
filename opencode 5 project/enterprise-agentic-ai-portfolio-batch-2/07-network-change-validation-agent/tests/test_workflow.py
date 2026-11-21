"""Change lifecycle workflow tests: state machine, apply, verify, rollback."""
from __future__ import annotations

import pytest

from app.services.state_machine import IllegalTransition, transition


def test_legal_transition_table() -> None:
    assert transition("PROPOSED", "VALIDATING") == "VALIDATING"
    assert transition("VALIDATING", "AWAITING_APPROVAL")
    assert transition("AWAITING_APPROVAL", "APPROVED")
    assert transition("AWAITING_APPROVAL", "REJECTED")
    assert transition("APPROVED", "EXECUTING")
    assert transition("EXECUTING", "VERIFYING")
    for terminal in ("COMPLETED", "FAILED"):
        assert transition("VERIFYING", terminal)
    assert transition("FAILED", "ROLLED_BACK")
    assert transition("COMPLETED", "ROLLED_BACK")
    assert transition("VERIFYING", "ROLLED_BACK")


def test_illegal_transitions_raise() -> None:
    with pytest.raises(IllegalTransition):
        transition("PROPOSED", "APPROVED")
    with pytest.raises(IllegalTransition):
        transition("PROPOSED", "COMPLETED")
    with pytest.raises(IllegalTransition):
        transition("REJECTED", "VALIDATING")
    with pytest.raises(IllegalTransition):
        transition("COMPLETED", "PROPOSED")


def _submit(client, name: str) -> int:
    spec = __import__("simulator.faults", fromlist=["FAULT_CATALOG"]).FAULT_CATALOG.get(
        name)
    r = client.post("/api/v1/changes", json={"title": f"[{name}]",
                                             "config_diff": spec.diff_text})
    assert r.status_code == 200
    return r.json()["id"]


def test_full_lifecycle_submit_validate_approve_apply_complete(client) -> None:
    cid = _submit(client, "acl_blackhole")
    change = client.get(f"/api/v1/changes/{cid}").json()
    assert change["status"] == "AWAITING_APPROVAL"
    assert change["validation"]["verdict"] == "FAIL"
    client.post(f"/api/v1/changes/{cid}/approve",
                json={"approver": "mgr", "justification": "fix validated"})
    result = client.post(f"/api/v1/changes/{cid}/apply").json()
    assert result["status"] == "COMPLETED"


def test_rollback_restores_previous_snapshot(client) -> None:
    before = client.get("/api/v1/network/snapshot").json()["payload"]
    cid = _submit(client, "mtu_mismatch")
    client.post(f"/api/v1/changes/{cid}/approve",
                json={"approver": "mgr", "justification": "test rollback"})
    applied = client.post(f"/api/v1/changes/{cid}/apply").json()
    assert applied["status"] in ("COMPLETED", "ROLLED_BACK")
    rolled = client.post(f"/api/v1/changes/{cid}/rollback?actor=ops").json()
    assert rolled["rolled_back"] is True
    restored = client.get("/api/v1/network/snapshot").json()["payload"]
    assert restored == before


def test_manual_rollback_of_completed_change(client) -> None:
    diff = "device wan-edge-01\ninterface Ethernet1/3\n+ mtu 9000\n"
    change = client.post("/api/v1/changes", json={
        "title": "spare iface mtu", "config_diff": diff}).json()
    cid = change["id"]
    assert change["validation"]["verdict"] == "PASS"
    client.post(f"/api/v1/changes/{cid}/approve", json={"approver": "mgr"})
    result = client.post(f"/api/v1/changes/{cid}/apply").json()
    assert result["status"] == "COMPLETED"
    rolled = client.post(f"/api/v1/changes/{cid}/rollback?actor=ops").json()
    assert rolled["status"] == "ROLLED_BACK"
    final = client.get(f"/api/v1/changes/{cid}").json()
    assert final["status"] == "ROLLED_BACK"


def test_propose_fix_endpoint_revalidates(client) -> None:
    cid = _submit(client, "acl_blackhole")
    payload = client.post(f"/api/v1/changes/{cid}/propose-fix").json()
    assert payload["fix_validated"] is True
    assert payload["proposed_fix_diff"]
    v = payload["validation"]
    kinds = {g["kind"] for g in v["regressions"]}
    assert "ACL_BLACKHOLE" not in kinds


def test_post_apply_verification_auto_rolls_back_bad_change(client) -> None:
    diff = ("device access-fin-01\n"
            "-no ip access-list SEG-ISOLATE-FIN")
    change = client.post("/api/v1/changes", json={
        "title": "delete segmentation acl", "config_diff": diff}).json()
    cid = change["id"]
    assert change["fix_validated"] is False
    client.post(f"/api/v1/changes/{cid}/approve",
                json={"approver": "mgr", "justification": "force"})
    result = client.post(f"/api/v1/changes/{cid}/apply").json()
    assert result["status"] == "ROLLED_BACK"
    compliance = client.get("/api/v1/intents").json()["compliance_pct"]
    assert compliance == 100.0
