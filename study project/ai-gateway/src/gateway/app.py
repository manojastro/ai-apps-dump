"""FastAPI gateway: auth -> rate limit -> budget -> guardrails -> route/cache ->
mock provider -> output guardrails -> metering. Offline, synthetic only."""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from collections.abc import Iterator
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from . import auth as auth_mod
from . import db as db_mod
from . import guardrails as guards
from . import metering as metering_mod
from . import models as models_mod
from . import provider_mock as provider_mod
from . import routing as routing_mod
from .rate_limit import InMemoryRedisStub, RedisTokenBucketStore
from .settings import Settings, get_settings


def _conn(settings: Settings) -> sqlite3.Connection:
    conn = db_mod.get_conn(settings.database_path)
    db_mod.init_db(conn)
    return conn


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="P5 Secure AI Gateway (mock-first)")

    _settings = settings or get_settings()
    conn = _conn(_settings)
    app.state.settings = _settings
    app.state.conn = conn
    app.state.policy = routing_mod.load_routing_policy(_settings.routing_policy_path)
    app.state.profiles = guards.load_profiles(_settings.guardrail_profiles_path)
    app.state.prices = metering_mod.load_prices(_settings.prices_path)
    app.state.cache = routing_mod.ExactCache(ttl_s=_settings.cache_ttl_s)
    app.state.redis = RedisTokenBucketStore(InMemoryRedisStub())

    def get_conn() -> sqlite3.Connection:
        return app.state.conn  # type: ignore[no-any-return]

    def tenant_from_key(raw: str | None) -> sqlite3.Row:
        if not raw:
            raise HTTPException(status_code=401, detail="missing tenant key")
        key = raw.removeprefix("Bearer ").strip() if raw.startswith("Bearer") else raw
        digest = hashlib.sha256(key.encode()).hexdigest()
        # Constant-time scan over active tenants (demo-scale; indexed lookup
        # in production with HMAC keys).
        rows = get_conn().execute(
            "SELECT * FROM tenants WHERE deleted = 0"
        ).fetchall()
        for row in rows:
            if hmac.compare_digest(str(row["key_hash"]), digest):
                return row  # type: ignore[no-any-return]
        raise HTTPException(status_code=401, detail="invalid tenant key")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "mock-first-offline"}

    @app.post("/admin/tenants")
    def admin_create_tenant(
        body: models_mod.TenantCreateRequest,
        x_admin_key: str = Header(default="", alias="X-Admin-Key"),
    ) -> dict[str, Any]:
        if not hmac.compare_digest(x_admin_key, _settings.admin_api_key):
            raise HTTPException(status_code=403, detail="bad admin key")
        raw_key = auth_mod.generate_api_key()
        digest = auth_mod.hash_key(raw_key)
        try:
            tid = db_mod.create_tenant(
                get_conn(),
                name=body.name,
                key_hash=digest,
                monthly_budget_usd=body.monthly_budget_usd,
                rpm=body.rpm,
                tpm=body.tpm,
                allowed_models=body.allowed_models,
                guardrail_profile=body.guardrail_profile,
            )
        except sqlite3.IntegrityError as err:
            raise HTTPException(status_code=409, detail="tenant exists") from err
        db_mod.record_audit(
            get_conn(), tenant=body.name, event="tenant_created", request_id=str(tid)
        )
        # Raw key is returned ONCE and never stored.
        return {"id": tid, "name": body.name, "api_key": raw_key}

    @app.get("/v1/usage")
    def tenant_usage(authorization: str = Header(default="")) -> dict[str, Any]:
        row = tenant_from_key(authorization)
        spent = metering_mod.month_spend(get_conn(), str(row["name"]))
        return {
            "tenant": row["name"],
            "month_spend_usd": round(spent, 6),
            "monthly_budget_usd": row["monthly_budget_usd"],
            "remaining_usd": round(float(row["monthly_budget_usd"]) - spent, 6),
        }

    @app.get("/admin/usage")
    def admin_usage(x_admin_key: str = Header(default="", alias="X-Admin-Key")) -> Any:
        if not hmac.compare_digest(x_admin_key, _settings.admin_api_key):
            raise HTTPException(status_code=403, detail="bad admin key")
        rows = get_conn().execute(
            """SELECT tenant, substr(datetime(ts, 'unixepoch'), 1, 10) AS day,
                      model, COUNT(*) AS n,
                      SUM(tokens_in) AS ti, SUM(tokens_out) AS tout,
                      SUM(cost_usd) AS cost
               FROM usage_ledger GROUP BY tenant, day, model ORDER BY day"""
        ).fetchall()
        return [dict(r) for r in rows]

    @app.post("/v1/chat/completions")
    def chat_completions(
        body: models_mod.ChatCompletionRequest,
        request: Request,
        response: Response,
        authorization: str = Header(default=""),
        x_task: str | None = Header(default=None, alias="X-Task"),
    ) -> Any:
        request_id = str(uuid.uuid4())
        row = tenant_from_key(authorization)
        tenant = str(row["name"])
        allowed = json.loads(str(row["allowed_models"] or "[]"))
        profile = dict(app.state.profiles.get(str(row["guardrail_profile"]),
                                              app.state.profiles["standard"]))

        def _blocked(reason: str, status: int = 400) -> JSONResponse:
            db_mod.record_usage(
                get_conn(), tenant=tenant, request_id=request_id,
                model=body.model, tokens_in=0, tokens_out=0, cost_usd=0.0,
                blocked=True, reason=reason,
            )
            db_mod.record_audit(get_conn(), tenant=tenant, event="blocked",
                                reason=reason, request_id=request_id)
            return JSONResponse(status_code=status,
                                content={"error": reason, "request_id": request_id})

        # --- Rate limit: 1 token per request (rpm) -------------------------
        rpm = int(row["rpm"])
        ok, retry = app.state.redis.allow(
            f"rl:{tenant}:rpm", capacity=float(rpm),
            refill_rate=float(rpm) / 60.0, cost=1.0,
        )
        if not ok:
            db_mod.record_audit(get_conn(), tenant=tenant, event="rate_limited",
                                reason="rpm", request_id=request_id)
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(max(1, int(retry + 0.999)))},
                content={"error": "rate_limited", "request_id": request_id},
            )

        # --- Budget: hard stop at 100% --------------------------------------
        spent = metering_mod.month_spend(get_conn(), tenant)
        state, reason = metering_mod.check_budget(
            spent, float(row["monthly_budget_usd"]))
        if state == "hard":
            return _blocked("budget_exceeded", status=402)

        # --- Input guardrails -------------------------------------------------
        raw_text = "\n".join(m.content for m in body.messages)
        inp = guards.check_input(raw_text, profile)
        if not inp.allowed:
            return _blocked(inp.reason)
        redacted_messages = [
            {"role": m.role, "content": guards.redact_pii(m.content)[0]}
            for m in body.messages
        ]

        # --- Model allow-list --------------------------------------------------
        primary, fallback = routing_mod.route(x_task, app.state.policy)
        wanted = body.model or primary
        # Task default wins unless caller explicitly picks an allowed model.
        effective = primary if body.model in ("", "general-default") else wanted
        if allowed and effective not in allowed and wanted not in allowed:
            return _blocked(f"model_not_allowed:{effective}", status=403)

        # --- Exact-match cache (per tenant, temp 0 only) -----------------------
        use_cache = body.temperature == 0
        ckey = routing_mod.cache_key(tenant, effective, redacted_messages,
                                     body.temperature)
        if use_cache:
            hit = app.state.cache.get(ckey)
            if hit is not None:
                assert isinstance(hit, dict)
                cost = metering_mod.estimate_cost(
                    effective, hit["tokens_in"], hit["tokens_out"],
                    app.state.prices)
                db_mod.record_usage(
                    get_conn(), tenant=tenant, request_id=request_id,
                    model=effective, tokens_in=hit["tokens_in"],
                    tokens_out=hit["tokens_out"], cost_usd=cost, cache_hit=True,
                )
                payload = _openai_payload(request_id, effective,
                                          hit["text"], hit["tokens_in"],
                                          hit["tokens_out"])
                payload["cache_hit"] = True
                if state == "soft":
                    payload["budget_warning"] = "soft_80pct"
                return payload

        # --- Provider (mock) with fallback -------------------------------------
        model_used = effective
        try:
            text, tin, tout = provider_mod.mock_chat(effective, redacted_messages)
        except provider_mod.MockProviderError:
            db_mod.record_audit(get_conn(), tenant=tenant,
                                event="provider_fallback",
                                reason=f"{effective}->{fallback}",
                                request_id=request_id)
            try:
                text, tin, tout = provider_mod.mock_chat(fallback,
                                                         redacted_messages)
                model_used = fallback
            except provider_mod.MockProviderError as e:
                return _blocked(f"provider_unavailable:{e}", status=502)

        # --- Output guardrails ---------------------------------------------------
        expect_json = bool((body.response_format or {}).get("json_schema")
                           or (body.response_format or {}).get("type") == "json_object")
        out = guards.check_output(text, profile, expect_json=expect_json)
        if not out.allowed:
            db_mod.record_usage(
                get_conn(), tenant=tenant, request_id=request_id,
                model=model_used, tokens_in=tin, tokens_out=tout, cost_usd=0.0,
                blocked=True, reason=out.reason,
            )
            db_mod.record_audit(get_conn(), tenant=tenant, event="blocked",
                                reason=out.reason, request_id=request_id)
            return JSONResponse(status_code=400,
                                content={"error": out.reason,
                                         "request_id": request_id})

        # --- Meter + respond (streaming stub = SSE chunks, same mock text) -------
        cost = metering_mod.estimate_cost(model_used, tin, tout, app.state.prices)
        db_mod.record_usage(
            get_conn(), tenant=tenant, request_id=request_id, model=model_used,
            tokens_in=tin, tokens_out=tout, cost_usd=cost,
        )
        if use_cache:
            app.state.cache.set(ckey, {"text": text, "tokens_in": tin,
                                       "tokens_out": tout})
        if body.stream:
            return StreamingResponse(
                _sse_chunks(request_id, model_used, text), media_type="text/event-stream"
            )
        payload = _openai_payload(request_id, model_used, text, tin, tout)
        payload["cache_hit"] = False
        if state == "soft":
            payload["budget_warning"] = "soft_80pct"
        if model_used != effective:
            payload["fallback_used"] = True
        return payload

    return app


def _openai_payload(rid: str, model: str, text: str, tin: int,
                    tout: int) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-{rid[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant",
                                             "content": text},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": tin, "completion_tokens": tout,
                  "total_tokens": tin + tout},
    }


def _sse_chunks(rid: str, model: str, text: str) -> Iterator[str]:
    words = text.split()
    half = max(1, len(words) // 2)
    for part in (" ".join(words[:half]), " ".join(words[half:])):
        chunk = {
            "id": f"chatcmpl-{rid[:8]}",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{"index": 0, "delta": {"content": part}}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


app = create_app()
