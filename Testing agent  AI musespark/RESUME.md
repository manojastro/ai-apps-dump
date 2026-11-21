# Sentinel — Resume File (state as of 2026-09-05)

Read this first in a new session. Everything below is verified fact, not aspiration.

## 1. One-line status

All offline-buildable code is written and proven: **81/81 pytest green**.
Every phase acceptance that needs live services is blocked on user-supplied
credentials — nothing further can be built without violating the project's
no-unverifiable-code rule.

## 2. How to resume

```powershell
cd "D:\ai apps dump\Testing agent  AI musespark"
uv sync --group dev          # deps (Python 3.11, uv)
uv run playwright install chromium --only-shell   # already done once; re-run if browsers missing
uv run pytest -q             # expect: 81 passed
```

Then work the blocker list in section 4, top to bottom.

## 3. Phase status

| Phase | Code | Tests | Acceptance | Blocker |
|---|---|---|---|---|
| 1 Planner | done | 15 green | NOT run live | `ANTHROPIC_API_KEY` |
| 2 Explorer groundwork (session, a11y, intent steps, policy) | done | 22 green (session 6, browser 9, redteam-policy 7 overlap) | NOT run live | key + `sf` login + Dev org URL |
| 2 Explorer orchestration (`run_test_case` LLM loop) | NOT written (stub raises) | — | — | key + org (must be built against live Lightning) |
| 3 Verifier / Reporter / Jira client | done | 27 green (verifier 11, reporter 8, jira 8) | NOT run live | Jira instance + Phase-2 runner |
| 4 Test renderer / GitHub client | done | 11 green (testwriter 7, github 4) | NOT run live | key (prose→actions) + repo token |
| 5 Metrics / runner / red-team fixtures | done | 13 green (evals 6, redteam 7) | NOT run live | all of the above; dataset has 4 placeholder scenarios, needs 40 |

## 4. Blockers — exact credentials needed (`.env`; see `.env.example`)

1. `ANTHROPIC_API_KEY` (+ `ANTHROPIC_MODEL`, default `claude-sonnet-4-5-20250929`)
2. Salesforce CLI on PATH + `sf org login web --alias sentinel-dev`, then `SALESFORCE_INSTANCE_URL`
3. `SENTINEL_ALLOWED_DOMAINS` (Dev org host)
4. Later: `JIRA_URL/JIRA_USER/JIRA_API_TOKEN`, `GITHUB_TOKEN/GITHUB_REPO`

## 5. Next coding steps, in order (start here when keys arrive)

1. `make demo` → confirm Phase 1 live (3 stories × 8+ valid cases). Paste sample output.
2. Write `explorer.run_test_case` LLM loop (snapshot → intent → `execute_intent_step` → `RunTrace`) against the live org: Lead → Opportunity → Closed Won, zero selectors.
3. Wire full LangGraph path in `sentinel/graph.py` (explorer/verifier/reporter/testwriter nodes still raise).
4. Live Phase 3 proof (broken flow files one bug; flaky files none) + `reporter.report`/`jira.file_issue` delivery.
5. Prose→`RecordedAction` translation + `testwriter.write_regression_test` + live PR.
6. Expand `evals/scenarios.yaml` to 40 against the real org config, add deepeval judge scorer, run `make evals` + `make redteam`, write real numbers into `docs/results.md`.

## 6. File inventory (repo root: `D:\ai apps dump\Testing agent  AI musespark`)

Implemented + tested: `sentinel/models.py` (incl. `RecordedAction`), `sentinel/config.py`,
`sentinel/graph.py` (planner-only), `sentinel/agents/planner.py`, `verifier.py`, `reporter.py`
(+`deliver`), `explorer.py` (`execute_intent_step` only), `testwriter.py` (`render_regression_test` only),
`sentinel/browser/session.py`, `accessibility.py` (CDP AX tree), `policy.py`, `guardrails.py` (re-exports),
`sentinel/integrations/jira.py`, `github.py`, `evals/metrics.py`, `evals/run_evals.py`
(`run_golden` + `main` prereq gate), 4 red-team pages in `evals/redteam/injection_pages/`,
`sentinel/demo_planner.py`, `Makefile`, `docker-compose.yml`.

Live-only stubs (raise `NotImplementedError` by design): `explorer.run_test_case`,
`reporter.report`, `jira.file_issue`, `testwriter.write_regression_test`, `github.open_pr`,
`integrations/slack.notify`, `run_evals` live agent path.

## 7. Hard-won decisions (do not re-litigate without new evidence)

- `deepeval` over `promptfoo` (Python-native, pytest-integrated, built-in LLM-judge).
- `pyproject.toml` pins `-p no:deepeval`: its pytest plugin hangs at startup (bisected).
  Phase 5 calls deepeval programmatically.
- A11y snapshot via CDP `Accessibility.getFullAXTree` (`page.accessibility` does not exist
  in Python Playwright); ignored/hidden nodes skipped in agent view.
- Injection screening uses `textContent`, not `innerText` (hidden bait is invisible to the latter).
- Generated regression scripts are ASCII-only (em-dashes broke execution on cp1252 locales).
- `verifier`: mixed env+product failures → `blocked` ("refusing to file"); runner crash = env failure.
- `verify()`/`run_golden()` take injectable callables — that is the offline-test seam, not a stub.
- New deps need user approval: Jira/GitHub clients are stdlib `urllib`; PyYAML is used only via
  the deepeval transitive install with an explicit error if absent.
- `python_classes = ["Test_*"]` so the imported Pydantic `TestCase` isn't collected as a test.

## 8. Known weak spots (admitted, for future work)

- Planner coverage gates match signal phrases — gameable; real quality gate is the Phase-5 judge rubric.
- Duplicate-detection threshold (0.5) untuned — needs real Jira data.
- Renderer knows 4 action kinds (click/fill/expect_title/expect_text) — no picklists/lookups yet.
- Injection screen is a phrase blocklist — catches known wording, not novel paraphrase.
- Browser tests are slow (~45–70s for Chromium suites); full suite ~50s.
