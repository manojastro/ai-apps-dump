"""Domain models shared by every layer.

All money is Decimal rounded to paise, quantities to 3 decimals and GST rates are
percentages (18 means 18%). Models are frozen so a value read from one backend can be
compared field-by-field with the same value read from another.

Free-text fields (`Invoice.notes`, `Invoice.remarks`, `InvoiceLine.description`) are
untrusted vendor input. Nothing in the deterministic core reads them.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from invoiceflow.core.money import to_money, to_quantity

Money = Annotated[Decimal, AfterValidator(to_money)]
Quantity = Annotated[Decimal, AfterValidator(to_quantity)]
GstRate = Annotated[Decimal, AfterValidator(to_money)]
StateCode = Annotated[str, Field(pattern=r"^[0-9]{2}$")]


class ExceptionCode(StrEnum):
    CLEAN = "CLEAN"
    PRICE_VARIANCE = "PRICE_VARIANCE"
    QTY_OVERBILLED = "QTY_OVERBILLED"
    MISSING_GRN = "MISSING_GRN"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    GST_MISMATCH = "GST_MISMATCH"
    PO_CLOSED = "PO_CLOSED"
    VENDOR_BANK_CHANGE = "VENDOR_BANK_CHANGE"


class Action(StrEnum):
    APPROVE = "APPROVE"
    HOLD_FOR_GRN = "HOLD_FOR_GRN"
    REQUEST_CREDIT_NOTE = "REQUEST_CREDIT_NOTE"
    REQUEST_CORRECTED_INVOICE = "REQUEST_CORRECTED_INVOICE"
    REJECT_DUPLICATE = "REJECT_DUPLICATE"
    ROUTE_TO_BUYER = "ROUTE_TO_BUYER"
    ESCALATE_FRAUD_REVIEW = "ESCALATE_FRAUD_REVIEW"


class Role(StrEnum):
    AP_CLERK = "AP_CLERK"
    AP_MANAGER = "AP_MANAGER"
    FINANCE_CONTROLLER = "FINANCE_CONTROLLER"
    AUDITOR = "AUDITOR"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class POStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Split(StrEnum):
    DEV = "dev"
    EVAL = "eval"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BankAccount(Frozen):
    ifsc: str = Field(pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    account_number: str = Field(pattern=r"^[0-9]{9,18}$", repr=False)

    @property
    def masked(self) -> str:
        """Safe for logs and traces: only the last 4 digits are shown."""
        return f"{self.ifsc}/{'X' * (len(self.account_number) - 4)}{self.account_number[-4:]}"


class Vendor(Frozen):
    vendor_id: str
    legal_name: str
    state_code: StateCode
    gstin: str
    pan: str
    bank: BankAccount
    city: str
    active: bool = True


class POLine(Frozen):
    line_no: int = Field(ge=1)
    item_code: str
    description: str
    quantity: Quantity
    unit_price: Money
    gst_rate: GstRate


class PurchaseOrder(Frozen):
    po_id: str
    vendor_id: str
    buyer_id: str
    po_date: date
    valid_until: date
    status: POStatus
    place_of_supply: StateCode
    lines: tuple[POLine, ...] = Field(min_length=1)

    def line(self, line_no: int) -> POLine | None:
        return next((line for line in self.lines if line.line_no == line_no), None)


class GRNLine(Frozen):
    po_line_no: int = Field(ge=1)
    quantity_received: Quantity


class GoodsReceipt(Frozen):
    grn_id: str
    po_id: str
    received_date: date
    lines: tuple[GRNLine, ...] = Field(min_length=1)


class InvoiceLine(Frozen):
    line_no: int = Field(ge=1)
    po_line_no: int = Field(ge=1)
    description: str
    quantity: Quantity
    unit_price: Money
    taxable_value: Money
    gst_rate: GstRate
    cgst: Money
    sgst: Money
    igst: Money

    @property
    def tax_total(self) -> Decimal:
        return self.cgst + self.sgst + self.igst


class Invoice(Frozen):
    invoice_id: str
    vendor_id: str
    invoice_number: str
    invoice_date: date
    received_date: date
    po_id: str
    supplier_gstin: str
    place_of_supply: StateCode
    bank: BankAccount
    lines: tuple[InvoiceLine, ...] = Field(min_length=1)
    gross_total: Money
    notes: str = ""
    remarks: str = ""

    @property
    def ledger_key(self) -> tuple[date, str]:
        """Order in which AP received invoices; earlier keys are 'prior' invoices."""
        return (self.received_date, self.invoice_id)


class ContractTerms(Frozen):
    """Structured truth behind a rendered contract document.

    The generator uses it to label invoices. It is never loaded into the AP tables:
    in the real world contracts are documents, so only the Markdown is searchable.
    """

    contract_id: str
    vendor_id: str
    effective_from: date
    effective_to: date
    payment_terms_days: int
    escalation_max_pct: Decimal | None = None
    escalation_effective_from: date | None = None


class GroundTruth(Frozen):
    """The expected answer for one invoice. Lives in the `eval` schema, never in `ap`."""

    invoice_id: str
    split: Split
    expected_exception: ExceptionCode
    expected_action: Action
    expected_required_approver: Role | None
    scenario: str
    adversarial_kind: str | None = None
    rationale: str
