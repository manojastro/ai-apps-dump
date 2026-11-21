"""Parse ServiceNow-style sysparm_query: only `field=value` joined by `^` (AND)."""

from __future__ import annotations


def parse_sysparm_query(q: str | None) -> dict[str, str]:
    """Parse `field=value^field2=value2` into a dict.

    Rules (kept small on purpose):
    - Empty / None -> {}.
    - Split on `^` for AND. Each part must contain exactly one `=` (split on first `=`).
    - Keys and values are stripped. Empty key or empty part raises ValueError.
    """
    if q is None or q.strip() == "":
        return {}
    out: dict[str, str] = {}
    parts = q.split("^")
    for raw in parts:
        part = raw.strip()
        if not part:
            raise ValueError(f"empty query part in {q!r}")
        if "=" not in part:
            raise ValueError(f"bad query part {part!r}: expected field=value")
        field, _, value = part.partition("=")
        field = field.strip()
        value = value.strip()
        if not field:
            raise ValueError(f"empty field in part {part!r}")
        out[field] = value
    return out


def build_where(parsed: dict[str, str], allowed: set[str], table_alias: str = "") -> tuple[str, list[str]]:
    """Build a safe WHERE clause from parsed query.

    Only allowlisted columns are used; anything else raises ValueError.
    Returns (clause_without_WHERE, params). Empty dict -> ("1=1", []).
    """
    if not parsed:
        return "1=1", []
    prefix = f"{table_alias}." if table_alias else ""
    clauses: list[str] = []
    params: list[str] = []
    for field in sorted(parsed.keys()):
        if field not in allowed:
            raise ValueError(f"field {field!r} not queryable")
        clauses.append(f"{prefix}{field} = ?")
        params.append(parsed[field])
    return " AND ".join(clauses), params
