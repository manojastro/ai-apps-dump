"""Durable event queue on a SQLite outbox table.

At-least-once delivery: a worker claims an event atomically, processes it, and marks it DONE.
If the worker dies, the claim lease expires and the event goes back to PENDING.
Failures retry with exponential backoff and become DEAD after max attempts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app import clock
from app.config import get_settings
from app.data.db import get_engine, session
from app.data.models import Outbox

EVENT_TYPES = (
    "BOOKING_REQUESTED",
    "VISIT_COMPLETED",
    "CHECKIN_RECEIVED",
    "STOCK_LOW",
    "TIMER_DUE",
    "APPROVAL_DECIDED",  # extra: lets approvals wake workflows durably
)


@dataclass
class ClaimedEvent:
    id: int
    type: str
    payload: dict
    attempts: int


def enqueue(type: str, payload: dict, *, available_at: datetime | None = None, dedupe_key: str | None = None) -> int:
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type {type}")
    now = clock.now()
    try:
        with session() as s:
            ev = Outbox(type=type, payload=payload, status="PENDING", attempts=0,
                        available_at=available_at or now, dedupe_key=dedupe_key, created_at=now)
            s.add(ev)
            s.flush()
            return ev.id
    except IntegrityError:
        with session() as s:
            existing = s.scalar(select(Outbox.id).where(Outbox.dedupe_key == dedupe_key))
            assert existing is not None
            return existing


def claim(worker_id: str) -> ClaimedEvent | None:
    """Atomically claim the oldest available event (single UPDATE ... RETURNING)."""
    now = clock.now()
    sub = (
        select(Outbox.id)
        .where(Outbox.status == "PENDING", Outbox.available_at <= now)
        .order_by(Outbox.available_at, Outbox.id)
        .limit(1)
        .scalar_subquery()
    )
    stmt = (
        update(Outbox)
        .where(Outbox.id == sub, Outbox.status == "PENDING")
        .values(status="CLAIMED", claimed_by=worker_id, claimed_at=now, attempts=Outbox.attempts + 1)
        .returning(Outbox.id, Outbox.type, Outbox.payload, Outbox.attempts)
    )
    with get_engine().begin() as conn:
        row = conn.execute(stmt).first()
    if row is None:
        return None
    return ClaimedEvent(id=row.id, type=row.type, payload=row.payload, attempts=row.attempts)


def complete(event_id: int, worker_id: str) -> None:
    with session() as s:
        s.execute(update(Outbox).where(Outbox.id == event_id, Outbox.claimed_by == worker_id)
                  .values(status="DONE", last_error=None))


def fail(event_id: int, worker_id: str, error: str) -> str:
    """Release a claimed event after a failure. Returns the new status."""
    cfg = get_settings()
    now = clock.now()
    with session() as s:
        ev = s.get(Outbox, event_id)
        if ev is None or ev.claimed_by != worker_id:
            return "UNKNOWN"
        ev.last_error = error[:500]
        if ev.attempts >= cfg.max_attempts:
            ev.status = "DEAD"
        else:
            ev.status = "PENDING"
            ev.available_at = now + timedelta(seconds=cfg.backoff_base_seconds * 2 ** (ev.attempts - 1))
        return ev.status


def reclaim_expired() -> int:
    """Return events whose worker vanished (lease expired) to PENDING, or DEAD if out of attempts."""
    cfg = get_settings()
    now = clock.now()
    cutoff = now - timedelta(seconds=cfg.queue_lease_seconds)
    n = 0
    with session() as s:
        stale = s.scalars(select(Outbox).where(Outbox.status == "CLAIMED", Outbox.claimed_at <= cutoff)).all()
        for ev in stale:
            ev.last_error = "lease expired (worker crashed?)"
            if ev.attempts >= cfg.max_attempts:
                ev.status = "DEAD"
            else:
                ev.status = "PENDING"
                ev.available_at = now
            n += 1
    return n


def counts() -> dict[str, int]:
    with session() as s:
        rows = s.execute(select(Outbox.status, Outbox.id)).all()
    out: dict[str, int] = {}
    for status, _ in rows:
        out[status] = out.get(status, 0) + 1
    return out


def next_pending_time() -> datetime | None:
    with session() as s:
        return s.scalar(select(Outbox.available_at).where(Outbox.status == "PENDING")
                        .order_by(Outbox.available_at).limit(1))
