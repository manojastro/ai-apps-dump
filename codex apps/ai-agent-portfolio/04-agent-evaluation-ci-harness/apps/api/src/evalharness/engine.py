from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .judge import Judge, MockJudge
from .metrics import aggregate, bootstrap_intervals, score_case
from .models import RunReport, SampleResult, TestCase
from .targets import TargetAdapter


class EvaluationEngine:
    def __init__(self, judge: Judge | None = None) -> None:
        self.judge = judge or MockJudge()

    def run(
        self,
        cases: list[TestCase],
        target: TargetAdapter,
        project_id: str = "demo-project",
        dataset_id: str = "demo-200",
    ) -> RunReport:
        if not cases:
            raise ValueError("an evaluation requires at least one test case")
        samples: list[SampleResult] = []
        for case in cases:
            try:
                response = target.invoke(case)
                metrics, violations = score_case(case, response)
                metrics.update(self.judge.score(case, response))
            except Exception as exc:  # target failures become inspectable sample failures
                from .models import TargetResponse
                response = TargetResponse(answer="", metadata={"error": str(exc)})
                metrics = {name: 0.0 for name in (
                    "context_precision", "context_recall", "groundedness", "answer_relevance",
                    "answer_correctness", "citation_correctness", "tool_selection_accuracy",
                    "task_success", "unanswerable_handling", "judge_correctness",
                )}
                violations = [f"target error: {exc}"]
            samples.append(SampleResult(case, response, metrics, violations))
        totals, categories = aggregate(samples)
        return RunReport(
            id=str(uuid4()), project_id=project_id, dataset_id=dataset_id,
            target=target.name, judge_config=self.judge.config(), aggregate=totals,
            category_metrics=categories, confidence_intervals=bootstrap_intervals(samples),
            samples=samples, created_at=datetime.now(UTC).isoformat(),
            metadata={"deterministic": isinstance(self.judge, MockJudge)},
        )


def compare_runs(candidate: RunReport, baseline: RunReport) -> dict:
    common = sorted(set(candidate.aggregate) & set(baseline.aggregate))
    deltas = {}
    regressions = {}
    lower_is_better = {"latency_p50_ms", "latency_p95_ms", "cost_per_request_usd", "unsafe_tool_calls"}
    for metric in common:
        current = candidate.aggregate[metric]
        previous = baseline.aggregate[metric]
        delta = current - previous
        relative = delta / abs(previous) if previous else (0.0 if delta == 0 else 1.0)
        deltas[metric] = {"baseline": previous, "candidate": current, "delta": delta, "relative": relative}
        degraded = relative > 0 if metric in lower_is_better else relative < 0
        if degraded:
            regressions[metric] = abs(relative)
    base_samples = {sample.case.id: sample for sample in baseline.samples}
    changed = []
    for sample in candidate.samples:
        old = base_samples.get(sample.case.id)
        if old and old.metrics.get("task_success") != sample.metrics.get("task_success"):
            changed.append({
                "case_id": sample.case.id,
                "baseline": old.metrics.get("task_success"),
                "candidate": sample.metrics.get("task_success"),
            })
    return {
        "baseline_id": baseline.id, "candidate_id": candidate.id,
        "deltas": deltas, "regressions": regressions, "changed_cases": changed,
    }

