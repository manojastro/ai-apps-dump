"""Load a dataset into Postgres. Idempotent: schema is created if missing, every table is
emptied, and all rows are inserted again inside one transaction. Running it twice leaves the
database identical; a failure part-way leaves it as it was."""

from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql

from invoiceflow.data.dataset import Dataset

DDL_PATH = Path(__file__).with_name("ddl") / "postgres.sql"
TABLES = (
    "ap.vendors",
    "ap.purchase_orders",
    "ap.po_lines",
    "ap.goods_receipts",
    "ap.grn_lines",
    "ap.invoices",
    "ap.invoice_lines",
    "eval.ground_truth",
)


def _table(name: str) -> sql.Identifier:
    return sql.Identifier(*name.split("."))


def load_dataset(conn: psycopg.Connection[Any], dataset: Dataset) -> dict[str, int]:
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(DDL_PATH.read_text(encoding="utf-8").encode("utf-8"))
        cur.execute(
            sql.SQL("TRUNCATE {}").format(
                sql.SQL(", ").join(_table(t) for t in (*TABLES, "ap.dataset_meta"))
            )
        )

        cur.executemany(
            "INSERT INTO ap.vendors VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    v.vendor_id,
                    v.legal_name,
                    v.state_code,
                    v.gstin,
                    v.pan,
                    v.bank.ifsc,
                    v.bank.account_number,
                    v.city,
                    v.active,
                )
                for v in dataset.vendors
            ],
        )
        cur.executemany(
            "INSERT INTO ap.purchase_orders VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    po.po_id,
                    po.vendor_id,
                    po.buyer_id,
                    po.po_date,
                    po.valid_until,
                    po.status.value,
                    po.place_of_supply,
                )
                for po in dataset.purchase_orders
            ],
        )
        cur.executemany(
            "INSERT INTO ap.po_lines VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    po.po_id,
                    line.line_no,
                    line.item_code,
                    line.description,
                    line.quantity,
                    line.unit_price,
                    line.gst_rate,
                )
                for po in dataset.purchase_orders
                for line in po.lines
            ],
        )
        cur.executemany(
            "INSERT INTO ap.goods_receipts VALUES (%s, %s, %s)",
            [(g.grn_id, g.po_id, g.received_date) for g in dataset.goods_receipts],
        )
        cur.executemany(
            "INSERT INTO ap.grn_lines VALUES (%s, %s, %s)",
            [
                (g.grn_id, line.po_line_no, line.quantity_received)
                for g in dataset.goods_receipts
                for line in g.lines
            ],
        )
        cur.executemany(
            "INSERT INTO ap.invoices VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    i.invoice_id,
                    i.vendor_id,
                    i.invoice_number,
                    i.invoice_date,
                    i.received_date,
                    i.po_id,
                    i.supplier_gstin,
                    i.place_of_supply,
                    i.bank.ifsc,
                    i.bank.account_number,
                    i.gross_total,
                    i.notes,
                    i.remarks,
                )
                for i in dataset.invoices
            ],
        )
        cur.executemany(
            "INSERT INTO ap.invoice_lines VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    i.invoice_id,
                    line.line_no,
                    line.po_line_no,
                    line.description,
                    line.quantity,
                    line.unit_price,
                    line.taxable_value,
                    line.gst_rate,
                    line.cgst,
                    line.sgst,
                    line.igst,
                )
                for i in dataset.invoices
                for line in i.lines
            ],
        )
        cur.executemany(
            "INSERT INTO eval.ground_truth VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    g.invoice_id,
                    g.split.value,
                    g.expected_exception.value,
                    g.expected_action.value,
                    g.expected_required_approver.value if g.expected_required_approver else None,
                    g.scenario,
                    g.adversarial_kind,
                    g.rationale,
                )
                for g in dataset.ground_truth
            ],
        )
        cur.execute(
            "INSERT INTO ap.dataset_meta (dataset_version, seed) VALUES (%s, %s)",
            (dataset.version, dataset.seed),
        )
    return row_counts(conn)


def row_counts(conn: psycopg.Connection[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in TABLES:
            cur.execute(sql.SQL("SELECT count(*) FROM {}").format(_table(table)))
            row = cur.fetchone()
            counts[table] = int(row[0]) if row else 0
    return counts


def loaded_version(conn: psycopg.Connection[Any]) -> str | None:
    with conn.cursor() as cur:
        cur.execute("SELECT dataset_version FROM ap.dataset_meta")
        row = cur.fetchone()
        return str(row[0]) if row else None
