"""Statistical drift detectors: PSI, KS, total variation, missingness, prediction rate."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

_EPS = 1e-6


@dataclass
class FeatureDrift:
    """Drift measurement for a single feature."""

    feature: str
    feature_type: str
    psi: float | None = None
    ks_statistic: float | None = None
    p_value: float | None = None
    tv_delta: float | None = None
    missing_delta: float | None = None
    baseline_missing: float = 0.0
    current_missing: float = 0.0
    drifted: bool = False
    severity: str = "none"
    detail: dict = field(default_factory=dict)


def psi(expected_counts: np.ndarray, actual_counts: np.ndarray) -> float:
    """Population Stability Index between two count vectors."""
    expected = np.asarray(expected_counts, dtype=float)
    actual = np.asarray(actual_counts, dtype=float)
    expected = expected / expected.sum()
    actual = actual / actual.sum()
    expected = np.clip(expected, _EPS, None)
    actual = np.clip(actual, _EPS, None)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


def severity_from_score(score: float) -> str:
    """Map a normalised drift score to a severity bucket."""
    if score < 0.10:
        return "none"
    if score < 0.20:
        return "low"
    if score < 0.25:
        return "medium"
    return "high"


def compute_numeric_drift(
    feature: str,
    reference: pd.Series,
    current: pd.Series,
    bin_edges: list[float],
) -> FeatureDrift:
    """PSI plus KS test for one numeric feature."""
    ref = reference.dropna().to_numpy(dtype=float)
    cur = current.dropna().to_numpy(dtype=float)
    edges = np.array(bin_edges, dtype=float)
    lower = np.concatenate(([-np.inf], edges[1:-1]))
    upper = np.concatenate((edges[1:-1], [np.inf]))

    ref_counts = np.histogram(ref, bins=edges)[0].astype(float)
    ref_open_low = float(np.sum(ref < edges[0]))
    ref_open_high = float(np.sum(ref > edges[-1]))
    ref_counts[0] += ref_open_low
    ref_counts[-1] += ref_open_high

    cur_counts = (
        np.histogram(np.clip(cur, edges[0], edges[-1]), bins=edges)[0].astype(float)
    )
    cur_counts[0] += float(np.sum(cur < edges[0]))
    cur_counts[-1] += float(np.sum(cur > edges[-1]))

    psi_value = psi(ref_counts, cur_counts)
    ks = ks_2samp(ref, cur)
    baseline_missing = float(reference.isna().mean())
    current_missing = float(current.isna().mean())
    missing_delta = abs(current_missing - baseline_missing)

    score = max(psi_value, missing_delta * 2.5)
    return FeatureDrift(
        feature=feature,
        feature_type="numeric",
        psi=round(psi_value, 6),
        ks_statistic=round(float(ks.statistic), 6),
        p_value=round(float(ks.pvalue), 8),
        baseline_missing=baseline_missing,
        current_missing=current_missing,
        missing_delta=round(missing_delta, 6),
        severity=severity_from_score(psi_value),
        detail={
            "ref_mean": float(np.mean(ref)) if len(ref) else None,
            "cur_mean": float(np.mean(cur)) if len(cur) else None,
            "n_bins": len(edges) - 1,
        },
    )


def compute_categorical_drift(
    feature: str,
    reference: pd.Series,
    current: pd.Series,
) -> FeatureDrift:
    """Total variation distance and new-category share for one categorical feature."""
    categories = sorted(
        set(reference.dropna().unique().tolist()) | set(current.dropna().unique().tolist()),
        key=str,
    )
    ref_counts = reference.value_counts(normalize=True, dropna=True)
    cur_counts = current.value_counts(normalize=True, dropna=True)
    tv = 0.5 * sum(
        abs(float(ref_counts.get(c, 0.0)) - float(cur_counts.get(c, 0.0)))
        for c in categories
    )
    known = set(reference.dropna().unique().tolist())
    unseen_mass = float(sum(v for k, v in cur_counts.items() if k not in known))
    baseline_missing = float(reference.isna().mean())
    current_missing = float(current.isna().mean())
    missing_delta = abs(current_missing - baseline_missing)
    score = max(tv, missing_delta * 2.5)
    return FeatureDrift(
        feature=feature,
        feature_type="categorical",
        tv_delta=round(tv, 6),
        baseline_missing=baseline_missing,
        current_missing=current_missing,
        missing_delta=round(missing_delta, 6),
        severity=severity_from_score(tv),
        detail={"unseen_category_mass": round(unseen_mass, 6)},
    )


def prediction_rate_drift(
    baseline_rate: float, current_rate: float, meaningful_delta: float
) -> dict:
    """Compare positive prediction rate against the training-time baseline."""
    delta = abs(float(current_rate) - float(baseline_rate))
    return {
        "baseline_positive_rate": float(baseline_rate),
        "positive_rate": float(current_rate),
        "absolute_delta": round(delta, 6),
        "drifted": bool(delta >= meaningful_delta),
        "meaningful_delta": float(meaningful_delta),
    }


def evaluate_window_drift(
    frame: pd.DataFrame,
    reference_frame: pd.DataFrame,
    stats: dict,
) -> list[FeatureDrift]:
    """Run all per-feature detectors available for a window."""
    from backend.app.ml.data_generator import CATEGORICAL_FEATURES, NUMERIC_FEATURES

    results: list[FeatureDrift] = []
    for col in NUMERIC_FEATURES:
        if col not in frame.columns or col not in reference_frame.columns:
            continue
        results.append(
            compute_numeric_drift(
                col,
                reference_frame[col],
                frame[col],
                stats["bin_edges"].get(col, [0.0, 1.0]),
            )
        )
    for col in CATEGORICAL_FEATURES + ["customer_segment"]:
        if col not in frame.columns or col not in reference_frame.columns:
            continue
        results.append(compute_categorical_drift(col, reference_frame[col], frame[col]))
    return results


def summarise_drift(results: list[FeatureDrift]) -> dict:
    """Aggregate drift measurements into gate-ready summary values."""
    numeric_psi = [r.psi for r in results if r.psi is not None]
    tv_values = [r.tv_delta for r in results if r.tv_delta is not None]
    missing_deltas = [r.missing_delta for r in results if r.missing_delta is not None]
    return {
        "drift_count": sum(1 for r in results if r.severity in ("medium", "high")),
        "max_psi": max(numeric_psi) if numeric_psi else 0.0,
        "max_tv_delta": max(tv_values) if tv_values else 0.0,
        "max_missing_delta": max(missing_deltas) if missing_deltas else 0.0,
        "high_severity_features": [r.feature for r in results if r.severity == "high"],
        "top_features": sorted(
            [
                (r.feature, r.psi or r.tv_delta or 0.0)
                for r in results
                if r.severity in ("medium", "high")
            ],
            key=lambda t: t[1],
            reverse=True,
        ),
    }
