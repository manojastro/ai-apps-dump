"""Bounded procurement workflow as a LangGraph state machine with durable Postgres checkpoints.

Graph persistence makes progress resumable; it does not make purchasing safe to replay. Every
side effect goes through the order ledger, which a resumed node consults before acting.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt
from sqlalchemy import select

from ..approvals import service as approvals
from ..browser.tools import BudgetExhausted, HumanHandoff, RunCanceled, SupplierBrowser, ToolResult
from ..core.audit import audit, run_event
from ..core.tracing import span
from ..core.db import tenant_session
from ..core.models import (
    ApprovalRequest,
    PolicyDecision,
    PolicyException,
    ProcurementRun,
    Quote,
    QuoteLine,
    Supplier,
    SupplierOrder,
)
from ..orders import ledger
from ..policies.engine import RequestSpec, SupplierStatus, evaluate, material_changes, rank
from ..quotes.normalize import normalize_product, normalize_quote, quote_hash
from ..quotes.schemas import ExtractedCheckout, ExtractedProduct, NormalizedQuote, NormalizedSpec
from ..suppliers.secrets import resolve
from .context import CONTEXTS, RunContext

MAX_REVALIDATIONS = 3
SAFE_PRE_CLICK = {"TERMS_CHANGED", "LEDGER_REFUSED", "DRY_RUN", "DESTINATION_UNAVAILABLE"}


class RunState(TypedDict, total=False):
    run_id: str
    tenant_id: str
    phase: str
    request: dict[str, Any]
    suppliers_pending: list[str]
    supplier_status: dict[str, dict[str, Any]]
    search_plan: dict[str, list[str]]
    current_supplier: str | None
    current_products: list[dict[str, Any]]
    current_checkouts: list[dict[str, Any]]
    quote_ids: list[str]
    selected_quote_id: str | None
    recommendation: dict[str, Any] | None
    approval_request_id: str | None
    revalidations: int
    budget_exhausted: str | None
    handoff: dict[str, Any] | None
    resume_to: str | None
    outcome: str | None
    outcome_detail: dict[str, Any]


def _ctx(state: RunState) -> RunContext:
    return CONTEXTS[state["run_id"]]


def guarded(phase: str):
    """Wrap a node: set phase, convert cancellation/budget/handoff into state transitions."""

    def deco(fn):
        def node(state: RunState) -> dict[str, Any]:
            ctx = _ctx(state)
            ctx.set_run(phase=phase, status="running")
            try:
                with span(f"node.{phase}", run_id=state["run_id"], tenant_id=state.get("tenant_id")):
                    out = fn(state, ctx) or {}
            except RunCanceled:
                return {"outcome": "canceled", "outcome_detail": {"phase": phase}}
            except BudgetExhausted as b:
                ctx.event("budget_exhausted", {"budget": b.budget, "detail": str(b), "phase": phase})
                return {
                    "budget_exhausted": b.budget,
                    "suppliers_pending": [],
                    "current_products": [],
                    "current_checkouts": [],
                }
            except HumanHandoff as h:
                return {
                    "handoff": {
                        "reason": h.reason,
                        "detail": h.detail,
                        "resume_to": phase,
                        "supplier": state.get("current_supplier"),
                    }
                }
            out.setdefault("phase", phase)
            return out

        node.__name__ = fn.__name__
        return node

    return deco


def _request_spec(req, canonical: dict[str, Any], db) -> RequestSpec:
    allowed = db.scalars(select(Supplier.key).where(Supplier.id.in_([uuid.UUID(x) for x in req.allowed_supplier_ids])))
    spec = dict(req.spec_requirements)
    spec.setdefault("family", canonical.get(req.canonical_product_id, {}).get("family"))
    return RequestSpec(
        req.canonical_product_id,
        spec,
        req.quantity,
        req.currency,
        req.budget_total,
        req.address_ref,
        req.delivery_deadline,
        tuple(allowed.all()),
    )


# ============================================================================ nodes


@guarded("intake")
def intake(state: RunState, ctx: RunContext):
    with tenant_session(ctx.tenant_id) as db:
        req = ctx.request(db)
        spec = _request_spec(req, ctx.canonical, db)
        run = db.get(ProcurementRun, ctx.run_id)
        if run.started_at is None:
            run.started_at = datetime.now(UTC)
        summary = {
            "canonical_product_id": spec.canonical_product_id,
            "family": spec.required_spec.get("family"),
            "required_spec": spec.required_spec,
            "quantity": spec.quantity,
            "currency": spec.currency,
            "budget_total": f"{spec.budget_total:.2f}",
            "address_ref": spec.address_ref,
            "delivery_deadline": spec.delivery_deadline.isoformat(),
            "suppliers": list(spec.allowed_supplier_keys),
        }
    return {
        "request": summary,
        "suppliers_pending": sorted(summary["suppliers"]),
        "supplier_status": {},
        "quote_ids": [],
        "revalidations": 0,
        "outcome": None,
        "handoff": None,
        "budget_exhausted": None,
        "outcome_detail": {},
    }


@guarded("request_validation")
def validate_request(state: RunState, ctx: RunContext):
    r = state["request"]
    missing = []
    if r["canonical_product_id"] not in ctx.canonical:
        missing.append("canonical_product_id (unknown product)")
    for key in ("min_ram_gb", "min_ssd_gb"):
        if not r["required_spec"].get(key):
            missing.append(f"required_spec.{key}")
    if r["quantity"] < 1:
        missing.append("quantity")
    if Decimal(r["budget_total"]) <= 0:
        missing.append("budget_total")
    if date.fromisoformat(r["delivery_deadline"]) <= datetime.now(UTC).date():
        missing.append("delivery_deadline (must be in the future)")
    with tenant_session(ctx.tenant_id) as db:
        destinations = ctx.policy(db).rules.get("destinations", {})
    if r["address_ref"] not in destinations:
        missing.append("address_ref (not a registered destination)")
    if not r["suppliers"]:
        missing.append("allowed suppliers")
    if missing:
        return {"outcome": "needs_clarification", "outcome_detail": {"missing": missing}}
    return {}


@guarded("search_planning")
def plan_search(state: RunState, ctx: RunContext):
    d = ctx.model.plan_search(
        {"family": state["request"]["family"], "spec": state["request"]["required_spec"]}, state["suppliers_pending"]
    )
    plan = {
        p.supplier_key: [q[:120] for q in p.queries[:2]]
        for p in d.value.plans
        if p.supplier_key in state["suppliers_pending"]
    }
    for s in state["suppliers_pending"]:
        plan.setdefault(s, [state["request"]["family"]])
    ctx.charge(d, "plan_search", {"plan": plan, "note": d.value.note})
    return {"search_plan": plan}


def _browser_for(ctx: RunContext, key: str):
    with tenant_session(ctx.tenant_id) as db:
        handle, _ = ctx.supplier_handle(db, key)
    return SupplierBrowser(ctx.browser(), handle, resolve(handle.credential_ref), ctx.sink, decided_by=ctx.decided_by)


def _product_from_model(
    ctx: RunContext, obs_page: dict[str, Any], dom: ExtractedProduct, supplier: str
) -> ExtractedProduct:
    d = ctx.model.extract_product(obs_page)
    ctx.charge(
        d,
        "extract_product",
        {"supplier": supplier, "product": d.value.product_name, "injection_suspected": d.value.injection_suspected},
    )
    if d.value.injection_suspected:
        ctx.event("injection_suspected", {"supplier": supplier, "url": dom.source_url})
    return ExtractedProduct(
        product_name=d.value.product_name,
        sku=d.value.sku,
        fields={f.label: f.value for f in d.value.facts},
        flags=d.value.unlabeled_badges,
        source_url=dom.source_url,
    )


@guarded("supplier_browsing")
def browse_supplier(state: RunState, ctx: RunContext):
    key = state["suppliers_pending"][0]
    status = dict(state.get("supplier_status", {}))
    products: list[dict[str, Any]] = []
    try:
        with _browser_for(ctx, key) as sb:
            if not sb.open_supplier().ok:
                status[key] = {"status": "unavailable", "detail": "could not open portal"}
                return {"current_supplier": key, "current_products": [], "supplier_status": status}
            candidates: dict[str, dict[str, Any]] = {}
            for query in state["search_plan"].get(key, []):
                res = sb.find_product(query, explanation=f"Search for {query}")
                if not res.ok and ctx.verify:
                    res = sb.find_product(query, explanation="Retry search after failure")
                for c in res.data.get("candidates", []):
                    candidates.setdefault(c["href"], c)
                if not res.ok and not candidates:
                    status[key] = {"status": "unavailable", "detail": res.message, "code": res.error_code}
                    return {"current_supplier": key, "current_products": [], "supplier_status": status}
            listing = list(candidates.values())
            d = ctx.model.choose_candidates(state["request"], listing)
            valid = {c["index"]: c for c in listing}
            chosen = [valid[i] for i in d.value.indexes if i in valid]  # validate against observation
            ctx.charge(
                d,
                "choose_candidates",
                {
                    "supplier": key,
                    "chosen": [c["text"] for c in chosen],
                    "reason": d.value.reason,
                    "rejected_indexes": [i for i in d.value.indexes if i not in valid],
                },
            )
            results_url = sb.last_obs.url if sb.last_obs else None
            for n, c in enumerate(chosen):
                if n and results_url:
                    sb.revisit(results_url, "Return to search results")
                r = sb.inspect_product(c["href"], explanation=f"Inspect {c['text'][:60]}")
                if not r.ok:
                    continue
                dom = ExtractedProduct(**r.data["product"])
                extracted = dom
                if not ctx.model.simulated:
                    extracted = _product_from_model(
                        ctx,
                        sb.last_obs.model_dump(include={"title", "headings", "pairs", "chips", "notes", "text"}),
                        dom,
                        key,
                    )
                # Untrusted page content may propose actions; they are validated, never trusted.
                if ctx.fixture_options.get("follow_injected_links"):
                    proposal = ctx.model.recover("Continue evaluating the product", sb.last_obs.summary())
                    ctx.charge(proposal, "recover", {"supplier": key, "proposal": proposal.value.model_dump()})
                    if proposal.value.type == "click_link" and proposal.value.index is not None:
                        blocked = sb.perform_page_action(
                            {"type": "click_link", "index": proposal.value.index}, explanation=proposal.value.reason
                        )
                        ctx.event(
                            "proposal_validated", {"supplier": key, "allowed": blocked.ok, "code": blocked.error_code}
                        )
                products.append({"href": c["href"], "product": extracted.model_dump(), "dom_product": dom.model_dump()})
    except HumanHandoff as h:
        if h.reason == "paused_by_user":
            raise
        status[key] = {"status": "needs_human", "detail": h.detail, "reason": h.reason}
        return {"current_supplier": key, "current_products": [], "supplier_status": status}
    status[key] = {"status": "browsed", "products": len(products)}
    return {"current_supplier": key, "current_products": products, "supplier_status": status}


@guarded("quote_extraction")
def extract_quotes(state: RunState, ctx: RunContext):
    key = state["current_supplier"]
    qty = state["request"]["quantity"]
    address = state["request"]["address_ref"]
    out: list[dict[str, Any]] = []
    if not state.get("current_products"):
        return {"current_checkouts": []}
    try:
        with _browser_for(ctx, key) as sb:
            for item in state["current_products"]:
                facts = normalize_product(ExtractedProduct(**item["product"]), key, ctx.sku_map, ctx.canonical)
                if not facts.sku:
                    out.append({"href": item["href"], "error": "SKU_NOT_FOUND"})
                    continue
                results: list[ToolResult] = sb.refresh_quote(item["href"], qty, facts.sku, address)
                last = results[-1]
                if not last.ok or last.tool != "extract_quote":
                    out.append(
                        {
                            "href": item["href"],
                            "product": item["product"],
                            "error": last.error_code,
                            "message": last.message,
                        }
                    )
                    continue
                fresh = results[0].data.get("product") or item["product"]
                product = fresh if ctx.model.simulated else item["product"]
                out.append(
                    {
                        "href": item["href"],
                        "product": product,
                        "checkout": last.data["checkout"],
                        "retrieved_at": last.at.isoformat(),
                        "evidence_ids": results[0].evidence_ids + last.evidence_ids,
                    }
                )
    except HumanHandoff as h:
        if h.reason == "paused_by_user":
            raise
        status = dict(state.get("supplier_status", {}))
        status[key] = {"status": "needs_human", "detail": h.detail, "reason": h.reason}
        return {"current_checkouts": [], "supplier_status": status}
    return {"current_checkouts": out}


def _save_quote(
    db,
    ctx: RunContext,
    supplier: Supplier,
    q: NormalizedQuote,
    product_url: str,
    evidence: list[str],
    supersedes: uuid.UUID | None = None,
    version: int = 1,
) -> Quote:
    policy = ctx.policy(db)
    row = Quote(
        tenant_id=ctx.tenant_id,
        run_id=ctx.run_id,
        supplier_id=supplier.id,
        version=version,
        supersedes_id=supersedes,
        sku=q.sku or "unknown",
        product_name=q.product_name[:300],
        canonical_id=q.canonical_id,
        normalized_spec=q.spec.model_dump(),
        quantity=q.quantity,
        pack_size=q.pack_size,
        stock_observed=q.stock_observed,
        unit_price=q.unit_price,
        subtotal=q.subtotal,
        discount=q.discount,
        tax=q.tax,
        shipping=q.shipping,
        total=q.total,
        price_basis=q.price_basis,
        tax_basis=q.tax_basis,
        currency=q.currency,
        delivery_date=q.delivery_date,
        delivery_confidence=q.delivery_confidence,
        address_ref=q.address_ref,
        supplier_quote_ref=q.supplier_quote_ref,
        product_url=product_url,
        source_url=q.source_url,
        retrieved_at=q.retrieved_at,
        expires_at=q.retrieved_at + _age(policy),
        evidence_ids=evidence,
        extraction_method=q.extraction_method,
        issues=q.issues + ([] if q.arithmetic_ok else ["arithmetic not verified"]),
        canonical_hash=quote_hash(q),
    )
    db.add(row)
    db.flush()
    for kind, desc, amount in (
        ("goods", f"{q.quantity} x {q.sku}", q.subtotal),
        ("discount", "Discount", q.discount),
        ("tax", f"Tax ({q.price_basis or 'unknown basis'})", q.tax),
        ("shipping", "Shipping", q.shipping),
    ):
        if amount is not None:
            db.add(QuoteLine(tenant_id=ctx.tenant_id, quote_id=row.id, kind=kind, description=desc, amount=amount))
    return row


def _age(policy):
    from datetime import timedelta

    return timedelta(seconds=int(policy.rules.get("max_quote_age_seconds", 3600)))


@guarded("normalization")
def normalize(state: RunState, ctx: RunContext):
    key = state["current_supplier"]
    ids = list(state.get("quote_ids", []))
    status = dict(state.get("supplier_status", {}))
    made = 0
    with tenant_session(ctx.tenant_id) as db:
        supplier = db.scalar(select(Supplier).where(Supplier.key == key))
        for item in state.get("current_checkouts", []):
            if "checkout" not in item:
                continue
            facts = normalize_product(ExtractedProduct(**item["product"]), key, ctx.sku_map, ctx.canonical)
            q = normalize_quote(
                facts,
                ExtractedCheckout(**item["checkout"]),
                supplier_key=key,
                requested_quantity=state["request"]["quantity"],
                retrieved_at=datetime.fromisoformat(item["retrieved_at"]),
                extraction_method="dom" if ctx.model.simulated else "model+dom",
            )
            row = _save_quote(db, ctx, supplier, q, item["href"], item.get("evidence_ids", []))
            ids.append(str(row.id))
            made += 1
            run_event(
                db,
                ctx.tenant_id,
                ctx.run_id,
                "quote",
                {
                    "quote_id": str(row.id),
                    "supplier": key,
                    "sku": q.sku,
                    "total": f"{q.total}" if q.total else None,
                    "arithmetic_ok": q.arithmetic_ok,
                    "issues": q.issues[:5],
                },
            )
    if status.get(key, {}).get("status") == "browsed":
        status[key] = {"status": "quoted" if made else "no_quotes", "quotes": made}
    pending = [s for s in state["suppliers_pending"] if s != key]
    return {
        "quote_ids": ids,
        "suppliers_pending": pending,
        "supplier_status": status,
        "current_products": [],
        "current_checkouts": [],
        "current_supplier": None,
    }


def _evaluate_quote(db, ctx: RunContext, quote: Quote, context: str):
    req = ctx.request(db)
    spec = _request_spec(req, ctx.canonical, db)
    supplier = db.get(Supplier, quote.supplier_id)
    policy = ctx.policy(db)
    nq = _to_normalized(quote, supplier.key)
    exceptions = set(db.scalars(select(PolicyException.rule).where(PolicyException.quote_id == quote.id)).all())
    ev = evaluate(
        nq,
        spec,
        SupplierStatus(supplier.key, supplier.enabled, supplier.eligibility_status),
        policy.rules,
        datetime.now(UTC),
        exceptions,
    )
    db.add(
        PolicyDecision(
            tenant_id=ctx.tenant_id,
            run_id=ctx.run_id,
            quote_id=quote.id,
            policy_version_id=policy.id,
            context=context,
            eligible=ev.eligible,
            results=ev.to_list(),
        )
    )
    return nq, ev


def _to_normalized(q: Quote, supplier_key: str) -> NormalizedQuote:
    return NormalizedQuote(
        supplier_key=supplier_key,
        sku=q.sku,
        product_name=q.product_name,
        canonical_id=q.canonical_id,
        spec=NormalizedSpec(**q.normalized_spec),
        quantity=q.quantity,
        pack_size=q.pack_size,
        stock_observed=q.stock_observed,
        unit_price=q.unit_price,
        subtotal=q.subtotal,
        discount=q.discount,
        tax=q.tax,
        shipping=q.shipping,
        total=q.total,
        currency=q.currency,
        price_basis=q.price_basis,
        tax_basis=q.tax_basis,
        tax_rate=None,
        delivery_date=q.delivery_date,
        delivery_confidence=q.delivery_confidence,
        address_ref=q.address_ref,
        supplier_quote_ref=q.supplier_quote_ref,
        source_url=q.source_url,
        retrieved_at=q.retrieved_at,
        issues=list(q.issues),
        arithmetic_ok="arithmetic not verified" not in q.issues
        and not any("!=" in i or "does not match" in i or "inconsistent" in i for i in q.issues),
        extraction_method=q.extraction_method,
    )


@guarded("policy_validation")
def policy_validation(state: RunState, ctx: RunContext):
    results = {}
    with tenant_session(ctx.tenant_id) as db:
        for qid in state.get("quote_ids", []):
            quote = db.get(Quote, uuid.UUID(qid))
            _, ev = _evaluate_quote(db, ctx, quote, "comparison")
            results[qid] = {"eligible": ev.eligible, "failed": [r.rule for r in ev.failed_hard]}
        run_event(db, ctx.tenant_id, ctx.run_id, "policy_checked", {"results": results})
    return {}


@guarded("comparison")
def comparison(state: RunState, ctx: RunContext):
    with tenant_session(ctx.tenant_id) as db:
        evaluated = []
        rows = []
        for qid in state.get("quote_ids", []):
            quote = db.get(Quote, uuid.UUID(qid))
            supplier = db.get(Supplier, quote.supplier_id)
            dec = db.scalar(
                select(PolicyDecision)
                .where(PolicyDecision.quote_id == quote.id, PolicyDecision.context == "comparison")
                .order_by(PolicyDecision.created_at.desc())
            )
            nq = _to_normalized(quote, supplier.key)
            from ..policies.engine import PolicyEvaluation, RuleResult

            ev = PolicyEvaluation(dec.eligible, [RuleResult(**r) for r in dec.results])
            evaluated.append((nq, ev, qid))
            rows.append(
                {
                    "quote_id": qid,
                    "supplier": supplier.key,
                    "sku": quote.sku,
                    "name": quote.product_name,
                    "total": f"{quote.total}" if quote.total is not None else None,
                    "delivery_date": quote.delivery_date.isoformat() if quote.delivery_date else None,
                    "ram_gb": quote.normalized_spec.get("ram_gb"),
                }
            )
        ranked = rank([(q, e) for q, e, _ in evaluated])
        id_by_obj = {id(q): qid for q, _, qid in evaluated}
        order = [id_by_obj[id(q)] for q, _ in ranked]
        eligible = [id_by_obj[id(q)] for q, e in ranked if e.eligible]
    statuses = state.get("supplier_status", {})
    if not rows:
        needs_human = [k for k, v in statuses.items() if v.get("status") == "needs_human"]
        if needs_human:
            return {
                "handoff": {
                    "reason": "authentication_required",
                    "supplier": needs_human[0],
                    "detail": "No offers could be gathered because supplier sign-in needs a person: "
                    + ", ".join(needs_human),
                    "resume_to": "supplier_browsing",
                    "suppliers": needs_human,
                }
            }
        return {
            "outcome": "no_offers",
            "outcome_detail": {"suppliers": statuses, "budget_exhausted": state.get("budget_exhausted")},
        }
    d = ctx.model.recommend(state["request"], rows)
    rec_id = d.value.quote_id
    ctx.charge(d, "recommend", {"recommended": rec_id, "reason": d.value.rationale})
    recommendation = {
        "quote_id": rec_id,
        "rationale": d.value.rationale,
        "simulated": d.simulated,
        "accepted": rec_id in eligible,
    }
    if ctx.verify and rec_id not in eligible:
        with tenant_session(ctx.tenant_id) as db:
            quote = db.get(Quote, uuid.UUID(rec_id)) if rec_id in {r["quote_id"] for r in rows} else None
            failed = []
            if quote is not None:
                _, ev = _evaluate_quote(db, ctx, quote, "recommendation")
                failed = [r.to_dict() for r in ev.failed_hard]
            run_event(
                db,
                ctx.tenant_id,
                ctx.run_id,
                "verifier_rejected_recommendation",
                {"quote_id": rec_id, "failed_rules": failed, "rationale": d.value.rationale},
            )
            audit(
                db,
                ctx.tenant_id,
                actor_type="agent",
                actor_id="verifier",
                action="recommendation.rejected",
                entity_type="quote",
                entity_id=rec_id,
                run_id=ctx.run_id,
                data={"failed_rules": failed},
            )
        recommendation["verifier"] = {"rejected": True, "failed_rules": failed}
        selected = eligible[0] if eligible else None
    elif ctx.verify:
        selected = rec_id
    else:
        selected = rec_id  # single-pass baseline trusts the recommendation (measured in evals)
    summary = {
        "ranked": order,
        "eligible": eligible,
        "statuses": statuses,
        "budget_exhausted": state.get("budget_exhausted"),
    }
    ctx.set_run(summary={"comparison": summary, "recommendation": recommendation})
    if not selected:
        return {"outcome": "no_eligible_offer", "recommendation": recommendation, "outcome_detail": summary}
    return {"selected_quote_id": selected, "recommendation": recommendation}


@guarded("approval_request")
def create_approval(state: RunState, ctx: RunContext):
    with tenant_session(ctx.tenant_id) as db:
        quote = db.get(Quote, uuid.UUID(state["selected_quote_id"]))
        current = (
            db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
            if state.get("approval_request_id")
            else None
        )
        if current is not None and current.quote_id == quote.id and current.status in ("pending", "approved"):
            return {}
        reason = None
        if current is not None and current.invalidation:
            reason = current.invalidation
        ar = approvals.create_request(
            db,
            run_id=ctx.run_id,
            req=ctx.request(db),
            quote=quote,
            supplier=db.get(Supplier, quote.supplier_id),
            policy=ctx.policy(db),
            supersedes=current,
            reason=reason,
        )
        run = db.get(ProcurementRun, ctx.run_id)
        run.approval_request_id = ar.id
        run.selected_quote_id = quote.id
        return {"approval_request_id": str(ar.id)}


def await_approval(state: RunState) -> dict[str, Any]:
    """Interrupt until a human decides. The resume payload is ignored for authorization: the
    decision is read from the database, where only an authenticated approver can write it."""
    ctx = _ctx(state)
    ctx.set_run(status="awaiting_approval", phase="awaiting_approval")
    interrupt({"approval_request_id": state["approval_request_id"]})
    with tenant_session(ctx.tenant_id) as db:
        ar = db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
        run = db.get(ProcurementRun, ctx.run_id)
        run.status, run.phase = "running", "approval_received"
        if run.cancel_requested:
            return {"outcome": "canceled"}
        status = ar.status
        superseded = db.scalar(
            select(ApprovalRequest).where(ApprovalRequest.supersedes_id == ar.id, ApprovalRequest.status == "pending")
        )
        # Human waiting time is tracked separately from active browsing time.
        run.waiting_ms += max(0, int((datetime.now(UTC) - ar.created_at).total_seconds() * 1000))
    if status == "rejected":
        return {"outcome": "rejected"}
    if status == "invalidated" and superseded is not None:
        # The approver chose another eligible quote; wait for a decision on that one.
        return {"approval_request_id": str(superseded.id), "selected_quote_id": str(superseded.quote_id)}
    if status == "expired":
        return {"approval_request_id": state["approval_request_id"], "outcome_detail": {"approval": "expired"}}
    return {}


def _route_after_await(state: RunState) -> str:
    if state.get("outcome"):
        return "report"
    ctx = _ctx(state)
    with tenant_session(ctx.tenant_id) as db:
        ar = db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
        status = ar.status
    if status in ("approved", "consumed"):
        return "revalidate"
    if status == "pending":
        return "await_approval"
    return "revalidate"  # expired: refresh terms and request a fresh approval


@guarded("quote_revalidation")
def revalidate(state: RunState, ctx: RunContext):
    revs = state.get("revalidations", 0) + 1
    if revs > MAX_REVALIDATIONS:
        return {
            "handoff": {
                "reason": "terms_unstable",
                "detail": "Supplier terms kept changing during revalidation",
                "resume_to": "quote_revalidation",
            },
            "revalidations": revs,
        }
    with tenant_session(ctx.tenant_id) as db:
        quote = db.get(Quote, uuid.UUID(state["selected_quote_id"]))
        supplier = db.get(Supplier, quote.supplier_id)
        ar = db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
        key, product_url, sku, binding = supplier.key, quote.product_url, quote.sku, dict(ar.binding)
        req_version = ctx.request(db).version
        policy_fields = ctx.policy(db).rules.get("material_change_fields")
    with _browser_for(ctx, key) as sb:
        if not sb.open_supplier().ok:
            return {
                "handoff": {
                    "reason": "supplier_unavailable",
                    "detail": f"{key} unavailable during revalidation",
                    "resume_to": "quote_revalidation",
                },
                "revalidations": revs,
            }
        results = sb.refresh_quote(product_url, binding["quantity"], sku, binding["address_ref"])
    last = results[-1]
    if not last.ok or last.tool != "extract_quote":
        return {
            "handoff": {
                "reason": "revalidation_failed",
                "detail": last.message or last.error_code,
                "resume_to": "quote_revalidation",
            },
            "revalidations": revs,
        }
    facts = normalize_product(ExtractedProduct(**results[0].data["product"]), key, ctx.sku_map, ctx.canonical)
    fresh = normalize_quote(
        facts,
        ExtractedCheckout(**last.data["checkout"]),
        supplier_key=key,
        requested_quantity=binding["quantity"],
        retrieved_at=last.at,
    )
    with tenant_session(ctx.tenant_id) as db:
        supplier = db.get(Supplier, uuid.UUID(binding["supplier_id"]))
        new_row = _save_quote(
            db,
            ctx,
            supplier,
            fresh,
            product_url,
            results[0].evidence_ids + last.evidence_ids,
            supersedes=quote.id,
            version=quote.version + 1,
        )
        _, ev = _evaluate_quote(db, ctx, new_row, "revalidation")
        changes = material_changes(binding["cart"], fresh, policy_fields)
        ar = db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
        if req_version != binding["request_version"]:
            changes.append(
                {"field": "request_version", "approved": str(binding["request_version"]), "current": str(req_version)}
            )
        expired = ar.status == "expired" or ar.expires_at <= datetime.now(UTC)
        if changes or not ev.eligible or expired or ar.status not in ("approved",):
            why = (
                "expired"
                if expired
                else ("terms_changed" if changes else ("policy_failed" if not ev.eligible else f"approval_{ar.status}"))
            )
            approvals.invalidate(db, ar, changes, why)
            if not ev.eligible:
                return {
                    "outcome": "no_eligible_offer",
                    "revalidations": revs,
                    "outcome_detail": {
                        "revalidation_failed_rules": [r.rule for r in ev.failed_hard],
                        "changes": changes,
                    },
                }
            return {
                "selected_quote_id": str(new_row.id),
                "revalidations": revs,
                "outcome_detail": {"last_invalidation": {"reason": why, "changes": changes}},
            }
        run_event(db, ctx.tenant_id, ctx.run_id, "revalidated", {"quote_id": str(new_row.id), "unchanged": True})
    return {"revalidations": revs, "outcome_detail": {"revalidated_quote_id": str(new_row.id)}}


def _route_after_revalidate(state: RunState) -> str:
    if state.get("outcome") or state.get("handoff"):
        return "report" if state.get("outcome") else "human_handoff"
    ctx = _ctx(state)
    with tenant_session(ctx.tenant_id) as db:
        ar = db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
        status = ar.status
    return "submit" if status == "approved" else "create_approval"


@guarded("submission")
def submit(state: RunState, ctx: RunContext):
    worker = ctx.worker_id
    with tenant_session(ctx.tenant_id) as db:
        intent = ledger.intent_for_run(db, ctx.run_id)
        if intent is not None and intent.status in ledger.IN_FLIGHT:
            run_event(
                db,
                ctx.tenant_id,
                ctx.run_id,
                "submission_skipped_reconcile",
                {"intent_status": intent.status, "reason": "possible external effect; reconcile first"},
            )
            return {"outcome_detail": {"submit": "reconcile_existing"}}
        if intent is not None and intent.status in ("submitted", "reconciled"):
            return {"outcome_detail": {"submit": "already_submitted"}}
        ar = db.get(ApprovalRequest, uuid.UUID(state["approval_request_id"]))
        intent = ledger.create_intent_from_approval(db, ar, worker)
        intent_id, intent_key = intent.id, intent.intent_key
        db.get(ProcurementRun, ctx.run_id).order_intent_id = intent.id
        binding = dict(ar.binding)
        supplier = db.get(Supplier, ar.supplier_id)
        key = supplier.key
        quote = db.get(Quote, uuid.UUID(state["selected_quote_id"]))
        product_facts = ExtractedProduct(product_name=quote.product_name, fields={}, source_url=quote.product_url or "")
    with tenant_session(ctx.tenant_id) as db:
        ledger.transition(db, intent_id, "submitting", actor=worker, expect=("approved",))
        attempt = ledger.begin_attempt(db, db.get(ledger.OrderIntent, intent_id), worker)
        attempt_id = attempt.id
    ctx.set_run(status="submitting")

    def ledger_allows() -> bool:
        with tenant_session(ctx.tenant_id) as db:
            row = db.get(ledger.OrderIntent, intent_id)
            return row.status == "submitting"

    def current_matches(checkout: ExtractedCheckout) -> list[dict[str, str]]:
        facts = normalize_product(product_facts, key, ctx.sku_map, ctx.canonical)
        facts.sku = binding["cart"]["sku"]
        live = normalize_quote(
            facts, checkout, supplier_key=key, requested_quantity=binding["quantity"], retrieved_at=datetime.now(UTC)
        )
        live.sku = binding["cart"]["sku"]
        return material_changes(binding["cart"], live, list(binding["cart"].keys()))

    with _browser_for(ctx, key) as sb:
        sb.open_supplier()
        result = sb.submit_approved_order(
            intent_key=intent_key,
            address_ref=binding["address_ref"],
            approved_cart=binding["cart"],
            ledger_allows=ledger_allows,
            current_matches=current_matches,
        )
    code = result.error_code
    with tenant_session(ctx.tenant_id) as db:
        attempt = db.get(ledger.OrderAttempt, attempt_id)
        attempt.finished_at = datetime.now(UTC)
        attempt.evidence_ids = result.evidence_ids
        attempt.detail = {"code": code, "message": result.message, "data": result.data}
        if result.ok:
            attempt.outcome = "submitted"
            ledger.transition(db, intent_id, "submitted", actor=worker)
            db.add(
                SupplierOrder(
                    tenant_id=ctx.tenant_id,
                    intent_id=intent_id,
                    supplier_id=uuid.UUID(binding["supplier_id"]),
                    supplier_order_ref=result.data["order_ref"],
                    sku=binding["cart"]["sku"],
                    quantity=binding["quantity"],
                    reconciled_via="confirmation_page",
                )
            )
            return {"outcome_detail": {"submit": "submitted", "order_ref": result.data["order_ref"]}}
        if code in SAFE_PRE_CLICK or (code or "").startswith("SUPPLIER_REJECTED_"):
            attempt.outcome = "rejected"
            ledger.transition(db, intent_id, "failed", actor=worker, reason=f"{code}: {result.message}")
            changes = result.data.get("changes", [])
            if code in ("TERMS_CHANGED", "SUPPLIER_REJECTED_QUOTE_CHANGED"):
                run_event(db, ctx.tenant_id, ctx.run_id, "submission_blocked_terms_changed", {"changes": changes})
                return {"outcome_detail": {"submit": "terms_changed", "changes": changes}}
            return {"outcome": "submission_rejected", "outcome_detail": {"code": code, "message": result.message}}
        attempt.outcome = "timeout" if code == "SUBMISSION_OUTCOME_UNKNOWN" else "error"
        intent = db.get(ledger.OrderIntent, intent_id)
        target = "cancellation_requested" if db.get(ProcurementRun, ctx.run_id).cancel_requested else "unknown"
        if intent.status == "submitting":
            ledger.transition(db, intent_id, target, actor=worker, reason=f"{code}: {result.message}")
        return {"outcome_detail": {"submit": "unknown", "code": code}}


def _route_after_submit(state: RunState) -> str:
    if state.get("outcome"):
        return "report"
    if state.get("handoff"):
        return "human_handoff"
    sub = state.get("outcome_detail", {}).get("submit")
    if sub in ("submitted", "already_submitted"):
        return "verify_receipt"
    if sub == "terms_changed":
        return "revalidate"
    return "reconcile"


@guarded("reconciliation")
def reconcile(state: RunState, ctx: RunContext):
    with tenant_session(ctx.tenant_id) as db:
        intent = ledger.intent_for_run(db, ctx.run_id)
        if intent is None:
            return {"outcome": "failed", "outcome_detail": {"reconcile": "no_intent"}}
        if intent.status in ("submitted", "reconciled"):
            return {"outcome_detail": {"submit": "submitted"}}
        intent_id, intent_key = intent.id, intent.intent_key
        supplier = db.get(Supplier, intent.supplier_id)
        key = supplier.key
        ctx.set_run(status="reconciling")
    found_refs: list[str] = []
    checks = 0
    with _browser_for(ctx, key) as sb:
        sb.open_supplier()
        for wait in (0, 3, 6):
            time.sleep(wait)
            checks += 1
            r = sb.inspect_order_history(intent_key)
            if r.ok and (r.data.get("found") or r.data.get("ambiguous")):
                found_refs = r.data["order_refs"]
                break
    with tenant_session(ctx.tenant_id) as db:
        intent = db.get(ledger.OrderIntent, intent_id)
        if len(found_refs) == 1:
            ledger.transition(
                db, intent_id, "submitted", actor=ctx.worker_id, reason="order found in supplier order history"
            )
            if db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == intent_id)) is None:
                db.add(
                    SupplierOrder(
                        tenant_id=ctx.tenant_id,
                        intent_id=intent_id,
                        supplier_id=intent.supplier_id,
                        supplier_order_ref=found_refs[0],
                        reconciled_via="order_history",
                    )
                )
            run_event(db, ctx.tenant_id, ctx.run_id, "reconciled", {"order_ref": found_refs[0], "checks": checks})
            return {"outcome_detail": {"submit": "submitted", "order_ref": found_refs[0], "reconciled": True}}
        if len(found_refs) > 1:
            return {
                "handoff": {
                    "reason": "ambiguous_orders",
                    "detail": f"Multiple orders carry {intent_key}",
                    "resume_to": "reconciliation",
                }
            }
        # Absent after a bounded window in an authoritative history: no order exists. Never resubmit
        # automatically; a new purchase needs a fresh approval.
        target = "canceled" if intent.status == "cancellation_requested" else "failed"
        ledger.transition(
            db,
            intent_id,
            target,
            actor=ctx.worker_id,
            reason=f"absence established after {checks} order-history checks",
        )
        run_event(db, ctx.tenant_id, ctx.run_id, "absence_established", {"intent_key": intent_key, "checks": checks})
        if target == "canceled":
            return {"outcome": "canceled"}
        return {"outcome_detail": {"submit": "absent"}}


def _route_after_reconcile(state: RunState) -> str:
    if state.get("outcome"):
        return "report"
    if state.get("handoff"):
        return "human_handoff"
    return "verify_receipt" if state.get("outcome_detail", {}).get("submit") == "submitted" else "revalidate"


@guarded("receipt_verification")
def verify_receipt(state: RunState, ctx: RunContext):
    with tenant_session(ctx.tenant_id) as db:
        intent = ledger.intent_for_run(db, ctx.run_id)
        so = db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == intent.id))
        ar = db.get(ApprovalRequest, intent.approval_request_id)
        binding, key, order_ref, intent_id, intent_key = (
            dict(ar.binding),
            ar.binding["supplier_key"],
            so.supplier_order_ref,
            intent.id,
            intent.intent_key,
        )
    with _browser_for(ctx, key) as sb:
        sb.open_supplier()
        r = sb.verify_receipt(order_ref)
    if not r.ok:
        return {
            "handoff": {
                "reason": "receipt_unavailable",
                "detail": r.message or r.error_code,
                "resume_to": "receipt_verification",
            }
        }
    rec = r.data["receipt"]
    cart = binding["cart"]
    from ..quotes.normalize import parse_money

    checks = {
        "order_ref": rec.get("Order reference") == order_ref,
        "po_reference": rec.get("PO reference") == intent_key,
        "sku": (rec.get("Item") or "").startswith(cart["sku"]),
        "quantity": rec.get("Quantity") == str(binding["quantity"]),
        "total": parse_money(rec.get("Total")) == Decimal(cart["total"]),
        "currency": rec.get("Currency") == cart["currency"],
        "delivery_date": rec.get("Delivery date") == cart["delivery_date"],
        "destination": rec.get("Ship to") == binding["address_ref"],
    }
    verified = all(checks.values())
    with tenant_session(ctx.tenant_id) as db:
        so = db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == intent_id))
        so.verified = verified
        so.verification = {"checks": checks, "receipt": rec}
        so.total = parse_money(rec.get("Total"))
        so.currency = rec.get("Currency")
        so.quantity = int(rec["Quantity"]) if (rec.get("Quantity") or "").isdigit() else None
        so.delivery_date = date.fromisoformat(rec["Delivery date"]) if rec.get("Delivery date") else None
        so.receipt_evidence_id = uuid.UUID(r.data["receipt_evidence_id"]) if r.data.get("receipt_evidence_id") else None
        if verified:
            ledger.transition(db, intent_id, "reconciled", actor=ctx.worker_id, reason="receipt verified")
        run_event(
            db,
            ctx.tenant_id,
            ctx.run_id,
            "receipt_verified" if verified else "receipt_mismatch",
            {"order_ref": order_ref, "checks": checks},
        )
    if not verified:
        return {"outcome": "receipt_mismatch", "outcome_detail": {"checks": checks}}
    return {"outcome": "purchased", "outcome_detail": {"order_ref": order_ref, "checks": checks}}


def human_handoff(state: RunState) -> dict[str, Any]:
    ctx = _ctx(state)
    h = state.get("handoff") or {}
    ctx.set_run(status="paused_for_human", phase="human_handoff", handoff=h)
    ctx.event("human_handoff", h)
    decision = interrupt({"handoff": h})
    action = (decision or {}).get("action", "retry") if isinstance(decision, dict) else "retry"
    ctx.set_run(status="running", handoff=None)
    if action == "cancel":
        return {"handoff": None, "outcome": "canceled"}
    resume_to = h.get("resume_to") or "supplier_browsing"
    if action == "skip":
        if resume_to == "supplier_browsing":
            return {"handoff": None, "resume_to": "policy_validation", "suppliers_pending": []}
        return {"handoff": None, "outcome": "canceled", "outcome_detail": {"skipped": resume_to}}
    pending = list(state.get("suppliers_pending", []))
    if resume_to == "supplier_browsing":
        extra = h.get("suppliers", []) + ([h["supplier"]] if h.get("supplier") else [])
        pending = list(dict.fromkeys(extra + pending))
    return {"handoff": None, "suppliers_pending": pending, "resume_to": resume_to}


def _route_after_handoff(state: RunState) -> str:
    if state.get("outcome"):
        return "report"
    target = {
        "supplier_browsing": "browse_supplier",
        "quote_extraction": "browse_supplier",
        "normalization": "browse_supplier",
        "quote_revalidation": "revalidate",
        "submission": "submit",
        "reconciliation": "reconcile",
        "receipt_verification": "verify_receipt",
        "comparison": "comparison",
        "search_planning": "plan_search",
        "policy_validation": "policy_validation",
    }
    resume = state.get("resume_to") or "supplier_browsing"
    if resume == "supplier_browsing" and not state.get("suppliers_pending"):
        return "policy_validation"
    return target.get(resume, "browse_supplier")


FINAL_STATUS = {
    "purchased": "completed",
    "no_eligible_offer": "no_eligible_offer",
    "no_offers": "no_eligible_offer",
    "needs_clarification": "needs_clarification",
    "canceled": "canceled",
    "rejected": "rejected",
    "submission_rejected": "failed",
    "receipt_mismatch": "failed",
    "failed": "failed",
}


def report(state: RunState) -> dict[str, Any]:
    ctx = _ctx(state)
    outcome = state.get("outcome") or "failed"
    with tenant_session(ctx.tenant_id) as db:
        run = db.get(ProcurementRun, ctx.run_id)
        summary = dict(run.summary or {})
        summary.update(
            {
                "outcome": outcome,
                "detail": state.get("outcome_detail", {}),
                "suppliers": state.get("supplier_status", {}),
                "budget_exhausted": state.get("budget_exhausted"),
                "recommendation": state.get("recommendation") or summary.get("recommendation"),
            }
        )
        run.summary = summary
        run.outcome = outcome
        run.status = FINAL_STATUS.get(outcome, "failed")
        run.phase = "finished"
        run.finished_at = datetime.now(UTC)
        if outcome == "canceled" and run.approval_request_id:
            ar = db.get(ApprovalRequest, run.approval_request_id)
            if ar and ar.status in ("pending", "approved"):
                approvals.invalidate(db, ar, [], "run_canceled")
        run_event(db, ctx.tenant_id, ctx.run_id, "run_finished", {"outcome": outcome, "status": run.status})
        audit(
            db,
            ctx.tenant_id,
            actor_type="agent",
            actor_id=None,
            action="run.finished",
            entity_type="run",
            entity_id=ctx.run_id,
            run_id=ctx.run_id,
            data={"outcome": outcome},
        )
    return {"phase": "finished"}


# ============================================================================ wiring


def _after(normal: str):
    def route(state: RunState) -> str:
        if state.get("outcome"):
            return "report"
        if state.get("handoff"):
            return "human_handoff"
        return normal

    return route


def _after_normalize(state: RunState) -> str:
    if state.get("outcome"):
        return "report"
    if state.get("handoff"):
        return "human_handoff"
    return (
        "browse_supplier"
        if state.get("suppliers_pending") and not state.get("budget_exhausted")
        else "policy_validation"
    )


def build_graph(checkpointer):
    g = StateGraph(RunState)
    for name, fn in [
        ("intake", intake),
        ("validate_request", validate_request),
        ("plan_search", plan_search),
        ("browse_supplier", browse_supplier),
        ("extract_quotes", extract_quotes),
        ("normalize", normalize),
        ("policy_validation", policy_validation),
        ("comparison", comparison),
        ("create_approval", create_approval),
        ("await_approval", await_approval),
        ("revalidate", revalidate),
        ("submit", submit),
        ("reconcile", reconcile),
        ("verify_receipt", verify_receipt),
        ("human_handoff", human_handoff),
        ("report", report),
    ]:
        g.add_node(name, fn)
    g.set_entry_point("intake")
    g.add_conditional_edges("intake", _after("validate_request"))
    g.add_conditional_edges("validate_request", _after("plan_search"))
    g.add_conditional_edges("plan_search", _after("browse_supplier"))
    g.add_conditional_edges("browse_supplier", _after("extract_quotes"))
    g.add_conditional_edges("extract_quotes", _after("normalize"))
    g.add_conditional_edges("normalize", _after_normalize)
    g.add_conditional_edges("policy_validation", _after("comparison"))
    g.add_conditional_edges("comparison", _after("create_approval"))
    g.add_conditional_edges("create_approval", _after("await_approval"))
    g.add_conditional_edges("await_approval", _route_after_await)
    g.add_conditional_edges("revalidate", _route_after_revalidate)
    g.add_conditional_edges("submit", _route_after_submit)
    g.add_conditional_edges("reconcile", _route_after_reconcile)
    g.add_conditional_edges("verify_receipt", _after("report"))
    g.add_conditional_edges("human_handoff", _route_after_handoff)
    g.add_edge("report", END)
    return g.compile(checkpointer=checkpointer)
