"""SQLite storage. Postgres note: swap this module for psycopg/SQLAlchemy;
schema in docs/decisions/ADR-002-servicenow-api.md. All data is synthetic."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS cmdb_ci (
  sys_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  class TEXT NOT NULL,
  service TEXT NOT NULL,
  environment TEXT NOT NULL DEFAULT 'prod'
);
CREATE TABLE IF NOT EXISTS cmdb_rel_ci (
  parent TEXT NOT NULL,
  child TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'depends_on',
  PRIMARY KEY (parent, child)
);
CREATE TABLE IF NOT EXISTS incident (
  sys_id TEXT PRIMARY KEY,
  number TEXT UNIQUE NOT NULL,
  short_description TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'New',
  priority TEXT NOT NULL DEFAULT '3',
  service TEXT NOT NULL DEFAULT '',
  ci TEXT NOT NULL DEFAULT '',
  caller TEXT NOT NULL DEFAULT '',
  opened_at TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT '',
  work_notes TEXT NOT NULL DEFAULT '[]',
  resolution TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS change_request (
  sys_id TEXT PRIMARY KEY,
  number TEXT UNIQUE NOT NULL,
  short_description TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  ci TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'Closed',
  risk TEXT NOT NULL DEFAULT 'Moderate',
  opened_at TEXT NOT NULL DEFAULT '',
  closed_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS app_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  service TEXT NOT NULL,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
  token_hash TEXT PRIMARY KEY,
  tool TEXT NOT NULL,
  target TEXT NOT NULL,
  action TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used INTEGER NOT NULL DEFAULT 0,
  used_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  tool TEXT NOT NULL,
  args_hash TEXT NOT NULL,
  target TEXT NOT NULL DEFAULT '',
  result TEXT NOT NULL DEFAULT '',
  success INTEGER NOT NULL DEFAULT 1
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    if p.parent != Path("") and str(p.parent) not in ("", "."):
        os.makedirs(p.parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def table_count(db_path: str, table: str) -> int:
    conn = connect(db_path)
    try:
        cur = conn.execute(f"SELECT COUNT(*) AS c FROM {table}")
        row = cur.fetchone()
        return int(row["c"]) if row else 0
    finally:
        conn.close()
