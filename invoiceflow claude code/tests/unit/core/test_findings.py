from invoiceflow.core.findings import PRECEDENCE, Finding, FindingReason, primary_exception
from invoiceflow.data.models import ExceptionCode


def finding(code: ExceptionCode, reason: FindingReason) -> Finding:
    return Finding(code=code, reason=reason, message="test")


def test_no_findings_is_clean() -> None:
    assert primary_exception([]) is ExceptionCode.CLEAN


def test_precedence_covers_every_exception_except_clean() -> None:
    assert set(PRECEDENCE) == set(ExceptionCode) - {ExceptionCode.CLEAN}


def test_precedence_order_is_the_approved_one() -> None:
    assert PRECEDENCE == (
        ExceptionCode.VENDOR_BANK_CHANGE,
        ExceptionCode.DUPLICATE_INVOICE,
        ExceptionCode.PO_CLOSED,
        ExceptionCode.MISSING_GRN,
        ExceptionCode.QTY_OVERBILLED,
        ExceptionCode.PRICE_VARIANCE,
        ExceptionCode.GST_MISMATCH,
    )


def test_most_severe_finding_wins() -> None:
    findings = [
        finding(ExceptionCode.GST_MISMATCH, FindingReason.WRONG_TAX_TYPE),
        finding(ExceptionCode.DUPLICATE_INVOICE, FindingReason.EXACT_DUPLICATE),
        finding(ExceptionCode.PRICE_VARIANCE, FindingReason.PRICE_ABOVE_TOLERANCE),
    ]
    assert primary_exception(findings) is ExceptionCode.DUPLICATE_INVOICE
