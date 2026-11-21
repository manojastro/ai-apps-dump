"""Build a new schema version from an old one with declarative operations.

Used by eval scenarios, tests and the demo to describe schema changes compactly, e.g.
    [{"op": "rename_field", "field": "amount", "to": "total_amount"}]
"""

from __future__ import annotations

import copy
from typing import Any


def _field(schema: dict[str, Any], name: str) -> dict[str, Any]:
    for f in schema["fields"]:
        if f["name"] == name:
            return f
    raise KeyError(f"field {name!r} not in schema")


def apply_mutations(schema: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    s = copy.deepcopy(schema)
    for op in ops:
        kind = op["op"]
        if kind == "rename_field":
            f = _field(s, op["field"])
            f["name"] = op["to"]
            if op.get("alias"):
                f["aliases"] = [*f.get("aliases", []), op["field"]]
        elif kind == "drop_field":
            s["fields"] = [f for f in s["fields"] if f["name"] != op["field"]]
        elif kind == "add_field":
            nf: dict[str, Any] = {"name": op["field"], "type": op["type"]}
            if "default" in op:
                nf["default"] = op["default"]
            if "doc" in op:
                nf["doc"] = op["doc"]
            s["fields"].append(nf)
        elif kind == "change_type":
            f = _field(s, op["field"])
            nullable = isinstance(f["type"], list) and "null" in f["type"]
            f["type"] = ["null", op["type"]] if nullable else op["type"]
        elif kind == "add_enum_symbol":
            f = _field(s, op["field"])
            t = f["type"][1] if isinstance(f["type"], list) else f["type"]
            t["symbols"] = [*t["symbols"], op["symbol"]]
        elif kind == "remove_enum_symbol":
            f = _field(s, op["field"])
            t = f["type"][1] if isinstance(f["type"], list) else f["type"]
            t["symbols"] = [x for x in t["symbols"] if x != op["symbol"]]
        elif kind == "make_nullable":
            f = _field(s, op["field"])
            if not (isinstance(f["type"], list) and "null" in f["type"]):
                f["type"] = ["null", f["type"]]
                f["default"] = None
        elif kind == "make_required":
            f = _field(s, op["field"])
            if isinstance(f["type"], list):
                f["type"] = next(t for t in f["type"] if t != "null")
                f.pop("default", None)
        elif kind == "set_doc":
            _field(s, op["field"])["doc"] = op["doc"]
        else:
            raise ValueError(f"unknown mutation op {kind!r}")
    return s
