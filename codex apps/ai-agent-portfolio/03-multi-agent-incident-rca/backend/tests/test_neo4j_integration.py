from __future__ import annotations

import os

import pytest

from app.graph import DependencyGraph


@pytest.mark.integration
def test_topology_persists_to_live_neo4j_when_configured():
    uri = os.getenv("NEO4J_TEST_URI")
    if not uri:
        pytest.skip("set NEO4J_TEST_URI to run the live Neo4j integration test")
    neo4j = pytest.importorskip("neo4j")
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "rca03-local-password")
    graph = DependencyGraph()
    assert graph.sync_neo4j(uri, user, password) == len(graph.nodes) + len(graph.edges)
    driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
    try:
        count = driver.execute_query("MATCH (n:Component) RETURN count(n) AS count").records[0]["count"]
        assert count >= len(graph.nodes)
    finally:
        driver.close()
