"""Deterministic per-asset verdicts: breaking | degraded | safe, with a reason and evidence.

An asset is reached from the changed field by one or more data-flow paths. Each hop of a path is a
lineage edge carrying how the value is used (via: ingest|value|join|filter|group, transform:
passthrough|cast|function|aggregate|arithmetic|coalesce, plus the SQL file/line/expression).
The verdict is the worst verdict over all (change, path) pairs.
"""

from __future__ import annotations

from typing import Any

VERDICT_ORDER = {"safe": 0, "degraded": 1, "breaking": 2}
NUMERIC = {"int", "long", "float", "double"}
STRINGISH = {"string", "enum", "bytes"}
LOSSLESS = {("int", "long"), ("float", "double")}
INT_TYPES = ("INT", "BIGINT", "SMALLINT", "TINYINT", "HUGEINT")


def worst(a: str, b: str) -> str:
    return a if VERDICT_ORDER[a] >= VERDICT_ORDER[b] else b


def _loc(h: dict[str, Any]) -> str:
    expr = (h.get("expression") or "").replace("\n", " ")
    return f"{h.get('sql_file')}:{h.get('line')}" + (f" `{expr[:120]}`" if expr else "")


def _sql_hops(hops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [h for h in hops if h.get("edge") == "DERIVES_FROM" and h.get("via") != "ingest"]


def assess_path(
    change: dict[str, Any], hops: list[dict[str, Any]], asset: dict[str, Any]
) -> tuple[str, str, list[str]]:
    kind, field = change["kind"], change["field"]
    sql = _sql_hops(hops)
    atype = asset["type"]
    test_type = asset.get("test_type")
    if not sql:
        return "safe", "not read by any SQL transform", []
    first = sql[0]
    ev = [_loc(first)]

    if kind in ("removed", "renamed"):
        what = f"renamed to `{change['new_field']}`" if kind == "renamed" else "removed"
        table = first["to"].removeprefix("column:").rsplit(".", 1)[0]
        stale = "" if first["to"] == asset["id"] else "; this asset is downstream of the failed build"
        return (
            "breaking",
            f"{first['sql_file']}:{first['line']} reads `{field}`, which was {what}; building {table} fails{stale}",
            ev,
        )

    if kind == "type_changed":
        ob, nb = change["details"]["old_base"], change["details"]["new_base"]
        if (ob, nb) in LOSSLESS or (ob in STRINGISH and nb in STRINGISH):
            return "safe", f"{ob} -> {nb} keeps values and SQL semantics", ev
        if ob in NUMERIC and nb in NUMERIC:
            for h in sql:
                if h.get("cast_to") and h["cast_to"].upper().startswith(INT_TYPES):
                    return (
                        "degraded",
                        f"{ob} -> {nb}: CAST to {h['cast_to']} at {h['sql_file']}:{h['line']} truncates values",
                        [_loc(h)],
                    )
            return "safe", f"Avro promotion {ob} -> {nb}; downstream SQL accepts the wider numeric type", ev
        for h in sql:
            via, t = h.get("via"), h.get("transform")
            if via in ("join", "filter"):
                return (
                    "breaking",
                    f"`{field}` ({nb}) is compared in a {via} at {h['sql_file']}:{h['line']}; types no longer match",
                    [_loc(h)],
                )
            if via == "group":
                return "degraded", f"grouping on `{field}` now groups {nb} values", [_loc(h)]
            if t == "cast":
                return (
                    "degraded",
                    f"CAST at {h['sql_file']}:{h['line']} converts {nb} back, but fails at runtime on non-convertible values",
                    [_loc(h)],
                )
            if t in ("aggregate", "arithmetic"):
                return (
                    "breaking",
                    f"{'/'.join(h.get('ops') or [t])} at {h['sql_file']}:{h['line']} cannot take {nb} values",
                    [_loc(h)],
                )
            if t == "function":
                return (
                    "breaking",
                    f"function {'/'.join(h.get('ops') or [])} at {h['sql_file']}:{h['line']} expects {ob}, gets {nb}",
                    [_loc(h)],
                )
            if t == "coalesce":
                return (
                    "degraded",
                    f"COALESCE at {h['sql_file']}:{h['line']} mixes {nb} with a {ob} default",
                    [_loc(h)],
                )
        if test_type == "accepted_values":
            return "safe", "accepted-values comparison is done on text", ev
        return (
            "degraded",
            f"`{field}` is passed through unchanged, so this asset's type changes {ob} -> {nb}",
            ev,
        )

    if kind == "enum_symbols_added":
        syms = change["details"]["symbols"]
        gate = next((h for h in sql if h.get("via") in ("filter", "join")), None)
        value_only = all(
            h.get("via") == "value" and h.get("transform") in ("passthrough", "function") for h in sql
        )
        if atype == "DataTest" and test_type == "accepted_values" and value_only:
            return "breaking", f"accepted-values test does not list {syms}; it will fail", ev
        if gate is not None:
            return (
                "degraded",
                f"new values {syms} now pass the {gate['via']} at {gate['sql_file']}:{gate['line']}; results change meaning",
                [_loc(gate)],
            )
        if atype == "Visual" and value_only:
            return "degraded", f"new categories {syms} appear in this visual", ev
        return "safe", f"carries new values {syms}; no filter or test depends on them", ev

    if kind == "enum_symbols_removed":
        syms = change["details"]["symbols"]
        for h in sql:
            if h.get("via") in ("filter", "join") and any(
                f"'{s}'" in (h.get("expression") or "") for s in syms
            ):
                return (
                    "degraded",
                    f"filter at {h['sql_file']}:{h['line']} references removed value(s) {syms}",
                    [_loc(h)],
                )
        return "safe", f"no SQL references removed values {syms}", ev

    if kind == "nullability_changed":
        if not change["details"].get("now_nullable"):
            return "safe", "field became required (stricter)", ev
        for h in sql:
            if h.get("transform") == "coalesce":
                return "safe", f"NULLs are handled by COALESCE at {h['sql_file']}:{h['line']}", [_loc(h)]
            if h.get("via") == "join":
                return (
                    "degraded",
                    f"NULL join keys at {h['sql_file']}:{h['line']} silently drop matches",
                    [_loc(h)],
                )
            if h.get("via") == "filter":
                return (
                    "degraded",
                    f"NULLs are excluded by the filter at {h['sql_file']}:{h['line']}",
                    [_loc(h)],
                )
            if h.get("transform") == "aggregate":
                return (
                    "degraded",
                    f"aggregate at {h['sql_file']}:{h['line']} skips NULLs; totals are understated",
                    [_loc(h)],
                )
        if atype == "DataTest" and test_type in ("not_null", "unique"):
            return "breaking", f"{test_type} test will fail once NULLs arrive", ev
        return "degraded", f"NULLs from `{field}` can now reach this asset", ev

    return "safe", f"{kind}: no downstream effect", ev


def failing_table(change: dict[str, Any], hops: list[dict[str, Any]]) -> str | None:
    """Table whose build errors because of this change on this path (None if the SQL still runs)."""
    sql = _sql_hops(hops)
    if not sql:
        return None
    table = lambda h: h["to"].removeprefix("column:").rsplit(".", 1)[0]  # noqa: E731
    if change["kind"] in ("removed", "renamed"):
        return table(sql[0])
    if change["kind"] == "type_changed":
        ob, nb = change["details"]["old_base"], change["details"]["new_base"]
        if (ob, nb) in LOSSLESS or (ob in STRINGISH and nb in STRINGISH) or (ob in NUMERIC and nb in NUMERIC):
            return None
        for h in sql:
            if h.get("via") in ("join", "filter") or h.get("transform") in (
                "aggregate",
                "arithmetic",
                "function",
            ):
                return table(h)
            if h.get("transform") in ("cast", "coalesce") or h.get("via") == "group":
                return None
    return None


def assess_asset(
    asset: dict[str, Any],
    changes: list[dict[str, Any]],
    paths_by_change: dict[int, list[list[dict[str, Any]]]],
) -> dict[str, Any]:
    verdict, reason, evidence, cause = "safe", "no affecting path", [], None
    failing: set[str] = set()
    for idx, paths in paths_by_change.items():
        change = changes[idx]
        for hops in paths:
            v, r, ev = assess_path(change, hops, asset)
            if v == "breaking" and (ft := failing_table(change, hops)):
                failing.add(ft)
            if cause is None or VERDICT_ORDER[v] > VERDICT_ORDER[verdict]:
                verdict, reason, evidence, cause = v, r, ev, change
                evidence = ev + [" → ".join(h["to"] for h in hops[-4:])]
    if asset["type"] == "DataTest":
        evidence.append(f"test {asset.get('name')} ({asset.get('test_type')})")
    return {
        "asset": asset["id"],
        "type": asset["type"],
        "verdict": verdict,
        "reason": reason,
        "evidence": evidence,
        "change": f"{cause['kind']}:{cause['field']}" if cause else None,
        "owner": asset.get("owner"),
        "label": asset.get("label"),
        "failing_tables": sorted(failing),
    }
