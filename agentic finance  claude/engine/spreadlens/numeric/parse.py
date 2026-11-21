"""Parse raw numeric strings from financial statements into exact Decimals.

Ordinary code, no AI. The rules here are deliberately conservative: anything we cannot
read with certainty becomes `unreadable`, never a guessed number.

Value states (kept distinct everywhere downstream):
  value           a parsed, non-zero number
  zero            a reported zero ("0", "0.00", or a dash where the document defines dash = nil)
  missing         blank cell / no figure reported
  unreadable      text present but not a reliable number (OCR noise, broken grouping)
  not_applicable  "n/a", "NA", "not applicable"
  dash_ambiguous  "-" / "–" / "—" where the document does not say what a dash means
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

VALUE = "value"
ZERO = "zero"
MISSING = "missing"
UNREADABLE = "unreadable"
NOT_APPLICABLE = "not_applicable"
DASH_AMBIGUOUS = "dash_ambiguous"

VALUE_STATES = (VALUE, ZERO, MISSING, UNREADABLE, NOT_APPLICABLE, DASH_AMBIGUOUS)
HAS_NUMBER = (VALUE, ZERO)

_DASHES = {"-", "–", "—", "‒", "−", "--"}
_NA = {"n/a", "na", "n.a.", "n.a", "not applicable", "nm", "n.m."}
_CURRENCY_TOKENS = ("₹", "rs.", "rs", "inr", "$", "us$", "usd", "€", "eur", "£", "gbp")

# International grouping: 1,234,567.89    Indian grouping: 12,34,567.89
_INTL = re.compile(r"^\d{1,3}(,\d{3})+$")
_INDIAN = re.compile(r"^\d{1,2}(,\d{2})*,\d{3}$")
_PLAIN = re.compile(r"^\d+$")


@dataclass(frozen=True)
class ParseContext:
    dash_means_zero: bool = False  # set only when the document states its convention
    allow_trailing_minus: bool = True


@dataclass
class ParsedNumber:
    raw: str
    state: str
    value: Decimal | None = None
    decimals: int | None = None  # digits after the decimal point in the source (precision)
    unit_hint: str | None = None  # "percent" when a % sign is present
    grouping: str | None = None  # indian | international | none
    notes: list[str] = field(default_factory=list)

    @property
    def has_number(self) -> bool:
        return self.state in HAS_NUMBER


def parse_number(raw: str | None, ctx: ParseContext | None = None) -> ParsedNumber:
    ctx = ctx or ParseContext()
    if raw is None:
        return ParsedNumber(raw="", state=MISSING)
    text = str(raw).strip()
    if text == "":
        return ParsedNumber(raw=text, state=MISSING)

    lowered = text.lower()
    if lowered in _NA:
        return ParsedNumber(raw=text, state=NOT_APPLICABLE)
    if text in _DASHES:
        if ctx.dash_means_zero:
            return ParsedNumber(raw=text, state=ZERO, value=Decimal("0"), decimals=0,
                                notes=["dash interpreted as zero per document convention"])
        return ParsedNumber(raw=text, state=DASH_AMBIGUOUS,
                            notes=["dash meaning not established by the document"])

    s = text
    notes: list[str] = []
    negative = False
    unit_hint = None

    # Strip currency tokens (only at the edges).
    s_low = s.lower()
    for tok in _CURRENCY_TOKENS:
        if s_low.startswith(tok):
            s = s[len(tok):].strip()
            s_low = s.lower()
            notes.append(f"stripped currency token '{tok}'")
            break

    if s.endswith("%"):
        unit_hint = "percent"
        s = s[:-1].strip()

    # Parentheses mean negative.
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
        notes.append("parentheses interpreted as negative")
    elif s.startswith("(") or s.endswith(")"):
        return ParsedNumber(raw=text, state=UNREADABLE, notes=["unbalanced parenthesis"])

    if s[:1] in {"-", "−", "–"}:
        negative = not negative
        s = s[1:].strip()
        notes.append("leading minus")
    elif ctx.allow_trailing_minus and s.endswith("-") and len(s) > 1:
        negative = True
        s = s[:-1].strip()
        notes.append("trailing minus interpreted as negative")

    s = s.replace(" ", "").replace(" ", "").replace(" ", "")
    if s == "":
        return ParsedNumber(raw=text, state=UNREADABLE, notes=notes + ["no digits"])

    if s.count(".") > 1:
        return ParsedNumber(raw=text, state=UNREADABLE, notes=notes + ["multiple decimal points"])
    int_part, _, frac_part = s.partition(".")
    if frac_part and not frac_part.isdigit():
        return ParsedNumber(raw=text, state=UNREADABLE, notes=notes + ["non-digit characters in fraction"])

    if "," in int_part:
        if _INDIAN.match(int_part) and not _INTL.match(int_part):
            grouping = "indian"
        elif _INTL.match(int_part) and not _INDIAN.match(int_part):
            grouping = "international"
        elif _INTL.match(int_part) and _INDIAN.match(int_part):
            grouping = "international"  # e.g. 12,345 is valid in both systems; same value either way
        else:
            return ParsedNumber(raw=text, state=UNREADABLE, notes=notes + ["digit grouping matches neither Indian nor international pattern"])
        int_digits = int_part.replace(",", "")
    elif _PLAIN.match(int_part or "0"):
        grouping = "none"
        int_digits = int_part or "0"
    else:
        return ParsedNumber(raw=text, state=UNREADABLE, notes=notes + ["non-digit characters"])

    try:
        value = Decimal(f"{int_digits}.{frac_part}" if frac_part else int_digits)
    except InvalidOperation:
        return ParsedNumber(raw=text, state=UNREADABLE, notes=notes + ["invalid decimal"])

    if negative:
        value = -value
    decimals = len(frac_part)
    state = ZERO if value == 0 else VALUE
    if state == ZERO:
        value = Decimal("0")
    return ParsedNumber(raw=text, state=state, value=value, decimals=decimals, unit_hint=unit_hint,
                        grouping=grouping, notes=notes)


_NUMERIC_TOKEN = re.compile(r"^[\(\-−–]?[₹$€£]?\s?[\d,]+(\.\d+)?\)?-?%?$")


def looks_numeric(token: str) -> bool:
    """Whether a token is plausibly a numeric cell (used by layout parsing; not a parser)."""
    t = token.strip()
    if t in _DASHES:
        return True
    return bool(_NUMERIC_TOKEN.match(t))
