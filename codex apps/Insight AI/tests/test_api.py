from fastapi.testclient import TestClient

from services.api.db import Session, User
from services.api.main import app


def test_unauthenticated_reads_are_denied():
    assert TestClient(app).get("/api/incidents").status_code == 401


def test_chunked_oversized_payload_rejected():
    def chunks():
        yield b"x" * 40000
        yield b"x" * 40000

    assert TestClient(app).post("/api/auth/login", content=chunks()).status_code == 413


def test_create_incident_is_persisted(client):
    result = client.post("/api/incidents", json={"title": "Checkout errors", "fixture": "payment_delay"})
    assert result.status_code == 200
    assert any(x["id"] == result.json()["id"] for x in client.get("/api/incidents").json())


def test_csrf_required_for_mutation(client):
    del client.headers["x-csrf-token"]
    assert client.post("/api/incidents", json={"title": "No CSRF"}).status_code == 403


def test_live_mode_does_not_fall_back_to_replay(client, monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    response = client.post("/api/incidents", json={"title": "Live", "mode": "live"})
    assert response.status_code == 503
    assert "PROVIDER" in response.text


def test_viewer_cannot_create_incident(client):
    who = client.get("/api/auth/me").json()
    with Session() as db:
        user = db.get(User, who["id"])
        user.role = "viewer"
        db.commit()
    assert client.post("/api/incidents", json={"title": "Forbidden"}).status_code == 403
