# ALL PROJECTS — master guide (P0–P6)

> 7 separate folders. Each runs on its own (stub mode if the others are off).
> Specs: `files/P0..P6 + 00-START-HERE.md`. All data synthetic (Acme Retail Ltd).

## 1. Separate folders — confirmed ✅

| # | Folder | Project | pyproject | README | CI | Docker |
|---|---|---|---|---|---|---|
| P0 | `ticketsort/` | Ticket triage API | ✅ | ✅ | ✅ | ✅ |
| P1 | `opscopilot/` | RAG over KEDB/SOPs | ✅ | ✅ | ✅ | ✅ |
| P2 | `agentjudge/` | Eval harness + CI gate | ✅ | ✅ | ✅ | ✅ |
| P3 | `mcp-ops-bridge/` | Mock ITSM + MCP server | ✅ | ✅ | ✅ | ✅ |
| P4 | `incident-commander/` | RCA agent + human approval | ✅ | ✅ | ✅ | ✅ |
| P5 | `ai-gateway/` | Secure gateway + cloud docs | ✅ | ✅ | ✅ | ✅ |
| P6 | `changeguard/` | Change-risk capstone | ✅ | ✅ | ✅ | ✅ |

Nothing is shared at import time. Cross-project calls are HTTP via `.env` URLs with stub fallback.

## 2. Measured status (mock provider, offline)

| Project | Tests | Reports (real, from repo) |
|---|---|---|
| ticketsort | 31 passed | `reports/eval_v1_2026-09-18.json` — cat 0.84, service 0.86, priority 0.34, injection 2/3, p95 0ms, $0 |
| opscopilot | 20 passed | `reports/smoke_20260918.json` — hit@5 1.0, refusal 0.933, citation 1.0 |
| agentjudge | 21 passed | `reports/run_stub_all_2026-09-19.json` — hit@5 1.0, faithfulness 0.847, kappa 0.455 |
| mcp-ops-bridge | 32 passed | 40 CIs / 200 incidents / 60 changes seeded; 9 tools; injection write blocked |
| incident-commander | 27 passed | `reports/eval_agent_vs_workflow.json` — agent RCA 1.00 vs workflow 0.40 |
| ai-gateway | 35 passed | `reports/redteam.json` — 14/20 blocked, 0 FP; KV 1 GiB math exact |
| changeguard | 25 passed | `reports/eval.json` — recall 0.806 vs baseline 0.389 |

## 3. What's DONE vs what's MISSING

DONE: code + tests green, ruff + mypy clean, Dockerfile + compose + CI, README/DEMO/LEARNING_LOG, eval reports on mock, git commits.

MISSING (do before calling it production / portfolio-final):
- [ ] Real LLM wiring: every repo runs on `mock` now. Add `LLM_API_KEY` + set `LLM_PROVIDER` and re-run evals for real numbers.
- [ ] Docker image builds never ran here (Docker daemon was off). Run `docker compose up --build` per repo once.
- [ ] Real Postgres/pgvector + Redis: P1/P3–P6 use SQLite/in-memory stubs. Compose files reference real services — verify against them.
- [ ] P1 PDFs: corpus is markdown (reportlab PDFs skipped). Add 2–10 real PDFs if you want the PDF-loader story.
- [ ] Langfuse tracing (P1/P4): code points exist, no live traces yet.
- [ ] Cloud deploy (P5): docs + scripts are skeletons with cost tables — nothing deployed, no vault secrets, no budget alert set.
- [ ] GitHub: repos are local-only. No remotes, no pushes, no live CI runs yet.
- [ ] P0 learner items: your 5 ticket templates (M3), prompt v2 tuned on a real LLM (M7), 15 INTERVIEW answers in your own words.

## 4. Prereqs (one time)

