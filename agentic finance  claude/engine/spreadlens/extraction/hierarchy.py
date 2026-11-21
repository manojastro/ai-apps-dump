"""Build statement hierarchy (headings, totals, parent totals) from row order and labels.

Each heading opens a frame. A 'Total X' row closes the frame whose heading is 'X' (or the
innermost open frame), and every row collected in the closed frames becomes a child of that
total. Rows consumed by an inner total reach outer groups only through that inner total, so
parent totals and their child rows are never double counted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from spreadlens.extraction.classify import is_subtotal_like, is_total_label, section_tag
from spreadlens.extraction.types import RawRow

NET_CASH = re.compile(r"^\s*net\s+cash\s+(?:flows?\s+)?(?:from|used\s+in|generated\s+from|provided\s+by)?\s*(?:\(used\s+in\)\s*)?(operating|investing|financing)\s+activities", re.I)
MAJOR = {"assets", "equity_and_liabilities", "income", "expenses", "operating", "investing", "financing"}


def _norm(s: str) -> str:
    s = re.sub(r"^\s*(\(?[a-z]\)|\(?[ivx]+\)|[a-z]\.|\d+\.)\s*", "", s.lower())
    s = re.sub(r"^\s*total\s+", "", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class _Frame:
    heading: RawRow | None
    level: int
    items: list[RawRow] = field(default_factory=list)


def _matches(heading: RawRow, total_norm: str) -> bool:
    h = _norm(heading.label)
    return bool(h) and (h == total_norm or total_norm.startswith(h) or h.startswith(total_norm))


def assign_hierarchy(rows: list[RawRow]) -> None:
    stack: list[_Frame] = [_Frame(None, -1)]

    def close_top() -> None:
        f = stack.pop()
        stack[-1].items.extend(f.items)

    for r in rows:
        if r.is_header:
            tag = section_tag(r.label)
            if tag in MAJOR:
                while len(stack) > 1:
                    close_top()
            else:
                while len(stack) > 1 and stack[-1].level >= r.level and stack[-1].heading is not None \
                        and section_tag(stack[-1].heading.label) not in (MAJOR | {"liabilities"}):
                    close_top()
            stack.append(_Frame(r, r.level))
            r.section_path = [f.heading.label.strip() for f in stack[1:-1] if f.heading is not None]
            continue

        r.section_path = [f.heading.label.strip() for f in stack[1:] if f.heading is not None]
        if is_total_label(r.label) or (r.is_total and NET_CASH.match(r.label)):
            r.is_total = True
            target = _norm(r.label)
            if NET_CASH.match(r.label):
                kind = NET_CASH.match(r.label).group(1).lower()  # type: ignore[union-attr]
                idx = next((i for i in range(len(stack) - 1, 0, -1) if stack[i].heading is not None
                            and section_tag(stack[i].heading.label) == kind), None)
                # Only a clean list of line items forms a group; intermediate subtotals would double count.
                if idx is not None and any(is_subtotal_like(c.label) for f in stack[idx:] for c in f.items):
                    while len(stack) > idx:
                        close_top()
                    stack[-1].items.append(r)
                    continue
            else:
                idx = next((i for i in range(len(stack) - 1, 0, -1) if stack[i].heading is not None and _matches(stack[i].heading, target)), None)
                if idx is None and len(stack) > 1:
                    idx = len(stack) - 1
            if idx is None:
                stack[-1].items.append(r)
                continue
            children: list[RawRow] = []
            while len(stack) > idx:
                children = stack.pop().items + children
            for c in children:
                if c.parent_total_index is None:
                    c.parent_total_index = r.row_index
            stack[-1].items.append(r)
            continue
        stack[-1].items.append(r)
