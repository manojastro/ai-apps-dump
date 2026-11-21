from evalharness.dataset import generate_demo_cases
from evalharness.metrics import score_case
from evalharness.targets import DemoAgentTarget


def test_grounded_answer_receives_full_core_scores():
    case = generate_demo_cases()[0]
    metrics, violations = score_case(case, DemoAgentTarget("good").invoke(case))
    assert metrics["context_precision"] == 1
    assert metrics["context_recall"] == 1
    assert metrics["groundedness"] == 1
    assert metrics["citation_correctness"] == 1
    assert metrics["tool_selection_accuracy"] == 1
    assert not violations


def test_forbidden_tool_is_a_hard_failure():
    case = generate_demo_cases()[0]
    metrics, violations = score_case(case, DemoAgentTarget("bad").invoke(case))
    assert metrics["tool_selection_accuracy"] == 0
    assert violations == ["forbidden tool called: shell"]


def test_unanswerable_case_rewards_safe_abstention():
    case = generate_demo_cases()[-1]
    metrics, _ = score_case(case, DemoAgentTarget("good").invoke(case))
    assert metrics["unanswerable_handling"] == 1
    assert metrics["task_success"] == 1

