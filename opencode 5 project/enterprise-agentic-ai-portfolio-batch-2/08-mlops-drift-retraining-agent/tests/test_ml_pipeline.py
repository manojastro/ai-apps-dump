"""Tests for the synthetic generator and champion/candidate pipelines."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    DriftKnobs,
    generate_customer_data,
)
from backend.app.ml.pipeline import (
    build_candidate_pipeline,
    build_champion_pipeline,
    compute_classification_metrics,
    compute_reference_stats,
    predict_pipeline,
    train_reference_champion,
)


def test_generator_shape_and_columns():
    frame = generate_customer_data(500, seed=1)
    assert len(frame) == 500
    for column in FEATURES + [TARGET]:
        assert column in frame.columns


def test_generator_deterministic_with_seed():
    a = generate_customer_data(300, seed=123)
    b = generate_customer_data(300, seed=123)
    pd.testing.assert_frame_equal(a, b)


def test_label_balance_reasonable():
    frame = generate_customer_data(6000, seed=42)
    rate = frame[TARGET].mean()
    assert 0.10 <= rate <= 0.45


def test_mean_shift_moves_means():
    base = generate_customer_data(4000, seed=9)
    shifted = generate_customer_data(4000, seed=9, knobs=DriftKnobs(mean_shift=1.2))
    assert base["monthly_charges"].mean() < shifted["monthly_charges"].mean()
    assert base["tenure_months"].mean() > shifted["tenure_months"].mean()


def test_variance_shift_increases_spread():
    base = generate_customer_data(4000, seed=9)
    wider = generate_customer_data(4000, seed=9, knobs=DriftKnobs(variance_shift=2.0))
    assert wider["usage_gb"].std() > base["usage_gb"].std()


def test_label_noise_flips_labels():
    clean = generate_customer_data(4000, seed=9)
    noisy = generate_customer_data(4000, seed=9, knobs=DriftKnobs(label_noise=0.5))
    flips = (clean[TARGET] != noisy[TARGET]).mean()
    assert 0.4 < flips < 0.6


def test_missingness_creates_nulls():
    frame = generate_customer_data(4000, seed=9, knobs=DriftKnobs(missingness_rate=0.3))
    assert 0.15 < frame["usage_gb"].isna().mean() < 0.45
    assert 0.05 < frame["payment_method"].isna().mean() < 0.45


def test_drop_features_removes_column():
    frame = generate_customer_data(200, seed=3, knobs=DriftKnobs(drop_features=["usage_gb"]))
    assert "usage_gb" not in frame.columns


def test_new_segment_share_changes_mix():
    base = generate_customer_data(4000, seed=8)
    shifted = generate_customer_data(4000, seed=8, knobs=DriftKnobs(new_segment_share=0.6))
    assert (
        shifted["customer_segment"].value_counts(normalize=True)["business"]
        > base["customer_segment"].value_counts(normalize=True)["business"] + 0.2
    )


def test_champion_pipeline_trains_and_predicts():
    artifact = train_reference_champion(n_samples=2500, seed=42)
    pipeline = artifact["pipeline"]
    assert isinstance(pipeline, Pipeline)
    holdout = generate_customer_data(800, seed=777)
    pred, prob = predict_pipeline(pipeline, holdout)
    assert len(pred) == 800
    assert ((prob >= 0) & (prob <= 1)).all()
    metrics = compute_classification_metrics(holdout[TARGET], pred, prob)
    assert metrics["roc_auc"] > 0.70
    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "brier", "roc_auc"}


def test_reference_stats_structure():
    frame = generate_customer_data(1500, seed=5)
    stats = compute_reference_stats(frame, np.zeros(len(frame)))
    assert set(stats["bin_edges"]) == set(NUMERIC_FEATURES)
    assert "contract_type" in stats["category_probs"]
    assert "positive_rate" in stats
    for col in NUMERIC_FEATURES:
        assert len(stats["bin_edges"][col]) >= 3


def test_candidate_pipeline_beats_random():
    from sklearn.dummy import DummyClassifier

    train = generate_customer_data(3000, seed=21)
    holdout = generate_customer_data(1200, seed=22)
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES

    gbt = build_candidate_pipeline()
    gbt.fit(train[features], train[TARGET])
    pred, prob = predict_pipeline(gbt, holdout)
    cand_auc = compute_classification_metrics(holdout[TARGET], pred, prob)["roc_auc"]

    dummy = DummyClassifier(strategy="stratified")
    dummy.fit(train[features], train[TARGET])
    d_pred = dummy.predict(holdout[features])
    d_prob = dummy.predict_proba(holdout[features])[:, 1]
    dummy_auc = compute_classification_metrics(holdout[TARGET], d_pred, d_prob)["roc_auc"]
    assert cand_auc > dummy_auc + 0.1
