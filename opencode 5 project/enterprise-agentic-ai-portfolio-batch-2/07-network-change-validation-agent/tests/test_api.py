"""API surface tests: observability endpoints, snapshot, faults, error contracts."""
from __future__ import annotations


def test_health(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readiness(client) -> None:
    r = client.get("/readiness")
    body = r.json()
    assert r.status_code == 200
    assert body["status"] == "ready"
    assert body["checks"]["database"] is True
    assert body["checks"]["twin_seed"] is True


def test_metrics_prometheus_format(client) -> None:
    client.get("/health")
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "# TYPE http_requests_total counter" in text
    assert "http_requests_total" in text
    assert "process_uptime_seconds" in text


def test_dashboard_served(client) -> None:
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert b"CHANGE VALIDATION" in r.content


def test_snapshot_seed_idempotent(client) -> None:
    r1 = client.post("/api/v1/network/snapshot", json={})
    r2 = client.post("/api/v1/network/snapshot", json={})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["devices"] >= 12
    topo = client.get("/api/v1/topology").json()
    assert len(topo["nodes"]) >= 12
    assert any(n["role"] == "firewall" for n in topo["nodes"])


def test_fault_catalog_and_unknown_fault_404(client) -> None:
    r = client.get("/api/v1/network/faults")
    names = {f["name"] for f in r.json()["faults"]}
    assert {"acl_blackhole", "bgp_route_leak", "benign_ntp_addition"} <= names
    missing = client.post("/api/v1/network/faults/nope", json={})
    assert missing.status_code == 404


def test_change_404s(client) -> None:
    client.post("/api/v1/network/snapshot", json={})
    assert client.get("/api/v1/changes/999").status_code == 404
    assert client.get("/api/v1/changes/999/validation").status_code == 404


def test_apply_before_approval_is_conflict_409(client) -> None:
    from simulator.faults import FAULT_CATALOG

    spec = FAULT_CATALOG.get("acl_blackhole")
    change = client.post("/api/v1/changes", json={
        "title": "t", "config_diff": spec.diff_text}).json()
    r = client.post(f"/api/v1/changes/{change['id']}/apply")
    assert r.status_code == 409
    assert "illegal" in r.json()["detail"].lower()


def test_reject_terminal_state_conflicts(client) -> None:
    from simulator.faults import FAULT_CATALOG

    spec = FAULT_CATALOG.get("acl_blackhole")
    change = client.post("/api/v1/changes", json={
        "title": "t", "config_diff": spec.diff_text}).json()
    cid = change["id"]
    r = client.post(f"/api/v1/changes/{cid}/reject",
                    json={"actor": "reviewer", "reason": "bad idea"})
    assert r.status_code == 200 and r.json()["status"] == "REJECTED"
    again = client.post(f"/api/v1/changes/{cid}/reject",
                        json={"actor": "reviewer"})
    assert again.status_code == 409
    approve_after_reject = client.post(
        f"/api/v1/changes/{cid}/approve",
        json={"approver": "x", "justification": "y"})
    assert approve_after_reject.status_code == 409


def test_high_risk_approval_requires_justification(client) -> None:
    from simulator.faults import FAULT_CATALOG

    spec = FAULT_CATALOG.get("acl_blackhole")
    change = client.post("/api/v1/changes", json={
        "title": "t", "config_diff": spec.diff_text}).json()
    cid = change["id"]
    no_justification = client.post(f"/api/v1/changes/{cid}/approve",
                                   json={"approver": "a"})
    assert no_justification.status_code == 422
    with_justification = client.post(
        f"/api/v1/changes/{cid}/approve",
        json={"approver": "a", "justification": "reviewed remediation"})
    assert with_justification.status_code == 200


def test_validation_report_shape(client) -> None:
    from simulator.faults import FAULT_CATALOG

    spec = FAULT_CATALOG.get("acl_blackhole")
    change = client.post("/api/v1/changes", json={
        "title": "t", "config_diff": spec.diff_text}).json()
    v = change["validation"]
    for field in ("verdict", "risk", "regressions", "intents", "rca",
                  "duration_ms", "stages"):
        assert field in v
    assert v["risk"]["band"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    kinds = {g["kind"] for g in v["regressions"]}
    assert "ACL_BLACKHOLE" in kinds
    assert v["rca"]["incident_id"].startswith("CHG-")


def test_topology_reachability_intents_kpis_views(client) -> None:
    for path in ("/api/v1/topology", "/api/v1/reachability", "/api/v1/intents"):
        r = client.get(path)
        assert r.status_code == 200, path
    kpis = client.get("/api/v1/kpis").json()
    assert "validation_runs_total" in kpis
    assert "unsafe_changes_prevented" in kpis
