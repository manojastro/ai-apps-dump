"""Deterministic synthetic event generator, driven by the Avro schemas.

Field values follow simple, readable rules keyed on field name and type, so the generator keeps
working when a schema evolves. All names, emails and ids are synthetic.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from schemaguard.schemas.avro import FieldSpec, RecordSchema

BASE_TS_MS = int(datetime(2026, 10, 1, tzinfo=UTC).timestamp() * 1000)
DAY_MS = 86_400_000
FIRST = ["Ada", "Ben", "Chen", "Dara", "Eli", "Fay", "Gus", "Hana", "Ivo", "Jun", "Kai", "Lea"]
LAST = ["Stone", "Rivera", "Okafor", "Novak", "Mori", "Lind", "Kerr", "Ibsen", "Haas", "Grey"]
COUNTRIES = ["US", "DE", "GB", "IN", "FR", "BR", "JP", "CA"]
CURRENCIES = ["USD", "EUR", "GBP"]
ENUM_WEIGHTS = {"PLACED": 0.15, "PAID": 0.35, "SHIPPED": 0.40, "CANCELLED": 0.10}

DEFAULT_COUNTS = {"customers.v1": 500, "orders.v1": 3000, "inventory.v1": 200}
PRIMARY_KEYS = {
    "customers.v1": "customer_id",
    "orders.v1": "order_id",
    "payments.v1": "payment_id",
    "inventory.v1": "sku",
}


def _value(f: FieldSpec, i: int, rng: random.Random, ctx: dict[str, Any], topic: str) -> Any:
    name = f.name
    if f.nullable and f.type == "string" and name == "coupon_code":
        return None if rng.random() < 0.8 else rng.choice(["SAVE10", "WELCOME", "VIP5"])
    if f.type == "enum":
        weights = [ENUM_WEIGHTS.get(s, 0.05) for s in f.symbols]
        return rng.choices(list(f.symbols), weights=weights)[0]
    if f.logical_type == "timestamp-millis":
        return BASE_TS_MS + rng.randrange(0, 30 * DAY_MS)
    if name == PRIMARY_KEYS.get(topic):
        return f"{name.split('_')[0][:3]}_{i:06d}"
    if name == "customer_id" and ctx.get("customer_ids"):
        return rng.choice(ctx["customer_ids"])
    if name == "full_name":
        return f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    if name == "email":
        return f"user{i:05d}@example.com"
    if name == "country":
        return rng.choice(COUNTRIES)
    if name == "currency":
        return rng.choices(CURRENCIES, weights=[0.7, 0.2, 0.1])[0]
    if f.type in ("double", "float"):
        return round(rng.uniform(5, 400), 2)
    if f.type in ("int", "long"):
        return rng.randint(1, 5) if name == "quantity" else rng.randint(-20, 50)
    if f.type == "boolean":
        return rng.random() < 0.5
    if f.type == "string":
        return f"{name}_{i}"
    return None


def generate_topic(
    schema: RecordSchema, topic: str, n: int, seed: int, ctx: dict[str, Any]
) -> list[dict[str, Any]]:
    rng = random.Random(f"{seed}:{topic}")
    return [{f.name: _value(f, i, rng, ctx, topic) for f in schema.fields} for i in range(n)]


def generate_all(
    schemas: dict[str, RecordSchema], seed: int = 42, scale: float = 1.0
) -> dict[str, list[dict[str, Any]]]:
    """Generate events for every topic. payments are derived from paid/shipped orders."""
    out: dict[str, list[dict[str, Any]]] = {}
    ctx: dict[str, Any] = {}
    if "customers.v1" in schemas:
        out["customers.v1"] = generate_topic(
            schemas["customers.v1"], "customers.v1", int(DEFAULT_COUNTS["customers.v1"] * scale), seed, ctx
        )
        ctx["customer_ids"] = [e["customer_id"] for e in out["customers.v1"]]
    if "orders.v1" in schemas:
        out["orders.v1"] = generate_topic(
            schemas["orders.v1"], "orders.v1", int(DEFAULT_COUNTS["orders.v1"] * scale), seed, ctx
        )
    if "payments.v1" in schemas and "orders.v1" in out:
        pay_schema = schemas["payments.v1"]
        rng = random.Random(f"{seed}:payments")
        paid = [o for o in out["orders.v1"] if o.get("status") in ("PAID", "SHIPPED")]
        events = []
        for i, o in enumerate(paid):
            e = {f.name: _value(f, i, rng, ctx, "payments.v1") for f in pay_schema.fields}
            if "order_id" in e:
                e["order_id"] = o["order_id"]
            if "amount" in e and "amount" in o:
                e["amount"] = o["amount"]
            events.append(e)
        out["payments.v1"] = events
    for topic, schema in schemas.items():
        if topic not in out:
            out[topic] = generate_topic(schema, topic, int(DEFAULT_COUNTS.get(topic, 200) * scale), seed, ctx)
    return out


def write_jsonl(events: dict[str, list[dict[str, Any]]], data_dir: Path) -> dict[str, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for topic, rows in events.items():
        p = data_dir / f"{topic}.jsonl"
        with p.open("w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        paths[topic] = p
    return paths
