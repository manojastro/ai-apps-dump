# Enterprise Agentic AI Portfolio — Batch 2

Status tracking for the five Batch 2 projects. A row is marked complete only when the
feature has been executed and verified locally (tests green, demo run, docs present).

Environment: Windows 11, Python 3.11.15, SQLite persistence per project (POC),
LLM_MODE=mock by default. No cloud accounts, physical network gear, or paid APIs required.

| # | Project | Simulator | Backend | Agent Workflow | Validation | Evaluation | UI | Tests | Docker | Docs | Demo |
|---|---------|-----------|---------|----------------|------------|------------|----|-------|--------|------|------|
| 6 | Cloud Security Attack-Path Agent | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| 7 | Network Digital Twin Change Validation | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| 8 | MLOps Drift & Safe Retraining Agent | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| 9 | API/Microservice Change-Impact Agent | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| 10 | QE Release Confidence Agent | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |

Legend: `pending` -> `in-progress` -> `working` (executed and verified) -> `expanded`.

## Verification commands

Each project is independently runnable from its own folder:

```
python -m pytest -q
python scripts/<demo>.py
python -m uvicorn backend.app.main:app --reload --port <port>
# dashboard: http://127.0.0.1:<port>/dashboard
```

Demo ports: P6=8611, P7=8612, P8=8613, P9=8614, P10=8615.
