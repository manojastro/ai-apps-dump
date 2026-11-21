from decimal import Decimal as D

import pytest

import builders as b
from invoiceflow.core.findings import Finding, FindingReason
from invoiceflow.core.gst import TaxType, check_gst, compute_line_tax, tax_type_for
from invoiceflow.core.gstin import make_gstin
from invoiceflow.data.models import ExceptionCode

TOLERANCE = D("1.00")


def reasons(findings: list[Finding]) -> set[FindingReason]:
    return {f.reason for f in findings}


def test_tax_type_depends_on_supplier_state_and_place_of_supply() -> None:
    assert tax_type_for("27", "27") is TaxType.INTRA_STATE
    assert tax_type_for("27", "29") is TaxType.INTER_STATE


def test_compute_line_tax_rounds_each_half_separately() -> None:
    # 100.01 * 9% = 9.0009 -> 9.00 for each half
    assert compute_line_tax(D("100.01"), D("18"), TaxType.INTRA_STATE) == (
        D("9.00"),
        D("9.00"),
        D("0.00"),
    )
    assert compute_line_tax(D("100.01"), D("18"), TaxType.INTER_STATE) == (
        D("0.00"),
        D("0.00"),
        D("18.00"),
    )


def test_correct_intra_state_invoice_has_no_findings() -> None:
    assert check_gst(b.invoice(), b.purchase_order(), b.vendor(), TOLERANCE) == []


def test_correct_inter_state_invoice_has_no_findings() -> None:
    po = b.purchase_order(place_of_supply=b.OTHER_STATE)
    inv = b.invoice(lines=(b.invoice_line(intra_state=False),), place_of_supply=b.OTHER_STATE)
    assert check_gst(inv, po, b.vendor(), TOLERANCE) == []


def test_igst_on_intra_state_supply_is_wrong_tax_type() -> None:
    inv = b.invoice(lines=(b.invoice_line(intra_state=False),))
    findings = check_gst(inv, b.purchase_order(), b.vendor(), TOLERANCE)
    assert reasons(findings) == {FindingReason.WRONG_TAX_TYPE}
    assert all(f.code is ExceptionCode.GST_MISMATCH for f in findings)


def test_cgst_sgst_on_inter_state_supply_is_wrong_tax_type() -> None:
    po = b.purchase_order(place_of_supply=b.OTHER_STATE)
    inv = b.invoice(place_of_supply=b.OTHER_STATE)
    assert reasons(check_gst(inv, po, b.vendor(), TOLERANCE)) == {FindingReason.WRONG_TAX_TYPE}


def test_rate_different_from_po_is_reported() -> None:
    po = b.purchase_order(lines=(b.po_line(rate="5"),))
    inv = b.invoice(lines=(b.invoice_line(rate="18"),))
    findings = check_gst(inv, po, b.vendor(), TOLERANCE)
    assert reasons(findings) == {FindingReason.GST_RATE_MISMATCH}
    assert findings[0].po_line_no == 1


@pytest.mark.parametrize(("delta", "flagged"), [("1.00", False), ("1.01", True)])
def test_tax_amount_tolerance_is_inclusive(delta: str, flagged: bool) -> None:
    line = b.invoice_line()  # 10 x 100 at 18% -> CGST 90, SGST 90
    off = line.model_copy(update={"cgst": line.cgst + D(delta)})
    inv = b.invoice(lines=(off,))
    found = FindingReason.TAX_AMOUNT_MISMATCH in reasons(
        check_gst(inv, b.purchase_order(), b.vendor(), TOLERANCE)
    )
    assert found is flagged


def test_invalid_gstin_on_invoice_is_reported_with_the_failure() -> None:
    good = b.vendor().gstin
    typo = good[:5] + ("A" if good[5] != "A" else "B") + good[6:]
    findings = check_gst(b.invoice(gstin=typo), b.purchase_order(), b.vendor(), TOLERANCE)
    assert FindingReason.GSTIN_INVALID in reasons(findings)
    invalid = next(f for f in findings if f.reason is FindingReason.GSTIN_INVALID)
    assert invalid.evidence["failure"] == "BAD_CHECK_CHARACTER"


def test_valid_gstin_that_is_not_the_vendor_master_one_is_reported() -> None:
    other = make_gstin(b.VENDOR_STATE, "ZZZZZ1111Z")
    findings = check_gst(b.invoice(gstin=other), b.purchase_order(), b.vendor(), TOLERANCE)
    assert reasons(findings) == {FindingReason.GSTIN_NOT_ON_VENDOR_MASTER}


def test_invalid_gstin_on_vendor_master_is_reported_once() -> None:
    bad = b.vendor().gstin[:14] + ("0" if b.vendor().gstin[14] != "0" else "1")
    vendor = b.vendor(gstin=bad)
    findings = check_gst(b.invoice(gstin=bad), b.purchase_order(), vendor, TOLERANCE)
    assert reasons(findings) == {FindingReason.GSTIN_INVALID}
