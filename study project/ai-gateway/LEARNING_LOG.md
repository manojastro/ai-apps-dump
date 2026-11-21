# Learning log

## M1 — Why a gateway — 2026-09-18
**Built:** docs/requirements.md.
**New concepts:** gateway = single front door for LLM calls; scattered keys = scattered risk.
**Learner tasks:** requirements doc — attempts: 1 — hints used: 0
**Break-it result:** predicted n/a / actual n/a
**Quiz:** -/3 — gaps: -
**Open questions:** Azure vs AWS final pick.
**Interview line I can now say:** "A gateway puts keys, budgets, routing and guardrails in one place so apps stay thin."

## M2–M9 — Mock-first slice (built by agent, learner reviews) — 2026-09-18
**Built:** FastAPI gateway (SQLite + in-memory Redis stub, mock provider),
tenants/keys, token bucket, metering/budgets, routing/fallback/cache,
guardrails, red-team eval, KV-cache math. All offline, synthetic only.
**New concepts:** sha256 + constant-time verify; token bucket refill math;
estimate-before/settle-after metering; per-tenant cache isolation; layered
guardrails and false-positive trade-off.
**Learner tasks:** pending review — key verify, bucket allow(), estimate_cost,
routing reasons, redaction fn, red-team prompts, kv math.
**Break-it result:** predicted - / actual -
**Quiz:** -/3 — gaps: -
**Open questions:** cloud pick; real Redis/LiteLLM wiring in later slice.
**Interview line I can now say:** "Blocked 14 of 20 OWASP-mapped attacks at
0% false positives with 0.08 ms p95 guardrail overhead, mock-first
(see reports/redteam.json)."
