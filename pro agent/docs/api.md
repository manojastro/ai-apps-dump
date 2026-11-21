# API

Interactive OpenAPI: `GET /api/docs` (schema at `/api/openapi.json`).

* Authentication: `POST /api/auth/login` sets an HttpOnly `procnav_session` cookie and a readable
  `procnav_csrf` cookie. Every non-GET request must send `X-CSRF-Token: <csrf>`.
* Tenant scope comes from the session; no endpoint accepts a tenant ID for authorization.
* Mutations that create things accept `Idempotency-Key` (8-200 chars). Same key + same body → the
  stored response; same key + different body → `409 IDEMPOTENCY_CONFLICT`.
* Pagination: `limit` (1-100), `offset`. Request bodies over 64 KB → `413 PAYLOAD_TOO_LARGE`.

## Error envelope

```json
{"error": {"code": "APPROVER_IS_REQUESTER", "message": "The requester cannot approve their own purchase", "details": {}}}
```

Stable codes: `AUTH_REQUIRED`, `AUTH_INVALID`, `CSRF_FAILED`, `FORBIDDEN_ROLE`, `NOT_FOUND`,
`VALIDATION_FAILED`, `RATE_LIMITED`, `IDEMPOTENCY_CONFLICT`, `INVALID_TRANSITION`, `REQUEST_INCOMPLETE`,
`RUN_ACTIVE`, `APPROVER_IS_REQUESTER`, `APPROVAL_EXPIRED`, `APPROVAL_NOT_PENDING`, `QUOTE_INELIGIBLE`,
`HARD_POLICY_EXCEPTION`, `RUN_NOT_CANCELABLE`, `PAYLOAD_TOO_LARGE`, `EVIDENCE_UNAVAILABLE`,
`FIXTURE_CONTROL_UNAVAILABLE`, `CONFLICT`.

## Endpoints

| Method & path | Role | Purpose |
|---|---|---|
| `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/session` | — | Session management |
| `GET /api/health` | — | DB and worker heartbeat status |
| `GET /api/catalog/products` | any | Canonical products |
| `GET /api/suppliers`, `PATCH /api/suppliers/{id}` | any / admin | Supplier configuration |
| `GET /api/policies`, `POST /api/policies` | any / admin | Policy versions (POST activates a new version) |
| `POST /api/policy-exceptions` | admin | Explicit hard-rule exception for one quote |
| `POST /api/requests`, `GET /api/requests`, `GET /api/requests/{id}` | requester/admin | Purchase requests |
| `POST /api/requests/{id}/runs` | requester/admin | Start an asynchronous run → `202` with run id |
| `GET /api/runs`, `GET /api/runs/{id}`, `GET /api/runs/{id}/steps` | any | Run status, budgets, typed steps |
| `GET /api/runs/{id}/events` | any | Persisted events: SSE (`Accept: text/event-stream`, resume with `Last-Event-ID`) or JSON polling (`?after=`) |
| `POST /api/runs/{id}/cancel`, `/pause`, `/resume` | requester/admin | Controls (resume body `{action: retry|skip|cancel}`) |
| `GET /api/runs/{id}/comparison`, `.csv`, `/summary.pdf` | any | Quote comparison and exports |
| `GET /api/approvals`, `GET /api/approvals/{id}` | any | Inbox and detail (with `can_decide`) |
| `POST /api/approvals/{id}/decision` | approver | Approve/reject with `acknowledged_fingerprint` |
| `POST /api/approvals/{id}/select-alternative` | approver | Choose another eligible quote (new bound request) |
| `GET /api/orders`, `GET /api/orders/{id}`, `POST /api/orders/{id}/reconcile` | any / approver+admin | Ledger, attempts, receipt checks; reconcile never resubmits |
| `GET /api/runs/{id}/evidence`, `GET /api/evidence/{id}` | any (own tenant) | Redacted evidence |
| `GET /api/audit` | any | Audit timeline |
| `GET /api/evals` | any | Benchmark results |
| `GET /api/admin/fixtures/scenarios`, `POST /api/admin/fixtures/reset`, `POST /api/admin/fixtures/mutate` | admin | Operator scenario controls (synthetic data only) |

## Examples

```bash
# sign in and keep cookies
curl -c jar -H 'Content-Type: application/json' \
  -d '{"email":"requester@acme.test","password":"<demo password>"}' http://localhost:8300/api/auth/login
CSRF=$(awk '/procnav_csrf/ {print $7}' jar)

# create a request (idempotent) and start a run
curl -b jar -H "X-CSRF-Token: $CSRF" -H 'Idempotency-Key: req-2026-10-07-001' -H 'Content-Type: application/json' \
  -d '{"title":"Ten laptops","canonical_product_id":"NW-PRO14-16-512","min_ram_gb":16,"min_ssd_gb":512,
       "quantity":10,"currency":"INR","budget_total":"500000.00","address_ref":"ADDR-BLR-01",
       "delivery_deadline":"2026-10-14"}' http://localhost:8300/api/requests
curl -b jar -H "X-CSRF-Token: $CSRF" -H 'Idempotency-Key: run-2026-10-07-001' -H 'Content-Type: application/json' \
  -d '{}' http://localhost:8300/api/requests/<request_id>/runs

# stream events
curl -N -b jar -H 'Accept: text/event-stream' http://localhost:8300/api/runs/<run_id>/events

# approver decides (fingerprint from GET /api/approvals/{id})
curl -b approver_jar -H "X-CSRF-Token: $CSRF2" -H 'Content-Type: application/json' -H 'Idempotency-Key: dec-001' \
  -d '{"decision":"approved","reason":"lowest verified landed cost","acknowledged_fingerprint":"<64 hex>"}' \
  http://localhost:8300/api/approvals/<approval_id>/decision
```
