from __future__ import annotations

from typing import Any

from app.models.plan import RegulatorySnapshot
from app.models.profile import HouseholdProfile, IPS


def tax_considerations(profile: HouseholdProfile, ips: IPS, snapshot: RegulatorySnapshot) -> list[str]:
    notes: list[str] = []
    regime = profile.tax_regime
    limit_80c = _num(snapshot.section_80c.value)
    nps_1b = _num(snapshot.section_80ccd_1b.value)
    nps_2 = snapshot.section_80ccd_2.value if isinstance(snapshot.section_80ccd_2.value, dict) else {}

    if regime == "unknown":
        notes.append(
            "Tax regime is unknown. No tax-saving amount is fabricated. "
            "Both old-regime and new-regime sketches are shown for education only."
        )
        notes.append(
            f"Old-regime educational sketch: Section 80C capacity in the snapshot is ₹{limit_80c:,.0f} "
            f"(source-backed snapshot; verify current applicability)."
        )
        notes.append(
            "New-regime educational sketch: do not assume 80C deductions apply. "
            "Only snapshot-verified new-regime benefits may be discussed."
        )
        return notes

    if regime == "new":
        notes.append(
            "New tax regime selected. Investments are not recommended solely to fill Section 80C. "
            "80C deductions are not applied automatically."
        )
        notes.append(
            "Employer NPS contributions may still be relevant if the snapshot confirms Section 80CCD(2) "
            f"applicability: {nps_2 or 'see snapshot'}."
        )
        notes.append(
            "Any NPS additional contribution under 80CCD(1B) is shown only if the snapshot lists it as "
            f"currently applicable (snapshot value ₹{nps_1b:,.0f}). Confirm on official sources."
        )
        return notes

    notes.append(
        f"Old tax regime selected. Remaining 80C capacity depends on existing eligible contributions. "
        f"Snapshot 80C ceiling: ₹{limit_80c:,.0f}."
    )
    notes.append(
        "Eligible items (EPF, ELSS, PPF, life-insurance premiums, principal repayment) are evaluated "
        "only when they already fit the plan — tax is never the sole reason to add a product."
    )
    notes.append(
        f"NPS 80CCD(1B) additional snapshot limit: ₹{nps_1b:,.0f}. Use only if cash-flow and IPS allow."
    )
    return notes


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
