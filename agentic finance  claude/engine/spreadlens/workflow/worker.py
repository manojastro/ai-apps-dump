"""Worker loop with bounded concurrency. Run standalone: `uv run python -m spreadlens.workflow.worker`."""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from spreadlens.config import Settings, get_settings
from spreadlens.db import _factory, session_scope
from spreadlens.observability import configure, log
from spreadlens.workflow.coordinator import claim, execute_task

logger = logging.getLogger("spreadlens.worker")


class Worker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.id = f"{socket.gethostname()}:{os.getpid()}:{id(self) % 10000}"
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def run_once(self) -> str | None:
        """Claim and execute one task. Returns outcome or None when the queue is empty."""
        with session_scope() as db:
            task_id = claim(db, self.id, self.settings.worker_lease_s + int(self.settings.stage_timeout_s))
        if task_id is None:
            return None
        outcome = execute_task(_factory(), self.settings, task_id, self.id)
        log(logger, logging.INFO, "task processed", task_id=task_id, outcome=outcome)
        return outcome

    def drain(self, max_tasks: int = 500) -> int:
        """Process until the queue is empty (used by tests and the CLI)."""
        n = 0
        while n < max_tasks:
            if self.run_once() is None:
                return n
            n += 1
        return n

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if self.run_once() is None:
                    self._stop.wait(self.settings.worker_poll_s)
            except Exception:  # noqa: BLE001
                logger.exception("worker loop error")
                self._stop.wait(2)

    def start(self) -> None:
        for _ in range(self.settings.worker_concurrency):
            t = threading.Thread(target=self._loop, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)


def drain_parallel(settings: Settings, workers: int = 4, timeout_s: float = 300) -> None:
    """Process the queue with several concurrent workers until no task is queued or running."""
    from sqlalchemy import func, select

    from spreadlens.models import WorkflowTask

    pool = [Worker(settings) for _ in range(workers)]
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            outcomes = list(ex.map(lambda w: w.run_once(), pool))
        if all(o is None for o in outcomes):
            with session_scope() as db:
                pending = db.scalar(select(func.count()).select_from(WorkflowTask).where(WorkflowTask.status.in_(["queued", "running"])))
            if not pending:
                return
            time.sleep(0.5)


if __name__ == "__main__":
    s = get_settings()
    configure(s.log_level, s.otel_exporter_otlp_endpoint)
    w = Worker(s)
    w.start()
    log(logger, logging.INFO, "worker started", concurrency=s.worker_concurrency, mode=s.agent_mode)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        w.stop()
