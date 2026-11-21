"""Extract supporting note sections from notes pages."""

from __future__ import annotations

import re

from spreadlens.extraction.classify import detect_scope
from spreadlens.extraction.types import PageText, RawNote, group_lines

HEADING = re.compile(r"^(?:note\s+)?(\d{1,3})[\.:]?\s+([A-Z][A-Za-z ,&'\-()/]{2,80})$")


def extract_notes(pages: list[PageText], note_pages: list[int]) -> list[RawNote]:
    out: list[RawNote] = []
    current: RawNote | None = None
    scope = None
    for pg in pages:
        if pg.page not in note_pages:
            continue
        lines = [" ".join(w.text for w in line) for line in group_lines(pg.words)]
        scope = detect_scope(" ".join(lines[:3])) or scope
        for line in lines:
            m = HEADING.match(line.strip())
            if m and not re.search(r"\d{3,}", m.group(2)):
                current = RawNote(note_ref=m.group(1), title=m.group(2).strip(), text="", page=pg.page, scope=scope)
                out.append(current)
            elif current is not None:
                current.text += line + "\n"
    return out
