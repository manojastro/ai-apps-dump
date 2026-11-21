import unittest
from decimal import Decimal
from app.decisions import InvoiceFacts, evaluate_invoice

class InvoiceDecisionTests(unittest.TestCase):
    def test_mismatch_requires_review(self):
        decision = evaluate_invoice(InvoiceFacts(Decimal('120.00'), Decimal('100.00'), True))
        self.assertEqual(decision.outcome, 'ESCALATE_FOR_REVIEW')
        self.assertTrue(decision.approval_required)

    def test_missing_receipt_blocks_payment(self):
        decision = evaluate_invoice(InvoiceFacts(Decimal('100.00'), Decimal('100.00'), False))
        self.assertEqual(decision.reason, 'Goods receipt missing')

    def test_matched_invoice_never_invents_payment_date(self):
        decision = evaluate_invoice(InvoiceFacts(Decimal('100.00'), Decimal('100.00'), True))
        self.assertIsNone(decision.confirmed_payment_date)
        self.assertTrue(decision.approval_required)
