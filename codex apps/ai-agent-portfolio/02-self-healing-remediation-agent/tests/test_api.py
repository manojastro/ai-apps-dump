def test_health(client):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200


def test_auth_and_csrf_are_required(client):
    assert client.get("/api/incidents").status_code == 401
    assert client.post("/api/incidents", json={"scenario": "crashloop"}, headers={"Authorization": "Bearer demo-operator-token"}).status_code == 403


def test_inject_low_risk_and_dashboard(client, auth):
    response = client.post("/api/incidents", json={"scenario": "crashloop"}, headers=auth)
    assert response.status_code == 201
    assert response.json()["status"] == "RESOLVED"
    dashboard = client.get("/api/dashboard", headers=auth).json()
    assert dashboard["total_incidents"] == 1
    assert dashboard["auto_resolution_rate"] == 1.0
    assert "selfheal_incidents_total 1" in client.get("/metrics").text


def test_medium_approval_api(client, auth):
    created = client.post("/api/incidents", json={"scenario": "bad_deployment"}, headers=auth).json()
    assert created["status"] == "PENDING_APPROVAL"
    response = client.post(f"/api/incidents/{created['id']}/approval",
                           json={"decision": "APPROVED", "comment": "reviewed"}, headers=auth)
    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"


def test_forced_failure_exposes_rollback_timeline(client, auth):
    response = client.post("/api/incidents", json={"scenario": "excessive_latency", "force_verification_failure": True}, headers=auth)
    body = response.json()
    assert body["status"] == "ROLLED_BACK"
    assert body["rollback_records"][0]["status"] == "SUCCEEDED"
    assert any(event["event_type"] == "rollback.completed" for event in body["audit_events"])


def test_viewer_cannot_inject(client):
    headers = {"Authorization": "Bearer demo-viewer-token", "X-CSRF-Token": "demo-csrf-token"}
    assert client.post("/api/incidents", json={"scenario": "crashloop"}, headers=headers).status_code == 403
