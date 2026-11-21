"""Build one immutable, versioned snapshot of a spread. Excel and PDF are rendered ONLY from it.

All decimals are strings. Every figure carries its observation ID and source reference.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.config import METRICS_VERSION, RULESET_VERSION, TAXONOMY_VERSION
from spreadlens.models import (
    AnalystAdjustment,
    CalculationResult,
    Company,
    DocumentVersion,
    MappingProposal,
    Observation,
    ReportingEntity,
    ReviewDecision,
    Spread,
    User,
    ValidationException,
    WorkflowRun,
)
from spreadlens.numeric.decimal_utils import dstr, quantize
from spreadlens.numeric.scale import SCALE_FACTORS
from spreadlens.services.spread import source_ref
from spreadlens.taxonomy.loader import load_taxonomy

STATEMENTS = ("balance_sheet", "income_statement", "cash_flow")
DISCLAIMER = ("Prepared to support analyst review. Passing arithmetic checks does not prove that the figures are correct, "
              "complete or compliant with any accounting framework. This pack is not a lending or investment decision.")


def display(o: Observation | None, display_scale: str) -> str | None:
    if o is None or o.current_value is None or o.current_state not in ("value", "zero"):
        return None
    if o.unit_type != "monetary":
        return dstr(o.current_value)
    return format(quantize(o.current_value / SCALE_FACTORS[display_scale], 2), "f")


def build_snapshot(db: Session, spread: Spread, created_by: str) -> dict:
    tax = load_taxonomy()
    company = db.get(Company, spread.company_id)
    entity = db.get(ReportingEntity, spread.entity_id)
    version = spread.current_version_no
    obs = list(db.scalars(select(Observation).where(Observation.spread_id == spread.id)))
    obs_by_id = {o.id: o for o in obs}
    annual = [o for o in obs if o.duration in ("annual", "point_in_time")]
    periods = sorted({o.period_end for o in annual}, reverse=True)
    per = [p.isoformat() for p in periods]
    ds = spread.display_scale

    statements: dict[str, dict] = {}
    for st in STATEMENTS:
        lines = []
        for item in tax.for_statement(st):
            cells = {}
            for p in periods:
                o = next((x for x in annual if x.canonical_code == item.code and x.period_end == p and x.is_preferred), None)
                if o is None:
                    continue
                cells[p.isoformat()] = {"value": display(o, ds), "state": o.current_state, "observation_id": o.id,
                                        "origin": "adjusted" if o.review_status == "corrected" or o.origin == "adjusted" else o.origin,
                                        "version_kind": o.version_kind, "source": source_ref(o), "label": o.original_label,
                                        "review_status": o.review_status, "raw_text": o.raw_text}
            if cells:
                lines.append({"code": item.code, "label": item.label, "unit": item.unit, "is_total": item.total, "cells": cells})
        # derived lines (kept distinct from reported figures)
        if st == "balance_sheet" and not any(line["code"] == "bs.total_liabilities" for line in lines):
            cells = {}
            for p in per:
                parts = [line["cells"].get(p) for line in lines if line["code"] in ("bs.total_current_liabilities", "bs.total_non_current_liabilities")]
                if len(parts) == 2 and all(c and c["value"] is not None for c in parts):
                    cells[p] = {"value": format(Decimal(parts[0]["value"]) + Decimal(parts[1]["value"]), "f"), "state": "value",
                                "origin": "derived", "observation_id": None, "source": "derived: total current + total non-current liabilities",
                                "inputs": [parts[0]["observation_id"], parts[1]["observation_id"]], "version_kind": "derived"}
            if cells:
                lines.append({"code": "bs.total_liabilities", "label": "Total liabilities (derived)", "unit": "monetary",
                              "is_total": True, "cells": cells, "derived": True})
                lines.sort(key=lambda x: tax.get(x["code"]).order if tax.get(x["code"]) else 9999)  # type: ignore[union-attr]
        unmapped = []
        for o in annual:
            if o.statement_type == st and o.canonical_code is None and o.current_state in ("value", "zero", "unreadable", "dash_ambiguous"):
                unmapped.append({"label": o.original_label, "period_end": o.period_end.isoformat(), "value": display(o, ds),
                                 "state": o.current_state, "observation_id": o.id, "source": source_ref(o)})
        statements[st] = {"available": any(o.statement_type == st for o in obs), "lines": lines, "unmapped_rows": unmapped}

    calcs = list(db.scalars(select(CalculationResult).where(CalculationResult.spread_id == spread.id,
                                                            CalculationResult.spread_version_no == version)))
    validations = [{"id": c.id, "rule_id": c.rule_id, "rule_version": c.rule_version, "title": c.title, "statement_type": c.statement_type,
                    "period_end": c.period_end.isoformat() if c.period_end else None, "expression": c.expression,
                    "expected": dstr(c.expected), "observed": dstr(c.observed), "difference": dstr(c.difference),
                    "tolerance": dstr(c.tolerance), "tolerance_basis": c.tolerance_basis, "severity": c.severity, "status": c.status,
                    "explanation": c.explanation, "inputs": c.input_observation_ids, "source_refs": c.source_refs}
                   for c in calcs if c.kind == "validation"]
    metrics = [{"id": c.id, "metric_id": c.rule_id, "version": c.rule_version, "title": c.title,
                "period_end": c.period_end.isoformat() if c.period_end else None, "formula": c.expression,
                "value": dstr(c.value), "display_value": _metric_display(c, ds), "unit": c.unit, "status": c.status,
                "explanation": c.explanation, "limitations": c.limitations, "inputs": c.input_observation_ids}
               for c in calcs if c.kind == "metric"]
    excs = list(db.scalars(select(ValidationException).where(ValidationException.spread_id == spread.id)))
    dv_ids = sorted({o.document_version_id for o in obs})
    excs += list(db.scalars(select(ValidationException).where(ValidationException.document_version_id.in_(dv_ids),
                                                              ValidationException.spread_id.is_(None))))
    exceptions = [{"id": e.id, "category": e.category, "severity": e.severity, "title": e.title, "detail": e.detail,
                   "status": e.status, "resolution_note": e.resolution_note, "agent_explanation": e.agent_explanation,
                   "observation_ids": e.observation_ids} for e in sorted(excs, key=lambda e: ({"critical": 0, "warning": 1}.get(e.severity, 2), e.title))
                  if e.status != "superseded"]
    users = {u.id: u.display_name for u in db.scalars(select(User))}
    adjustments = [{"id": a.id, "action": a.action, "field": a.field, "before": a.before, "after": a.after, "reason": a.reason,
                    "user": users.get(a.user_id, a.user_id), "at": a.created_at.isoformat(), "observation_id": a.observation_id,
                    "label": obs_by_id[a.observation_id].original_label if a.observation_id in obs_by_id else None,
                    "version_before": a.spread_version_before, "version_after": a.spread_version_after}
                   for a in db.scalars(select(AnalystAdjustment).where(AnalystAdjustment.spread_id == spread.id).order_by(AnalystAdjustment.created_at))]
    decisions = [{"decision": d.decision, "user": users.get(d.user_id), "role": d.role, "version": d.spread_version_no,
                  "comment": d.comment, "stale": d.is_stale, "at": d.created_at.isoformat()}
                 for d in db.scalars(select(ReviewDecision).where(ReviewDecision.spread_id == spread.id).order_by(ReviewDecision.created_at))]
    approval = next((d for d in reversed(decisions) if d["decision"] == "approve" and d["version"] == version and not d["stale"]), None)
    docs = []
    for dv in db.scalars(select(DocumentVersion).where(DocumentVersion.id.in_(dv_ids))):
        run = db.scalar(select(WorkflowRun).where(WorkflowRun.document_version_id == dv.id).order_by(WorkflowRun.created_at.desc()))
        docs.append({"document_version_id": dv.id, "filename": dv.filename, "sha256": dv.sha256, "version_no": dv.version_no,
                     "kind": dv.file_kind, "pages": dv.page_count, "agent_mode": run.agent_mode if run else None})
    mapping_stats = {"rows": 0, "mapped": 0}
    for p in db.scalars(select(MappingProposal).where(MappingProposal.row_id.in_({o.row_id for o in obs}), MappingProposal.is_current.is_(True))):
        mapping_stats["rows"] += 1
        mapping_stats["mapped"] += bool(p.decided_code or p.proposed_code) and p.status != "rejected"
    sources = [{"observation_id": o.id, "label": o.original_label, "code": o.canonical_code, "period_end": o.period_end.isoformat(),
                "raw_text": o.raw_text, "state": o.current_state, "value_units": dstr(o.current_value), "scale": o.original_scale,
                "document": next((d["filename"] for d in docs if d["document_version_id"] == o.document_version_id), None),
                "source": source_ref(o), "method": o.extraction_method, "preferred": o.is_preferred, "version_kind": o.version_kind,
                "transformations": o.transformations}
               for o in sorted(annual, key=lambda o: (o.statement_type, o.period_end, o.original_label))]
    return {
        "schema": "spreadlens.snapshot.v1",
        "company": {"id": company.id, "name": company.name} if company else None,
        "entity": {"id": entity.id, "name": entity.name, "scope": entity.scope} if entity else None,
        "spread_id": spread.id, "spread_version": version, "currency": spread.currency, "display_scale": ds,
        "periods": per, "statements": statements, "validations": validations, "metrics": metrics,
        "exceptions": exceptions, "adjustments": adjustments, "decisions": decisions, "approval": approval,
        "review_status": "approved" if approval else "unreviewed_draft", "documents": docs, "sources": sources,
        "mapping": mapping_stats,
        "versions": {"taxonomy": TAXONOMY_VERSION, "ruleset": RULESET_VERSION, "metrics": METRICS_VERSION},
        "disclaimer": DISCLAIMER, "created_by": users.get(created_by, created_by),
        "comparability": _limitations(spread, obs, statements),
    }


def _metric_display(c: CalculationResult, ds: str) -> str | None:
    if c.value is None:
        return None
    if c.unit == "percent":
        return f"{quantize(c.value * 100, 1)}%"
    if c.unit == "monetary":
        return format(quantize(c.value / SCALE_FACTORS[ds], 2), "f")
    return format(quantize(c.value, 2), "f")


def _limitations(spread: Spread, obs: list[Observation], statements: dict) -> list[str]:
    out = [f"All figures are {spread.scope} and in {spread.currency}; other scopes and currencies are kept in separate spreads. "
           "Cross-currency comparison is not available (no currency conversion)."]
    if any(o.version_kind == "restated" for o in obs):
        out.append("Some comparatives were restated in a later document; the restated value is used and the original is retained.")
    if any(o.duration not in ("annual", "point_in_time") for o in obs):
        out.append("Non-annual figures were excluded from annual comparisons.")
    for st, d in statements.items():
        if not d["available"]:
            out.append(f"No {st.replace('_', ' ')} was provided; dependent checks and ratios are reported as insufficient data.")
    if any(o.canonical_code == "is.cost_of_sales" and "material" in o.original_label.lower() for o in obs):
        out.append("'Cost of sales' is the reported cost of materials consumed; it may exclude inventory changes and other direct costs.")
    out.append("EBITDA and debt service coverage are not computed: no universal definition / incomplete debt service information.")
    return out
