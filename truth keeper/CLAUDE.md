# TruthKeeper

Cross-system reconciliation agent. It finds contradictions between a simulated CRM, billing system
and marketing tool, estimates money at risk, has an LLM explain each one and propose ONE allow-listed
fix, and applies a fix to sandbox data only after a human approves it.

## Commands
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # (Linux/mac: .venv/bin/pip)
python -m data.generator.generate --seed 42 --n 500      # synthetic data + ground truth
python -m app.cli seed                                   # data (if missing) + fresh sandbox copy
python -m app.cli run                                    # detect + propose (MOCK by default)
uvicorn app.api.main:create_app --factory --reload       # UI at http://localhost:8000
pytest -q                                                # all tests, offline, MOCK mode
ruff check .
python -m evals.run_all                                  # detection + proposal evals -> evals/results/
python -m evals.detection_eval --strategy name_only      # debugging exercise
```

## Layout
- `app/adapters/` one adapter per system -> `CustomerRecord`
- `app/core/` models, normalize, matcher, detector, impact, actions (allow-list), proposer, pipeline
- `app/llm/` `client.py` (ONLY place that calls an LLM; MOCK mode), `mock.py`, `prompts/explain_v*.md`
- `app/approval/` state DB + approval service, `app/audit/` append-only log, `app/applier/` sandbox applier
- `app/api/` FastAPI + Jinja UI · `app/tracing.py` OpenTelemetry -> Phoenix
- `data/generator/` generator + committed `ground_truth.json` · `data/generated/` originals (gitignored)
  · `data/sandbox/` the only data fixes may touch
- `evals/` detection/proposal evals, `run_all.py`, `regressions/` (replayed by tests), `results/`
- `docs/` decisions, architecture, deployment plan

## Hard rules
- No deployment, no git push, no real external API calls, no emails/SMS/calls, no paid services without
  explicit approval in chat.
- Synthetic data only (`.example` domains).
- Secrets only via env vars / `.env` (gitignored). Never print or commit keys.
- Every LLM call goes through `app/llm/client.py`. Tests must pass offline in MOCK mode.
- LLM output is parsed into Pydantic and validated; retried at most twice, then FAILED. Never silently accepted.
- Rules decide whether a conflict exists. The LLM never makes the final data-changing decision.
- Fixes only touch `data/sandbox/` copies. The audit log is append-only.
- Never invent metrics. Unmeasured = "not measured".
