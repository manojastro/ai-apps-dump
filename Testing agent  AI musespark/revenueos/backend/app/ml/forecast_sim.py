"""Monte Carlo forecast, plus a walk-forward back-test.

Each simulated quarter flips one weighted coin per deal: it lands this quarter with
probability p_win x p_in_quarter. Summing the winners over 5,000 runs gives a range,
not just a number, because a pipeline of a few large deals is genuinely uncertain.

The back-test never peeks. For each past quarter it trains only on deals closed before
that quarter's snapshot date, then compares the forecast with what actually happened.

Run: uv run python -m app.ml.forecast_sim
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.ml.common import make_lightgbm, make_logistic
from app.ml.features import (
    DEAL_FEATURES,
    Frames,
    close_date_at,
    deal_features,
    deal_snapshots,
    fit_stage_days,
    load_frames,
    open_deals_at,
)

N_SIMULATIONS = 5_000
SIM_SEED = 42
BACKTEST_OFFSET_DAYS = 14

# Fixed weights a typical CRM would apply. This is what the model has to beat.
STAGE_WEIGHTS = {"prospecting": 0.10, "qualification": 0.25, "proposal": 0.50, "negotiation": 0.75}


@dataclass
class ForecastRange:
    low: float
    expected: float
    high: float


def simulate(
    amounts: np.ndarray,
    probabilities: np.ndarray,
    base: float = 0.0,
    n_runs: int = N_SIMULATIONS,
    seed: int = SIM_SEED,
) -> ForecastRange:
    """Return the P10, mean and P90 of simulated quarter revenue."""
    if len(amounts) == 0:
        return ForecastRange(base, base, base)
    rng = np.random.default_rng(seed)
    wins = rng.random((n_runs, len(amounts))) < probabilities
    totals = base + wins @ amounts
    low, high = np.percentile(totals, [10, 90])
    return ForecastRange(float(low), float(totals.mean()), float(high))


def quarter_label(d: date | pd.Timestamp) -> str:
    period = pd.Timestamp(d).to_period("Q")
    return f"{period.year}Q{period.quarter}"


def quarter_bounds(label: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    period = pd.Period(label, freq="Q")
    return period.start_time.normalize(), period.end_time.normalize()


def stage_weighted(amounts: np.ndarray, stages: pd.Series) -> float:
    return float((amounts * stages.map(STAGE_WEIGHTS).to_numpy()).sum())


def rep_commit(amounts: np.ndarray, stages: pd.Series) -> float:
    """Reps commit what has reached negotiation."""
    return float(amounts[(stages == "negotiation").to_numpy()].sum())


def _training_rows(fr: Frames, t: pd.Timestamp, stage_days: dict) -> pd.DataFrame:
    """Snapshots strictly before t, for deals already resolved before t."""
    from app.ml.features import snapshot_dates

    start = fr.deals["created_at"].min().date()
    dates = snapshot_dates(start, (t - pd.Timedelta(days=1)).date())
    snapshots = deal_snapshots(fr, dates)
    resolved = fr.deals[fr.deals["closed_at"] < t].set_index("id")
    snapshots = snapshots[snapshots["deal_id"].isin(resolved.index)]
    rows = deal_features(fr, snapshots, stage_days)
    rows["won"] = (rows["deal_id"].map(resolved["outcome"]) == "won").astype(int)
    return rows


def _slip_rates_before(rows: pd.DataFrame, fr: Frames) -> dict[str, float]:
    from app.ml.train_win import fit_slip_rates

    return fit_slip_rates(rows, fr)


def backtest_quarter(fr: Frames, label: str, algorithm: str) -> dict:
    start, end = quarter_bounds(label)
    t = start + pd.Timedelta(days=BACKTEST_OFFSET_DAYS)
    stage_days = fit_stage_days(fr, t)
    rows = _training_rows(fr, t, stage_days)
    model = make_lightgbm() if algorithm == "lightgbm" else make_logistic()
    model.fit(rows[DEAL_FEATURES], rows["won"])
    slip = _slip_rates_before(rows, fr)

    deals = fr.deals
    open_at_t = open_deals_at(fr, t)
    in_quarter = close_date_at(open_at_t, t).between(start, end)
    pipeline = open_at_t[in_quarter]
    features = deal_features(
        fr, pd.DataFrame({"deal_id": pipeline["id"].values, "as_of": t}), stage_days
    )
    p_win = model.predict_proba(features[DEAL_FEATURES])[:, 1]
    p_landing = p_win * features["stage"].map(slip).to_numpy()
    amounts = pipeline["amount"].to_numpy()
    stages = features["stage"].reset_index(drop=True)

    won = deals[deals["outcome"] == "won"]
    won_q = won[won["closed_at"].between(start, end)]
    qtd = float(won_q[won_q["closed_at"] <= t]["amount"].sum())
    actual_pipeline = qtd + float(won_q[won_q["id"].isin(pipeline["id"])]["amount"].sum())
    actual_total = float(won_q["amount"].sum())

    forecast = simulate(amounts, p_landing, base=qtd)
    weighted = qtd + stage_weighted(amounts, stages)
    commit = qtd + rep_commit(amounts, stages)

    def error(value: float) -> float:
        return round(abs(value - actual_pipeline) / actual_pipeline, 4)

    return {
        "quarter": label,
        "snapshot_date": t.date().isoformat(),
        "training_rows": len(rows),
        "open_deals_in_quarter": len(pipeline),
        "low": round(forecast.low, 2),
        "expected": round(forecast.expected, 2),
        "high": round(forecast.high, 2),
        "stage_weighted": round(weighted, 2),
        "rep_commit": round(commit, 2),
        "actual_from_pipeline": round(actual_pipeline, 2),
        "actual_total_closed_won": round(actual_total, 2),
        "abs_pct_error_model": error(forecast.expected),
        "abs_pct_error_stage_weighted": error(weighted),
        "abs_pct_error_rep_commit": error(commit),
        "within_p10_p90": bool(forecast.low <= actual_pipeline <= forecast.high),
    }


def backtest(fr: Frames, as_of: date, algorithm: str, quarters: int = 4) -> dict:
    current = pd.Timestamp(as_of).to_period("Q")
    labels = [quarter_label((current - i).start_time) for i in range(quarters, 0, -1)]
    results = [backtest_quarter(fr, label, algorithm) for label in labels]

    def mean_of(key: str) -> float:
        return round(float(np.mean([r[key] for r in results])), 4)

    return {
        "algorithm": algorithm,
        "note": (
            "Error is measured against closed-won from deals visible at the snapshot, plus "
            "quarter-to-date wins. Deals created and closed after the snapshot are not "
            "forecastable from pipeline and are shown separately as actual_total_closed_won."
        ),
        "quarters": results,
        "mape_model": mean_of("abs_pct_error_model"),
        "mape_stage_weighted": mean_of("abs_pct_error_stage_weighted"),
        "mape_rep_commit": mean_of("abs_pct_error_rep_commit"),
        "p10_p90_coverage": round(float(np.mean([r["within_p10_p90"] for r in results])), 2),
    }


def main() -> None:
    from app.ml.common import load_active
    from app.ml.train_win import MODEL_NAME

    settings = get_settings()
    algorithm = load_active(MODEL_NAME)["algorithm"]
    result = backtest(load_frames(), settings.data_as_of, algorithm)
    path = settings.artifact_dir / "forecast_backtest.json"
    path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
