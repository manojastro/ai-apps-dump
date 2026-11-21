"""SLA lookup — code decides the promise, LLM only phrases it."""

from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml

from ticketsort.domain.models import Priority

_CACHE: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    p = Path(__file__).resolve().parents[3] / "config" / "sla.yaml"
    if not p.exists():
        p = Path("config/sla.yaml")
    _CACHE = yaml.safe_load(p.read_text()) or {}
    return _CACHE


def sla_for(priority: Priority) -> timedelta:
    """Return response target for a priority. Defaults to 24h."""
    hours = int(_load().get(priority.value, 24))
    return timedelta(hours=hours)
