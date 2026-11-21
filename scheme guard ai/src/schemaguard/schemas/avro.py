"""Normalised view of an Avro record schema, used by the diff, classifier, generator and extractors."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fastavro

PRIMITIVES = {"null", "boolean", "int", "long", "float", "double", "bytes", "string"}

DUCKDB_TYPES = {
    "string": "VARCHAR",
    "enum": "VARCHAR",
    "int": "INTEGER",
    "long": "BIGINT",
    "float": "FLOAT",
    "double": "DOUBLE",
    "boolean": "BOOLEAN",
    "bytes": "BLOB",
    "fixed": "BLOB",
}


class _NoDefault:
    def __repr__(self) -> str:
        return "NO_DEFAULT"


NO_DEFAULT: Any = _NoDefault()


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str  # base Avro type (string, int, long, double, enum, record, array, map, fixed, ...)
    nullable: bool = False
    logical_type: str | None = None
    symbols: tuple[str, ...] = ()
    doc: str | None = None
    default: Any = NO_DEFAULT
    aliases: tuple[str, ...] = ()
    position: int = 0

    @property
    def has_default(self) -> bool:
        return self.default is not NO_DEFAULT

    @property
    def type_label(self) -> str:
        base = self.type if not self.logical_type else f"{self.type}({self.logical_type})"
        return f"{base}?" if self.nullable else base

    @property
    def duckdb_type(self) -> str:
        return DUCKDB_TYPES.get(self.type, "VARCHAR")


@dataclass
class RecordSchema:
    name: str
    namespace: str | None
    fields: list[FieldSpec]
    doc: str | None = None
    owner: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name

    def field(self, name: str) -> FieldSpec | None:
        return next((f for f in self.fields if f.name == name), None)

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]

    def canonical_json(self) -> str:
        return json.dumps(self.raw, sort_keys=True, separators=(",", ":"))


def _resolve_type(t: Any) -> tuple[str, bool, str | None, tuple[str, ...]]:
    """Return (base_type, nullable, logical_type, enum_symbols)."""
    nullable = False
    if isinstance(t, list):
        non_null = [x for x in t if x != "null"]
        nullable = len(non_null) != len(t)
        if len(non_null) != 1:
            return ("union", nullable, None, ())
        t = non_null[0]
    if isinstance(t, str):
        return (t if t in PRIMITIVES else "named", nullable, None, ())
    if isinstance(t, dict):
        base = t.get("type")
        if base == "enum":
            return ("enum", nullable, None, tuple(t.get("symbols", [])))
        if isinstance(base, str):
            return (base, nullable, t.get("logicalType"), ())
    return ("unknown", nullable, None, ())


def parse_schema(raw: dict[str, Any] | str) -> RecordSchema:
    if isinstance(raw, str):
        raw = json.loads(raw)
    assert isinstance(raw, dict)
    if raw.get("type") != "record":
        raise ValueError("only Avro record schemas are supported")
    # Validates the schema (raises on invalid Avro). Custom attributes like x-owner are allowed.
    fastavro.parse_schema(json.loads(json.dumps(raw)), _write_hint=False)
    fields = []
    for i, f in enumerate(raw.get("fields", [])):
        base, nullable, logical, symbols = _resolve_type(f["type"])
        fields.append(
            FieldSpec(
                name=f["name"],
                type=base,
                nullable=nullable,
                logical_type=logical,
                symbols=symbols,
                doc=f.get("doc"),
                default=f.get("default", NO_DEFAULT),
                aliases=tuple(f.get("aliases", [])),
                position=i,
            )
        )
    return RecordSchema(
        name=raw["name"],
        namespace=raw.get("namespace"),
        fields=fields,
        doc=raw.get("doc"),
        owner=raw.get("x-owner"),
        raw=raw,
    )


def load_schema_file(path: Path) -> RecordSchema:
    return parse_schema(json.loads(Path(path).read_text(encoding="utf-8")))


def topic_from_filename(path: Path) -> str:
    """orders.v1.avsc -> orders.v1"""
    return Path(path).name.removesuffix(".avsc")


def load_pipeline_schemas(avro_dir: Path) -> dict[str, RecordSchema]:
    return {topic_from_filename(p): load_schema_file(p) for p in sorted(Path(avro_dir).glob("*.avsc"))}
