"""Data quality rules and simulated latency regression checks."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    SEGMENT_COLUMN,
)

RANGE_RULES: dict[str, tuple[float, float]] = {
    "tenure_months": (0.0, 200.0),
    "monthly_charges": (0.0, 1000.0),
    "usage_gb": (0.0, 500.0),
    "support_tickets_30d": (0.0, 100.0),
}
MAX_NULL_FRACTION = 0.30
LATENCY_REGRESSION_FACTOR = 1.6


@dataclass
class QualityCheck:
    """Outcome of a single data quality rule."""

    check_name: str
    passed: bool
    value: float | None = None
    details: dict = field(default_factory=dict)


def run_quality_checks(
    frame: pd.DataFrame,
    max_severity_score: float,
    baseline_latency_ms: float = 12.0,
) -> list[QualityCheck]:
    """Schema completeness, range validity, null fraction and latency regression."""
    checks: list[QualityCheck] = []

    expected = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [SEGMENT_COLUMN]
    missing_cols = [c for c in expected if c not in frame.columns]
    checks.append(
        QualityCheck(
            check_name="schema_complete",
            passed=len(missing_cols) == 0,
            details={"missing_columns": missing_cols},
        )
    )

    range_violations: dict[str, int] = {}
    for col, (low, high) in RANGE_RULES.items():
        if col not in frame.columns:
            continue
        series = pd.to_numeric(frame[col], errors="coerce").dropna()
        violations = int(((series < low) | (series > high)).sum())
        if violations:
            range_violations[col] = violations
    checks.append(
        QualityCheck(
            check_name="numeric_ranges",
            passed=len(range_violations) == 0,
            value=float(sum(range_violations.values())),
            details={"violations": range_violations},
        )
    )

    null_fractions = {c: float(frame[c].isna().mean()) for c in frame.columns}
    worst_col = max(null_fractions, key=null_fractions.get)
    worst_value = null_fractions[worst_col]
    checks.append(
        QualityCheck(
            check_name="null_fraction",
            passed=worst_value <= MAX_NULL_FRACTION,
            value=round(worst_value, 6),
            details={"worst_column": worst_col, "null_fractions": null_fractions},
        )
    )

    simulated_latency = baseline_latency_ms * (
        1.0 + 0.05 * (len(frame) / 4000.0) + 0.35 * max_severity_score
    )
    checks.append(
        QualityCheck(
            check_name="latency_regression",
            passed=simulated_latency <= baseline_latency_ms * LATENCY_REGRESSION_FACTOR,
            value=round(simulated_latency, 3),
            details={
                "baseline_ms": baseline_latency_ms,
                "simulated_ms": round(simulated_latency, 3),
                "max_severity_score": round(max_severity_score, 4),
            },
        )
    )

    segment_ok = SEGMENT_COLUMN in frame.columns and set(
        frame[SEGMENT_COLUMN].dropna().unique()
    ).issubset({"retail", "business"})
    checks.append(QualityCheck(check_name="segment_domain", passed=bool(segment_ok)))

    return checks
