"""Ratios and trends (metrics-1.1.0). Computed only from sufficient, comparable inputs.

Definitions (also in docs/taxonomy-and-rules.md):
  revenue_growth     (revenue_t - revenue_t-1) / revenue_t-1 ; prior base <= 0 -> special interpretation
  net_profit_margin  net_profit / revenue ; revenue <= 0 -> special interpretation
  gross_margin       gross_profit / revenue ; only when gross profit is reported
  current_ratio      total_current_assets / total_current_liabilities ; denominator <= 0 -> special
  working_capital    total_current_assets - total_current_liabilities (monetary)
  debt_to_equity     (current_borrowings + non_current_borrowings) / total_equity ; excludes lease liabilities;
                     equity <= 0 -> special interpretation
  net_debt           current_borrowings + non_current_borrowings - cash_and_equivalents ; excludes lease
                     liabilities and other bank balances
  ocf_to_net_profit  operating_cash_flow / net_profit ; net profit <= 0 -> special interpretation
  free_cash_flow     operating_cash_flow - |purchase of property, plant and equipment| ; capex must be identified
EBITDA and debt service coverage are intentionally not computed (no universal definition / incomplete inputs).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from spreadlens.rules.types import Fact, MetricResult, SpreadFacts

VERSION = "metrics-1.1.0"
COMPUTED = "computed"
INSUFFICIENT = "insufficient_data"
SPECIAL = "special_interpretation"
NA = "not_applicable"


def _need(sf: SpreadFacts, p: date, codes: list[str]) -> tuple[list[Fact], list[str]]:
    got, problems = [], []
    for c in codes:
        f = sf.get(c, p)
        if f is None:
            problems.append(f"{c} not available")
        elif not f.numeric:
            problems.append(f"{c} is {f.state}")
        else:
            got.append(f)
    return got, problems


def _ratio(mid: str, title: str, p: date, num_code: str, den_code: str, sf: SpreadFacts, formula: str,
           den_label: str, limitations: list[str] | None = None) -> MetricResult:
    facts, problems = _need(sf, p, [num_code, den_code])
    ids = [f.id for f in facts]
    if problems:
        return MetricResult(mid, VERSION, title, p, formula, ids, None, "ratio", INSUFFICIENT,
                            "Not computed: " + "; ".join(problems) + ".", limitations or [])
    num, den = facts[0].value, facts[1].value
    assert num is not None and den is not None
    if den <= 0:
        return MetricResult(mid, VERSION, title, p, formula, ids, None, "ratio", SPECIAL,
                            f"{den_label} is {'zero' if den == 0 else 'negative'} ({den:f}); an ordinary ratio would be misleading.",
                            limitations or [])
    return MetricResult(mid, VERSION, title, p, formula, ids, num / den, "ratio", COMPUTED,
                        f"{num:f} / {den:f}", limitations or [])


def _borrowings(sf: SpreadFacts, p: date) -> tuple[Decimal | None, list[str], list[str], list[str]]:
    ids, lim, problems = [], [], []
    total = Decimal("0")
    found = 0
    for c in ("bs.current_borrowings", "bs.non_current_borrowings"):
        f = sf.get(c, p)
        if f is None:
            if c in sf.present_codes:
                problems.append(f"{c} not available for this period")
            else:
                lim.append(f"{c} not presented; treated as nil")
            continue
        if not f.numeric:
            problems.append(f"{c} is {f.state}")
            continue
        total += f.value  # type: ignore[operator]
        ids.append(f.id)
        found += 1
    if found == 0 and not problems:
        problems.append("no borrowings line identified")
    lim.append("Debt excludes lease liabilities and other financial liabilities.")
    return (None if problems else total), ids, lim, problems


def compute_metrics(sf: SpreadFacts) -> list[MetricResult]:
    out: list[MetricResult] = []
    periods = sf.periods
    for i, p in enumerate(periods):
        # Revenue growth needs the immediately preceding comparable annual period.
        if i > 0:
            prev = periods[i - 1]
            gap = (p - prev).days
            facts, problems = _need(sf, p, ["is.revenue"])
            pf, pproblems = _need(sf, prev, ["is.revenue"])
            formula = "(revenue_t - revenue_t-1) / revenue_t-1"
            ids = [f.id for f in facts + pf]
            if not 350 <= gap <= 380:
                out.append(MetricResult("revenue_growth", VERSION, "Revenue growth", p, formula, ids, None, "percent", NA,
                                        f"Periods are {gap} days apart; not comparable annual periods.", [], prev))
            elif problems or pproblems:
                out.append(MetricResult("revenue_growth", VERSION, "Revenue growth", p, formula, ids, None, "percent",
                                        INSUFFICIENT, "Not computed: " + "; ".join(problems + pproblems) + ".", [], prev))
            else:
                cur, base = facts[0].value, pf[0].value
                assert cur is not None and base is not None
                if base <= 0:
                    out.append(MetricResult("revenue_growth", VERSION, "Revenue growth", p, formula, ids, None, "percent",
                                            SPECIAL, f"Prior-period revenue is {'zero' if base == 0 else 'negative'}; growth % is not meaningful.",
                                            [], prev))
                else:
                    out.append(MetricResult("revenue_growth", VERSION, "Revenue growth", p, formula, ids,
                                            (cur - base) / base, "percent", COMPUTED, f"({cur:f} - {base:f}) / {base:f}", [], prev))

        out.append(_ratio("net_profit_margin", "Net profit margin", p, "is.net_profit", "is.revenue", sf,
                          "net_profit / revenue", "Revenue"))
        if sf.get("is.gross_profit", p) is not None:
            out.append(_ratio("gross_margin", "Gross margin", p, "is.gross_profit", "is.revenue", sf,
                              "gross_profit / revenue", "Revenue"))
        else:
            out.append(MetricResult("gross_margin", VERSION, "Gross margin", p, "gross_profit / revenue", [], None, "ratio",
                                    NA, "Gross profit is not reported; not derived.", []))
        out.append(_ratio("current_ratio", "Current ratio", p, "bs.total_current_assets", "bs.total_current_liabilities",
                          sf, "total_current_assets / total_current_liabilities", "Current liabilities"))

        facts, problems = _need(sf, p, ["bs.total_current_assets", "bs.total_current_liabilities"])
        if problems:
            out.append(MetricResult("working_capital", VERSION, "Working capital", p,
                                    "total_current_assets - total_current_liabilities", [f.id for f in facts], None,
                                    "monetary", INSUFFICIENT, "Not computed: " + "; ".join(problems) + "."))
        else:
            out.append(MetricResult("working_capital", VERSION, "Working capital", p,
                                    "total_current_assets - total_current_liabilities", [f.id for f in facts],
                                    facts[0].value - facts[1].value, "monetary", COMPUTED,  # type: ignore[operator]
                                    f"{facts[0].value:f} - {facts[1].value:f}"))

        debt, dids, dlim, dprob = _borrowings(sf, p)
        eq = sf.get("bs.total_equity", p)
        formula = "(current_borrowings + non_current_borrowings) / total_equity"
        if dprob or eq is None or not eq.numeric:
            why = dprob + ([] if eq is not None and eq.numeric else ["bs.total_equity not usable"])
            out.append(MetricResult("debt_to_equity", VERSION, "Debt to equity", p, formula, dids, None, "ratio",
                                    INSUFFICIENT, "Not computed: " + "; ".join(why) + ".", dlim))
        elif eq.value <= 0:  # type: ignore[operator]
            out.append(MetricResult("debt_to_equity", VERSION, "Debt to equity", p, formula, dids + [eq.id], None, "ratio",
                                    SPECIAL, "Total equity is zero or negative; leverage ratio is not meaningful.", dlim))
        else:
            out.append(MetricResult("debt_to_equity", VERSION, "Debt to equity", p, formula, dids + [eq.id],
                                    debt / eq.value, "ratio", COMPUTED, f"{debt:f} / {eq.value:f}", dlim))  # type: ignore[operator]

        cash = sf.get("bs.cash_and_equivalents", p)
        formula = "current_borrowings + non_current_borrowings - cash_and_equivalents"
        if dprob or cash is None or not cash.numeric:
            why = dprob + ([] if cash is not None and cash.numeric else ["bs.cash_and_equivalents not usable"])
            out.append(MetricResult("net_debt", VERSION, "Net debt", p, formula, dids, None, "monetary", INSUFFICIENT,
                                    "Not computed: " + "; ".join(why) + ".", dlim + ["Excludes other bank balances."]))
        else:
            out.append(MetricResult("net_debt", VERSION, "Net debt", p, formula, dids + [cash.id], debt - cash.value,  # type: ignore[operator]
                                    "monetary", COMPUTED, f"{debt:f} - {cash.value:f}", dlim + ["Excludes other bank balances."]))

        out.append(_ratio("ocf_to_net_profit", "Operating cash flow / net profit", p, "cf.operating_cash_flow",
                          "is.net_profit", sf, "operating_cash_flow / net_profit", "Net profit"))

        facts, problems = _need(sf, p, ["cf.operating_cash_flow", "cf.capex"])
        formula = "operating_cash_flow - |purchase_of_property_plant_equipment|"
        lim = ["Capex = purchase of property, plant and equipment as reported in investing activities; "
               "excludes acquisitions and intangible purchases unless combined in the source line."]
        if problems:
            out.append(MetricResult("free_cash_flow", VERSION, "Free cash flow", p, formula, [f.id for f in facts], None,
                                    "monetary", INSUFFICIENT, "Not computed: " + "; ".join(problems) + ".", lim))
        else:
            ocf, capex = facts[0].value, facts[1].value
            assert ocf is not None and capex is not None
            out.append(MetricResult("free_cash_flow", VERSION, "Free cash flow", p, formula, [f.id for f in facts],
                                    ocf - abs(capex), "monetary", COMPUTED, f"{ocf:f} - |{capex:f}|", lim))
    return out
