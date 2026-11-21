"""Three-way match: invoice vs purchase order vs goods receipts, plus vendor and GST checks.

Pure function, no I/O. It reads only structured fields: invoice free text (notes, remarks,
line descriptions) is never consulted, so instructions hidden there cannot change a result.
Every problem found is returned; the primary exception code follows `PRECEDENCE`.
"""

from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from invoiceflow.core.duplicates import find_duplicates
from invoiceflow.core.findings import Finding, FindingReason, primary_exception
from invoiceflow.core.gst import check_gst
from invoiceflow.core.tolerance import PriceVariance, ToleranceParams, price_variance
from invoiceflow.data.models import (
    ExceptionCode,
    Frozen,
    GoodsReceipt,
    Invoice,
    Money,
    POStatus,
    PurchaseOrder,
    Vendor,
)


class MatchParams(Frozen):
    tolerance: ToleranceParams
    near_duplicate_window_days: int
    tax_amount_tolerance: Money


class MatchResult(Frozen):
    invoice_id: str
    primary: ExceptionCode
    findings: tuple[Finding, ...]
    price_variance: PriceVariance


class MatchInputError(ValueError):
    """The inputs do not describe one invoice against its own PO. Never guessed around."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def _check_inputs(
    invoice: Invoice, po: PurchaseOrder, grns: Sequence[GoodsReceipt], vendor: Vendor
) -> None:
    if invoice.po_id != po.po_id:
        raise MatchInputError("PO_MISMATCH", f"invoice references {invoice.po_id}, got {po.po_id}")
    if not invoice.vendor_id == po.vendor_id == vendor.vendor_id:
        raise MatchInputError(
            "VENDOR_MISMATCH",
            f"invoice {invoice.vendor_id}, PO {po.vendor_id}, vendor {vendor.vendor_id}",
        )
    for line in invoice.lines:
        if po.line(line.po_line_no) is None:
            raise MatchInputError(
                "UNKNOWN_PO_LINE", f"invoice line {line.line_no} bills PO line {line.po_line_no}"
            )
    for grn in grns:
        if grn.po_id != po.po_id:
            raise MatchInputError("GRN_PO_MISMATCH", f"{grn.grn_id} belongs to {grn.po_id}")


def _bank_findings(invoice: Invoice, vendor: Vendor) -> list[Finding]:
    if invoice.bank == vendor.bank:
        return []
    return [
        Finding(
            code=ExceptionCode.VENDOR_BANK_CHANGE,
            reason=FindingReason.BANK_DETAILS_DIFFER,
            message="bank details on the invoice differ from the vendor master",
            evidence={"invoice_account": invoice.bank.masked, "master_account": vendor.bank.masked},
        )
    ]


def _po_findings(invoice: Invoice, po: PurchaseOrder) -> list[Finding]:
    if po.status is POStatus.CLOSED:
        return [
            Finding(
                code=ExceptionCode.PO_CLOSED,
                reason=FindingReason.PO_STATUS_CLOSED,
                message=f"{po.po_id} is closed",
            )
        ]
    if invoice.invoice_date > po.valid_until:
        return [
            Finding(
                code=ExceptionCode.PO_CLOSED,
                reason=FindingReason.PO_EXPIRED,
                message=f"{po.po_id} expired on {po.valid_until.isoformat()}",
                evidence={
                    "valid_until": po.valid_until.isoformat(),
                    "invoice_date": invoice.invoice_date.isoformat(),
                },
            )
        ]
    return []


def _receipt_findings(
    invoice: Invoice, po: PurchaseOrder, grns: Sequence[GoodsReceipt]
) -> list[Finding]:
    received: dict[int, Decimal] = defaultdict(Decimal)
    for grn in grns:
        for grn_line in grn.lines:
            received[grn_line.po_line_no] += grn_line.quantity_received

    findings: list[Finding] = []
    for line in invoice.lines:
        po_line = po.line(line.po_line_no)
        if po_line is None:
            continue
        got = received[line.po_line_no]
        evidence = {
            "invoiced": str(line.quantity),
            "received": str(got),
            "ordered": str(po_line.quantity),
        }
        if got == 0:
            findings.append(
                Finding(
                    code=ExceptionCode.MISSING_GRN,
                    reason=FindingReason.NO_GOODS_RECEIPT,
                    message=f"no goods receipt for PO line {line.po_line_no}",
                    po_line_no=line.po_line_no,
                    evidence=evidence,
                )
            )
        elif line.quantity > got:
            over_order = line.quantity > po_line.quantity
            findings.append(
                Finding(
                    code=ExceptionCode.QTY_OVERBILLED,
                    reason=(
                        FindingReason.QTY_EXCEEDS_ORDERED
                        if over_order
                        else FindingReason.QTY_EXCEEDS_RECEIVED
                    ),
                    message=(
                        f"invoiced {line.quantity} on PO line {line.po_line_no}, "
                        f"received {got}, ordered {po_line.quantity}"
                    ),
                    po_line_no=line.po_line_no,
                    evidence=evidence,
                )
            )
    return findings


def match_invoice(
    invoice: Invoice,
    po: PurchaseOrder,
    grns: Sequence[GoodsReceipt],
    vendor: Vendor,
    prior_invoices: Sequence[Invoice],
    params: MatchParams,
) -> MatchResult:
    _check_inputs(invoice, po, grns, vendor)
    variance = price_variance(invoice, po, params.tolerance)

    findings = [
        *_bank_findings(invoice, vendor),
        *find_duplicates(invoice, prior_invoices, params.near_duplicate_window_days),
        *_po_findings(invoice, po),
        *_receipt_findings(invoice, po, grns),
    ]
    if not variance.within_tolerance:
        findings.append(
            Finding(
                code=ExceptionCode.PRICE_VARIANCE,
                reason=FindingReason.PRICE_ABOVE_TOLERANCE,
                message=(
                    f"overcharge {variance.overcharge_amount} is {variance.overcharge_pct}% "
                    f"of {variance.base_amount}"
                ),
                evidence={
                    "overcharge_amount": str(variance.overcharge_amount),
                    "overcharge_pct": str(variance.overcharge_pct),
                    "base_amount": str(variance.base_amount),
                },
            )
        )
    findings.extend(check_gst(invoice, po, vendor, params.tax_amount_tolerance))

    return MatchResult(
        invoice_id=invoice.invoice_id,
        primary=primary_exception(findings),
        findings=tuple(findings),
        price_variance=variance,
    )
