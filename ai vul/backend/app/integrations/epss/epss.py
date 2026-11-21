"""FIRST Exploit Prediction Scoring System (EPSS) adapter.

EPSS is a *probability estimate* of exploitation activity in the next 30 days. It is never
treated as proof of exploitation anywhere in this application.
"""

from __future__ import annotations

from typing import Any

from app.integrations.http import request_with_retry

BATCH_SIZE = 50  # keep URLs well below common length limits


def parse_epss_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """Parse one EPSS API row; returns None for malformed values instead of guessing."""
    try:
        epss = float(row["epss"])
        percentile = float(row["percentile"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (0.0 <= epss <= 1.0 and 0.0 <= percentile <= 1.0):
        return None
    return {"cve": str(row.get("cve", "")).upper(), "epss": epss, "percentile": percentile, "date": row.get("date")}


class EpssClient:
    def __init__(self, api_url: str, timeout: float = 20.0) -> None:
        self.api_url = api_url
        self.timeout = timeout

    def fetch(self, cve_ids: list[str]) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        for i in range(0, len(cve_ids), BATCH_SIZE):
            batch = cve_ids[i : i + BATCH_SIZE]
            resp = request_with_retry("GET", self.api_url, params={"cve": ",".join(batch)}, timeout=self.timeout)
            resp.raise_for_status()
            for row in resp.json().get("data", []):
                parsed = parse_epss_row(row)
                if parsed:
                    results[parsed["cve"]] = parsed
        return results
