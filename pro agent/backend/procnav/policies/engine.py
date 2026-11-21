"""Deterministic purchasing policy evaluation, ranking, and material-change detection.

A model confidence score is never an input here. Hard rules decide eligibility; soft preferences
are reported but cannot make a quote ineligible.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ..quotes.normalize import cart_view
from ..quotes.schemas import NormalizedQuote


@dataclass(frozen=True)
class RequestSpec:
    canonical_product_id: str
    required_spec: dict[str, Any]  # family, cpu, min_ram_gb, min_ssd_gb, storage_type, os
    quantity: int
    currency: str
    budget_total: Decimal
    address_ref: str
    delivery_deadline: date
    allowed_supplier_keys: tuple[str, ...]


@dataclass(frozen=True)
class SupplierStatus:
    key: str
    enabled: bool
    eligibility_status: str


@dataclass
class RuleResult:
    rule: str
    hard: bool
    passed: bool
    expected: str
    observed: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyEvaluation:
    eligible: bool
    results: list[RuleResult] = field(default_factory=list)

    @property
    def failed_hard(self) -> list[RuleResult]:
        return [r for r in self.results if r.hard and not r.passed]

    @property
    def failed_soft(self) -> list[RuleResult]:
        return [r for r in self.results if not r.hard and not r.passed]

    def to_list(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.results]


def _fmt(v: Any) -> str:
    if v is None:
        return "not observed"
    if isinstance(v, Decimal):
        return f"{v:.2f}"
    return str(v)


def evaluate(
    quote: NormalizedQuote,
    request: RequestSpec,
    supplier: SupplierStatus,
    policy: dict[str, Any],
    now: datetime,
    exceptions: set[str] | None = None,
) -> PolicyEvaluation:
    """Evaluate every rule (no short-circuit) so the comparison can show all failures."""
    exceptions = exceptions or set()
    out: list[RuleResult] = []

    def rule(name: str, passed: bool, expected: Any, observed: Any, message: str, hard: bool = True) -> None:
        if hard and not passed and name in exceptions:
            out.append(
                RuleResult(
                    name, True, True, _fmt(expected), _fmt(observed), f"{message} (authorized exception on record)"
                )
            )
            return
        out.append(RuleResult(name, hard, passed, _fmt(expected), _fmt(observed), message))

    req = request.required_spec
    s = quote.spec
    rule(
        "spec.canonical_family",
        s.family is not None and s.family == req.get("family"),
        req.get("family"),
        s.family,
        "Product family must match the canonical specification",
    )
    if req.get("cpu"):
        rule("spec.cpu", s.cpu == req["cpu"], req["cpu"], s.cpu, "Processor must match the canonical specification")
    rule(
        "spec.ram_gb",
        s.ram_gb is not None and s.ram_gb >= int(req["min_ram_gb"]),
        f">= {req['min_ram_gb']} GB",
        f"{s.ram_gb} GB" if s.ram_gb is not None else None,
        "Memory below the required minimum",
    )
    rule(
        "spec.ssd_gb",
        s.ssd_gb is not None and s.ssd_gb >= int(req["min_ssd_gb"]),
        f">= {req['min_ssd_gb']} GB",
        f"{s.ssd_gb} GB" if s.ssd_gb is not None else None,
        "Storage below the required minimum",
    )
    rule(
        "spec.storage_type",
        s.storage_type == req.get("storage_type", "SSD"),
        req.get("storage_type", "SSD"),
        s.storage_type,
        "Storage type must match",
    )
    if req.get("os"):
        rule("spec.os", s.os == req["os"], req["os"], s.os, "Operating system must match")
    rule(
        "unit.pack_size",
        quote.pack_size == 1,
        "1 laptop per unit",
        quote.pack_size,
        "Quantities are individual laptops; packs or ambiguous bundles need clarification",
    )
    rule(
        "quantity.match",
        quote.quantity == request.quantity,
        request.quantity,
        quote.quantity,
        "Checkout quantity must equal the requested quantity",
    )
    rule(
        "stock.available",
        quote.stock_observed is not None and quote.stock_observed >= request.quantity,
        f">= {request.quantity}",
        quote.stock_observed,
        "Supplier stock must cover the full quantity",
    )
    allowed_here = supplier.key in request.allowed_supplier_keys
    sup_ok = (
        supplier.enabled and supplier.eligibility_status == "approved" and supplier.key in request.allowed_supplier_keys
    )
    rule(
        "supplier.eligible",
        sup_ok,
        "approved and allowed for this request",
        f"{supplier.eligibility_status}, {'allowed' if allowed_here else 'not allowed'}",
        "Supplier must be approved, enabled and allowed for the request",
    )
    rule(
        "delivery.confirmed",
        quote.delivery_confidence == "confirmed",
        "confirmed date",
        quote.delivery_confidence,
        "Delivery date is uncertain; ask the supplier to confirm",
    )
    rule(
        "delivery.deadline",
        quote.delivery_date is not None and quote.delivery_date <= request.delivery_deadline,
        f"on or before {request.delivery_deadline.isoformat()}",
        quote.delivery_date,
        "Delivery misses the deadline",
    )
    rule(
        "destination.match",
        quote.address_ref == request.address_ref,
        request.address_ref,
        quote.address_ref,
        "Quote must ship to the requested destination",
    )
    allowed = policy.get("allowed_currencies", ["INR"])
    rule(
        "currency.allowed",
        quote.currency is not None and quote.currency == request.currency and quote.currency in allowed,
        request.currency,
        quote.currency,
        "Currency must be certain and allowed",
    )
    age = (now - quote.retrieved_at).total_seconds()
    max_age = int(policy.get("max_quote_age_seconds", 3600))
    rule("quote.fresh", age <= max_age, f"<= {max_age}s old", f"{int(age)}s", "Quote is stale; refresh required")
    missing = [
        n for n in ("unit_price", "subtotal", "discount", "tax", "shipping", "total") if getattr(quote, n) is None
    ]
    rule(
        "cost.components_present",
        not missing,
        "unit price, subtotal, discount, tax, shipping, total",
        "missing: " + ", ".join(missing) if missing else "all present",
        "All cost components must be shown",
    )
    rule(
        "arithmetic.consistent",
        quote.arithmetic_ok,
        "components sum to total",
        "consistent"
        if quote.arithmetic_ok
        else "; ".join(i for i in quote.issues if any(w in i for w in ("Total", "Subtotal", "Tax", "tax", "basis")))
        or "not verifiable",
        "Totals must be arithmetically consistent",
    )
    rule(
        "budget.landed_total",
        quote.total is not None and quote.total <= request.budget_total,
        f"<= INR {request.budget_total:.2f}",
        quote.total,
        "Landed cost (including tax and shipping) exceeds the budget",
    )
    limit = Decimal(str(policy.get("per_order_spending_limit", "999999999")))
    rule(
        "budget.spending_limit",
        quote.total is not None and quote.total <= limit,
        f"<= INR {limit:.2f}",
        quote.total,
        "Exceeds the per-order spending limit",
    )

    prefs = policy.get("soft_preferences", {})
    if prefs.get("max_delivery_days_preferred") and quote.delivery_date:
        days = (quote.delivery_date - now.date()).days
        rule(
            "pref.fast_delivery",
            days <= int(prefs["max_delivery_days_preferred"]),
            f"<= {prefs['max_delivery_days_preferred']} days",
            f"{days} days",
            "Slower than preferred",
            hard=False,
        )
    if prefs.get("preferred_suppliers"):
        rule(
            "pref.supplier",
            supplier.key in prefs["preferred_suppliers"],
            "preferred supplier",
            supplier.key,
            "Not a preferred supplier",
            hard=False,
        )

    eligible = all(r.passed for r in out if r.hard)
    return PolicyEvaluation(eligible=eligible, results=out)


def rank(candidates: list[tuple[NormalizedQuote, PolicyEvaluation]]) -> list[tuple[NormalizedQuote, PolicyEvaluation]]:
    """Eligible first by landed total, then earlier delivery, then supplier key (documented tie-breaker)."""

    def key(item: tuple[NormalizedQuote, PolicyEvaluation]):
        q, ev = item
        return (
            0 if ev.eligible else 1,
            q.total if q.total is not None else Decimal("Infinity"),
            q.delivery_date or date.max,
            q.supplier_key,
            q.sku,
        )

    return sorted(candidates, key=key)


def material_changes(approved: dict[str, Any], current: NormalizedQuote, fields: list[str]) -> list[dict[str, str]]:
    """Compare an approved cart view with the freshly observed cart. Any difference is material."""
    now_view = cart_view(current)
    changes = []
    for f in fields:
        a, c = approved.get(f), now_view.get(f)
        if _fmt(_norm(a)) != _fmt(_norm(c)):
            changes.append({"field": f, "approved": _fmt(_norm(a)), "current": _fmt(_norm(c))})
    return changes


def _norm(v: Any) -> Any:
    if isinstance(v, str):
        try:
            if any(ch.isdigit() for ch in v) and v.replace(".", "", 1).replace("-", "", 1).isdigit():
                return Decimal(v)
        except ArithmeticError:
            return v
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v
