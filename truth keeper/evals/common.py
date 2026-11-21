"""Shared helpers for evals."""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def load_ground_truth(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4)}


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 2)
    qs = statistics.quantiles(values, n=100, method="inclusive")
    return round(qs[max(0, min(98, int(p) - 1))], 2)
