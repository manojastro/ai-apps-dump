# Architecture decision records

All decisions below are accepted for the portfolio implementation, dated 2026-09-22.

## ADR 001 — LangGraph for explicit orchestration

Context: parallel investigation, conditional retry, durable state and human pauses must be inspectable.
Decision: use typed StateGraph nodes, reducers, join edges and supported checkpointers.
Consequence: graph dependencies are testable; execution remains coupled to LangGraph checkpoint semantics.

## ADR 002 — Deterministic acceptance criteria

Context: generated fixes may sound correct but corrupt data.
Decision: require all ten mandatory validators on replayed data before verification.
Consequence: acceptance is reproducible; rule coverage and reference-ledger correctness remain critical.

## ADR 003 — PostgreSQL and pgvector, SQLite locally

Context: audit data needs relational queries and knowledge benefits from filtered vector ranking.
Decision: PostgreSQL/pgvector in Compose; SQLite and the same cosine baseline for zero-service local use.
Consequence: easy onboarding, but both database paths require separate integration verification.

## ADR 004 — Separate verifier package

Context: worker self-approval creates correlated errors and hidden reasoning leakage.
Decision: an isolated deterministic verifier checks public evidence, claims, mandatory checks and permissions.
Consequence: independent boundaries are inspectable; this is not a general-purpose model-based fact checker.

## ADR 005 — Sandbox-only mutation

Context: a portfolio recovery agent must not execute unreviewed production changes.
Decision: allowlisted transformations on copied fixture rows; generate diff artifacts only.
Consequence: reliable replay and safe demonstrations; real deployment integration is intentionally future work.

## ADR 006 — Bounded remediation and correction

Context: unconstrained retries increase cost and can hide repeated failure.
Decision: default three remediation attempts, bounded evidence rounds and bounded provider correction.
Consequence: every path has a stopping condition; some incidents terminate without a recovery.

## ADR 007 — Reproducible simulator before vendor integrations

Context: reviewers need to run the complete flow without cloud accounts or paid models.
Decision: five controlled failure scenarios and a deterministic provider behind adapter protocols.
Consequence: transparent tests and labeled evaluation; measurements do not claim production generalization.
