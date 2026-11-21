"""Call an eve agent over its HTTP API (/eve/v1) and return a schema-validated structured result.

Wire contract (eve docs, "Base eve Channel" and "Sessions, Runs, and Streaming"):
  POST {base}/eve/v1/session  {"message", "outputSchema", "clientContext"} -> 202 {"sessionId"}
  GET  {base}/eve/v1/session/{id}/stream  NDJSON: {"at","facts":[...]} | {"progress":...} | {"$eve":...}
  the structured result is a `content.completed` fact with data.kind == "result";
  spend arrives as `usage.recorded`; the turn ends with `turn.settled`.
  POST {base}/eve/v1/session/{id}/end  retires the session.

Failures raise LiveAgentError. Callers must NOT fall back to demo output; the stage fails visibly.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from spreadlens.config import Settings
from spreadlens.observability import correlation_id

T = TypeVar("T", bound=BaseModel)


class LiveAgentError(RuntimeError):
    pass


@dataclass
class LiveCallResult:
    data: Any
    session_id: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float | None = None
    model: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    duration_ms: int = 0
    attempts: int = 1


def _usage_numbers(data: dict) -> tuple[int, int, float | None]:
    tin = tout = 0
    cost = None
    flat = dict(data)
    for k in ("usage", "tokens"):
        if isinstance(data.get(k), dict):
            flat.update(data[k])
    for k, v in flat.items():
        lk = k.lower()
        if isinstance(v, (int, float)):
            if "input" in lk and "token" in lk:
                tin += int(v)
            elif "output" in lk and "token" in lk:
                tout += int(v)
            elif lk in ("costusd", "cost_usd"):
                cost = (cost or 0.0) + float(v)
    return tin, tout, cost


class EveClient:
    def __init__(self, base_url: str, settings: Settings) -> None:
        self.base = base_url.rstrip("/")
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        h = {"content-type": "application/json"}
        if self.settings.eve_service_token:
            h["authorization"] = f"Bearer {self.settings.eve_service_token}"
        cid = correlation_id.get()
        if cid:
            h["x-correlation-id"] = cid
        return h

    def run(self, message: str, schema: type[T], client_context: dict | None = None) -> tuple[T, LiveCallResult]:
        last: Exception | None = None
        for attempt in range(1, self.settings.live_model_max_retries + 2):
            try:
                res = self._run_once(message, schema.model_json_schema(), client_context)
                res.attempts = attempt
                try:
                    return schema.model_validate(res.data), res
                except ValidationError as exc:
                    last = LiveAgentError(f"agent output failed schema validation: {exc.error_count()} errors")
            except (httpx.HTTPError, LiveAgentError) as exc:
                last = exc
            time.sleep(min(2 ** attempt, 8))
        raise LiveAgentError(f"live agent call failed after retries: {last}")

    def _run_once(self, message: str, output_schema: dict, client_context: dict | None) -> LiveCallResult:
        started = time.monotonic()
        body: dict[str, Any] = {"message": message, "outputSchema": output_schema}
        if client_context:
            body["clientContext"] = client_context
        timeout = httpx.Timeout(self.settings.live_request_timeout_s, connect=10.0)
        with httpx.Client(timeout=timeout, follow_redirects=False) as http:
            r = http.post(f"{self.base}/eve/v1/session", json=body, headers=self._headers())
            if r.status_code not in (200, 201, 202):
                raise LiveAgentError(f"session create returned HTTP {r.status_code}")
            session_id = r.json().get("sessionId") or r.headers.get("x-eve-session-id")
            if not session_id:
                raise LiveAgentError("no sessionId in response")
            result = LiveCallResult(data=None, session_id=session_id)
            outcome = None
            with http.stream("GET", f"{self.base}/eve/v1/session/{session_id}/stream", headers=self._headers()) as s:
                for line in s.iter_lines():
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    if rec.get("$eve") == "stream.ended":
                        break
                    for fact in rec.get("facts", []):
                        t, d = fact.get("type"), fact.get("data", {}) or {}
                        if t == "content.completed" and d.get("kind") == "result":
                            result.data = d.get("value")
                        elif t == "usage.recorded":
                            tin, tout, cost = _usage_numbers(d)
                            result.tokens_in += tin
                            result.tokens_out += tout
                            if cost is not None:
                                result.cost_usd = (result.cost_usd or 0.0) + cost
                        elif t == "model.started":
                            result.model = d.get("modelId") or result.model
                        elif t == "call.requested":
                            cap = d.get("capability") or {}
                            result.tool_calls.append(str(cap.get("name") or d.get("name") or "tool"))
                        elif t == "turn.settled":
                            outcome = d.get("outcome")
                    if outcome:
                        break
            try:
                http.post(f"{self.base}/eve/v1/session/{session_id}/end", json={"reason": "stage complete"}, headers=self._headers())
            except httpx.HTTPError:
                pass
        result.duration_ms = int((time.monotonic() - started) * 1000)
        if outcome != "completed":
            raise LiveAgentError(f"agent turn ended with outcome {outcome!r}")
        if result.data is None:
            raise LiveAgentError("agent produced no structured result")
        if result.cost_usd is None:
            result.cost_usd = (result.tokens_in * self.settings.model_price_input_per_mtok
                               + result.tokens_out * self.settings.model_price_output_per_mtok) / 1_000_000
        return result
