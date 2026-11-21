"""Spread recalculation, versioning, exception sync and invalidation.

How a correction triggers recalculation:
  correction -> analyst_adjustments row + observation.current_value -> recompute(spread)
  -> build facts from current values -> run every rule and metric again (deterministic)
  -> content hash differs -> new immutable spread version with its own calculation results
  -> exceptions re-synced (auto-resolved, reopened or created) -> review decisions on older
     versions marked stale -> exports of older versions are reported as stale.
"""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from spreadlens.config import METRICS_VERSION, RULESET_VERSION
from spreadlens.metrics.ratios import compute_metrics
from spreadlens.models import (
    CalculationResult,
    DocumentVersion,
    ExtractedRow,
    MappingProposal,
    Observation,
    ReviewDecision,
    Spread,
    SpreadVersion,
    Statement,
    ValidationException,
    utcnow,
)
from spreadlens.rules.engine import run_rules
from spreadlens.rules.types import Fact, SpreadFacts, SubtotalGroup
from spreadlens.services.artifacts import content_hash
from spreadlens.services.audit import audit, metric
from spreadlens.services.normalize import presented_sign

MANAGED_CATEGORIES = {"validation", "unreadable_cell", "dash_ambiguous", "low_confidence", "unmapped_row",
                      "ambiguous_mapping", "missing_statement", "non_annual_period", "unresolved_figure"}
ANNUAL = ("annual", "point_in_time")


def source_ref(o: Observation) -> str:
    if o.sheet:
        return f"{o.sheet}!{o.cell_ref}"
    return f"p{o.page}" + (f" [{','.join(str(round(x)) for x in o.bbox)}]" if o.bbox else "")


def choose_preferred(db: Session, obs: list[Observation]) -> None:
    """Pick one value per (code, period, duration): analyst adjustment > restated > latest document."""
    stmt_latest: dict[str, date] = {}
    for st_id, mx in db.execute(select(Observation.statement_id, func.max(Observation.period_end))
                                .where(Observation.id.in_([o.id for o in obs])).group_by(Observation.statement_id)):
        stmt_latest[st_id] = mx
    dv_created = {dv.id: dv.created_at for dv in db.scalars(select(DocumentVersion).where(DocumentVersion.id.in_({o.document_version_id for o in obs})))}
    groups: dict[tuple, list[Observation]] = {}
    for o in obs:
        if o.canonical_code:
            groups.setdefault((o.canonical_code, o.period_end, o.duration), []).append(o)
        else:
            o.is_preferred = False
    for members in groups.values():
        conf_rank = {"high": 3, "medium": 2, "low": 1}
        members.sort(key=lambda o: (o.origin == "adjusted", o.version_kind == "restated",
                                    stmt_latest.get(o.statement_id) or date.min, dv_created.get(o.document_version_id),
                                    conf_rank.get((o.confidence or {}).get("mapping") or "", 0), o.id), reverse=True)
        for i, o in enumerate(members):
            o.is_preferred = i == 0


def _fact(o: Observation, value_sign: int = 1) -> Fact:
    v = o.current_value if o.current_state in ("value", "zero") else None
    return Fact(id=o.id, code=o.canonical_code, period_end=o.period_end,
                value=None if v is None else v * value_sign, state=o.current_state,
                decimals=o.source_decimals, scale=o.original_scale if o.unit_type == "monetary" else None,
                statement_type=o.statement_type, label=o.original_label, document_version_id=o.document_version_id,
                version_kind=o.version_kind, restated_flag=o.version_kind == "restated", source_ref=source_ref(o))


