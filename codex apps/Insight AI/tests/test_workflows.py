import time

from sqlalchemy import func, select

from services.api.db import Action, Execution, Job, Session
from services.worker.runner import claim_job, execute_action, process_investigation


def investigated(client, fixture="payment_delay", tool_limit=12):
    incident = client.post(
        "/api/incidents", json={"title": "Replay checkout investigation", "fixture": fixture}
    ).json()
    run = client.post(
        "/api/investigations", json={"incident_id": incident["id"], "tool_limit": tool_limit}
    ).json()
    process_investigation(run["id"])
    return client.get(f"/api/investigations/{run['id']}").json()


def test_replay_evidence_and_checkpoint_resume(client):
    run = investigated(client)
    assert run["status"] == "awaiting_review"
    assert run["state"]["diagnosis"]["category"] == "payment_delay"
    process_investigation(run["id"])
    refreshed = client.get(f"/api/investigations/{run['id']}").json()
    assert len(refreshed["evidence"]) == len(run["evidence"]) == 6


def test_cross_run_evidence_denied(client):
    first, second = investigated(client), investigated(client)
    evidence_id = first["evidence"][0]["id"]
    assert client.get(f"/api/investigations/{second['id']}/evidence/{evidence_id}").status_code == 404


def test_rejected_action_never_executes(client):
    run = investigated(client)
    action = run["action"]
    assert (
        client.post(f"/api/actions/{action['id']}/reject", json={"action_hash": action["digest"]}).status_code
        == 200
    )
    execute_action(action["id"])
    with Session() as db:
        assert (
            db.scalar(select(func.count()).select_from(Execution).where(Execution.action_id == action["id"]))
            == 0
        )


def test_approved_action_executes_once_with_verification(client):
    run = investigated(client)
    action = run["action"]
    assert (
        client.post(
            f"/api/actions/{action['id']}/approve", json={"action_hash": action["digest"]}
        ).status_code
        == 200
    )
    execute_action(action["id"])
    execute_action(action["id"])
    updated = client.get(f"/api/investigations/{run['id']}").json()
    assert updated["action"]["result"]["verified"]
    with Session() as db:
        assert (
            db.scalar(select(func.count()).select_from(Execution).where(Execution.action_id == action["id"]))
            == 1
        )


def test_tampered_and_expired_approvals_denied(client):
    run = investigated(client)
    action = run["action"]
    assert (
        client.post(f"/api/actions/{action['id']}/approve", json={"action_hash": "0" * 64}).status_code == 409
    )
    with Session() as db:
        db.get(Action, action["id"]).expires_at = time.time() - 1
        db.commit()
    assert (
        client.post(
            f"/api/actions/{action['id']}/approve", json={"action_hash": action["digest"]}
        ).status_code
        == 409
    )


def test_insufficient_evidence_abstains(client):
    run = investigated(client, "missing_evidence")
    assert run["status"] == "inconclusive"
    assert run["action"] is None


def test_budget_exhaustion_is_terminal(client):
    assert investigated(client, tool_limit=1)["status"] == "budget_exceeded"


def test_expired_worker_lease_reclaimable():
    with Session() as db:
        # Isolate this claim test from queued jobs left by API workflow fixtures.
        for row in db.scalars(select(Job)):
            row.status = "completed"
        job = Job(kind="investigate", target_id="orphan", status="running", lease_until=time.time() - 1)
        db.add(job)
        db.commit()
        job_id = job.id
    assert claim_job("new-worker") == job_id
    assert claim_job("duplicate-worker") is None
