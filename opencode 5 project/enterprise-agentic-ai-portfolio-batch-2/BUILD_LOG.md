# Build Log — Batch 2

Chronological record of design decisions, failures, fixes, and tradeoffs. No raw terminal dumps.

## 2026-08-25 — Bootstrap

- Workspace root created at `D:\ai apps dump\opencode 5 project\enterprise-agentic-ai-portfolio-batch-2`
  with five independent project folders. Existing files in the parent folder: none.
- Environment inspected: Python 3.11.15 (venv at `hermes-agent\venv`), pip 24.0.
- Dependencies installed globally and shared read-only by all projects:
  fastapi, uvicorn, pydantic v2, sqlalchemy, httpx, pytest, networkx,
  scikit-learn, scipy, pandas, numpy, joblib.
  - Failure: first combined `pip install` timed out twice (slow network, large wheels);
    fixed by installing incrementally with `--prefer-binary`. Verified imports afterwards.

## Key design decisions (apply to all five projects)

1. **SQLite per project for the POC** instead of PostgreSQL: zero-infrastructure local runs;
   SQLAlchemy ORM keeps the production Postgres swap trivial. Documented in each LIMITATIONS.md.
2. **Deterministic-first agent pipelines**: every agent step is typed Python producing
   structured evidence/hypotheses persisted to DB; the LLM adapter (mock by default) only
   narrates computed results. LLM never decides control flow, scores, or remediations.
3. **Typed tool framework** everywhere: input/output Pydantic schemas, permission flag
   (safe/mutating), timeout, and DB audit of every call. No shell execution from agents.
4. **Approval state machine** shared conceptually across projects:
   PROPOSED -> VALIDATING -> AWAITING_APPROVAL -> APPROVED -> EXECUTING -> VERIFYING ->
   COMPLETED | FAILED | ROLLED_BACK; illegal transitions rejected.
5. **Validation before recommendation is "done"**: P6 shadow attack-graph re-analysis,
   P7 candidate digital-twin simulation, P8 champion/challenger gates + shadow/canary,
   P9 contract/consumer tests + blast-radius verification, P10 targeted test execution.
6. **Parallel build strategy**: five isolated workers, one per project folder, then a
   supervisor pass for root docs, cross-checks, and demo verification.

## Build entries

- (workers append below)
