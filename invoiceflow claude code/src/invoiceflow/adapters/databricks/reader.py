"""Databricks implementation of APDataReader over Unity Catalog Delta tables.

Same row mapping as Postgres (`data/rows.py`), so parity is about the SQL and the types,
not about two copies of mapping code. Reads the full tables: the deterministic matcher
needs exact bank details to compare them. The LLM-facing governed tools are the masked
Unity Catalog functions created by `setup.py`.
"""

from collections import defaultdict
from typing import Any

from invoiceflow.adapters.databricks.sql import SqlRunner, identifier
from invoiceflow.data.models import GoodsReceipt, GroundTruth, Invoice, PurchaseOrder, Vendor
from invoiceflow.data.rows import grn_from_rows, invoice_from_rows, po_from_rows, vendor_from_row
from invoiceflow.ports.data import NotFoundError


class Snapshot:
    """Every AP record read with one query per table (8 statements in total).

    Batch work (parity, evaluation) uses this instead of per-record reads: on a 2X-Small
    Free Edition warehouse each statement takes seconds, so per-record reads do not scale.
    """

    def __init__(self, runner: SqlRunner, catalog: str, schema: str) -> None:
        prefix = f"{identifier(catalog)}.{identifier(schema)}"

        def table(name: str) -> list[dict[str, Any]]:
            return runner.query(f"SELECT * FROM {prefix}.{identifier(name)}")  # noqa: S608

        def grouped(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
            out: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                out[row[key]].append(row)
            return out

        po_lines = grouped(table("po_lines"), "po_id")
        grn_lines = grouped(table("grn_lines"), "grn_id")
        invoice_lines = grouped(table("invoice_lines"), "invoice_id")
        self.vendors = tuple(
            sorted((vendor_from_row(r) for r in table("vendors")), key=lambda v: v.vendor_id)
        )
        self.purchase_orders = tuple(
            sorted(
                (po_from_rows(r, po_lines[r["po_id"]]) for r in table("purchase_orders")),
                key=lambda p: p.po_id,
            )
        )
        self.goods_receipts = tuple(
            sorted(
                (grn_from_rows(r, grn_lines[r["grn_id"]]) for r in table("goods_receipts")),
                key=lambda g: g.grn_id,
            )
        )
        self.invoices = tuple(
            sorted(
                (invoice_from_rows(r, invoice_lines[r["invoice_id"]]) for r in table("invoices")),
                key=lambda i: i.ledger_key,
            )
        )


def snapshot_labels(runner: SqlRunner, catalog: str, eval_schema: str) -> tuple[GroundTruth, ...]:
    rows = runner.query(
        f"SELECT * FROM {identifier(catalog)}.{identifier(eval_schema)}.`ground_truth`"  # noqa: S608
    )
    return tuple(sorted((GroundTruth.model_validate(r) for r in rows), key=lambda g: g.invoice_id))


class DatabricksReader:
    def __init__(self, runner: SqlRunner, catalog: str, schema: str) -> None:
        self._runner = runner
        self._prefix = f"{identifier(catalog)}.{identifier(schema)}"

    def _t(self, table: str) -> str:
        return f"{self._prefix}.{identifier(table)}"

    def _one(self, entity: str, key: str, table: str, column: str) -> dict[str, Any]:
        rows = self._runner.query(
            f"SELECT * FROM {self._t(table)} WHERE {identifier(column)} = :key",  # noqa: S608
            {"key": key},
        )
        if not rows:
            raise NotFoundError(entity, key)
        return rows[0]

    def _where(self, table: str, column: str, key: str) -> list[dict[str, Any]]:
        return self._runner.query(
            f"SELECT * FROM {self._t(table)} WHERE {identifier(column)} = :key",  # noqa: S608
            {"key": key},
        )

    def get_vendor(self, vendor_id: str) -> Vendor:
        return vendor_from_row(self._one("vendor", vendor_id, "vendors", "vendor_id"))

    def get_purchase_order(self, po_id: str) -> PurchaseOrder:
        header = self._one("purchase order", po_id, "purchase_orders", "po_id")
        return po_from_rows(header, self._where("po_lines", "po_id", po_id))

    def get_goods_receipts(self, po_id: str) -> tuple[GoodsReceipt, ...]:
        headers = sorted(self._where("goods_receipts", "po_id", po_id), key=lambda r: r["grn_id"])
        return tuple(
            grn_from_rows(h, self._where("grn_lines", "grn_id", h["grn_id"])) for h in headers
        )

    def get_invoice(self, invoice_id: str) -> Invoice:
        header = self._one("invoice", invoice_id, "invoices", "invoice_id")
        return invoice_from_rows(header, self._where("invoice_lines", "invoice_id", invoice_id))

    def list_invoice_ids(self) -> tuple[str, ...]:
        rows = self._runner.query(
            f"SELECT invoice_id FROM {self._t('invoices')} "  # noqa: S608
            "ORDER BY received_date, invoice_id"
        )
        return tuple(row["invoice_id"] for row in rows)

    def prior_invoices(self, invoice: Invoice) -> tuple[Invoice, ...]:
        rows = self._runner.query(
            f"SELECT invoice_id FROM {self._t('invoices')} "  # noqa: S608
            "WHERE vendor_id = :vendor AND (received_date < :received "
            "OR (received_date = :received AND invoice_id < :invoice)) "
            "ORDER BY received_date, invoice_id",
            {
                "vendor": invoice.vendor_id,
                "received": invoice.received_date.isoformat(),
                "invoice": invoice.invoice_id,
            },
        )
        return tuple(self.get_invoice(row["invoice_id"]) for row in rows)
