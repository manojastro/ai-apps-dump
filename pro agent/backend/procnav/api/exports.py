"""CSV comparison export and PDF run summary."""

from __future__ import annotations

import csv
import io
from typing import Any

from fpdf import FPDF

CSV_COLUMNS = [
    "quote_version",
    "supplier",
    "sku",
    "product_name",
    "ram_gb",
    "ssd_gb",
    "quantity",
    "pack_size",
    "stock_observed",
    "unit_price",
    "subtotal",
    "discount",
    "tax",
    "shipping",
    "total",
    "currency",
    "price_basis",
    "delivery_date",
    "delivery_confidence",
    "age_seconds",
    "eligible",
    "failed_rules",
]


def comparison_csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["# Synthetic demo data. Prices, tax rates and suppliers are fictional."])
    w.writerow(CSV_COLUMNS)
    for q in rows:
        failed = ";".join(r["rule"] for r in q["policy_results"] if r["hard"] and not r["passed"])
        w.writerow(
            [
                q["version"],
                q["supplier"]["key"],
                q["sku"],
                q["product_name"],
                q["spec"].get("ram_gb"),
                q["spec"].get("ssd_gb"),
                q["quantity"],
                q["pack_size"],
                q["stock_observed"],
                q["unit_price"],
                q["subtotal"],
                q["discount"],
                q["tax"],
                q["shipping"],
                q["total"],
                q["currency"],
                q["price_basis"],
                q["delivery_date"],
                q["delivery_confidence"],
                q["age_seconds"],
                q["eligible"],
                failed,
            ]
        )
    return buf.getvalue()


def _latin(text: str) -> str:
    return text.replace("₹", "INR ").encode("latin-1", "replace").decode("latin-1")


def run_summary_pdf(
    run: dict[str, Any], request: dict[str, Any], quotes: list[dict[str, Any]], order: dict[str, Any] | None
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Procurement Navigator - run summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(160, 0, 0)
    label = "SIMULATED MODEL DECISIONS - " if run["simulated_model"] else ""
    pdf.multi_cell(0, 5, _latin(label + "Synthetic suppliers and fixture data; no real purchase or payment."))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    for k, v in [
        ("Run", run["id"]),
        ("Request", request["title"]),
        ("Outcome", run["outcome"] or run["status"]),
        ("Quantity", request["quantity"]),
        ("Budget", f"INR {request['budget_total']}"),
        ("Deadline", request["delivery_deadline"]),
        ("Destination", request["address_ref"]),
        ("Browser actions", run["action_count"]),
        ("Active time (s)", round(run["active_ms"] / 1000, 1)),
        ("Human waiting (s)", round(run["waiting_ms"] / 1000, 1)),
        ("Model cost (USD)", run["model_cost"]),
    ]:
        pdf.cell(45, 6, _latin(str(k)))
        pdf.cell(0, 6, _latin(str(v)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Quote comparison", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 8)
    widths = [18, 32, 14, 24, 22, 22, 26, 32]
    for h, w in zip(
        ["Supplier", "SKU", "RAM", "Unit", "Tax", "Shipping", "Landed total", "Eligibility"], widths, strict=True
    ):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for q in quotes:
        failed = [r["rule"] for r in q["policy_results"] if r["hard"] and not r["passed"]]
        cells = [
            q["supplier"]["key"],
            q["sku"],
            f"{q['spec'].get('ram_gb')} GB",
            q["unit_price"] or "-",
            q["tax"] or "-",
            q["shipping"] or "-",
            q["total"] or "-",
            "eligible" if q["eligible"] else ",".join(failed)[:22],
        ]
        for c, w in zip(cells, widths, strict=True):
            pdf.cell(w, 6, _latin(str(c)), border=1)
        pdf.ln()
    if order and order.get("supplier_order"):
        so = order["supplier_order"]
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Order", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for k, v in [
            ("Ledger state", order["status"]),
            ("Supplier order", so["supplier_order_ref"]),
            ("PO / idempotency token", order["intent_key"]),
            ("Total", f"INR {so['total']}"),
            ("Receipt verified", so["verified"]),
            ("Reconciled via", so["reconciled_via"]),
        ]:
            pdf.cell(45, 6, _latin(str(k)))
            pdf.cell(0, 6, _latin(str(v)), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
