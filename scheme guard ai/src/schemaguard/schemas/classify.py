"""Deterministic change classification.

Two views per change:
* Avro compatibility (would the registry accept it under BACKWARD / FORWARD / FULL?)
* Downstream severity for SQL consumers that read fields *by name*:
  breaking > potentially_breaking > non_breaking.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from schemaguard.schemas.diff import FieldChange, SchemaDiff

Severity = Literal["breaking", "potentially_breaking", "non_breaking"]
SEVERITY_ORDER: dict[str, int] = {"non_breaking": 0, "potentially_breaking": 1, "breaking": 2}

# Avro schema resolution: data written as key can be read as any of the values.
AVRO_PROMOTIONS: dict[str, set[str]] = {
    "int": {"long", "float", "double"},
    "long": {"float", "double"},
    "float": {"double"},
    "string": {"bytes"},
    "bytes": {"string"},
}
LOSSLESS_WIDENINGS = {("int", "long"), ("float", "double")}


def can_promote(writer: str, reader: str) -> bool:
    return writer == reader or reader in AVRO_PROMOTIONS.get(writer, set())


@dataclass
class ChangeClassification:
    change: dict[str, Any]
    severity: Severity
    backward: bool  # new schema can read old data
    forward: bool  # old schema can read new data
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClassificationResult:
    change_class: Severity
    compatibility: dict[str, bool]
    per_change: list[ChangeClassification] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_class": self.change_class,
            "compatibility": self.compatibility,
            "per_change": [c.to_dict() for c in self.per_change],
        }


def classify_change(c: FieldChange) -> ChangeClassification:
    d = c.to_dict()
    if c.kind == "added":
        has_default = bool(c.details.get("has_default"))
        return ChangeClassification(
            d,
            "non_breaking",
            backward=has_default,
            forward=True,
            reason="new field; existing consumers ignore it"
            + ("" if has_default else " (no default: new readers cannot read old data)"),
        )
    if c.kind == "removed":
        return ChangeClassification(
            d,
            "breaking",
            backward=True,
            forward=bool(c.details.get("had_default")),
            reason="field removed; any consumer that selects it by name will fail",
        )
    if c.kind == "renamed":
        alias = c.details.get("method") == "alias"
        return ChangeClassification(
            d,
            "breaking",
            backward=alias,
            forward=False,
            reason=f"field renamed {c.field} -> {c.new_field}; SQL that selects '{c.field}' will fail",
        )
    if c.kind == "type_changed":
        old_b, new_b = c.details["old_base"], c.details["new_base"]
        back, fwd = can_promote(old_b, new_b), can_promote(new_b, old_b)
        if (old_b, new_b) in LOSSLESS_WIDENINGS:
            sev: Severity = "non_breaking"
            reason = f"lossless widening {old_b} -> {new_b}"
        elif back:
            sev = "potentially_breaking"
            reason = f"Avro promotion {old_b} -> {new_b}; values change representation/precision"
        else:
            sev = "breaking"
            reason = f"incompatible type change {old_b} -> {new_b}"
        return ChangeClassification(d, sev, backward=back, forward=fwd, reason=reason)
    if c.kind == "enum_symbols_added":
        return ChangeClassification(
            d,
            "potentially_breaking",
            backward=True,
            forward=False,
            reason=f"new enum symbols {c.details['symbols']}; accepted-value checks and filters may break",
        )
    if c.kind == "enum_symbols_removed":
        return ChangeClassification(
            d,
            "potentially_breaking",
            backward=False,
            forward=True,
            reason=f"enum symbols removed {c.details['symbols']}; filters on them silently match nothing",
        )
    if c.kind == "nullability_changed":
        if c.details.get("now_nullable"):
            return ChangeClassification(
                d,
                "potentially_breaking",
                backward=True,
                forward=False,
                reason="field became nullable; NULLs can now reach not-null columns and aggregates",
            )
        return ChangeClassification(
            d, "non_breaking", backward=False, forward=True, reason="field became required (stricter)"
        )
    return ChangeClassification(
        d, "non_breaking", backward=True, forward=True, reason=f"{c.kind}: metadata only"
    )


def classify(diff: SchemaDiff) -> ClassificationResult:
    per = [classify_change(c) for c in diff.changes]
    if not per:
        return ClassificationResult("non_breaking", {"backward": True, "forward": True, "full": True}, [])
    worst = max(per, key=lambda p: SEVERITY_ORDER[p.severity]).severity
    back = all(p.backward for p in per)
    fwd = all(p.forward for p in per)
    return ClassificationResult(worst, {"backward": back, "forward": fwd, "full": back and fwd}, per)
