from app.graph import DependencyGraph


def test_dependency_graph_neighborhood_and_neo4j_queries_are_parameterized():
    graph = DependencyGraph()
    snapshot = graph.snapshot("checkout-api")
    assert {node["id"] for node in snapshot["nodes"]} >= {"checkout-api", "payment-api", "orders-db"}
    statements = graph.neo4j_statements()
    assert statements
    assert all("$" in query for query, _params in statements)
    assert all(isinstance(params, dict) for _query, params in statements)

