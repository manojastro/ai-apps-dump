"""Deterministic invoice decisions. All writes and outbound messages require approval."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass(frozen=True)
class InvoiceFacts:
    invoice_amount: Decimal
    purchase_order_amount: Decimal
    goods_received: bool
    confirmed_payment_date: date | None = None

@dataclass(frozen=True)
class InvoiceDecision:
    outcome: str
    reason: str
    approval_required: bool
    confirmed_payment_date: date | None

def evaluate_invoice(facts: InvoiceFacts) -> InvoiceDecision:
    if not isinstance(facts.invoice_amount, Decimal) or not isinstance(facts.purchase_order_amount, Decimal):
        raise TypeError('Amounts must be Decimal')
    if not facts.invoice_amount.is_finite() or not facts.purchase_order_amount.is_finite() or min(facts.invoice_amount, facts.purchase_order_amount) < 0:
        raise ValueError('Amounts must be finite and non-negative')
    if not facts.goods_received:
        return InvoiceDecision('ESCALATE_FOR_REVIEW', 'Goods receipt missing', True, None)
    if facts.invoice_amount != facts.purchase_order_amount:
        return InvoiceDecision('ESCALATE_FOR_REVIEW', 'Invoice amount does not match purchase order', True, None)
    return InvoiceDecision('REVIEW_RESPONSE', 'Invoice matches purchase order and receipt', True, facts.confirmed_payment_date)
