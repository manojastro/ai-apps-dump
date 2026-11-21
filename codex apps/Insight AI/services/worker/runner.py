"""Database-authoritative jobs. Redis/RQ is an optional dispatch accelerator."""

import signal
import threading
import time
import uuid
from contextlib import contextmanager
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import or_, select, update

from packages.agent.contracts import Budget, Diagnosis, Evidence, action_hash, verify_recovery
from packages.agent.scripted import diagnose
from packages.connectors.replay import ConnectorError, ReplayConnector, snapshot
from services.api.db import (
    DATA,
    DATABASE_URL,
    Action,
    Audit,
    EvidenceRow,
    Execution,
    Incident,
    Job,
    Run,
    Session,
    Setting,
    add_event,
)

TERMINAL = {"completed", "failed", "inconclusive", "cancelled", "budget_exceeded"}


class Cancelled(Exception):
    pass


class GraphState(TypedDict):
    run_id: str


def check_run(db, run_id):
    run = db.get(Run, run_id)
    if not run or run.status in TERMINAL:
        raise Cancelled()
    return run


def collect(run_id, tool, parameters=None):
    with Session() as db:
        run = check_run(db, run_id)
        state = dict(run.state)
        previous = next(
            (x for x in state.get("tools", []) if x["tool"] == tool and x["inputs"] == (parameters or {})),
            None,
        )
        if previous:
            return previous
        budget = Budget(**state.get("budget", {"tool_limit": state.get("tool_limit", 12)}))
        budget.reserve_tool()
        state["budget"] = budget.model_dump()
        run.state = state
        run.status = "investigating"
        incident = db.get(Incident, run.incident_id)
        packet, mode = incident.snapshot, run.mode
        db.commit()  # Reserve before I/O; replaying a crash can consume another reservation.
    start = time.perf_counter()
    evidence, error = None, None
    try:
        if mode == "replay":
            evidence = ReplayConnector(packet).call(tool, run_id, parameters)
        else:
            from packages.connectors.live import LiveConnector

            evidence = LiveConnector().call(tool, run_id, parameters)
    except ConnectorError as exc:
        error = exc.code
    duration = round((time.perf_counter() - start) * 1000, 2)
    result = {
        "tool": tool,
        "inputs": parameters or {},
        "duration_ms": duration,
        "status": "error" if error else "success",
        "error": error,
        "evidence_ids": [evidence.id] if evidence else [],
        "output": evidence.model_dump() if evidence else {"error": error},
    }
    with Session() as db:
        run = check_run(db, run_id)
        state = dict(run.state)
        state["tools"] = [*state.get("tools", []), result]
        run.state = state
        if evidence:
            db.add(EvidenceRow(id=evidence.id, run_id=run_id, data=evidence.model_dump()))
        add_event(db, run_id, "tool", f"{tool}: {evidence.summary if evidence else error}", result)
        db.commit()
    return result


def initial_context(state: GraphState):
    collect(state["run_id"], "query_metrics")
    collect(state["run_id"], "get_service_dependencies")
    return state


def investigate(state: GraphState):
    run_id = state["run_id"]
    with Session() as db:
        mode = check_run(db, run_id).mode
    if mode == "live":
        from packages.agent.live import live_investigate

        live_investigate(run_id, collect)
    else:
        for tool in ("search_traces", "search_logs", "get_deployments", "compare_config"):
            collect(run_id, tool)
        with Session() as db:
            run = check_run(db, run_id)
            evidence = [
                Evidence(**e.data)
                for e in db.scalars(select(EvidenceRow).where(EvidenceRow.run_id == run_id))
            ]
            diagnosis = diagnose(evidence)
            diagnosis.validate_evidence(evidence, run_id)
            run.state = {**run.state, "diagnosis": diagnosis.model_dump()}
            add_event(db, run_id, "finding", diagnosis.explanation, diagnosis.model_dump())
            db.commit()
    return state


