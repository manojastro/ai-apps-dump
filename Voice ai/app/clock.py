"""Simulated clock. Naive UTC datetimes everywhere.

Tests and demos freeze/advance it so timers (e.g. "3 days later") can be skipped.
Without freezing it follows the wall clock plus an optional offset.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

_frozen: datetime | None = None
_offset = timedelta(0)


def now() -> datetime:
    base = _frozen if _frozen is not None else datetime.now(timezone.utc).replace(tzinfo=None)
    return base + _offset


def freeze(dt: datetime) -> None:
    global _frozen, _offset
    _frozen, _offset = dt, timedelta(0)


def advance(delta: timedelta) -> None:
    global _offset
    _offset += delta


def set_to(dt: datetime) -> None:
    """Move the clock to an absolute time (only forward in practice)."""
    global _offset
    base = _frozen if _frozen is not None else datetime.now(timezone.utc).replace(tzinfo=None)
    _offset = dt - base


def reset() -> None:
    global _frozen, _offset
    _frozen, _offset = None, timedelta(0)
