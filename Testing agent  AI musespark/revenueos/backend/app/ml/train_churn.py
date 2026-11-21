"""Train and evaluate the churn model.

Label: the account stops (non-renewal or cancellation) within 90 days of the scoring date.

Why the gap between train and test: a training row dated T looks forward to T + 90. If a
test row starts inside that window, training labels would reveal test-period outcomes.
So training snapshots must end at least 90 days before the first test snapshot. That
"purge" costs data, but without it the reported result would be flattering and false.

Run: uv run python -m app.ml.train_churn
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from app.core.config import get_settings
from app.ml.common import (
    RANDOM_STATE,
    binary_report,
    data_fingerprint,
    load_active,
    make_lightgbm,
    make_logistic,
    register_model,
    replace_predictions,
)
from app.ml.explain import CHURN_TEMPLATES, explain_frame
from app.ml.features import CHURN_FEATURES, Frames, churn_features, load_frames

MODEL_NAME = "churn_90d"
HORIZON_DAYS = 90
SNAPSHOT_STEP_DAYS = 15
TEST_SNAPSHOTS = 3
HIGH_RISK = 0.35
MEDIUM_RISK = 0.15


def snapshot_grid(fr: Frames, as_of: date) -> list[pd.Timestamp]:
    """Scoring dates with enough usage history behind them and a full label window ahead."""
    first = fr.usage["date"].min() + pd.Timedelta(days=75)
    last = pd.Timestamp(as_of) - pd.Timedelta(days=HORIZON_DAYS)
    dates = pd.date_range(first, last, freq=f"{SNAPSHOT_STEP_DAYS}D")
    return list(dates)


def add_label(fr: Frames, rows: pd.DataFrame) -> pd.DataFrame:
    churned = fr.accounts.set_index("id")["churned_at"]
    churn_date = rows["account_id"].map(churned)
    window_end = rows["as_of"] + pd.Timedelta(days=HORIZON_DAYS)
    label = churn_date.notna() & (churn_date > rows["as_of"]) & (churn_date <= window_end)
    return rows.assign(churned=label.astype(int))


def top_decile_capture(rows: pd.DataFrame, scores: np.ndarray) -> dict:
    """Share of true churners found by working only the top 10% of accounts per snapshot."""
    frame = rows[["as_of", "churned"]].assign(score=scores)
    captured = total = 0
    for _, group in frame.groupby("as_of"):
        k = max(1, int(np.ceil(len(group) * 0.10)))
        captured += int(group.nlargest(k, "score")["churned"].sum())
        total += int(group["churned"].sum())
    return {
        "captured": captured, "total_churners": total,
        "capture_rate": round(captured / total, 4) if total else None,
    }


def fit(algorithm: str, rows: pd.DataFrame):
    model = make_lightgbm() if algorithm == "lightgbm" else make_logistic()
    model.fit(rows[CHURN_FEATURES], rows["churned"])
    return model


def predict(model, rows: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(rows[CHURN_FEATURES])[:, 1]


def renewal_baseline(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Trivial baseline: renewal proximity alone, which is what a calendar would tell you."""
    def closeness(frame: pd.DataFrame) -> np.ndarray:
        return (frame["days_to_renewal"].clip(-30, 365) <= HORIZON_DAYS).astype(float).to_frame()

    model = LogisticRegression(random_state=RANDOM_STATE)
    model.fit(closeness(train), train["churned"])
    return model.predict_proba(closeness(test))[:, 1]


def train(fr: Frames, as_of: date) -> dict:
    grid = snapshot_grid(fr, as_of)
    rows = add_label(fr, churn_features(fr, grid))

    test_dates = grid[-TEST_SNAPSHOTS:]
    purge_before = test_dates[0] - pd.Timedelta(days=HORIZON_DAYS)
    train_rows = rows[rows["as_of"] <= purge_before]
    test_rows = rows[rows["as_of"].isin(test_dates)]

    train_dates = sorted(train_rows["as_of"].unique())
    val_start = train_dates[int(len(train_dates) * 0.67)]
    fit_rows = train_rows[train_rows["as_of"] < val_start - pd.Timedelta(days=HORIZON_DAYS)]
    if fit_rows["churned"].sum() < 5:  # Too thin once purged: fall back to no purge here.
        fit_rows = train_rows[train_rows["as_of"] < val_start]
    val_rows = train_rows[train_rows["as_of"] >= val_start]

    validation = {}
    for algorithm in ("logistic_regression", "lightgbm"):
        scores = predict(fit(algorithm, fit_rows), val_rows)
        validation[algorithm] = round(float(roc_auc_score(val_rows["churned"], scores)), 4)
    selected = max(validation, key=validation.get)

    y = test_rows["churned"].to_numpy()
    groups = test_rows["account_id"].to_numpy()
    report = {}
    capture = {}
    for algorithm in ("logistic_regression", "lightgbm"):
        scores = predict(fit(algorithm, train_rows), test_rows)
        report[algorithm] = binary_report(y, scores, groups, HIGH_RISK)
        capture[algorithm] = top_decile_capture(test_rows, scores)
    baseline = renewal_baseline(train_rows, test_rows)
    report["renewal_baseline"] = binary_report(y, baseline, groups, HIGH_RISK)
    capture["renewal_baseline"] = top_decile_capture(test_rows, baseline)
    report["selected"] = report[selected]

    model = fit(selected, rows)
    version = f"{as_of.isoformat()}-{data_fingerprint(rows[CHURN_FEATURES + ['churned']])}"
    metrics = {
        "train_snapshots": [str(pd.Timestamp(d).date()) for d in train_dates],
        "test_snapshots": [str(d.date()) for d in test_dates],
        "train_rows": len(train_rows),
        "train_positive_rows": int(train_rows["churned"].sum()),
        "test_rows": len(test_rows),
        "test_positive_rows": int(y.sum()),
        "validation_auc": validation,
        "selected_algorithm": selected,
        "test": report,
        "top_decile_capture": capture,
        "high_risk_threshold": HIGH_RISK,
        "medium_risk_threshold": MEDIUM_RISK,
        "final_training_rows": len(rows),
    }
    artifact = {"model": model, "algorithm": selected, "features": CHURN_FEATURES}
    register_model(MODEL_NAME, version, selected, artifact, metrics)
    return metrics


def score_accounts(fr: Frames, as_of: date, artifact: dict | None = None) -> pd.DataFrame:
    artifact = artifact or load_active(MODEL_NAME)
    frame = churn_features(fr, [pd.Timestamp(as_of)])
    frame["p_churn"] = artifact["model"].predict_proba(frame[CHURN_FEATURES])[:, 1]
    return frame


def store_scores(fr: Frames, as_of: date) -> int:
    artifact = load_active(MODEL_NAME)
    frame = score_accounts(fr, as_of, artifact)
    reasons = explain_frame(artifact["model"], frame, CHURN_FEATURES, CHURN_TEMPLATES, False)
    rows = [
        {"entity_id": account_id, "score": p, "reasons": r}
        for account_id, p, r in zip(frame["account_id"], frame["p_churn"], reasons, strict=True)
    ]
    replace_predictions("account", MODEL_NAME, artifact["version"], rows)
    return len(rows)


def main() -> None:
    settings = get_settings()
    fr = load_frames()
    metrics = train(fr, settings.data_as_of)
    print(json.dumps(metrics, indent=2, default=str))
    print(f"Scored accounts: {store_scores(fr, settings.data_as_of)}")


if __name__ == "__main__":
    main()
