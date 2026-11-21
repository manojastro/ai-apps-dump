# 08 — APIs for AI Engineers

**What this chapter is for:** so you can stand up a chat/RAG endpoint, call a model provider without hanging the process, and explain what happens on 429, a dropped SSE stream, or a retried POST that books a ticket.

**Roles that score this as core:** GenAI / Agentic (skill-matrix 5), FDE (5), Cloud AI (4), Solutions Engineer / Architect (4). **All eight roles get asked.** AIOps and AI Security get the auth, 429, and webhook slices even when they never write FastAPI.

Python is in **82.5%** of ~889 January 2026 AI Engineer JDs; FastAPI is in **10.7%** and a much higher share of take-homes. LLM integration is in **25.4%**. The coding round is almost never “implement HTTP/2.” It is timeouts, retries, auth, streaming, and an error envelope.

Chapter 06 is the Python you type. This chapter is the **HTTP contract** they score: status, headers, identity, idempotency, backoff, gateways, provider outage.

---

## Interviewer intent

| Signal | Pass | Fail |
| --- | --- | --- |
| Timeouts on every hop | Connect + read + total budget | Bare `requests.get` |
| Retry taxonomy | 429/503/timeout + jitter; never 400 | Retry everything, including POST charge |
| Authn vs authz | Principal on the request; tools run as the user | API key in the repo; model is the ACL |
| Streaming | SSE, TTFT, cancel upstream | “WebSocket because chat” as a reflex |
| Failure visible | Envelope + `request_id` + 429/504 | 200 with `{error}` swallowed; stack traces |
| Provider outage | Circuit, fallback, degrade | Tight retry loop that amplifies a 429 |

**Highest-signal question:** *The provider returns 429 mid-stream. What does the client see, and do you retry?*

---

## Probability ranking (applied AI loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | Timeouts + retries + jitter on LLM HTTP | Almost certain | Code + taxonomy |
| 2 | 429 / provider outage / fallback | Very high | Budget, circuit, user message |
| 3 | SSE / streaming chat | Very high in GenAI/FDE | Cancel, TTFT, partial failure |
| 4 | Auth (API key vs OIDC/JWT vs mTLS) | Very high in enterprise | User vs service vs tool OBO |
| 5 | Idempotency on writes / tools | Very high if agents | Key + store + 409 |
| 6 | Error envelopes + status codes | High | 401/403/422/429/504 |
| 7 | FastAPI RAG/chat shape | High (take-home) | Validation, DI, stream |
| 8 | Rate limits (in and out) | High | Token bucket, tenant quotas |
| 9 | LLM client (pooling, 200-with-error) | High | Adapter, usage headers |
| 10 | Tool-calling HTTP contracts | High for agentic | Schema, authz, timeouts |
| 11 | Pagination / cursors | Medium–high | Keyset, not OFFSET |
| 12 | Webhooks | Medium | Signature, retries, replay |
| 13 | Gateways + versioning | Medium–high senior | One policy plane |
| 14 | Circuit breakers | Medium–high senior | Fail fast vs retry storm |

---

## How to study this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Then the senior cut. Write a 6-part card: concept, logic, structure, keywords, example, trade-off.

For coding follow-ups, narrate: signature → timeouts → happy path → 429 → non-retryable → test. Do not implement a framework. Implement the contract.

---

## The one diagram you should be able to draw

```
Caller
  │  Authorization  Idempotency-Key  X-Request-Id  Accept
  ▼
Gateway ── TLS, authn, WAF, rate limit, routing, correlation id
  ▼
FastAPI ── Pydantic, tenant, deadline
  ├─ POST /v1/query          JSON envelope
  ├─ POST /v1/chat           SSE  text/event-stream
  └─ POST /v1/tools/:name    idempotent write
  ▼
LLM client ── connect/read timeouts, pool, 429/5xx retry+jitter,
              circuit breaker, fallback model, usage + request_id
```

Every arrow has a timeout. Every write has an idempotency story. Every error has a code the caller can branch on.

---

## Q1. REST, status codes, and error envelopes for an AI API

**Why they ask.** They want a service, not a notebook. Status codes and a stable error body are how clients, gateways, and on-call actually work.

**What they expect.** Resource-oriented routes, the status set you will actually emit, one error envelope, no 200-with-hidden-error on *your* API (even if providers do it).

**Answer structure keywords.** resources · 2xx/4xx/5xx · 422 vs 400 · 429 Retry-After · 504 · envelope · request_id · no stack traces.

**30-second.** REST here means resources and verbs: `POST /v1/query`, `GET /v1/traces/{id}`, `POST /v1/chat`. Success is 200/201/202. Validation is 422. Authn 401, authz 403, missing 404, conflict/idempotency mismatch 409, rate limit 429, our timeout 504, we are down 503. Errors are a JSON envelope with `code`, `message`, `request_id`, optional `retry_after_ms`. Never leak stacks or prompts.

