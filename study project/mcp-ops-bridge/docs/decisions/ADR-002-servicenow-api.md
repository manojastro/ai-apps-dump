# ADR-002 — ServiceNow-shaped API over SQLite (Postgres path noted)

Status: accepted. Date: 2026-09-18.

Context: need a ServiceNow Table-API shape (`sysparm_query`, `sysparm_limit/offset`)
for incidents/CMDB/changes/logs, offline and small.

Decision: FastAPI + SQLite (`sqlite3` stdlib, file `data/itsm.db`), `sysparm_query`
supports ONLY `field=value` ANDed with `^`, allowlisted columns, parameterized
queries. `blast_radius` is Python BFS over `cmdb_rel_ci` (parent depends_on child).

Postgres upgrade path: swap `mock_itsm/db.py` for a psycopg pool, keep the same
tables/routes; use `ILIKE` if case-insensitive search is needed; implement
`blast_radius` as a recursive CTE ("keep following depends_on links until depth N").

Consequences: zero external DB for the slice; SQL joins stay visible; moving to
Postgres later is a `db.py` swap, not a rewrite.
