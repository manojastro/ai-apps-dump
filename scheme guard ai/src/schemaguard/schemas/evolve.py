"""Convert events written with the old schema into what producers would emit under the new one.

The sandbox uses this to create realistic sample data for the *new* schema: values keep their
meaning (a renamed field carries the same amount; an int that becomes a string is str(int)), while
new enum symbols and newly-nullable fields show up in a fixed share of rows.
"""

from __future__ import annotations

import random
from typing import Any

from schemaguard.schemas.avro import RecordSchema
from schemaguard.schemas.diff import SchemaDiff

NEW_SYMBOL_SHARE = 0.05
NEW_NULL_SHARE = 0.10


def _convert(value: Any, old_base: str, new_base: str) -> Any:
    if value is None:
        return None
    if new_base in ("string", "enum"):
        return str(value)
    if new_base in ("int", "long"):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
    if new_base in ("float", "double"):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if new_base == "boolean":
        return bool(value)
    return value


def evolve_events(
    events: list[dict[str, Any]], old: RecordSchema, new: RecordSchema, diff: SchemaDiff, seed: int = 42
) -> list[dict[str, Any]]:
    rng = random.Random(f"evolve:{seed}:{diff.topic}")
    renames = diff.renames  # old -> new
    reverse = {v: k for k, v in renames.items()}
    added_symbols: dict[str, list[str]] = {}
    newly_nullable: set[str] = set()
    for c in diff.changes:
        if c.kind == "enum_symbols_added":
            added_symbols[c.field] = list(c.details["symbols"])
        if c.kind == "nullability_changed" and c.details.get("now_nullable"):
            newly_nullable.add(c.field)

    out = []
    for e in events:
        rec: dict[str, Any] = {}
        for nf in new.fields:
            src_name = reverse.get(nf.name, nf.name)
            of = old.field(src_name)
            if of is None:  # brand-new field
                rec[nf.name] = nf.default if nf.has_default else _placeholder(nf.type, rng)
                continue
            v = e.get(src_name)
            if of.type != nf.type:
                v = _convert(v, of.type, nf.type)
            if nf.type == "enum" and nf.name in added_symbols and rng.random() < NEW_SYMBOL_SHARE:
                v = rng.choice(added_symbols[nf.name])
            if nf.type == "enum" and v is not None and v not in nf.symbols:
                v = nf.symbols[0] if nf.symbols else v
            if nf.name in newly_nullable and rng.random() < NEW_NULL_SHARE:
                v = None
            rec[nf.name] = v
        out.append(rec)
    return out


def _placeholder(base: str, rng: random.Random) -> Any:
    return {
        "string": "n/a",
        "int": 0,
        "long": 0,
        "double": 0.0,
        "float": 0.0,
        "boolean": False,
    }.get(base)
