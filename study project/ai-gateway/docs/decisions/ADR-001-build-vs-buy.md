# ADR-001 — Build a thin gateway, don't buy one

Date: 2026-09-18. Status: accepted.
Context: need tenant keys, budgets, guardrails for 3 internal apps.
Decision: build a thin FastAPI gateway (mock provider first), adopt a
managed gateway later if traffic justifies it.
Consequences: full control + learning value; we own uptime and safety gaps.
