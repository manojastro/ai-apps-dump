"""Load connector data into Postgres. Safe to run repeatedly.

Why upsert on source ids: re-running after a failure, or on a schedule, must never
duplicate rows. Rows that break referential integrity go to `load_rejects` so they
stay visible to the data-quality report rather than vanishing.

Run: uv run python -m scripts.load_data
"""
from __future__ import annotations

import math
from collections.abc import Iterable

import bcrypt
import pandas as pd
from sqlalchemy import Engine, Table, func, select, text
from sqlalchemy.dialects.postgresql import insert

from app.connectors.base import LOAD_ORDER, Connector
from app.connectors.synthetic import SyntheticCsvConnector
from app.core.config import get_settings
from app.db import models
from app.db.models import Base
from app.db.session import get_engine

BATCH_SIZE = 5_000

# table -> [(child column, parent table)]; used to quarantine orphans before insert.
FOREIGN_KEYS = {
    "users": [("team_id", "teams")],
    "accounts": [("owner_id", "users")],
    "contacts": [("account_id", "accounts")],
    "deals": [("account_id", "accounts"), ("owner_id", "users")],
    "deal_stage_history": [("deal_id", "deals")],
    "activities": [("deal_id", "deals"), ("contact_id", "contacts")],
    "subscriptions": [("account_id", "accounts")],
    "invoices": [("account_id", "accounts")],
    "payments": [("invoice_id", "invoices"), ("account_id", "accounts")],
    "usage_daily": [("account_id", "accounts")],
    "tickets": [("account_id", "accounts")],
}


def _clean(value: object) -> object:
    """Turn pandas missing values into SQL NULL."""
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _coerce(frame: pd.DataFrame, table: Table) -> list[dict]:
    """Convert a frame to dict rows matching the column types of the target table."""
    frame = frame[[c.name for c in table.columns if c.name in frame.columns]].copy()
    for column in table.columns:
        if column.name not in frame.columns:
            continue
        python_type = column.type.python_type
        if python_type.__name__ == "date":
            frame[column.name] = pd.to_datetime(frame[column.name], errors="coerce").dt.date
        elif python_type is int:
            frame[column.name] = frame[column.name].astype("Int64").astype(object)
    rows = frame.to_dict("records")
    return [{k: _clean(None if v is pd.NA else v) for k, v in row.items()} for row in rows]


def _split_orphans(
    name: str, frame: pd.DataFrame, seen: dict[str, set]
) -> tuple[pd.DataFrame, list[dict]]:
    rejects: list[dict] = []
    keep = pd.Series(True, index=frame.index)
    for column, parent in FOREIGN_KEYS.get(name, []):
        present = frame[column].notna()
        orphan = present & ~frame[column].isin(seen[parent])
        for _, row in frame[orphan].iterrows():
            rejects.append(dict(table_name=name, source_id=str(row.get("id")),
                                reason=f"{column}={row[column]} has no parent in {parent}"))
        keep &= ~orphan
    return frame[keep], rejects


def _upsert(conn, table: Table, rows: Iterable[dict]) -> None:
    rows = list(rows)
    primary = [c.name for c in table.primary_key.columns]
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        stmt = insert(table).values(batch)
        updates = {c: stmt.excluded[c] for c in batch[0] if c not in primary}
        conn.execute(stmt.on_conflict_do_update(index_elements=primary, set_=updates)
                     if updates else stmt.on_conflict_do_nothing())


def _password_hash() -> str | None:
    password = get_settings().demo_user_password
    if not password or password == "replace-me":
        return None  # Accounts stay unusable until a real demo password is configured.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()


def load(connector: Connector, engine: Engine | None = None) -> dict[str, int]:
    """Upsert every table in one transaction and return final row counts."""
    engine = engine or get_engine()
    frames = connector.fetch_all()
    seen: dict[str, set] = {}
    with engine.begin() as conn:
        for name in LOAD_ORDER:
            frame = frames[name]
            if name == "users":
                frame = frame.assign(password_hash=_password_hash())
            frame, rejects = _split_orphans(name, frame, seen)
            if "id" in frame.columns:
                seen[name] = set(frame["id"].tolist())
            table = Base.metadata.tables[name]
            _upsert(conn, table, _coerce(frame, table))
            if rejects:
                stmt = insert(models.LoadReject.__table__).values(rejects)
                conn.execute(stmt.on_conflict_do_nothing(constraint="uq_load_reject"))
        counts = {
            name: conn.execute(select(func.count()).select_from(Base.metadata.tables[name]))
            .scalar_one()
            for name in LOAD_ORDER + ["load_rejects"]
        }
    return counts


def reset_data(engine: Engine | None = None) -> None:
    """Empty every table. Only used by tests and full demo rebuilds."""
    engine = engine or get_engine()
    names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


def main() -> None:
    settings = get_settings()
    counts = load(SyntheticCsvConnector(settings.data_dir))
    for name, count in counts.items():
        print(f"{name:22s} {count:>8,}")


if __name__ == "__main__":
    main()
