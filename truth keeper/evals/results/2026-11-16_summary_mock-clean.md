# Eval summary 2026-11-16_mock-clean

MOCK mode: the 'model' is a deterministic fixture, so these numbers test the pipeline and validators, not a real LLM.

## Detection

| dataset | type | precision | recall | F1 |
|---|---|---|---|---|
| default (seed 42) | CANCELLED_BUT_BILLING_ACTIVE | 1.0 | 1.0 | 1.0 |
| default (seed 42) | PLAN_MISMATCH | 1.0 | 1.0 | 1.0 |
| default (seed 42) | CHURNED_STILL_MARKETED | 1.0 | 1.0 | 1.0 |
| default (seed 42) | EMAIL_MISMATCH | 1.0 | 1.0 | 1.0 |
| default (seed 42) | DUPLICATE_CUSTOMER | 1.0 | 1.0 | 1.0 |
| default (seed 42) | PAST_DUE_BUT_CRM_ACTIVE | 1.0 | 1.0 | 1.0 |
| default (seed 42) | OVERALL | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | CANCELLED_BUT_BILLING_ACTIVE | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | PLAN_MISMATCH | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | CHURNED_STILL_MARKETED | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | EMAIL_MISMATCH | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | DUPLICATE_CUSTOMER | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | PAST_DUE_BUT_CRM_ACTIVE | 1.0 | 1.0 | 1.0 |
| hard (seed 7) | OVERALL | 1.0 | 1.0 | 1.0 |

## Proposals

| dataset | prompt | mode/model | n | action acc | params acc | schema-valid (1st try) | failure rate | mean attempts | tokens in/out | cost USD | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| default (seed 42) | v1 | mock/mock-clean | 120 | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | 50358/10824 (est.) | 0.0 | 0.07 / 0.12 |
| hard (seed 7) | v1 | mock/mock-clean | 120 | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | 50524/10836 (est.) | 0.0 | 0.06 / 0.09 |
| default (seed 42) | v2 | mock/mock-clean | 120 | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | 74501/10824 (est.) | 0.0 | 0.05 / 0.08 |
| hard (seed 7) | v2 | mock/mock-clean | 120 | 1.0 | 1.0 | 1.0 | 0.0 | 1.0 | 74676/10836 (est.) | 0.0 | 0.06 / 0.08 |

Regression cases saved this run: 0
