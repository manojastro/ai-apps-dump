"""Versioned deterministic validation rules (ruleset rules-1.2.0).

Each rule:
  * looks up the facts it needs by canonical code and period,
  * returns `insufficient_data` when an input exists but is not a usable number,
  * returns `not_applicable` when the source structure does not present the inputs at all,
  * otherwise computes an exact Decimal residual and compares it with the rounding tolerance.

Rules never modify facts. They only report.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from spreadlens.rules.tolerance import rounding_tolerance
from spreadlens.rules.types import (
    FAIL,
    INSUFFICIENT,
    NOT_APPLICABLE,
    PASS,
    REQUIRES_REVIEW,
    Fact,
    RuleResult,
    SpreadFacts,
)

RULESET = "rules-1.2.0"


def _n(d) -> str:
    """Exact decimal string without exponent or trailing zeros (base units)."""
    if d is None:
        return "n/a"
    q = d.normalize()
    return format(q.quantize(1) if q == q.to_integral() else q, "f")


@dataclass(frozen=True)
class Term:
    code: str
    sign: int = 1
    optional: bool = False  # absent => treated as "not separately reported" (0), and said so


@dataclass(frozen=True)
class RuleDef:
    rule_id: str
    version: str
    title: str
    statement_type: str
    severity: str
    fn: Callable[[SpreadFacts, date, "RuleDef"], RuleResult | None]


def _state_text(f: Fact) -> str:
    return {"missing": "missing", "unreadable": "unreadable", "not_applicable": "reported as not applicable",
            "dash_ambiguous": "a dash of unestablished meaning"}.get(f.state, f.state)


def _equation(sf: SpreadFacts, period: date, rule: RuleDef, lhs: list[Term], rhs: str,
              alt_rhs: list[list[Term]] | None = None, expr: str = "") -> RuleResult:
    """Check sum(lhs) == rhs for one period."""
    base = dict(rule_id=rule.rule_id, rule_version=rule.version, title=rule.title,
                statement_type=rule.statement_type, period_end=period, severity=rule.severity,
                key=f"{rule.rule_id}:{period.isoformat()}")

    rhs_fact = sf.get(rhs, period)
    lhs_facts: list[tuple[Term, Fact | None]] = [(t, sf.get(t.code, period)) for t in lhs]
    required_absent = [t.code for t, f in lhs_facts if f is None and not t.optional]

    # Not presented at all -> the source structure does not support the check.
    if rhs_fact is None and all(f is None for _, f in lhs_facts):
        return RuleResult(**base, input_ids=[], expression=expr, expected=None, observed=None, difference=None,
                          tolerance=None, tolerance_basis=None, status=NOT_APPLICABLE,
                          explanation="None of the inputs are presented for this period.")
    never = [c for c in ([rhs] if rhs_fact is None else []) + required_absent if c not in sf.present_codes]
    if (rhs_fact is None or required_absent) and never and len(never) == len(required_absent) + (rhs_fact is None):
        return RuleResult(**base, input_ids=[f.id for _, f in lhs_facts if f] + ([rhs_fact.id] if rhs_fact else []),
                          expression=expr, expected=None, observed=None, difference=None, tolerance=None,
                          tolerance_basis=None, status=NOT_APPLICABLE,
                          explanation="The source presentation does not include: " + ", ".join(never)
                          + ". The check does not apply to this structure.")
    if rhs_fact is None or required_absent:
        missing = ([rhs] if rhs_fact is None else []) + required_absent
        return RuleResult(**base, input_ids=[f.id for _, f in lhs_facts if f] + ([rhs_fact.id] if rhs_fact else []),
                          expression=expr, expected=None, observed=None, difference=None, tolerance=None,
                          tolerance_basis=None, status=INSUFFICIENT,
                          explanation="Required inputs not available for this period: " + ", ".join(missing)
                          + ". No result is inferred.")
    assert rhs_fact is not None
    unusable = [f for _, f in lhs_facts if f is not None and not f.numeric] + ([] if rhs_fact.numeric else [rhs_fact])
    if unusable:
        return RuleResult(**base, input_ids=[rhs_fact.id] + [f.id for _, f in lhs_facts if f], expression=expr,
                          expected=None, observed=None, difference=None, tolerance=None, tolerance_basis=None,
                          status=INSUFFICIENT,
                          explanation="Inputs are not usable numbers: "
                          + "; ".join(f"'{f.label}' is {_state_text(f)}" for f in unusable) + ".",
                          source_refs=[f.source_ref for f in unusable])

    used = [(t, f) for t, f in lhs_facts if f is not None]
    expected = sum((Decimal(t.sign) * f.value for t, f in used), Decimal("0"))  # type: ignore[operator]
    observed = rhs_fact.value
    assert observed is not None
    diff = observed - expected
    tol, basis = rounding_tolerance([f for _, f in used] + [rhs_fact])
    omitted = [t.code for t, f in lhs_facts if f is None and t.optional]
    note = (" Not separately reported (treated as nil): " + ", ".join(omitted) + ".") if omitted else ""
    status = PASS if abs(diff) <= tol else FAIL
    explanation = (
        f"Expected {_n(expected)} from components, observed {_n(observed)}; residual {_n(diff)} (base units) "
        f"{'within' if status == PASS else 'exceeds'} rounding tolerance {_n(tol)}.{note}"
    )
    return RuleResult(**base, input_ids=[f.id for _, f in used] + [rhs_fact.id], expression=expr,
                      expected=expected, observed=observed, difference=diff, tolerance=tol, tolerance_basis=basis,
                      status=status, explanation=explanation,
                      source_refs=[f.source_ref for _, f in used] + [rhs_fact.source_ref])


# ---------------------------------------------------------------- rule bodies

def r01_balance(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    if sf.get("bs.total_equity_and_liabilities", p) is not None:
        return _equation(sf, p, rule, [Term("bs.total_equity_and_liabilities")], "bs.total_assets",
                         expr="total_assets = total_equity_and_liabilities")
    if sf.get("bs.total_liabilities", p) is not None:
        return _equation(sf, p, rule, [Term("bs.total_equity"), Term("bs.total_liabilities")], "bs.total_assets",
                         expr="total_assets = total_equity + total_liabilities")
    return _equation(sf, p, rule, [Term("bs.total_equity"), Term("bs.total_current_liabilities"),
                                   Term("bs.total_non_current_liabilities")], "bs.total_assets",
                     expr="total_assets = total_equity + total_current_liabilities + total_non_current_liabilities")


def r02_assets(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    return _equation(sf, p, rule, [Term("bs.total_current_assets"), Term("bs.total_non_current_assets")],
                     "bs.total_assets", expr="total_assets = total_current_assets + total_non_current_assets")


def r03_liabilities(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    return _equation(sf, p, rule, [Term("bs.total_current_liabilities"), Term("bs.total_non_current_liabilities")],
                     "bs.total_liabilities",
                     expr="total_liabilities = total_current_liabilities + total_non_current_liabilities")


def r05_gross_profit(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    if sf.get("is.gross_profit", p) is None:
        return RuleResult(rule.rule_id, rule.version, rule.title, rule.statement_type, p, [], "gross_profit = revenue - cost_of_sales",
                          None, None, None, None, None, rule.severity, NOT_APPLICABLE,
                          "Gross profit is not presented; the check does not apply to this presentation.",
                          key=f"{rule.rule_id}:{p.isoformat()}")
    return _equation(sf, p, rule, [Term("is.revenue"), Term("is.cost_of_sales", -1)], "is.gross_profit",
                     expr="gross_profit = revenue - cost_of_sales")


def r06_net_profit(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    expr = "net_profit = profit_before_tax - tax_expense  (tax charge positive, credit negative)"
    if sf.get("is.tax_expense", p) is None and (sf.get("is.current_tax", p) or sf.get("is.deferred_tax", p)):
        return _equation(sf, p, rule, [Term("is.profit_before_tax"), Term("is.current_tax", -1, optional=True),
                                       Term("is.deferred_tax", -1, optional=True)], "is.net_profit",
                         expr="net_profit = profit_before_tax - current_tax - deferred_tax")
    return _equation(sf, p, rule, [Term("is.profit_before_tax"), Term("is.tax_expense", -1)], "is.net_profit", expr=expr)


def r07_cash_categories(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    return _equation(sf, p, rule, [Term("cf.operating_cash_flow"), Term("cf.investing_cash_flow"),
                                   Term("cf.financing_cash_flow")], "cf.net_change_in_cash",
                     expr="net_change_in_cash = operating + investing + financing")


def r08_cash_roll(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    return _equation(sf, p, rule, [Term("cf.opening_cash"), Term("cf.net_change_in_cash"),
                                   Term("cf.fx_effect", optional=True)], "cf.closing_cash",
                     expr="closing_cash = opening_cash + net_change_in_cash + fx_effect (if separately reported)")


def r09_cash_to_bs(sf: SpreadFacts, p: date, rule: RuleDef) -> RuleResult:
    key = f"{rule.rule_id}:{p.isoformat()}"
    cf = sf.get("cf.closing_cash", p)
    bs = sf.get("bs.cash_and_equivalents", p)
    expr = "cf.closing_cash = bs.cash_and_equivalents + disclosed reconciling items (e.g. bank overdrafts)"
    if cf is None or bs is None:
        status = NOT_APPLICABLE if (cf is None and bs is None) else INSUFFICIENT
        return RuleResult(rule.rule_id, rule.version, rule.title, None, p, [f.id for f in (cf, bs) if f], expr,
                          None, None, None, None, None, rule.severity, status,
                          "Both the cash flow closing cash and balance sheet cash are needed.", key=key)
    if not (cf.numeric and bs.numeric):
        return RuleResult(rule.rule_id, rule.version, rule.title, None, p, [cf.id, bs.id], expr, None, None, None,
                          None, None, rule.severity, INSUFFICIENT, "An input is not a usable number.", key=key)
    tol, basis = rounding_tolerance([cf, bs])
    diff = cf.value - bs.value  # type: ignore[operator]
    if abs(diff) <= tol:
        return RuleResult(rule.rule_id, rule.version, rule.title, None, p, [cf.id, bs.id], expr, bs.value, cf.value,
                          diff, tol, basis, rule.severity, PASS, "Closing cash agrees with balance sheet cash.",
                          [cf.source_ref, bs.source_ref], key=key)
    items = sf.cash_reconciling_items.get(p, [])
    adj = sum((v for _, v in items), Decimal("0"))
    if items and abs(diff - adj) <= tol + tol:
        return RuleResult(rule.rule_id, rule.version, rule.title, None, p, [cf.id, bs.id], expr, bs.value + adj, cf.value,  # type: ignore[operator]
                          diff - adj, tol, basis, rule.severity, PASS,
                          "Difference is explained by disclosed reconciling items: "
                          + ", ".join(f"{n} {_n(v)}" for n, v in items) + ".", [cf.source_ref, bs.source_ref], key=key)
    return RuleResult(rule.rule_id, rule.version, rule.title, None, p, [cf.id, bs.id], expr, bs.value, cf.value, diff,
                      tol, basis, rule.severity, REQUIRES_REVIEW,
                      f"Closing cash differs from balance sheet cash by {_n(diff)}. Cash definitions can differ "
                      "(e.g. overdrafts, restricted balances); an analyst must confirm the reconciling items.",
                      [cf.source_ref, bs.source_ref], key=key)


RULES: list[RuleDef] = [
    RuleDef("R01", "1.1", "Assets equal liabilities plus equity", "balance_sheet", "critical", r01_balance),
    RuleDef("R02", "1.0", "Current + non-current assets equal total assets", "balance_sheet", "critical", r02_assets),
    RuleDef("R03", "1.0", "Current + non-current liabilities equal total liabilities", "balance_sheet", "critical", r03_liabilities),
    RuleDef("R05", "1.0", "Revenue less cost of sales equals gross profit", "income_statement", "warning", r05_gross_profit),
    RuleDef("R06", "1.1", "Profit before tax less tax equals net profit", "income_statement", "critical", r06_net_profit),
    RuleDef("R07", "1.0", "Cash flow categories equal net movement", "cash_flow", "critical", r07_cash_categories),
    RuleDef("R08", "1.0", "Opening cash plus movement equals closing cash", "cash_flow", "critical", r08_cash_roll),
    RuleDef("R09", "1.0", "Closing cash agrees to balance sheet cash", "cash_flow", "warning", r09_cash_to_bs),
]

STATEMENT_CODES_PREFIX = {"balance_sheet": "bs.", "income_statement": "is.", "cash_flow": "cf."}


def r04_subtotals(sf: SpreadFacts) -> list[RuleResult]:
    out = []
    for g in sf.groups:
        key = f"R04:{g.statement_type}:{g.total.label}:{g.period_end.isoformat()}"
        expr = f"'{g.total.label}' = sum of {len(g.children)} printed component rows"
        base = dict(rule_id="R04", rule_version="1.1", title=f"Components reconcile to '{g.total.label}'",
                    statement_type=g.statement_type, period_end=g.period_end, expression=expr, severity="warning", key=key)
        ids = [c.id for c in g.children] + [g.total.id]
        bad = [c for c in (*g.children, g.total) if not c.numeric]
        if bad:
            # Missing children rows in the group (blank cells) are a nil only if printed as zero.
            out.append(RuleResult(**base, input_ids=ids, expected=None, observed=None, difference=None, tolerance=None,
                                  tolerance_basis=None, status=INSUFFICIENT,
                                  explanation="Not all component cells are usable numbers: "
                                  + "; ".join(f"'{c.label}' is {_state_text(c)}" for c in bad) + ".",
                                  source_refs=[c.source_ref for c in bad]))
            continue
        expected = sum((c.value for c in g.children), Decimal("0"))  # type: ignore[misc]
        observed = g.total.value
        diff = observed - expected  # type: ignore[operator]
        tol, basis = rounding_tolerance(list(g.children) + [g.total])
        status = PASS if abs(diff) <= tol else FAIL
        out.append(RuleResult(**base, input_ids=ids, expected=expected, observed=observed, difference=diff,
                              tolerance=tol, tolerance_basis=basis, status=status,
                              explanation=f"Components sum to {_n(expected)}; subtotal shows {_n(observed)}; residual {_n(diff)}.",
                              source_refs=[c.source_ref for c in (*g.children, g.total)]))
    return out


def r10_comparatives(sf: SpreadFacts) -> list[RuleResult]:
    """Same item and period reported by more than one uploaded document."""
    by_key: dict[tuple[str, date], list[Fact]] = {}
    for f in sf.all_facts:
        if f.code:
            by_key.setdefault((f.code, f.period_end), []).append(f)
    out = []
    for (code, period), facts in sorted(by_key.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        docs = {f.document_version_id for f in facts}
        if len(docs) < 2:
            continue
        usable = [f for f in facts if f.numeric]
        key = f"R10:{code}:{period.isoformat()}"
        base = dict(rule_id="R10", rule_version="1.0", title=f"Comparable figure agrees across documents: {code}",
                    statement_type=facts[0].statement_type, period_end=period,
                    expression=f"{code}@{period} equal in every uploaded document", key=key)
        if len(usable) < 2:
            out.append(RuleResult(**base, input_ids=[f.id for f in facts], expected=None, observed=None, difference=None,
                                  tolerance=None, tolerance_basis=None, severity="warning", status=INSUFFICIENT,
                                  explanation="Fewer than two usable values to compare."))
            continue
        first, *rest = sorted(usable, key=lambda f: f.document_version_id)
        worst = max(rest, key=lambda f: abs(f.value - first.value))  # type: ignore[operator]
        diff = worst.value - first.value  # type: ignore[operator]
        tol, basis = rounding_tolerance([first, worst])
        if abs(diff) <= tol:
            out.append(RuleResult(**base, input_ids=[f.id for f in usable], expected=first.value, observed=worst.value,
                                  difference=diff, tolerance=tol, tolerance_basis=basis, severity="info", status=PASS,
                                  explanation="Values agree across documents."))
        else:
            restated = any(f.restated_flag for f in usable)
            out.append(RuleResult(**base, input_ids=[f.id for f in usable], expected=first.value, observed=worst.value,
                                  difference=diff, tolerance=tol, tolerance_basis=basis,
                                  severity="info" if restated else "warning", status=REQUIRES_REVIEW,
                                  explanation=("The later document labels this comparative as restated; both versions are kept. "
                                               if restated else "Documents disagree and no restatement label was found. ")
                                  + f"Difference {_n(diff)}.",
                                  source_refs=[f.source_ref for f in usable]))
    return out


def run_rules(sf: SpreadFacts) -> list[RuleResult]:
    results: list[RuleResult] = []
    for p in sf.periods:
        for rule in RULES:
            prefix = STATEMENT_CODES_PREFIX[rule.statement_type]
            # Skip a statement entirely absent for this period, but report it once as not applicable.
            has_stmt = any(k[1] == p and k[0].startswith(prefix) for k in sf.preferred)
            if not has_stmt and rule.rule_id != "R09":
                results.append(RuleResult(rule.rule_id, rule.version, rule.title, rule.statement_type, p, [], "", None,
                                          None, None, None, None, rule.severity, INSUFFICIENT,
                                          f"No {rule.statement_type.replace('_', ' ')} available for this period.",
                                          key=f"{rule.rule_id}:{p.isoformat()}"))
                continue
            r = rule.fn(sf, p, rule)
            if r is not None:
                results.append(r)
    results.extend(r04_subtotals(sf))
    results.extend(r10_comparatives(sf))
    return results
