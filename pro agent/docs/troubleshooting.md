# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid configuration: ...` at startup | Settings validator rejected an incompatible combination | Read the listed problems; e.g. production needs `SESSION_SECRET` ≥ 32 chars, `CREDENTIALS_KEY`, `COOKIE_SECURE=true` |
| UI shows `Bad Gateway (HTTP_502)` on sign-in | API not running on 8300 | Start the API (`uv run uvicorn procnav.api.app:app --port 8300` in `backend/`) |
| Runs stay `queued` | No worker | Start `python -m procnav.workers.main`; dashboard shows worker health |
| Every supplier `unavailable` | Portals not running or origins mismatch | Start `python -m mockportals.main`; check `BROWSER_ALLOWED_ORIGINS` matches supplier `base_url` |
| `BLOCKED_NAVIGATION` steps | Page linked outside allowed origins (expected in the malicious scenario) | Add the origin only if it is a legitimate supplier/auth/asset origin |
| Browser scenario tests skipped | Portals not reachable at `127.0.0.1:8309/healthz` | Start the portals first |
| `run_lock_busy` in worker logs | Another worker holds the run (duplicate delivery) | Expected; the job is deferred and retried |
| Run `paused_for_human` with `authentication_required` | Supplier demands MFA | A person must resolve sign-in; the agent never bypasses MFA |
| Approval says "purchase changed since you reviewed it" | Fingerprint changed (fresh approval request exists) | Reload the inbox and review the new request |
| Order `unknown` | Submission timed out after a possible click | See runbook: reconcile from order history; never resubmit |
| `alembic revision --autogenerate` proposes dropping `checkpoint*` tables | LangGraph-owned tables | Already excluded in `alembic/env.py`; do not hand-edit them |
| Chromium fails in Docker with sandbox errors | Seccomp profile missing | Keep `security_opt: seccomp=./infra/docker/seccomp_profile.json`; do not add `--no-sandbox` |
| Real-model run fails with `ModelUnavailable` | API key, egress or rate limit | Check `MODEL_API_KEY`, use `docker-compose.real-model.yml` for egress, check budgets |
