"""Durable workflow execution: checkpointing, background execution, resume and crash recovery."""

from __future__ import annotations

import logging
import sqlite3
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import session_scope
from app.core.types import utcnow
from app.graphs.investigation import build_graph
from app.llm.base import LLMProvider
from app.llm.factory import build_provider
from app.models.enums import WorkflowStatus
from app.models.vulnerability import Finding
from app.models.workflow import WorkflowEvent, WorkflowRun
from app.observability.logging import workflow_id_var

log = logging.getLogger("aegis.workflow")


class WorkflowConflict(Exception):
    pass


def make_checkpointer(url: str | None = None) -> tuple[BaseCheckpointSaver[Any], Any]:
    """Return (saver, closeable). PostgreSQL in production, SQLite file locally, memory in tests."""
    url = url or get_settings().checkpoint_database_url or get_settings().database_url
    if url.startswith("postgresql"):
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        conninfo = url.replace("postgresql+psycopg://", "postgresql://")
        pool = ConnectionPool(
            conninfo, max_size=10, kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row}, open=True
        )
        saver = PostgresSaver(pool)  # type: ignore[arg-type]
        saver.setup()
        return saver, pool
    if url.startswith("sqlite") and ":memory:" not in url and url not in ("sqlite://", "sqlite:///"):
        from langgraph.checkpoint.sqlite import SqliteSaver

        path = url.split("///", 1)[1]
        conn = sqlite3.connect(path.replace(".db", "_checkpoints.db"), check_same_thread=False)
        sqlite_saver = SqliteSaver(conn)
        sqlite_saver.setup()
        return sqlite_saver, conn
    return InMemorySaver(), None


