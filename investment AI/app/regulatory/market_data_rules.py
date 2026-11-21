from __future__ import annotations

FRESHNESS_HOURS = {
    "market_index": 24,
    "bank_post_office_rate": 24 * 7,
    "regulatory": 24 * 30,
}


def freshness_status(age_hours: float, kind: str) -> str:
    limit = FRESHNESS_HOURS.get(kind, 24)
    if age_hours <= limit:
        return "verified"
    return "stale"
