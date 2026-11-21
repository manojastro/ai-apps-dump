# Evaluation

`app.evaluation` expands seven certified incident templates into eight deterministic signal/failure variants each: 56 replays. Every replay creates a clean database and sandbox, runs the actual LangGraph, auto-approves MEDIUM changes as a named benchmark operator, and measures its actual terminal records.

Metrics are diagnosis accuracy, approved runbook selection, risk classification, unsafe-action blocking, expected verified terminal recovery, rollback success, MTTR/runtime, approval rate by tier, committed duplicate action rate, and configured model cost per incident. Variant 8 forces verification failure for every reversible incident class, exercising compensating rollback. HIGH cases remain blocked.

Run:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation --output reports/evaluation.json --markdown reports/evaluation.md
```

The JSON contains every case and is the auditable source for the Markdown summary. Results depend on the current code and are never hardcoded in documentation. This benchmark proves deterministic POC behavior, not production diagnosis quality against real telemetry.

