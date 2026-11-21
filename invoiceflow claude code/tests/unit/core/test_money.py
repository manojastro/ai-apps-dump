from decimal import Decimal as D

import pytest

from invoiceflow.core.money import format_inr, percent_of, to_money, to_quantity


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("10.005", "10.01"), ("10.004", "10.00"), ("-10.005", "-10.01"), ("7", "7.00")],
)
def test_to_money_rounds_half_up_to_paise(raw: str, expected: str) -> None:
    assert to_money(D(raw)) == D(expected)
    assert str(to_money(D(raw))) == expected


def test_to_quantity_keeps_three_decimals() -> None:
    assert str(to_quantity(D("2.0005"))) == "2.001"


@pytest.mark.parametrize(
    ("part", "whole", "expected"),
    [("2", "100", "2.0000"), ("1", "3", "33.3333"), ("5", "0", "0.0000")],
)
def test_percent_of(part: str, whole: str, expected: str) -> None:
    assert percent_of(D(part), D(whole)) == D(expected)


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("0", "₹0.00"),
        ("999.5", "₹999.50"),
        ("5000", "₹5,000.00"),
        ("100000", "₹1,00,000.00"),
        ("1000000", "₹10,00,000.00"),
        ("123456789.01", "₹12,34,56,789.01"),
        ("-100000", "-₹1,00,000.00"),
    ],
)
def test_format_inr_uses_indian_grouping(amount: str, expected: str) -> None:
    assert format_inr(D(amount)) == expected
