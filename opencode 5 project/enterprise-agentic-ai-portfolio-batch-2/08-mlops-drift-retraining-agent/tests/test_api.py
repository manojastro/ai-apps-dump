"""API surface tests including health, metrics, dashboard and illegal transitions."""
from __future__ import annotations


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness(client, trained_baseline):
    response = client.get("/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["database"] is True
    assert body["champion_version"] == trained_baseline["version"]


def test_metrics_prometheus_format(client, trained_baseline):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "# TYPE api_requests_total counter" in text
    assert 'api_requests_total{method="GET",path="/health",status="200"}' in text
    assert "# TYPE champion_info gauge" in text
    assert f'champion_info{{algorithm="LogisticRegression",version="{trained_baseline["version"]}"}} 1.0' in text
    assert "monitoring_windows_total" in text
    assert "drift_alerts_total" in text


def test_dashboard_served(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Drift" in response.content


def test_train_baseline(trained_baseline):
    assert trained_baseline["status"] == "champion"
    assert trained_baseline["metrics"]["roc_auc"] > 0.7
    assert "cand_f1_tolerance" in trained_baseline["thresholds"]


def test_window_submit_and_evaluate_flow(client, trained_baseline):
    window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "api-clean", "n_samples": 2000, "seed": 7001},
    ).json()
    assert window["n_samples"] == 2000
    evaluation = client.post(f"/api/v1/monitoring/windows/{window['id']}/evaluate").json()
    assert evaluation["alert"] is False

    latest = client.get("/api/v1/monitoring/latest").json()
    assert latest["id"] == window["id"]
    drift = client.get("/api/v1/monitoring/drift").json()
    assert len(drift["results"]) >= 7
    perf = client.get("/api/v1/monitoring/performance").json()
    assert perf["results"]
    fairness = client.get("/api/v1/monitoring/fairness").json()
    assert fairness["fairness"]["disparity_ratio"] > 0.8
    quality = client.get("/api/v1/monitoring/quality").json()
    assert all(c["passed"] for c in quality["checks"])


def test_decide_endpoint_monitor_on_clean(client, trained_baseline):
    window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "api-decide", "n_samples": 2000, "seed": 7002},
    ).json()
    client.post(f"/api/v1/monitoring/windows/{window['id']}/evaluate")
    decision = client.post("/api/v1/retraining/decide", json={"window_id": window["id"]})
    assert decision.status_code == 200
    assert decision.json()["decision"] == "monitor"


def test_decide_requires_evaluated_window(client, trained_baseline):
    window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "api-unevaluated", "n_samples": 500, "seed": 7003},
    ).json()
    response = client.post("/api/v1/retraining/decide", json={"window_id": window["id"]})
    assert response.status_code in (400, 409, 500)


def test_candidate_train_and_evaluate_endpoints(client, trained_baseline):
    trained = client.post("/api/v1/candidates/train", json={"seed": 51, "n_samples": 2500}).json()
    evaluated = client.post("/api/v1/candidates/evaluate", json={"version": trained["version"]}).json()
    assert evaluated["verdict"] in ("pass", "reject")
    listing = client.get("/api/v1/candidates").json()
    assert any(e["version"] == trained["version"] for e in listing["evaluations"])
    risk = client.get(f"/api/v1/candidates/{trained['version']}/risk").json()
    assert risk["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_shadow_and_canary_endpoints(client, trained_baseline):
    trained = client.post("/api/v1/candidates/train", json={"seed": 52, "n_samples": 2000}).json()
    shadow = client.post("/api/v1/shadow/run", json={"version": trained["version"], "n_requests": 800}).json()
    assert shadow["disagreement_rate"] >= 0.0
    canary = client.post("/api/v1/shadow/canary", json={"version": trained["version"], "n_requests": 800}).json()
    assert isinstance(canary["passed"], bool)
    results = client.get("/api/v1/shadow/results").json()
    assert results["shadow_comparisons"]


def test_full_promotion_flow_with_illegal_transition(client, trained_baseline):
    trained = client.post("/api/v1/candidates/train", json={"seed": 53, "n_samples": 2500}).json()
    evaluated = client.post("/api/v1/candidates/evaluate", json={"version": trained["version"]}).json()
    if evaluated["verdict"] != "pass":
        trained2 = client.post("/api/v1/candidates/train", json={"seed": 54, "n_samples": 2500}).json()
        evaluated = client.post("/api/v1/candidates/evaluate", json={"version": trained2["version"]}).json()
        assert evaluated["verdict"] == "pass"
        trained = trained2

    created = client.post("/api/v1/promotions", json={"candidate_version": trained["version"]}).json()
    promotion_id = created["promotion_id"]
    assert created["state"] == "AWAITING_APPROVAL"

    approved = client.post(
        f"/api/v1/promotions/{promotion_id}/approve", json={"approver": "tester"}
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "COMPLETED"

    illegal = client.post(f"/api/v1/promotions/{promotion_id}/approve", json={})
    assert illegal.status_code == 409
    illegal_reject = client.post(f"/api/v1/promotions/{promotion_id}/reject", json={})
    assert illegal_reject.status_code == 409


def test_approve_unknown_promotion_404(client):
    assert client.post("/api/v1/promotions/99999/approve", json={}).status_code == 404


def test_registry_and_kpis(client, trained_baseline):
    registry = client.get("/api/v1/registry").json()
    versions = [m["version"] for m in registry["models"]]
    assert trained_baseline["version"] in versions
    kpis = client.get("/api/v1/kpis").json()
    assert kpis["windows_evaluated"] >= 0
    snapshots = client.get("/api/v1/kpi-snapshots").json()
    assert snapshots["snapshots"]


def test_tools_listing_endpoint(client):
    tools = client.get("/api/v1/models/tools").json()["tools"]
    assert len(tools) == 7
    by_name = {t["name"]: t for t in tools}
    assert by_name["promote_model_tool"]["permission"] == "mutating"
