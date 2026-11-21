"""What the deterministic checks found, and which finding decides the exception code."""

from collections.abc import Iterable
from enum import StrEnum

from pydantic import Field

from invoiceflow.data.models import ExceptionCode, Frozen


class FindingReason(StrEnum):
    BANK_DETAILS_DIFFER = "BANK_DETAILS_DIFFER"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    PO_STATUS_CLOSED = "PO_STATUS_CLOSED"
    PO_EXPIRED = "PO_EXPIRED"
    NO_GOODS_RECEIPT = "NO_GOODS_RECEIPT"
    QTY_EXCEEDS_RECEIVED = "QTY_EXCEEDS_RECEIVED"
    QTY_EXCEEDS_ORDERED = "QTY_EXCEEDS_ORDERED"
    PRICE_ABOVE_TOLERANCE = "PRICE_ABOVE_TOLERANCE"
    GSTIN_INVALID = "GSTIN_INVALID"
    GSTIN_NOT_ON_VENDOR_MASTER = "GSTIN_NOT_ON_VENDOR_MASTER"
    WRONG_TAX_TYPE = "WRONG_TAX_TYPE"
    GST_RATE_MISMATCH = "GST_RATE_MISMATCH"
    TAX_AMOUNT_MISMATCH = "TAX_AMOUNT_MISMATCH"


class Finding(Frozen):
    code: ExceptionCode
    reason: FindingReason
    message: str
    po_line_no: int | None = None
    evidence: dict[str, str] = Field(default_factory=dict)


# Most severe first (approved Phase 1 interpretation 7): stop-payment risks come first.
PRECEDENCE: tuple[ExceptionCode, ...] = (
    ExceptionCode.VENDOR_BANK_CHANGE,
    ExceptionCode.DUPLICATE_INVOICE,
    ExceptionCode.PO_CLOSED,
    ExceptionCode.MISSING_GRN,
    ExceptionCode.QTY_OVERBILLED,
    ExceptionCode.PRICE_VARIANCE,
    ExceptionCode.GST_MISMATCH,
)


def primary_exception(findings: Iterable[Finding]) -> ExceptionCode:
    codes = {finding.code for finding in findings}
    return next((code for code in PRECEDENCE if code in codes), ExceptionCode.CLEAN)
