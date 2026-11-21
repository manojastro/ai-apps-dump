"""End-to-end workflow test mirroring the demo script through the API."""
from __future__ import annotations

BAD_DIFF = ("device fw-01\n"
            "+ip access-list APP-DB-GUARD\n"
            "+ deny tcp 10.30.0.0/24 10.30.1.0/24 eq 5432\n"
            "+ permit ip any any\n"
            "interface Vlan210\n"
            "+ ip access-group APP-DB-GUARD in\n")


def test_e2e_bad_change_caught_fixed_applied_verified(client) -> None:
    seed = client.post("/api/v1/network/snapshot", json={})
    assert seed.status_code == 200

    baseline = client.get("/api/v1/intents").json()
    assert baseline["compliance_pct"] == 100.0

    submitted = client.post("/api/v1/changes", json={
        "title": "Add APP-DB-GUARD ACL on firewall",
        "config_diff": BAD_DIFF,
        "requested_by": "e2e",
    })
    change = submitted.json()
    cid = change["id"]
    v = change["validation"]

    assert change["status"] == "AWAITING_APPROVAL"
    assert v["verdict"] == "FAIL"
    assert v["risk"]["band"] in ("HIGH", "CRITICAL")
    kinds = {g["kind"] for g in v["regressions"]}
    assert "ACL_BLACKHOLE" in kinds
    assert "INTENT_MUST_REACH_BROKEN" in kinds
    blocked = v["matrix_diff_summary"]["newly_blocked_detail"]
    assert any(m["flow"]["src"] == "app-01" and m["flow"]["dst"] == "db-01"
               and m["flow"]["port"] == 5432 for m in blocked)
    assert v["rca"]["root_cause"]
    assert len(v["stages"]) >= 10
    assert v["narration"].startswith("[mock-llm]")

    fix = client.post(f"/api/v1/changes/{cid}/propose-fix").json()
    assert fix["fix_validated"] is True
    assert fix["proposed_fix_diff"]
    post_fix_kinds = {g["kind"] for g in fix["validation"]["regressions"]}
    assert "ACL_BLACKHOLE" not in post_fix_kinds

    approved = client.post(
        f"/api/v1/changes/{cid}/approve",
        json={"approver": "net-manager", "comment": "lgtm",
              "justification": "remediated config validated on twin"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    applied = client.post(f"/api/v1/changes/{cid}/apply").json()
    assert applied["status"] == "COMPLETED"

    final = client.get("/api/v1/intents").json()
    assert final["compliance_pct"] == 100.0
    snapshot = client.get("/api/v1/network/snapshot").json()["payload"]
    acls = {a["name"]: a for a in snapshot["acls"]}
    assert not acls.get("APP-DB-GUARD", {}).get("rules")

    kpis = client.get("/api/v1/kpis").json()
    assert kpis["validation_runs_total"] >= 2


def test_e2e_benign_change_passes_and_completes(client) -> None:
    from simulator.faults import FAULT_CATALOG

    spec = FAULT_CATALOG.get("benign_ntp_addition")
    change = client.post("/api/v1/changes", json={
        "title": spec.title, "config_diff": spec.diff_text}).json()
    cid = change["id"]
    v = change["validation"]
    assert v["verdict"] == "PASS"
    assert v["risk"]["band"] == "LOW"
    assert not v["regressions"]
    client.post(f"/api/v1/changes/{cid}/approve", json={"approver": "mgr"})
    result = client.post(f"/api/v1/changes/{cid}/apply").json()
    assert result["status"] == "COMPLETED"


def test_e2e_rejected_change_never_touches_current(client) -> None:
    from simulator.faults import FAULT_CATALOG

    before = client.get("/api/v1/network/snapshot").json()["payload"]
    spec = FAULT_CATALOG.get("segmentation_violation")
    change = client.post("/api/v1/changes", json={
        "title": spec.title, "config_diff": spec.diff_text}).json()
    cid = change["id"]
    r = client.post(f"/api/v1/changes/{cid}/reject",
                    json={"actor": "sec-team", "reason": "violates policy"})
    assert r.status_code == 200
    after = client.get("/api/v1/network/snapshot").json()["payload"]
    assert before == after
    statuses = {c["id"]: c["status"] for c in client.get("/api/v1/changes").json()}
    assert statuses[cid] == "REJECTED"
