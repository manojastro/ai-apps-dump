"""Local PostgreSQL without Docker (development and tests).

    uv run python -m spreadlens.devdb          # start embedded PostgreSQL 16, create DBs, write .env

Uses the `pgserver` dev dependency (bundled PostgreSQL binaries). Data lives in engine/data/pg-dev.
Docker Compose remains the documented alternative (postgres:16 on port 5433).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def start() -> str:
    import pgserver
    import psycopg

    data = ROOT / "data" / "pg-dev"
    data.mkdir(parents=True, exist_ok=True)
    srv = pgserver.get_server(str(data), cleanup_mode=None)
    uri = srv.get_uri()
    with psycopg.connect(uri, autocommit=True) as c:
        for db in ("spreadlens", "spreadlens_test"):
            if not c.execute("select 1 from pg_database where datname=%s", (db,)).fetchone():
                c.execute(f"create database {db}")
    base = uri.rsplit("/", 1)[0].replace("postgresql://", "postgresql+psycopg://")
    return base


def write_env(base: str) -> None:
    env = ROOT / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    lines = [x for x in lines if not re.match(r"^SPREADLENS_(DATABASE_URL|TEST_DATABASE_URL)=", x)]
    lines += [f"SPREADLENS_DATABASE_URL={base}/spreadlens", f"SPREADLENS_TEST_DATABASE_URL={base}/spreadlens_test"]
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    b = start()
    write_env(b)
    print(f"{b}/spreadlens")
    if "--print-test" in sys.argv:
        print(f"{b}/spreadlens_test")
    os.environ.setdefault("SPREADLENS_DATABASE_URL", f"{b}/spreadlens")
