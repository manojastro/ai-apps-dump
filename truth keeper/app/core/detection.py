"""Read the three systems, match them and detect conflicts (adapters -> matcher -> detector -> impact)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.adapters import BillingAdapter, CRMAdapter, MarketingAdapter
from app.core import detector, impact
from app.core.matcher import MatchResult, match
from app.core.models import Conflict
from app.tracing import get_tracer


@dataclass
class DetectionRun:
    conflicts: list[Conflict]
    match: MatchResult
    as_of: date


def detect_dir(data_dir: Path, strategy: str = "default", respect_review_flags: bool = True) -> DetectionRun:
    tracer = get_tracer()
    with tracer.start_as_current_span("detection.run") as span:
        span.set_attribute("tk.data_dir", str(data_dir))
        billing_adapter = BillingAdapter(data_dir)
        with tracer.start_as_current_span("adapters.read_all"):
            crm = CRMAdapter(data_dir).read_all()
            billing = billing_adapter.read_all()
            marketing = MarketingAdapter(data_dir).read_all()
            as_of = billing_adapter.read_as_of()
            flags = billing_adapter.read_open_flag_conflict_ids() if respect_review_flags else set()
        with tracer.start_as_current_span("matcher.match") as s:
            m = match(crm, billing, marketing, strategy=strategy)
            s.set_attribute("tk.unmatched_billing", len(m.unmatched.get("billing", [])))
            s.set_attribute("tk.unmatched_marketing", len(m.unmatched.get("marketing", [])))
        with tracer.start_as_current_span("detector.detect") as s:
            conflicts = impact.attach(detector.detect(m.customers, as_of, suppressed_ids=flags))
            s.set_attribute("tk.conflicts", len(conflicts))
        span.set_attribute("tk.conflicts", len(conflicts))
        return DetectionRun(conflicts=conflicts, match=m, as_of=as_of)
