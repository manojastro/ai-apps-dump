"""Deterministic Avro record diff.

Change kinds: added, removed, renamed (candidate, with evidence), type_changed, enum_symbols_added,
enum_symbols_removed, nullability_changed, default_changed, doc_changed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from dataclasses import field as dc_field
from difflib import SequenceMatcher
from typing import Any, Literal

from schemaguard.schemas.avro import FieldSpec, RecordSchema

ChangeKind = Literal[
    "added",
    "removed",
    "renamed",
    "type_changed",
    "enum_symbols_added",
    "enum_symbols_removed",
    "nullability_changed",
    "default_changed",
    "doc_changed",
]

RENAME_THRESHOLD = 0.6


@dataclass
class FieldChange:
    kind: ChangeKind
    field: str  # field name in the old schema (new name for `added`)
    new_field: str | None = None  # new name, for `renamed`
    old_type: str | None = None
    new_type: str | None = None
    details: dict[str, Any] = dc_field(default_factory=dict)
    evidence: list[str] = dc_field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FieldChange:
        return cls(**d)


@dataclass
class SchemaDiff:
    topic: str
    changes: list[FieldChange]
    old_fields: list[str]
    new_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "changes": [c.to_dict() for c in self.changes],
            "old_fields": self.old_fields,
            "new_fields": self.new_fields,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SchemaDiff:
        return cls(
            topic=d["topic"],
            changes=[FieldChange.from_dict(c) for c in d["changes"]],
            old_fields=list(d["old_fields"]),
            new_fields=list(d["new_fields"]),
        )

    @property
    def renames(self) -> dict[str, str]:
        return {c.field: c.new_field for c in self.changes if c.kind == "renamed" and c.new_field}

    def changes_for(self, old_field: str) -> list[FieldChange]:
        return [c for c in self.changes if c.field == old_field]


def _type_key(f: FieldSpec) -> tuple[str, str | None]:
    return (f.type, f.logical_type)


def rename_score(old: FieldSpec, new: FieldSpec) -> tuple[float, list[str]]:
    """Score how likely `new` is `old` renamed. Returns (confidence 0..1, evidence)."""
    evidence: list[str] = []
    if old.name in new.aliases:
        return 1.0, [f"new field '{new.name}' declares Avro alias '{old.name}'"]
    if _type_key(old) != _type_key(new) or old.nullable != new.nullable:
        return 0.0, []
    if old.type == "enum" and set(old.symbols) != set(new.symbols):
        return 0.0, []
    ratio = SequenceMatcher(None, old.name, new.name).ratio()
    contains = old.name in new.name or new.name in old.name
    score = 0.35 + 0.35 * ratio + (0.2 if contains else 0.0) + (0.1 if old.position == new.position else 0.0)
    evidence.append(f"same type {new.type_label}")
    evidence.append(f"name similarity {ratio:.2f}" + (" (one name contains the other)" if contains else ""))
    if old.position == new.position:
        evidence.append(f"same field position {new.position}")
    return min(round(score, 2), 0.95), evidence


def diff_schemas(old: RecordSchema, new: RecordSchema, topic: str) -> SchemaDiff:
    changes: list[FieldChange] = []
    old_by = {f.name: f for f in old.fields}
    new_by = {f.name: f for f in new.fields}
    removed = [f for f in old.fields if f.name not in new_by]
    added = [f for f in new.fields if f.name not in old_by]

    # Greedy best-first rename matching between removed and added fields.
    candidates = []
    for r in removed:
        for a in added:
            score, ev = rename_score(r, a)
            if score >= RENAME_THRESHOLD:
                candidates.append((score, r.name, a.name, ev))
    matched_old: set[str] = set()
    matched_new: set[str] = set()
    for score, r_name, a_name, ev in sorted(candidates, key=lambda c: -c[0]):
        if r_name in matched_old or a_name in matched_new:
            continue
        matched_old.add(r_name)
        matched_new.add(a_name)
        rf = old_by[r_name]
        changes.append(
            FieldChange(
                kind="renamed",
                field=r_name,
                new_field=a_name,
                old_type=rf.type_label,
                new_type=new_by[a_name].type_label,
                details={"confidence": score, "method": "alias" if score == 1.0 else "heuristic"},
                evidence=ev,
            )
        )

    for r in removed:
        if r.name not in matched_old:
            changes.append(
                FieldChange("removed", r.name, old_type=r.type_label, details={"had_default": r.has_default})
            )
    for a in added:
        if a.name not in matched_new:
            changes.append(
                FieldChange(
                    "added",
                    a.name,
                    new_type=a.type_label,
                    details={"has_default": a.has_default, "nullable": a.nullable, "doc": a.doc},
                )
            )

    for name, o in old_by.items():
        n = new_by.get(name)
        if n is None:
            continue
        if _type_key(o) != _type_key(n):
            changes.append(
                FieldChange(
                    "type_changed",
                    name,
                    old_type=o.type_label,
                    new_type=n.type_label,
                    details={"old_base": o.type, "new_base": n.type},
                )
            )
        elif o.type == "enum" and o.symbols != n.symbols:
            plus = [s for s in n.symbols if s not in o.symbols]
            minus = [s for s in o.symbols if s not in n.symbols]
            if plus:
                changes.append(
                    FieldChange(
                        "enum_symbols_added",
                        name,
                        old_type=o.type_label,
                        new_type=n.type_label,
                        details={"symbols": plus},
                    )
                )
            if minus:
                changes.append(
                    FieldChange(
                        "enum_symbols_removed",
                        name,
                        old_type=o.type_label,
                        new_type=n.type_label,
                        details={"symbols": minus},
                    )
                )
        if o.nullable != n.nullable:
            changes.append(
                FieldChange(
                    "nullability_changed",
                    name,
                    old_type=o.type_label,
                    new_type=n.type_label,
                    details={"now_nullable": n.nullable},
                )
            )
        if o.has_default != n.has_default or (o.has_default and o.default != n.default):
            changes.append(
                FieldChange(
                    "default_changed",
                    name,
                    details={
                        "old": None if not o.has_default else o.default,
                        "new": None if not n.has_default else n.default,
                    },
                )
            )
        if (o.doc or "") != (n.doc or ""):
            changes.append(FieldChange("doc_changed", name, details={"old": o.doc, "new": n.doc}))

    order = {f: i for i, f in enumerate(old.field_names + new.field_names)}
    changes.sort(key=lambda c: (order.get(c.field, 999), c.kind))
    return SchemaDiff(topic=topic, changes=changes, old_fields=old.field_names, new_fields=new.field_names)