1. Git, Docker Desktop (start the daemon), `uv`, VS Code, Python 3.12+ (uv handles it).
2. GitHub account + SSH.
3. LLM key for the apps (OpenAI/Azure/Anthropic) OR Ollama local free. Set a spending limit. Coding-agent model (`/models` in OpenCode) is separate.
4. Ports free: see table below. If a port is busy, change `--port`.

## 5. Env vars (each repo has `.env.example` → copy to `.env`)

| Var | Used by | Example |
|---|---|---|
| `LLM_PROVIDER` | all | `mock` (now) → `openai` later |
| `LLM_API_KEY` | P0/P1/P4/P5/P6 via gateway | `sk-...` (never commit) |
| `LLM_MODEL` | all | `gpt-4o-mini` |
| `OPSCOPILOT_URL` | P2/P3/P4 | `http://localhost:8101` |
| `MOCK_ITSM_URL` | P3/P4/P6 | `http://localhost:8103` |
| `GATEWAY_URL` | P0/P1/P4/P6 | `http://localhost:8106` |
| `MAX_USD_PER_RUN` | eval scripts | `1.0` |

## 6. Run each locally (any order works — stubs cover missing services)

Suggested ports (defaults in code are all 8000 — override to run together):

| Project | Command | URL |
|---|---|---|
| P0 ticketsort | `cd ticketsort && uv sync --group dev && uv run uvicorn ticketsort.api.main:app --port 8000` | http://localhost:8000 |
| P1 opscopilot | `cd opscopilot && uv sync --group dev && uv run python scripts/generate_corpus.py && uv run uvicorn opscopilot.app:app --port 8101` | http://localhost:8101 |
| P2 agentjudge | `cd agentjudge && uv sync --group dev && uv run agentjudge run --target stub --set golden_set.jsonl --subset smoke` | CLI, no port |
| P3 mock-itsm | `cd mcp-ops-bridge && uv sync --group dev && uv run uvicorn mock_itsm.app:app --port 8103` | http://localhost:8103 |
| P3 ops-mcp | `uv run python -m ops_mcp.server --transport stdio` (or http `--port 8104`) | stdio / :8104 |
| P4 incident-commander | `cd incident-commander && uv sync --group dev && uv run uvicorn incident_commander.api:app --port 8105` | http://localhost:8105 |
| P5 ai-gateway | `cd ai-gateway && uv sync --group dev && uv run uvicorn gateway.app:app --port 8106` | http://localhost:8106 |
| P6 changeguard | `cd changeguard && uv sync --group dev && uv run python scripts/generate_history.py && uv run uvicorn changeguard.api:app --port 8107` | http://localhost:8107 |

Verify each: `uv run pytest -q`, `uv run ruff check src scripts tests`, `uv run mypy src`.

## 7. Deploy with Docker (per repo)

```powershell
cd ticketsort  # repeat per folder
docker compose up --build
# health: http://localhost:<port>/health
docker compose down
```

There is no single root compose — deploy order for a full stack: postgres/redis → P5 gateway → P1 + P3 → P0/P4/P6 → P2 gate. P5 `docs/deploy-azure.md` / `docs/deploy-aws.md` + `scripts/deploy/*` are the cloud path (skeletons — fill in resource names, vault secrets, budget alert, then `scripts/teardown*` to stop billing).

## 8. Push to GitHub (7 public repos)

```powershell
cd ticketsort  # repeat: opscopilot, agentjudge, mcp-ops-bridge, incident-commander, ai-gateway, changeguard
git status
gh repo create ticketsort --public --source=. --push
```

Then: update Career OS / Obsidian from each `LEARNING_LOG.md`, resume bullets only from `reports/` numbers.

## 9. Immediate next actions

1. `Docker Desktop` on → `docker compose up --build` in `ticketsort/`.
2. Choose LLM provider → `.env` keys → re-run `scripts/*eval*.py` per repo for real metrics.
3. `gh repo create` × 7 → watch CI (mock env) go green.
4. Start P1 detail study: `Read AGENTS.md, LEARNING_LOG.md` in `opscopilot/` and run `/recap`.
