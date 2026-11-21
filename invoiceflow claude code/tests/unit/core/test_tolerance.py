from decimal import Decimal as D

import pytest

import builders as b
from invoiceflow.core.tolerance import PriceVariance, ToleranceParams, price_variance

PARAMS = ToleranceParams(max_pct=D("2.00"), max_amount=D("5000.00"))


def variance(po_price: str, inv_price: str, qty: str = "100") -> PriceVariance:
    po = b.purchase_order(lines=(b.po_line(qty=qty, price=po_price),))
    inv = b.invoice(lines=(b.invoice_line(qty=qty, price=inv_price),))
    return price_variance(inv, po, PARAMS)


def test_no_price_change_is_zero_variance() -> None:
    pv = variance("100.00", "100.00")
    assert pv.overcharge_amount == D("0.00")
    assert pv.within_tolerance


@pytest.mark.parametrize(
    ("inv_price", "pct", "within"),
    [("102.00", "2.0000", True), ("102.01", "2.0100", False)],
)
def test_percentage_boundary_is_inclusive(inv_price: str, pct: str, within: bool) -> None:
    # Base = 100 x 100.00 = 10,000; 2% = 200.
    pv = variance("100.00", inv_price)
    assert pv.overcharge_pct == D(pct)
    assert pv.within_tolerance is within


@pytest.mark.parametrize(("inv_price", "within"), [("305000.00", True), ("305000.01", False)])
def test_amount_boundary_is_inclusive(inv_price: str, within: bool) -> None:
    # One unit at 3,00,000: a 5,000 overcharge is only 1.67%, so the amount limit decides.
    pv = variance("300000.00", inv_price, qty="1")
    assert pv.overcharge_pct < D("2")
    assert pv.within_tolerance is within


def test_both_limits_at_their_boundary_at_once_is_within() -> None:
    pv = variance("250.00", "255.00", qty="1000")  # 5,000.00 and exactly 2.00%
    assert (pv.overcharge_amount, pv.overcharge_pct) == (D("5000.00"), D("2.0000"))
    assert pv.within_tolerance


def test_undercharge_is_not_a_variance() -> None:
    pv = variance("100.00", "90.00")
    assert pv.overcharge_amount == D("0.00")
    assert pv.within_tolerance


def test_only_overcharged_lines_count_but_base_covers_all_lines() -> None:
    po = b.purchase_order(
        lines=(b.po_line(1, qty="10", price="100.00"), b.po_line(2, qty="10", price="100.00"))
    )
    inv = b.invoice(
        lines=(
            b.invoice_line(1, qty="10", price="110.00"),  # +100
            b.invoice_line(2, qty="10", price="50.00"),  # undercharge ignored
        )
    )
    pv = price_variance(inv, po, PARAMS)
    assert pv.overcharge_amount == D("100.00")
    assert pv.base_amount == D("2000.00")
    assert pv.overcharge_pct == D("5.0000")
    assert not pv.within_tolerance
