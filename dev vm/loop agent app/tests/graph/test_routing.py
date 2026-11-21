from app.graph.routing import after_approval, after_evaluate, after_policy, evidence_router
from app.graph.main import build_main_graph, build_rca_subgraph
from langgraph.checkpoint.memory import InMemorySaver


def test_graph_compiles():
    g = build_main_graph(checkpointer=InMemorySaver())
    assert g is not None


def test_rca_subgraph_compiles():
    g = build_rca_subgraph()
    assert g is not None


def test_permission_skips_rca():
    cmd = evidence_router({"skip_rca": True, "error_message": "expired credential"})
    assert cmd.goto == "request_human_approval"


def test_schema_fans_out():
    cmd = evidence_router({"skip_rca": False, "incident_id": "x", "pipeline_id": "customer_daily_etl"})
    assert isinstance(cmd.goto, list)
    names = [s.node for s in cmd.goto]
    assert "inspect_schema" in names
    assert "inspect_data_quality" in names


def test_high_risk_policy_requires_human():
    assert after_policy({"policy_action": "REQUIRE_APPROVAL"}) == "request_human_approval"
    assert after_policy({"policy_action": "BLOCK"}) == "generate_incident_report"
    assert after_policy({"policy_action": "AUTO_APPROVE"}) == "apply_recovery"


def test_rejected_approval_does_not_recover():
    assert after_approval({"human_decision": "reject", "selected_remediation": {"type": "schema_mapping"}}) == "generate_incident_report"


def test_failed_hypothesis_reflects():
    state = {
        "loop_iterations": 1,
        "hypotheses": [{"id": "HYP-001", "status": "REJECTED", "confidence": 0.2}],
        "active_hypothesis": {"status": "REJECTED", "confidence": 0.2},
        "experiments": [{"id": "e"}],
        "loop_history": [{"confidence": 0.2}],
        "estimated_cost": 0.0,
        "tokens_used": 10,
    }
    assert after_evaluate(state) == "reflect"
