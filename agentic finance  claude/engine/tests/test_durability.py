"""Restart, lease expiry and idempotency of the durable workflow."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select, text

from spreadlens.config import get_settings
from spreadlens.db import _factory, session_scope
from spreadlens.models import Observation, Statement, WorkflowRun, WorkflowTask
from spreadlens.workflow import coordinator
from spreadlens.workflow.coordinator import claim, enqueue, execute_task
from spreadlens.workflow.worker import Worker, drain_parallel
from tests.conftest import drain, new_company, upload

pytestmark = pytest.mark.integration


def _tasks(run_id):
    with session_scope() as db:
        return [(t.stage, t.status, t.attempts) for t in db.scalars(select(WorkflowTask).where(WorkflowTask.run_id == run_id).order_by(WorkflowTask.created_at))]


def test_worker_crash_mid_stage_recovers_via_lease(client, analyst, workspace_id, monkeypatch):
    cid = new_company(client, analyst, workspace_id, "Crash co")
    up = upload(client, analyst, cid, "05_aravalli_fy25_no_cashflow.pdf")
    w = Worker(get_settings())
    # run integrity + understand normally
    assert w.run_once() == "succeeded" and w.run_once() == "succeeded"
    # simulate a crash during the extract stage: claim the task, then die before committing
    with session_scope() as db:
        tid = claim(db, "dead-worker", 60)
    original = coordinator.HANDLERS["extract"]

    def crash(*a, **k):
        original(*a, **k)  # does all the writes...
        raise SystemExit("power cut")  # ...but never commits

    monkeypatch.setitem(coordinator.HANDLERS, "extract", crash)
    with pytest.raises(SystemExit):
        execute_task(_factory(), get_settings(), tid, "dead-worker")
    monkeypatch.setitem(coordinator.HANDLERS, "extract", original)
    with session_scope() as db:
        dv_id = db.get(WorkflowTask, tid).payload and db.get(WorkflowRun, up["run_id"]).document_version_id
        assert db.scalar(select(func.count()).select_from(Statement).where(Statement.document_version_id == dv_id)) == 0  # nothing partial
        # the task is still "running" under a dead lease; expire it
        db.execute(text("UPDATE workflow_tasks SET lease_until = now() - interval '1 second' WHERE id = :i"), {"i": tid})
    drain()
    stages = _tasks(up["run_id"])
    extract = [s for s in stages if s[0] == "extract"][0]
    assert extract[1] == "succeeded" and extract[2] == 2  # retried exactly once after the crash
    with session_scope() as db:
        run = db.get(WorkflowRun, up["run_id"])
        assert run.status == "completed"
        assert db.scalar(select(func.count()).select_from(Statement).where(Statement.document_version_id == run.document_version_id)) == 2


def test_enqueue_is_idempotent_and_stage_replay_does_not_duplicate(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Idempotent co")
    up = upload(client, analyst, cid, "05_aravalli_fy25_no_cashflow.pdf")
    drain()
    with session_scope() as db:
        run = db.get(WorkflowRun, up["run_id"])
        before = db.scalar(select(func.count()).select_from(WorkflowTask).where(WorkflowTask.run_id == run.id))
        enqueue(db, run, "extract", {})  # same idempotency key -> ignored
        enqueue(db, run, "map", {})
    with session_scope() as db:
        assert db.scalar(select(func.count()).select_from(WorkflowTask).where(WorkflowTask.run_id == up["run_id"])) == before
        n_obs = db.scalar(select(func.count()).select_from(Observation).where(Observation.document_version_id == run.document_version_id))
        # replay the normalize stage explicitly: it replaces its own output, never duplicates it
        t = db.scalar(select(WorkflowTask).where(WorkflowTask.run_id == run.id, WorkflowTask.stage == "normalize"))
        t.status, t.attempts = "queued", 0
        r = db.scalar(select(WorkflowTask).where(WorkflowTask.run_id == run.id, WorkflowTask.stage == "reconcile"))
        r.status = "succeeded"
    drain()
    with session_scope() as db:
        assert db.scalar(select(func.count()).select_from(Observation).where(Observation.document_version_id == run.document_version_id)) == n_obs


def test_parallel_workers_process_independent_documents(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Parallel co")
    ups = [upload(client, analyst, cid, f) for f in ("01_aravalli_fy25_standalone.pdf", "04_aravalli_fy25_lakhs.xlsx",
                                                     "07_aravalli_fy26_restated_comparative.pdf")]
    drain_parallel(get_settings(), workers=3)
    with session_scope() as db:
        for u in ups:
            assert db.get(WorkflowRun, u["run_id"]).status == "completed"


def test_retry_failed_stage_is_not_a_new_revision(client, analyst, workspace_id, monkeypatch):
    cid = new_company(client, analyst, workspace_id, "Retry co")
    up = upload(client, analyst, cid, "05_aravalli_fy25_no_cashflow.pdf")

    def boom(*a, **k):
        raise RuntimeError("live model unavailable")

    monkeypatch.setitem(coordinator.HANDLERS, "map", boom)
    monkeypatch.setattr(coordinator, "timedelta", lambda seconds: __import__("datetime").timedelta(seconds=0))
    drain()
    with session_scope() as db:
        run = db.get(WorkflowRun, up["run_id"])
        # extraction succeeded, mapping failed: shown as a partial failure, never silently replaced by demo output
        assert run.status == "partial" and "map" in run.error
    monkeypatch.undo()
    r = client.post(f"/api/runs/{up['run_id']}/retry", headers=analyst)
    assert r.status_code == 200 and r.json()["retried_stage"] == "map"
    drain()
    doc = client.get(f"/api/documents/{up['document_version_id']}", headers=analyst).json()
    assert doc["status"] == "ready_for_review" and doc["version_no"] == 1 and len(doc["runs"]) == 1
    # a new upload of an edited file is a new revision of the same document
    up2 = upload(client, analyst, cid, "01_aravalli_fy25_standalone.pdf")
    assert up2["version_no"] == 1  # different title -> different document
