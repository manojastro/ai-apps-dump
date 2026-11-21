"""Token price table. SET BY LEARNER — verify on provider site."""

from pathlib import Path
from typing import Any

import yaml


def load_prices(path: Path | None = None) -> dict[str, Any]:
    p = path or Path(__file__).resolve().parents[3] / "config" / "prices.yaml"
    if not p.exists():
        p = Path("config/prices.yaml")
    return yaml.safe_load(p.read_text()) or {}


def estimate_cost(
    model: str, tokens_in: int, tokens_out: int, prices: dict[str, Any] | None = None
) -> float:
    """USD for one call. Prices are per 1K tokens."""
    table: dict[str, Any] = prices if prices is not None else load_prices()
    # search openai.<model> or any provider section containing model
    entry: dict[str, float] | None = None
    for _provider, models in table.items():
        if isinstance(models, dict) and model in models:
            raw = models[model]
            entry = {
                "in": float(raw.get("input_per_1k", 0)),
                "out": float(raw.get("output_per_1k", 0)),
            }
            break
    if entry is None:
        return 0.0
    return tokens_in / 1000 * entry["in"] + tokens_out / 1000 * entry["out"]
