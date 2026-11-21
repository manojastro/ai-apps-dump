"""Threat-intelligence service: CISA KEV, FIRST EPSS and NVD with caching and provenance.

Modes
-----
* ``offline`` (default): answers come from the bundled snapshot of *real* public data
  (``data/fixtures/threat_intel_snapshot.json``), labelled with its catalog version and
  fetch timestamp. CVEs outside the snapshot are reported as ``unavailable`` - never guessed.
* ``live``: answers come from the official APIs, cached in ``threat_intel_cache``. If a
  live call fails the service falls back to the snapshot and says so.

Three distinct outcomes are always kept apart: ``found``, ``not_found`` (the authoritative
source was checked and has no entry) and ``unavailable`` (we could not check).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.types import utcnow
from app.integrations.cisa.kev import KevClient, normalize_kev_entry
from app.integrations.epss.epss import EpssClient
from app.integrations.nvd.nvd import NvdClient
from app.models.vulnerability import ThreatIntelCache

log = logging.getLogger("aegis.threat_intel")


@dataclass
class IntelResult:
    source: str
    cve_id: str
    status: str  # found | not_found | unavailable
    data: dict[str, Any] | None
    origin: str  # live | cache | snapshot | none
    fetched_at: str | None
    reference: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@lru_cache
def load_snapshot(path: str | None = None) -> dict[str, Any]:
    p = Path(path or get_settings().threat_intel_snapshot_path)
    if not p.exists():
        log.warning("threat intel snapshot missing at %s", p)
        return {"nvd": {}, "epss": {}, "kev": {}, "kev_catalog": {}, "generated_at": None}
    return json.loads(p.read_text(encoding="utf-8"))


def _age_hours(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((utcnow() - dt).total_seconds() / 3600, 1)


class ThreatIntelService:
    def __init__(self, db: Session, mode: str | None = None) -> None:
        self.db = db
        self.settings = get_settings()
        self.mode = mode or self.settings.threat_intel_mode
        self.snapshot = load_snapshot()

    # ------------------------------------------------------------------ cache helpers
    def _cache_get(self, source: str, key: str) -> ThreatIntelCache | None:
        return self.db.scalar(select(ThreatIntelCache).where(ThreatIntelCache.source == source, ThreatIntelCache.key == key))

    def _cache_put(self, source: str, key: str, status: str, payload: dict[str, Any], error: str | None = None) -> None:
        row = self._cache_get(source, key)
        expires = utcnow() + timedelta(hours=self.settings.threat_intel_cache_hours)
        if row is None:
            row = ThreatIntelCache(source=source, key=key, origin="live")
            self.db.add(row)
        row.status, row.payload, row.error = status, payload, error
        row.fetched_at, row.expires_at, row.origin = utcnow(), expires, "live"

    @staticmethod
    def _fresh(row: ThreatIntelCache | None) -> bool:
        return row is not None and row.status != "error" and (row.expires_at is None or row.expires_at > utcnow())

    def _snapshot_checked(self, cve_id: str) -> bool:
        return cve_id in self.snapshot.get("nvd", {}) or cve_id in self.snapshot.get("epss", {})

    # ------------------------------------------------------------------ KEV
    def refresh_kev_catalog(self) -> dict[str, Any]:
        client = KevClient(self.settings.kev_feed_url)
        try:
            catalog = client.fetch_catalog()
        except Exception as exc:
            self._cache_put("kev_catalog", "catalog", "error", {}, error=str(exc)[:500])
            self.db.flush()
            raise
        self.db.execute(delete(ThreatIntelCache).where(ThreatIntelCache.source == "kev"))
        now, expires = utcnow(), utcnow() + timedelta(hours=self.settings.threat_intel_cache_hours)
        self.db.add_all(
            ThreatIntelCache(
                source="kev",
                key=str(v.get("cveID", "")).upper(),
                status="ok",
                payload=normalize_kev_entry(v),
                origin="live",
                fetched_at=now,
                expires_at=expires,
            )
            for v in catalog.get("vulnerabilities", [])
            if v.get("cveID")
        )
        meta = {
            "catalog_version": catalog.get("catalogVersion"),
            "date_released": catalog.get("dateReleased"),
            "count": catalog.get("count"),
        }
        self._cache_put("kev_catalog", "catalog", "ok", meta)
        self.db.flush()
        return meta

    def kev_status(self) -> dict[str, Any]:
        row = self._cache_get("kev_catalog", "catalog")
        snap = self.snapshot.get("kev_catalog", {})
        return {
            "mode": self.mode,
            "live": None
            if row is None
            else {
                "status": row.status,
                "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
                "error": row.error,
                **(row.payload or {}),
            },
            "snapshot": {**snap, "age_hours": _age_hours(snap.get("fetched_at"))},
        }

    def get_kev(self, cve_id: str) -> IntelResult:
        cve_id = cve_id.upper()
        notes: list[str] = []
        if self.mode == "live":
            catalog = self._cache_get("kev_catalog", "catalog")
            if not self._fresh(catalog):
                try:
                    self.refresh_kev_catalog()
                    catalog = self._cache_get("kev_catalog", "catalog")
                except Exception as exc:
                    notes.append(f"Live KEV refresh failed ({type(exc).__name__}); using snapshot")
            if self._fresh(catalog):
                assert catalog is not None
                ref = f"CISA KEV catalog {catalog.payload.get('catalog_version')}"
                row = self._cache_get("kev", cve_id)
                fetched = catalog.fetched_at.isoformat()
                if row:
                    return IntelResult("kev", cve_id, "found", row.payload, "cache", fetched, ref, notes)
                return IntelResult("kev", cve_id, "not_found", None, "cache", fetched, ref, notes)
        snap_meta = self.snapshot.get("kev_catalog", {})
        ref = f"CISA KEV catalog {snap_meta.get('catalog_version')} (offline snapshot)"
        if self._snapshot_checked(cve_id):
            entry = self.snapshot.get("kev", {}).get(cve_id)
            status = "found" if entry else "not_found"
            return IntelResult(
                "kev",
                cve_id,
                status,
                normalize_kev_entry(entry) if entry else None,
                "snapshot",
                snap_meta.get("fetched_at"),
                ref,
                notes,
            )
        notes.append("CVE not covered by offline snapshot; KEV status unknown")
        return IntelResult("kev", cve_id, "unavailable", None, "none", None, ref, notes)

    # ------------------------------------------------------------------ EPSS
    def get_epss_many(self, cve_ids: list[str]) -> dict[str, IntelResult]:
        cve_ids = sorted({c.upper() for c in cve_ids})
        out: dict[str, IntelResult] = {}
        notes: list[str] = []
        if self.mode == "live":
            stale = []
            for cve in cve_ids:
                row = self._cache_get("epss", cve)
                if self._fresh(row):
                    assert row is not None
                    status = "found" if row.status == "ok" else "not_found"
                    out[cve] = IntelResult(
                        "epss", cve, status, row.payload or None, "cache", row.fetched_at.isoformat(), "FIRST EPSS API"
                    )
                else:
                    stale.append(cve)
            if stale:
                try:
                    fetched = EpssClient(self.settings.epss_api_url).fetch(stale)
                    for cve in stale:
                        if cve in fetched:
                            self._cache_put("epss", cve, "ok", fetched[cve])
                            out[cve] = IntelResult(
                                "epss", cve, "found", fetched[cve], "live", utcnow().isoformat(), "FIRST EPSS API"
                            )
                        else:
                            self._cache_put("epss", cve, "not_found", {})
                            out[cve] = IntelResult(
                                "epss",
                                cve,
                                "not_found",
                                None,
                                "live",
                                utcnow().isoformat(),
                                "FIRST EPSS API",
                                ["No EPSS score published for this CVE"],
                            )
                    self.db.flush()
                except Exception as exc:
                    notes.append(f"Live EPSS lookup failed ({type(exc).__name__}); using snapshot")
        for cve in cve_ids:
            if cve in out:
                continue
            snap = self.snapshot.get("epss", {}).get(cve)
            if snap:
                out[cve] = IntelResult(
                    "epss",
                    cve,
                    "found",
                    snap,
                    "snapshot",
                    snap.get("fetched_at"),
                    f"FIRST EPSS ({snap.get('date')}, offline snapshot)",
                    list(notes),
                )
            else:
                out[cve] = IntelResult(
                    "epss",
                    cve,
                    "unavailable",
                    None,
                    "none",
                    None,
                    "FIRST EPSS",
                    [*notes, "EPSS not available offline for this CVE"],
                )
        return out

    def get_epss(self, cve_id: str) -> IntelResult:
        return self.get_epss_many([cve_id])[cve_id.upper()]

    # ------------------------------------------------------------------ NVD
    def get_nvd(self, cve_id: str, allow_live: bool = True) -> IntelResult:
        cve_id = cve_id.upper()
        notes: list[str] = []
        if self.mode == "live" and allow_live:
            row = self._cache_get("nvd", cve_id)
            if self._fresh(row):
                assert row is not None
                status = "found" if row.status == "ok" else "not_found"
                return IntelResult(
                    "nvd", cve_id, status, row.payload or None, "cache", row.fetched_at.isoformat(), "NVD CVE API 2.0"
                )
            try:
                key = self.settings.nvd_api_key.get_secret_value()
                rec = NvdClient(self.settings.nvd_api_url, key).fetch(cve_id)
                self._cache_put("nvd", cve_id, "ok" if rec else "not_found", rec or {})
                self.db.flush()
                return IntelResult(
                    "nvd", cve_id, "found" if rec else "not_found", rec, "live", utcnow().isoformat(), "NVD CVE API 2.0"
                )
            except Exception as exc:
                notes.append(f"Live NVD lookup failed ({type(exc).__name__}); using snapshot")
        snap = self.snapshot.get("nvd", {}).get(cve_id)
        if snap:
            return IntelResult(
                "nvd", cve_id, "found", snap, "snapshot", snap.get("fetched_at"), "NVD CVE API 2.0 (offline snapshot)", notes
            )
        return IntelResult(
            "nvd",
            cve_id,
            "unavailable",
            None,
            "none",
            None,
            "NVD CVE API 2.0",
            [*notes, "No authoritative NVD record available offline"],
        )

    def known_ranges(self) -> dict[str, list[dict[str, Any]]]:
        """CVE -> affected CPE ranges for every CVE we hold NVD data for (snapshot + cache)."""
        ranges = {cve: rec.get("cpe_ranges", []) for cve, rec in self.snapshot.get("nvd", {}).items()}
        for row in self.db.scalars(
            select(ThreatIntelCache).where(ThreatIntelCache.source == "nvd", ThreatIntelCache.status == "ok")
        ):
            ranges[row.key] = row.payload.get("cpe_ranges", [])
        return ranges
