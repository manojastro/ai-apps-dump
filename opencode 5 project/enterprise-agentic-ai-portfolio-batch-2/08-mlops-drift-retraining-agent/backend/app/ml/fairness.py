"""Segment fairness measurement for churn selections."""
from __future__ import annotations

import numpy as np
import pandas as pd


def selection_rates_by_segment(
    predictions: np.ndarray, segments: pd.Series
) -> dict[str, float]:
    """Positive selection rate per customer segment."""
    frame = pd.DataFrame({"pred": np.asarray(predictions), "seg": segments.to_numpy()})
    rates = frame.groupby("seg")["pred"].mean()
    return {str(k): round(float(v), 6) for k, v in rates.items()}


def disparity_ratio(rates: dict[str, float]) -> float:
    """Min over max selection rate ratio; 1.0 means perfect parity."""
    values = [v for v in rates.values() if v >= 0.0]
    if len(values) < 2:
        return 1.0
    lowest, highest = min(values), max(values)
    if highest <= 0.0:
        return 1.0
    return round(lowest / highest, 6)


def evaluate_fairness(
    predictions: np.ndarray,
    segments: pd.Series,
    threshold: float = 0.8,
) -> dict:
    """Full fairness evaluation payload for persistence."""
    rates = selection_rates_by_segment(predictions, segments)
    ratio = disparity_ratio(rates)
    return {
        "segment_column": "customer_segment",
        "selection_rates": rates,
        "disparity_ratio": ratio,
        "threshold": threshold,
        "passed": bool(ratio >= threshold),
    }