**2-minute.**

```json
{
  "error": {
    "code": "rate_limited",
    "message": "Tenant token budget exhausted",
    "retry_after_ms": 1200,
    "request_id": "req_7f3"
  }
}
```

Map: empty retrieval → 200 with `citations: []` and `refused: true` (it is a valid business result), not 404. Provider outage → 503 with Retry-After if we did not fallback. Pydantic failures stay 422. I do not invent 200 for failed tools. Version in the path (`/v1`) so `/v2` can break (Q12). GET is safe/idempotent; POST is not unless we make it so (Q4). List endpoints (`GET /v1/traces`) paginate with an opaque `next_cursor` over a keyset, not `?page=` / OFFSET — SQL in Chapter 07, contract here.

**Senior / deep.** Distinguish **transport** failures from **application** failures. Some model providers return HTTP 200 with `{"error": ...}` — the adapter must raise. Your public API should not copy that habit. Problem+JSON (`application/problem+json`) is fine; consistency beats fashion. Idempotent create returns 200 with the stored result on replay, 201 on first apply. Streaming errors cannot change the status code after TTFT — send an `event: error` and close (Q8).

**Weak answer.** “REST is CRUD. I’d return 500 if anything goes wrong.”

**Mistakes.**

- 200 + `{error}` on your API.
- 401 vs 403 confused (identity vs permission).
- 404 for “the model doesn’t know.”

**Follow-ups + strong replies.**

- *204 vs 200?* 204 for successful empty writes. Chat always has a body.
- *Why not 418?* Don’t be cute in a production envelope.

**Example.** Typical `POST /v1/query`: 200 with answer+citations, 401 missing JWT, 403 tenant mismatch, 422 empty question, 429 tenant TPM, 504 retrieve+generate exceeded 30s.

---

## Q2. Headers that actually matter

**Why they ask.** Headers are the control plane: identity, idempotency, tracing, content negotiation, cache. Candidates who only know `Content-Type` miss the round.

**What they expect.** `Authorization`, `Idempotency-Key`, `Retry-After`, correlation ids, `Accept` for SSE, what you must **not** log.

**Answer structure keywords.** Authorization · Idempotency-Key · Retry-After · X-Request-Id · Accept · Cache-Control · redaction.

**30-second.** Inbound: `Authorization` (Bearer JWT or API key), `Idempotency-Key` on writes, `Accept: text/event-stream` for chat, `X-Request-Id` if the caller has one. Outbound: `Retry-After` on 429/503, `X-Request-Id` we generated, `Cache-Control: no-store` on personalized answers. Never log Authorization, cookies, or API keys.

**2-minute.** Correlation: if the caller sends a request id, honor it if it matches a strict charset; otherwise mint one and return it. Pass it to the provider and into traces. `Content-Type: application/json` on JSON bodies; SSE is `text/event-stream` with `Cache-Control: no-cache` and no gzip midway if it breaks flush. `WWW-Authenticate` on 401. For LLM providers I also send (or read) usage and processing-ms headers when they exist — they feed cost metrics.

**Senior / deep.** Hop-by-hop vs end-to-end: do not forward `Connection` / `Transfer-Encoding`. Strip inbound `X-Forwarded-*` you do not trust; set them at the gateway. `Idempotency-Key` is stored hashed with a hash of the body (Q4). CORS is a browser policy, not auth — never use `Access-Control-Allow-Origin: *` with credentials on an enterprise copilot.

**Weak answer.** “Headers are Content-Type and Authorization.”

**Mistakes.**

- Logging the full Authorization header.
- Forgetting Retry-After on 429.
- Buffering SSE because of `Content-Encoding`.

**Follow-ups + strong replies.**

- *Custom `X-Tenant-Id`?* Display only. Tenant comes from the token, not a spoofable header.
- *ETag on GET /traces/{id}?* Fine. Not on chat POST.

**Example.** Typical gateway injects `X-Request-Id`, verifies JWT, rate-limits, and forwards `Authorization` only to internal services that need OBO — never to logs.

---

## Q3. Auth — API key, OAuth2, OIDC, JWT, mTLS

**Why they ask.** Enterprise loops fail candidates who paste OpenAI keys into frontends and call it auth. They want user vs service vs tool identity.

**What they expect.** A decision table. Authn vs authz. JWT as a format, OIDC as identity, OAuth2 as delegation. mTLS for service-to-service. Tools run as the user.

**Answer structure keywords.** authn vs authz · API key M2M · OIDC user login · JWT bearer · OBO/token exchange · mTLS · least privilege · rotation.

**30-second.** **API keys** are shared secrets for M2M (your backend → provider, or a partner integration). **OIDC** is how users sign in (identity token). **OAuth2** is delegation (access token to call APIs). **JWT** is a token format, not a protocol. **mTLS** binds a client cert to a workload. Users hit us with OIDC/JWT. We hit OpenAI/Bedrock with a vaulted key or cloud IAM. Tools use on-behalf-of so they are not a superuser.

