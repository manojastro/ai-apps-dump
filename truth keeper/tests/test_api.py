from fastapi.testclient import TestClient

from app.api.main import create_app


def client(env):
    settings, _ = env
    return TestClient(create_app(settings))


def test_health_and_empty_queue(env):
    c = client(env)
    h = c.get("/health").json()
    assert h["ok"] and h["llm_mode"] == "mock"
    assert c.get("/conflicts").json() == []


def test_full_flow_over_http(env):
    c = client(env)
    run = c.post("/pipeline/run", json={}).json()
    assert run["detected"] == 120 and run["proposed"] == 120

    rows = c.get("/conflicts", params={"type": "CANCELLED_BUT_BILLING_ACTIVE"}).json()
    assert rows and all(r["type"] == "CANCELLED_BUT_BILLING_ACTIVE" for r in rows)
    assert len(c.get("/conflicts", params={"min_impact": 1000}).json()) < 120
    pid = rows[0]["proposal"]["id"]

    detail = c.get(f"/proposals/{pid}").json()
    assert detail["conflict"]["evidence"]["crm_status"] == "cancelled" and detail["explanation"]
    assert detail["prompt_version"] == "v1"

    assert c.post(f"/proposals/{pid}/approve", json={"reviewer": ""}).status_code == 422
    assert c.post(f"/proposals/{pid}/approve", json={"reviewer": "alice", "note": "ok"}).json()["status"] == "APPROVED"
    assert c.post(f"/proposals/{pid}/approve", json={"reviewer": "alice"}).status_code == 409
    applied = c.post(f"/proposals/{pid}/apply", json={"actor": "alice"}).json()
    assert applied["outcome"] == "applied"
    assert c.post(f"/proposals/{pid}/apply", json={"actor": "alice"}).json()["outcome"] == "already_applied"

    other = c.get("/conflicts", params={"type": "PLAN_MISMATCH"}).json()[0]["proposal"]["id"]
    assert c.post(f"/proposals/{other}/reject", json={"reviewer": "bob", "reason": "wrong plan"}).json()["status"] \
        == "REJECTED"
    assert c.get("/proposals/999999").status_code == 404
    assert any(e["event"] == "fix_applied" for e in c.get("/audit").json())
    stats = c.get("/stats").json()
    assert stats["proposals_applied"] == 1 and stats["proposals_rejected"] == 1


def test_ui_pages_render_and_forms_work(env):
    c = client(env)
    assert "Run detection" in c.get("/").text
    c.post("/ui/run", follow_redirects=False)
    page = c.get("/").text
    assert "CANCELLED_BUT_BILLING_ACTIVE" in page
    pid = c.get("/conflicts").json()[0]["proposal"]["id"]
    assert "Evidence" in c.get(f"/ui/proposals/{pid}").text
    r = c.post(f"/ui/proposals/{pid}/approve", data={"reviewer": "alice", "note": ""}, follow_redirects=True)
    assert "Approved" in r.text
    r = c.post(f"/ui/proposals/{pid}/apply", data={"actor": "alice"}, follow_redirects=True)
    assert "applied" in r.text
