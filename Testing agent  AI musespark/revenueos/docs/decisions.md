# Decisions

Each entry says what was chosen and why, in the form you would explain it in an interview.

## Core principle

**Models calculate, the LLM explains, every claim cites its source.** An LLM is good at reading a question and writing a clear answer. It is unreliable at arithmetic and can invent facts. So numbers come from models and SQL, the LLM can only reach them through tools, and code then checks its answer.

## Planted rules in the synthetic data

The generator is a small causal simulation. Hidden traits are drawn first, outcomes follow from them, and the observable trail is written to match. The exact values live in `PLANTED_RULES` in `backend/scripts/generate_synthetic_data.py`.

**Deal outcomes (new and expansion deals), as changes to the log-odds of winning:**

| Rule | Effect |
|---|---|
| Executive engaged | +1.30 |
| Deal goes dark (activity stops partway through) | -1.60 |
| Each stakeholder above two | +0.25 |
| Deal stalls | -0.70 |
| Severe support ticket during the deal | -0.60 |
| Expansion deal | +0.50 |
| Oversized compared with the account | -0.40 |
| Heavy discount above 25% | -0.25 |
| Discount otherwise | 0 (discounts do not help) |

**Churn at each renewal, as changes to the log-odds of leaving (base -3.0):**

| Signal, starting 75 to 150 days before renewal | Effect |
|---|---|
| Usage decline | +1.5 |
| Late payment | +1.4 |
| Ticket spike | +1.1 |
| Champion leaves | +0.9 |

Signals also occur on accounts that stay, so the model cannot treat any signal as certain.

**Realistic shape:** a few large accounts and many small ones (lognormal ARR), and half of deals close in the last fortnight of a quarter.

**Injected mess:** 6 duplicate accounts (about 3%), missing fields, 12 stale open deals, 11 impossible dates, 25 orphan rows, and 4 prompt-injection strings in tickets. `injected_issues.json` records exactly what was injected, so tests can prove the quality report finds all of it.

**What this means for the metrics.** The models are rediscovering rules I wrote. Good scores prove the pipeline works: no leakage, correct splits, reasons that match the data. They do not predict accuracy on real data, which is messier and has rules nobody knows.

**Simplification to know about.** Every account starts as a customer, so a `new` deal means new business with an existing account. Deal amounts are not linked to subscription MRR, except that renewal deals use the current contract value.

## Data and storage

- **Postgres with pgvector, not a separate vector database.** Relational data and search live together, so team scoping is one SQL join, and there is one system to run.
- **Upsert on source ids.** Re-running a load cannot duplicate rows.
- **Quarantine, do not drop.** Orphans go to `load_rejects`. A silent drop would hide a source-system problem.
- **Data quality runs on raw connector output.** Foreign keys would otherwise block orphans from ever being visible.
- **Empty cells are the only null.** Default pandas parsing read the region code "NA" as missing. A test now guards this.

## Machine learning

- **Point-in-time features.** Each training row is a deal or account as it looked on a past date. Tests delete all later data and assert the features do not change.
- **Time-based splits.** Random splits let a model learn from the future. Train is older, test is newer.
- **Purged churn split.** A churn label looks 90 days ahead, so training snapshots stop 90 days before the first test snapshot.
- **Model chosen on validation, never on test.** The test set is only reported. The final model is refit on all history.
- **Confidence intervals on AUC, clustered by entity.** Held-out sets are small and one deal appears in several snapshots.
- **SHAP for reasons, templates for words.** SHAP says what mattered. A template states it using the real value. If the template does not fit the value, the reason is skipped.
- **Model comparison includes logistic regression.** A simple model is the honest benchmark for a complex one. The planted rules are close to linear, so it is competitive.

## Forecast

- **Monte Carlo, not a single number.** A few large deals create real uncertainty, so a range is more honest.
- **Probability of landing = win probability x in-quarter rate.** A win next quarter does not help this quarter. The rate is learned per stage from history.
- **Walk-forward back-test.** Each past quarter uses a model trained only on what was known 14 days into it.
- **Error is measured on forecastable revenue.** Deals created and closed after the snapshot cannot be forecast from pipeline, so they are excluded from error and shown separately.
- **Variance items reconcile.** Each deal's change falls into exactly one category, and a test asserts they sum to the total.

## Copilot

- **Fixed read-only tools, no SQL tool.** A successful prompt injection has nothing dangerous to call.
- **Scope lives in the tools.** The model cannot widen access, whatever it is told.
- **Guardrails in code, not only in the prompt.** Citations and numbers are checked after the answer, with one repair attempt. Bad citations are removed, and unmatched numbers are flagged to the user.
- **Suspicious text is withheld before the model sees it.** Pattern matching cannot catch everything, so read-only tools remain the true safety boundary.
- **Manual tool loop, not the SDK tool runner.** Each call must be scoped, wrapped and recorded, and the final answer must pass checks.
- **Daily brief uses no LLM.** A scheduled list of facts should be free, repeatable and unable to hallucinate.
- **Claude Opus 5.5 by default, with server-side refusal fallback.** The model comes from `LLM_MODEL`. The fallback beta only applies to models that support it.
- **Local hashing embeddings.** Anthropic has no embeddings endpoint, and project rules avoid other paid APIs. It matches words, not meaning. `Embedder` is the swap point.
- **Exact vector search, no HNSW index.** An approximate index filters after searching, so a team-scoped user could silently lose matches, and it behaved badly with near-duplicate text in testing. An exact scan is fast at 7,000 rows. At much larger scale, use HNSW with pgvector iterative scans.

## Security

- **Scope object used by every read.** One place to enforce, one place to test.
- **Same 404 for missing and forbidden records.** A user cannot probe what exists.
- **Role and team read from the database, not the token.** A stale or tampered claim grants nothing.
- **httpOnly cookie through a same-origin proxy.** JavaScript cannot read the token. API clients may use a Bearer token.
- **Logs record ids and sizes, with a redacting formatter as backup.**
- **Patched framework versions.** The first pinned Next.js and React versions had known vulnerabilities, so they were upgraded before writing UI code.

## Environment

- **`pgserver` as a Docker-free fallback.** It runs a real PostgreSQL 16 with pgvector, so development and tests do not depend on Docker. It is a dev-only dependency.
- **Fixed `DATA_AS_OF`.** "Today" in the synthetic world is fixed, so results repeat.
