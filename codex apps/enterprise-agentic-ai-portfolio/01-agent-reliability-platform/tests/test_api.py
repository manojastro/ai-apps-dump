from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_readiness_metrics_and_dashboard(tmp_path):
    with TestClient(create_app(tmp_path / "api.db")) as client:
        assert client.get("/health").json()["status"] == "healthy"
        assert client.get("/ready").json()["status"] == "ready"
        assert "arp_http_requests_total" in client.get("/metrics").text
        assert "Trust the evidence" in client.get("/").text


def test_full_api_investigation_and_guarded_action(tmp_path):
    with TestClient(create_app(tmp_path / "workflow.db")) as client:
        response = client.post("/api/v1/demo/run", json={"scenario": "hallucinated_success", "agent_version": "1.0.0"})
        assert response.status_code == 200
        body = response.json()
        assert body["verified_outcome"]["success"] is False
        assert body["rca"]["evidence"]
        action_id = body["proposed_action"]["action_id"]
        assert client.post(f"/api/v1/actions/{action_id}/execute").status_code == 403
        approval = client.post(f"/api/v1/actions/{action_id}/approval", json={"approver": "api-reviewer", "decision": "APPROVED", "reason": "Verified evidence"})
        assert approval.status_code == 200
        assert client.post(f"/api/v1/actions/{action_id}/execute").json()["status"] == "EXECUTED"
        incident = client.get(f"/api/v1/incidents/{body['incident_id']}")
        assert incident.status_code == 200
        assert incident.json()["validations"]


def test_regression_gate_blocks_known_bad_candidate(tmp_path):
    with TestClient(create_app(tmp_path / "regression.db")) as client:
        result = client.post("/api/v1/regression/compare", json={"current_version": "1.0.0", "candidate_version": "1.1.0-regressed"})
        assert result.status_code == 200
        assert result.json()["decision"] == "BLOCK"


def test_input_validation_rejects_unknown_scenario(tmp_path):
    with TestClient(create_app(tmp_path / "validation.db")) as client:
        response = client.post("/api/v1/demo/run", json={"scenario": "arbitrary"})
        assert response.status_code == 422


def test_dashboard_metrics_count_non_primary_detection_codes(tmp_path):
    with TestClient(create_app(tmp_path / "dashboard.db")) as client:
        assert client.post("/api/v1/demo/run", json={"scenario": "wrong_tool"}).status_code == 200
        fleet = client.get("/api/v1/dashboard").json()["fleet"]
        assert fleet["tool_accuracy"] == 1.0
