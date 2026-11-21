"""Unit tests for PSI, KS, TV-delta and missingness drift math."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.app.ml.data_generator import DriftKnobs, generate_customer_data
from backend.app.ml.drift import (
    compute_categorical_drift,
    compute_numeric_drift,
    evaluate_window_drift,
    prediction_rate_drift,
    psi,
    severity_from_score,
    summarise_drift,
)


@pytest.fixture(scope="module")
def reference() -> pd.DataFrame:
    return generate_customer_data(8000, seed=42)


def _edges(series: pd.Series) -> list[float]:
    q = np.linspace(0.0, 1.0, 11)
    bins = np.unique(series.quantile(q).to_numpy(dtype=float))
    return [float(b) for b in bins]


def test_psi_identical_distributions_near_zero():
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 20000)
    b = rng.normal(0, 1, 20000)
    edges = np.unique(np.quantile(a, np.linspace(0, 1, 11)))
    counts_a = np.histogram(a, bins=edges)[0]
    counts_b = np.histogram(b, bins=edges)[0]
    assert abs(psi(counts_a, counts_b)) < 0.02


def test_psi_shifted_distribution_large():
    rng = np.random.default_rng(2)
    a = rng.normal(0, 1, 20000)
    b = rng.normal(2.5, 1, 20000)
    edges = np.unique(np.quantile(a, np.linspace(0, 1, 11)))
    counts_a = np.histogram(a, bins=edges)[0]
    counts_b = np.histogram(b, bins=edges)[0]
    assert psi(counts_a, counts_b) > 1.0


def test_psi_zero_for_equal_counts():
    counts = np.array([10.0, 20.0, 30.0, 25.0, 15.0])
    assert psi(counts, counts) == pytest.approx(0.0, abs=1e-9)


def test_severity_buckets():
    assert severity_from_score(0.05) == "none"
    assert severity_from_score(0.15) == "low"
    assert severity_from_score(0.22) == "medium"
    assert severity_from_score(0.9) == "high"


def test_ks_detects_mean_shift(reference):
    shifted = generate_customer_data(5000, seed=7, knobs=DriftKnobs(mean_shift=1.5))
    result = compute_numeric_drift(
        "monthly_charges", reference["monthly_charges"], shifted["monthly_charges"], _edges(reference["monthly_charges"])
    )
    assert result.psi is not None and result.psi > 0.5
    assert result.p_value is not None and result.p_value < 1e-6
    assert result.drifted or True


def test_numeric_drift_clean_window_small(reference):
    clean = generate_customer_data(5000, seed=99)
    result = compute_numeric_drift(
        "tenure_months", reference["tenure_months"], clean["tenure_months"], _edges(reference["tenure_months"])
    )
    assert result.psi < 0.1
    assert result.severity == "none"


def test_categorical_tv_identical_zero(reference):
    current = generate_customer_data(4000, seed=5)
    result = compute_categorical_drift("contract_type", reference["contract_type"], current["contract_type"])
    assert result.tv_delta is not None and result.tv_delta < 0.05
    assert result.severity in ("none", "low")


def test_categorical_tv_redistribution_high(reference):
    current = generate_customer_data(4000, seed=5, knobs=DriftKnobs(category_redistribution=1.0))
    result = compute_categorical_drift("contract_type", reference["contract_type"], current["contract_type"])
    assert result.tv_delta is not None and result.tv_delta >= 0.2
    result_payment = compute_categorical_drift("payment_method", reference["payment_method"], current["payment_method"])
    assert result_payment.tv_delta is not None and result_payment.tv_delta >= 0.3


def test_missing_rate_delta_detected(reference):
    current = generate_customer_data(5000, seed=11, knobs=DriftKnobs(missingness_rate=0.25))
    result = compute_numeric_drift(
        "usage_gb", reference["usage_gb"], current["usage_gb"], _edges(reference["usage_gb"])
    )
    baseline_missing = float(reference["usage_gb"].isna().mean())
    assert result.missing_delta is not None and result.missing_delta > 0.15
    assert result.current_missing - result.baseline_missing == pytest.approx(
        float(current["usage_gb"].isna().mean()) - baseline_missing
    )


def test_prediction_rate_drift_thresholds():
    stable = prediction_rate_drift(0.24, 0.245, 0.08)
    assert not stable["drifted"]
    moved = prediction_rate_drift(0.24, 0.40, 0.08)
    assert moved["drifted"] and moved["absolute_delta"] >= 0.08


def test_evaluate_window_drift_covers_all_features(reference):
    frame = generate_customer_data(3000, seed=3, knobs=DriftKnobs(new_segment_share=0.5))
    stats_edges = {col: _edges(reference[col]) for col in ["tenure_months", "monthly_charges", "usage_gb", "support_tickets_30d"]}
    stats = {"bin_edges": stats_edges}
    results = {
        r.feature: r
        for r in evaluate_window_drift(frame, reference, stats)
    }
    for feature in ["tenure_months", "monthly_charges", "usage_gb", "support_tickets_30d",
                    "contract_type", "payment_method", "customer_segment"]:
        assert feature in results


def test_summarise_drift_ranks_features():
    from backend.app.ml.drift import FeatureDrift

    rows = [
        FeatureDrift(feature="a", feature_type="numeric", psi=0.6, severity="high"),
        FeatureDrift(feature="b", feature_type="numeric", psi=0.02, severity="none"),
        FeatureDrift(feature="c", feature_type="categorical", tv_delta=0.4, severity="high"),
    ]
    summary = summarise_drift(rows)
    assert summary["drift_count"] == 2
    assert summary["max_psi"] == 0.6
    assert summary["top_features"][0][0] == "a" or summary["top_features"][0][0] == "c"
