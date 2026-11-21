# Portfolio evidence

Measured on the local Windows development environment on 2026-09-06/07. These are project results, not enterprise impact estimates.

## Scripted benchmark

Both comparisons executed 48 cases after resuming from a recorded timeout. The controller retained already committed case results and executed the remaining lifecycle cases. These are deterministic plumbing tests on unreviewed synthetic fixtures.

| Candidate | Passed cases | Diagnosis accuracy | Paired regressions | Maximum case latency | Release |
|---|---:|---:|---:|---:|---|
| script-v1 | 48/48 | 16/16 | 0 | 12,523.74 ms | Fail: latency threshold exceeded |
| script-regression | 44/48 | 12/16 | 4 | 8,813.79 ms | Fail: diagnosis threshold and regression limit |

Both also lack reviewed cases and real-model evaluation evidence. See `evidence/script-v1-benchmark.json` and `evidence/script-regression-benchmark.json`. Scripted reasoning consumes zero model tokens; cost is not estimated.

A subsequent fresh browser-triggered regression benchmark completed all 48 cases without manual resumption. It reproduced 44 passing cases, 12/16 diagnosis accuracy and four regressions. Maximum latency was 10,693.62 ms, so it also failed the latency policy. Its full export is `evidence/evaluation-report.json`.

## Actual demo telemetry

Command: `uv run --locked python -m tests.demo_measurements`, with `python -m demo.cli up` already running. One warmed healthy sample had 40 requests. Each fault and subsequent reset sample had 35 requests. No container CPU limit was active in this Windows measurement.

| State | Errors / requests | p95 latency |
|---|---:|---:|
| Healthy baseline | 0/40 | 486.64 ms |
| Payment delay | 35/35 | 998.31 ms |
| Configuration regression | 35/35 | 97.22 ms |
| Pool exhaustion | 35/35 | 230.23 ms |
| CPU saturation | 4/35 | 3,284.20 ms |

Fast failures can lower response latency while making the service unusable. Reset samples are retained in `evidence/live-demo-measurements.json`; payment and configuration reset samples still had errors. Trace/span IDs were present in observed structured logs. An unauthorized control request returned 403.

## Workflow evidence

`evidence/incident-report.json` demonstrates a supported replay diagnosis and approved scripted recovery. API/workflow tests cover inconclusive evidence, rejection, tampered/expired approval, cross-run evidence scope and duplicate-action prevention. Screenshots document actual rendered pages. Final validation results are recorded in BUILD_STATUS.md.

## Résumé templates

- Built a local production investigation and evaluation platform with persisted tool activity, evidence-linked findings and hash-bound recovery approvals; validated **28 backend tests**.
- Implemented a **48-case scripted benchmark** that caught **four deliberate diagnosis regressions**; distinguished plumbing validation from unverified real-model quality.
- Instrumented three demo services and measured **320 requests** across the healthy baseline, four bounded faults and four reset samples; documented recovery limitations without fabricating business savings.

Do not replace unavailable live-model, deployment or business-impact measurements with invented numbers.