**2-minute.**

| Path | Mechanism | Trap |
| --- | --- | --- |
| Browser → your API | OIDC login, short-lived JWT, refresh in httpOnly cookie or BFF | Putting the LLM provider key in the SPA |
| Partner M2M → your API | API key or OAuth2 client credentials + mTLS | Long-lived key in a ticket |
| Your API → model provider | Vault / IAM role, not env on a laptop | One key for all tenants |
| Agent tool → SaaS | OBO / token exchange as the user | God-mode service account |

Validate JWT: issuer, audience, signature, `exp`, `nbf`. Authz is a separate step: tenant, role, resource. A valid token for tenant A must 403 on tenant B’s docs. Rotate keys; scope them (retrieve vs write).

**Senior / deep.** Confused deputy is the agentic failure: the tool runtime has `chunks:read` on every tenant. Injection then becomes a breach. Fix: pass the user assertion, or mint a downscoped token per tool call (Chapter 11). For Azure estates say Entra, OBO, Easy Auth at the gateway. For AWS: IAM on Bedrock, Cognito/OIDC at the edge. mTLS inside the mesh does not replace user authz. Don’t roll a custom JWT just to look clever.

**Weak answer.** “We put the OpenAI key in `.env` and a login page.”

**Mistakes.**

- API key in the frontend.
- Treating JWT `sub` as a tenant ACL without checks.
- Infinite-lived keys in Git.

**Follow-ups + strong replies.**

- *API key vs JWT for a public SDK?* User-context: JWT. Server-side SDK: key bound to a tenant, rate-limited, rotatable.
- *Where do you store the provider key?* Secret manager. Inject at runtime. Never into prompts or traces.

**Example.** Typical B2B copilot: Entra OIDC to the app, JWT validated at the gateway, tenant from `tid`. Bedrock called with the task role. Jira tool uses OBO. The model never sees a bearer token.

---

## Q4. Idempotency — POSTs, tools, provider calls

**Why they ask.** Agents and retries are at-least-once. Without keys you double-refund, double-email, double-ingest.

**What they expect.** Client key, server store, hash of body, replay vs 409, TTL, what is *not* idempotent (streaming complete).

**Answer structure keywords.** Idempotency-Key · store first · hash body · replay 200 · mismatch 409 · TTL · exactly-once effect.

**30-second.** The client sends `Idempotency-Key` (UUID) on any POST with side effects. The server records the key, a hash of the canonical body, and later the response. Same key + same body: return the stored result. Same key + different body: 409. Different key: new work. Retrieval GET does not need this. LLM **generation** is not naturally idempotent; tool **writes** must be.

**2-minute.** Store the key *before* calling the downstream API (outbox). If we crash after the provider charged but before we saved, replay with the same key and **look up** first. Keys expire (24–72h) so the table does not grow forever; after expiry a replay may redo — document that. Natural keys beat random ones when they exist (`refund:{order_id}:{amount}`). FastAPI middleware can wrap this; the tool executor must still pass the key into the ledger unique constraint (Chapter 07).

**Senior / deep.** Exactly-once *delivery* is a lie. Exactly-once *effect* is a unique constraint plus a stored result. For streaming, you cannot replay tokens to a new HTTP connection as the same response — persist the final transcript under the key and on retry return JSON instead of SSE, or 409 “already completed.” Provider-side `Idempotency-Key` (when they support it) is extra, not a substitute for your store. Agents: the runtime generates the key from `(run_id, step, tool, canonical_args)` so ReAct retries do not double-apply (Chapter 11).

**Weak answer.** “POST isn’t idempotent so we just hope the user doesn’t click twice.”

**Mistakes.**

- Key only in memory on one replica.
- Not hashing the body (key reuse with different amount).
- Retrying streaming complete() as if it were a PUT.

**Follow-ups + strong replies.**

- *Who mints the key?* Caller for user-driven POSTs. Runtime for tool steps.
- *GET with side effects?* Don’t. Use POST.

**Example.** Typical `create_refund` tool: key `refund:{order_id}:{cents}`. First call inserts intent, calls ledger, stores result. Agent retries after 504 → same row, no second charge.

---

## Q5. Retries, backoff, jitter

**Why they ask.** This is the job. Missing jitter synchronized-retries a 429 into an outage. Retrying 400 burns money.

**What they expect.** Retryable vs not, exponential backoff, jitter, Retry-After, attempt cap **and** deadline, idempotent-only writes. (Implementation: Chapter 06 Exercise 2.)

**Answer structure keywords.** 429/503/408 · no 400/401/403 · exp backoff · full jitter · Retry-After · deadline · idempotent POST only.

