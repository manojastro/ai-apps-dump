"""Deterministic rules and metrics. Includes proofs that insufficient data never becomes a result."""

from datetime import date
from decimal import Decimal

from spreadlens.metrics.ratios import compute_metrics
from spreadlens.rules.engine import run_rules
from spreadlens.rules.types import Fact, SpreadFacts, SubtotalGroup

P1, P0 = date(2025, 3, 31), date(2024, 3, 31)


def fact(code, value, period=P1, state="value", decimals=2, scale="crores", st=None, doc="d1", restated=False, fid=None):
    st = st or {"bs": "balance_sheet", "is": "income_statement", "cf": "cash_flow"}[code.split(".")[0]]
    v = None if value is None else Decimal(value) * Decimal(10_000_000)
    return Fact(id=fid or f"{code}@{period}@{doc}", code=code, period_end=period, value=v, state=state if value is not None else state,
                decimals=decimals, scale=scale, statement_type=st, label=code, document_version_id=doc, restated_flag=restated,
                source_ref=f"{doc}:p1")


def facts_of(*fs, groups=None):
    pref = {(f.code, f.period_end): f for f in fs}
    return SpreadFacts(preferred=pref, all_facts=list(fs), groups=groups or [], periods=sorted({f.period_end for f in fs}),
                       present_codes={f.code for f in fs})


def by_rule(results, rid, period=P1):
    return [r for r in results if r.rule_id == rid and r.period_end == period][0]


def test_balance_sheet_passes_within_rounding():
    sf = facts_of(fact("bs.total_assets", "1000.00"), fact("bs.total_equity_and_liabilities", "1000.01"))
    r = by_rule(run_rules(sf), "R01")
    # tolerance = 2 x 0.005 crore = 0.01 crore -> residual 0.01 crore passes
    assert r.status == "pass"
    assert r.difference == Decimal("-100000.00")  # observed (assets) - expected (E&L)
    assert r.tolerance == Decimal("100000.0000")


def test_balance_sheet_fails_beyond_rounding():
    sf = facts_of(fact("bs.total_assets", "1000.00"), fact("bs.total_equity_and_liabilities", "1001.00"))
    r = by_rule(run_rules(sf), "R01")
    assert r.status == "fail"
    assert r.difference == Decimal("-10000000.00")  # exact residual stored


def test_unreadable_input_is_insufficient_not_pass():
    sf = facts_of(fact("bs.total_assets", None, state="unreadable"), fact("bs.total_equity_and_liabilities", "1000"))
    r = by_rule(run_rules(sf), "R01")
    assert r.status == "insufficient_data"
    assert r.expected is None and r.observed is None and r.difference is None


def test_dash_is_not_treated_as_zero():
    sf = facts_of(fact("is.profit_before_tax", "100"), fact("is.tax_expense", None, state="dash_ambiguous"),
                  fact("is.net_profit", "100"))
    r = by_rule(run_rules(sf), "R06")
    assert r.status == "insufficient_data"


def test_missing_statement_is_insufficient():
    sf = facts_of(fact("bs.total_assets", "10"), fact("bs.total_equity_and_liabilities", "10"))
    r = by_rule(run_rules(sf), "R07")
    assert r.status == "insufficient_data"


def test_not_presented_subtotal_is_not_applicable():
    sf = facts_of(fact("bs.total_assets", "10"), fact("bs.total_equity_and_liabilities", "10"),
                  fact("bs.total_current_liabilities", "4"), fact("bs.total_non_current_liabilities", "3"))
    r = by_rule(run_rules(sf), "R03")  # total_liabilities never presented
    assert r.status == "not_applicable"


def test_gross_profit_not_applicable_when_not_reported():
    sf = facts_of(fact("is.revenue", "100"), fact("is.net_profit", "10"))
    assert by_rule(run_rules(sf), "R05").status == "not_applicable"


def test_cash_roll_with_fx():
    sf = facts_of(fact("cf.opening_cash", "50"), fact("cf.net_change_in_cash", "10"), fact("cf.fx_effect", "0.50"),
                  fact("cf.closing_cash", "60.50"), fact("cf.operating_cash_flow", "30"), fact("cf.investing_cash_flow", "-15"),
                  fact("cf.financing_cash_flow", "-5"))
    res = run_rules(sf)
    assert by_rule(res, "R08").status == "pass"
    assert by_rule(res, "R07").status == "pass"


def test_subtotal_group_detects_mismatch_without_double_counting():
    t = fact("bs.total_current_assets", "100")
    kids = (fact("bs.inventories", "40"), fact("bs.trade_receivables", "30"), fact("bs.cash_and_equivalents", "20"))
    sf = facts_of(t, *kids, groups=[SubtotalGroup("balance_sheet", P1, t, kids)])
    r = [r for r in run_rules(sf) if r.rule_id == "R04"][0]
    assert r.status == "fail" and r.difference == Decimal("100000000.00")


def test_restatement_surfaced():
    a = fact("is.revenue", "100", period=P0, doc="d1")
    b = fact("is.revenue", "104", period=P0, doc="d2", restated=True)
    sf = SpreadFacts(preferred={("is.revenue", P0): b}, all_facts=[a, b], periods=[P0], present_codes={"is.revenue"})
    r = [r for r in run_rules(sf) if r.rule_id == "R10"][0]
    assert r.status == "requires_review" and "restated" in r.explanation


def test_metrics_zero_and_negative_denominators():
    sf = facts_of(fact("is.revenue", "0", state="zero", period=P0), fact("is.revenue", "100"),
                  fact("is.net_profit", "-5"), fact("cf.operating_cash_flow", "8"),
                  fact("bs.total_equity", "-20"), fact("bs.non_current_borrowings", "50"),
                  fact("bs.total_current_assets", "10"), fact("bs.total_current_liabilities", "0", state="zero"))
    m = {(x.metric_id, x.period_end): x for x in compute_metrics(sf)}
    assert m[("revenue_growth", P1)].status == "special_interpretation"
    assert m[("ocf_to_net_profit", P1)].status == "special_interpretation"
    assert m[("debt_to_equity", P1)].status == "special_interpretation"
    assert m[("current_ratio", P1)].status == "special_interpretation"
    assert m[("revenue_growth", P1)].value is None


def test_metrics_insufficient_never_fabricated():
    sf = facts_of(fact("is.revenue", "100"))
    for m in compute_metrics(sf):
        if m.metric_id != "net_profit_margin":
            continue
        assert m.status == "insufficient_data" and m.value is None


def test_metric_values_exact():
    sf = facts_of(fact("is.revenue", "200", period=P0), fact("is.revenue", "250"), fact("is.net_profit", "25"),
                  fact("cf.operating_cash_flow", "40"), fact("cf.capex", "-15"))
    m = {(x.metric_id, x.period_end): x for x in compute_metrics(sf)}
    assert m[("revenue_growth", P1)].value == Decimal("0.25")
    assert m[("net_profit_margin", P1)].value == Decimal("0.1")
    assert m[("free_cash_flow", P1)].value == Decimal("250000000.00")
