from __future__ import annotations

import csv
import io
import re

from app.models.profile import Holding
from app.security.pii_redactor import redact_pii

CATEGORY_HINTS = (
    ("epf", "retirement", "epf"),
    ("vpf", "retirement", "vpf"),
    ("ppf", "retirement", "ppf"),
    ("nps", "retirement", "nps"),
    ("apy", "retirement", "apy"),
    ("scss", "retirement", "scss"),
    ("ssy", "retirement", "ssy"),
    ("elss", "equity", "elss"),
    ("index", "equity", "index_fund"),
    ("nifty", "equity", "index_fund"),
    ("sensex", "equity", "index_fund"),
    ("etf", "equity", "etf"),
    ("flexi", "equity", "flexi_cap"),
    ("large cap", "equity", "large_cap"),
    ("midcap", "equity", "midcap"),
    ("smallcap", "equity", "smallcap"),
    ("stock", "equity", "direct_equity"),
    ("share", "equity", "direct_equity"),
    ("gold", "gold", "gold"),
    ("silver", "gold", "silver"),
    ("sgb", "gold", "sgb"),
    ("reit", "real_assets", "reit"),
    ("invit", "real_assets", "invit"),
    ("property", "real_assets", "property"),
    ("fd", "cash_safety", "fd"),
    ("rd", "cash_safety", "rd"),
    ("liquid", "cash_safety", "liquid_fund"),
    ("overnight", "cash_safety", "overnight_fund"),
    ("arbitrage", "cash_safety", "arbitrage_fund"),
    ("savings", "cash_safety", "savings"),
    ("debt", "fixed_income", "debt_fund"),
    ("gilt", "fixed_income", "gilt"),
    ("bond", "fixed_income", "bond"),
    ("crypto", "alternatives", "vda"),
    ("bitcoin", "alternatives", "vda"),
    ("vda", "alternatives", "vda"),
    ("chit", "alternatives", "chit_fund"),
    ("pms", "alternatives", "pms"),
    ("aif", "alternatives", "aif"),
)

AMOUNT_RE = re.compile(
    r"(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(lakh|lac|cr|crore)?",
    re.IGNORECASE,
)


def _to_inr(amount: str, unit: str | None) -> float:
    value = float(amount.replace(",", ""))
    unit_l = (unit or "").lower()
    if unit_l in {"lakh", "lac"}:
        value *= 100_000
    elif unit_l in {"cr", "crore"}:
        value *= 10_000_000
    return value


def classify(name: str) -> tuple[str, str]:
    lowered = name.lower()
    for hint, category, vehicle in CATEGORY_HINTS:
        if hint in lowered:
            return category, vehicle
    return "unknown", "other"


def parse_holdings_text(raw: str) -> tuple[list[Holding], dict]:
    redacted = redact_pii(raw or "")
    text = redacted.text
    holdings: list[Holding] = []
    if not text.strip():
        return [], {"redacted": redacted.redacted, "kinds": redacted.kinds}

    sample = text.lstrip()
    if "," in sample.splitlines()[0] and any(
        h in sample.splitlines()[0].lower() for h in ("name", "value", "amount", "category")
    ):
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            name = (row.get("name") or row.get("instrument") or "").strip()
            if not name:
                continue
            amount_raw = row.get("current_value_inr") or row.get("value") or row.get("amount") or "0"
            amount = float(re.sub(r"[^0-9.]", "", amount_raw) or 0)
            category = (row.get("category") or "").strip() or classify(name)[0]
            vehicle = (row.get("vehicle_type") or "").strip() or classify(name)[1]
            locked = str(row.get("locked") or "").lower() in {"1", "true", "yes"}
            holdings.append(
                Holding(
                    name=name,
                    category=category,
                    vehicle_type=vehicle,
                    current_value_inr=amount,
                    locked=locked,
                    notes=redact_pii(row.get("notes") or "").text,
                )
            )
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = AMOUNT_RE.search(line)
            if not match:
                continue
            amount = _to_inr(match.group(1), match.group(2))
            name = (line[: match.start()] + line[match.end() :]).strip(" -:\t")
            if not name:
                name = line
            category, vehicle = classify(name)
            locked = any(k in name.lower() for k in ("epf", "ppf", "nps tier i", "nps tier 1", "ssy"))
            holdings.append(
                Holding(
                    name=name[:120],
                    category=category,
                    vehicle_type=vehicle,
                    current_value_inr=amount,
                    locked=locked,
                    notes="",
                )
            )

    # Duplicate detection by normalized name.
    seen: dict[str, Holding] = {}
    merged: list[Holding] = []
    for h in holdings:
        key = re.sub(r"\s+", " ", h.name.lower())
        if key in seen:
            seen[key].current_value_inr += h.current_value_inr
            seen[key].notes = (seen[key].notes + " duplicate_merged").strip()
        else:
            seen[key] = h
            merged.append(h)

    meta = {
        "redacted": redacted.redacted,
        "kinds": redacted.kinds,
        "redacted_text": redacted.text,
        "count": len(merged),
    }
    return merged, meta


def current_allocation(holdings: list[Holding]) -> dict[str, float]:
    total = sum(h.current_value_inr for h in holdings)
    buckets = {
        "cash": 0.0,
        "fixed_income": 0.0,
        "equity": 0.0,
        "gold": 0.0,
        "international": 0.0,
        "alternatives": 0.0,
        "real_assets": 0.0,
        "retirement_locked": 0.0,
        "unknown": 0.0,
    }
    mapping = {
        "cash_safety": "cash",
        "fixed_income": "fixed_income",
        "equity": "equity",
        "gold": "gold",
        "alternatives": "alternatives",
        "real_assets": "real_assets",
        "retirement": "retirement_locked",
        "unknown": "unknown",
    }
    if total <= 0:
        return buckets
    for h in holdings:
        bucket = mapping.get(h.category, "unknown")
        buckets[bucket] += 100.0 * h.current_value_inr / total
    return {k: round(v, 2) for k, v in buckets.items()}
