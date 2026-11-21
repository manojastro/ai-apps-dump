"""Tests for the heading-aware splitter."""

from opscopilot.chunk import chunk_corpus, chunk_document
from opscopilot.models import Document


def _doc() -> Document:
    return Document(
        doc_id="KB0001",
        doc_type="kedb",
        title="Outlook password prompt",
        service="outlook",
        status="active",
        updated_at="2025-07-10",
        content=(
            "# Outlook password prompt\n"
            "## Symptoms\n\nOutlook keeps asking for password.\n\n"
            "## Workaround\n\nClear Credential Manager entries.\n"
        ),
        path="",
    )


def test_heading_chunks_carry_title_and_section() -> None:
    chunks = chunk_document(_doc())
    assert len(chunks) >= 2
    sections = {c.section for c in chunks}
    assert "Symptoms" in sections
    assert "Workaround" in sections
    for c in chunks:
        assert c.content.startswith("Outlook password prompt > ")
        assert c.doc_id == "KB0001"


def test_long_section_splits_at_paragraphs() -> None:
    paras = "\n\n".join(f"Paragraph {i} with enough words to matter. " * 8 for i in range(20))
    doc = Document(
        doc_id="SOP-X",
        doc_type="sop",
        title="Long SOP",
        service="vpn",
        status="active",
        updated_at="2025-01-01",
        content=f"# Long SOP\n\n## Steps\n\n{paras}\n",
        path="",
    )
    chunks = chunk_document(doc, max_chars=800)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.content) <= 900  # prefix + body under cap (with slack)
        assert c.content.startswith("Long SOP > Steps")


def test_chunk_ids_unique_and_corpus_order() -> None:
    docs = [_doc(), _doc().model_copy(update={"doc_id": "KB0002"})]
    chunks = chunk_corpus(docs)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    assert ids[0].startswith("KB0001")
