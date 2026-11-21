"""Eval metric engine: (expected, predicted) pairs -> EvalReport.

All seven headline metrics from the spec, computed as pure functions so the
math is unit-tested offline with a scripted confusion matrix. The LLM-as-judge
bug-quality score enters as data (live: deepeval scorer; offline: injected
numbers) — the engine averages what it is given and reports coverage, never
fabricating scores.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from sentinel.models import VerdictLabel


class EvalResult(BaseModel):
    scenario_id: str
    expected: VerdictLabel
    predicted: VerdictLabel
    cost_usd: float = Field(default=0.0, ge=0.0)
    steps: int = Field(default=0, ge=0)
    bug_quality: int | None = Field(default=None, ge=1, le=5)


class EvalReport(BaseModel):
    n: int
    precision: float
    recall: float
    false_alarm_rate: float
    blocked_misclassification_rate: float
    mean_cost_usd: float
    mean_steps: float
    bug_quality_mean: float | None
    bug_quality_n: int = 0


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def compute_metrics(results: list[EvalResult]) -> EvalReport:
    bugs_expected = [r for r in results if r.expected == "real_bug"]
    bugs_predicted = [r for r in results if r.predicted == "real_bug"]
    tp = [r for r in bugs_predicted if r.expected == "real_bug"]
    flaky_expected = [r for r in results if r.expected == "flaky"]
    blocked_expected = [r for r in results if r.expected == "blocked"]
    qualities = [r.bug_quality for r in results if r.bug_quality is not None]

    return EvalReport(
        n=len(results),
        precision=_safe_div(len(tp), len(bugs_predicted)),
        recall=_safe_div(len(tp), len(bugs_expected)),
        false_alarm_rate=_safe_div(
            sum(1 for r in flaky_expected if r.predicted == "real_bug"), len(flaky_expected)),
        blocked_misclassification_rate=_safe_div(
            sum(1 for r in blocked_expected if r.predicted == "real_bug"), len(blocked_expected)),
        mean_cost_usd=_safe_div(sum(r.cost_usd for r in results), len(results)),
        mean_steps=_safe_div(sum(r.steps for r in results), len(results)),
        bug_quality_mean=(sum(qualities) / len(qualities)) if qualities else None,
        bug_quality_n=len(qualities),
    )


def render_markdown(report: EvalReport) -> str:
    """Rows for docs/results.md — written by the harness, never hand-edited."""
    q = f"{report.bug_quality_mean:.2f} (n={report.bug_quality_n})" if report.bug_quality_mean is not None else "n/a"
    return (
        f"| Precision | {report.precision:.3f} |\n"
        f"| Recall | {report.recall:.3f} |\n"
        f"| False-alarm rate | {report.false_alarm_rate:.3f} |\n"
        f"| Blocked-misclassification rate | {report.blocked_misclassification_rate:.3f} |\n"
        f"| Mean cost per test case | ${report.mean_cost_usd:.4f} |\n"
        f"| Mean steps | {report.mean_steps:.1f} |\n"
        f"| Bug report quality (1-5) | {q} |\n"
        f"| Scenarios | {report.n} |\n"
    )
