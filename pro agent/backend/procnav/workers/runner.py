"""Execute one job: take the run lock, rebuild context, resume the graph from its checkpoint.

Playwright pages never survive a restart. A resumed node opens a fresh isolated context,
restores permitted encrypted session state, navigates again and re-observes before acting.
"""

from __future__ import annotations

import threading
import traceback
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from ..agents.context import CONTEXTS, RunContext
from ..agents.graph import build_graph
from ..core.audit import log, run_event
from ..core.config import get_settings
from ..core.db import app_engine, tenant_session
from ..core.models import Job, ProcurementRun
from . import jobs

TERMINAL = {"completed", "failed", "canceled", "rejected", "no_eligible_offer", "needs_clarification"}


def checkpoint_url() -> str:
    return get_settings().app_database_url.replace("postgresql+psycopg://", "postgresql://")


def thread_config(tenant_id: uuid.UUID, run_id: uuid.UUID) -> dict[str, Any]:
    # Tenant-qualified thread IDs; checkpoints are only ever loaded for a run the job row names.
    return {"configurable": {"thread_id": f"{tenant_id}:{run_id}"}, "recursion_limit": 200}


@contextmanager
def _heartbeat(job: Job, worker_id: str):
    s = get_settings()
    stop = threading.Event()

    def beat():
        while not stop.wait(s.job_heartbeat_seconds):
            jobs.heartbeat(job.id, worker_id, s.job_lease_seconds)

    t = threading.Thread(target=beat, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join(timeout=2)


def execute(job: Job, worker_id: str) -> str:
    with app_engine().connect() as lock_conn:
        if not jobs.try_run_lock(lock_conn, job.run_id):
            jobs.release(job.id, worker_id, delay_seconds=5)
            log.info("run_lock_busy", run=str(job.run_id), job=str(job.id))
            return "deferred"
        try:
            with tenant_session(job.tenant_id) as db:
                run = db.get(ProcurementRun, job.run_id)
                status = run.status if run else None
            if status is None or status in TERMINAL:
                jobs.complete(job.id, worker_id)
                return "skipped"
            ctx = RunContext(tenant_id=job.tenant_id, run_id=job.run_id, worker_id=worker_id)
            CONTEXTS[str(job.run_id)] = ctx
            try:
                with _heartbeat(job, worker_id), PostgresSaver.from_conn_string(checkpoint_url()) as saver:
                    graph = build_graph(saver)
                    config = thread_config(job.tenant_id, job.run_id)
                    snapshot = graph.get_state(config)
                    if job.kind == "start" and not snapshot.values:
                        graph.invoke({"run_id": str(job.run_id), "tenant_id": str(job.tenant_id)}, config)
                    elif snapshot.interrupts or any(t.interrupts for t in snapshot.tasks):
                        if job.kind in ("resume", "handoff"):
                            graph.invoke(Command(resume={"job_id": str(job.id), **(job.payload or {})}), config)
                        # a redelivered start job while waiting for a human: nothing to do
                    elif snapshot.next:
                        with tenant_session(job.tenant_id) as db:
                            run_event(
                                db,
                                job.tenant_id,
                                job.run_id,
                                "resumed_from_checkpoint",
                                {"next": list(snapshot.next), "worker": worker_id},
                            )
                        graph.invoke(None, config)  # resume after a crash from the last checkpoint
            finally:
                ctx.close()
                CONTEXTS.pop(str(job.run_id), None)
            jobs.complete(job.id, worker_id)
            return "done"
        except Exception as err:  # noqa: BLE001
            detail = f"{type(err).__name__}: {err}"
            log.error("job_failed", job=str(job.id), run=str(job.run_id), error=detail[:500])
            outcome = jobs.fail(job.id, worker_id, detail + "\n" + traceback.format_exc()[-3000:])
            with tenant_session(job.tenant_id) as db:
                run = db.get(ProcurementRun, job.run_id)
                run_event(db, job.tenant_id, job.run_id, "worker_error", {"error": detail[:300], "job_status": outcome})
                if outcome == "dead":
                    run.status, run.error_code, run.finished_at = "failed", "WORKER_ERROR", datetime.now(UTC)
            return "failed"
        finally:
            jobs.run_unlock(lock_conn, job.run_id)
