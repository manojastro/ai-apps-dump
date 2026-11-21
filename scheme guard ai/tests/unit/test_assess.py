"""Pure verdict rules (no graph, no LLM)."""

from schemaguard.agent.assess import assess_asset, assess_path

ING = {
    "from": "field:t.x",
    "to": "column:raw.t.x",
    "edge": "DERIVES_FROM",
    "via": "ingest",
    "transform": "passthrough",
}


def hop(to, via="value", transform="passthrough", line=3, expression=None, ops=None, cast_to=None):
    return {"from": "column:raw.t.x", "to": to, "edge": "DERIVES_FROM", "via": via, "transform": transform,
            "sql_file": "sql/s.sql", "line": line, "expression": expression, "ops": ops or [], "cast_to": cast_to}  # fmt: skip


COL = {"id": "column:stg.s.x", "type": "Column"}


def ch(kind, **details):
    return {"kind": kind, "field": "x", "new_field": details.pop("new_field", None), "details": details}


def test_removed_and_renamed_are_breaking():
    v, r, ev = assess_path(ch("removed"), [ING, hop("column:stg.s.x")], COL)
    assert v == "breaking" and "sql/s.sql:3" in r
    v, r, _ = assess_path(ch("renamed", new_field="y"), [ING, hop("column:stg.s.x")], COL)
    assert v == "breaking" and "renamed to `y`" in r


def test_raw_only_path_is_safe():
    assert assess_path(ch("removed"), [ING], COL)[0] == "safe"


def test_type_change_rules():
    tc = ch("type_changed", old_base="int", new_base="string")
    assert assess_path(tc, [ING, hop("c", transform="aggregate", ops=["sum"])], COL)[0] == "breaking"
    assert assess_path(tc, [ING, hop("c", transform="cast", cast_to="INT")], COL)[0] == "degraded"
    assert assess_path(tc, [ING, hop("c", via="join", transform="join")], COL)[0] == "breaking"
    assert assess_path(tc, [ING, hop("c")], COL)[0] == "degraded"
    widen = ch("type_changed", old_base="int", new_base="long")
    assert assess_path(widen, [ING, hop("c", transform="aggregate")], COL)[0] == "safe"
    promo = ch("type_changed", old_base="double", new_base="float")
    assert assess_path(promo, [ING, hop("c")], COL)[0] == "safe"
    to_double = ch("type_changed", old_base="int", new_base="double")
    assert assess_path(to_double, [ING, hop("c", transform="cast", cast_to="INTEGER")], COL)[0] == "degraded"


def test_enum_rules():
    e = ch("enum_symbols_added", symbols=["NEW"])
    test_asset = {"id": "test:t", "type": "DataTest", "test_type": "accepted_values"}
    tested = {"from": "c", "to": "test:t", "edge": "TESTED_BY"}
    assert assess_path(e, [ING, hop("c"), tested], test_asset)[0] == "breaking"
    assert assess_path(e, [ING, hop("c"), hop("d", via="filter", transform="filter")], COL)[0] == "degraded"
    assert assess_path(e, [ING, hop("c")], COL)[0] == "safe"
    assert (
        assess_path(
            e, [ING, hop("c"), {"to": "visual:v", "edge": "USED_BY"}], {"id": "visual:v", "type": "Visual"}
        )[0]
        == "degraded"
    )
    removed = ch("enum_symbols_removed", symbols=["CANCELLED"])
    filt = hop("d", via="filter", transform="filter", expression="f.x <> 'CANCELLED'")
    assert assess_path(removed, [ING, filt], COL)[0] == "degraded"
    assert assess_path(removed, [ING, hop("c")], COL)[0] == "safe"


def test_nullability_rules():
    n = ch("nullability_changed", now_nullable=True)
    nn_test = {"id": "test:t", "type": "DataTest", "test_type": "not_null"}
    assert assess_path(n, [ING, hop("c"), {"to": "test:t", "edge": "TESTED_BY"}], nn_test)[0] == "breaking"
    assert assess_path(n, [ING, hop("c", transform="coalesce")], nn_test)[0] == "safe"
    assert assess_path(n, [ING, hop("c", transform="aggregate")], COL)[0] == "degraded"
    assert assess_path(n, [ING, hop("c", via="join", transform="join")], COL)[0] == "degraded"
    assert assess_path(ch("nullability_changed", now_nullable=False), [ING, hop("c")], COL)[0] == "safe"


def test_assess_asset_takes_worst_over_paths_and_changes():
    changes = [ch("enum_symbols_added", symbols=["N"]), ch("removed")]
    out = assess_asset(COL, changes, {0: [[ING, hop("c")]], 1: [[ING, hop("column:stg.s.x")]]})
    assert out["verdict"] == "breaking" and out["change"] == "removed:x"
    assert assess_asset(COL, changes, {})["verdict"] == "safe"
