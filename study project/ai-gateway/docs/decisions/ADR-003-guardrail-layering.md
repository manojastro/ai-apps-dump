# ADR-003 — Layered guardrails with profiles

Date: 2026-09-18. Status: accepted.
Context: one check cannot catch injection, PII, and bad output at once.
Decision: layers (size -> injection -> PII redact -> output schema/secrets),
per-tenant profiles (`strict`, `standard`), every block logged with a reason.
Trade-off: stricter blocks more attacks AND more good requests (see
`reports/redteam.json` for the measured numbers).
Does not replace system-level controls (auth, network, data retention).
