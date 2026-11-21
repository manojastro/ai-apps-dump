"""Build the offline threat-intelligence snapshot used by the demo environment.

The snapshot contains *real* public data fetched from authoritative sources:

* NVD CVE API 2.0       -> description, CVSS v3.x, CWE, affected CPE version ranges
* FIRST EPSS API        -> exploitation probability + percentile
* CISA KEV catalog      -> known-exploited status (subset for the selected CVEs)

Every record keeps its source URL and fetch timestamp so the application can show
provenance and data freshness. Re-run this script to refresh the snapshot:

    python scripts/build_threat_intel_snapshot.py

Only the Python standard library is used so it can run before the backend venv exists.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CVES = [
    "CVE-2021-44228",
    "CVE-2022-22965",
    "CVE-2021-41773",
    "CVE-2024-6387",
    "CVE-2023-46604",
    "CVE-2023-22515",
    "CVE-2022-0847",
    "CVE-2021-4034",
    "CVE-2023-38545",
    "CVE-2022-42889",
    "CVE-2023-38831",
    "CVE-2025-0411",
    "CVE-2024-23897",
    "CVE-2023-4863",
    "CVE-2022-3602",
    "CVE-2023-48795",
    "CVE-2024-45490",
    "CVE-2024-27198",
    "CVE-2023-45853",
    "CVE-2024-3094",
]

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_URL = "https://api.first.org/data/v1/epss"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
OUT = Path(__file__).resolve().parents[1] / "data" / "fixtures" / "threat_intel_snapshot.json"
UA = {"User-Agent": "AegisRemediate-AI snapshot builder (research/demo)"}


def get_json(url: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed allowlisted hosts
        return json.loads(resp.read().decode("utf-8"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def extract_nvd(cve_item: dict) -> dict:
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
        {
            d["value"]
            for w in cve.get("weaknesses", [])
            for d in w.get("description", [])
            if d.get("value", "").startswith("CWE-")
        }
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
    refs = [r["url"] for r in cve.get("references", [])][:8]
    return {
        "cve_id": cve["id"],
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
        "vuln_status": cve.get("vulnStatus"),
        "description": desc,
        "cvss": cvss,
        "cwes": cwes,
        "cpe_ranges": ranges,
        "references": refs,
        "cisa_kev_fields_in_nvd": {
            "cisaExploitAdd": cve.get("cisaExploitAdd"),
            "cisaActionDue": cve.get("cisaActionDue"),
        },
    }


def main() -> int:
    snapshot: dict = {
        "generated_at": now(),
        "notice": (
            "Real public data cached for offline demonstration. NVD and CISA KEV content is "
            "US-government public domain; EPSS data courtesy of FIRST.org (https://www.first.org/epss)."
        ),
        "sources": {"nvd": NVD_URL, "epss": EPSS_URL, "kev": KEV_URL},
        "nvd": {},
        "epss": {},
        "kev": {},
        "kev_catalog": {},
        "errors": [],
    }

    print(f"Fetching CISA KEV catalog from {KEV_URL}")
    try:
        kev = get_json(KEV_URL)
        snapshot["kev_catalog"] = {
            "catalog_version": kev.get("catalogVersion"),
            "date_released": kev.get("dateReleased"),
            "count": kev.get("count"),
            "fetched_at": now(),
        }
        wanted = set(CVES)
        for v in kev.get("vulnerabilities", []):
            if v.get("cveID") in wanted:
                snapshot["kev"][v["cveID"]] = v
    except Exception as exc:  # pragma: no cover - network dependent
        snapshot["errors"].append(f"kev: {exc}")

    print(f"Fetching EPSS for {len(CVES)} CVEs")
    try:
        data = get_json(f"{EPSS_URL}?cve={','.join(CVES)}")
        for row in data.get("data", []):
            snapshot["epss"][row["cve"]] = {
                "epss": float(row["epss"]),
                "percentile": float(row["percentile"]),
                "date": row.get("date"),
                "fetched_at": now(),
            }
    except Exception as exc:  # pragma: no cover
        snapshot["errors"].append(f"epss: {exc}")

    for i, cve_id in enumerate(CVES):
        url = f"{NVD_URL}?{urllib.parse.urlencode({'cveId': cve_id})}"
        print(f"[{i + 1}/{len(CVES)}] NVD {cve_id}")
        for attempt in range(4):
            try:
                data = get_json(url)
                items = data.get("vulnerabilities", [])
                if items:
                    rec = extract_nvd(items[0])
                    rec["fetched_at"] = now()
                    rec["source_url"] = url
                    snapshot["nvd"][cve_id] = rec
                else:
                    snapshot["errors"].append(f"nvd: {cve_id} not found")
                break
            except Exception as exc:  # pragma: no cover
                print(f"   retry {attempt + 1}: {exc}")
                time.sleep(10 * (attempt + 1))
        else:
            snapshot["errors"].append(f"nvd: {cve_id} failed after retries")
        # NVD public rate limit is 5 requests / 30s without an API key.
        time.sleep(6.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(snapshot['nvd'])} NVD, {len(snapshot['epss'])} EPSS, {len(snapshot['kev'])} KEV)")
    if snapshot["errors"]:
        print("Errors:", *snapshot["errors"], sep="\n  ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
