"""SQLite bootstrap: deterministic init. Schema v4 (M20 resolution_patterns)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 4


def get_db_path(db_path: str = "./data/autopilot.db") -> Path:
    return Path(db_path)


def get_connection(db_path: str | Path = "./data/autopilot.db") -> sqlite3.Connection:
    """Open SQLite with WAL + FK + Row factory. Creates parent dirs."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: str | Path = "./data/autopilot.db") -> Path:
    """Create DB + apply database/schema.sql + record version. Idempotent."""
    path = Path(db_path)
    schema_file = Path(__file__).with_name("schema.sql")
    sql = schema_file.read_text(encoding="utf-8")
    conn = get_connection(path)
    try:
        conn.executescript(sql)
        conn.execute(
            "INSERT OR IGNORE INTO schema_version(version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        conn.commit()
    finally:
        conn.close()
    return path
