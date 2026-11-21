"""Optional NVD CVE API 2.0 enrichment adapter (rate-limit aware)."""

from __future__ import annotations

import threading
import time
from typing import Any

from app.integrations.http import request_with_retry

_lock = threading.Lock()
_last_call = 0.0


def extract_nvd(cve_item: dict[str, Any]) -> dict[str, Any]:
    cve = cve_item["cve"]
    desc = next((d["value"] for d in cve.get("descriptions", []) if d.get("lang") == "en"), None)
    metrics = cve.get("metrics", {})
    cvss = None
    for key in ("cvssMetricV31", "cvssMetricV30"):
        entries = metrics.get(key) or []
        primary = next((m for m in entries if m.get("type") == "Primary"), entries[0] if entries else None)
        if primary:
            data = primary["cvssData"]
            cvss = {
                "version": data.get("version"),
                "base_score": data.get("baseScore"),
                "base_severity": data.get("baseSeverity"),
                "vector": data.get("vectorString"),
                "source": primary.get("source"),
            }
            break
    cwes = sorted(
        {d["value"] for w in cve.get("weaknesses", []) for d in w.get("description", []) if d.get("value", "").startswith("CWE-")}
    )
    ranges = []
    for conf in cve.get("configurations", []):
        for node in conf.get("nodes", []):
            for match in node.get("cpeMatch", []):
                if not match.get("vulnerable"):
                    continue
                parts = match["criteria"].split(":")
                ranges.append(
                    {
                        "criteria": match["criteria"],
                        "vendor": parts[3] if len(parts) > 3 else None,
                        "product": parts[4] if len(parts) > 4 else None,
                        "version": parts[5] if len(parts) > 5 else None,
                        "version_start_including": match.get("versionStartIncluding"),
                        "version_start_excluding": match.get("versionStartExcluding"),
                        "version_end_excluding": match.get("versionEndExcluding"),
                        "version_end_including": match.get("versionEndIncluding"),
                    }
                )
    return {
        "cve_id": cve["id"],
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
        "vuln_status": cve.get("vulnStatus"),
        "description": desc,
        "cvss": cvss,
        "cwes": cwes,
        "cpe_ranges": ranges,
        "references": [r["url"] for r in cve.get("references", [])][:8],
    }


class NvdClient:
    def __init__(self, api_url: str, api_key: str = "", timeout: float = 30.0) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        # Public limit: 5 req / 30 s without a key, 50 req / 30 s with one.
        self.min_interval = 0.7 if api_key else 6.5

    def fetch(self, cve_id: str) -> dict[str, Any] | None:
        global _last_call
        with _lock:
            wait = self.min_interval - (time.monotonic() - _last_call)
            if wait > 0:
                time.sleep(wait)
            _last_call = time.monotonic()
        headers = {"apiKey": self.api_key} if self.api_key else {}
        resp = request_with_retry(
            "GET", self.api_url, params={"cveId": cve_id}, headers=headers, timeout=self.timeout, backoff=6.0
        )
        resp.raise_for_status()
        items = resp.json().get("vulnerabilities", [])
        return extract_nvd(items[0]) if items else None
