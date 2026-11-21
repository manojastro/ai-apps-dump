from evals.run import evaluate


async def test_all_golden_scenarios_and_incorrect_remediations():
    report = await evaluate()
    assert report["metrics"]["incident_count"] == 15
    assert report["metrics"]["false_remediation_acceptance_rate"] == 0
    assert report["metrics"]["expected_outcome_accuracy"] == 1
    assert report["metrics"]["root_cause_top_1_accuracy"] == 1
    assert report["metrics"]["human_escalation_accuracy"] == 1
    assert report["metrics"]["risk_classification_accuracy"] == 1
    assert report["metrics"]["tool_selection_correctness"] == 1
    for case in report["cases"]:
        assert case["operations_correct"]
        assert case["branches_correct"]
        assert case["mandatory_checks_executed"]
