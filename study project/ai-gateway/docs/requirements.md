# Requirements (learner-written, M1)

## Why a gateway?
Today every app (TicketSort, OpsCopilot, Incident Commander) would call model
providers directly. That means: API keys scattered in every repo, no single
view of spend, every app re-implements rate limits and safety checks
differently, and revoking one tenant means touching every service. A gateway
is the single front door: one place for keys, budgets, routing, guardrails
and audit. IT analogy: a central service desk front door instead of every
user calling engineers directly.

## Functional requirements
1. OpenAI-compatible `POST /v1/chat/completions` with `X-Task` routing.
2. Tenant keys: shown once, stored hashed, per-tenant allowed models.
3. Per-tenant rpm/tpm rate limits; 429 with `Retry-After`.
4. Cost ledger + monthly budgets (soft alert 80%, hard stop 100%).
5. Task routing with fallback + per-tenant exact-match cache (TTL).
6. Input/output guardrails with logged reasons; strict/standard profiles.
7. Usage endpoints for tenant and admin.

## Non-functional requirements
- Gateway overhead budget: p95 < 50 ms added latency (see `reports/load.json`).
- Availability: single container is fine for this slice (no HA claim).
- Data retention: ledger rows kept 90 days in real deploy (SQLite file here).
- Offline mock-first: no provider network calls in this slice.
- All data synthetic (Acme Retail Ltd). No real PII, keys, or employer data.
