# -*- coding: utf-8 -*-
"""Assemble Comprehensive_AI_Roles_Career_Transition_Manual.docx."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_builder import new_document
import content_intro
import content_roles_1
import content_roles_2
import content_roles_3
import content_roles_4
import content_roles_5
import content_crossrole

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Comprehensive_AI_Roles_Career_Transition_Manual.docx")


def main() -> None:
    doc = new_document()

    content_intro.build(doc)
    content_roles_1.build_aiops(doc)
    content_roles_2.build_cloudai(doc)
    content_roles_3.build_automation(doc)
    content_roles_3.build_aisecurity(doc)
    content_roles_4.build_fde(doc)
    content_roles_4.build_genai(doc)
    content_roles_5.build_solutions(doc)
    content_crossrole.build(doc)

    # Word's implicit final paragraph after the last table can spill onto a
    # blank trailing page; shrink it to 1pt so it never occupies visible space.
    from docx.shared import Pt as _Pt
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _El
    last_p = doc.paragraphs[-1]
    p_pr = last_p._p.get_or_add_pPr()
    r_pr = _El("w:rPr")
    sz = _El("w:sz")
    sz.set(_qn("w:val"), "2")
    r_pr.append(sz)
    p_pr.append(r_pr)
    last_p.paragraph_format.space_before = _Pt(0)
    last_p.paragraph_format.space_after = _Pt(0)
    last_p.paragraph_format.line_spacing = 1.0

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
