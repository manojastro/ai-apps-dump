from datetime import date, timedelta

import pytest

import builders as b
from invoiceflow.core.duplicates import find_duplicates, normalize_invoice_number
from invoiceflow.core.findings import FindingReason
from invoiceflow.data.models import ExceptionCode, Invoice, InvoiceLine

WINDOW = 7


@pytest.mark.parametrize(
    "variant", ["CF-2026-0042", "cf/2026/42", "CF 2026 042", "CF2026-0042", " cf_2026_0042 "]
)
def test_format_variants_normalize_to_the_same_number(variant: str) -> None:
    assert normalize_invoice_number(variant) == "CF202642"


def test_digits_glued_to_each_other_are_a_different_number() -> None:
    # Documented limitation: without a separator, "2026" and "0042" become one digit run.
    assert normalize_invoice_number("CF20260042") != normalize_invoice_number("CF-2026-0042")


def prior(
    number: str, days_before: int = 3, lines: tuple[InvoiceLine, ...] | None = None
) -> Invoice:
    current = b.invoice()
    return b.invoice(
        invoice_id="INV-0000",
        invoice_number=number,
        invoice_date=current.invoice_date - timedelta(days=days_before),
        received_date=current.received_date - timedelta(days=days_before),
        lines=lines,
    )


def test_same_number_is_an_exact_duplicate_at_any_date() -> None:
    findings = find_duplicates(b.invoice(), [prior("CF-2026-0042", days_before=60)], WINDOW)
    assert [f.reason for f in findings] == [FindingReason.EXACT_DUPLICATE]
    assert findings[0].code is ExceptionCode.DUPLICATE_INVOICE
    assert findings[0].evidence["prior_invoice_id"] == "INV-0000"


def test_reformatted_number_is_an_exact_duplicate() -> None:
    findings = find_duplicates(b.invoice(), [prior("cf/2026/42", days_before=60)], WINDOW)
    assert [f.reason for f in findings] == [FindingReason.EXACT_DUPLICATE]


@pytest.mark.parametrize(("days", "flagged"), [(7, True), (8, False)])
def test_near_duplicate_window_is_inclusive(days: int, flagged: bool) -> None:
    findings = find_duplicates(b.invoice(), [prior("CF-2026-0099", days_before=days)], WINDOW)
    assert ([f.reason for f in findings] == [FindingReason.NEAR_DUPLICATE]) is flagged


def test_near_duplicate_needs_the_same_gross_amount() -> None:
    different_amount = prior("CF-2026-0099", lines=(b.invoice_line(qty="11"),))
    assert find_duplicates(b.invoice(), [different_amount], WINDOW) == []


def test_other_vendors_invoices_are_ignored() -> None:
    other = prior("CF-2026-0042").model_copy(update={"vendor_id": "V999"})
    assert find_duplicates(b.invoice(), [other], WINDOW) == []


def test_the_invoice_itself_and_later_invoices_are_not_prior() -> None:
    current = b.invoice()
    later = current.model_copy(
        update={"invoice_id": "INV-0009", "received_date": date(2026, 6, 30)}
    )
    assert find_duplicates(current, [current, later], WINDOW) == []
