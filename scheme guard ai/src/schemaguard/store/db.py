"""Minimal DB-API wrapper so the same SQL runs on SQLite (default) and Postgres (optional extra).

SQL is written with `?` placeholders; for Postgres they are rewritten to `%s`.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, url_or_path: str | Path):
        self._lock = threading.RLock()
        target = str(url_or_path)
        if target.startswith(("postgres://", "postgresql://")):
            import psycopg  # optional extra: schemaguard[postgres]

            self.kind = "postgres"
            self._conn: Any = psycopg.connect(target, autocommit=True)
        else:
            self.kind = "sqlite"
            if target != ":memory:":
                Path(target).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(target, check_same_thread=False, isolation_level=None)
            self._conn.execute("PRAGMA journal_mode=WAL")
        self.target = target

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.kind == "postgres" else sql

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        with self._lock:
            self._conn.execute(self._sql(sql), tuple(params))

    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        with self._lock:
            if self.kind == "postgres":
                with self._conn.cursor() as cur:
                    cur.executemany(self._sql(sql), [tuple(r) for r in rows])
            else:
                self._conn.executemany(sql, [tuple(r) for r in rows])

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[tuple[Any, ...]]:
        with self._lock:
            cur = self._conn.execute(self._sql(sql), tuple(params))
            return list(cur.fetchall())

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            if self.kind == "postgres":
                with self._conn.transaction():
                    yield
            else:
                self._conn.execute("BEGIN")
                try:
                    yield
                except Exception:
                    self._conn.execute("ROLLBACK")
                    raise
                self._conn.execute("COMMIT")

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def open_database(database_url: str, sqlite_path: Path) -> Database:
    return Database(database_url or sqlite_path)
