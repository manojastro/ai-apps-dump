from app.graph.routing import after_evaluate, after_sandbox, after_verify
from app.graph.stagnation import detect_stagnation


def test_max_iterations_escalates():
    state = {
        "loop_iterations": 8,
        "hypotheses": [{"id": "HYP-001", "status": "REJECTED", "confidence": 0.2}],
        "active_hypothesis": {"status": "REJECTED", "confidence": 0.2},
        "experiments": [],
        "loop_history": [],
    }
    assert after_evaluate(state) == "request_human_approval"


def test_confirmed_goes_to_root_cause():
    state = {
        "loop_iterations": 2,
        "hypotheses": [{"id": "HYP-002", "status": "CONFIRMED", "confidence": 0.96}],
        "active_hypothesis": {"id": "HYP-002", "status": "CONFIRMED", "confidence": 0.96},
        "experiments": [{"id": "e1"}],
        "loop_history": [{"confidence": 0.5}, {"confidence": 0.96}],
        "tokens_used": 100,
        "estimated_cost": 0.01,
    }
    assert after_evaluate(state) == "determine_root_cause"


def test_stagnation_detected():
    s = detect_stagnation(
        {
            "hypotheses": [
                {"statement": "The source table is unavailable"},
                {"statement": "The source table is unavailable"},
            ],
            "experiments": [
                {"payload": {"sql": "SELECT 1"}},
                {"payload": {"sql": "SELECT 1"}},
            ],
            "loop_history": [{"confidence": 0.4}, {"confidence": 0.4}, {"confidence": 0.4}],
        }
    )
    assert s["stagnating"]


def test_duplicate_hypothesis_signal():
    s = detect_stagnation(
        {
            "hypotheses": [
                {"statement": "Renamed customer_id to customer_uuid"},
                {"statement": "Renamed customer_id to customer_uuid"},
            ]
        }
    )
    assert "same_hypothesis_repeated" in s["signals"]


def test_remediation_attempts_limited():
    state = {
        "remediation_attempts": 3,
        "sandbox_result": {"passed": False, "pipeline": {"status": "FAILED"}},
        "selected_remediation": {"type": "schema_mapping"},
    }
    assert after_sandbox(state) == "request_human_approval"


def test_recovery_loop_limited():
    state = {"final_status": "INVESTIGATING", "recovery_healthy": False, "recovery_cycles": 2}
    assert after_verify(state) == "generate_incident_report"
