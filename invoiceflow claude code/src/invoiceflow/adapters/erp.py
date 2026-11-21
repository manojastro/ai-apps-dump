"""ERP clients. In-process (tests, Databricks jobs, where a laptop service is unreachable)
and HTTP with retries. Retries reuse the same idempotency key, so a timeout after the ERP
committed cannot create a second decision."""

import time
from typing import Any

import httpx

from invoiceflow.ports.erp import ErpConflictError, ErpResult, ErpUnavailableError
from invoiceflow.services.erp_sandbox.store import ErpStore


class InProcessERP:
    def __init__(self, store: ErpStore) -> None:
        self.store = store

    def post_decision(
        self, idempotency_key: str, invoice_id: str, action: str, payload: dict[str, Any]
    ) -> ErpResult:
        return self.store.record(idempotency_key, "decision", invoice_id, action, payload)

    def create_hold(self, idempotency_key: str, invoice_id: str, reason: str) -> ErpResult:
        return self.store.record(
            idempotency_key, "hold", invoice_id, "HOLD_FOR_GRN", {"reason": reason}
        )


class HttpERP:
    def __init__(
        self, client: httpx.Client, retries: int = 3, backoff_seconds: float = 0.2
    ) -> None:
        self._client = client
        self._retries = retries
        self._backoff = backoff_seconds

    def _post(self, path: str, key: str, body: dict[str, Any]) -> ErpResult:
        last: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                response = self._client.post(path, json=body, headers={"Idempotency-Key": key})
            except httpx.TransportError as exc:
                last = exc
            else:
                if response.status_code == 409:
                    raise ErpConflictError(response.text)
                if response.status_code < 500:
                    response.raise_for_status()
                    return ErpResult.model_validate(response.json())
                last = httpx.HTTPStatusError(
                    f"ERP returned {response.status_code}",
                    request=response.request,
                    response=response,
                )
            if attempt < self._retries:
                time.sleep(self._backoff * (2**attempt))
        raise ErpUnavailableError(f"ERP unavailable after {self._retries + 1} attempts: {last}")

    def post_decision(
        self, idempotency_key: str, invoice_id: str, action: str, payload: dict[str, Any]
    ) -> ErpResult:
        return self._post(
            "/decisions",
            idempotency_key,
            {"invoice_id": invoice_id, "action": action, "payload": payload},
        )

    def create_hold(self, idempotency_key: str, invoice_id: str, reason: str) -> ErpResult:
        return self._post("/holds", idempotency_key, {"invoice_id": invoice_id, "reason": reason})
