"""ERP write interface. Only the executor uses it, and only after an ALLOW decision."""

from typing import Any, Literal, Protocol

from invoiceflow.data.models import Frozen


class ErpResult(Frozen):
    decision_id: str
    idempotency_key: str
    kind: Literal["decision", "hold"]
    replayed: bool
    simulated: Literal[True] = True


class ErpConflictError(RuntimeError):
    """The idempotency key was already used for a different payload."""


class ErpUnavailableError(RuntimeError):
    """The ERP could not be reached after all retries."""


class ERPClient(Protocol):
    def post_decision(
        self, idempotency_key: str, invoice_id: str, action: str, payload: dict[str, Any]
    ) -> ErpResult: ...

    def create_hold(self, idempotency_key: str, invoice_id: str, reason: str) -> ErpResult: ...
