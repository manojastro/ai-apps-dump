"""Price variance against the PO, measured per invoice (approved interpretations 1 and 2).

Overcharge = sum over lines of max(0, invoiced unit price - PO unit price) x invoiced qty.
Base = sum over lines of PO unit price x invoiced qty. Undercharges are not a variance.
Within tolerance means overcharge <= max_amount AND overcharge % <= max_pct (both inclusive).
"""

from decimal import Decimal

from invoiceflow.core.money import percent_of, to_money
from invoiceflow.data.models import Frozen, Invoice, Money, PurchaseOrder


class ToleranceParams(Frozen):
    max_pct: Decimal
    max_amount: Money


class PriceVariance(Frozen):
    overcharge_amount: Money
    base_amount: Money
    overcharge_pct: Decimal
    within_tolerance: bool


def price_variance(invoice: Invoice, po: PurchaseOrder, params: ToleranceParams) -> PriceVariance:
    overcharge = Decimal("0")
    base = Decimal("0")
    for line in invoice.lines:
        po_line = po.line(line.po_line_no)
        if po_line is None:
            continue  # the matcher rejects unknown PO lines before pricing
        base += po_line.unit_price * line.quantity
        overcharge += max(Decimal("0"), line.unit_price - po_line.unit_price) * line.quantity
    overcharge_amount, base_amount = to_money(overcharge), to_money(base)
    pct = percent_of(overcharge_amount, base_amount)
    return PriceVariance(
        overcharge_amount=overcharge_amount,
        base_amount=base_amount,
        overcharge_pct=pct,
        within_tolerance=overcharge_amount <= params.max_amount and pct <= params.max_pct,
    )