**30-second.** Retry timeouts, 429, 503, 202-not-ready. Do not retry 400, 401, 403, 404, 422 unless you refreshed auth. Sleep `min(cap, base * 2**k) * U(0.5, 1.0)`. Honor `Retry-After` when present. Cap by attempts **and** a total deadline (a 30s user request cannot sleep 8+8+8). Writes only with the same idempotency key.

**2-minute.** Taxonomy lives on *your* exception type (`is_retryable`, `retry_after`), not on string matching. 409 is not retryable. 425/408 maybe. Some providers 200-with-error — treat as the inner status. In the request path, fail fast to 503 after a small budget; in a worker, you can wait longer. Log first and last attempt at error, middle at debug (Chapter 06). `Retry-After: 1.5` seconds vs HTTP-date — parse both.

**Senior / deep.** Jitter exists so clients do not retry in lockstep after a shared outage (thundering herd). Full jitter vs equal jitter vs decorrelated jitter — name AWS’s blog if they push; full jitter is the interview default. Retries **amplify** load: pair with a circuit breaker (Q7) and a concurrency semaphore. Streaming: if the connection dies after tokens started, **do not** retry complete() unless the API has a resume token — you will duplicate or fork the answer. Embeddings and GETs are safer to retry.

**Weak answer.** `for i in range(10): try: call() except: pass`.

**Mistakes.**

- Retry 400. No jitter. No deadline.
- Retrying non-idempotent POST.
- Sleeping in a FastAPI handler for 30s per attempt.

**Follow-ups + strong replies.**

- *Would you retry mid-SSE?* No, unless resume is supported. Surface partial + error event.
- *Sync SDK in async route?* `to_thread` plus the same policy; do not block the loop (Chapter 06).

**Example.** Typical LLM client: 3 attempts, 0.25s base, 4s cap, full jitter, honor Retry-After, 20s deadline. 400 raises immediately. On-call graph shows attempt=3 only on 503 storms.

---

## Q6. Rate limits — inbound, outbound, tenants

**Why they ask.** Providers have RPM/TPM. One noisy tenant or a retry bug 429s everyone. They want a limiter *and* a story when the provider is the source of truth.

**What they expect.** Token bucket vs sliding window, per-tenant + global, TPM vs RPM, 429 with Retry-After, process-local vs Redis.

**Answer structure keywords.** RPM vs TPM · token bucket · sliding window · per-tenant · 429 · Redis for multi-worker · provider is source of truth.

**30-second.** Limit **inbound** (abuse, fairness) and **outbound** (provider quotas). Providers count requests and tokens. A token bucket allows bursts (chat spikes); a sliding window matches “N per 60s.” One bucket per tenant plus a global bucket. Six Uvicorn workers = 6× a process-local limiter — use Redis for a fleet cap. Still handle 429s; our limiter is best-effort.

**2-minute.** On 429 we return the same to the caller with Retry-After, or queue. Fairness: a noisy eval job gets its own key and cannot starve interactive chat. Estimate TPM from prompt size *before* the call; reject or compact rather than 429 at the provider. Batch embeddings (64 texts / call) instead of 64 limited calls. Chapter 06 Exercise 3 is the in-process bucket; say its limit.

**Senior / deep.** Shadow-limit before enforce so you learn p99. Separate limits: auth’d interactive, batch ingest, eval CI. Cost kill-switch is not the same as RPM — a 1M-token call is one request. For multi-tenant SaaS, noisy-neighbor is an SLO: isolate with queues. Gateway (APISIX, Kong, APIM, AWS API Gateway) can enforce coarse RPM; application still enforces TPM because only we know token estimates.

**Weak answer.** “The provider rate-limits us so we don’t need to.”

**Mistakes.**

- One global bucket for all tenants.
- Limiting only requests, not tokens.
- Retry without jitter that re-trips the same window.

**Follow-ups + strong replies.**

- *Sliding vs fixed window?* Fixed bursts at boundaries (59s and 01s). Sliding is smoother. Bucket is best for configured bursts.
- *Who pays 429?* Interactive users see 429. Batch workers backoff. Never hide it as 500.

**Example.** Typical copilot: Redis sliding window 60 RPM/tenant interactive, separate 10 RPM batch, outbound TPM bucket per model. Eval job uses the batch key.

---

## Q7. Timeouts and circuit breakers

**Why they ask.** Hung sockets are the silent outage. Retries without a breaker turn a provider blip into a self-DoS.

**What they expect.** Connect vs read vs total deadline, TTFT vs full-generation timeout, breaker states, what the user sees when open.

**Answer structure keywords.** connect/read/write/pool · deadline · TTFT · circuit closed/open/half-open · fail fast · fallback.

