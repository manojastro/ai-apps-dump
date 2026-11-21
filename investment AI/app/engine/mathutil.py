from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def round_pct(value: float, digits: int = 2) -> float:
    return round(value, digits)


def normalize_weights(weights: dict[str, float], *, total: float = 100.0) -> dict[str, float]:
    raw = {k: max(0.0, v) for k, v in weights.items()}
    s = sum(raw.values())
    if s <= 0:
        raise ValueError("weights must be positive")
    scaled = {k: (v / s) * total for k, v in raw.items()}
    # Fix residual rounding on the largest sleeve.
    rounded = {k: round_pct(v) for k, v in scaled.items()}
    drift = round_pct(total - sum(rounded.values()))
    if drift != 0:
        largest = max(rounded, key=rounded.get)
        rounded[largest] = round_pct(rounded[largest] + drift)
    return rounded


def weights_sum_ok(weights: dict[str, float], *, total: float = 100.0, tol: float = 0.05) -> bool:
    return abs(sum(weights.values()) - total) <= tol


def monthly_surplus(
    take_home: float,
    essential: float,
    discretionary: float,
    insurance: float,
    rent: float,
    emis: float,
) -> float:
    return take_home - essential - discretionary - insurance - rent - emis


def compound_future_value(principal: float, annual_rate_pct: float, years: float) -> float:
    return principal * ((1 + annual_rate_pct / 100.0) ** years)


def remaining_interest(principal: float, annual_rate_pct: float, emi: float, months: int) -> float:
    if months <= 0 or emi <= 0 or principal <= 0:
        return 0.0
    monthly_rate = annual_rate_pct / 12.0 / 100.0
    balance = principal
    interest = 0.0
    for _ in range(months):
        if balance <= 0:
            break
        i = balance * monthly_rate
        interest += i
        principal_pay = emi - i
        if principal_pay <= 0:
            # EMI does not cover interest; cap to avoid infinite growth in the sim.
            break
        balance -= principal_pay
    return max(0.0, interest)
