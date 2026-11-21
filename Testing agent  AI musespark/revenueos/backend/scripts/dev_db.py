"""Start a local PostgreSQL 16 + pgvector without Docker.

Why this exists: `docker compose up` is the standard path, but this gives a real
Postgres on laptops where Docker is unavailable. It writes backend/.env.devdb, which
Settings reads automatically. Run: uv run python -m scripts.dev_db
"""
from __future__ import annotations

from pathlib import Path

import pgserver
import psycopg

from app.core.config import BACKEND_DIR, REPO_DIR


def ensure_database(admin_uri: str, name: str) -> str:
    with psycopg.connect(admin_uri, autocommit=True) as conn:
        exists = conn.execute("select 1 from pg_database where datname=%s", (name,)).fetchone()
        if not exists:
            conn.execute(f'create database "{name}"')
    return admin_uri.rsplit("/", 1)[0] + f"/{name}"


def main() -> None:
    admin_uri = pgserver.get_server(Path(REPO_DIR / ".pgdata"), cleanup_mode=None).get_uri()
    urls = {
        "DATABASE_URL": ensure_database(admin_uri, "revenueos"),
        "TEST_DATABASE_URL": ensure_database(admin_uri, "revenueos_test"),
    }
    lines = [
        f"{key}={value.replace('postgresql://', 'postgresql+psycopg://', 1)}"
        for key, value in urls.items()
    ]
    (BACKEND_DIR / ".env.devdb").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Postgres ready. Wrote backend/.env.devdb")


if __name__ == "__main__":
    main()