**30-second.** Every HTTP call has connect and read timeouts; the request has a **deadline** smaller than the user’s patience. Chat: short connect (5s), long read while streaming (60s), but cancel if TTFT > 8s. A circuit breaker counts failures; after a threshold it **opens** and fails fast for a cooldown, then half-open with a probe. Open ≠ retry storm.

**2-minute.** `httpx.Timeout(connect=5, read=60, write=10, pool=5)` plus `asyncio.wait_for` on the whole handler. Nested timeouts: retrieve 3s, generate 20s, tools 5s each, total 30s. Breaker key is `(provider, model, region)` not “the internet.” On open: fallback model, or retrieval-only degrade, or 503. Half-open allows one probe; success closes, failure reopens. Do not hold a breaker open on 400s — those are our bugs.

**Senior / deep.** Timeouts must **cancel work** (close the socket, abort the provider read) or you keep paying. Circuit + bulkhead (max in-flight) + retry budget is the resilience trio. For streaming, a read timeout between tokens is different from TTFT — implement idle-timeout. Multi-provider: independent breakers so OpenAI open does not block Bedrock. Expose breaker state as a metric; page on `open` for the primary provider.

**Weak answer.** “We set timeout=None so big jobs can finish.”

**Mistakes.**

- One 600s timeout on everything.
- Breaker on 401 (will never recover without a human).
- Retries while the breaker is open.

**Follow-ups + strong replies.**

- *Default read 60s and the user hung up?* Cancel upstream. Connection-disconnect is a first-class signal.
- *Library?* Tenacity for retry; a small breaker (or resilience4j-style) at the adapter. Don’t import a mesh to hide missing timeouts.

**Example.** Typical adapter: OpenAI breaker opens after 5 consecutive timeouts, 30s cooldown, fallback to a smaller model on another vendor. Users see “degraded quality, still answering.” Traces show `circuit=open`.

---

## Q8. SSE / streaming chat

**Why they ask.** Streaming is in the skill matrix at 4 for GenAI/Agentic. TTFT is the product. They want SSE as the default, plus cancel and error-after-200.

**What they expect.** `text/event-stream`, event types, why not WebSocket first, proxy buffering, cancellation of the provider call, what happens mid-stream on 429.

**Answer structure keywords.** SSE · TTFT · event: token/done/error · cancel upstream · no retry mid-stream · proxy buffering · WS when bidirectional.

**30-second.** Chat tokens are **SSE**: one HTTP response, `text/event-stream`, events as `data:` lines. First byte is TTFT. If the client disconnects, cancel the upstream model call. Do not retry a half-finished stream. WebSockets are for true bidirectional (voice, collaborative cursors), not for “tokens arriving.”

**2-minute.**

```
event: token
data: {"t":"Hello"}

event: done
data: {"finish_reason":"stop","usage":{"out":12}}
```

FastAPI: `StreamingResponse` with `media_type="text/event-stream"`, headers `Cache-Control: no-cache`, `X-Accel-Buffering: no`. Heartbeat comments (`: ping`) beat idle proxies. Auth **before** you start the stream; you cannot 401 after tokens. Errors after start: `event: error` then close — status is already 200.

**Senior / deep.** Backpressure: if the client is slow, stop reading the provider (or you buffer RAM and still pay decode). Persist the final transcript for audit even if the client vanished. Tool-calls mid-stream: either buffer until the tool JSON is complete or emit `event: tool_call` with a validated payload — never execute on a partial name. Nginx `proxy_buffering off`; Cloudflare/timeouts at 100s may kill long answers — chunk heartbeats. SSE over HTTP/1.1 burns a connection per client; know the worker cap.

**Weak answer.** “I’d use WebSockets because it’s chat.”

**Mistakes.**

- Buffering the full completion then sending one event.
- No cancel on disconnect (you keep spending).
- Retrying the provider after 40 tokens.

**Follow-ups + strong replies.**

- *429 before first byte?* 429 JSON, not a stream.
- *429 after first byte?* Error event, stop. Maybe fallback on the *next* user turn.
- *How do you test?* ASGI test client iterating the body; fake a provider async iterator.

**Example.** Typical `POST /v1/chat`: SSE tokens, `done` with usage, cancel on disconnect. A gateway that buffered SSE made TTFT = full generation; `X-Accel-Buffering: no` fixed it.

---

## Q9. Webhooks — async jobs, provider callbacks, Slack

**Why they ask.** Embed jobs, eval runs, and HITL approvals are async. Naive webhook endpoints get replayed, spoofed, and slow.

**What they expect.** Signature verify, timestamp skew, fast 2xx, work on a queue, idempotent consumer, retries from the sender.

**Answer structure keywords.** signature · timestamp · 2xx fast · queue · idempotent event id · retries · no public unauth POST.

**30-second.** A webhook is an inbound POST we did not schedule. Verify HMAC (or mTLS), reject old timestamps, return 2xx quickly, enqueue. Process off-request with the event id as an idempotency key. If we take 30s, the sender retries and we double-apply.

