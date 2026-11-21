# LEARNING_LOG — AgentJudge (P2 mock-first slice)

All data synthetic (Acme Retail Ltd). Mock-first: no API keys, $0 runs.

## M1 — Skeleton + target adapter — 2026-09-18
**Built:** `Target` protocol, `OpsCopilotTarget` (httpx), `StubTarget` (canned, deterministic misses), Typer CLI skeleton, pydantic-settings config.
**New concepts:** Protocol/adapter — one harness tests many systems by talking only to search()/ask().
**Learner tasks:** n/a (fast slice).
**Break-it result:** predicted stub returns 1.0 everywhere / actual ~0.9s (deterministic misses on every 7th/9th/5th record).
**Quiz:** n/a (fast slice).
**Open questions:** Real OpsCopilot response shape for `/v1/ask` (TargetAnswer fields may need mapping).
**Interview line I can now say:** "The runner never touches HTTP; it only calls search() and ask() on a Target protocol, so adding Incident Commander later is one new file."

## M2 — Golden set — 2026-09-18
**Built:** 50 frozen records (20 hand-written AQ-001..020 + 30 programmatic expansions), 15 smoke; `scripts/generate_golden.py`, `scripts/check_balance.py`, `tests/test_golden.py`, ADR-001.
**New concepts:** must-refuse rows stop the harness rewarding guesses; freezing the set keeps run comparison valid.
**Learner tasks:** 20 hand-written questions — attempts: 1 — hints used: 0.
**Break-it result:** predicted unanswerable rows score 0 retrieval / actual hit/recall treat empty-expected as 1.0 when nothing retrieved, refusal_accuracy carries the signal instead.
**Quiz:** n/a (fast slice).
**Open questions:** None.
**Interview line I can now say:** "Our 50-question set covers six categories including seven must-refuse rows, and it's frozen so every run compares against the same baseline."

## M3/M4 — Retrieval + generation metrics — 2026-09-18
**Built:** `metrics.py` (hit_rate@k, recall@k, MRR, context precision/recall, refusal accuracy, citation validity) + `gen_metrics.py` (keyword-overlap faithfulness) + tests + worked example in docs/.
**New concepts:** Faithfulness = grounded claims ÷ total claims; recall = of all docs that could fix this, how many did we find.
**Learner tasks:** n/a (fast slice).
**Break-it result:** predicted filler answers score 0 faithfulness / actual confirmed (≈0.0 vs reference context).
**Quiz:** n/a (fast slice).
**Open questions:** RAGAS/DeepEval integration deferred to the live-target slice.
**Interview line I can now say:** "Faithfulness is grounded claims over total claims — we walk one answer claim by claim in docs/faithfulness_example.md."

## M5 — Mock judge + calibration — 2026-09-18
**Built:** `docs/rubric.md` (1–5 correctness/completeness/safety), deterministic mock scorer, `cohens_kappa`, `labels/human_20.jsonl`, `calibrate` command + script.
**New concepts:** Kappa = agreement beyond lucky guessing; judges prefer long answers and their own model family, so we calibrate.
**Learner tasks:** rubric + 20 hand labels — attempts: 1 — hints used: 0.
**Break-it result:** predicted kappa ≈ 1.0 / actual high-0.8s (a few deliberate human/judge disagreements).
**Quiz:** n/a (fast slice).
**Open questions:** Real LLM judge calibration values will differ; re-run `calibrate` then.
**Interview line I can now say:** "We don't trust the judge blindly — we measured Cohen's kappa against 20 human labels."

## M6/M7/M8 — Reports, gate, variance — 2026-09-18
**Built:** JSON + Markdown reports, `compare`, `gate` (exit 1 on breach/regression), `--repeat 3` spread note, CI workflow gating full mock run vs baseline.
**New concepts:** A quality gate is a CAB check that runs itself; evals are noisy so tolerance + repeats separate signal from noise.
**Learner tasks:** `detect_regressions` — attempts: 1 — hints used: 0.
**Break-it result:** predicted degraded run fails gate / actual exit 1 confirmed in tests.
**Quiz:** n/a (fast slice).
**Open questions:** Thresholds are mock-baseline values; reset from a real baseline before enforcing on a live target.
**Interview line I can now say:** "The gate blocks releases when faithfulness or hit rate drops, the same way a change gate blocks a risky deployment."
