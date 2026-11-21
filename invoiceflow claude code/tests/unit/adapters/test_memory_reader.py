import pytest

from invoiceflow.adapters.local.memory import MemoryReader
from invoiceflow.data.dataset import Dataset
from invoiceflow.ports.data import APDataReader, NotFoundError


def test_memory_reader_satisfies_the_port(dataset: Dataset) -> None:
    reader: APDataReader = MemoryReader(dataset)
    first = dataset.invoices[0]
    assert reader.get_invoice(first.invoice_id) == first
    assert reader.get_purchase_order(first.po_id).po_id == first.po_id
    assert reader.get_vendor(first.vendor_id).vendor_id == first.vendor_id


@pytest.mark.parametrize(
    ("method", "entity"),
    [
        ("get_invoice", "invoice"),
        ("get_vendor", "vendor"),
        ("get_purchase_order", "purchase order"),
    ],
)
def test_missing_records_raise_a_structured_error(
    dataset: Dataset, method: str, entity: str
) -> None:
    reader = MemoryReader(dataset)
    with pytest.raises(NotFoundError) as exc:
        getattr(reader, method)("NOPE-1")
    assert (exc.value.entity, exc.value.key) == (entity, "NOPE-1")


def test_goods_receipts_for_a_po_without_receipts_is_empty(dataset: Dataset) -> None:
    assert MemoryReader(dataset).get_goods_receipts("PO-NONE") == ()


def test_prior_invoices_are_same_vendor_and_strictly_earlier(dataset: Dataset) -> None:
    reader = MemoryReader(dataset)
    invoice = dataset.invoices[-1]
    prior = reader.prior_invoices(invoice)
    assert prior
    assert all(p.vendor_id == invoice.vendor_id for p in prior)
    assert all(p.ledger_key < invoice.ledger_key for p in prior)
    assert list(prior) == sorted(prior, key=lambda p: p.ledger_key)


def test_invoice_ids_are_in_ledger_order(dataset: Dataset) -> None:
    ids = MemoryReader(dataset).list_invoice_ids()
    assert ids == tuple(inv.invoice_id for inv in dataset.invoices)