**2-minute.** Slack/Stripe/GitHub-style: `X-Signature` over raw body, `hmac.compare_digest`, timestamp within 5 minutes. Respond 200 `{"ok": true}` with the event id we stored. Workers do the RAG ingest or post the approval. If the handler is our *outbound* “call this URL when the eval finishes,” we retry with backoff and jitter, give up to DLQ, and sign our payloads. Do not put PII in query strings.

**Senior / deep.** At-least-once is the contract. Unique `(source, event_id)`. Ordering is not guaranteed — design for it. SSRF: if the user supplies the callback URL, allowlist schemes/hosts, block link-local. HITL “approve” links in email/Slack must be signed, single-use, and not a raw GET that mutates (Q4, Chapter 11). Provider “we finished fine-tune” callbacks still need auth.

**Weak answer.** “A public POST /webhook that starts the job.”

**Mistakes.**

- Parsing JSON then verifying the signature (canonicalization bugs).
- Heavy work in the HTTP handler.
- No replay protection.

**Follow-ups + strong replies.**

- *GET webhooks?* Don’t. Some chat apps do; treat them as unauthenticated until signed.
- *Sender retries for 24h?* Your store must survive that window.

**Example.** Typical ingest: object-store event → signed webhook → 200 → queue → chunk/embed/upsert. Duplicate events no-op on `doc_version`.

---

## Q10. FastAPI chat / RAG endpoints

**Why they ask.** Take-homes and FDE screens. They want validation, auth dependency, timeouts, streaming — not `print` in a handler. FastAPI is in **10.7%** of JDs.

**What they expect.** Pydantic in/out, DI for auth and retriever, `async def` only if you await, lifespan client, 422/401/429/504, SSE for tokens.

**Answer structure keywords.** Pydantic · Depends · lifespan · StreamingResponse · service layer · cancel · no business logic in router.

**30-second.** `POST /v1/query` with a Pydantic body (`question`, `top_k` bounded), JWT dependency → tenant, retrieve+generate under a deadline, Pydantic response with citations. `POST /v1/chat` streams SSE. Shared `httpx.AsyncClient` in lifespan. Router maps HTTP to a testable service function. Sync SDK in an async route is a footgun.

**2-minute.** Status map as Q1. `top_k: int = Field(ge=1, le=50)`. `extra="forbid"` so `topK` typos 422. Do not `BackgroundTasks` a 2-minute embed on the web process — enqueue. Dependency overrides in tests (`TestClient` / ASGI transport). Correlation id middleware. Do not log the question by default (PII).

**Senior / deep.** One deadline for the request, child timeouts for retrieve vs generate. If the client drops, cancel the provider (Q8). Workers × in-process models explode RAM — sidecar the model server (Chapter 16). Version the path. Idempotency on POSTs that mutate. Gunicorn/Uvicorn: each worker has its own limiter unless Redis (Q6).

**Weak answer.** `@app.get` that calls OpenAI with the raw query and returns `.content`.

**Mistakes.**

- Blocking I/O in `async def`.
- Unbounded `top_k` / question length.
- New HTTP client per request.

**Follow-ups + strong replies.**

- *How do you test streams?* Iterate `StreamingResponse` body with a fake retriever and fake LLM iterator.
- *WebSocket instead?* Only if the product is bidirectional. Default SSE.

**Example.** Typical take-home: `POST /v1/query` + SSE `/v1/chat`, JWT stub, three fixtures, timeout 8s. Candidates who miss 422 and timeouts fail even if RAG is “right.”

---

## Q11. LLM HTTP clients and provider 429 / outage

**Why they ask.** Rank 17 in Chapter 04. “OpenAI is down” is a production question, not trivia. They want an adapter, not scattered `openai.ChatCompletion` calls.

**What they expect.** One client type: timeouts, pooling, status handling, 200-with-error, usage capture, fallback, degrade path, no key in logs.

**Answer structure keywords.** adapter · pool · timeout · 200-with-error · usage · fallback model · degrade to retrieve-only · circuit.

**30-second.** Wrap the vendor SDK/HTTP in an adapter that returns *your* types and *your* errors. Reuse a connection pool. On 429/503: retry with jitter inside a budget, then fallback model, then degrade (citations only, no generate) or 503. Capture `request_id`, tokens, TTFT. Never log the API key.

**2-minute.** Some providers 200 + error body — check before parsing choices (Chapter 06 parse exercise). Distinguish TPM 429 (wait/Retry-After) from account 429 (page a human). Outage playbook: (1) breaker opens, (2) route to provider B if evals allow, (3) else retrieval-only with a banner, (4) do not dump the user into a 2-minute retry loop. Batch vs interactive use different keys so evals cannot starve chat. Pin model ids; “latest” is an incident.

