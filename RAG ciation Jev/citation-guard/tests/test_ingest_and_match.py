import re

from citation_guard.quote_match import (
    QuoteStatus,
    match_quote,
    normalize,
    normalize_text,
    passage_window,
)

# ------------------------------------------------------------------ ingest / cleaning


def test_page_header_footer_and_formfeed_removed(synth_doc):
    t = synth_doc.clean_text
    assert "[Page" not in t
    assert "RFC 9999" not in t
    assert "\f" not in t


def test_paragraph_split_by_page_break_is_rejoined(synth_doc):
    norm = normalize_text(synth_doc.clean_text)
    assert "the parser MUST reject widgets without one." in norm


def test_hyphen_rejoin_keeps_compound_hyphen(synth_doc):
    assert "case-sensitive strings" in synth_doc.clean_text
    assert "case-\n" not in synth_doc.clean_text


def test_sections_and_offsets(synth_doc):
    ids = [s.section_id for s in synth_doc.sections]
    assert ids == ["preamble", "1", "2"]
    for s in synth_doc.sections:
        assert synth_doc.clean_text[s.start:s.end] == s.text
    assert synth_doc.section("2").title == "Processing Rules"


def test_offset_map_points_to_raw_lines(synth_doc):
    off = synth_doc.clean_text.index("Processors SHOULD")
    raw_line = synth_doc.raw_line_at(off)
    from tests.conftest import SYNTH_RFC

    assert "Processors SHOULD" in SYNTH_RFC.split("\n")[raw_line - 1]


def test_real_rfc_clean(rfc_doc):
    t = rfc_doc.clean_text
    assert not re.search(r"\[Page \d+\]", t)
    assert not re.search(r"^RFC 7519\s{2,}", t, re.M)
    numbered = [s for s in rfc_doc.sections if re.match(r"^(\d+|[A-Z])(\.\d+)*$", s.section_id)]
    assert len(numbered) == 50
    assert rfc_doc.section("4.1.4").title == '"exp" (Expiration Time) Claim'


# ------------------------------------------------------------------ normalisation


def test_normalize_quotes_dashes_whitespace():
    s = "The “exp” claim — is  \n  OPTIONAL’s"
    norm, idx = normalize(s)
    assert norm == "The \"exp\" claim - is OPTIONAL's"
    assert len(idx) == len(norm) + 1
    assert s[idx[norm.index("OPTIONAL")]] == "O"


def test_normalize_nfkc():
    assert normalize_text("ﬁle Ａ") == "file A"  # ligature fi, fullwidth A


# ------------------------------------------------------------------ Check A


def test_found_in_cited_section(synth_doc):
    m = match_quote(synth_doc, "Processors SHOULD ignore unknown fields.", "2")
    assert m.status == QuoteStatus.FOUND_IN_CITED_SECTION
    assert synth_doc.clean_text[m.start:m.end] == "Processors SHOULD ignore unknown fields."


def test_found_with_curly_quotes_and_line_break(synth_doc):
    m = match_quote(synth_doc, 'The name field is a "case-sensitive" value.', "2")
    assert m.status == QuoteStatus.FOUND_IN_CITED_SECTION


def test_found_elsewhere(synth_doc):
    m = match_quote(synth_doc, "Processors SHOULD ignore unknown fields.", "1")
    assert m.status == QuoteStatus.FOUND_ELSEWHERE
    assert m.found_section_id == "2"


def test_not_found(synth_doc):
    m = match_quote(synth_doc, "Processors MAY ignore unknown fields.", "2")
    assert m.status == QuoteStatus.NOT_FOUND
    assert m.start is None
    assert m.closest_fuzzy_score is not None and m.closest_fuzzy_score > 80  # debug only


def test_too_short(synth_doc):
    m = match_quote(synth_doc, "MUST NOT", "2")
    assert m.status == QuoteStatus.QUOTE_TOO_SHORT


def test_case_sensitive(synth_doc):
    m = match_quote(synth_doc, "processors should ignore unknown fields.", "2")
    assert m.status == QuoteStatus.NOT_FOUND


def test_real_rfc_quote(rfc_doc):
    m = match_quote(rfc_doc, "Use of this claim is OPTIONAL.", "4.1.4")
    assert m.status == QuoteStatus.FOUND_IN_CITED_SECTION
    assert m.occurrences == 7  # every registered claim section ends with this sentence


# ------------------------------------------------------------------ passage window


def test_passage_stays_inside_section_and_contains_quote(rfc_doc):
    q = "the JWT MUST NOT be accepted for processing"
    m = match_quote(rfc_doc, q, "4.1.4")
    p = passage_window(rfc_doc, m.start, m.end, window=1500)
    sec = rfc_doc.section("4.1.4")
    assert sec.start <= p.start and p.end <= sec.end
    assert q in p.text
    assert p.section_id == "4.1.4"


def test_passage_size_and_sentence_snap(rfc_doc):
    q = "The \"aud\" (audience) claim identifies the recipients"
    m = match_quote(rfc_doc, q, "4.1.3")
    p = passage_window(rfc_doc, m.start, m.end, window=60)
    # Window limit respected (both sides), measured on the raw span.
    assert m.start - p.start <= 60 and p.end - m.end <= 60
    assert q in p.text
    # Right edge snapped back to a sentence end.
    assert p.text.rstrip().endswith(".")


def test_passage_large_window_in_long_section(rfc_doc):
    q = "Finally, note that it is an application decision which algorithms may"
    m = match_quote(rfc_doc, q, "7.2")
    p = passage_window(rfc_doc, m.start, m.end, window=1500)
    sec = rfc_doc.section("7.2")
    assert m.start - p.start <= 1500 and p.end - m.end <= 1500
    assert sec.start <= p.start and p.end <= sec.end
    # Left edge snapped: passage starts at a sentence start (capital letter or list marker).
    first = p.text.lstrip()[0]
    assert first.isupper() or first.isdigit()
