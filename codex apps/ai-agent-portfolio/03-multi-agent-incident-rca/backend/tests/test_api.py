from __future__ import annotations

from fastapi.testclient import TestClient

from app import api as api_module


def client() -> TestClient:
    api_module.repository.clear()
    return TestClient(api_module.app)


def test_health_incident_and_investigation_flow():
    with client() as http:
        assert http.get("/healthz").json()["status"] == "ok"
        payload = {
            "title": "Injected deployment incident",
            "service": "checkout-api",
            "scenario": "bad-deployment",
            "severity": "SEV-2",
            "alert_summary": "5xx alert",
        }
        created = http.post("/api/v1/incidents", json=payload).json()
        response = http.post(f"/api/v1/incidents/{created['id']}/investigate")
        assert response.status_code == 200
        result = response.json()
        assert result["hypotheses"][0]["category"] == "deployment"
        assert all(item["id"].startswith("EV-") for item in result["evidence"])
        assert http.get(f"/api/v1/incidents/{created['id']}/rca").status_code == 200


def test_viewer_cannot_create_incident_and_unknown_scenario_rejected():
    payload = {
        "title": "Blocked incident",
        "service": "checkout-api",
        "scenario": "not-real",
        "severity": "SEV-2",
        "alert_summary": "test",
    }
    with client() as http:
        assert http.post("/api/v1/incidents", json=payload, headers={"X-Role": "viewer"}).status_code == 403
        assert http.post("/api/v1/incidents", json=payload).status_code == 422


def test_audit_log_requires_admin():
    with client() as http:
        assert http.get("/api/v1/audit", headers={"X-Role": "viewer"}).status_code == 403
        assert http.get("/api/v1/audit", headers={"X-Role": "admin"}).status_code == 200

