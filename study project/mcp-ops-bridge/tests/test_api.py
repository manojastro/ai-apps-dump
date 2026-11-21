"""mock-itsm API tests via TestClient (offline)."""

from fastapi.testclient import TestClient

from mock_itsm import app as appmod


def _client(db_path: str, monkeypatch) -> TestClient:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(appmod.settings, "itsm_db_path", db_path)
    return TestClient(appmod.app)


def test_list_with_sysparm_query(db_path: str, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    c = _client(db_path, monkeypatch)
    r = c.get("/api/now/table/incident", params={"sysparm_query": "service=vpn", "sysparm_limit": 5})
    assert r.status_code == 200
    assert len(r.json()["result"]) >= 1


def test_get_one_scenario(db_path: str, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    c = _client(db_path, monkeypatch)
    r = c.get("/api/now/table/incident/INC1000001")
    assert r.status_code == 200
    assert r.json()["result"]["ci"] == "vpn-gateway-01"


def test_patch_needs_token(db_path: str, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    c = _client(db_path, monkeypatch)
    r = c.patch("/api/now/table/incident/INC1000001", json={"state": "In Progress"})
    assert r.status_code == 403


def test_approval_then_patch(db_path: str, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    c = _client(db_path, monkeypatch)
    a = c.post("/approvals", json={"tool": "update_incident_state", "target": "INC1000001"})
    assert a.status_code == 201
    token = a.json()["approval_token"]
    r = c.patch(
        "/api/now/table/incident/INC1000001",
        json={"state": "In Progress"},
        headers={"X-Approval-Token": token, "X-Approval-Tool": "update_incident_state"},
    )
    assert r.status_code == 200
    assert r.json()["result"]["state"] == "In Progress"
    # reuse must fail
    r2 = c.patch(
        "/api/now/table/incident/INC1000001",
        json={"state": "Resolved"},
        headers={"X-Approval-Token": token, "X-Approval-Tool": "update_incident_state"},
    )
    assert r2.status_code == 403


def test_change_ci_filter(db_path: str, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    c = _client(db_path, monkeypatch)
    r = c.get("/api/now/table/change_request", params={"ci": "fw-edge-01"})
    assert r.status_code == 200
    assert any(x["number"] == "CHG1000001" for x in r.json()["result"])


def test_logs_capped(db_path: str, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    c = _client(db_path, monkeypatch)
    r = c.get("/api/logs", params={"service": "vpn", "limit": 500})
    assert r.status_code == 200
    assert len(r.json()["result"]) <= 200


def test_seed_counts(db_path: str) -> None:
    from mock_itsm.db import table_count

    assert table_count(db_path, "cmdb_ci") == 40
    assert table_count(db_path, "incident") == 200
    assert table_count(db_path, "change_request") == 60
