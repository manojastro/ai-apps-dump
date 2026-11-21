"""Policy and contract search. Implementations must filter by access scope before ranking
and must abstain (empty hits, `abstained=True`) rather than return weak matches."""

from collections.abc import Sequence
from typing import Protocol

from invoiceflow.retrieval.models import AccessScope, DocType, RetrievalResult


class Retriever(Protocol):
    def search(
        self,
        query: str,
        scope: AccessScope,
        k: int = 5,
        doc_types: Sequence[DocType] | None = None,
    ) -> RetrievalResult: ...
