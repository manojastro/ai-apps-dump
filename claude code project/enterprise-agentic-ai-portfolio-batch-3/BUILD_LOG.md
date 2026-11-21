# Batch 3 Portfolio — Build Log

Meaningful architectural decisions, failed approaches, tradeoffs, and fixes.
No raw terminal dumps.

---

## 2026-08-25 — Kickoff & environment decisions

**Environment recon.** Windows 11 host. Python 3.11.15 available as `python`
(also 3.13 via `py`). Node 22 + npm 10 present. Docker CLI 28.1.1 +
Compose v2.35 installed but **daemon not running at kickoff**; Docker Desktop
was launched and availability re-checked later (see entries below). Git 2.52.
D: drive has ~9.9 GB free — enough for five venvs, SQLite data, and local
Docker images, but a constraint worth noting.

**Decision — frontend stack.** The brief prefers React/Next/TypeScript. We
deliberately build the five dashboards as zero-dependency static SPAs served by
each FastAPI backend instead. Rationale: (a) `docker compose up --build` works
with no Node toolchain or registry flakiness; (b) review effort goes to
dashboard information architecture rather than build plumbing; (c) each
`LIMITATIONS.md` records the React migration path. Tradeoff accepted knowingly.

**Decision — migrations.** SQLAlchemy `create_all()` on startup instead of
Alembic for POC; schema evolution is out of scope for batch 3 and recorded in
each project's LIMITATIONS.

**Decision — graph storage.** NetworkX in-process graphs seeded from each
project's relational store. Neo4j is documented as an adapter interface, not a
runtime dependency — keeps the five-project Docker footprint small on a 9.9 GB
free-disk machine.

**Decision — orchestration.** A framework-neutral workflow engine (persisted
stage machine) is the runtime; LangGraph mapping is documented per stage so the
migration is mechanical if adopted. Business logic never imports a framework.

**Failed approach — scaffolding via Git Bash.** Initial `mkdir && git init`
through the Bash tool hung for >2 min on this host; switched to PowerShell for
directory/git operations. Workers are instructed to avoid interactive git
entirely (supervisor commits).

## 2026-08-25 — Worker 13 complete & independently verified (first finisher)

SAP Change Impact Agent delivered by Worker 13. Supervisor verification:
re-ran pytest independently (**50 passed / 0 failed**, ~44s), confirmed all
required files present, and executed `scripts\create_high_risk_transport.py
--fresh` end-to-end — canonical pricing transport flows import → impact
(ORDER_TO_CASH + RECORD_TO_REPORT + INVOIC_OUT) → regression scope 4/17 tests
with reason codes → risk 63.5/100 HIGH → approval gate → simulated regression
**fails BILLING_CREATE_TEST + INVOIC_PAYLOAD_TEST pre-release**, records
DEF-0001/0002 → VALIDATION_FAILED. Clean control transport passes at LOW risk.
Evaluation reports recall/precision/risk-band accuracy 1.0 across 6 authored
transports (self-authored ground truth — proves spec compliance, not real-SAP
accuracy; documented as such in LIMITATIONS.md). Worker also built the Docker
image and ran the container through its HEALTHCHECK plus live API/SPA/metrics/
evaluation checks inside the container, then stopped it. Notable real bugs
found and fixed during the build: SQLAlchemy autoflush=False hid pending
TransportObject rows from a relationship load (objects_changed persisted as 0);
naive-vs-aware datetime subtraction in the demo approvals step.

## 2026-08-25 — Worker 14 complete & independently verified

Endpoint Patch Risk & Safe Rollout Agent delivered. Supervisor verification:
re-ran pytest independently (**157 passed / 0 failed**; ~4 min under concurrent
build load vs worker's ~25 s — same result), required-files check all present,
and executed `scripts\start_patch_campaign.py --reseed` against the full
2501-endpoint estate. Observed live: approval gate refused pre-approval ring
advance (403); Ring 0 clean; **Ring 1 autonomously halted at 50% failure vs
5% threshold**; failures classified app_crash; RCA named
`warehouse-scanner-suite 7.3.1 < 7.4.2` as catalog-confirmed root cause
(confidence 0.95) and separately flagged a suspected *undocumented*
incompatibility (scanner firmware 3.2.0 on 100% of failures, 0% of successes);
rollback restored 11 devices with post-rollback validation passing; campaign
ROLLED_BACK without ever reaching Rings 3–4. Clean-patch control completes all
five rings (worker-verified). Real bugs fixed mid-build by the worker: missing
`functools.wraps` on a FastAPI decorator broke every gated route with 422s;
sandbox `dispose()` destroyed the shared session factory; demo scripts
resolved SQLite paths against caller CWD.

---

*(entries appended during build)*
