"""Retrieval data types: chunks with access metadata, scopes, and results."""

from datetime import date
from typing import Literal

from invoiceflow.data.models import Frozen, Role

DocType = Literal["policy", "gst_guide", "contract"]
ALL_ROLES: tuple[Role, ...] = tuple(Role)
CONTRACT_ROLES: tuple[Role, ...] = (
    Role.AP_CLERK,
    Role.AP_MANAGER,
    Role.FINANCE_CONTROLLER,
    Role.AUDITOR,
)
GLOBAL_VENDOR = "ALL"  # vendor_id for documents that apply to every vendor


class Chunk(Frozen):
    chunk_id: str  # "<doc_id>:<section>", e.g. "AP-POL:§4.2"
    doc_id: str
    doc_type: DocType
    section: str
    title: str
    text: str
    vendor_id: str = GLOBAL_VENDOR
    effective_from: date | None = None
    effective_to: date | None = None
    allowed_roles: tuple[Role, ...] = ALL_ROLES


class AccessScope(Frozen):
    """Who is asking. `vendor_ids=None` means every vendor; the agent is scoped to the one
    vendor whose invoice it is handling."""

    role: Role
    vendor_ids: frozenset[str] | None = None

    def allows(self, chunk: Chunk) -> bool:
        if self.role not in chunk.allowed_roles:
            return False
        if chunk.vendor_id == GLOBAL_VENDOR:
            return True
        return self.vendor_ids is None or chunk.vendor_id in self.vendor_ids


class Hit(Frozen):
    chunk: Chunk
    score: float


class RetrievalResult(Frozen):
    query: str
    hits: tuple[Hit, ...]
    abstained: bool = False
    reason: str = ""

    @property
    def chunk_ids(self) -> tuple[str, ...]:
        return tuple(hit.chunk.chunk_id for hit in self.hits)
