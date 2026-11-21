"""Worker process: bounded concurrency, heartbeats, retention housekeeping.

python -m procnav.workers.main
"""

from __future__ import annotations

import os
import signal
import socket
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime

from sqlalchemy import select

from ..core import tracing
from ..core.audit import log
from ..core.config import get_settings
from ..core.db import global_session, tenant_session
from ..core.models import Tenant, WorkerHeartbeat
from ..evidence import store
from . import jobs
from .runner import execute


def _beat(worker_id: str, active: int) -> None:
    with global_session() as s:
        row = s.get(WorkerHeartbeat, worker_id)
        now = datetime.now(UTC)
        if row is None:
            s.add(
                WorkerHeartbeat(
                    worker_id=worker_id,
                    seen_at=now,
                    active_jobs=active,
                    info={"host": socket.gethostname(), "pid": os.getpid()},
                )
            )
        else:
            row.seen_at, row.active_jobs = now, active


def _housekeeping() -> None:
    with global_session() as s:
        tenant_ids = s.scalars(select(Tenant.id)).all()
    for tid in tenant_ids:
        with tenant_session(tid) as db:
            n = store.purge_expired(db)
            if n:
                log.info("evidence_purged", tenant=str(tid), count=n)


def main() -> None:
    s = get_settings()
    worker_id = os.environ.get("WORKER_ID") or f"{s.worker_id}-{socket.gethostname()}-{os.getpid()}"
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    pool = ThreadPoolExecutor(max_workers=s.max_concurrent_runs, thread_name_prefix="run")
    running: set[Future] = set()
    last_beat = last_housekeeping = 0.0
    tracing.setup("procnav-worker")
    log.info("worker_started", worker=worker_id, concurrency=s.max_concurrent_runs)
    while not stop.is_set():
        running = {f for f in running if not f.done()}
        now = time.monotonic()
        if now - last_beat > s.job_heartbeat_seconds:
            _beat(worker_id, len(running))
            last_beat = now
        if now - last_housekeeping > 3600:
            _housekeeping()
            last_housekeeping = now
        free = s.max_concurrent_runs - len(running)
        if free > 0:
            for job in jobs.claim(worker_id, s.job_lease_seconds, limit=free):
                log.info("job_claimed", job=str(job.id), run=str(job.run_id), kind=job.kind)
                running.add(pool.submit(execute, job, worker_id))
        stop.wait(1.0)
    log.info("worker_stopping", worker=worker_id, active=len(running))
    pool.shutdown(wait=True)


if __name__ == "__main__":
    main()
