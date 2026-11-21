"""Small builders for synthetic test objects.

Taxes are computed here independently of `invoiceflow.core.gst`, so core tests do not
check the implementation against itself.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from invoiceflow.core.gstin import make_gstin
from invoiceflow.data.models import (
    BankAccount,
    GoodsReceipt,
    GRNLine,
    Invoice,
    InvoiceLine,
    POLine,
    POStatus,
    PurchaseOrder,
    Vendor,
)

D = Decimal
VENDOR_STATE = "27"  # Maharashtra
OTHER_STATE = "29"  # Karnataka
VENDOR_PAN = "QWXYZ9876K"


def _round(value: Decimal) -> Decimal:
    return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def bank(account_number: str = "100200300400", ifsc: str = "XSYN0000001") -> BankAccount:
    return BankAccount(ifsc=ifsc, account_number=account_number)


def vendor(
    vendor_id: str = "V001", state_code: str = VENDOR_STATE, gstin: str | None = None
) -> Vendor:
    return Vendor(
        vendor_id=vendor_id,
        legal_name="Copperleaf Fasteners Pvt Ltd",
        state_code=state_code,
        gstin=gstin or make_gstin(state_code, VENDOR_PAN),
        pan=VENDOR_PAN,
        bank=bank(),
        city="Pune",
    )


def po_line(line_no: int = 1, qty: str = "10", price: str = "100.00", rate: str = "18") -> POLine:
    return POLine(
        line_no=line_no,
        item_code=f"ITEM-{line_no:03d}",
        description="M8 hex bolts, zinc plated",
        quantity=D(qty),
        unit_price=D(price),
        gst_rate=D(rate),
    )


def purchase_order(
    lines: tuple[POLine, ...] | None = None,
    po_id: str = "PO-0001",
    status: POStatus = POStatus.OPEN,
    place_of_supply: str = VENDOR_STATE,
    po_date: date = date(2026, 5, 1),
    valid_until: date = date(2026, 7, 30),
) -> PurchaseOrder:
    return PurchaseOrder(
        po_id=po_id,
        vendor_id="V001",
        buyer_id="BUY-01",
        po_date=po_date,
        valid_until=valid_until,
        status=status,
        place_of_supply=place_of_supply,
        lines=lines or (po_line(),),
    )


def grn(received: dict[int, str], po_id: str = "PO-0001", grn_id: str = "GRN-0001") -> GoodsReceipt:
    return GoodsReceipt(
        grn_id=grn_id,
        po_id=po_id,
        received_date=date(2026, 5, 10),
        lines=tuple(GRNLine(po_line_no=n, quantity_received=D(q)) for n, q in received.items()),
    )


def invoice_line(
    po_line_no: int = 1,
    qty: str = "10",
    price: str = "100.00",
    rate: str = "18",
    intra_state: bool = True,
    line_no: int | None = None,
) -> InvoiceLine:
    taxable = _round(D(qty) * D(price))
    if intra_state:
        half = _round(taxable * D(rate) / 200)
        cgst, sgst, igst = half, half, D("0.00")
    else:
        cgst, sgst, igst = D("0.00"), D("0.00"), _round(taxable * D(rate) / 100)
    return InvoiceLine(
        line_no=line_no or po_line_no,
        po_line_no=po_line_no,
        description="M8 hex bolts, zinc plated",
        quantity=D(qty),
        unit_price=D(price),
        taxable_value=taxable,
        gst_rate=D(rate),
        cgst=cgst,
        sgst=sgst,
        igst=igst,
    )


def invoice(
    lines: tuple[InvoiceLine, ...] | None = None,
    invoice_id: str = "INV-0001",
    invoice_number: str = "CF-2026-0042",
    invoice_date: date = date(2026, 5, 12),
    received_date: date = date(2026, 5, 14),
    gstin: str | None = None,
    bank_account: BankAccount | None = None,
    place_of_supply: str = VENDOR_STATE,
    notes: str = "",
) -> Invoice:
    lines = lines or (invoice_line(),)
    gross = sum((line.taxable_value + line.tax_total for line in lines), D("0"))
    return Invoice(
        invoice_id=invoice_id,
        vendor_id="V001",
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        received_date=received_date,
        po_id="PO-0001",
        supplier_gstin=gstin or make_gstin(VENDOR_STATE, VENDOR_PAN),
        place_of_supply=place_of_supply,
        bank=bank_account or bank(),
        lines=lines,
        gross_total=gross,
        notes=notes,
    )
