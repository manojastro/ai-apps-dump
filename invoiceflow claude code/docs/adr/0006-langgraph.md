# ADR 0006: LangGraph for the agent

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (spec), Claude Code

## Context

The workflow is mostly fixed: match, investigate, retrieve, propose, validate, authorize,
approve, execute, record. It needs one bounded LLM tool loop, a durable human-approval pause
that survives restarts, and explicit failure routing.

## Options considered

1. **LangGraph** (1.2.17). An explicit state graph with conditional edges, `interrupt()` +
   `Command(resume=...)` for human approval, and pluggable checkpointers (SQLite,
   Postgres).
2. **OpenAI Agents SDK.** It's a good fit for model-driven tool loops. Durable mid-workflow
   human approval and a fixed control flow would have to be built by hand.
3. **A plain Python loop.** It's the smallest option, but persistence, resume and
   step-level tracing would all have to be reinvented.
4. **Agent Bricks templates.** Recommended by Databricks, but in Beta and unverified on
   Free Edition (ADR 0001).

## Decision

LangGraph. The graph lives in `agent/graph.py`; nodes are plain functions over a TypedDict
state that holds ids and JSON, never raw invoices.

## Consequences

- **A node re-runs from the top on resume**, so `await_approval` contains only `interrupt()`.
  Every other side effect is idempotent (audit event keys, ERP idempotency keys, drafts).
- **Resume across a real process restart is proven** by
  `tests/unit/agent/test_restart_and_wrappers.py`: one process pauses, another resumes
  from the SQLite checkpoint.
- The model chooses tools only inside `investigate`. Everything else is deterministic code.
