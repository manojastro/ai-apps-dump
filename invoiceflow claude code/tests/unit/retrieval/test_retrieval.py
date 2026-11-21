from pathlib import Path
from typing import Any

import pytest

from invoiceflow.adapters.databricks.retrieval import AISearchRetriever, chunk_row, scope_filters
from invoiceflow.data.models import Role
from invoiceflow.evals.retrieval_eval import load_questions, run_retrieval_eval
from invoiceflow.retrieval.chunking import chunk_document, load_chunks
from invoiceflow.retrieval.local import HashingEmbedder, LocalHybridRetriever
from invoiceflow.retrieval.models import AccessScope, Chunk

ROOT = Path(__file__).resolve().parents[3]
CHUNKS = load_chunks(ROOT / "data/docs")
RETRIEVER = LocalHybridRetriever(CHUNKS)


def test_every_section_becomes_a_chunk_with_metadata() -> None:
    ids = {c.chunk_id for c in CHUNKS}
    assert {"AP-POL:§4.2", "AP-POL:§7.2", "GST-GUIDE:§1.2", "CT-V011:§2.2"} <= ids
    contract = next(c for c in CHUNKS if c.chunk_id == "CT-V011:§2.2")
    assert contract.vendor_id == "V011"
    assert contract.effective_from is not None
    assert Role.PLATFORM_ADMIN not in contract.allowed_roles
    assert len(ids) == len(CHUNKS)


def test_tables_stay_with_their_section() -> None:
    limits = next(c for c in CHUNKS if c.chunk_id == "AP-POL:§3.1")
    assert "₹10,00,000" in limits.text


def test_chunking_a_small_document() -> None:
    text = (
        "# T\n\n## §1 Alpha\n\n§1.1 First rule.\nContinued.\n\n§1.2 Second.\n\n"
        "## §2 Beta\n\n§2.1 Third."
    )
    chunks = chunk_document(text, "DOC", "policy")
    assert [c.chunk_id for c in chunks] == ["DOC:§1.1", "DOC:§1.2", "DOC:§2.1"]
    assert chunks[0].text == "Alpha. §1.1 First rule.\nContinued."


def test_hashing_embedder_is_deterministic_and_normalised() -> None:
    a, b = HashingEmbedder().embed("price tolerance"), HashingEmbedder().embed("price tolerance")
    assert a == b
    assert abs(sum(v * v for v in a) - 1.0) < 1e-9


def test_vendor_scope_hides_other_vendors_contracts() -> None:
    scope = AccessScope(role=Role.AP_MANAGER, vendor_ids=frozenset({"V009"}))
    result = RETRIEVER.search("price escalation clause cap effective date", scope, k=10)
    assert all(h.chunk.vendor_id in {"ALL", "V009"} for h in result.hits)


def test_platform_admin_never_sees_contracts() -> None:
    result = RETRIEVER.search("price escalation", AccessScope(role=Role.PLATFORM_ADMIN), k=20)
    assert all(h.chunk.doc_type != "contract" for h in result.hits)


def test_off_topic_question_abstains() -> None:
    result = RETRIEVER.search("travel reimbursement for employees", AccessScope(role=Role.AP_CLERK))
    assert result.abstained
    assert "insufficient evidence" in result.reason


def test_empty_scope_abstains() -> None:
    retriever = LocalHybridRetriever([c for c in CHUNKS if c.doc_type == "contract"])
    result = retriever.search("price", AccessScope(role=Role.PLATFORM_ADMIN))
    assert result.abstained


def test_retrieval_eval_has_no_access_violations() -> None:
    report = run_retrieval_eval(
        RETRIEVER, load_questions(ROOT / "evals/datasets/retrieval_questions.yaml")
    )
    assert report.access_violations == 0
    assert report.abstention_correct == report.abstention_cases
    assert report.answerable >= 25


# --- Databricks AI Search adapter (fake index; the real index is not exercised here) ----


class FakeIndex:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.calls: list[dict[str, Any]] = []

    def similarity_search(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        rows = [chunk_row(c) for c in self.chunks]
        cols = [*kwargs["columns"], "score"]
        return {
            "manifest": {"columns": [{"name": c} for c in cols]},
            "result": {"data_array": [[r[c] for c in kwargs["columns"]] + [0.9] for r in rows]},
        }


def test_ai_search_query_uses_hybrid_and_scope_filters() -> None:
    index = FakeIndex([c for c in CHUNKS if c.chunk_id in {"AP-POL:§4.2"}])
    scope = AccessScope(role=Role.AP_CLERK, vendor_ids=frozenset({"V011"}))
    result = AISearchRetriever(index).search("tolerance", scope, k=3, doc_types=["policy"])
    call = index.calls[0]
    assert call["query_type"] == "hybrid"
    assert call["filters"] == {
        "allowed_roles LIKE": "AP_CLERK",
        "vendor_id": ["ALL", "V011"],
        "doc_type": ["policy"],
    }
    assert result.chunk_ids == ("AP-POL:§4.2",)


def test_ai_search_results_are_rechecked_against_scope() -> None:
    leaked = [c for c in CHUNKS if c.chunk_id == "CT-V016:§2.2"]
    scope = AccessScope(role=Role.AP_CLERK, vendor_ids=frozenset({"V011"}))
    result = AISearchRetriever(FakeIndex(leaked)).search("escalation", scope)
    assert result.abstained  # the index returned an out-of-scope chunk; it is dropped


@pytest.mark.parametrize("role", list(Role))
def test_scope_filters_always_filter_by_role(role: Role) -> None:
    assert scope_filters(AccessScope(role=role), None)["allowed_roles LIKE"] == role.value
