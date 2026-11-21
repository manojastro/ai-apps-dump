"""Flat table layout shared by the SQL backends.

One spec drives the Databricks Delta tables (column types and casts), the flat JSON Lines
files uploaded to a Unity Catalog volume, and the SQLite stand-in used in tests. Column
names match `data/ddl/postgres.sql` and `data/rows.py`.
"""

from collections.abc import Iterator
from typing import Any

from invoiceflow.data.dataset import Dataset

# table -> ((column, Databricks SQL type), ...)
AP_TABLES: dict[str, tuple[tuple[str, str], ...]] = {
    "vendors": (
        ("vendor_id", "STRING"),
        ("legal_name", "STRING"),
        ("state_code", "STRING"),
        ("gstin", "STRING"),
        ("pan", "STRING"),
        ("bank_ifsc", "STRING"),
        ("bank_account_number", "STRING"),
        ("city", "STRING"),
        ("active", "BOOLEAN"),
    ),
    "purchase_orders": (
        ("po_id", "STRING"),
        ("vendor_id", "STRING"),
        ("buyer_id", "STRING"),
        ("po_date", "DATE"),
        ("valid_until", "DATE"),
        ("status", "STRING"),
        ("place_of_supply", "STRING"),
    ),
    "po_lines": (
        ("po_id", "STRING"),
        ("line_no", "INT"),
        ("item_code", "STRING"),
        ("description", "STRING"),
        ("quantity", "DECIMAL(14,3)"),
        ("unit_price", "DECIMAL(14,2)"),
        ("gst_rate", "DECIMAL(5,2)"),
    ),
    "goods_receipts": (("grn_id", "STRING"), ("po_id", "STRING"), ("received_date", "DATE")),
    "grn_lines": (
        ("grn_id", "STRING"),
        ("po_line_no", "INT"),
        ("quantity_received", "DECIMAL(14,3)"),
    ),
    "invoices": (
        ("invoice_id", "STRING"),
        ("vendor_id", "STRING"),
        ("invoice_number", "STRING"),
        ("invoice_date", "DATE"),
        ("received_date", "DATE"),
        ("po_id", "STRING"),
        ("supplier_gstin", "STRING"),
        ("place_of_supply", "STRING"),
        ("bank_ifsc", "STRING"),
        ("bank_account_number", "STRING"),
        ("gross_total", "DECIMAL(14,2)"),
        ("notes", "STRING"),
        ("remarks", "STRING"),
    ),
    "invoice_lines": (
        ("invoice_id", "STRING"),
        ("line_no", "INT"),
        ("po_line_no", "INT"),
        ("description", "STRING"),
        ("quantity", "DECIMAL(14,3)"),
        ("unit_price", "DECIMAL(14,2)"),
        ("taxable_value", "DECIMAL(14,2)"),
        ("gst_rate", "DECIMAL(5,2)"),
        ("cgst", "DECIMAL(14,2)"),
        ("sgst", "DECIMAL(14,2)"),
        ("igst", "DECIMAL(14,2)"),
    ),
}
EVAL_TABLES: dict[str, tuple[tuple[str, str], ...]] = {
    "ground_truth": (
        ("invoice_id", "STRING"),
        ("split", "STRING"),
        ("expected_exception", "STRING"),
        ("expected_action", "STRING"),
        ("expected_required_approver", "STRING"),
        ("scenario", "STRING"),
        ("adversarial_kind", "STRING"),
        ("rationale", "STRING"),
    ),
}


def _s(value: Any) -> Any:
    """Decimals and dates travel as strings so nothing is lost before the CAST."""
    if value is None or isinstance(value, bool | int):
        return value
    return str(value)


def flat_rows(dataset: Dataset, table: str) -> Iterator[dict[str, Any]]:
    if table == "vendors":
        for v in dataset.vendors:
            yield {
                "vendor_id": v.vendor_id,
                "legal_name": v.legal_name,
                "state_code": v.state_code,
                "gstin": v.gstin,
                "pan": v.pan,
                "bank_ifsc": v.bank.ifsc,
                "bank_account_number": v.bank.account_number,
                "city": v.city,
                "active": v.active,
            }
    elif table == "purchase_orders":
        for po in dataset.purchase_orders:
            yield {
                "po_id": po.po_id,
                "vendor_id": po.vendor_id,
                "buyer_id": po.buyer_id,
                "po_date": _s(po.po_date),
                "valid_until": _s(po.valid_until),
                "status": po.status.value,
                "place_of_supply": po.place_of_supply,
            }
    elif table == "po_lines":
        for po in dataset.purchase_orders:
            for line in po.lines:
                yield {
                    "po_id": po.po_id,
                    "line_no": line.line_no,
                    "item_code": line.item_code,
                    "description": line.description,
                    "quantity": _s(line.quantity),
                    "unit_price": _s(line.unit_price),
                    "gst_rate": _s(line.gst_rate),
                }
    elif table == "goods_receipts":
        for grn in dataset.goods_receipts:
            yield {"grn_id": grn.grn_id, "po_id": grn.po_id, "received_date": _s(grn.received_date)}
    elif table == "grn_lines":
        for grn in dataset.goods_receipts:
            for gl in grn.lines:
                yield {
                    "grn_id": grn.grn_id,
                    "po_line_no": gl.po_line_no,
                    "quantity_received": _s(gl.quantity_received),
                }
    elif table == "invoices":
        for i in dataset.invoices:
            yield {
                "invoice_id": i.invoice_id,
                "vendor_id": i.vendor_id,
                "invoice_number": i.invoice_number,
                "invoice_date": _s(i.invoice_date),
                "received_date": _s(i.received_date),
                "po_id": i.po_id,
                "supplier_gstin": i.supplier_gstin,
                "place_of_supply": i.place_of_supply,
                "bank_ifsc": i.bank.ifsc,
                "bank_account_number": i.bank.account_number,
                "gross_total": _s(i.gross_total),
                "notes": i.notes,
                "remarks": i.remarks,
            }
    elif table == "invoice_lines":
        for i in dataset.invoices:
            for il in i.lines:
                yield {
                    "invoice_id": i.invoice_id,
                    "line_no": il.line_no,
                    "po_line_no": il.po_line_no,
                    "description": il.description,
                    "quantity": _s(il.quantity),
                    "unit_price": _s(il.unit_price),
                    "taxable_value": _s(il.taxable_value),
                    "gst_rate": _s(il.gst_rate),
                    "cgst": _s(il.cgst),
                    "sgst": _s(il.sgst),
                    "igst": _s(il.igst),
                }
    elif table == "ground_truth":
        for g in dataset.ground_truth:
            yield {
                "invoice_id": g.invoice_id,
                "split": g.split.value,
                "expected_exception": g.expected_exception.value,
                "expected_action": g.expected_action.value,
                "expected_required_approver": (
                    g.expected_required_approver.value if g.expected_required_approver else None
                ),
                "scenario": g.scenario,
                "adversarial_kind": g.adversarial_kind,
                "rationale": g.rationale,
            }
    else:
        raise KeyError(table)
