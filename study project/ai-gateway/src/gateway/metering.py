"""Metering: token estimate, cost estimate, monthly budget check, ledger reads."""

from __future__ import annotations

import calendar
import sqlite3
import time
from pathlib import Path
from typing import Literal

import yaml


def estimate_tokens(text: str) -> int:
    """Mock token estimate (whitespace split). Real gateway would use tiktoken."""
    return max(1, len(text.split()))


def load_prices(prices_path: str) -> dict[str, dict[str, float]]:
    data = yaml.safe_load(Path(prices_path).read_text(encoding="utf-8"))
    return dict(data.get("models", {}))


def estimate_cost(
    model: str, tokens_in: int, tokens_out: int,
    prices: dict[str, dict[str, float]],
) -> float:
    """Cost in USD from prices.yaml (per-1K-token rates). Unknown model -> 0."""
    entry = prices.get(model)
    if not entry:
        return 0.0
    return (
        tokens_in / 1000.0 * float(entry.get("input_per_1k", 0.0))
        + tokens_out / 1000.0 * float(entry.get("output_per_1k", 0.0))
    )


def month_start_ts(now: float | None = None) -> float:
    t = time.localtime(now)
    return float(calendar.timegm((t.tm_year, t.tm_mon, 1, 0, 0, 0, 0, 0, 0)))


def month_spend(conn: sqlite3.Connection, tenant: str,
                now: float | None = None) -> float:
    start = month_start_ts(now)
    row = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) AS s FROM usage_ledger"
        " WHERE tenant = ? AND ts >= ?",
        (tenant, start),
    ).fetchone()
    return float(row["s"])


BudgetState = Literal["ok", "soft", "hard"]


def check_budget(spent: float, budget: float) -> tuple[BudgetState, str]:
    """Soft alert at 80%, hard stop at 100%."""
    if budget <= 0:
        return "hard", "budget_exceeded"
    ratio = spent / budget
    if ratio >= 1.0:
        return "hard", "budget_exceeded"
    if ratio >= 0.8:
        return "soft", "budget_soft_alert"
    return "ok", ""
