# ADR-001 — Golden set of 50 (15 smoke)

Date: 2026-09-18. Status: accepted.

## Context

Research notes disagreed on golden-set size (15 vs 50 vs 50–200).
The set must cover 6 categories (answerable, unanswerable, conflicting,
exact_code, multi_hop, outdated), include must-refuse rows, and stay cheap
enough to run on every PR (smoke subset).

## Decision

- **50 full + 15 smoke.** 50 is the smallest size that gives every category
  ≥6 rows while keeping a full mock run instant and a future LLM-judge run
  affordable. 15 smoke rows cover all 6 categories for CI.
- 20 rows hand-written (learner task M2); 30 programmatic expansions,
  reviewed; all `author: human`. All synthetic (Acme Retail Ltd).
- The set is **frozen once baseline runs start**: edits create a new version,
  otherwise run-to-run comparison is meaningless.

## Consequences

- Gate thresholds are set from the stub baseline in `eval_config.yaml`.
- Re-verified by `scripts/check_balance.py` and `tests/test_golden.py`.
