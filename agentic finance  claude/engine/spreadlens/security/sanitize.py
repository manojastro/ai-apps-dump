"""Untrusted-text handling: spreadsheet formula injection and prompt-injection detection."""

from __future__ import annotations

import re
from dataclasses import dataclass

FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "\n", "|", "%")


def excel_safe_text(value: object) -> str:
    """Neutralise text that a spreadsheet could interpret as a formula or DDE command.

    Prefixes with an apostrophe-equivalent: a leading single quote is stripped by Excel on
    display, so we use a visible zero-width-safe prefix "'" and also store as an explicit string.
    Numbers formatted as text (e.g. '-12.5') are left untouched because they are not formulas.
    """
    s = "" if value is None else str(value)
    s = s.replace("\x00", "")
    if s and s[0] in FORMULA_TRIGGERS and not re.fullmatch(r"[-+]?\d[\d,]*(\.\d+)?", s):
        return "'" + s
    return s


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?)", re.I),
    re.compile(r"\b(system|developer)\s+(prompt|instruction|message)s?\b", re.I),
    re.compile(r"\b(you\s+are\s+now|act\s+as)\b.{0,40}\b(assistant|agent|ai|model)\b", re.I),
    re.compile(r"\b(mark|set|treat)\b.{0,40}\b(checks?|validations?|exceptions?)\b.{0,20}\b(pass(ed)?|resolved|green)\b", re.I),
    re.compile(r"\b(approve|sign[\s-]?off)\b.{0,60}\bwithout\b.{0,30}\breview", re.I),
    re.compile(r"\b(api[\s_-]?keys?|secrets?|environment\s+variables|passwords?|tokens?)\b.{0,40}\b(print|reveal|show|send|exfiltrate|output)\b|\b(print|reveal|show|send|exfiltrate|output)\b.{0,40}\b(api[\s_-]?keys?|secrets?|environment\s+variables|credentials)\b", re.I),
    re.compile(r"\b(call|invoke|run|use)\s+the\s+\w+\s+tool\b", re.I),
    re.compile(r"\bto\s+any\s+(ai|llm|language\s+model|agent)\b", re.I),
]


@dataclass
class InjectionFinding:
    pattern: str
    excerpt: str
    location: str


def detect_injection(text: str, location: str) -> list[InjectionFinding]:
    out = []
    for pat in INJECTION_PATTERNS:
        m = pat.search(text)
        if m:
            a, b = max(0, m.start() - 40), min(len(text), m.end() + 40)
            out.append(InjectionFinding(pat.pattern[:60], text[a:b].replace("\n", " "), location))
    return out


def wrap_untrusted(text: str, tag: str = "document_data") -> str:
    """Delimit document content for a model prompt. The agent instructions say content inside
    these tags is data and must never be followed as instructions."""
    clean = text.replace(f"</{tag}>", f"</ {tag}>")
    return f"<{tag}>\n{clean}\n</{tag}>"
