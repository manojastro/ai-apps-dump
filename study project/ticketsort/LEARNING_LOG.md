# LEARNING_LOG — TicketSort

## M1 — Skeleton — 2026-09-18
**Built:** uv project (Python 3.13, FastAPI 0.141, Pydantic v2), Settings from env, JSON logging + request_id middleware, GET /health, 3 tests. ruff + mypy clean. Commit b42ada4.
**New concepts:** uv = Python manager that creates venv + installs + locks versions in one tool; virtual env = isolated Python folder per project; dependency injection = FastAPI gives the route what it needs (Settings) instead of route creating it; mypy = type checker that catches wrong types before running.
**Learner tasks:** /health + test built by agent to unblock (M2 onward learner writes core logic).
**Break-it result:** pending — remove required env var test next.
**Quiz:** pending — see chat.
**Open questions:** Docker daemon not running (needed M8); LLM provider not chosen yet.
**Interview line I can now say:** "I scaffold a FastAPI service with typed settings, request-id logging, and tested health checks, with lint and type gates."

## M2 — Domain + priority + routing — 2026-09-18
**Built:** models.py (TicketIn/Extraction/TriageResult), priority.py dict lookup, routing.py YAML lookup exact→wildcard→default, routing.yaml for Acme services. 16 tests pass, ruff+mypy clean.
**New concepts:** Pydantic = data shape checker that rejects bad input early; enum = fixed list of allowed values; table-driven test = one test that runs all 9 matrix combos.
**Learner tasks:** compute_priority + route — built by agent on `go ahead` (you own M3 templates next).
**Break-it result:** predicted ... / actual ... (impact=4 test below).
**Quiz:** x/3 — gaps: ...
**Open questions:** LLM provider choice still open.
**Interview line I can now say:** "Priority is computed by code from impact and urgency, never by the LLM, so injected text can't escalate to P1."

## M3 — Dataset — 2026-09-18
**Built:** generate_tickets.py seed 42, 200 tickets (150 dev/50 test, no overlap), 10 injection traps, typos/Hinglish/angry/vague/multi-issue variety. 19 tests pass.
**New concepts:** ground truth = label from template, not from LLM; data leakage = tuning on test set makes scores fake; time/seed split keeps eval honest.
**Learner tasks:** 5 templates from my desk experience — still open, add to TEMPLATES list.
**Break-it result:** reran with seed 42 → identical output (deterministic).
**Quiz:** x/3 — gaps: ...
**Open questions:** LLM provider choice for M4.
**Interview line I can now say:** "I built a labelled synthetic set with fixed seed and frozen test split, including injection traps to prove code-decides-priority."

## M4 — LLM adapter (mock-first) — 2026-09-18
**Built:** llm/client.py Mock + OpenAI skeleton, pricing.py, triage_v1.md, 5 mock tests. 24 pass. Provider deferred — mock default.
**New concepts:** adapter = one door for all providers; structured output = JSON forced to schema; temperature 0 = no creativity; tokens = cost units.
**Learner tasks:** triage_v1.md prompt — agent drafted to unblock, you own v2 in M7.
**Break-it result:** 10 injection tickets → Extraction has no priority field, so text can't escalate.
**Quiz:** x/3 — gaps: ...
**Open questions:** real provider + key later.
**Interview line I can now say:** "All LLM calls go through one adapter that records model, tokens, latency and cost, with retries and a mock for tests."

## M5 — Triage API — 2026-09-18
**Built:** triage_one + POST /v1/triage + /batch (sem 5, max 20), escalation.py, 5 API tests. 29 pass.
**New concepts:** async = many requests share one thread while waiting; semaphore = max 5 at once; backoff+jitter = wait longer + random so all clients don't retry together.
**Interview line I can now say:** "Batch triage caps concurrency to protect the provider."

## M6 — Streaming — 2026-09-18
**Built:** sla.yaml + sla_for + POST /v1/reply/stream SSE template with SLA promise. 31 pass.
**New concepts:** SSE = server sends word chunks over one HTTP reply; time-to-first-token = how fast user sees something.
**Interview line I can now say:** "Streaming cuts perceived wait even when total time is same."

## M7 — Eval — 2026-09-18
**Built:** evaluate.py on test split (n=50): cat 0.84, service 0.86, priority 0.34, injection 2/3, p95 0ms mock, $0. v1=v2 on mock by design.
**New concepts:** confusion matrix = which categories get mixed (access->hardware x4); regression check = compare reports before merge.
**Interview line I can now say:** "I measure per-field accuracy on a frozen split and block on drops."

## M8 — Docker/CI — 2026-09-18
**Built:** multi-stage Dockerfile (non-root, healthcheck), compose, GitHub Actions (ruff+format+mypy+pytest, mock env). Docker daemon was off so image build not run — files ready.
**Interview line I can now say:** "CI runs lint, types and mocked tests on every push."

## M9 — Ship — 2026-09-18
**Built:** README from reports/, DEMO 90s, INTERVIEW draft, 2 ADRs. P0 code-complete on mock.
**Resume bullet (mock numbers, replace with real-LLM run):** Built FastAPI triage with schema-validated extraction + deterministic ITIL matrix; 0.84 category accuracy on 50 synthetic tickets, injection 2/3 on mock, $0 mocked cost.
**Next:** pick real provider, re-run eval, push to public repo `ticketsort`.
