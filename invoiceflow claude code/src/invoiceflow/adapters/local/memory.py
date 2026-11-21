"""In-memory APDataReader over a generated Dataset (or a Databricks Snapshot). Fast and needs
no Docker: used by unit tests, CI, the baseline and batch runs on Databricks data. The
Postgres and Databricks adapters must return exactly the same objects."""

from collections import defaultdict
from collections.abc import Sequence
from typing import Protocol

from invoiceflow.data.models import GoodsReceipt, Invoice, PurchaseOrder, Vendor
from invoiceflow.ports.data import NotFoundError


class Records(Protocol):
    @property
    def vendors(self) -> Sequence[Vendor]: ...
    @property
    def purchase_orders(self) -> Sequence[PurchaseOrder]: ...
    @property
    def goods_receipts(self) -> Sequence[GoodsReceipt]: ...
    @property
    def invoices(self) -> Sequence[Invoice]: ...


class MemoryReader:
    def __init__(self, dataset: Records) -> None:
        self._vendors = {v.vendor_id: v for v in dataset.vendors}
        self._pos = {po.po_id: po for po in dataset.purchase_orders}
        self._invoices = {inv.invoice_id: inv for inv in dataset.invoices}
        self._grns: dict[str, list[GoodsReceipt]] = defaultdict(list)
        for grn in sorted(dataset.goods_receipts, key=lambda g: g.grn_id):
            self._grns[grn.po_id].append(grn)
        self._ledger = sorted(dataset.invoices, key=lambda inv: inv.ledger_key)

    def get_vendor(self, vendor_id: str) -> Vendor:
        try:
            return self._vendors[vendor_id]
        except KeyError:
            raise NotFoundError("vendor", vendor_id) from None

    def get_purchase_order(self, po_id: str) -> PurchaseOrder:
        try:
            return self._pos[po_id]
        except KeyError:
            raise NotFoundError("purchase order", po_id) from None

    def get_goods_receipts(self, po_id: str) -> tuple[GoodsReceipt, ...]:
        return tuple(self._grns.get(po_id, ()))

    def get_invoice(self, invoice_id: str) -> Invoice:
        try:
            return self._invoices[invoice_id]
        except KeyError:
            raise NotFoundError("invoice", invoice_id) from None

    def list_invoice_ids(self) -> tuple[str, ...]:
        return tuple(inv.invoice_id for inv in self._ledger)

    def prior_invoices(self, invoice: Invoice) -> tuple[Invoice, ...]:
        return tuple(
            other
            for other in self._ledger
            if other.vendor_id == invoice.vendor_id and other.ledger_key < invoice.ledger_key
        )
