import json
from types import SimpleNamespace
from typing import Any

from invoiceflow.adapters.cache import CachingReader
from invoiceflow.adapters.databricks.retrieval import AISearchRetriever, SdkIndex
from invoiceflow.adapters.local.memory import MemoryReader
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.models import Role
from invoiceflow.retrieval.models import AccessScope


class CountingReader(MemoryReader):
    def __init__(self, dataset: Dataset) -> None:
        super().__init__(dataset)
        self.calls = 0

    def get_invoice(self, invoice_id: str):  # type: ignore[no-untyped-def]
        self.calls += 1
        return super().get_invoice(invoice_id)


def test_caching_reader_returns_the_same_records_and_reads_once(dataset: Dataset) -> None:
    inner = CountingReader(dataset)
    cached = CachingReader(inner)
    invoice = dataset.invoices[10]
    for _ in range(5):
        assert cached.get_invoice(invoice.invoice_id) == invoice
    assert inner.calls == 1
    assert cached.prior_invoices(invoice) == MemoryReader(dataset).prior_invoices(invoice)
    assert cached.get_purchase_order(invoice.po_id) == inner.get_purchase_order(invoice.po_id)
    assert cached.get_goods_receipts(invoice.po_id) == inner.get_goods_receipts(invoice.po_id)
    assert cached.get_vendor(invoice.vendor_id) == inner.get_vendor(invoice.vendor_id)
    assert cached.list_invoice_ids() == inner.list_invoice_ids()


class FakeIndexes:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    def query_index(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        columns = [*kwargs["columns"], "score"]
        row = [
            "AP-POL:§4.2",
            "AP-POL",
            "policy",
            "§4.2",
            "Three-way match",
            "Price tolerance.",
            "ALL",
            None,
            None,
            "AP_CLERK AP_MANAGER FINANCE_CONTROLLER AUDITOR PLATFORM_ADMIN",
            0.03,
        ]
        return SimpleNamespace(
            manifest=SimpleNamespace(columns=[SimpleNamespace(name=c) for c in columns]),
            result=SimpleNamespace(data_array=[row]),
        )


def test_sdk_index_sends_hybrid_query_with_json_filters() -> None:
    indexes = FakeIndexes()
    workspace = SimpleNamespace(vector_search_indexes=indexes)
    retriever = AISearchRetriever(SdkIndex(workspace, "cat.sch.idx"))  # type: ignore[arg-type]
    scope = AccessScope(role=Role.AP_CLERK, vendor_ids=frozenset({"V011"}))
    result = retriever.search("price tolerance", scope, k=3, doc_types=["policy"])
    assert indexes.kwargs["query_type"] == "HYBRID"
    assert indexes.kwargs["index_name"] == "cat.sch.idx"
    assert json.loads(indexes.kwargs["filters_json"]) == {
        "allowed_roles LIKE": "AP_CLERK",
        "vendor_id": ["ALL", "V011"],
        "doc_type": ["policy"],
    }
    assert result.chunk_ids == ("AP-POL:§4.2",)
