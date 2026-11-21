# ProductionLens implementation plan

Specification: docs/REQUIREMENTS.md. Existing InsightAI is preserved at /insight.

## Decisions
- Reuse installed Next.js, React, TypeScript, Tailwind and Recharts instead of replacing the working frontend with Vite. Root app is the web boundary.
- Add FastAPI and a separate worker process. SQLAlchemy supports PostgreSQL in Compose and SQLite for a credential-free local replay profile. SQLite is a development adaptation, not a PostgreSQL validation claim.
- Persist jobs before transport. Reconcile queued and lease-expired work from the database.
- Never substitute scripted responses in live mode. Missing provider configuration is an explicit error.
- No publishing, paid resources or external mutations.

## Ordered vertical slices
1. Foundation: migrations, unique local admin setup, sessions, roles, API health; validate authentication and persistence.
2. Replay investigations: versioned telemetry, bounded tool interfaces, durable worker, evidence-backed diagnosis, usable incident workspace; validate scope and cancellation.
3. Recovery: exact-action hash, review, expiry, idempotent demo replay executor, evidence-based verification; validate reject/duplicate/tamper paths.
4. Evaluation: independent scenario catalog and assertions, baseline/candidate comparisons, fail-closed release policy, exports; validate regression and absent critical evidence.
5. Demo/live infrastructure: bounded demo services, real telemetry adapters, provider tool loop, Compose services; measure what can run locally and document unverified paths.
6. Product verification: responsive browser flows, API tests, build, CI, documentation and measured evidence.

## Design
Palette: canvas #0b1019, slate #121a27, border #253044, text #e7edf6, cyan #54c5df, emerald #5ed5ae, amber #e9b768.
Typography: Segoe UI for readable operational content; Consolas reserved for trace IDs and code.
Layout: left-aligned incident operations desk with a narrow navigation rail, broad investigation/evidence area, contextual activity rail.
```
nav | workspace / explicit mode                       | user
    | heading + create investigation
    | counters tied to persisted runs
    | incident list / telemetry plot  | integration state
    | evidence and agent events       | review queue
```
Design critique: generic dashboards overemphasize anonymous metric cards. ProductionLens instead makes an evidence-linked investigation timeline the distinctive element, using restrained cyan to connect observations, tool activity and review. Every sample and simulated result is visibly labeled.

## Verification limits at inspection
Windows, Python 3.11.15, Node 22.17.1. Docker CLI exists; Docker Linux engine unavailable. No Git repository exists yet. No provider credentials inspected or assumed.
