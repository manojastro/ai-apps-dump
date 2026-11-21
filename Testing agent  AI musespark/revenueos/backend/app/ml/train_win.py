"""Train and evaluate the deal win-probability model.

Evaluation design:
- Rows are snapshots of open deals on past dates, labelled by the final outcome.
- Time-based split: train on deals closed before the cutoff, test on snapshots after it.
- Model choice and threshold come from a validation slice inside the training period,
  so the test set is touched once. It is reported, never tuned against.
- The shipped model is then refit on all resolved history.

Run: uv run python -m app.ml.train_win
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from app.core.config import get_settings
from app.ml.common import (
    best_f1_threshold,
    binary_report,
    data_fingerprint,
    load_active,
    make_lightgbm,
    make_logistic,
    register_model,
    replace_predictions,
)
from app.ml.explain import DEAL_TEMPLATES, explain_frame
from app.ml.features import (
    DEAL_FEATURES,
    Frames,
    close_date_at,
    deal_features,
    deal_snapshots,
    fit_stage_days,
    load_frames,
    snapshot_dates,
)

MODEL_NAME = "win_probability"
TEST_SHARE = 0.30
VALIDATION_SHARE = 0.25


def labelled_rows(fr: Frames, stage_days: dict, end: pd.Timestamp) -> pd.DataFrame:
    """Snapshot rows for deals resolved by `end`, with the label attached."""
    start = fr.deals["created_at"].min().date()
    frame = deal_snapshots(fr, snapshot_dates(start, end.date()))
    resolved = fr.deals[fr.deals["closed_at"].notna() & (fr.deals["closed_at"] <= end)]
    frame = frame[frame["deal_id"].isin(resolved["id"])]
    frame = deal_features(fr, frame, stage_days)
    lookup = resolved.set_index("id")
    frame["won"] = (frame["deal_id"].map(lookup["outcome"]) == "won").astype(int)
    frame["closed_at"] = frame["deal_id"].map(lookup["closed_at"])
    return frame


def stage_rate_baseline(train: pd.DataFrame, rows: pd.DataFrame) -> np.ndarray:
    """Trivial baseline: the historical win rate of the deal's current stage."""
    rates = train.groupby("stage")["won"].mean()
    return rows["stage"].map(rates).fillna(train["won"].mean()).to_numpy()


def fit(algorithm: str, rows: pd.DataFrame):
    model = make_lightgbm() if algorithm == "lightgbm" else make_logistic()
    model.fit(rows[DEAL_FEATURES], rows["won"])
    return model


