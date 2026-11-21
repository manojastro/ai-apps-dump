"""Databricks adapter against a SQLite stand-in (see sqlite_runner.py). Not a Databricks test:
the live parity run is `uv run invoiceflow databricks parity` (marked as not yet run)."""

import pytest

from invoiceflow.adapters.databricks.reader import DatabricksReader
from invoiceflow.adapters.databricks.setup import Target, function_statements, table_statements
from invoiceflow.adapters.databricks.sql import identifier
from invoiceflow.adapters.local.memory import MemoryReader
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.tables import AP_TABLES, EVAL_TABLES
from invoiceflow.ports.data import NotFoundError
from sqlite_runner import SqliteRunner

TARGET = Target(catalog="invoiceflow", schema="ap", eval_schema="eval", volume="raw")


def test_reader_matches_memory_reader_record_by_record(dataset: Dataset) -> None:
    db = DatabricksReader(SqliteRunner(dataset), "invoiceflow", "ap")
    mem = MemoryReader(dataset)
    assert db.list_invoice_ids() == mem.list_invoice_ids()
    for vendor in dataset.vendors:
        assert db.get_vendor(vendor.vendor_id) == vendor
    for po in dataset.purchase_orders[:60]:
        assert db.get_purchase_order(po.po_id) == po
        assert db.get_goods_receipts(po.po_id) == mem.get_goods_receipts(po.po_id)
    for invoice in dataset.invoices[::5]:
        assert db.get_invoice(invoice.invoice_id) == invoice
        assert db.prior_invoices(invoice) == mem.prior_invoices(invoice)


def test_reader_uses_named_parameters_not_string_splicing(dataset: Dataset) -> None:
    runner = SqliteRunner(dataset)
    reader = DatabricksReader(runner, "invoiceflow", "ap")
    with pytest.raises(NotFoundError):
        reader.get_invoice("x' OR '1'='1")
    assert all("x' OR" not in statement for statement in runner.statements)


def test_identifiers_are_validated() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        identifier("ap; DROP TABLE x")
    with pytest.raises(ValueError, match="unsafe"):
        DatabricksReader(SqliteRunner.__new__(SqliteRunner), "invoiceflow", "a-p")


def test_setup_creates_every_table_from_the_volume_with_casts() -> None:
    statements = list(table_statements(TARGET))
    assert statements[0] == "CREATE CATALOG IF NOT EXISTS `invoiceflow`"
    creates = [s for s in statements if s.startswith("CREATE OR REPLACE TABLE")]
    assert len(creates) == len(AP_TABLES) + len(EVAL_TABLES)
    invoices = next(s for s in creates if "`ap`.`invoices`" in s)
    assert "read_files('/Volumes/invoiceflow/ap/raw/invoices.jsonl'" in invoices
    assert "CAST(`gross_total` AS DECIMAL(14,2))" in invoices
    assert any("`eval`.`ground_truth`" in s for s in creates)


def test_governed_functions_never_return_full_bank_accounts() -> None:
    mask = "concat(repeat('X', length(bank_account_number) - 4), right(bank_account_number, 4))"
    functions = list(function_statements(TARGET))
    assert len(functions) == 6
    for sql in functions:
        selected = sql.split("RETURN SELECT", 1)[1].split("FROM", 1)[0]
        assert "bank_account_number" not in selected.replace(mask, "MASKED")
        assert sql.startswith("CREATE OR REPLACE FUNCTION")
        assert "COMMENT 'InvoiceFlow read-only tool" in sql
        assert not any(word in sql.upper() for word in ("INSERT ", "UPDATE ", "DELETE ", "MERGE "))
