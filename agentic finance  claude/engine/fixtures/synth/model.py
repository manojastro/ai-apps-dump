"""Synthetic company model. Fictional: 'Aravalli Polymers Limited' (no relation to any real company).

All totals are computed from components with Decimal, and balancing figures are derived so that the
three statements are internally consistent across two annual periods:
  * dividends make closing cash equal balance-sheet cash,
  * other equity rolls forward (opening + profit - dividends),
  * other current liabilities balance the balance sheet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal as D

FY25, FY24 = date(2025, 3, 31), date(2024, 3, 31)
PERIODS = [FY25, FY24]


@dataclass
class Row:
    label: str
    kind: str = "item"  # header | item | total
    level: int = 1
    note: str | None = None
    code: str | None = None
    values: dict[date, D | str | None] = field(default_factory=dict)  # str = raw override (e.g. unreadable)


@dataclass
class StatementSpec:
    statement_type: str
    title: str
    rows: list[Row]


def _sum(*xs: D) -> D:
    return sum(xs, D("0"))


BASE_INPUTS = {
    FY25: dict(ppe=D("1245.60"), cwip=D("86.40"), intang=D("34.75"), nci=D("120.00"), onca=D("45.30"),
               inv=D("412.80"), tr=D("538.25"), cash=D("96.45"), obb=D("28.00"), oca=D("63.15"),
               sc=D("150.00"), ncb=D("385.20"), dtl=D("62.35"), oncl=D("24.15"), cb=D("168.90"), tp=D("402.75"),
               rev=D("3842.60"), oi=D("24.80"), com=D("2305.55"), emp=D("384.25"), fin=D("52.40"), dep=D("118.70"),
               oth=D("612.10"), ctax=D("92.15"), dtax=D("6.55"),
               intinc=D("12.30"), dinv=D("47.40"), dtr=D("66.35"), dtp=D("46.55"), dol=D("52.90"), taxpaid=D("85.80"),
               capex=D("218.55"), sale=D("4.20"), pinv=D("10.00"), intrec=D("12.30"), dobb=D("3.00"),
               ncbnet=D("-25.40"), cbnet=D("26.60")),
    FY24: dict(ppe=D("1180.25"), cwip=D("52.10"), intang=D("38.20"), nci=D("110.00"), onca=D("41.70"),
               inv=D("365.40"), tr=D("471.90"), cash=D("74.30"), obb=D("25.00"), oca=D("58.65"),
               sc=D("150.00"), ncb=D("410.60"), dtl=D("55.80"), oncl=D("22.40"), cb=D("142.30"), tp=D("356.20"),
               rev=D("3415.20"), oi=D("19.60"), com=D("2083.30"), emp=D("345.10"), fin=D("49.80"), dep=D("109.40"),
               oth=D("536.20"), ctax=D("72.40"), dtax=D("5.10"),
               intinc=D("9.80"), dinv=D("30.10"), dtr=D("52.40"), dtp=D("28.70"), dol=D("12.10"), taxpaid=D("70.15"),
               capex=D("176.40"), sale=D("3.10"), pinv=D("15.00"), intrec=D("9.80"), dobb=D("2.00"),
               ncbnet=D("-30.20"), cbnet=D("18.30")),
}
OPENING_OTHER_EQUITY = D("1010.00")  # other equity at 31 March 2023
OPENING_CASH = D("72.95")  # cash at 31 March 2023


def build_company(scale_factor: D = D("1"), inputs: dict | None = None, opening_oe: D = OPENING_OTHER_EQUITY,
                  opening_cash: D = OPENING_CASH, periods: list[date] | None = None, title_date: str = "31 March 2025") -> dict:
    """Return {'bs','is','cf'} StatementSpecs plus computed values. `periods` newest first."""
    f = scale_factor
    periods = periods or PERIODS
    a = {p: dict(v) for p, v in (inputs or BASE_INPUTS).items()}
    opening_other_equity, opening_cash_first = opening_oe, opening_cash
    if f != 1:
        for p in a:
            a[p] = {k: (x * f).quantize(D("0.01")) for k, x in a[p].items()}
        opening_other_equity = (opening_other_equity * f).quantize(D("0.01"))
        opening_cash_first = (opening_cash_first * f).quantize(D("0.01"))
    opening_cash_fy24 = opening_cash_first

    c: dict[date, dict[str, D]] = {}
    prev_oe = opening_other_equity
    prev_cash = opening_cash_fy24
    for p in sorted(periods):
        x = dict(a[p])
        x["tnca"] = _sum(x["ppe"], x["cwip"], x["intang"], x["nci"], x["onca"])
        x["tca"] = _sum(x["inv"], x["tr"], x["cash"], x["obb"], x["oca"])
        x["ta"] = x["tnca"] + x["tca"]
        x["ti"] = x["rev"] + x["oi"]
        x["te"] = _sum(x["com"], x["emp"], x["fin"], x["dep"], x["oth"])
        x["pbt"] = x["ti"] - x["te"]
        x["tax"] = x["ctax"] + x["dtax"]
        x["pat"] = x["pbt"] - x["tax"]
        x["eps"] = (x["pat"] / D("15")).quantize(D("0.01"))
        x["opbwc"] = x["pbt"] + x["dep"] + x["fin"] - x["intinc"]
        x["cgo"] = x["opbwc"] - x["dinv"] - x["dtr"] + x["dtp"] + x["dol"]
        x["ocf"] = x["cgo"] - x["taxpaid"]
        x["icf"] = -x["capex"] + x["sale"] - x["pinv"] + x["intrec"] - x["dobb"]
        x["open"] = prev_cash
        x["net"] = x["cash"] - x["open"]
        # dividends balance the cash flow: financing = net - ocf - icf
        fcf_total = x["net"] - x["ocf"] - x["icf"]
        x["div"] = x["ncbnet"] + x["cbnet"] - x["fin"] - fcf_total  # positive amount paid
        x["fcf"] = fcf_total
        x["oe"] = prev_oe + x["pat"] - x["div"]
        x["teq"] = x["sc"] + x["oe"]
        x["tncl"] = _sum(x["ncb"], x["dtl"], x["oncl"])
        x["ocl"] = x["ta"] - x["teq"] - x["tncl"] - x["cb"] - x["tp"]
        x["tcl"] = _sum(x["cb"], x["tp"], x["ocl"])
        x["tel"] = x["teq"] + x["tncl"] + x["tcl"]
        assert x["tel"] == x["ta"]
        assert x["div"] > 0, x["div"]
        c[p] = x
        prev_oe, prev_cash = x["oe"], x["cash"]

    def vals(key: str, sign: int = 1) -> dict[date, D]:
        return {p: sign * c[p][key] for p in periods}

    bs = StatementSpec("balance_sheet", f"Balance Sheet as at {title_date}", [
        Row("ASSETS", "header", 0),
        Row("Non-current assets", "header", 0),
        Row("Property, plant and equipment", note="3", code="bs.property_plant_equipment", values=vals("ppe")),
        Row("Capital work-in-progress", code="bs.capital_work_in_progress", values=vals("cwip")),
        Row("Intangible assets", code="bs.intangible_assets", values=vals("intang")),
        Row("Non-current investments", note="4", code="bs.non_current_investments", values=vals("nci")),
        Row("Other non-current assets", code="bs.other_non_current_assets", values=vals("onca")),
        Row("Total non-current assets", "total", 0, code="bs.total_non_current_assets", values=vals("tnca")),
        Row("Current assets", "header", 0),
        Row("Inventories", note="5", code="bs.inventories", values=vals("inv")),
        Row("Trade receivables", note="6", code="bs.trade_receivables", values=vals("tr")),
        Row("Cash and cash equivalents", note="7", code="bs.cash_and_equivalents", values=vals("cash")),
        Row("Other bank balances", note="7", code="bs.other_bank_balances", values=vals("obb")),
        Row("Other current assets", code="bs.other_current_assets", values=vals("oca")),
        Row("Total current assets", "total", 0, code="bs.total_current_assets", values=vals("tca")),
        Row("Total assets", "total", 0, code="bs.total_assets", values=vals("ta")),
        Row("EQUITY AND LIABILITIES", "header", 0),
        Row("Equity", "header", 0),
        Row("Equity share capital", code="bs.share_capital", values=vals("sc")),
        Row("Other equity", code="bs.other_equity", values=vals("oe")),
        Row("Total equity", "total", 0, code="bs.total_equity", values=vals("teq")),
        Row("Non-current liabilities", "header", 0),
        Row("Borrowings", note="8", code="bs.non_current_borrowings", values=vals("ncb")),
        Row("Deferred tax liabilities (net)", code="bs.deferred_tax_liabilities", values=vals("dtl")),
        Row("Other non-current liabilities", code="bs.other_non_current_liabilities", values=vals("oncl")),
        Row("Total non-current liabilities", "total", 0, code="bs.total_non_current_liabilities", values=vals("tncl")),
        Row("Current liabilities", "header", 0),
        Row("Borrowings", note="8", code="bs.current_borrowings", values=vals("cb")),
        Row("Trade payables", code="bs.trade_payables", values=vals("tp")),
        Row("Other current liabilities", code="bs.other_current_liabilities", values=vals("ocl")),
        Row("Total current liabilities", "total", 0, code="bs.total_current_liabilities", values=vals("tcl")),
        Row("Total equity and liabilities", "total", 0, code="bs.total_equity_and_liabilities", values=vals("tel")),
    ])
    is_ = StatementSpec("income_statement", f"Statement of Profit and Loss for the year ended {title_date}", [
        Row("Income", "header", 0),
        Row("Revenue from operations", note="9", code="is.revenue", values=vals("rev")),
        Row("Other income", code="is.other_income", values=vals("oi")),
        Row("Total income", "total", 0, code="is.total_income", values=vals("ti")),
        Row("Expenses", "header", 0),
        Row("Cost of materials consumed", code="is.cost_of_sales", values=vals("com")),
        Row("Employee benefits expense", code="is.employee_benefits", values=vals("emp")),
        Row("Finance costs", note="10", code="is.finance_costs", values=vals("fin")),
        Row("Depreciation and amortisation expense", code="is.depreciation_amortisation", values=vals("dep")),
        Row("Other expenses", code="is.other_expenses", values=vals("oth")),
        Row("Total expenses", "total", 0, code="is.total_expenses", values=vals("te")),
        Row("Profit before tax", "total", 0, code="is.profit_before_tax", values=vals("pbt")),
        Row("Tax expense", "header", 0),
        Row("Current tax", code="is.current_tax", values=vals("ctax")),
        Row("Deferred tax", code="is.deferred_tax", values=vals("dtax")),
        Row("Total tax expense", "total", 0, code="is.tax_expense", values=vals("tax")),
        Row("Profit for the year", "total", 0, code="is.net_profit", values=vals("pat")),
        Row("Earnings per equity share (face value Rs 10 each)", "header", 0),
        Row("Basic (in Rs)", code="is.eps_basic", values=vals("eps")),
        Row("Diluted (in Rs)", code="is.eps_diluted", values=vals("eps")),
    ])
    cf = StatementSpec("cash_flow", f"Statement of Cash Flows for the year ended {title_date}", [
        Row("Cash flows from operating activities", "header", 0),
        Row("Profit before tax", code=None, values=vals("pbt")),
        Row("Depreciation and amortisation", values=vals("dep")),
        Row("Finance costs", values=vals("fin")),
        Row("Interest income", values=vals("intinc", -1)),
        Row("Operating profit before working capital changes", values=vals("opbwc")),
        Row("(Increase) in inventories", values=vals("dinv", -1)),
        Row("(Increase) in trade receivables", values=vals("dtr", -1)),
        Row("Increase in trade payables", values=vals("dtp")),
        Row("Increase in other liabilities", values=vals("dol")),
        Row("Cash generated from operations", values=vals("cgo")),
        Row("Income taxes paid (net)", values=vals("taxpaid", -1)),
        Row("Net cash from operating activities", "total", 0, code="cf.operating_cash_flow", values=vals("ocf")),
        Row("Cash flows from investing activities", "header", 0),
        Row("Purchase of property, plant and equipment", code="cf.capex", values=vals("capex", -1)),
        Row("Proceeds from sale of property, plant and equipment", values=vals("sale")),
        Row("Purchase of investments", values=vals("pinv", -1)),
        Row("Interest received", values=vals("intrec")),
        Row("Increase in other bank balances", values=vals("dobb", -1)),
        Row("Net cash used in investing activities", "total", 0, code="cf.investing_cash_flow", values=vals("icf")),
        Row("Cash flows from financing activities", "header", 0),
        Row("Repayment of non-current borrowings (net)", values=vals("ncbnet")),
        Row("Proceeds from current borrowings (net)", values=vals("cbnet")),
        Row("Finance costs paid", values=vals("fin", -1)),
        Row("Dividends paid", values=vals("div", -1)),
        Row("Net cash used in financing activities", "total", 0, code="cf.financing_cash_flow", values=vals("fcf")),
        Row("Net increase in cash and cash equivalents", "total", 0, code="cf.net_change_in_cash", values=vals("net")),
        Row("Cash and cash equivalents at the beginning of the year", code="cf.opening_cash", values=vals("open")),
        Row("Cash and cash equivalents at the end of the year", "total", 0, code="cf.closing_cash", values=vals("cash")),
    ])
    return {"bs": bs, "is": is_, "cf": cf, "computed": c}


NOTES = [
    ("3", "Property, plant and equipment",
     "Gross block, accumulated depreciation and net carrying amounts by asset class. Freehold land is not depreciated."),
    ("7", "Cash and cash equivalents",
     "Cash and cash equivalents comprise balances with banks in current accounts and deposits with original maturity of "
     "three months or less. Other bank balances are deposits with maturity of more than three months and are excluded."),
    ("8", "Borrowings",
     "Non-current borrowings are secured term loans from banks repayable over five years. Current borrowings are "
     "working capital loans repayable on demand. Current maturities of long-term debt are included in current borrowings."),
    ("9", "Revenue from operations", "Revenue comprises sale of polymer products and related services, net of discounts."),
]


def ground_truth(spec: dict, scope: str, scale: str = "crores", doc_id: str = "") -> list[dict]:
    """Expected canonical observations: one per (code, period)."""
    out = []
    for key in ("bs", "is", "cf"):
        st: StatementSpec = spec[key]
        for r in st.rows:
            if r.kind == "header" or r.code is None:
                continue
            for p, val in r.values.items():
                if isinstance(val, D):
                    out.append({"code": r.code, "period_end": p.isoformat(), "value": format(val, "f"), "scale": scale,
                                "statement_type": st.statement_type, "scope": scope, "label": r.label, "doc": doc_id})
    return out