def build_facts(db: Session, spread: Spread, obs: list[Observation]) -> SpreadFacts:
    annual = [o for o in obs if o.duration in ANNUAL and o.unit_type == "monetary"]
    preferred = {(o.canonical_code, o.period_end): _fact(o) for o in annual if o.canonical_code and o.is_preferred}
    all_facts = [_fact(o) for o in annual if o.canonical_code and o.origin != "adjusted"]
    groups: list[SubtotalGroup] = []
    by_row_period: dict[tuple[str, date], Observation] = {(o.row_id, o.period_end): o for o in annual}
    rows = {r.id: r for r in db.scalars(select(ExtractedRow).where(ExtractedRow.id.in_({o.row_id for o in annual})))}
    children: dict[str, list[ExtractedRow]] = {}
    for r in rows.values():
        if r.parent_total_row_id:
            children.setdefault(r.parent_total_row_id, []).append(r)
    periods = sorted({o.period_end for o in annual})
    for parent_id, kids in children.items():
        parent = rows.get(parent_id)
        if parent is None:
            continue
        for p in periods:
            t = by_row_period.get((parent_id, p))
            if t is None:
                continue
            kid_obs = []
            for k in sorted(kids, key=lambda r: r.row_index):
                ko = by_row_period.get((k.id, p))
                if ko is not None:
                    kid_obs.append(ko)
                else:
                    # printed component without a figure for this period: treated as missing, not zero
                    kid_obs.append(None)
            if not kid_obs:
                continue
            facts = []
            for k, ko in zip(sorted(kids, key=lambda r: r.row_index), kid_obs):
                if ko is None:
                    facts.append(Fact(id=f"missing:{k.id}:{p}", code=None, period_end=p, value=None, state="missing",
                                      decimals=None, scale=None, statement_type=t.statement_type, label=k.label))
                else:
                    facts.append(_fact(ko, presented_sign(ko)))
            groups.append(SubtotalGroup(t.statement_type, p, _fact(t, presented_sign(t)), tuple(facts)))
    present = {o.canonical_code for o in obs if o.canonical_code}
    return SpreadFacts(preferred=preferred, all_facts=all_facts, groups=groups, periods=periods, present_codes=present)  # type: ignore[arg-type]


def _hash_state(obs: list[Observation], mappings: list[tuple]) -> str:
    return content_hash({
        "ruleset": RULESET_VERSION, "metrics": METRICS_VERSION,
        "obs": sorted((o.id, o.canonical_code, None if o.current_value is None else format(o.current_value.normalize(), "f"),
                       o.current_state, o.is_preferred, o.review_status) for o in obs),
        "mappings": sorted(mappings),
    })


def _fp(key: str) -> str:
    return key if len(key) <= 64 else hashlib.sha256(key.encode()).hexdigest()


def _rule_fp(r: CalculationResult, obs_by_id: dict[str, Observation]) -> str:
    stmt = ""
    if r.rule_id == "R04" and r.input_observation_ids:
        o = obs_by_id.get(r.input_observation_ids[-1])
        stmt = o.statement_id if o else ""
    return f"rule:{r.rule_id}:{r.title}:{r.period_end}:{stmt}"


def _exc(db: Session, spread: Spread, version: int, existing: dict[str, ValidationException], seen: set[str], fp: str,
         category: str, severity: str, title: str, detail: str, **kw) -> None:
    fp = _fp(fp)
    seen.add(fp)
    e = existing.get(fp)
    if e is None:
        db.add(ValidationException(workspace_id=spread.workspace_id, company_id=spread.company_id, spread_id=spread.id,
                                   fingerprint=fp, category=category, severity=severity, title=title[:300], detail=detail,
                                   first_seen_version=version, last_seen_version=version, status="open", **kw))
        return
    changed = e.detail != detail
    e.title, e.severity, e.last_seen_version = title[:300], severity, version
    for k, v in kw.items():
        setattr(e, k, v)
    if e.status in ("resolved", "superseded"):
        e.status, e.resolution_note = "open", f"Raised again in version {version}."
    elif e.status == "explained" and changed:
        e.status = "open"
        e.resolution_note = f"Reopened in version {version}: the inputs changed after the explanation was accepted."
    e.detail = detail


