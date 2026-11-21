from __future__ import annotations

from datetime import datetime

from app.models.facts import SourcedValue


def mock_nps(fetched_at: datetime) -> dict:
    src = SourcedValue(
        value="Retrieve current PFRDA/NPS Trust allocation rules at runtime. Not hardcoded as permanent law.",
        unit="",
        source_url="https://www.npstrust.org.in/",
        source_tier=1,
        fetched_at=fetched_at,
        as_of="mock-fixture",
        confidence="medium",
        verification="verified",
        mock=True,
        notes="MOCK. Equity ceilings and auto-choice glide paths change; always refresh the snapshot.",
    )
    return {
        "tier1": src.model_dump(),
        "tier2": SourcedValue(
            value="NPS Tier II is more liquid than Tier I; tax treatment is snapshot-backed.",
            source_url="https://www.pfrda.org.in/",
            source_tier=1,
            fetched_at=fetched_at,
            as_of="mock-fixture",
            confidence="medium",
            verification="verified",
            mock=True,
        ).model_dump(),
        "equity_cap_note": "Never hardcode current NPS allocation rules permanently.",
    }
