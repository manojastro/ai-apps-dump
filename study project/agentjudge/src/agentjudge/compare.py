"""Run comparison + regression detection (pure code)."""

from pydantic import BaseModel


class Regression(BaseModel):
    metric: str
    baseline: float
    current: float
    delta: float
    tolerance: float


KEY_METRICS = ("hit_rate_at_5", "faithfulness", "refusal_accuracy")


def _summary_metrics(report: dict[str, object]) -> dict[str, float]:
    summary = report.get("summary", {})
    assert isinstance(summary, dict)
    return {k: float(summary.get(k, 0.0)) for k in KEY_METRICS}


def compare_runs(
    current: dict[str, object], baseline: dict[str, object]
) -> dict[str, dict[str, float]]:
    """Delta per key metric: {"metric": {"baseline", "current", "delta"}}."""
    cur, base = _summary_metrics(current), _summary_metrics(baseline)
    return {
        k: {"baseline": base[k], "current": cur[k], "delta": cur[k] - base[k]} for k in KEY_METRICS
    }


def detect_regressions(
    current: dict[str, object],
    baseline: dict[str, object],
    tolerance: float = 0.02,
) -> list[Regression]:
    """Flag metrics that dropped more than tolerance vs baseline."""
    out: list[Regression] = []
    for metric, vals in compare_runs(current, baseline).items():
        if vals["delta"] < -tolerance:
            out.append(
                Regression(
                    metric=metric,
                    baseline=vals["baseline"],
                    current=vals["current"],
                    delta=vals["delta"],
                    tolerance=tolerance,
                )
            )
    return out
