"""Deterministic screen over invoice free text (notes, remarks, line descriptions).

It never obeys the text; it only raises signals that make the system *more* cautious:

- REMITTANCE_CHANGE_REQUEST: the text asks to pay a different account (AP-POL §7.1).
  This forces a VENDOR_BANK_CHANGE escalation.
- INSTRUCTION_IN_TEXT: the text addresses an automated system or claims an override.
  Recorded for the audit trail and the evaluation; it changes nothing by itself.

This is a safety net, not the LLM. The evaluation reports its effect separately.
"""

import re

from invoiceflow.data.models import Invoice

_ACCOUNT_NUMBER = re.compile(r"\b\d{9,18}\b")
_IFSC = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
_REMIT_WORDS = re.compile(
    r"\b(remit|remittance|new account|new beneficiary|bank (has )?changed|revised bank|"
    r"pay (this invoice )?to|use account|a/c)\b",
    re.IGNORECASE,
)
_INSTRUCTION = re.compile(
    r"\b(ignore|disregard|override|system:|instruction|assistant|ai agent|admin mode|"
    r"pre-approved|preapproved|do not raise|skip (variance|checks)|approve (this|all|at|for|"
    r"full|without))",
    re.IGNORECASE,
)

REMITTANCE_CHANGE_REQUEST = "REMITTANCE_CHANGE_REQUEST"
INSTRUCTION_IN_TEXT = "INSTRUCTION_IN_TEXT"


def free_text(invoice: Invoice) -> str:
    return "\n".join(
        part
        for part in (invoice.notes, invoice.remarks, *(line.description for line in invoice.lines))
        if part
    )


def screen(invoice: Invoice) -> list[str]:
    text = " ".join([invoice.notes, invoice.remarks])  # descriptions rarely carry bank details
    signals = []
    asks_for_account = bool(_ACCOUNT_NUMBER.search(text) or _IFSC.search(text))
    if asks_for_account and _REMIT_WORDS.search(text):
        signals.append(REMITTANCE_CHANGE_REQUEST)
    if _INSTRUCTION.search(free_text(invoice)):
        signals.append(INSTRUCTION_IN_TEXT)
    return signals