def sync_exceptions(db: Session, spread: Spread, version: int, obs: list[Observation], results: list[CalculationResult]) -> None:
    existing = {e.fingerprint: e for e in db.scalars(select(ValidationException).where(ValidationException.spread_id == spread.id))
                if e.category in MANAGED_CATEGORIES}
    seen: set[str] = set()
    obs_by_id = {o.id: o for o in obs}
    for r in results:
        if r.kind != "validation":
            continue
        rfp = _rule_fp(r, obs_by_id)
        if r.status == "fail":
            _exc(db, spread, version, existing, seen, rfp, "validation", r.severity,
                 f"{r.rule_id} failed: {r.title} ({r.period_end})", r.explanation, calculation_result_id=r.id,
                 observation_ids=r.input_observation_ids,
                 suggested_action="Inspect the source cells; correct an extraction error or accept with an explanation.")
        elif r.status == "requires_review":
            _exc(db, spread, version, existing, seen, rfp, "validation",
                 "warning" if r.severity != "info" else "info", f"{r.rule_id} needs review: {r.title} ({r.period_end})",
                 r.explanation, calculation_result_id=r.id, observation_ids=r.input_observation_ids)
        elif r.status == "insufficient_data" and r.severity == "critical" and r.input_observation_ids:
            _exc(db, spread, version, existing, seen, rfp, "validation", "warning",
                 f"{r.rule_id} could not run: {r.title} ({r.period_end})", r.explanation, calculation_result_id=r.id,
                 observation_ids=r.input_observation_ids)
    for o in obs:
        if o.review_status in ("corrected", "accepted"):
            continue
        if o.current_state == "unreadable":
            _exc(db, spread, version, existing, seen, f"cell:{o.cell_id}", "unreadable_cell", "warning",
                 f"Unreadable figure: '{o.original_label}' ({o.period_end})",
                 f"Source text '{o.raw_text}' is not a reliable number. It stays unresolved until an analyst enters the value.",
                 observation_ids=[o.id], row_ids=[o.row_id])
        elif o.current_state == "dash_ambiguous":
            _exc(db, spread, version, existing, seen, f"cell:{o.cell_id}", "dash_ambiguous", "warning",
                 f"Dash of unknown meaning: '{o.original_label}' ({o.period_end})",
                 "The document does not state whether a dash means nil. Confirm zero or enter the figure.",
                 observation_ids=[o.id], row_ids=[o.row_id])
        elif o.review_status == "unresolved":
            _exc(db, spread, version, existing, seen, f"unresolved:{o.id}", "unresolved_figure", "warning",
                 f"Marked unresolved: '{o.original_label}' ({o.period_end})", "An analyst marked this figure unresolved.",
                 observation_ids=[o.id], row_ids=[o.row_id])
        ocr = (o.confidence or {}).get("ocr")
        if ocr is not None and ocr < 0.8 and o.current_state in ("value", "zero"):
            _exc(db, spread, version, existing, seen, f"ocr:{o.cell_id}", "low_confidence", "info",
                 f"Low OCR confidence ({ocr:.2f}): '{o.original_label}' ({o.period_end})",
                 "Compare the figure with the scanned page before relying on it.", observation_ids=[o.id], row_ids=[o.row_id])
        if o.duration not in ANNUAL:
            _exc(db, spread, version, existing, seen, f"period:{o.statement_id}:{o.duration}", "non_annual_period", "info",
                 f"Non-annual period excluded ({o.duration})",
                 "Quarterly / year-to-date figures are stored but excluded from annual comparisons.", observation_ids=[o.id])
    # mapping exceptions (per row)
    row_ids = {o.row_id for o in obs}
    props = {p.row_id: p for p in db.scalars(select(MappingProposal).where(MappingProposal.row_id.in_(row_ids), MappingProposal.is_current.is_(True)))}
    unmapped_by_stmt: dict[str, list[str]] = {}
    for o in obs:
        p = props.get(o.row_id)
        if p is None or p.status in ("accepted", "changed"):
            continue
        if o.canonical_code is None and o.current_state in ("value", "zero"):
            unmapped_by_stmt.setdefault(o.statement_id, []).append(o.original_label)
        elif p.confidence == "low" and p.status == "proposed":
            _exc(db, spread, version, existing, seen, f"map:{o.row_id}", "ambiguous_mapping", "warning",
                 f"Ambiguous mapping: '{o.original_label}' -> {p.proposed_code}", p.rationale,
                 row_ids=[o.row_id], observation_ids=[o.id])
    for st_id, labels in unmapped_by_stmt.items():
        uniq = sorted(set(labels))
        st = db.get(Statement, st_id)
        _exc(db, spread, version, existing, seen, f"unmapped:{st_id}", "unmapped_row", "info",
             f"{len(uniq)} rows not mapped in {st.title if st else 'statement'}",
             "These rows have no canonical item. They remain visible in the grid and still take part in subtotal checks: "
             + "; ".join(uniq[:12]) + ("..." if len(uniq) > 12 else ""))
    present_types = {o.statement_type for o in obs}
    for t in ("balance_sheet", "income_statement", "cash_flow"):
        if t not in present_types:
            _exc(db, spread, version, existing, seen, f"missing:{t}", "missing_statement", "warning",
                 f"Missing statement: {t.replace('_', ' ')}",
                 "No uploaded document provides this statement for this entity and scope. Checks that need it report insufficient data.")
    for fp, e in existing.items():
        if fp not in seen and e.status in ("open", "explained"):
            e.status = "resolved"
            e.resolution_note = f"No longer raised after recalculation (version {version})."
            e.resolved_at = utcnow()


