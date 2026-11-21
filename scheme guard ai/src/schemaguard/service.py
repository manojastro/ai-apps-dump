"""SchemaGuardService: owns stores, the lineage graph, the compiled agent and the run registry.

Used by the API, the worker/poller, the CLI and the eval harness. Run state lives in the LangGraph
checkpointer (thread_id = run_id); the `runs` table is an index with status and idempotency keys.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from schemaguard.agent.graph import build_graph
from schemaguard.agent.state import Deps
from schemaguard.config import Settings, get_settings
from schemaguard.lineage.builder import build_lineage
from schemaguard.lineage.store import SqlLineageStore
from schemaguard.llm import LLMClient, make_llm
from schemaguard.observability import configure_logging, get_logger, run_context
from schemaguard.schemas.avro import load_pipeline_schemas
from schemaguard.store.db import Database, open_database

log = get_logger("service")

RUNS_SQL = """create table if not exists runs (
    run_id text primary key,
    idempotency_key text unique not null,
    topic text not null,
    status text not null,
    created_at double precision not null,
    updated_at double precision not null,
    change_class text,
    error text,
    source text
)"""


def idempotency_key(topic: str, new_schema: dict[str, Any]) -> str:
    canonical = json.dumps(new_schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{topic}\n{canonical}".encode()).hexdigest()[:32]


class SchemaGuardService:
    def __init__(
        self, settings: Settings | None = None, llm: LLMClient | None = None, background: bool = False
    ):
        self.settings = s = settings or get_settings()
        configure_logging(s.log_level, s.otel_console)
        s.home.mkdir(parents=True, exist_ok=True)
        self.db: Database = open_database(s.database_url, s.sqlite_path)
        self.db.execute(RUNS_SQL)
        self.lineage_store = SqlLineageStore(self.db)
        self.pipeline_dir = Path(s.pipeline_dir)
        built = build_lineage(self.pipeline_dir)
        for w in built.warnings:
            log.warning("lineage warning", extra={"warning": w})
        version = self.lineage_store.save(built.graph, source=str(self.pipeline_dir))
        self.lineage = self.lineage_store.load(version)
        self.lineage_version = version
        self.deps = Deps(s, llm or make_llm(s), self.lineage, version, self.pipeline_dir)
        self._checkpointer, self._cp_conn = self._make_checkpointer()
        self.graph = build_graph(self.deps).compile(checkpointer=self._checkpointer)
        self._pool = ThreadPoolExecutor(max_workers=2) if background else None
        self._lock = threading.Lock()
        self.futures: dict[str, Future[Any]] = {}

    # ------------------------------------------------------------------ setup
    def _make_checkpointer(self) -> tuple[Any, Any]:
        s = self.settings
        if s.database_url:
            import psycopg
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg.rows import dict_row

            pg_conn = psycopg.connect(
                s.database_url, autocommit=True, prepare_threshold=0, row_factory=dict_row
            )
            pg_saver = PostgresSaver(pg_conn)
            pg_saver.setup()
            return pg_saver, pg_conn
        from langgraph.checkpoint.sqlite import SqliteSaver

        conn = sqlite3.connect(str(s.home / "checkpoints.db"), check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()
        return saver, conn

    def close(self) -> None:
        if self._pool:
            self._pool.shutdown(wait=True)
        self._cp_conn.close()
        self.db.close()

    # ------------------------------------------------------------------ runs
    def _cfg(self, run_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": run_id}, "recursion_limit": 100}

    def _set_status(
        self, run_id: str, status: str, error: str | None = None, change_class: str | None = None
    ) -> None:
        self.db.execute(
            "update runs set status = ?, updated_at = ?, error = coalesce(?, error), change_class = coalesce(?, change_class) where run_id = ?",
            (status, time.time(), error, change_class, run_id),
        )

    def submit_change(
        self,
        topic: str,
        new_schema: dict[str, Any],
        old_schema: dict[str, Any] | None = None,
        source: str = "api",
        subject: str = "",
        old_version: int | None = None,
        new_version: int | None = None,
    ) -> tuple[str, bool]:
        """Start a run. Returns (run_id, created). Same topic + schema => same run (idempotent)."""
        key = idempotency_key(topic, new_schema)
        existing = self.db.query("select run_id from runs where idempotency_key = ?", (key,))
        if existing:
            return existing[0][0], False
        if old_schema is None:
            current = load_pipeline_schemas(self.pipeline_dir / "avro")
            if topic not in current:
                raise KeyError(f"unknown topic {topic!r} and no old_schema given")
            old_schema = current[topic].raw
        run_id = uuid.uuid4().hex
        now = time.time()
        try:
            self.db.execute(
                "insert into runs(run_id, idempotency_key, topic, status, created_at, updated_at, source) values (?, ?, ?, ?, ?, ?, ?)",
                (run_id, key, topic, "running", now, now, source),
            )
        except Exception:  # lost a race with an identical submission
            existing = self.db.query("select run_id from runs where idempotency_key = ?", (key,))
            if existing:
                return existing[0][0], False
            raise
        event = {
            "topic": topic,
            "subject": subject or f"{topic}-value",
            "old_version": old_version,
            "new_version": new_version,
            "old_schema": old_schema,
            "new_schema": new_schema,
            "source": source,
            "received_at": now,
        }
        self._execute(run_id, {"run_id": run_id, "change_event": event, "errors": [], "assessments": []})
        return run_id, True

    def _execute(self, run_id: str, payload: Any) -> None:
        if self._pool:
            self.futures[run_id] = self._pool.submit(self._invoke, run_id, payload)
        else:
            self._invoke(run_id, payload)

    def _invoke(self, run_id: str, payload: Any) -> None:
        with run_context(run_id):
            try:
                self.graph.invoke(payload, self._cfg(run_id))
                self._sync_status(run_id)
            except Exception as exc:
                log.exception("run failed")
                self._set_status(run_id, "failed", error=f"{type(exc).__name__}: {exc}"[:1000])

    def _sync_status(self, run_id: str) -> str:
        snap = self.graph.get_state(self._cfg(run_id))
        values = snap.values or {}
        waiting = any(t.interrupts for t in snap.tasks)
        status = "awaiting_approval" if waiting else values.get("status", "running")
        cc = (values.get("change_class") or {}).get("change_class")
        self._set_status(run_id, status, change_class=cc)
        return status

    def approve(self, run_id: str, reviewer: str, comment: str = "") -> None:
        self._resume(run_id, {"decision": "approve", "reviewer": reviewer, "comment": comment})

    def reject(self, run_id: str, reviewer: str, comment: str = "") -> None:
        self._resume(run_id, {"decision": "reject", "reviewer": reviewer, "comment": comment})

    def _resume(self, run_id: str, answer: dict[str, Any]) -> None:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError(run_id)
        if run["status"] != "awaiting_approval":
            raise ValueError(f"run {run_id} is {run['status']}, not awaiting_approval")
        self._set_status(run_id, "running")
        self._execute(run_id, Command(resume=answer))

    def wait(self, run_id: str, timeout: float = 300) -> None:
        f = self.futures.get(run_id)
        if f:
            f.result(timeout=timeout)

    # ------------------------------------------------------------------ queries
    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.query(
            "select run_id, topic, status, change_class, created_at, updated_at, error, source from runs order by created_at desc limit ?",
            (limit,),
        )
        keys = ["run_id", "topic", "status", "change_class", "created_at", "updated_at", "error", "source"]
        return [dict(zip(keys, r, strict=True)) for r in rows]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        rows = self.db.query(
            "select run_id, topic, status, change_class, created_at, updated_at, error, source from runs where run_id = ?",
            (run_id,),
        )
        if not rows:
            return None
        keys = ["run_id", "topic", "status", "change_class", "created_at", "updated_at", "error", "source"]
        run = dict(zip(keys, rows[0], strict=True))
        snap = self.graph.get_state(self._cfg(run_id))
        run["state"] = snap.values or {}
        run["next"] = list(snap.next)
        run["pending_approval"] = [i.value for t in snap.tasks for i in t.interrupts]
        return run

    def mermaid(self) -> str:
        return self.graph.get_graph().draw_mermaid()
