from __future__ import annotations

from datetime import datetime

from app.models.facts import SourcedValue


def mock_lrs(fetched_at: datetime) -> SourcedValue:
    return SourcedValue(
        value={
            "framework": "Liberalised Remittance Scheme",
            "note": "Limits, TCS and tax rules MUST come from the current RegulatorySnapshot.",
        },
        unit="",
        source_url="https://www.rbi.org.in/",
        source_tier=1,
        fetched_at=fetched_at,
        as_of="mock-fixture",
        confidence="medium",
        verification="verified",
        mock=True,
        notes="MOCK. Do not treat this object as the live LRS limit.",
    )
