"""blast_radius(ci, depth): everything that (transitively) depends on a CI.

Meaning: if A depends_on B and B depends_on C, then blast_radius(C, 2)
includes B and A. Edges stored in cmdb_rel_ci as (parent=dependent,
child=dependency, rel_type='depends_on'). BFS in Python (small graph);
Postgres version would be a recursive CTE — see ADR-002.
"""

from __future__ import annotations

import sqlite3


def blast_radius(conn: sqlite3.Connection, ci: str, depth: int = 2) -> dict[str, object]:
    """BFS over reverse depends_on edges up to `depth` hops.

    Returns {"ci": start, "depth": depth, "affected": [...], "edges": [...]}.
    Raises ValueError if start CI unknown or depth < 1.
    """
    if depth < 1:
        raise ValueError("depth must be >= 1")
    cur = conn.execute("SELECT name FROM cmdb_ci WHERE name = ?", (ci,))
    if cur.fetchone() is None:
        raise ValueError(f"unknown ci {ci!r}")
    # Build dependents index: dependency -> [dependents]
    dependents: dict[str, list[str]] = {}
    edges: list[dict[str, str]] = []
    for row in conn.execute("SELECT parent, child FROM cmdb_rel_ci"):
        parent = str(row["parent"])
        child = str(row["child"])
        dependents.setdefault(child, []).append(parent)
        edges.append({"from": parent, "to": child})
    seen: set[str] = {ci}
    affected: list[str] = []
    frontier: list[str] = [ci]
    for _ in range(depth):
        nxt: list[str] = []
        for node in frontier:
            for dep in dependents.get(node, []):
                if dep not in seen:
                    seen.add(dep)
                    affected.append(dep)
                    nxt.append(dep)
        frontier = nxt
        if not frontier:
            break
    affected_sorted = sorted(affected)
    used_edges = [e for e in edges if e["from"] in seen and e["to"] in seen]
    return {"ci": ci, "depth": depth, "affected": affected_sorted, "edges": used_edges}
