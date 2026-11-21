"""PostgreSQL-backed job queue with leases, heartbeats and bounded retries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.db import global_session
from ..core.models import Job


def enqueue(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    kind: str,
    dedupe_key: str,
    payload: dict[str, Any] | None = None,
    delay_seconds: int = 0,
) -> Job | None:
    """Insert a job unless one with the same dedupe key exists (idempotent enqueue)."""
    job = Job(
        tenant_id=tenant_id,
        run_id=run_id,
        kind=kind,
        dedupe_key=dedupe_key,
        payload=payload or {},
        available_at=datetime.now(UTC) + timedelta(seconds=delay_seconds),
    )
    try:
        with session.begin_nested():
            session.add(job)
            session.flush()
    except IntegrityError:
        return None
    return job


def claim(worker_id: str, lease_seconds: int, limit: int = 1) -> list[Job]:
    """Claim available jobs, including ones whose lease expired (worker died)."""
    now = datetime.now(UTC)
    with global_session() as s:
        rows = s.scalars(
            select(Job)
            .where(
                or_(Job.status == "queued", (Job.status == "leased") & (Job.lease_expires_at < now)),
                Job.available_at <= now,
            )
            .order_by(Job.available_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        ).all()
        for job in rows:
            job.status = "leased"
            job.lease_owner = worker_id
            job.lease_expires_at = now + timedelta(seconds=lease_seconds)
            job.heartbeat_at = now
            job.attempts += 1
        s.flush()
        for job in rows:
            s.expunge(job)
        return list(rows)


def heartbeat(job_id: uuid.UUID, worker_id: str, lease_seconds: int) -> bool:
    now = datetime.now(UTC)
    with global_session() as s:
        res = s.execute(
            update(Job)
            .where(Job.id == job_id, Job.lease_owner == worker_id, Job.status == "leased")
            .values(heartbeat_at=now, lease_expires_at=now + timedelta(seconds=lease_seconds))
        )
        return res.rowcount == 1


def complete(job_id: uuid.UUID, worker_id: str) -> None:
    with global_session() as s:
        s.execute(update(Job).where(Job.id == job_id, Job.lease_owner == worker_id).values(status="done"))


def fail(job_id: uuid.UUID, worker_id: str, error: str, retry_in: int = 10) -> str:
    with global_session() as s:
        job = s.get(Job, job_id)
        if job is None or job.lease_owner != worker_id:
            return "lost"
        job.last_error = error[:2000]
        if job.attempts >= job.max_attempts:
            job.status = "dead"
        else:
            job.status = "queued"
            job.available_at = datetime.now(UTC) + timedelta(seconds=retry_in * job.attempts)
        return job.status


def release(job_id: uuid.UUID, worker_id: str, delay_seconds: int) -> None:
    """Give a job back without counting the attempt (e.g. run lock held elsewhere)."""
    with global_session() as s:
        job = s.get(Job, job_id)
        if job and job.lease_owner == worker_id:
            job.status = "queued"
            job.attempts = max(0, job.attempts - 1)
            job.available_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)


def try_run_lock(conn, run_id: uuid.UUID) -> bool:
    return bool(
        conn.execute(text("SELECT pg_try_advisory_lock(hashtextextended(:k, 0))"), {"k": f"run:{run_id}"}).scalar()
    )


def run_unlock(conn, run_id: uuid.UUID) -> None:
    conn.execute(text("SELECT pg_advisory_unlock(hashtextextended(:k, 0))"), {"k": f"run:{run_id}"})
