from __future__ import annotations

import re
from dataclasses import dataclass, field

PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
AADHAAR_RE = re.compile(r"\b[2-9][0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.IGNORECASE)
ACCOUNT_RE = re.compile(r"\b(?:account|a/c|acct|bank\s*a/c)[:\s#-]*([0-9]{9,18})\b", re.IGNORECASE)
CUSTOMER_RE = re.compile(r"\b(?:customer\s*id|cust\s*id|client\s*id)[:\s#-]*([A-Z0-9-]{6,})\b", re.IGNORECASE)
STATEMENT_RE = re.compile(r"\b(?:statement\s*(?:id|no|number)|ref\s*no)[:\s#-]*([A-Z0-9-]{6,})\b", re.IGNORECASE)
NAKED_ACCOUNT_RE = re.compile(r"\b[0-9]{11,18}\b")


@dataclass
class RedactionResult:
    text: str
    redacted: bool
    kinds: list[str] = field(default_factory=list)


def _luhn_ok(number: str) -> bool:
    digits = [int(ch) for ch in number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def redact_pii(text: str) -> RedactionResult:
    """Deterministic PII redaction. Never call an LLM for this step."""
    if not text:
        return RedactionResult(text="", redacted=False, kinds=[])
    kinds: list[str] = []
    out = text

    def _sub(pattern: re.Pattern[str], label: str, kind: str) -> None:
        nonlocal out
        if pattern.search(out):
            kinds.append(kind)
            out = pattern.sub(label, out)

    _sub(PAN_RE, "[REDACTED_PAN]", "pan")
    _sub(AADHAAR_RE, "[REDACTED_AADHAAR]", "aadhaar")
    _sub(IFSC_RE, "[REDACTED_IFSC]", "ifsc")
    if ACCOUNT_RE.search(out):
        kinds.append("bank_account")
        out = ACCOUNT_RE.sub("[REDACTED_BANK_ACCOUNT]", out)

    def card_repl(match: re.Match[str]) -> str:
        raw = re.sub(r"[^0-9]", "", match.group(0))
        if _luhn_ok(raw):
            kinds.append("card")
            return "[REDACTED_CARD]"
        return match.group(0)

    out = CARD_RE.sub(card_repl, out)
    out = CUSTOMER_RE.sub("[REDACTED_CUSTOMER_ID]", out)
    if CUSTOMER_RE.search(text):
        kinds.append("customer_id")
    out = STATEMENT_RE.sub("[REDACTED_STATEMENT_ID]", out)
    if STATEMENT_RE.search(text):
        kinds.append("statement_id")

    # Remaining long digit runs that look like accounts, but not amounts with commas/₹.
    def naked_acct(match: re.Match[str]) -> str:
        span_start = match.start()
        prefix = out[max(0, span_start - 12) : span_start].lower()
        if any(token in prefix for token in ("₹", "rs", "inr", "emi", "sip", "lakh", "value")):
            return match.group(0)
        kinds.append("bank_account")
        return "[REDACTED_BANK_ACCOUNT]"

    out = NAKED_ACCOUNT_RE.sub(naked_acct, out)
    unique_kinds = sorted(set(kinds))
    return RedactionResult(text=out, redacted=bool(unique_kinds), kinds=unique_kinds)
