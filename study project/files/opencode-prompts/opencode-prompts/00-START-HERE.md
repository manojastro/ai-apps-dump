# START HERE — AI Career OS Learning Builds (OpenCode)

## What's in this pack

| File | What it is |
|---|---|
| `AGENTS.md` | Shared "teaching mode" rules. Copy into the root of EVERY project repo. |
| `.opencode/commands/*.md` | Slash commands (`/checkpoint`, `/explain`, `/quiz`, `/breakit`, `/interview`, `/recap`). Copy the folder into every repo. |
| `P0-ticketsort.md` | Step 0 — L1 ticket triage API (Python, FastAPI, LLM APIs) |
| `P1-opscopilot.md` | Step 1 — RAG over KEDB/SOPs (RAG, pgvector, LangChain, hybrid search) |
| `P2-agentjudge.md` | Step 2 — Eval harness + CI gate (evals, RAGAS, LLM-as-judge) |
| `P3-mcp-ops-bridge.md` | Step 3 — MCP server + mock ITSM API (MCP, JSON-RPC, tool safety) |
| `P4-incident-commander.md` | Step 4 — LangGraph agent with human approval (agents, HITL, observability) |
| `P5-ai-gateway.md` | Step 5 — Secure AI gateway + cloud deploy (guardrails, cost, security, cloud) |
| `P6-changeguard.md` | Step 6 — Capstone: change-risk investigator (everything combined) |

## The shared world (same in every project)

All projects use one fictional company so the pieces fit together:

- **Company:** Acme Retail Ltd (fictional, synthetic data only)
- **Services:** `email`, `vpn`, `sso`, `payroll-app`, `pos-api`, `orders-db`, `network-core`
- **Assignment groups:** `SD-L1`, `EUC`, `Network-Ops`, `DB-Ops`, `App-Support`, `IAM`, `Security-Ops`
- **Repos (one public GitHub repo each):** `ticketsort`, `opscopilot`, `agentjudge`, `mcp-ops-bridge`, `incident-commander`, `ai-gateway`, `changeguard`

Each repo runs **on its own**. When a project needs an earlier one, it calls it over HTTP using a URL from `.env`, and it has a **stub mode** so it still works if the other service isn't running.

## Ownership grows project by project

| Project | You write | Agent writes |
|---|---|---|
| P0 | ~25% (core logic) | ~75% |
| P1 | ~35% | ~65% |
| P2 | ~45% | ~55% |
| P3 | ~50% | ~50% |
| P4 | ~55% | ~45% |
| P5 | ~60% | ~40% |
| P6 | ~70% (agent mostly plans and reviews) | ~30% |

This is on purpose. By P6 you should be driving and the agent just helps.

## One-time setup (do this before P0)

1. Install: **Git**, **Docker Desktop**, **uv** (Python manager), **OpenCode**, a code editor (VS Code).
2. Create a **GitHub** account (if needed) and set up SSH keys.
3. Pick an LLM provider for development and get an API key. Options: OpenAI, Azure OpenAI, Anthropic, or **Ollama** (free, runs locally, weaker at strict JSON). A cheap hosted model is best for learning structured output. Set a **spending limit** on the provider dashboard.
4. In OpenCode, run `/models` and pick the model you want the *coding agent* to use. (This is separate from the LLM your *app* calls.)

## How to run each project

```bash
mkdir ticketsort && cd ticketsort
git init
cp /path/to/pack/AGENTS.md .
cp -r /path/to/pack/.opencode .
opencode
```

Inside OpenCode:

1. Press **Tab** to switch to the **plan** agent (it reads and plans but doesn't edit files).
2. Paste the WHOLE project prompt (e.g. `P0-ticketsort.md`). Or type: `Read P0-ticketsort.md and follow it` after copying the file into the repo.
3. Answer its setup questions. Check the plan it gives you.
4. Press **Tab** again to switch to the **build** agent. Type `go`.
5. Work milestone by milestone. Use `/checkpoint` at the end of each milestone.

**Tip:** Start each new day with a new session and type: `Read AGENTS.md, LEARNING_LOG.md and the project prompt. Tell me where we are and what's next.` The log is your memory between sessions.

## Realistic timeline

About 20 weeks at 12–15 hours/week for P0–P5, then P6. This is a guess — your speed will set the real number. Going slower and understanding everything beats going fast and understanding nothing. Interviews test the understanding.

## After each project

- Push to a **public** GitHub repo with a clean README.
- Update the Career OS app: project status, skills moved to "Project Applied", new STAR story.
- Add the `/recap` output to Obsidian.
- Write the resume bullet **only** from numbers in `reports/`.
