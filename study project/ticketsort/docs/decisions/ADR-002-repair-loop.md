# ADR-002 — Structured output + repair loop (max 2)

Date: 2026-09-18. Status: accepted.
Context: LLMs return near-JSON with typos.
Decision: native JSON mode where available, Pydantic validate, send error back max 2 times, then 502.
Consequences: fewer 502s, bounded cost/latency.
