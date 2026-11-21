# DEMO — 90 seconds, offline, no keys

## Setup (before the call)

```bash
uv sync --group dev
uv run python scripts/generate_corpus.py
uv run uvicorn opscopilot.app:app --port 8000
```

Open `http://localhost:8000`. (Backup: `uv run python scripts/smoke_eval.py` output.)

## Script

**0:00–0:15 — The problem.** "Service-desk engineers search the KEDB by keywords and
hope. OpsCopilot answers with citations to the exact article — or says it doesn't know."

**0:15–0:40 — Happy path.** Ask: *"Outlook keeps asking for password after MFA reset,
what is the fix?"* Point at the answer citing `[KB0001 §Workaround]`, click it —
`/v1/sources/KB0001` opens the full article. Toggle "show retrieval debug": keyword
and vector lists fused by RRF.

**0:40–1:00 — Exact code.** Ask: *"VPN fails with ERR_VPN_809 on home broadband."*
"Keyword search catches what vectors miss — that's why retrieval is hybrid."

**1:00–1:20 — Honest failure.** Ask: *"How do I bake sourdough bread on Mars?"*
"Best fused score 0.0164, below the 0.029 threshold — so it refuses instead of
inventing an answer." Then the conflict question (*"Shared mailbox sync is slow —
disable cached mode?"*): "Two articles disagree; it cites both instead of picking one."

**1:20–1:30 — Numbers.** "All figures from `reports/smoke_20260918.json`, produced by
`scripts/smoke_eval.py`: hit_rate@5 1.0, refusal accuracy 0.933, citation validity 1.0,
p95 40.17 ms — all offline on synthetic data."

## If something breaks live

Fall back to the report + `docs/rrf-worked-example.md` hand computation. Never improvise metrics.
