"""API + worker tests (in-process FastAPI TestClient, SQLite)."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from schemaguard import config
from schemaguard.schemas.registry import FileSchemaRegistry, seed_registry, subject_for_topic
from schemaguard.service import SchemaGuardService
from schemaguard.worker import RegistryPoller
from tests.conftest import PIPELINE, mutated

RENAME = [{"op": "rename_field", "field": "amount", "to": "total_amount"}]


@pytest.fixture
def client(settings, monkeypatch):
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    monkeypatch.setattr("schemaguard.service.get_settings", lambda: settings)
    monkeypatch.setattr("schemaguard.api.app.get_settings", lambda: settings)
    from schemaguard.api.app import app

    with TestClient(app) as c:
        yield c


def wait_status(client, run_id, want, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/runs/{run_id}").json()
        if r["status"] in want:
            return r
        time.sleep(0.3)
    raise AssertionError(f"run {run_id} stuck in {r['status']}")


def test_health(client):
    h = client.get("/health").json()
    assert h["status"] == "ok" and h["llm_provider"] == "fake" and h["database"] == "sqlite"


def test_full_demo_flow_over_http(client):
    r = client.post("/changes", json={"topic": "orders.v1", "mutations": RENAME})
    assert r.status_code == 202
    run_id = r.json()["run_id"]
    run = wait_status(client, run_id, {"awaiting_approval"})
    assert run["state"]["aggregate"]["dashboards"]["Sales Overview"] == "breaking"
    assert "total_amount" in run["state"]["patch"]["diff"]
    dot = client.get(f"/runs/{run_id}/graph.dot").text
    assert "digraph" in dot and "Revenue by Day" in dot
    assert client.post("/changes", json={"topic": "orders.v1", "mutations": RENAME}).json() == {
        "run_id": run_id, "created": False, "status_url": f"/runs/{run_id}",
    }  # fmt: skip
    assert client.post(f"/runs/{run_id}/approve", json={"reviewer": "alice"}).status_code == 202
    run = wait_status(client, run_id, {"completed", "failed"})
    assert run["status"] == "completed"
    report = client.get(f"/runs/{run_id}/report").text
    assert "Approval record" in report and "alice" in report
    assert client.post(f"/runs/{run_id}/approve", json={"reviewer": "alice"}).status_code == 409
    assert any(x["run_id"] == run_id for x in client.get("/runs").json())


def test_lineage_endpoints(client):
    d = client.get("/lineage/downstream", params={"node": "field:orders.v1.amount"}).json()
    assert "Sales Overview" in d["blast_radius"]["dashboards"]
    u = client.get("/lineage/upstream", params={"node": "column:mart.daily_revenue.revenue"}).json()
    assert any(n["id"] == "field:orders.v1.amount" for n in u["nodes"])
    assert client.get("/lineage/downstream", params={"node": "field:nope"}).status_code == 404


def test_validation_and_auth(client, settings, monkeypatch):
    assert client.post("/changes", json={"topic": "orders.v1"}).status_code == 422
    assert client.post(
        "/changes", json={"topic": "orders.v1", "mutations": [{"op": "drop_field", "field": "zzz"}]}
    ).status_code in (202, 422)
    assert client.post("/runs/nope/approve", json={"reviewer": "x"}).status_code == 404
    monkeypatch.setattr(settings, "api_key", "s3cret")
    assert client.get("/runs").status_code == 401
    assert client.get("/runs", headers={"X-API-Key": "s3cret"}).status_code == 200
    assert client.get("/health").status_code == 200


def test_registry_poller_detects_new_version_once(settings, tmp_path):
    reg = FileSchemaRegistry(tmp_path / "registry")
    seed_registry(reg, PIPELINE / "avro")
    svc = SchemaGuardService(settings)
    poller = RegistryPoller(svc, reg)
    assert poller.poll_once() == []  # first sight = baseline
    reg.register(subject_for_topic("orders.v1"), mutated(RENAME))
    (run_id,) = poller.poll_once()
    assert poller.poll_once() == []  # not processed twice
    run = svc.get_run(run_id)
    assert run["status"] == "awaiting_approval"
    assert (
        run["state"]["change_event"]["new_version"] == 2
        and run["state"]["change_event"]["source"] == "registry-poller"
    )
    svc.close()
