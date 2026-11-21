"""Postgres backend: idempotent load and parity with the in-memory reader.

Needs `docker compose up -d --wait` and a `.env` with POSTGRES_PASSWORD. Run with
`uv run pytest -m integration`. The parity test is the foundation for Phase 2, where the
same comparison runs against Databricks.
"""

from collections.abc import Iterator
from typing import Any

import psycopg
import pytest

from invoiceflow.adapters.local.memory import MemoryReader
from invoiceflow.adapters.local.postgres import PostgresGroundTruth, PostgresReader
from invoiceflow.config import Settings
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.loader import load_dataset, loaded_version, row_counts
from invoiceflow.data.models import Split
from invoiceflow.evals.baseline import run_baseline
from invoiceflow.policy.matrix import load_matrix
from invoiceflow.ports.data import NotFoundError

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def conn(dataset: Dataset) -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(Settings().postgres_conninfo()) as connection:
        load_dataset(connection, dataset)
        yield connection


def test_load_is_idempotent(conn: psycopg.Connection[Any], dataset: Dataset) -> None:
    first = row_counts(conn)
    second = load_dataset(conn, dataset)
    assert first == second
    assert second["ap.invoices"] == len(dataset.invoices)
    assert second["eval.ground_truth"] == len(dataset.ground_truth)
    assert loaded_version(conn) == dataset.version


def test_every_record_matches_the_in_memory_reader(
    conn: psycopg.Connection[Any], dataset: Dataset
) -> None:
    pg, mem = PostgresReader(conn), MemoryReader(dataset)
    assert pg.list_invoice_ids() == mem.list_invoice_ids()
    for vendor in dataset.vendors:
        assert pg.get_vendor(vendor.vendor_id) == mem.get_vendor(vendor.vendor_id)
    for po in dataset.purchase_orders:
        assert pg.get_purchase_order(po.po_id) == mem.get_purchase_order(po.po_id)
        assert pg.get_goods_receipts(po.po_id) == mem.get_goods_receipts(po.po_id)
    for invoice in dataset.invoices:
        assert pg.get_invoice(invoice.invoice_id) == invoice
        assert pg.prior_invoices(invoice) == mem.prior_invoices(invoice)


def test_ground_truth_round_trips(conn: psycopg.Connection[Any], dataset: Dataset) -> None:
    assert PostgresGroundTruth(conn).labels() == tuple(
        sorted(dataset.ground_truth, key=lambda label: label.invoice_id)
    )


def test_missing_record_is_a_structured_error(conn: psycopg.Connection[Any]) -> None:
    with pytest.raises(NotFoundError) as exc:
        PostgresReader(conn).get_invoice("INV-NOPE")
    assert exc.value.entity == "invoice"


def test_baseline_gives_identical_results_on_both_backends(
    conn: psycopg.Connection[Any], dataset: Dataset
) -> None:
    labels, matrix = dataset.labels(Split.DEV), load_matrix()
    assert run_baseline(PostgresReader(conn), labels, matrix) == run_baseline(
        MemoryReader(dataset), labels, matrix
    )
