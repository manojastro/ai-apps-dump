# Sentinel — autonomous QA agent for Salesforce Lightning

> **Headline metrics (Phase 1):** Planner produces 8+ schema-valid cases per story (incl. 5 mandatory edges). Explorer/Verifier/Reporter/TestWriter + full eval numbers land in Phases 2–5 — see `docs/results.md`. No fake numbers are published.

Sentinel takes a plain-English user story, plans test cases, drives a real Salesforce Developer org in a browser (intent + accessibility roles, never hard-coded selectors), re-runs failures 3× to separate real bugs from flakes, files a reproducible Jira bug, and opens a PR with a permanent Playwright regression test.

The eval harness is the point: 40+ golden scenarios (pass / real bug / flaky / blocked) measuring precision, recall, false-alarm rate, cost, and prompt-injection resistance.

```
UserStory ──▶ Planner ──▶ TestCase[] ──▶ Explorer ──▶ RunTrace ──▶ Verifier ──▶ Verdict
                                                                    │ pass/flaky/blocked → stop
                                                                    ▼ real_bug
                                                              Reporter ──▶ Jira issue
                                                                  +
                                                              TestWriter ─▶ GitHub PR (Playwright test)
Guardrails (code-enforced): domain allowlist · production block · blocked-action deny list · TEST- disposable data + cleanup · budget kill switch · human reviews all issues/PRs
```

## Why deepeval (not promptfoo)

`promptfoo` is Node-first; Sentinel is Python-only (`uv`, Playwright-Python, LangGraph). `deepeval` is Python-native, runs under `pytest`, and ships LLM-as-judge scorers we reuse for the bug-report quality rubric (1–5 reproducibility). One stack, one install.

## 15-minute setup

1. `uv sync --group dev` + `uv run playwright install chromium`
2. Salesforce Dev org: `sf org login web --alias sentinel-dev` (browser MFA once — never automate the login form), then set `SALESFORCE_INSTANCE_URL` to the Dev URL.
3. Copy `.env.example` → `.env`, set `ANTHROPIC_API_KEY`, `SENTINEL_ALLOWED_DOMAINS`.
4. `make demo` (Phase 1: planner only) · `make test` · later: `make evals`, `make redteam`.

Auth detail tutorials get wrong: MFA means we never script username+password. We `sf org login web` once, extract access token + instance URL, inject into the Playwright context, refresh on expiry. Full steps land with Phase 2 in this README.

## Repo map

- `sentinel/models.py` — all Pydantic boundaries
- `sentinel/agents/planner.py` — story → test cases
- `evals/` — golden scenarios + red-team pages (Phase 5)
- `docs/architecture.md`, `docs/results.md` — why + numbers
