"""Recognise statement titles, scope, section headings and total rows from text."""

from __future__ import annotations

import re

TITLE_PATTERNS = [
    ("balance_sheet", re.compile(r"\b(balance\s+sheet|statement\s+of\s+financial\s+position)\b", re.I)),
    ("income_statement", re.compile(r"\b(statement\s+of\s+profit\s+(and|&|or)\s+loss|profit\s+(and|&)\s+loss\s+(account|statement)|income\s+statement|statement\s+of\s+(comprehensive\s+)?income|statement\s+of\s+operations)\b", re.I)),
    ("cash_flow", re.compile(r"\b(cash\s+flows?\s+statement|statement\s+of\s+cash\s+flows?)\b", re.I)),
]
NOTES_TITLE = re.compile(r"\bnotes?\s+(to|forming\s+part\s+of)\s+(the\s+)?(standalone\s+|consolidated\s+)?financial\s+statements\b", re.I)
NOTE_HEADING = re.compile(r"^\s*(?:note\s+)?(\d{1,3})[\.:]?\s+([A-Z][A-Za-z ,&'\-()/]{2,80})$")
STOP_MARKERS = re.compile(r"(as per our report of even date|for and on behalf of the board|significant accounting policies|the accompanying notes)", re.I)

TOTAL_LABEL = re.compile(r"^\s*total\b", re.I)
SUBTOTAL_LIKE = re.compile(
    r"^\s*(gross\s+profit|profit\s+before\s+tax|profit\s+(for|after)\s+(the\s+)?(year|period|tax)|net\s+profit|"
    r"net\s+cash\s+(from|used|generated|flow|provided)|cash\s+generated\s+from\s+operations|net\s+(increase|decrease|change)|operating\s+profit|"
    r"cash\s+and\s+cash\s+equivalents\s+at\s+the\s+end)", re.I)

SECTION_KEYWORDS = [
    ("non_current_assets", re.compile(r"^non[\s\-]?current\s+assets$", re.I)),
    ("current_assets", re.compile(r"^current\s+assets$", re.I)),
    ("assets", re.compile(r"^assets$", re.I)),
    ("equity_and_liabilities", re.compile(r"^equity\s+and\s+liabilities$", re.I)),
    ("equity", re.compile(r"^(equity|shareholders'?\s+funds)$", re.I)),
    ("non_current_liabilities", re.compile(r"^non[\s\-]?current\s+liabilities$", re.I)),
    ("current_liabilities", re.compile(r"^current\s+liabilities$", re.I)),
    ("liabilities", re.compile(r"^liabilities$", re.I)),
    ("income", re.compile(r"^(income|revenue)$", re.I)),
    ("expenses", re.compile(r"^expenses$", re.I)),
    ("tax", re.compile(r"^(tax\s+expense|income\s+tax\s+expense)s?:?$", re.I)),
    ("eps", re.compile(r"^earnings\s+per\s+(equity\s+)?share", re.I)),
    ("operating", re.compile(r"cash\s+flows?\s+(from|used\s+in)\s+operating\s+activities", re.I)),
    ("investing", re.compile(r"cash\s+flows?\s+(from|used\s+in)\s+investing\s+activities", re.I)),
    ("financing", re.compile(r"cash\s+flows?\s+(from|used\s+in)\s+financing\s+activities", re.I)),
]


def classify_title(text: str) -> str | None:
    for kind, pat in TITLE_PATTERNS:
        if pat.search(text):
            return kind
    return None


def detect_scope(text: str) -> str | None:
    t = text.lower()
    if "consolidated" in t:
        return "consolidated"
    if "standalone" in t or "stand-alone" in t:
        return "standalone"
    return None


def section_tag(label: str) -> str | None:
    clean = re.sub(r"^\s*(\(?[a-z]\)|\(?[ivx]+\)|[a-z]\.|\d+\.)\s*", "", label.strip()).strip(" :")
    for tag, pat in SECTION_KEYWORDS:
        if pat.search(clean):
            return tag
    return None


def is_total_label(label: str) -> bool:
    return bool(TOTAL_LABEL.match(label))


def is_subtotal_like(label: str) -> bool:
    return bool(TOTAL_LABEL.match(label) or SUBTOTAL_LIKE.match(label))


def unit_type_for(label: str, section_path: list[str]) -> str:
    t = (label + " " + " ".join(section_path)).lower()
    if re.search(r"earnings\s+per\s+(equity\s+)?share|\beps\b|\(in ₹\)|\(in rs\.?\)|per\s+(equity\s+)?share", t) \
            or label.strip().lower() in ("basic", "diluted"):
        return "eps"
    if re.search(r"number\s+of\s+(equity\s+)?shares|no\.\s+of\s+shares", t):
        return "shares"
    if "%" in label or re.search(r"\bpercent(age)?\b|margin\s*\(%\)", t):
        return "percent"
    return "monetary"
