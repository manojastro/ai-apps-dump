# ADR-001 — Approval tokens for AI writes

Status: accepted. Date: 2026-09-18.

Context: LLMs can be tricked (prompt injection) into calling destructive tools.
Change management for AI needs the same gate as CAB: a human approves each change.

Decision: single-use, scoped (`tool` + `target` record), expiring (10 min default)
random tokens. Stored ONLY as SHA-256 hash; compared with `hmac.compare_digest`;
marked `used` in the same `BEGIN IMMEDIATE` transaction as the scope/expiry check.

Alternatives: long-lived API keys (replayable — rejected), human click-to-approve
per call without scope (too broad — rejected), prompt-only "ask before writing"
(spoofable — rejected).

Consequences: every write needs `POST /approvals` first; replays/wrong-target/
expired tokens fail (tests prove it); audit_log records each attempt.
