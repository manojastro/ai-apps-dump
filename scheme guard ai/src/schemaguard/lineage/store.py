"""LineageStore: persists versioned lineage graph builds.

* SqlLineageStore (default): nodes/edges tables in SQLite or Postgres, one version per distinct build.
* Neo4jLineageStore (optional extra, `schemaguard[neo4j]`): same interface. Written but not exercised
  in CI or on the build machine; graph queries always run on the in-memory NetworkX graph.
"""

from __future__ import annotations

import json
import time
from typing import Protocol

from schemaguard.lineage.model import LineageGraph
from schemaguard.store.db import Database


class LineageStore(Protocol):
    def save(self, graph: LineageGraph, source: str = "") -> int: ...
    def load(self, version: int | None = None) -> LineageGraph: ...
    def latest_version(self) -> int | None: ...


SCHEMA_SQL = [
    """create table if not exists lineage_builds (
        version integer primary key, content_hash text not null, source text, created_at double precision not null)""",
    """create table if not exists lineage_nodes (
        version integer not null, id text not null, type text not null, attrs text not null,
        primary key (version, id))""",
    """create table if not exists lineage_edges (
        version integer not null, src text not null, dst text not null, type text not null, attrs text not null)""",
    "create index if not exists ix_lineage_edges_v on lineage_edges(version, src)",
]


class SqlLineageStore:
    def __init__(self, db: Database):
        self.db = db
        for stmt in SCHEMA_SQL:
            db.execute(stmt)

    def latest_version(self) -> int | None:
        rows = self.db.query("select max(version) from lineage_builds")
        return rows[0][0] if rows and rows[0][0] is not None else None

    def save(self, graph: LineageGraph, source: str = "") -> int:
        h = graph.content_hash()
        latest = self.latest_version()
        if latest is not None:
            (prev_hash,) = self.db.query(
                "select content_hash from lineage_builds where version = ?", (latest,)
            )[0]
            if prev_hash == h:
                return int(latest)  # identical build: reuse version (reproducible runs)
        version = (latest or 0) + 1
        nodes, edges = graph.to_records()
        with self.db.transaction():
            self.db.execute(
                "insert into lineage_builds(version, content_hash, source, created_at) values (?, ?, ?, ?)",
                (version, h, source, time.time()),
            )
            self.db.executemany(
                "insert into lineage_nodes(version, id, type, attrs) values (?, ?, ?, ?)",
                [(version, n["id"], n["type"], json.dumps(n["attrs"], default=str)) for n in nodes],
            )
            self.db.executemany(
                "insert into lineage_edges(version, src, dst, type, attrs) values (?, ?, ?, ?, ?)",
                [
                    (version, e["src"], e["dst"], e["type"], json.dumps(e["attrs"], default=str))
                    for e in edges
                ],
            )
        return version

    def load(self, version: int | None = None) -> LineageGraph:
        v = version if version is not None else self.latest_version()
        if v is None:
            raise LookupError("no lineage build stored yet; run `schemaguard lineage build`")
        nodes = [
            {"id": i, "type": t, "attrs": json.loads(a)}
            for i, t, a in self.db.query("select id, type, attrs from lineage_nodes where version = ?", (v,))
        ]
        edges = [
            {"src": s, "dst": d, "type": t, "attrs": json.loads(a)}
            for s, d, t, a in self.db.query(
                "select src, dst, type, attrs from lineage_edges where version = ?", (v,)
            )
        ]
        if not nodes:
            raise LookupError(f"lineage version {v} not found")
        return LineageGraph.from_records(nodes, edges)


class Neo4jLineageStore:  # pragma: no cover - needs a Neo4j server (compose profile `neo4j`)
    def __init__(self, uri: str, user: str, password: str):
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def latest_version(self) -> int | None:
        with self.driver.session() as s:
            rec = s.run("MATCH (b:LineageBuild) RETURN max(b.version) AS v").single()
            return rec["v"] if rec else None

    def save(self, graph: LineageGraph, source: str = "") -> int:
        version = (self.latest_version() or 0) + 1
        nodes, edges = graph.to_records()
        with self.driver.session() as s:
            s.run(
                "CREATE (:LineageBuild {version: $v, hash: $h, source: $src})",
                v=version,
                h=graph.content_hash(),
                src=source,
            )
            s.run(
                "UNWIND $rows AS r CREATE (:LNode {version: $v, id: r.id, type: r.type, attrs: r.attrs})",
                v=version,
                rows=[{**n, "attrs": json.dumps(n["attrs"], default=str)} for n in nodes],
            )
            s.run(
                "UNWIND $rows AS r MATCH (a:LNode {version: $v, id: r.src}), (b:LNode {version: $v, id: r.dst}) "
                "CREATE (a)-[:LEDGE {type: r.type, attrs: r.attrs}]->(b)",
                v=version,
                rows=[{**e, "attrs": json.dumps(e["attrs"], default=str)} for e in edges],
            )
        return version

    def load(self, version: int | None = None) -> LineageGraph:
        v = version if version is not None else self.latest_version()
        with self.driver.session() as s:
            nodes = [
                {"id": r["id"], "type": r["type"], "attrs": json.loads(r["attrs"])}
                for r in s.run(
                    "MATCH (n:LNode {version: $v}) RETURN n.id AS id, n.type AS type, n.attrs AS attrs", v=v
                )
            ]
            edges = [
                {"src": r["src"], "dst": r["dst"], "type": r["type"], "attrs": json.loads(r["attrs"])}
                for r in s.run(
                    "MATCH (a:LNode {version: $v})-[e:LEDGE]->(b:LNode) RETURN a.id AS src, b.id AS dst, e.type AS type, e.attrs AS attrs",
                    v=v,
                )
            ]
        return LineageGraph.from_records(nodes, edges)
