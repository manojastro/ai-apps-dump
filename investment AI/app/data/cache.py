from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import get_settings
from app.constants import PARSER_VERSION


class MemoryCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, tuple[datetime, dict[str, Any]]] = {}

    @staticmethod
    def make_key(url: str, schema: dict | None = None) -> str:
        payload = json.dumps(
            {"url": url.strip().lower(), "schema": schema or {}, "parser": PARSER_VERSION},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            expires, value = item
            if datetime.now(timezone.utc) > expires:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else get_settings().cache_ttl_seconds
        with self._lock:
            self._store[key] = (datetime.now(timezone.utc) + timedelta(seconds=ttl), value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


CACHE = MemoryCache()
