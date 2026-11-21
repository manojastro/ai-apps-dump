"""Persistent fixture store for the synthetic supplier portals.

The agent never reaches this database. It sees supplier facts only through the rendered
portal pages. The evaluator and operator use the private control API instead.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.engine import Engine

FIXTURES_DIR = Path(os.environ.get("FIXTURES_DIR", Path(__file__).resolve().parents[2] / "fixtures"))

metadata = MetaData()

products = Table(
    "products",
    metadata,
    Column("supplier", String(16), primary_key=True),
    Column("sku", String(64), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("canonical_id", String(64), nullable=False),
    Column("pack_size", Integer, nullable=False),
    Column("unit_price", Numeric(14, 2), nullable=False),
    Column("discount_pct", Numeric(6, 4), nullable=False),
    Column("discount_min_qty", Integer, nullable=False),
    Column("delivery_days", Integer, nullable=False),
    Column("delivery_certain", Boolean, nullable=False),
    Column("stock", Integer, nullable=False),
    Column("price_version", Integer, nullable=False, default=1),
    Column("visible", Boolean, nullable=False, default=True),
)

carts = Table(
    "carts",
    metadata,
    Column("supplier", String(16), primary_key=True),
    Column("account", String(64), primary_key=True),
    Column("sku", String(64), primary_key=True),
    Column("qty", Integer, nullable=False),
)

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("supplier", String(16), nullable=False),
    Column("account", String(64), nullable=False),
    Column("order_ref", String(32), nullable=False, unique=True),
    Column("po_reference", String(128), nullable=False),
    Column("quote_ref", String(64), nullable=False),
    Column("sku", String(64), nullable=False),
    Column("product_name", String(200), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("unit_price", Numeric(14, 2), nullable=False),
    Column("subtotal", Numeric(14, 2), nullable=False),
    Column("discount", Numeric(14, 2), nullable=False),
    Column("tax", Numeric(14, 2), nullable=False),
    Column("shipping", Numeric(14, 2), nullable=False),
    Column("total", Numeric(14, 2), nullable=False),
    Column("currency", String(3), nullable=False),
    Column("address_ref", String(32), nullable=False),
    Column("delivery_date", String(10), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("receipt_available_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("supplier", "account", "po_reference", name="uq_order_po_reference"),
)

sessions = Table(
    "sessions",
    metadata,
    Column("token", String(64), primary_key=True),
    Column("supplier", String(16), nullable=False),
    Column("account", String(64), nullable=True),
    Column("mfa_pending", Boolean, nullable=False, default=False),
    Column("page_views", Integer, nullable=False, default=0),
    Column("expired", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

scenario_state = Table(
    "scenario_state",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(64), nullable=False),
    Column("effects", JSON, nullable=False),
    Column("counters", JSON, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

request_log = Table(
    "request_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("supplier", String(16), nullable=False),
    Column("method", String(8), nullable=False),
    Column("path", String(400), nullable=False),
    Column("status", Integer, nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
)


def database_url() -> str:
    return os.environ.get(
        "SUPPLIERS_DATABASE_URL",
        "postgresql+psycopg://suppliers:devsuppliers@127.0.0.1:55433/suppliers",
    )


_engine: Engine | None = None


def engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(database_url(), pool_pre_ping=True, pool_size=10, max_overflow=10)
        metadata.create_all(_engine)
    return _engine


def load_catalog() -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / "catalog.json").read_text(encoding="utf-8"))


def load_scenarios() -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]


def now() -> datetime:
    return datetime.now(UTC)


def reset(scenario: str = "happy_path", *, keep_orders: bool = False) -> dict[str, Any]:
    """Rebuild deterministic inventory and apply a named scenario. Destructive to fixture data only."""
    scenarios = load_scenarios()
    if scenario not in scenarios:
        raise KeyError(scenario)
    effects = scenarios[scenario].get("effects", {})
    catalog = load_catalog()
    eng = engine()
    with eng.begin() as conn:
        conn.execute(delete(products))
        conn.execute(delete(carts))
        conn.execute(delete(sessions))
        conn.execute(delete(scenario_state))
        conn.execute(delete(request_log))
        if not keep_orders:
            conn.execute(delete(orders))
        for supplier, spec in catalog["suppliers"].items():
            sup_effects = effects.get(supplier, {})
            for p in spec["products"]:
                row = {
                    "supplier": supplier,
                    "sku": p["sku"],
                    "name": p["name"],
                    "canonical_id": p["canonical_id"],
                    "pack_size": p["pack_size"],
                    "unit_price": Decimal(p["unit_price"]),
                    "discount_pct": Decimal(p["discount_pct"]),
                    "discount_min_qty": p["discount_min_qty"],
                    "delivery_days": p["delivery_days"],
                    "delivery_certain": p["delivery_certain"],
                    "stock": p["stock"],
                    "price_version": 1,
                    "visible": p.get("hidden_unless_scenario") is None or bool(sup_effects.get("show_pack")),
                }
                for key, value in sup_effects.get("products", {}).get(p["sku"], {}).items():
                    row[key] = Decimal(value) if key in ("unit_price", "discount_pct") else value
                conn.execute(insert(products).values(**row))
        conn.execute(
            insert(scenario_state).values(id=1, name=scenario, effects=effects, counters={}, updated_at=now())
        )
    return {"scenario": scenario, "effects": effects}


def get_state(conn) -> dict[str, Any]:
    row = conn.execute(select(scenario_state).where(scenario_state.c.id == 1)).mappings().first()
    if row is None:
        return {"name": "uninitialised", "effects": {}, "counters": {}}
    return dict(row)


def bump_counter(conn, key: str) -> int:
    """Increment a scenario counter under a row lock and return the new value."""
    row = (
        conn.execute(select(scenario_state).where(scenario_state.c.id == 1).with_for_update())
        .mappings()
        .first()
    )
    if row is None:
        return 0
    counters = dict(row["counters"] or {})
    counters[key] = int(counters.get(key, 0)) + 1
    conn.execute(scenario_state.update().where(scenario_state.c.id == 1).values(counters=counters))
    return counters[key]


def apply_product_changes(conn, supplier: str, changes: dict[str, dict[str, Any]]) -> None:
    for sku, fields in changes.items():
        values: dict[str, Any] = {}
        for key, value in fields.items():
            values[key] = Decimal(value) if key in ("unit_price", "discount_pct") else value
        if {"unit_price", "discount_pct"} & values.keys():
            values["price_version"] = products.c.price_version + 1
        conn.execute(
            products.update().where(products.c.supplier == supplier, products.c.sku == sku).values(**values)
        )
