"""Build domain models from database rows. Shared by every SQL backend (Postgres,
Databricks) so the mapping exists once. Column names match the DDL in data/ddl."""

from collections.abc import Mapping, Sequence
from typing import Any

from invoiceflow.data.models import (
    BankAccount,
    GoodsReceipt,
    GRNLine,
    Invoice,
    InvoiceLine,
    POLine,
    PurchaseOrder,
    Vendor,
)

Row = Mapping[str, Any]


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "t"}
    return bool(value)


def vendor_from_row(row: Row) -> Vendor:
    return Vendor(
        vendor_id=row["vendor_id"],
        legal_name=row["legal_name"],
        state_code=row["state_code"],
        gstin=row["gstin"],
        pan=row["pan"],
        bank=BankAccount(ifsc=row["bank_ifsc"], account_number=row["bank_account_number"]),
        city=row["city"],
        active=_bool(row["active"]),
    )


def po_from_rows(header: Row, lines: Sequence[Row]) -> PurchaseOrder:
    return PurchaseOrder(
        po_id=header["po_id"],
        vendor_id=header["vendor_id"],
        buyer_id=header["buyer_id"],
        po_date=header["po_date"],
        valid_until=header["valid_until"],
        status=header["status"],
        place_of_supply=header["place_of_supply"],
        lines=tuple(
            POLine(
                line_no=int(line["line_no"]),
                item_code=line["item_code"],
                description=line["description"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                gst_rate=line["gst_rate"],
            )
            for line in sorted(lines, key=lambda r: int(r["line_no"]))
        ),
    )


def grn_from_rows(header: Row, lines: Sequence[Row]) -> GoodsReceipt:
    return GoodsReceipt(
        grn_id=header["grn_id"],
        po_id=header["po_id"],
        received_date=header["received_date"],
        lines=tuple(
            GRNLine(po_line_no=int(line["po_line_no"]), quantity_received=line["quantity_received"])
            for line in sorted(lines, key=lambda r: int(r["po_line_no"]))
        ),
    )


def invoice_from_rows(header: Row, lines: Sequence[Row]) -> Invoice:
    return Invoice(
        invoice_id=header["invoice_id"],
        vendor_id=header["vendor_id"],
        invoice_number=header["invoice_number"],
        invoice_date=header["invoice_date"],
        received_date=header["received_date"],
        po_id=header["po_id"],
        supplier_gstin=header["supplier_gstin"],
        place_of_supply=header["place_of_supply"],
        bank=BankAccount(ifsc=header["bank_ifsc"], account_number=header["bank_account_number"]),
        lines=tuple(
            InvoiceLine(
                line_no=int(line["line_no"]),
                po_line_no=int(line["po_line_no"]),
                description=line["description"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                taxable_value=line["taxable_value"],
                gst_rate=line["gst_rate"],
                cgst=line["cgst"],
                sgst=line["sgst"],
                igst=line["igst"],
            )
            for line in sorted(lines, key=lambda r: int(r["line_no"]))
        ),
        gross_total=header["gross_total"],
        notes=header["notes"] or "",
        remarks=header["remarks"] or "",
    )
