"""GST checks: GSTIN validity, tax type for the place of supply, rate vs PO, tax arithmetic.

Supply within one state is taxed as CGST + SGST (half the rate each); supply across states
is taxed as IGST (the full rate). The supplier's state comes from the vendor master and the
place of supply from the PO, because the PO is the authority on where goods are delivered.
"""

from decimal import Decimal
from enum import StrEnum

from invoiceflow.core.findings import Finding, FindingReason
from invoiceflow.core.gstin import validate_gstin
from invoiceflow.core.money import to_money
from invoiceflow.data.models import ExceptionCode, Invoice, PurchaseOrder, Vendor

ZERO = Decimal("0.00")


class TaxType(StrEnum):
    INTRA_STATE = "INTRA_STATE"
    INTER_STATE = "INTER_STATE"


def tax_type_for(supplier_state: str, place_of_supply: str) -> TaxType:
    return TaxType.INTRA_STATE if supplier_state == place_of_supply else TaxType.INTER_STATE


def compute_line_tax(
    taxable_value: Decimal, gst_rate: Decimal, tax_type: TaxType
) -> tuple[Decimal, Decimal, Decimal]:
    """(CGST, SGST, IGST), each rounded to paise on its own."""
    if tax_type is TaxType.INTRA_STATE:
        half = to_money(taxable_value * gst_rate / 200)
        return half, half, ZERO
    return ZERO, ZERO, to_money(taxable_value * gst_rate / 100)


def _gst_finding(
    reason: FindingReason, message: str, po_line_no: int | None = None, **evidence: str
) -> Finding:
    return Finding(
        code=ExceptionCode.GST_MISMATCH,
        reason=reason,
        message=message,
        po_line_no=po_line_no,
        evidence=evidence,
    )


def check_gst(
    invoice: Invoice, po: PurchaseOrder, vendor: Vendor, tax_amount_tolerance: Decimal
) -> list[Finding]:
    findings: list[Finding] = []

    gstin = validate_gstin(invoice.supplier_gstin)
    if not gstin.valid:
        findings.append(
            _gst_finding(
                FindingReason.GSTIN_INVALID,
                f"supplier GSTIN on the invoice is invalid: {gstin.detail}",
                gstin=invoice.supplier_gstin,
                failure=str(gstin.failure),
            )
        )
    if invoice.supplier_gstin != vendor.gstin:
        findings.append(
            _gst_finding(
                FindingReason.GSTIN_NOT_ON_VENDOR_MASTER,
                "supplier GSTIN on the invoice differs from the vendor master",
                invoice_gstin=invoice.supplier_gstin,
                master_gstin=vendor.gstin,
            )
        )

    tax_type = tax_type_for(vendor.state_code, po.place_of_supply)
    for line in invoice.lines:
        po_line = po.line(line.po_line_no)
        if po_line is not None and line.gst_rate != po_line.gst_rate:
            findings.append(
                _gst_finding(
                    FindingReason.GST_RATE_MISMATCH,
                    f"GST rate {line.gst_rate}% differs from the PO rate {po_line.gst_rate}%",
                    line.po_line_no,
                    invoice_rate=str(line.gst_rate),
                    po_rate=str(po_line.gst_rate),
                )
            )

        charged_intra = line.cgst != ZERO or line.sgst != ZERO
        charged_inter = line.igst != ZERO
        right_type = (
            (charged_intra and not charged_inter)
            if tax_type is TaxType.INTRA_STATE
            else (charged_inter and not charged_intra)
        )
        if not right_type:
            findings.append(
                _gst_finding(
                    FindingReason.WRONG_TAX_TYPE,
                    f"{tax_type.value} supply must be taxed as "
                    + ("CGST + SGST" if tax_type is TaxType.INTRA_STATE else "IGST"),
                    line.po_line_no,
                    expected=tax_type.value,
                    supplier_state=vendor.state_code,
                    place_of_supply=po.place_of_supply,
                )
            )
            continue

        expected = compute_line_tax(line.taxable_value, line.gst_rate, tax_type)
        charged = (line.cgst, line.sgst, line.igst)
        if any(abs(c - e) > tax_amount_tolerance for c, e in zip(charged, expected, strict=True)):
            findings.append(
                _gst_finding(
                    FindingReason.TAX_AMOUNT_MISMATCH,
                    "tax amounts do not match the taxable value and rate",
                    line.po_line_no,
                    charged="/".join(str(c) for c in charged),
                    expected="/".join(str(e) for e in expected),
                )
            )
    return findings