def predict(model, rows: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(rows[DEAL_FEATURES])[:, 1]


def fit_slip_rates(rows: pd.DataFrame, fr: Frames) -> dict[str, float]:
    """Of won deals expected to close this quarter, how many actually did, by stage.

    A win that lands next quarter does not help this quarter's forecast, so the
    simulation multiplies win probability by this rate.
    """
    deals = fr.deals.set_index("id")
    frame = rows[rows["won"] == 1].copy()
    outcomes: dict[str, list[int]] = {}
    for t, group in frame.groupby("as_of"):
        known = close_date_at(deals.loc[group["deal_id"]], t)
        quarter = pd.Timestamp(t).to_period("Q")
        expected_in = known.dt.to_period("Q") == quarter
        closed_in = deals.loc[group["deal_id"], "closed_at"].dt.to_period("Q") == quarter
        for stage, hit, expected in zip(group["stage"], closed_in, expected_in, strict=True):
            if expected:
                outcomes.setdefault(stage, []).append(int(hit))
    overall = [v for hits in outcomes.values() for v in hits]
    default = float(np.mean(overall)) if overall else 0.8
    return {
        stage: float(np.mean(outcomes[stage])) if len(outcomes.get(stage, [])) >= 5 else default
        for stage in ("prospecting", "qualification", "proposal", "negotiation")
    }


def train(fr: Frames, as_of: date) -> dict:
    end = pd.Timestamp(as_of)
    resolved = fr.deals[fr.deals["closed_at"].notna()].sort_values("closed_at")
    cutoff = resolved["closed_at"].iloc[int(len(resolved) * (1 - TEST_SHARE))]
    stage_days = fit_stage_days(fr, cutoff)
    rows = labelled_rows(fr, stage_days, end)

    train_rows = rows[rows["closed_at"] < cutoff]
    test_rows = rows[(rows["as_of"] >= cutoff) & (rows["closed_at"] >= cutoff)]

    closed_train = train_rows.drop_duplicates("deal_id").sort_values("closed_at")
    val_cut = closed_train["closed_at"].iloc[int(len(closed_train) * (1 - VALIDATION_SHARE))]
    fit_rows = train_rows[train_rows["closed_at"] < val_cut]
    val_rows = train_rows[(train_rows["closed_at"] >= val_cut) & (train_rows["as_of"] >= val_cut)]

    validation: dict[str, float] = {}
    val_scores: dict[str, np.ndarray] = {}
    for algorithm in ("logistic_regression", "lightgbm"):
        scores = predict(fit(algorithm, fit_rows), val_rows)
        val_scores[algorithm] = scores
        validation[algorithm] = round(float(roc_auc_score(val_rows["won"], scores)), 4)
    selected = max(validation, key=validation.get)
    threshold = best_f1_threshold(val_rows["won"].to_numpy(), val_scores[selected])

    y = test_rows["won"].to_numpy()
    groups = test_rows["deal_id"].to_numpy()
    test_report = {}
    for algorithm in ("logistic_regression", "lightgbm"):
        scores = predict(fit(algorithm, train_rows), test_rows)
        test_report[algorithm] = binary_report(y, scores, groups, threshold)
    baseline_scores = stage_rate_baseline(train_rows, test_rows)
    test_report["stage_baseline"] = binary_report(y, baseline_scores, groups, threshold)
    test_report["selected"] = test_report[selected]

    # Final model: all resolved history, with stage averages refit to match.
    final_stage_days = fit_stage_days(fr, end + pd.Timedelta(days=1))
    final_rows = labelled_rows(fr, final_stage_days, end)
    model = fit(selected, final_rows)
    slip_rates = fit_slip_rates(final_rows, fr)

    version = f"{as_of.isoformat()}-{data_fingerprint(final_rows[DEAL_FEATURES + ['won']])}"
    metrics = {
        "cutoff": cutoff.date().isoformat(),
        "train": {"rows": len(train_rows), "deals": int(train_rows["deal_id"].nunique())},
        "test_rows": len(test_rows),
        "validation_auc": validation,
        "selected_algorithm": selected,
        "test": test_report,
        "slip_rates": slip_rates,
        "final_training_rows": len(final_rows),
    }
    artifact = {
        "model": model, "algorithm": selected, "features": DEAL_FEATURES,
        "stage_days": final_stage_days, "threshold": threshold, "slip_rates": slip_rates,
    }
    register_model(MODEL_NAME, version, selected, artifact, metrics)
    return metrics


def score_open_deals(fr: Frames, as_of: date, artifact: dict | None = None) -> pd.DataFrame:
    """Score deals open on `as_of`, using only what was known on that date."""
    artifact = artifact or load_active(MODEL_NAME)
    t = pd.Timestamp(as_of)
    snapshots = deal_snapshots(fr, [t])
    frame = deal_features(fr, snapshots, artifact["stage_days"])
    frame["p_win"] = artifact["model"].predict_proba(frame[DEAL_FEATURES])[:, 1]
    return frame


def store_scores(fr: Frames, as_of: date) -> int:
    artifact = load_active(MODEL_NAME)
    frame = score_open_deals(fr, as_of, artifact)
    reasons = explain_frame(artifact["model"], frame, DEAL_FEATURES, DEAL_TEMPLATES, True)
    rows = [
        {"entity_id": deal_id, "score": p, "reasons": r}
        for deal_id, p, r in zip(frame["deal_id"], frame["p_win"], reasons, strict=True)
    ]
    replace_predictions("deal", MODEL_NAME, artifact["version"], rows)
    return len(rows)


def main() -> None:
    settings = get_settings()
    fr = load_frames()
    metrics = train(fr, settings.data_as_of)
    print(json.dumps(metrics, indent=2, default=str))
    print(f"Scored open deals: {store_scores(fr, settings.data_as_of)}")


if __name__ == "__main__":
    main()
