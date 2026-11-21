"""SIMULATED ERP API. Not a real ERP: it records decisions so the agent's executor has
something idempotent to call.

Run: `uv run uvicorn invoiceflow.services.erp_sandbox.app:build --factory --port 8081`
"""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict

from invoiceflow.config import Settings
from invoiceflow.ports.erp import ErpConflictError
from invoiceflow.services.erp_sandbox.store import ErpStore


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoice_id: str
    action: str
    payload: dict[str, Any] = {}


class HoldIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoice_id: str
    reason: str


def create_app(store: ErpStore) -> FastAPI:
    app = FastAPI(title="InvoiceFlow sandbox ERP (SIMULATED)", version="1")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "simulated": True}

    @app.post("/decisions")
    def post_decision(
        body: DecisionIn, idempotency_key: str = Header(..., alias="Idempotency-Key")
    ) -> dict[str, Any]:
        try:
            result = store.record(
                idempotency_key, "decision", body.invoice_id, body.action, body.payload
            )
        except ErpConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return result.model_dump()

    @app.post("/holds")
    def create_hold(
        body: HoldIn, idempotency_key: str = Header(..., alias="Idempotency-Key")
    ) -> dict[str, Any]:
        try:
            result = store.record(
                idempotency_key, "hold", body.invoice_id, "HOLD_FOR_GRN", {"reason": body.reason}
            )
        except ErpConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return result.model_dump()

    @app.get("/decisions/{decision_id}")
    def get_decision(decision_id: str) -> dict[str, Any]:
        found = store.get(decision_id)
        if found is None:
            raise HTTPException(status_code=404, detail="no such decision")
        return found

    @app.get("/outbox")
    def outbox() -> list[dict[str, Any]]:
        return store.outbox()

    return app


def build() -> FastAPI:
    """Factory for uvicorn; nothing is created at import time."""
    return create_app(ErpStore(Path(Settings().invoiceflow_state_dir) / "erp_sandbox.db"))
