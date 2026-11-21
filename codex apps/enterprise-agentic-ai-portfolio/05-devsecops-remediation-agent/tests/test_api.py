from backend.app.main import create_app
from fastapi.testclient import TestClient


APPROVER_HEADERS = {"X-API-Key": "forgeguard-local-demo-approver"}
EXECUTOR_HEADERS = {"X-API-Key": "forgeguard-local-demo-executor"}


def test_operations_dashboard_and_openapi(client):
    assert client.get("/health").json()["status"] == "healthy"
    assert client.get("/ready").json()["status"] == "ready"
    assert "devsecops_investigations_total" in client.get("/metrics").text
    assert "ForgeGuard" in client.get("/").text
    schema = client.get("/openapi.json").json()
    assert "/api/v1/incidents/{incident_id}/remediate" in schema["paths"]


def test_live_contract_blocks_then_validates_remediation(client):
    scenarios = client.get("/api/v1/scenarios")
    assert scenarios.status_code == 200 and len(scenarios.json()) == 3

    scan = client.post("/api/v1/scenarios/sql_injection/scan")
    assert scan.status_code == 201
    incident = scan.json()
    incident_id = incident["incident_id"]
    assert incident["status"] == "AWAITING_APPROVAL"

    assert client.post(f"/api/v1/incidents/{incident_id}/remediate").status_code == 403
    assert client.post(
        f"/api/v1/incidents/{incident_id}/remediate", headers=EXECUTOR_HEADERS
    ).status_code == 409
    assert client.post(
        f"/api/v1/incidents/{incident_id}/approval",
        json={"approved": True, "reason": "missing verified credential"},
    ).status_code == 403
    assert client.post(
        f"/api/v1/incidents/{incident_id}/approval",
        headers=EXECUTOR_HEADERS,
        json={"approved": True, "reason": "executor cannot approve"},
    ).status_code == 403

    approval = client.post(
        f"/api/v1/incidents/{incident_id}/approval",
        headers=APPROVER_HEADERS,
        json={"approved": True, "reason": "Reviewed exact patch hashes and rollback"},
    )
    assert approval.status_code == 200 and approval.json()["status"] == "APPROVED"

    remediation = client.post(
        f"/api/v1/incidents/{incident_id}/remediate", headers=EXECUTOR_HEADERS
    )
    assert remediation.status_code == 200
    result = remediation.json()
    assert result["status"] == "VALIDATED"
    assert result["validation"]["result"]["passed"] is True

    summary = client.get("/api/v1/evaluations/summary").json()
    assert summary["finding_validity"] == 1.0
    assert summary["exploitability_accuracy"] == 1.0
    assert summary["remediation_success_rate"] == 1.0
    assert summary["security_regressions"] == 0
    assert summary["test_regressions"] == 0
    assert len(client.get("/api/v1/activity").json()) == 4


def test_input_validation_and_unknown_scenario(client):
    assert client.post("/api/v1/scenarios/not-real/scan").status_code == 404
    assert client.get("/api/v1/incidents?limit=0").status_code == 422
    response = client.post(
        "/api/v1/incidents/missing/approval",
        headers=APPROVER_HEADERS,
        json={"approved": True, "reason": "no"},
    )
    assert response.status_code == 422


def test_api_key_authentication_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "api_key")
    monkeypatch.setenv("VIEWER_API_KEY", "viewer-key")
    monkeypatch.setenv("APPROVER_API_KEY", "approver-key")
    monkeypatch.setenv("EXECUTOR_API_KEY", "executor-key")
    app = create_app(tmp_path / "auth.db", tmp_path / "auth-workspaces")
    with TestClient(app) as protected:
        assert protected.get("/api/v1/scenarios").status_code == 401
        assert protected.get("/api/v1/scenarios", headers={"X-API-Key": "viewer-key"}).status_code == 200
        incident = protected.post(
            "/api/v1/scenarios/sql_injection/scan", headers={"X-API-Key": "viewer-key"}
        ).json()
        approval_path = f"/api/v1/incidents/{incident['incident_id']}/approval"
        assert protected.post(
            approval_path, headers={"X-API-Key": "viewer-key"},
            json={"approved": True, "reason": "viewer cannot approve"},
        ).status_code == 403
        assert protected.post(
            approval_path, headers={"X-API-Key": "approver-key"},
            json={"approved": True, "reason": "verified reviewer"},
        ).status_code == 200
        remediation_path = f"/api/v1/incidents/{incident['incident_id']}/remediate"
        assert protected.post(remediation_path, headers={"X-API-Key": "approver-key"}).status_code == 403
        assert protected.post(remediation_path, headers={"X-API-Key": "executor-key"}).status_code == 200


def test_duplicate_identity_credentials_fail_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "api_key")
    monkeypatch.setenv("VIEWER_API_KEY", "duplicate")
    monkeypatch.setenv("APPROVER_API_KEY", "duplicate")
    monkeypatch.setenv("EXECUTOR_API_KEY", "executor")
    import pytest
    with pytest.raises(RuntimeError, match="distinct"):
        create_app(tmp_path / "bad-auth.db", tmp_path / "bad-auth-workspaces")
