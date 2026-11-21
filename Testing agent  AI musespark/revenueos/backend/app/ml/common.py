"""Shared ML helpers: metrics, artifact storage, the model registry.

Metrics report a confidence interval because the held-out sets here are small. A bare
AUC of 0.80 hides how much it could move with a different sample. The interval is
clustered by entity, since one deal can appear in several snapshots.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ModelVersion, Prediction
from app.db.session import get_engine

RANDOM_STATE = 42


def make_logistic() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=0.5, max_iter=2000, random_state=RANDOM_STATE)),
    ])


def make_lightgbm() -> LGBMClassifier:
    # Small trees and strong regularisation: only a few hundred examples exist.
    return LGBMClassifier(
        n_estimators=150, learning_rate=0.03, num_leaves=7, min_child_samples=20,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=2.0,
        random_state=RANDOM_STATE, n_jobs=1, deterministic=True, force_row_wise=True,
        verbose=-1,
    )


def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    index = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    total = 0.0
    for b in range(bins):
        mask = index == b
        if mask.any():
            total += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    return float(total)


def calibration_table(y: np.ndarray, p: np.ndarray, bins: int = 5) -> list[dict[str, float]]:
    """Predicted vs. observed rate per equal-count bin."""
    order = np.argsort(p)
    rows = []
    for chunk in np.array_split(order, bins):
        if len(chunk):
            rows.append({
                "n": int(len(chunk)),
                "mean_predicted": round(float(p[chunk].mean()), 3),
                "observed_rate": round(float(y[chunk].mean()), 3),
            })
    return rows


def bootstrap_auc_ci(
    y: np.ndarray, p: np.ndarray, groups: np.ndarray, n_boot: int = 500
) -> tuple[float, float]:
    """95% interval, resampling whole entities so repeated snapshots stay together."""
    rng = np.random.default_rng(RANDOM_STATE)
    unique = np.unique(groups)
    positions = {g: np.flatnonzero(groups == g) for g in unique}
    scores = []
    for _ in range(n_boot):
        sample = rng.choice(unique, size=len(unique), replace=True)
        idx = np.concatenate([positions[g] for g in sample])
        if 0 < y[idx].sum() < len(idx):
            scores.append(roc_auc_score(y[idx], p[idx]))
    low, high = np.percentile(scores, [2.5, 97.5])
    return float(low), float(high)


def binary_report(
    y: np.ndarray, p: np.ndarray, groups: np.ndarray, threshold: float
) -> dict[str, Any]:
    predicted = (p >= threshold).astype(int)
    low, high = bootstrap_auc_ci(y, p, groups)
    return {
        "rows": int(len(y)),
        "entities": int(len(np.unique(groups))),
        "positive_rate": round(float(y.mean()), 4),
        "auc": round(float(roc_auc_score(y, p)), 4),
        "auc_ci95": [round(low, 4), round(high, 4)],
        "brier": round(float(brier_score_loss(y, p)), 4),
        "ece": round(expected_calibration_error(y, p), 4),
        "threshold": round(float(threshold), 3),
        "precision": round(float(precision_score(y, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(y, predicted, zero_division=0)), 4),
        "calibration": calibration_table(y, p),
    }


def best_f1_threshold(y: np.ndarray, p: np.ndarray) -> float:
    best, best_f1 = 0.5, -1.0
    for threshold in np.arange(0.2, 0.81, 0.02):
        predicted = p >= threshold
        tp = (predicted & (y == 1)).sum()
        if predicted.sum() == 0 or tp == 0:
            continue
        precision, recall = tp / predicted.sum(), tp / y.sum()
        f1 = 2 * precision * recall / (precision + recall)
        if f1 > best_f1:
            best, best_f1 = float(threshold), float(f1)
    return best


def data_fingerprint(frame: pd.DataFrame) -> str:
    """Short hash of training data, so a version maps to exactly what it was trained on."""
    digest = hashlib.sha256(pd.util.hash_pandas_object(frame, index=False).values.tobytes())
    return digest.hexdigest()[:8]


def artifact_path(model_name: str, version: str) -> Path:
    folder = get_settings().artifact_dir
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{model_name}-{version}.joblib"


def register_model(
    model_name: str, version: str, algorithm: str, artifact: dict, metrics: dict
) -> None:
    """Save the artifact and mark this version active. Re-running replaces the same version."""
    path = artifact_path(model_name, version)
    joblib.dump(artifact, path)
    clean_metrics = json.loads(json.dumps(metrics, default=float))
    with Session(get_engine()) as session:
        session.execute(update(ModelVersion).where(ModelVersion.model_name == model_name)
                        .values(is_active=False))
        existing = (session.query(ModelVersion)
                    .filter_by(model_name=model_name, version=version).one_or_none())
        if existing:
            existing.metrics_json = clean_metrics
            existing.algorithm = algorithm
            existing.artifact_path = path.name
            existing.is_active = True
        else:
            session.add(ModelVersion(
                model_name=model_name, version=version, algorithm=algorithm,
                metrics_json=clean_metrics, artifact_path=path.name, is_active=True,
            ))
        session.commit()
    _log_mlflow(model_name, version, clean_metrics)


def _log_mlflow(model_name: str, version: str, metrics: dict) -> None:
    """Optional local tracking. Skipped unless MLFLOW_TRACKING_URI is set."""
    uri = get_settings().mlflow_tracking_uri
    if not uri:
        return
    import mlflow

    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(model_name)
    with mlflow.start_run(run_name=version):
        test = metrics.get("test", {}).get("selected", {})
        mlflow.log_metrics({k: v for k, v in test.items() if isinstance(v, float)})


def load_active(model_name: str) -> dict:
    with Session(get_engine()) as session:
        row = (session.query(ModelVersion)
               .filter_by(model_name=model_name, is_active=True).one_or_none())
    if row is None:
        raise LookupError(f"No active model named {model_name}. Run training first.")
    artifact = joblib.load(get_settings().artifact_dir / row.artifact_path)
    artifact["version"] = row.version
    return artifact


def replace_predictions(
    entity_type: str, model_name: str, version: str, rows: list[dict]
) -> None:
    """Replace this version's scores, so a re-run does not stack duplicates."""
    with Session(get_engine()) as session:
        session.query(Prediction).filter_by(
            entity_type=entity_type, model_name=model_name, model_version=version
        ).delete()
        session.add_all(Prediction(
            entity_type=entity_type, entity_id=int(r["entity_id"]), model_name=model_name,
            model_version=version, score=float(r["score"]), reasons_json=r["reasons"],
        ) for r in rows)
        session.commit()