class WorkflowRunner:
    def __init__(
        self,
        checkpointer: BaseCheckpointSaver[Any] | None = None,
        provider: LLMProvider | None = None,
        workers: int | None = None,
        synchronous: bool = False,
    ) -> None:
        if checkpointer is None:
            checkpointer, self._closeable = make_checkpointer()
        else:
            self._closeable = None
        self.checkpointer = checkpointer
        self.provider = provider
        self.graph = build_graph(provider).compile(checkpointer=checkpointer)
        self.synchronous = synchronous
        self.executor = ThreadPoolExecutor(
            max_workers=workers or get_settings().workflow_workers, thread_name_prefix="aegis-workflow"
        )
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()
        self._futures: list[Future[None]] = []

    # ------------------------------------------------------------------ internals
    def _lock(self, run_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(run_id, threading.Lock())

    @staticmethod
    def config(run_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": run_id}, "recursion_limit": 100}

    def _invoke(self, run_id: str, payload: Any) -> None:
        workflow_id_var.set(run_id)
        with self._lock(run_id):
            try:
                self.graph.invoke(payload, self.config(run_id))
            except Exception as exc:
                log.exception("workflow failed", extra={"run_id": run_id})
                with session_scope() as db:
                    run = db.get(WorkflowRun, run_id)
                    if run is not None:
                        run.status = WorkflowStatus.FAILED
                        run.error = f"{type(exc).__name__}: {str(exc)[:1500]}"
                        run.completed_at = utcnow()
                        db.add(
                            WorkflowEvent(
                                workflow_run_id=run_id,
                                event_type="error",
                                node=run.current_node,
                                message=f"Workflow failed: {type(exc).__name__}",
                                payload={"error": str(exc)[:500]},
                            )
                        )
                return
            snapshot = self.graph.get_state(self.config(run_id))
            if not snapshot.next:
                with session_scope() as db:
                    run = db.get(WorkflowRun, run_id)
                    if run is not None and run.status not in WorkflowStatus.terminal():
                        run.status = WorkflowStatus.COMPLETED
                        run.completed_at = utcnow()

    def _submit(self, run_id: str, payload: Any) -> Future[None] | None:
        if self.synchronous:
            self._invoke(run_id, payload)
            return None
        future = self.executor.submit(self._invoke, run_id, payload)
        with self._locks_guard:
            self._futures = [f for f in self._futures if not f.done()] + [future]
        return future

    # ------------------------------------------------------------------ public API
    def start(self, finding_id: str, started_by: str | None) -> WorkflowRun:
        with session_scope() as db:
            finding = db.get(Finding, finding_id)
            if finding is None:
                raise WorkflowConflict("Finding not found")
            active = db.scalar(
                select(WorkflowRun).where(WorkflowRun.finding_id == finding_id, WorkflowRun.status.in_(WorkflowStatus.active()))
            )
            if active is not None:
                raise WorkflowConflict(f"An investigation is already active for this finding ({active.id})")
            provider = self.provider or build_provider()
            run = WorkflowRun(
                finding_id=finding_id,
                status=WorkflowStatus.QUEUED,
                started_by=started_by,
                provider=provider.name,
                model=provider.model,
            )
            db.add(run)
            db.flush()
            db.add(
                WorkflowEvent(
                    workflow_run_id=run.id,
                    event_type="status",
                    node=None,
                    message="Investigation queued",
                    payload={"provider": provider.name},
                )
            )
            run_id = run.id
        initial = {"run_id": run_id, "finding_id": finding_id, "started_by": started_by}
        self._submit(run_id, initial)
        with session_scope() as db:
            created = db.get(WorkflowRun, run_id)
            assert created is not None
            db.expunge(created)
            return created

    def resume(self, run_id: str, value: dict[str, Any], expected: set[str] | None = None) -> None:
        with session_scope() as db:
            run = db.get(WorkflowRun, run_id)
            if run is None:
                raise WorkflowConflict("Workflow run not found")
            if expected and run.status not in expected:
                raise WorkflowConflict(f"Workflow is {run.status}; cannot resume for this action")
            run.resume_count += 1
            db.add(
                WorkflowEvent(
                    workflow_run_id=run_id,
                    event_type="resumed",
                    node=run.current_node,
                    message=f"Workflow resumed ({value.get('type', 'input')})",
                    payload={k: v for k, v in value.items() if k != "actor_id"},
                )
            )
        self._submit(run_id, Command(resume=value))

    def pending_interrupt(self, run_id: str) -> dict[str, Any] | None:
        snap = self.graph.get_state(self.config(run_id))
        for task in snap.tasks:
            for intr in getattr(task, "interrupts", ()) or ():
                return {"node": task.name, "value": intr.value}
        return None

    def recover(self) -> int:
        """Resume runs that were executing when the process stopped (crash/restart recovery)."""
        with session_scope() as db:
            ids = list(
                db.scalars(select(WorkflowRun.id).where(WorkflowRun.status.in_([WorkflowStatus.QUEUED, WorkflowStatus.RUNNING])))
            )
        for run_id in ids:
            snap = self.graph.get_state(self.config(run_id))
            with session_scope() as db:
                db.add(
                    WorkflowEvent(
                        workflow_run_id=run_id,
                        event_type="recovered",
                        node=None,
                        message="Resuming from last durable checkpoint after restart",
                        payload={},
                    )
                )
            if snap.values:
                self._submit(run_id, None)  # continue from last checkpoint
            else:
                with session_scope() as db:
                    run = db.get(WorkflowRun, run_id)
                    initial = {"run_id": run_id, "finding_id": run.finding_id, "started_by": run.started_by} if run else None
                if initial:
                    self._submit(run_id, initial)
        if ids:
            log.info("recovered %d interrupted workflow(s)", len(ids))
        return len(ids)

    def wait_idle(self, timeout: float = 60.0) -> None:
        """Block until all submitted work has finished (tests, seeding, graceful shutdown)."""
        from concurrent.futures import wait

        with self._locks_guard:
            pending = [f for f in self._futures if not f.done()]
        wait(pending, timeout=timeout)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=False)
        if self._closeable is not None:
            try:
                self._closeable.close()
            except Exception:  # pragma: no cover - best effort during shutdown
                log.debug("checkpointer close failed", exc_info=True)


_runner: WorkflowRunner | None = None


def get_runner() -> WorkflowRunner:
    global _runner
    if _runner is None:
        _runner = WorkflowRunner()
    return _runner


def set_runner(runner: WorkflowRunner | None) -> None:
    global _runner
    if _runner is not None and runner is not _runner:
        _runner.shutdown()
    _runner = runner