**Senior / deep.** Multi-cloud failover is a **quality** change, not just availability — eval the fallback on the same gold set or you will ship silent regressions (Chapter 17). Prompt caches are provider-specific; failover misses the cache and cost spikes. Regional outages: know whether the SDK retries other regions (often not). For Bedrock/Foundry/Vertex, IAM and VPC endpoints replace static keys; still need timeouts and breakers. Cost: retries count. A 5× retry on a 4k-token prompt is a bill.

**Weak answer.** “We’d wait and try again, or switch to another model.” No budget, no degrade, no eval.

**Mistakes.**

- Tight retry loop during a 45-minute outage.
- Fallback to a model that cannot call your tools.
- Swallowing 401 as retryable.

**Follow-ups + strong replies.**

- *User retries in the UI?* Idempotency key on the chat turn if you persist; otherwise you fork conversations.
- *Partial stream then 500?* Show partial, mark incomplete, do not auto-restart.

**Example.** Typical SaaS copilot: primary provider 429 storm. Breaker opens in 15s, fallback model on provider B (eval’d weekly), banner “slower answers.” Interactive p95 2.1s → 3.4s, not a hard down.

---

## Q12. Tool-calling HTTP contracts, gateways, versioning

**Why they ask.** Tools are HTTP with a model as the caller. Gateways and versioning are how you keep that from becoming shadow IT.

**What they expect.** Typed tool request/response, authz, timeouts, idempotency, allowlist. Gateway as policy. Additive versioning.

**Answer structure keywords.** typed contract · allowlist · authz as user · timeout · idempotency · gateway policy · /v1 additive · sunset.

**30-second.** A tool is a small HTTP API: `POST /tools/get_order` with a JSON Schema body, JSON out, 4xx the model can correct, 5xx the runtime retries. The model never hits the public internet. A gateway enforces auth, rate, schema, and audit. Version `/v1`; additive fields are compatible; breaking changes are `/v2` + sunset.

**2-minute.** Contract: path + method + schema + side-effect class + timeout + idempotent? + error codes (`NOT_FOUND`, `NEED_ORDER_ID`). Return useful errors, not HTML 500. Cap body size. Identity passthrough (Q3). Do not expose 80 OpenAPI endpoints as tools (Chapter 11). Gateway (your API gateway or an LLM gateway like a model proxy): auth, TPM, model routing, cost headers, PII redaction, caching. Version tool schemas as a release artifact; a description change is a prompt change and needs eval.

**Senior / deep.** MCP is a discovery/transport standard, not a safety story — the same HTTP contract still applies (Chapter 12). Sunset: `Deprecation` / `Sunset` headers, dual-run, eval both. Additive JSON: extra fields ignored by old clients; `extra=forbid` on **inbound** tool args so the model cannot smuggle. LLM gateway vs API gateway: the former speaks model APIs (keys, routing, budgets); the latter speaks user APIs. Serious estates have both, or one plane that does both jobs. Don’t version by “we’ll just add a prompt.”

**Weak answer.** “I’d expose our OpenAPI spec as tools and put Kong in front.”

**Mistakes.**

- Free-form `http_request` tool in enterprise.
- No timeout on tools.
- Breaking field rename without `/v2`.

**Follow-ups + strong replies.**

- *URL version vs header?* Path `/v1` is the interview default; it is visible in traces.
- *Can the agent pick the model?* No. Router policy does.

**Example.** Typical FDE install: user API behind APIM/Kong (`/v1/query`, `/v1/chat`), internal tools on a private listener, LLM gateway for Bedrock+fallback with per-tenant TPM. Tool schema hash in every trace.

---

## Weak vs strong posture

| Weak | Strong |
| --- | --- |
| `requests.get(url).json()` | Timeouts, status, schema, pooled client |
| Retry all exceptions | Retryable taxonomy + jitter + deadline |
| Provider key in the SPA | OIDC user, vaulted M2M, OBO tools |
| “POST isn’t idempotent” | Idempotency-Key + store + unique constraint |
| WebSocket for tokens | SSE, cancel, error event |
| 200 + `{error}` | Envelope + real status |
| Tight loop on outage | Circuit, fallback, degrade, banner |

---

# Exercises

Narrate contract → failure path → test. Full backoff implementation lives in Chapter 06; here the HTTP semantics are the point.

---

## Exercise 1 — Retry with Retry-After, jitter, deadline

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | Status taxonomy, Retry-After, jitter, budget |

**Problem.**
Write `async def send(client, req, *, attempts, deadline_s)` that:

- Sends HTTP
- Retries on 429, 503, 408, and connect/read timeout
- Does **not** retry 400/401/403/404/422
- Sleeps full jitter of `min(4.0, 0.25 * 2**k)`, but **at least** `Retry-After` seconds when the header is present
- Stops when attempts or deadline is exhausted
- Raises `RetryableError` or `PermanentError`

