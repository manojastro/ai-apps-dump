import json
from pathlib import Path

import pytest

from schemaguard.schemas.avro import load_pipeline_schemas, parse_schema
from schemaguard.schemas.classify import can_promote, classify
from schemaguard.schemas.diff import diff_schemas
from schemaguard.schemas.evolve import evolve_events
from schemaguard.schemas.mutate import apply_mutations

REPO = Path(__file__).resolve().parents[2]
ORDERS = json.loads((REPO / "demo_pipeline/avro/orders.v1.avsc").read_text())


def _diff(ops):
    old = parse_schema(ORDERS)
    new = parse_schema(apply_mutations(ORDERS, ops))
    d = diff_schemas(old, new, "orders.v1")
    return d, classify(d)


def kinds(d):
    return sorted(c.kind for c in d.changes)


def test_no_change():
    d, c = _diff([])
    assert d.changes == []
    assert c.change_class == "non_breaking" and c.compatibility["full"]


def test_rename_detected_heuristically():
    d, c = _diff([{"op": "rename_field", "field": "amount", "to": "total_amount"}])
    assert kinds(d) == ["renamed"]
    ch = d.changes[0]
    assert (ch.field, ch.new_field) == ("amount", "total_amount")
    assert ch.details["method"] == "heuristic" and ch.details["confidence"] >= 0.6
    assert any("same type" in e for e in ch.evidence)
    assert c.change_class == "breaking"


def test_rename_detected_by_alias_is_backward_compatible():
    d, c = _diff([{"op": "rename_field", "field": "amount", "to": "gross", "alias": True}])
    assert kinds(d) == ["renamed"] and d.changes[0].details["method"] == "alias"
    assert c.per_change[0].backward is True and c.per_change[0].forward is False


def test_unrelated_names_are_not_a_rename():
    d, c = _diff(
        [
            {"op": "drop_field", "field": "currency"},
            {"op": "add_field", "field": "zzz", "type": "string", "default": ""},
        ]
    )
    assert kinds(d) == ["added", "removed"]
    assert c.change_class == "breaking"


def test_rename_requires_same_type():
    d, _ = _diff(
        [
            {"op": "drop_field", "field": "amount"},
            {"op": "add_field", "field": "amount_cents", "type": "long"},
        ]
    )
    assert kinds(d) == ["added", "removed"]


def test_removed_field():
    d, c = _diff([{"op": "drop_field", "field": "coupon_code"}])
    assert kinds(d) == ["removed"]
    assert d.changes[0].details["had_default"] is True
    assert c.per_change[0].forward is True  # old readers fall back to the default
    assert c.change_class == "breaking"


@pytest.mark.parametrize(
    "field,new_type,severity,backward",
    [
        ("quantity", "string", "breaking", False),
        ("quantity", "long", "non_breaking", True),
        ("quantity", "double", "potentially_breaking", True),
        ("amount", "string", "breaking", False),
    ],
)
def test_type_changes(field, new_type, severity, backward):
    d, c = _diff([{"op": "change_type", "field": field, "type": new_type}])
    assert kinds(d) == ["type_changed"]
    assert c.change_class == severity
    assert c.per_change[0].backward is backward


def test_enum_symbol_added_and_removed():
    d, c = _diff([{"op": "add_enum_symbol", "field": "status", "symbol": "REFUNDED"}])
    assert kinds(d) == ["enum_symbols_added"] and d.changes[0].details["symbols"] == ["REFUNDED"]
    assert c.change_class == "potentially_breaking" and c.compatibility["forward"] is False
    d, c = _diff([{"op": "remove_enum_symbol", "field": "status", "symbol": "PLACED"}])
    assert kinds(d) == ["enum_symbols_removed"] and c.compatibility["backward"] is False


def test_nullability_changes():
    d, c = _diff([{"op": "make_nullable", "field": "customer_id"}])
    assert "nullability_changed" in kinds(d)
    assert c.change_class == "potentially_breaking"
    d, c = _diff([{"op": "make_required", "field": "coupon_code"}])
    assert "nullability_changed" in kinds(d)
    assert c.change_class == "non_breaking"


def test_added_fields():
    d, c = _diff([{"op": "add_field", "field": "channel", "type": ["null", "string"], "default": None}])
    assert kinds(d) == ["added"] and c.change_class == "non_breaking" and c.compatibility["full"]
    d, c = _diff([{"op": "add_field", "field": "region", "type": "string"}])
    assert c.change_class == "non_breaking" and c.compatibility["backward"] is False


def test_doc_change_is_metadata():
    d, c = _diff([{"op": "set_doc", "field": "amount", "doc": "new words"}])
    assert kinds(d) == ["doc_changed"] and c.change_class == "non_breaking"


def test_promotion_table():
    assert can_promote("int", "long") and can_promote("int", "double") and not can_promote("long", "int")
    assert not can_promote("double", "string")


def test_evolve_events_carries_values_through_rename_and_type_change():
    schemas = load_pipeline_schemas(REPO / "demo_pipeline/avro")
    old = schemas["orders.v1"]
    new = parse_schema(
        apply_mutations(
            ORDERS,
            [
                {"op": "rename_field", "field": "amount", "to": "total_amount"},
                {"op": "change_type", "field": "quantity", "type": "string"},
                {"op": "add_enum_symbol", "field": "status", "symbol": "REFUNDED"},
            ],
        )
    )
    d = diff_schemas(old, new, "orders.v1")
    events = [
        {"order_id": f"o{i}", "customer_id": "c", "amount": 10.5, "currency": "USD", "quantity": 3,
         "status": "PAID", "coupon_code": None, "created_at": 1}
        for i in range(400)
    ]  # fmt: skip
    out = evolve_events(events, old, new, d)
    assert all("amount" not in e and e["total_amount"] == 10.5 for e in out)
    assert all(e["quantity"] == "3" for e in out)
    assert any(e["status"] == "REFUNDED" for e in out)
