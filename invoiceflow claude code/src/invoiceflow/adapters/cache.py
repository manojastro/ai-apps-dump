"""Read-through cache for any APDataReader.

The graph re-reads the same invoice, PO and vendor in several nodes. Against Databricks each
read is a SQL Statement API round trip, so a batch run wraps the reader in this cache. Safe
because AP master data is read-only for the agent and static for the length of a run; do
not use it in a long-lived service where invoices change underneath.
"""

from invoiceflow.data.models import GoodsReceipt, Invoice, PurchaseOrder, Vendor
from invoiceflow.ports.data import APDataReader


class CachingReader:
    def __init__(self, inner: APDataReader) -> None:
        self._inner = inner
        self._vendors: dict[str, Vendor] = {}
        self._pos: dict[str, PurchaseOrder] = {}
        self._grns: dict[str, tuple[GoodsReceipt, ...]] = {}
        self._invoices: dict[str, Invoice] = {}
        self._prior: dict[str, tuple[Invoice, ...]] = {}
        self._ids: tuple[str, ...] | None = None

    def get_vendor(self, vendor_id: str) -> Vendor:
        if vendor_id not in self._vendors:
            self._vendors[vendor_id] = self._inner.get_vendor(vendor_id)
        return self._vendors[vendor_id]

    def get_purchase_order(self, po_id: str) -> PurchaseOrder:
        if po_id not in self._pos:
            self._pos[po_id] = self._inner.get_purchase_order(po_id)
        return self._pos[po_id]

    def get_goods_receipts(self, po_id: str) -> tuple[GoodsReceipt, ...]:
        if po_id not in self._grns:
            self._grns[po_id] = self._inner.get_goods_receipts(po_id)
        return self._grns[po_id]

    def get_invoice(self, invoice_id: str) -> Invoice:
        if invoice_id not in self._invoices:
            self._invoices[invoice_id] = self._inner.get_invoice(invoice_id)
        return self._invoices[invoice_id]

    def list_invoice_ids(self) -> tuple[str, ...]:
        if self._ids is None:
            self._ids = self._inner.list_invoice_ids()
        return self._ids

    def prior_invoices(self, invoice: Invoice) -> tuple[Invoice, ...]:
        if invoice.invoice_id not in self._prior:
            prior = self._inner.prior_invoices(invoice)
            for p in prior:
                self._invoices.setdefault(p.invoice_id, p)
            self._prior[invoice.invoice_id] = prior
        return self._prior[invoice.invoice_id]