def recompute(db: Session, spread: Spread, reason: str, user_id: str | None = None) -> int:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": spread.id})
    db.refresh(spread)
    obs = list(db.scalars(select(Observation).where(Observation.spread_id == spread.id)))
    choose_preferred(db, obs)
    db.flush()
    mappings = [(p.row_id, p.status, p.decided_code or p.proposed_code or "")
                for p in db.scalars(select(MappingProposal).where(MappingProposal.row_id.in_({o.row_id for o in obs}),
                                                                  MappingProposal.is_current.is_(True)))]
    h = _hash_state(obs, mappings)
    last = db.scalar(select(SpreadVersion).where(SpreadVersion.spread_id == spread.id).order_by(SpreadVersion.version_no.desc()))
    if last is not None and last.content_hash == h:
        return last.version_no
    version = (last.version_no if last else 0) + 1
    sf = build_facts(db, spread, obs)
    rule_results = run_rules(sf)
    metric_results = compute_metrics(sf)
    stored: list[CalculationResult] = []
    for r in rule_results:
        cr = CalculationResult(workspace_id=spread.workspace_id, spread_id=spread.id, spread_version_no=version, kind="validation",
                               rule_id=r.rule_id, rule_version=r.rule_version, title=r.title, statement_type=r.statement_type,
                               period_end=r.period_end, input_observation_ids=[i for i in r.input_ids if not i.startswith("missing:")],
                               expression=r.expression, expected=r.expected, observed=r.observed, difference=r.difference,
                               tolerance=r.tolerance, tolerance_basis=r.tolerance_basis, severity=r.severity, status=r.status,
                               explanation=r.explanation, source_refs=r.source_refs)
        db.add(cr)
        stored.append(cr)
    for m in metric_results:
        cr = CalculationResult(workspace_id=spread.workspace_id, spread_id=spread.id, spread_version_no=version, kind="metric",
                               rule_id=m.metric_id, rule_version=m.version, title=m.title, statement_type=None,
                               period_end=m.period_end, input_observation_ids=m.input_ids, expression=m.formula,
                               value=m.value, unit=m.unit, status=m.status, explanation=m.explanation, limitations=m.limitations,
                               severity="info")
        db.add(cr)
        stored.append(cr)
    db.flush()
    stmt_hashes = {}
    for t in ("balance_sheet", "income_statement", "cash_flow"):
        sub = [o for o in obs if o.statement_type == t]
        if sub:
            stmt_hashes[t] = _hash_state(sub, [])[:16]
    db.add(SpreadVersion(workspace_id=spread.workspace_id, spread_id=spread.id, version_no=version, content_hash=h,
                         reason=reason[:200], statement_hashes=stmt_hashes, created_by=user_id))
    prev_status = spread.review_status
    spread.current_version_no = version
    stale = list(db.scalars(select(ReviewDecision).where(ReviewDecision.spread_id == spread.id, ReviewDecision.is_stale.is_(False),
                                                          ReviewDecision.spread_version_no < version)))
    for d in stale:
        d.is_stale = True
        d.stale_reason = f"Figures changed in version {version}: {reason}"
    if prev_status in ("approved", "submitted_for_review"):
        spread.review_status = "reopened" if prev_status == "approved" else "in_preparation"
        audit(db, spread.workspace_id, user_id, "review.invalidated", "spread", spread.id,
              details={"from_status": prev_status, "version": version, "reason": reason[:200]})
    sync_exceptions(db, spread, version, obs, stored)
    metric(db, spread.workspace_id, "spread.version", version, spread_id=spread.id)
    metric(db, spread.workspace_id, "validation.fail", sum(1 for r in rule_results if r.status == "fail"), spread_id=spread.id)
    metric(db, spread.workspace_id, "mapping.coverage",
           (sum(1 for o in obs if o.canonical_code) / len(obs)) if obs else 0.0, spread_id=spread.id)
    db.flush()
    return version


def open_critical(db: Session, spread: Spread) -> list[ValidationException]:
    return list(db.scalars(select(ValidationException).where(
        ValidationException.spread_id == spread.id, ValidationException.status == "open", ValidationException.severity == "critical")))


def doc_level_critical(db: Session, spread: Spread) -> list[ValidationException]:
    dv_ids = {o for (o,) in db.execute(select(Observation.document_version_id).where(Observation.spread_id == spread.id).distinct())}
    if not dv_ids:
        return []
    return list(db.scalars(select(ValidationException).where(
        ValidationException.document_version_id.in_(dv_ids), ValidationException.spread_id.is_(None),
        ValidationException.status == "open", ValidationException.severity == "critical")))


__all__ = ["recompute", "open_critical", "doc_level_critical", "build_facts", "choose_preferred", "Decimal"]
