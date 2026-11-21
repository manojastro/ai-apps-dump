"""Routing (X-Task -> primary + fallback) and per-tenant exact-match cache."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path

import yaml


def load_routing_policy(path: str) -> dict[str, object]:
    return dict(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def route(task: str | None, policy: dict[str, object]) -> tuple[str, str]:
    """Return (primary, fallback) for an X-Task value; unknown -> general."""
    tasks = policy.get("tasks")
    assert isinstance(tasks, dict)
    default = str(policy.get("default_task", "general"))
    entry = tasks.get((task or default).strip() or default, tasks.get(default))
    assert isinstance(entry, dict)
    return str(entry["primary"]), str(entry["fallback"])


def cache_key(tenant: str, model: str, messages: list[dict[str, str]],
              temperature: float) -> str:
    """Tenant-scoped exact-match key (never shared across tenants)."""
    payload = json.dumps(
        {"tenant": tenant, "model": model, "messages": messages,
         "temperature": temperature},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class ExactCache:
    """Thread-safe TTL cache. Key always includes tenant (see cache_key)."""

    def __init__(self, ttl_s: int = 300) -> None:
        self.ttl_s = ttl_s
        self._store: dict[str, tuple[object, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, now: float | None = None) -> object | None:
        t = time.time() if now is None else now
        with self._lock:
            hit = self._store.get(key)
            if hit is None:
                return None
            value, expiry = hit
            if t > expiry:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: object, now: float | None = None) -> None:
        t = time.time() if now is None else now
        with self._lock:
            self._store[key] = (value, t + self.ttl_s)
