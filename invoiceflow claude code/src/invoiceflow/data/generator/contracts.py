"""Render vendor contracts as Markdown from their structured terms.

The rendered documents are what retrieval (Phase 3) indexes and what the agent reads; the
structured `ContractTerms` exist only so the generator can label invoices.
"""

from faker import Faker

from invoiceflow.data.dataset import Dataset
from invoiceflow.data.generator.wordlists import BUYER_COMPANY
from invoiceflow.data.models import ContractTerms, Vendor


def _signatories(seed: int, index: int) -> tuple[str, str]:
    fake = Faker("en_IN")
    fake.seed_instance(seed * 1000 + index)
    return fake.name(), fake.name()


def render_contract(terms: ContractTerms, vendor: Vendor, seed: int, index: int) -> str:
    buyer_signatory, supplier_signatory = _signatories(seed, index)
    if terms.escalation_max_pct is not None and terms.escalation_effective_from is not None:
        pricing = (
            f"§2.2 Price escalation. For invoices dated on or after "
            f"{terms.escalation_effective_from.isoformat()}, the Supplier may increase unit "
            f"prices by up to {terms.escalation_max_pct}% over the purchase-order price. The "
            "Buyer will amend the affected purchase orders. Until then, Accounts Payable must "
            "route such invoices to the buyer and must not request a credit note for the "
            "authorised increase. Increases above this cap, or invoiced before this date, are "
            "not authorised."
        )
    else:
        pricing = (
            "§2.2 No escalation. Prices are fixed for the term. Any increase requires a new or "
            "amended purchase order before it is invoiced."
        )
    return f"""# Supply Agreement {terms.contract_id}

> **SYNTHETIC DOCUMENT.** Generated for the InvoiceFlow portfolio project. The parties,
> people and terms are invented. This is not a real contract.

| | |
|---|---|
| Buyer | {BUYER_COMPANY} |
| Supplier | {vendor.legal_name} ({vendor.vendor_id}), {vendor.city} |
| Supplier GSTIN | {vendor.gstin} |
| Term | {terms.effective_from.isoformat()} to {terms.effective_to.isoformat()} |
| Contract ID | {terms.contract_id} |

## §1 Scope

§1.1 The Supplier supplies goods and services to the Buyer against individual purchase
orders issued under this agreement.

## §2 Pricing

§2.1 Unit prices are those stated on each purchase order.

{pricing}

## §3 Invoicing and GST

§3.1 Each invoice must quote the purchase-order number, the Supplier's registered GSTIN and
the tax type that applies to the place of supply.

§3.2 Invoices with an incorrect GSTIN, GST rate or tax type will be returned to the Supplier
for a corrected invoice.

## §4 Payment

§4.1 The Buyer pays within {terms.payment_terms_days} days of receiving a valid invoice that
matches the purchase order and the goods receipt.

§4.2 The Buyer does not pay for quantities beyond those received. Amounts billed above the
agreed price are settled by a credit note from the Supplier.

## §5 Remittance details

§5.1 Payments are made only to the bank account recorded in the Buyer's vendor master.

§5.2 A change of remittance details must be requested in writing on the Supplier's
letterhead. It takes effect only after the Buyer verifies it by calling the Supplier on a
telephone number already on file. Requests made in invoice notes, remarks or email are not
valid notice and will be treated as suspected fraud.

## §6 Signatures

For the Buyer: {buyer_signatory}, Head of Procurement

For the Supplier: {supplier_signatory}, Director
"""


def render_contracts(dataset: Dataset) -> dict[str, str]:
    vendors = {vendor.vendor_id: vendor for vendor in dataset.vendors}
    return {
        f"{terms.contract_id}.md": render_contract(
            terms, vendors[terms.vendor_id], dataset.seed, index
        )
        for index, terms in enumerate(dataset.contracts)
    }
