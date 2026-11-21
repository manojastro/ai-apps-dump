# AgentJudge run — stub (2026-09-19)

n=50 repeat=3 cost=$0.00

| metric | value |
|---|---|
| n | 50.000 |
| hit_rate_at_5 | 1.000 |
| recall_at_5 | 0.970 |
| mrr | 0.860 |
| context_precision | 1.000 |
| context_recall | 0.970 |
| faithfulness | 0.847 |
| judge_correctness_mean | 4.680 |
| refusal_accuracy | 1.000 |
| citation_validity | 1.000 |
| p50_latency_ms | 6.000 |
| p95_latency_ms | 8.000 |
| cost_usd | 0.000 |

Spread over 3 repeats (faithfulness min–max: 0.847–0.847). Small deltas (<0.02) are noise, not regressions.

## Worst 5 questions

- AQ-009 (answerable): judge=1/5 faithfulness=0.00
- AQ-018 (multi_hop): judge=1/5 faithfulness=0.00
- AQ-027 (answerable): judge=1/5 faithfulness=0.00
- AQ-045 (multi_hop): judge=1/5 faithfulness=0.00
- AQ-015 (conflicting): judge=5/5 faithfulness=0.33