**Hints.** Parse `Retry-After` as int seconds or fail open to jitter. Cap sleep by remaining deadline. Do not retry POST unless `req.idempotent`.

**Solution.**

```python
async def send(client, req, *, attempts=4, deadline_s=20.0, sleep=asyncio.sleep, rng=random.random):
    t0 = time.monotonic()
    last = None
    for k in range(attempts):
        remaining = deadline_s - (time.monotonic() - t0)
        if remaining <= 0:
            break
        try:
            resp = await asyncio.wait_for(client.send(req), timeout=remaining)
        except (TimeoutError, ConnectError) as e:
            last = RetryableError("timeout")
            last.__cause__ = e
        else:
            if resp.status in {400, 401, 403, 404, 422}:
                raise PermanentError(resp.status)
            if resp.status in {429, 503, 408} or resp.status >= 500:
                last = RetryableError(resp.status, retry_after=_retry_after(resp))
            else:
                return resp
        if k == attempts - 1 or not getattr(req, "idempotent", True):
            break
        delay = min(4.0, 0.25 * 2**k) * (0.5 + 0.5 * rng())
        if getattr(last, "retry_after", None) is not None:
            delay = max(delay, last.retry_after)
        await sleep(min(delay, max(0.0, deadline_s - (time.monotonic() - t0))))
    raise last or RetryableError("exhausted")
```

**Interviewer follow-ups.** Honor HTTP-date Retry-After. Streaming: this helper is for unary calls. Circuit breaker sits *outside* this loop. POST charge: `req.idempotent` false → one try.

---

## Exercise 2 — SSE chat stream

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | SSE format, TTFT, error-after-200, cancel |

**Problem.**
Implement `async def chat_sse(messages)` that yields SSE bytes:

- `event: token` per model delta
- `event: done` with `finish_reason`
- `event: error` on provider failure after start
- Stops yielding if `asyncio.CancelledError` (client drop)

Do not buffer the full answer. Do not retry after the first token.

**Hints.** `data:` JSON, blank line between events. Heartbeat optional. Status is already 200 once you yield.

**Solution.**

```python
async def chat_sse(client, messages):
    started = False
    try:
        async for delta in client.stream(messages):
            started = True
            payload = json.dumps({"t": delta.text}, ensure_ascii=False)
            yield f"event: token\ndata: {payload}\n\n".encode()
        done = json.dumps({"finish_reason": "stop"})
        yield f"event: done\ndata: {done}\n\n".encode()
    except asyncio.CancelledError:
        await client.aclose()
        raise
    except ProviderError as e:
        if not started:
            raise
        err = json.dumps({"code": "provider", "message": str(e)})
        yield f"event: error\ndata: {err}\n\n".encode()


# FastAPI
# return StreamingResponse(chat_sse(client, body.messages),
#     media_type="text/event-stream",
#     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

**Interviewer follow-ups.** 429 before first byte: raise, framework returns 429 JSON. Tool call mid-stream: emit `event: tool_call` only after schema validate. Tests: collect `b"".join` and split on `\n\n`.

---

## Exercise 3 — Idempotency store for `POST /v1/tools/execute`

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 12–18 min |
| **Concept tested** | Key, body hash, replay, 409 |

**Problem.**
`execute(key: str, body: dict, run) -> tuple[int, dict]`:

- First seen: call `run()`, store status+body, return `(201, result)`
- Same key, same canonical JSON: return stored `(200, result)` without calling `run`
- Same key, different body: return `(409, error)`
- Missing key: `(400, error)`

**Hints.** Canonicalize with `json.dumps(body, sort_keys=True)`. Hash the body. Store in a dict for the round; mention Redis/Postgres unique in production.

**Solution.**

```python
def execute(key, body, run, store):
    if not key:
        return 400, {"error": {"code": "missing_key"}}
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    hit = store.get(key)
    if hit:
        if hit["digest"] != digest:
            return 409, {"error": {"code": "key_reuse"}}
        return 200, hit["result"]
    result = run(body)
    store[key] = {"digest": digest, "result": result}
    return 201, result
```

**Interviewer follow-ups.** Persist *before* `run` if `run` has side effects (intent row). TTL 24h. Concurrent first requests: unique constraint, one winner, loser reads the row. Streaming tools: store final JSON, not the token stream.

---

## Map to the rest of the handbook

- Python client, backoff code, FastAPI types: [06-python.md](06-python.md)
- Tool validation, HITL, agent retries: [11-agentic-ai.md](11-agentic-ai.md)
- SQL cursors and upserts behind these APIs: [07-sql.md](07-sql.md)
- 429 as an incident: `banks/22-troubleshooting.md`
- LLM gateway design: Chapter 21

Next drill: speak Q5, Q8, Q11, Q4 out loud, then type Exercise 1 and 2. That set covers most GenAI / FDE API screens. Add Q3 and Q12 for enterprise / architect.