def prepare(state: GraphState):
    with Session() as db:
        run = check_run(db, state["run_id"])
        diagnosis = Diagnosis(**run.state["diagnosis"])
        evidence = [
            Evidence(**e.data) for e in db.scalars(select(EvidenceRow).where(EvidenceRow.run_id == run.id))
        ]
        diagnosis.validate_evidence(evidence, run.id)
        supported_fault = diagnosis.confidence == "supported" and diagnosis.category not in {
            "healthy",
            "inconclusive",
        }
        if supported_fault and run.mode == "replay":
            setting = db.get(Setting, "demo")
            revision = setting.data.get("revision", 0) if setting else 0
            proposal = {
                "operation": "reset_demo",
                "target": "replay-lab",
                "parameters": {"revision": revision},
                "mode": "replay",
                "evidence_ids": diagnosis.evidence_ids,
                "expected_effect": "Reset replay fault and compare a fresh scripted healthy sample",
                "risk": "Low: modifies only this local replay lab; no production effects",
                "preconditions": [
                    "Demo revision unchanged",
                    "Reviewer approval is current",
                    "Run not cancelled",
                ],
                "rollback": "Re-activate a bounded scenario in Demo lab",
            }
            if not db.scalar(select(Action).where(Action.run_id == run.id)):
                db.add(
                    Action(
                        run_id=run.id,
                        proposal=proposal,
                        digest=action_hash(proposal),
                        expires_at=time.time() + 900,
                    )
                )
            run.status = "awaiting_review"
            add_event(db, run.id, "review", "Recovery proposal awaits review of its exact parameters")
        else:
            run.status = "inconclusive" if diagnosis.category == "inconclusive" else "completed"
            add_event(
                db,
                run.id,
                run.status,
                "Findings saved. Live mutation is unavailable in this release."
                if run.mode == "live"
                else "Investigation report is ready",
            )
        run.state = {
            **run.state,
            "verification_plan": "Compare error rate and p95 under comparable traffic; require at least 30 fresh requests",
            "completed_at": time.time(),
        }
        db.get(Incident, run.incident_id).status = run.status
        db.commit()
    return state


@contextmanager
def saver():
    if DATABASE_URL.startswith("postgresql"):
        from langgraph.checkpoint.postgres import PostgresSaver

        with PostgresSaver.from_conn_string(
            DATABASE_URL.replace("postgresql+psycopg", "postgresql")
        ) as checkpoint:
            checkpoint.setup()
            yield checkpoint
    else:
        from langgraph.checkpoint.sqlite import SqliteSaver

        with SqliteSaver.from_conn_string(str(DATA / "checkpoints.db")) as checkpoint:
            yield checkpoint


def process_investigation(run_id):
    with Session() as db:
        run = db.get(Run, run_id)
        if not run or run.status in TERMINAL or run.status == "awaiting_review":
            return
    builder = StateGraph(GraphState)
    builder.add_node("initial_context", initial_context)
    builder.add_node("investigate", investigate)
    builder.add_node("prepare_findings", prepare)
    builder.add_edge(START, "initial_context")
    builder.add_edge("initial_context", "investigate")
    builder.add_edge("investigate", "prepare_findings")
    builder.add_edge("prepare_findings", END)
    try:
        with saver() as checkpoint:
            graph = builder.compile(checkpointer=checkpoint)
            config = {"configurable": {"thread_id": run_id}}
            saved = graph.get_state(config)
            graph.invoke(None if saved.next else {"run_id": run_id}, config)
    except Cancelled:
        return
    except Exception as exc:
        with Session() as db:
            run = db.get(Run, run_id)
            if run.status != "cancelled":
                status = "budget_exceeded" if "budget" in str(exc).lower() else "failed"
                run.status = status
                # Provider and connector adapters expose only normalized, secret-free exceptions.
                message = (
                    str(exc)[:300] if isinstance(exc, (ValueError, ConnectorError)) else type(exc).__name__
                )
                run.state = {**run.state, "error": message}
                add_event(db, run_id, status, message)
                db.commit()


