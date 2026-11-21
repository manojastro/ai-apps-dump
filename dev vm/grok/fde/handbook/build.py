#!/usr/bin/env python3
"""Build the FDE + Agentic AI career handbook .docx."""
from pathlib import Path

from handbook.theme import Book, init_document
from handbook.part_a import cover, front_matter, part1, part2, part3, part4
from handbook.part_b import part5, part6, part7, part8
from handbook.part_c import part9, part10, part11, part12, references


def main():
    out = Path("/home/ubuntu/grok/fde/FDE_Agentic_AI_Engineering_Handbook_v1.0.docx")
    doc = init_document()
    b = Book(doc)
    cover(b)
    front_matter(b)
    part1(b)
    part2(b)
    part3(b)
    part4(b)
    part5(b)
    part6(b)
    part7(b)
    part8(b)
    part9(b)
    part10(b)
    part11(b)
    part12(b)
    references(b)
    core = doc.core_properties
    core.title = "Forward Deployed Engineer & Agentic AI Engineer Handbook"
    core.subject = "Career, production, and interview handbook"
    core.author = "Study copy compiled 15 September 2026"
    core.comments = "Version 1.0. Update the TOC field in Microsoft Word (F9) after opening."
    doc.save(out)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
