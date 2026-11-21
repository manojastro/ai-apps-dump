"""Duplicate invoice screening against invoices received earlier from the same vendor.

Exact duplicate: same vendor and the same normalized invoice number, on any date.
Near duplicate: same vendor, same gross amount, invoice dates at most `window_days` apart,
and a *different* normalized number (the spec's "different number format").

Normalization uppercases, splits into letter runs and digit runs, strips leading zeros
from digit runs, and joins them, so "CF-2026-0042" and "cf/2026/42" both become "CF202642".
Digit runs with no separator between them ("CF20260042") stay one run: a known limitation.
"""

import re
from collections.abc import Iterable

from invoiceflow.core.findings import Finding, FindingReason
from invoiceflow.data.models import ExceptionCode, Invoice

_RUNS = re.compile(r"[A-Z]+|[0-9]+")


def normalize_invoice_number(number: str) -> str:
    runs = _RUNS.findall(number.upper())
    return "".join(str(int(run)) if run.isdigit() else run for run in runs)


def find_duplicates(
    invoice: Invoice, prior_invoices: Iterable[Invoice], window_days: int
) -> list[Finding]:
    number = normalize_invoice_number(invoice.invoice_number)
    findings: list[Finding] = []
    for prior in sorted(prior_invoices, key=lambda inv: inv.ledger_key):
        if prior.vendor_id != invoice.vendor_id or prior.ledger_key >= invoice.ledger_key:
            continue
        evidence = {
            "prior_invoice_id": prior.invoice_id,
            "prior_invoice_number": prior.invoice_number,
            "prior_invoice_date": prior.invoice_date.isoformat(),
        }
        if normalize_invoice_number(prior.invoice_number) == number:
            findings.append(
                Finding(
                    code=ExceptionCode.DUPLICATE_INVOICE,
                    reason=FindingReason.EXACT_DUPLICATE,
                    message=f"same invoice number as {prior.invoice_id}",
                    evidence=evidence,
                )
            )
        elif (
            prior.gross_total == invoice.gross_total
            and abs((invoice.invoice_date - prior.invoice_date).days) <= window_days
        ):
            findings.append(
                Finding(
                    code=ExceptionCode.DUPLICATE_INVOICE,
                    reason=FindingReason.NEAR_DUPLICATE,
                    message=(
                        f"same gross amount as {prior.invoice_id} within {window_days} days, "
                        "different invoice number"
                    ),
                    evidence=evidence,
                )
            )
    return findings