def execute_action(action_id):
    # Replay mutation and executor deduplication share one database transaction.
    with Session() as db:
        claimed = db.execute(
            update(Action)
            .where(Action.id == action_id, Action.status == "approved")
            .values(status="executing")
        )
        if not claimed.rowcount:
            return
        action = db.get(Action, action_id)
        run = db.get(Run, action.run_id)
        setting = db.get(Setting, "demo")
        current = dict(setting.data) if setting else {"mode": "replay", "revision": 0}
        p = action.proposal
        valid = (
            action.expires_at > time.time()
            and action_hash(p) == action.digest
            and run.status == "awaiting_review"
            and run.mode == "replay"
            and p["operation"] == "reset_demo"
            and p["target"] == "replay-lab"
            and p["parameters"] == {"revision": current.get("revision", 0)}
            and action.reviewer is not None
        )
        if not valid:
            action.status = "blocked"
            action.result = {
                "error": "Execution preconditions changed or approval expired; create a new investigation"
            }
            add_event(db, run.id, "blocked", action.result["error"])
            run.status = "completed"
            db.commit()
            return
        current.update(fault=None, revision=current.get("revision", 0) + 1, expires_at=None)
        if setting:
            setting.data = current
        else:
            db.add(Setting(id="demo", data=current))
        incident = db.get(Incident, run.incident_id)
        after_packet = snapshot("healthy")
        after = after_packet["metrics"]
        recovery = verify_recovery(incident.snapshot.get("metrics", {}), after)
        recovery.update(
            mode="replay",
            measurement="Fresh scripted fixture, not live service telemetry",
            observed_at=after_packet["observed_at"],
        )
        fresh = Evidence.make(
            run.id,
            "metrics",
            after,
            "Post-reset replay sample: 240 requests at the healthy baseline",
            observed_at=after_packet["observed_at"],
            source_record_id="fixture-v1/recovery",
        )
        db.add(EvidenceRow(id=fresh.id, run_id=run.id, data=fresh.model_dump()))
        db.add(Execution(action_id=action_id, result=recovery))
        action.status, action.result = "executed", recovery
        run.status = "completed"
        run.state = {**run.state, "recovery": recovery}
        incident.status = "resolved" if recovery["verified"] else "open"
        add_event(db, run.id, "recovery", recovery["reason"], recovery)
        db.add(
            Audit(
                actor="restricted-replay-executor",
                operation="demo.reset",
                target=action_id,
                data={"hash": action.digest},
            )
        )
        db.commit()


def claim_job(owner):
    with Session() as db:
        eligible = or_(Job.status == "queued", (Job.status == "running") & (Job.lease_until < time.time()))
        job = db.scalar(select(Job).where(eligible).order_by(Job.created_at).limit(1))
        if not job:
            return None
        updated = db.execute(
            update(Job)
            .where(Job.id == job.id, eligible)
            .values(status="running", lease_until=time.time() + 300, owner=owner, attempts=Job.attempts + 1)
        )
        db.commit()
        return job.id if updated.rowcount else None


def work_once():
    owner = str(uuid.uuid4())
    job_id = claim_job(owner)
    if not job_id:
        return False
    with Session() as db:
        job = db.get(Job, job_id)
        kind, target = job.kind, job.target_id
    error = None
    stop_renewing = threading.Event()

    def renew_lease():
        while not stop_renewing.wait(10):
            with Session() as db:
                db.execute(
                    update(Job)
                    .where(Job.id == job_id, Job.owner == owner, Job.status == "running")
                    .values(lease_until=time.time() + 300)
                )
                heartbeat = db.get(Setting, "worker")
                if heartbeat:
                    heartbeat.data = {"at": time.time()}
                db.commit()

    renewal = threading.Thread(target=renew_lease, daemon=True)
    renewal.start()
    try:
        if kind == "investigate":
            process_investigation(target)
        elif kind == "execute":
            execute_action(target)
        elif kind == "evaluate":
            from packages.evaluation.harness import process_evaluation

            process_evaluation(target)
        else:
            raise ValueError("UNKNOWN_JOB_TYPE")
    except Exception as exc:
        error = type(exc).__name__
    finally:
        stop_renewing.set()
        renewal.join(timeout=2)
    with Session() as db:
        if error and kind == "evaluate":
            from services.api.db import Evaluation

            evaluation = db.get(Evaluation, target)
            if evaluation and evaluation.status != "cancelled":
                evaluation.status = "failed"
                evaluation.report = {"mode": evaluation.mode, "error": error}
        db.execute(
            update(Job)
            .where(Job.id == job_id, Job.owner == owner)
            .values(status="failed" if error else "completed", error=error)
        )
        db.commit()
    return True


def main():
    stop = False

    def shutdown(*_):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    while not stop:
        with Session() as db:
            heartbeat = db.get(Setting, "worker")
            if heartbeat:
                heartbeat.data = {"at": time.time()}
            else:
                db.add(Setting(id="worker", data={"at": time.time()}))
            demo = db.get(Setting, "demo")
            if demo and demo.data.get("expires_at") and demo.data["expires_at"] < time.time():
                demo.data = {
                    **demo.data,
                    "fault": None,
                    "expires_at": None,
                    "revision": demo.data["revision"] + 1,
                }
            db.commit()
        if not work_once():
            time.sleep(0.75)


if __name__ == "__main__":
    main()
