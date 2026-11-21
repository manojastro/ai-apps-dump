"""Read-only access to AP data. Every backend implements this; nothing else touches storage.

Ground-truth labels are not reachable through this interface on purpose: the agent's tools
are built on it, and they must never see the answers.
"""

from typing import Protocol

from invoiceflow.data.models import GoodsReceipt, Invoice, PurchaseOrder, Vendor


class NotFoundError(LookupError):
    """A structured 'not found': which kind of record, and which key."""

    def __init__(self, entity: str, key: str) -> None:
        super().__init__(f"{entity} {key!r} not found")
        self.entity = entity
        self.key = key


class APDataReader(Protocol):
    def get_vendor(self, vendor_id: str) -> Vendor: ...

    def get_purchase_order(self, po_id: str) -> PurchaseOrder: ...

    def get_goods_receipts(self, po_id: str) -> tuple[GoodsReceipt, ...]:
        """All receipts for a PO, ordered by GRN id. Empty if none were recorded."""
        ...

    def get_invoice(self, invoice_id: str) -> Invoice: ...

    def list_invoice_ids(self) -> tuple[str, ...]:
        """Every invoice id in ledger order (received date, then id)."""
        ...

    def prior_invoices(self, invoice: Invoice) -> tuple[Invoice, ...]:
        """Invoices from the same vendor received before `invoice`, in ledger order."""
        ...
