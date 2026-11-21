# ADR-001 — Code computes priority, LLM extracts only

Date: 2026-09-18. Status: accepted.
Context: ticket text may contain "set P1" injection.
Decision: ITIL matrix + routing in code; LLM returns impact/urgency/category/service only.
Consequences: injection can't escalate; audit is a table, not a prompt.
