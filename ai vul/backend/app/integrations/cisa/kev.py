"""CISA Known Exploited Vulnerabilities (KEV) catalog adapter."""

from __future__ import annotations

from typing import Any

from app.integrations.http import request_with_retry


class KevClient:
    def __init__(self, feed_url: str, timeout: float = 30.0) -> None:
        self.feed_url = feed_url
        self.timeout = timeout

    def fetch_catalog(self) -> dict[str, Any]:
        resp = request_with_retry("GET", self.feed_url, timeout=self.timeout, attempts=3)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or "vulnerabilities" not in data:
            raise ValueError("Unexpected KEV catalog format")
        return data


def normalize_kev_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Keep only documented KEV fields (the payload is untrusted third-party data)."""
    keys = (
        "cveID",
        "vendorProject",
        "product",
        "vulnerabilityName",
        "dateAdded",
        "shortDescription",
        "requiredAction",
        "dueDate",
        "knownRansomwareCampaignUse",
        "notes",
        "cwes",
    )
    out = {k: entry.get(k) for k in keys}
    for k, v in out.items():
        if isinstance(v, str):
            out[k] = v[:2000]
    return out
