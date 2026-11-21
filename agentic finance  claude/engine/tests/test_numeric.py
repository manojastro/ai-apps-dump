from decimal import Decimal

import pytest

from spreadlens.numeric.decimal_utils import excel_safe, group_indian
from spreadlens.numeric.parse import ParseContext, parse_number
from spreadlens.numeric.scale import SCALE_FACTORS, detect_currency, detect_scale, half_unit, to_base_units


@pytest.mark.parametrize("raw,state,value,decimals", [
    ("1,234.56", "value", "1234.56", 2),
    ("12,34,567.89", "value", "1234567.89", 2),       # Indian grouping
    ("1,234,567", "value", "1234567", 0),             # international grouping
    ("(1,234.50)", "value", "-1234.50", 2),           # parentheses negative
    ("1,234-", "value", "-1234", 0),                  # trailing minus
    ("-45", "value", "-45", 0),
    ("0", "zero", "0", 0),
    ("0.00", "zero", "0", 2),
    ("", "missing", None, None),
    ("-", "dash_ambiguous", None, None),
    ("—", "dash_ambiguous", None, None),
    ("n/a", "not_applicable", None, None),
    ("1,2O4", "unreadable", None, None),              # OCR letter O
    ("12,3456", "unreadable", None, None),            # broken grouping
    ("1.2.3", "unreadable", None, None),
    ("(12", "unreadable", None, None),
    ("₹ 1,000", "value", "1000", 0),
])
def test_parse_number(raw, state, value, decimals):
    p = parse_number(raw)
    assert p.state == state
    if value is None:
        assert p.value is None
    else:
        assert p.value == Decimal(value)
        assert p.decimals == decimals


def test_dash_zero_only_when_document_says_so():
    assert parse_number("-", ParseContext(dash_means_zero=True)).state == "zero"
    assert parse_number("-").state == "dash_ambiguous"


def test_percent_unit_hint():
    p = parse_number("12.5%")
    assert p.value == Decimal("12.5") and p.unit_hint == "percent"


def test_exact_scale_factors():
    assert to_base_units(Decimal("1.23"), "crores") == Decimal("12300000.00")
    assert to_base_units(Decimal("4.5"), "lakhs") == Decimal("450000.0")
    assert SCALE_FACTORS["millions"] == Decimal(10) ** 6
    # Exactness: no binary floating point drift
    assert to_base_units(Decimal("0.1"), "units") + to_base_units(Decimal("0.2"), "units") == Decimal("0.3")


def test_half_unit():
    assert half_unit(2, "crores") == Decimal("50000")  # 0.005 crore
    assert half_unit(0, "lakhs") == Decimal("50000")


def test_detect_scale_and_conflict():
    assert detect_scale("(All amounts in ₹ crores, unless otherwise stated)").value == "crores"
    assert detect_scale("Amounts in ₹ lakhs").value == "lakhs"
    assert detect_scale("(USD in thousands)").value == "thousands"
    d = detect_scale("Amounts in ₹ crores\nNote: amounts in ₹ lakhs")
    assert d.value is None and set(d.conflicts) == {"crores", "lakhs"}


def test_detect_currency():
    assert detect_currency("All amounts in ₹ crores").value == "INR"
    assert detect_currency("Amounts in USD millions").value == "USD"
    assert detect_currency("no currency here").value is None


def test_indian_grouping_display_and_excel_precision():
    assert group_indian(Decimal("1234567.891")) == "12,34,567.89"
    assert group_indian(Decimal("-1000")) == "(1,000.00)"
    assert excel_safe(Decimal("123456789012345"))
    assert not excel_safe(Decimal("1234567890123456.78"))
