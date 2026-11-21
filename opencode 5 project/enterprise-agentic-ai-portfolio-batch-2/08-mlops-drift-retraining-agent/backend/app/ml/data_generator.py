"""Seeded synthetic customer churn generator with drift knobs."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "usage_gb",
    "support_tickets_30d",
]
CATEGORICAL_FEATURES = ["contract_type", "payment_method"]
SEGMENT_COLUMN = "customer_segment"
TARGET = "churn"
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [SEGMENT_COLUMN]

CONTRACT_CATEGORIES = ["month-to-month", "one-year", "two-year"]
PAYMENT_CATEGORIES = ["credit_card", "bank_transfer", "electronic_check"]
SEGMENTS = ["retail", "business"]

_MEAN_SHIFT_DIRECTIONS = {
    "tenure_months": -1.0,
    "monthly_charges": 0.8,
    "usage_gb": 0.6,
    "support_tickets_30d": 0.7,
}
_MISSING_COLUMNS = ["usage_gb", "payment_method"]


@dataclass
class DriftKnobs:
    """Controls applied to the generator to simulate population change."""

    mean_shift: float = 0.0
    variance_shift: float = 1.0
    category_redistribution: float = 0.0
    new_segment_share: float = 0.0
    missingness_rate: float = 0.0
    seasonality_factor: float = 1.0
    label_noise: float = 0.0
    drop_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> DriftKnobs:
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (payload or {}).items() if k in known})


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_customer_data(
    n_samples: int,
    seed: int,
    knobs: DriftKnobs | None = None,
) -> pd.DataFrame:
    """Generate a labelled customer churn sample under optional drift knobs."""
    knobs = knobs or DriftKnobs()
    rng = np.random.default_rng(seed)

    tenure = np.clip(rng.gamma(shape=2.0, scale=24.0, size=n_samples), 1.0, 72.0)
    charges = np.clip(rng.normal(65.0, 20.0, size=n_samples), 15.0, 130.0)
    usage = np.clip(rng.normal(50.0, 15.0, size=n_samples), 5.0, 120.0)
    usage = usage * knobs.seasonality_factor
    tickets = rng.poisson(1.2, size=n_samples).astype(float)

    contract_p = np.array([0.60, 0.25, 0.15])
    shifted_contract_p = np.array([0.85, 0.10, 0.05])
    r = min(max(knobs.category_redistribution, 0.0), 1.0)
    contract_probs = (1 - r) * contract_p + r * shifted_contract_p
    contract = rng.choice(CONTRACT_CATEGORIES, size=n_samples, p=contract_probs)

    payment_p = np.array([0.45, 0.35, 0.20])
    shifted_payment_p = np.array([0.30, 0.15, 0.55])
    payment_probs = (1 - r) * payment_p + r * shifted_payment_p
    payment = rng.choice(PAYMENT_CATEGORIES, size=n_samples, p=payment_probs)

    business_share = float(np.clip(0.25 + knobs.new_segment_share, 0.0, 0.95))
    segment = rng.choice(
        SEGMENTS, size=n_samples, p=[1 - business_share, business_share]
    )

    df = pd.DataFrame(
        {
            "tenure_months": tenure,
            "monthly_charges": charges,
            "usage_gb": usage,
            "support_tickets_30d": tickets,
            "contract_type": contract,
            "payment_method": payment,
            "customer_segment": segment,
        }
    )

    logit = (
        -1.4
        - 0.04 * df["tenure_months"].to_numpy()
        + 0.022 * (df["monthly_charges"].to_numpy() - 65.0)
        - 0.012 * (df["usage_gb"].to_numpy() - 50.0)
        + 0.60 * df["support_tickets_30d"].to_numpy()
        + np.where(contract == "month-to-month", 1.4, 0.0)
        + np.where(contract == "two-year", -0.7, 0.0)
        + np.where(payment == "electronic_check", 0.6, 0.0)
        + np.where(segment == "business", 0.3, 0.0)
    )
    probs = _sigmoid(logit)
    labels = (rng.random(n_samples) < probs).astype(int)

    noise_mask = rng.random(n_samples) < knobs.label_noise
    labels = np.where(noise_mask, 1 - labels, labels)
    df[TARGET] = labels

    if knobs.variance_shift != 1.0:
        for col in NUMERIC_FEATURES:
            mu = df[col].mean()
            df[col] = mu + (df[col] - mu) * knobs.variance_shift
        df["support_tickets_30d"] = df["support_tickets_30d"].clip(lower=0).round()

    if knobs.mean_shift != 0.0:
        for col in NUMERIC_FEATURES:
            sigma = df[col].std() or 1.0
            df[col] = df[col] + _MEAN_SHIFT_DIRECTIONS[col] * knobs.mean_shift * sigma
        df["support_tickets_30d"] = df["support_tickets_30d"].clip(lower=0).round()

    if knobs.missingness_rate > 0.0:
        for col in _MISSING_COLUMNS:
            mask = rng.random(n_samples) < knobs.missingness_rate
            df.loc[mask, col] = np.nan

    for col in knobs.drop_features:
        if col in df.columns:
            df = df.drop(columns=[col])

    return df.reset_index(drop=True)


def feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return model input columns present in a frame."""
    return [c for c in FEATURES if c in frame.columns]
