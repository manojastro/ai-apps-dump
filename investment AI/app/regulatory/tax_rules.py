from __future__ import annotations

from datetime import datetime

from app.models.facts import SourcedValue

# Mock-mode educational placeholders. Live mode must overwrite from official pages.
# Values are labelled mock and must never be presented as live law.


def mock_tax_fields(fetched_at: datetime) -> dict[str, SourcedValue]:
    common = dict(
        source_url="https://incometaxindia.gov.in/",
        source_tier=1,
        fetched_at=fetched_at,
        as_of="mock-fixture",
        confidence="medium",
        verification="verified",
        mock=True,
        notes="MOCK FIXTURE. Confirm on the Income Tax Department site before any real-world use.",
    )
    return {
        "assessment_year": SourcedValue(value="AY 2027-28 / FY 2026-27", unit="", **common),
        "section_80c": SourcedValue(value=150000, unit="INR", **common),
        "section_80ccd_1b": SourcedValue(value=50000, unit="INR", **common),
        "section_80ccd_2": SourcedValue(
            value={"employer_nps": "snapshot-backed; confirm current percentage cap"},
            unit="",
            **common,
        ),
        "vda_tax": SourcedValue(
            value={"treatment": "VDA tax treatment must be read from the current official source"},
            unit="",
            **common,
        ),
        "new_regime_slabs": SourcedValue(
            value=[
                {"upto": 400000, "rate": 0},
                {"upto": 800000, "rate": 5},
                {"upto": 1200000, "rate": 10},
                {"upto": 1600000, "rate": 15},
                {"upto": 2000000, "rate": 20},
                {"upto": 2400000, "rate": 25},
                {"upto": None, "rate": 30},
            ],
            unit="INR",
            **common,
        ),
        "old_regime_note": SourcedValue(
            value="Old-regime slabs and age-based exemption are snapshot-backed; not applied unless tax_regime=old.",
            unit="",
            **common,
        ),
        "standard_deduction_new": SourcedValue(value=75000, unit="INR", **common),
        "rebate_87a_new": SourcedValue(value=60000, unit="INR", **common),
    }
