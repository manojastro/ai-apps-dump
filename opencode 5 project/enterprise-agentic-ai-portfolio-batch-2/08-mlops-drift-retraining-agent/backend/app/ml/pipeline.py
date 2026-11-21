"""Model pipelines, metric computation and artifact persistence."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    DriftKnobs,
    TARGET,
    generate_customer_data,
)


def build_champion_pipeline() -> Pipeline:
    """Logistic regression champion with full preprocessing."""
    numeric = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric, NUMERIC_FEATURES),
            ("cat", categorical, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", LogisticRegression(max_iter=500, solver="lbfgs")),
        ]
    )


def build_candidate_pipeline() -> Pipeline:
    """Gradient boosting candidate trainer."""
    numeric = Pipeline(steps=[("impute", SimpleImputer(strategy="median"))])
    categorical = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric, NUMERIC_FEATURES),
            ("cat", categorical, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                GradientBoostingClassifier(
                    n_estimators=150, learning_rate=0.08, max_depth=3, random_state=0
                ),
            ),
        ]
    )


def compute_classification_metrics(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    y_prob: np.ndarray | pd.Series,
) -> dict[str, float]:
    """Compute the standard deployment metric set."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, np.asarray(y_prob, dtype=float))),
    }
    unique = set(np.unique(np.asarray(y_true)))
    if len(unique) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    else:
        metrics["roc_auc"] = 0.0
    return metrics


def predict_pipeline(
    pipeline: Pipeline, frame: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    """Return class predictions and churn probabilities for a frame."""
    prob = pipeline.predict_proba(frame)[:, 1]
    pred = (prob >= 0.5).astype(int)
    return pred, prob


def save_artifact(path: Path, payload: dict[str, Any]) -> None:
    """Persist a model artifact bundle with joblib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, path)


def load_artifact(path: Path | str) -> dict[str, Any]:
    """Load a model artifact bundle."""
    return joblib.load(path)


def train_reference_champion(n_samples: int = 6000, seed: int = 42) -> dict[str, Any]:
    """Train a fresh champion on clean reference data and compute reference stats."""
    train = generate_customer_data(n_samples, seed)
    holdout = generate_customer_data(4000, seed + 997)
    pipeline = build_champion_pipeline()
    pipeline.fit(train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train[TARGET])
    pred, prob = predict_pipeline(pipeline, holdout)
    metrics = compute_classification_metrics(holdout[TARGET], pred, prob)
    ref_pred, _ = predict_pipeline(pipeline, train)
    stats = compute_reference_stats(train, ref_pred)
    return {
        "pipeline": pipeline,
        "metrics": metrics,
        "stats": stats,
        "reference_df": train,
        "n_train": len(train),
        "seed": seed,
        "knobs": DriftKnobs().to_dict(),
    }


def compute_reference_stats(frame: pd.DataFrame, predictions: np.ndarray) -> dict[str, Any]:
    """Capture reference distributions used by every drift detector."""
    edges: dict[str, list[float]] = {}
    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    missing: dict[str, float] = {}
    for col in NUMERIC_FEATURES:
        series = frame[col].dropna()
        quantiles = np.linspace(0.0, 1.0, 11)
        bins = np.unique(series.quantile(quantiles).to_numpy(dtype=float))
        if len(bins) < 3:
            bins = np.array([series.min(), series.median(), series.max()])
        edges[col] = [float(b) for b in bins]
        means[col] = float(frame[col].mean())
        stds[col] = float(frame[col].std())
        missing[col] = float(frame[col].isna().mean())
    category_probs: dict[str, dict[str, float]] = {}
    for col in CATEGORICAL_FEATURES + ["customer_segment"]:
        counts = frame[col].value_counts(dropna=False, normalize=True)
        category_probs[col] = {str(k): float(v) for k, v in counts.items()}
        missing[col] = float(frame[col].isna().mean())
    return {
        "bin_edges": edges,
        "means": means,
        "stds": stds,
        "missing_rates": missing,
        "category_probs": category_probs,
        "positive_rate": float(np.mean(predictions)),
        "baseline_latency_ms": 12.0,
    }
