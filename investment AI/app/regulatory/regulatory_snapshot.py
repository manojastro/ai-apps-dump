from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.plan import RegulatorySnapshot
from app.regulatory.lrs_rules import mock_lrs
from app.regulatory.nps_rules import mock_nps
from app.regulatory.source_registry import registry_records
from app.regulatory.tax_rules import mock_tax_fields


def build_mock_snapshot(*, conflict: bool = False) -> RegulatorySnapshot:
    now = datetime.now(timezone.utc)
    tax = mock_tax_fields(now)
    sources = registry_records(mock=True, fetched_at=now, as_of="mock-fixture", verification="verified")
    conflicts: list[str] = []
    if conflict:
        conflicts.append(
            "CONFLICTING_SOURCE: two mock 80C ceilings differ. Neither value is silently selected."
        )
        tax["section_80c"] = tax["section_80c"].model_copy(
            update={"verification": "conflicting", "notes": "Conflicting mock values; not used for a single pick."}
        )
    return RegulatorySnapshot(
        snapshot_id=f"reg-{uuid4().hex[:12]}",
        generated_at=now,
        assessment_year=tax["assessment_year"],
        tax_regimes={
            "new": tax["new_regime_slabs"].model_dump(),
            "old": tax["old_regime_note"].model_dump(),
            "standard_deduction_new": tax["standard_deduction_new"].model_dump(),
            "rebate_87a_new": tax["rebate_87a_new"].model_dump(),
        },
        section_80c=tax["section_80c"],
        section_80ccd_1b=tax["section_80ccd_1b"],
        section_80ccd_2=tax["section_80ccd_2"],
        vda_tax=tax["vda_tax"],
        lrs=mock_lrs(now),
        nps=mock_nps(now),
        market_data_restrictions={
            "no_telegram_tips": True,
            "authoritative_only": True,
            "note": "Secondary sources cannot override authoritative sources.",
        },
        sources=sources,
        degraded=True,
        data_mode="mock",
        conflicts=conflicts,
    )
