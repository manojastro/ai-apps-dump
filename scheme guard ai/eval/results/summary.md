# SchemaGuard evaluation summary

- **Date (UTC):** 2026-11-15 15:05
- **Command:** `uv run python eval/run_eval.py --llm fake`
- **Git commit:** `e6f1183`  ·  **LLM provider:** `fake`  ·  **Scenarios:** 25

> The `fake` provider is a deterministic scripted fixer, not a model. These numbers measure SchemaGuard's
> deterministic parts (lineage, verdict rules, sandbox, loop control, guardrails) and the fake's heuristics;
> they say nothing about LLM quality. Token counts for `fake` are character-based estimates and cost is $0.

Labels in `eval/scenarios/` were written by the same author as the verdict rules, so the label-based
metrics measure consistency with that specification. The **oracle** rows are independent: they compare
predictions with what DuckDB actually does when the unchanged pipeline runs on the new schema.

| Metric | Value |
|---|---|
| Impact precision (graph traversal) | 100.0% (214 TP / 0 FP) |
| Impact recall (graph traversal) | 100.0% (0 FN) |
| Verdict accuracy | 100.0% over 183 labelled assets |
| Route accuracy (report / approval / escalate) | 100.0% |
| Change-class accuracy | 100.0% |
| Fix test-pass rate | 100.0% (14/14 scenarios expected to be fixable) |
| Avg retries in fix loop | 0.12 over 16 runs |
| Escalation accuracy | 100.0% (precision 100.0%, recall 100.0%) |
| Injection detection accuracy | 100.0% |
| Failing-build prediction accuracy | 100.0% |
| **Oracle:** predicted failing builds = DuckDB reality | 100.0% of scenarios |
| **Oracle:** breaking-test precision / recall vs DuckDB | 100.0% / 100.0% (101 TP, 101 predicted, 101 actual) |
| Latency to decision p50 / p95 | 3.06s / 3.70s |
| Latency end-to-end (incl. approval + branch) p50 / p95 | 3.83s / 4.83s |
| Tokens per run (mean / max) | 3918 / 9689 |
| LLM calls per run (mean) | 3.4 |
| Estimated cost per run (mean) / total | $0.0000 / $0.0000 |

## Per scenario

| Scenario | Route exp → got | Final | Impact FP/FN | Verdicts ok | Fix | Retries | Time (s) |
|---|---|---|---|---|---|---|---|
| s01_rename_amount | approval → approval | completed | 0/0 | 12/12 | pass | 0 | 4.66 |
| s02_rename_amount_alias | approval → approval | completed | 0/0 | 10/10 | pass | 0 | 4.28 |
| s03_drop_amount | escalate → escalate | escalated | 0/0 | 10/10 | fail | 1 | 3.10 |
| s04_drop_unused_coupon | report → report | no_impact | 0/0 | 0/0 | — | 0 | 0.04 |
| s05_drop_currency | approval → approval | completed | 0/0 | 4/4 | pass | 0 | 4.22 |
| s06_quantity_int_to_string | approval → approval | completed | 0/0 | 5/5 | pass | 0 | 4.17 |
| s07_quantity_int_to_long | report → report | no_impact | 0/0 | 5/5 | — | 0 | 0.05 |
| s08_amount_double_to_string | approval → approval | completed | 0/0 | 10/10 | pass | 0 | 4.39 |
| s09_status_new_enum | approval → approval | completed | 0/0 | 18/18 | pass | 0 | 3.86 |
| s10_customer_id_nullable | approval → approval | completed | 0/0 | 5/5 | pass | 0 | 4.10 |
| s11_add_nullable_field | report → report | no_impact | 0/0 | 0/0 | — | 0 | 0.04 |
| s12_add_required_field | report → report | no_impact | 0/0 | 0/0 | — | 0 | 0.04 |
| s13_doc_injection_only | report → report | no_impact | 0/0 | 0/0 | — | 0 | 0.05 |
| s14_rename_with_injection | approval → approval | completed | 0/0 | 10/10 | pass | 0 | 3.83 |
| s15_unconsumed_topic | report → report | no_impact | 0/0 | 0/0 | — | 0 | 0.04 |
| s16_payments_rename_amount | approval → approval | completed | 0/0 | 6/6 | pass | 0 | 3.66 |
| s17_payment_method_new_enum | approval → approval | completed | 0/0 | 5/5 | pass | 0 | 4.57 |
| s18_customers_rename_country | approval → approval | completed | 0/0 | 9/9 | pass | 0 | 4.92 |
| s19_customers_drop_email | approval → approval | completed | 0/0 | 1/1 | pass | 0 | 4.88 |
| s20_drop_customer_id | escalate → escalate | escalated | 0/0 | 30/30 | fail | 1 | 3.37 |
| s21_created_at_to_string | approval → approval | completed | 0/0 | 10/10 | pass | 0 | 4.41 |
| s22_multi_rename_and_enum | approval → approval | completed | 0/0 | 15/15 | pass | 0 | 4.17 |
| s23_coupon_required | report → report | no_impact | 0/0 | 0/0 | — | 0 | 0.05 |
| s24_enum_remove_cancelled | escalate → escalate | escalated | 0/0 | 13/13 | — | 0 | 0.14 |
| s25_quantity_int_to_double | report → report | no_impact | 0/0 | 5/5 | — | 0 | 0.06 |

## Oracle disagreements (prediction vs running the unchanged pipeline on the new schema)

None.

## Mismatches

None.
