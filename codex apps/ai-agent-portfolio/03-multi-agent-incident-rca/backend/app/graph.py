from __future__ import annotations

from typing import Any

from .fixtures import DEPENDENCIES, SERVICES


class DependencyGraph:
    """Neo4j-shaped adapter with a deterministic in-memory fallback for local tests."""

    def __init__(self) -> None:
        self.nodes = [dict(node) for node in SERVICES]
        self.edges = [dict(edge) for edge in DEPENDENCIES]

    def snapshot(self, service: str | None = None) -> dict[str, list[dict[str, Any]]]:
        if not service:
            return {"nodes": self.nodes, "edges": self.edges}
        neighbor_ids = {service}
        for edge in self.edges:
            if edge["source"] == service or edge["target"] == service:
                neighbor_ids.update((edge["source"], edge["target"]))
        return {
            "nodes": [node for node in self.nodes if node["id"] in neighbor_ids],
            "edges": [
                edge
                for edge in self.edges
                if edge["source"] in neighbor_ids and edge["target"] in neighbor_ids
            ],
        }

    def dependencies_of(self, service: str) -> list[str]:
        return [edge["target"] for edge in self.edges if edge["source"] == service]

    def neo4j_statements(self) -> list[tuple[str, dict[str, Any]]]:
        statements: list[tuple[str, dict[str, Any]]] = []
        for node in self.nodes:
            statements.append(
                (
                    "MERGE (s:Component {id: $id}) SET s.kind=$kind, s.team=$team",
                    node,
                )
            )
        for edge in self.edges:
            statements.append(
                (
                    "MATCH (a:Component {id:$source}),(b:Component {id:$target}) "
                    "MERGE (a)-[:DEPENDS_ON {type:$type}]->(b)",
                    edge,
                )
            )
        return statements

    def sync_neo4j(self, uri: str, user: str, password: str) -> int:
        """Persist the deterministic topology in Neo4j using parameterized Cypher."""

        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            driver.verify_connectivity()
            with driver.session() as session:
                for statement, parameters in self.neo4j_statements():
                    session.run(statement, **parameters).consume()
        finally:
            driver.close()
        return len(self.nodes) + len(self.edges)
