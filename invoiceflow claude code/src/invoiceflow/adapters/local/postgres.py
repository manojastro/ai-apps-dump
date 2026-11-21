"""Postgres implementation of APDataReader (read-only queries on the `ap` schema).

`PostgresGroundTruth` reads the `eval` schema and is used only by evaluation code.
"""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from invoiceflow.data.models import GoodsReceipt, GroundTruth, Invoice, PurchaseOrder, Split, Vendor
from invoiceflow.data.rows import grn_from_rows, invoice_from_rows, po_from_rows, vendor_from_row
from invoiceflow.ports.data import NotFoundError


class PostgresReader:
    def __init__(self, conn: psycopg.Connection[Any]) -> None:
        self._conn = conn

    def _rows(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query.encode("utf-8"), params)
            return cur.fetchall()

    def _one(self, entity: str, key: str, query: str) -> dict[str, Any]:
        rows = self._rows(query, (key,))
        if not rows:
            raise NotFoundError(entity, key)
        return rows[0]

    def get_vendor(self, vendor_id: str) -> Vendor:
        return vendor_from_row(
            self._one("vendor", vendor_id, "SELECT * FROM ap.vendors WHERE vendor_id = %s")
        )

    def get_purchase_order(self, po_id: str) -> PurchaseOrder:
        header = self._one(
            "purchase order", po_id, "SELECT * FROM ap.purchase_orders WHERE po_id = %s"
        )
        lines = self._rows("SELECT * FROM ap.po_lines WHERE po_id = %s", (po_id,))
        return po_from_rows(header, lines)

    def get_goods_receipts(self, po_id: str) -> tuple[GoodsReceipt, ...]:
        headers = self._rows(
            "SELECT * FROM ap.goods_receipts WHERE po_id = %s ORDER BY grn_id", (po_id,)
        )
        return tuple(
            grn_from_rows(
                header,
                self._rows("SELECT * FROM ap.grn_lines WHERE grn_id = %s", (header["grn_id"],)),
            )
            for header in headers
        )

    def get_invoice(self, invoice_id: str) -> Invoice:
        header = self._one("invoice", invoice_id, "SELECT * FROM ap.invoices WHERE invoice_id = %s")
        lines = self._rows("SELECT * FROM ap.invoice_lines WHERE invoice_id = %s", (invoice_id,))
        return invoice_from_rows(header, lines)

    def list_invoice_ids(self) -> tuple[str, ...]:
        rows = self._rows("SELECT invoice_id FROM ap.invoices ORDER BY received_date, invoice_id")
        return tuple(row["invoice_id"] for row in rows)

    def prior_invoices(self, invoice: Invoice) -> tuple[Invoice, ...]:
        rows = self._rows(
            "SELECT invoice_id FROM ap.invoices WHERE vendor_id = %s "
            "AND (received_date, invoice_id) < (%s, %s) ORDER BY received_date, invoice_id",
            (invoice.vendor_id, invoice.received_date, invoice.invoice_id),
        )
        return tuple(self.get_invoice(row["invoice_id"]) for row in rows)


class PostgresGroundTruth:
    """Reads labels from the `eval` schema. Evaluation code only; never given to the agent."""

    def __init__(self, conn: psycopg.Connection[Any]) -> None:
        self._conn = conn

    def labels(self, split: Split | None = None) -> tuple[GroundTruth, ...]:
        with self._conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM eval.ground_truth ORDER BY invoice_id")
            rows = cur.fetchall()
        labels = tuple(GroundTruth.model_validate(row) for row in rows)
        return labels if split is None else tuple(label for label in labels if label.split is split)
