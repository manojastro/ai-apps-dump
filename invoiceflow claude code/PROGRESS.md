# Progress

One report per phase, newest first, in the format from [CLAUDE.md](CLAUDE.md). Status words follow the fixed ladder: *planned → implemented → unit-tested → integration-tested (local) → tested on Databricks → deployed (Azure) → verified end-to-end*.

## Databricks workspace run — 2026-10-25

Run at Manoj's request: "Run the Databricks setup, parity check and AI Search index on my
workspace, then a full live eval." Free Edition; nothing paid was created.

**Status:**

| Component | Status |
|---|---|
| Unity Catalog tables, volume and governed functions | tested on Databricks |
| Databricks data reader (bulk snapshot; per-record sample) | tested on Databricks (parity: 0 mismatches) |
| AI Search endpoint and Delta Sync index | tested on Databricks |
| Agent end to end on the Databricks backend (UC data, AI Search, serving endpoint) | tested on Databricks (graph run from a laptop, not as a job) |

**What I did:**

1. Discovered the config myself: SQL warehouse `Serverless Starter Warehouse` (2X-Small),
   catalog `workspace` (the only one Free Edition has), no existing AI Search endpoint.
2. Created schemas `workspace.invoiceflow_ap` / `workspace.invoiceflow_eval`, the 8 tables,
   the 6 masked read-only functions, the AI Search endpoint `invoiceflow-search`, and the
   index `workspace.invoiceflow_ap.policy_index` (embeddings `databricks-gte-large-en`).
3. Ran parity and the retrieval eval, then the agent over the whole dev split.

**Evidence:**

- [docs/evidence/databricks/parity-2026-10-25.log](docs/evidence/databricks/parity-2026-10-25.log)
- [docs/RETRIEVAL_REPORT_AISEARCH.md](docs/RETRIEVAL_REPORT_AISEARCH.md)
- [docs/EVAL_REPORT_LIVE_FULL.md](docs/EVAL_REPORT_LIVE_FULL.md) and
  `docs/evidence/eval/agent-dev-live-databricks-full-2026-10-25.json`
- 1,414 recorded model responses for replay:
  `docs/evidence/eval/recordings-full-dev-2026-10-25.jsonl.gz`

**Measured results** (2026-10-25):

- **Setup:** `uv run invoiceflow databricks setup` in 89 s. The governed `get_vendor('V001')`
  returns `XXXXXXXX5846` (masked).
- **Parity:** `uv run invoiceflow databricks parity` found **0 mismatches** over 30 vendors,
  200 POs, 276 goods receipts, 325 invoices and 325 labels (field by field), plus a
  10-invoice per-record sample with prior-invoice queries. Took 106 s.
- **AI Search retrieval** (`uv run invoiceflow retrieval eval --backend databricks`, 31
  questions): recall@1 / @3 / @5 = **0.929 / 1.000 / 1.000** (local retriever: 0.857 /
  0.964 / 0.964). Access-control violations **0**. Off-topic abstention **0 / 2** (no score
  threshold).
- **Full live eval**, all 196 dev invoices on the Databricks backend
  (`INVOICEFLOW_BACKEND=databricks uv run invoiceflow eval agent --split dev --provider databricks`):

  | Metric | Agent (`databricks-gpt-oss-120b`) | Rule-only baseline |
  |---|---|---|
  | Exception | 196 / 196 | 194 / 196 |
  | Action | 196 / 196 | 190 / 196 |
  | Required approver | 196 / 196 | 194 / 196 |
  | Unsafe outcomes | 0 | 2 |
  | Adversarial invoices with no unsafe outcome | 16 / 16 | 14 / 16 |
  | Executed policy violations | 0 | n/a |
  | Proposals stopped by validation or policy | 0 | 0 |
  | Manual-queue fallbacks | 0 | n/a |
  | Citations relevant to the expected exception | 164 / 196 (83.7%) | n/a |
  | Latency p50 / p95 | 15.0 s / 21.8 s | n/a |
  | Tokens in / out | 3,144,692 / 341,481 | n/a |
  | Tool calls / tool errors | 1,059 / 7 | n/a |

  Wall clock was 2,906 s (48 min). Cost is not priced: Free Edition, with no price
  configured.

**How to read the perfect scores:**

- **The exception is mostly decided by deterministic code.** The model may only escalate,
  so 196 / 196 on exceptions reflects the matcher, the text screen and the validators as
  much as the model.
- **What the model demonstrably added:** contract-authorized price increases routed to the
  buyer (the stub and the baseline ask for credit notes), 0 unsafe proposals on 16
  adversarial invoices, and better citations (83.7% vs the stub's 60.2%).
- **The two hidden bank changes** are also caught by the deterministic regex screen.
- **The data is synthetic, and labels follow the same written rules as the checks.** These
  results show the system does what the spec says on that data, not how it would do on real
  invoices.
- **This is one run** on 196 invoices, with no repeat runs to measure variance. The held-out
  split has not been run live.
- The report's "uncommitted changes" flag comes from the run's own recording file, which
  was being written while the run was in progress.

**CI:** GitHub Actions run
[40176340860](https://github.com/manojastro/invoiceflow/actions/runs/40176340860) at commit
`8386fbc` passed all four jobs: checks, OPA, the secret scan, and Postgres integration
(5 passed in a `pgvector/pgvector:0.8.7-pg17` service container). The Phase 1 Postgres
backend is therefore integration-tested in CI, though not on this laptop.

**What is NOT done:**

- The graph has not run as a Databricks job or endpoint.
- No live run on the held-out split.
- No AI Search score threshold.
- The embedding model was not compared.
- Phase 7 is not started.

**Decisions made:**

- Batch reads use a bulk `Snapshot` (8 statements), because per-record reads take about 5 s
  each on Free Edition.
- AI Search goes through the Databricks SDK, so the CLI login is used and no token was
  created.
- Recordings are stored gzip-compressed (`.jsonl.gz`); replay reads them.

## Phases 2–6 — Databricks layer, retrieval, agent, evaluation, enterprise controls — 2026-10-25

Built in one pass at Manoj's request: "skip Postgres for now ... complete code ...
deployment later ... don't ask for permission ... upload to GitHub". Phase 7 (Azure
deployment) is not started. The Phase 1 Postgres integration tests now run in CI instead.

**Status:**

| Component | Status |
|---|---|
| Databricks reader, UC setup (tables from a volume), governed UC functions | implemented; tested against a SQLite stand-in. **Not run on the workspace.** |
| Retrieval: section chunking, scoped hybrid search, abstention | unit-tested (local) |
| AI Search adapter and index setup | implemented; tested with a fake index. **Not run on the workspace.** |
| LLM adapters: stub, record/replay, OpenAI-compatible | unit-tested; **Databricks endpoint called live** (`databricks-gpt-oss-120b`) |
| Agent graph: tools, budgets, validators, policy, interrupt/resume, executor | unit-tested; resume proven across two processes |
| SIMULATED ERP: idempotency, outbox, HTTP retries | unit-tested |
| Audit hash chain, evidence packs, email drafts | unit-tested |
| Approval service: dev tokens (v1), Entra ID OIDC (v2) | unit-tested; no Entra tenant |
| Policy v2: OPA/Rego | unit-tested (`opa test`); 6,496-case parity with Python |
| Eval harness, reports, CI gate | implemented; gate passing locally |
| GitHub Actions CI | implemented; pushed (result: see the CI section below) |
| Threat model, Entra setup steps, ADRs 0004–0011, case study, interview notes | written; **not yet reviewed by Manoj** |

**What I built:**

- **The full agent.** A LangGraph state machine that investigates an exception invoice
  with read-only tools and retrieves the policy and the vendor's own contract. It proposes a
  resolution as JSON. Deterministic validators and a policy engine decide whether it may
  run, and a human approves through a durable pause. Only an executor writes to a
  simulated ERP, with idempotency keys. Every step goes into a hash-chained audit log and
  an evidence pack.
- **The Databricks pieces.** They are wired behind the same ports.
- **An evaluation harness** that compares the agent with the rule-only baseline.
- **An OPA version of the policy,** proven equal to the Python one.
- **CI** that runs all of this on every push.

**How to run it:** see the README ("Run it locally", "Run with Databricks").

**Evidence:**

- [docs/evidence/phase-6/acceptance-2026-10-25.log](docs/evidence/phase-6/acceptance-2026-10-25.log)
- [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md) (stub, dev),
  [docs/EVAL_REPORT_HELDOUT.md](docs/EVAL_REPORT_HELDOUT.md) (stub, held-out),
  [docs/EVAL_REPORT_LIVE.md](docs/EVAL_REPORT_LIVE.md) (live model, subset),
  [docs/RETRIEVAL_REPORT.md](docs/RETRIEVAL_REPORT.md)
- Recorded live-model responses for replay:
  `docs/evidence/eval/recordings-gpt-oss-120b-2026-10-25.jsonl`

**Measured results** (all 2026-10-25):

- **Tests.** `uv run pytest` with the coverage gate: **315 passed**, 5 deselected (Postgres
  integration, which runs in CI). Coverage of `core` + `policy`: **97.24%** (the OPA client
  now counts toward `policy`).
- **OPA.** `opa test` passes. Python/OPA parity holds on **6,496 / 6,496** generated cases.
- **Retrieval** (`uv run invoiceflow retrieval eval`, 31 questions): recall@1 / @3 / @5 =
  **0.857 / 0.964 / 0.964**. Off-topic abstention 2 / 2; access-control violations 0.
- **Agent with the deterministic stub model** (measures the harness and the regex screen,
  not an LLM):

  | Split | Invoices | Exception | Action | Approver | Unsafe | Executed violations |
  |---|---|---|---|---|---|---|
  | dev | 196 | 100.0% | 98.0% | 100.0% | 0 | 0 |
  | held-out | 129 | 100.0% | 96.9% | 100.0% | 0 | 0 |
  | baseline, dev | 196 | 99.0% | 96.9% | 99.0% | 2 | n/a |

  The stub's remaining action errors are the contract-authorized price escalations (a
  credit note instead of routing to the buyer). Its citation relevance is 60.2% on dev.
  The 2 unsafe outcomes the baseline has and the stub agent doesn't (hidden bank changes)
  are caught by the **deterministic text screen**, not by a model.
- **Agent with a live Databricks model** (`databricks-gpt-oss-120b`, from a laptop) on a
  **targeted subset** of 22 dev invoices: all 16 adversarial ones plus the 6
  contract-escalation cases.

  | Metric | Result |
  |---|---|
  | Exception | 22 / 22 |
  | Action | 22 / 22, including **4 / 4 escalation-authorized prices routed to the buyer**, which the stub and the baseline get wrong |
  | Approver | 22 / 22 |
  | Unsafe outcomes | 0 |
  | Executed violations | 0 |
  | Relevant citations | 19 / 22 |
  | Latency p50 / p95 | 20.7 s / 30.3 s |
  | Tokens in / out | 430,376 / 50,790 |
  | Cost | not priced (Free Edition; no price configured) |

  This is a subset chosen for difficulty, not the full split; a full live run is not done.
- **CI.** The first run on GitHub failed at setup in every job: `astral-sh/setup-uv@v10` is
  not a published tag. Fixed by pinning exact versions; the result of the re-run is in the
  CI section below.

**What is NOT done / known limitations:** see [docs/LIMITATIONS.md](docs/LIMITATIONS.md). The
main items:

- The Databricks setup, parity and index commands have not run on the workspace.
- No full live-model eval; only the subset.
- No Entra tenant is configured.
- Phase 7 is not started.
- Approved interpretation 9 still awaits confirmation.

**Risks and failure modes found:** [docs/CASE_STUDY.md](docs/CASE_STUDY.md). The serious
ones:

- A default action that would have executed a hold without approval (caught by an
  end-to-end test).
- An abstention rule that answered off-topic questions (fixed, at the cost of one valid
  answer).
- A CLEAN fast path that never ran.

**Decisions made:** ADRs [0004](docs/adr/0004-databricks-vs-snowflake.md)–[0011](docs/adr/0011-policy-python-and-opa.md).
Small deviations from the spec:

- CLEAN invoices with vendor text are investigated rather than going straight to policy,
  because the hidden bank changes are CLEAN on structured data.
- A deterministic remittance screen backs up the LLM. Its effect is reported separately.

**What Manoj should understand before deployment:**

1. **Escalate, never downgrade.** The model may only make a case *more* cautious. That one
   rule turns prompt injection from "approve this" into, at worst, a case in the manual queue.
2. **Nodes re-run on resume.** That is why the approval node holds nothing but `interrupt()`
   and every side effect is idempotent.
3. **Idempotency keys come from the case, the action and the policy version.** Retries and
   duplicate deliveries can't pay twice; a changed payload under the same key is a conflict.
4. **The stub measures the harness; the live model measures judgment.** Read the two eval
   reports with that in mind, and note which wins came from the regex screen.
5. **Two policy engines, one truth.** The parity test is what makes keeping both safe.

**Next phase plan (Phase 7, needs approval to spend):**

- Run the Databricks setup, parity and index commands on the workspace.
- Run the full live eval and choose the default model.
- Write the IaC for Azure Container Apps and Key Vault, with a cost estimate first.
- Set up OIDC deploys and create the Entra app registration (with approval).
- Run load and failure tests.

## Phase 1 — Synthetic data + deterministic core — 2026-10-25

**Status:**

| Component | Status |
|---|---|
| Synthetic data generator, documents and samples | unit-tested |
| Deterministic core (matcher, tolerance, GSTIN, GST, duplicates) | unit-tested |
| Policy engine v1 (control matrix + evaluator) | unit-tested |
| Read-only data port + in-memory adapter | unit-tested |
| Local Postgres backend, loader and reader | implemented. Integration tests are written but **not yet run**: Docker Desktop was not running. |
| Rule-only baseline, scorers and report | unit-tested; dev-split run recorded |

**What I built:**

- **A generator** that writes a fake but realistic Accounts Payable world from one seed:
  30 vendors, 200 POs, 276 goods receipts, 325 invoices, 6 contracts, an AP policy manual
  and a GST guide. Each invoice is built on purpose to show one problem (or none), and its
  label records that intent.
- **A deterministic engine** that checks an invoice against its PO, receipts and vendor:
  price tolerance, quantities, missing receipts, duplicates, PO status, GSTIN check
  character, tax type and rate, and bank details.
- **A policy engine** that reads the control matrix and says ALLOW, REQUIRE_APPROVAL or
  DENY, and why.
- **A rule-only baseline** that runs the engine and the policy over the dev invoices and
  writes a report.
- **A local Postgres backend** in Docker, with a loader.

None of it uses an LLM.

**How to run it:**

```bash
uv sync
uv run invoiceflow data generate
uv run pytest
uv run pytest --cov=invoiceflow.core --cov=invoiceflow.policy --cov-fail-under=90
uv run invoiceflow baseline
docker compose up -d --wait        # needs .env with POSTGRES_PASSWORD
uv run invoiceflow data load
uv run pytest -m integration
```

**Evidence:**

- [docs/evidence/phase-1/acceptance-2026-10-25.log](docs/evidence/phase-1/acceptance-2026-10-25.log),
  run at commit `f62cf05` on a clean tree: lint, format, mypy, tests, the coverage gate,
  dataset generation, the baseline, refusal of the eval split, every pre-commit hook, and
  8 mutation checks.
- [docs/BASELINE_REPORT.md](docs/BASELINE_REPORT.md) and its JSON evidence, generated at
  commit `81750ee` (clean).
- [docs/evidence/phase-1/label-handcheck-2026-10-25.md](docs/evidence/phase-1/label-handcheck-2026-10-25.md).

**Measured results** (all 2026-10-25):

- `uv run pytest`: **246 passed**, 5 deselected (the integration tests, which need Docker).
- Coverage gate (`--cov=invoiceflow.core --cov=invoiceflow.policy --cov-fail-under=90`):
  **98.18%**.
- Mutation checks: **8 of 8 deliberate bugs caught** by the tests. The bugs were: the GSTIN
  modulo, the inclusive ₹5,000 limit, the inclusive 7-day window, the PO validity date, the
  bank-change check, segregation of duties, the tolerance check on APPROVE, and who may
  approve.
- `uv run invoiceflow data generate`: dataset `d82a2336ce47af65`, 196 dev / 129 eval
  invoices (16 adversarial in dev).
- `uv run invoiceflow baseline --split dev` (memory backend, 196 invoices):

  | Metric | Result |
  |---|---|
  | Exception classification | 194/196 (99.0%) |
  | Action | 190/196 (96.9%) |
  | Required approver | 194/196 (99.0%) |
  | All three correct | 190/196 (96.9%) |
  | Policy denials | 0 |
  | Unsafe outcomes on adversarial invoices | 2 of 16 |

  Every error falls in two scenarios designed to need knowledge the rules don't have:
  `adv_hidden_bank_change` (2) and `price_escalation_within` (4).
- Label hand-check: 20 of 20 dev labels agree with the policy manual.
- Postgres load idempotency and parity with the in-memory reader: `[NOT YET MEASURED]`.

**What is NOT done / known limitations:**

- **The Postgres integration tests have not run.** Docker Desktop could not be started from
  this session, so the Postgres backend stays at "implemented". Phase 1 acceptance is
  complete only once `uv run pytest -m integration` passes.
- **Interpretation 9 deviates from the approved text.** The approved near-duplicate rule
  was redundant, so the code follows the spec's wording ("different number format").
  Details are in [CONTROL_MATRIX.md](docs/CONTROL_MATRIX.md). Needs your confirmation.
- **Tests first was followed for `core` but not fully for `policy`.** The policy evaluator
  was drafted just before its tests (both before any commit), a slip against rule 7. I also
  couldn't show the "red" run, because the command-safety check was failing at the time.
  The 8 mutation checks are the evidence that the tests catch real bugs.
- **The held-out split was looked at once.** While building the generator, I ran a
  whole-dataset matcher-vs-label check that included it. Nothing was changed as a result;
  see [DATASET.md](docs/DATASET.md).
- **The baseline's high scores are optimistic by construction.** Labels and matcher follow
  the same written rules on clean synthetic data.
- **Data-model limits:** one invoice per PO line (no cumulative billing), invoice numbers
  with glued digit groups are not normalized, GST rates are illustrative, and a genuine
  repeat order inside 7 days would be flagged.
- **The control-matrix path is resolved from the source tree.** That works for this
  editable install. It needs packaging as a resource before Databricks uses it (Phase 2).

**Risks and failure modes found:**

- **A generator bug is a label bug.** Mitigated by intent checks inside the generator
  (it refuses to finish if a price change lands on the wrong side of tolerance), invariant
  tests, the hand-check, and listing every matcher/label disagreement as "unexpected".
- **A misreading of the spec shared by the labels and the matcher is invisible to the
  baseline.** Mitigated only by writing every interpretation down for your review.
- **Exact-value boundaries** (gross exactly ₹1,00,000.00) cannot always be hit with one
  line, because tax rounding skips some values. The first fallback still failed: whole-rupee
  second lines keep the same rounding pattern. Found and fixed during generation.
- **Faker upgrades** would change the data. The version is pinned and recorded, and a drift
  test protects the committed contracts and samples.

**Decisions made:** [ADR 0002](docs/adr/0002-ports-and-adapters.md) (ports and adapters),
[ADR 0003](docs/adr/0003-local-backend-postgres.md) (Postgres + pgvector),
[CONTROL_MATRIX.md](docs/CONTROL_MATRIX.md) (interpretations). Added `pydantic-settings`,
which was not in the plan, to read `.env`.

**What Manoj should understand before the next phase:**

1. **Labels come from intent, not from the matcher.** The generator decides "this invoice is
   overpriced by 5%" and builds it that way. If the matcher wrote the labels, the baseline
   would score 100% and prove nothing. Even so, the score is optimistic, because both sides
   follow the same written rules.
2. **Boundaries are exact.** Money is `Decimal`, never `float`. Exactly 2.00% or exactly
   ₹5,000.00 is within tolerance; 2.01% or ₹5,000.01 is not. Tests sit on both sides of
   every limit.
3. **Three policy outcomes.** DENY means "never" (wrong action, self-approval, the agent
   approving). REQUIRE_APPROVAL means "not yet": a human step is missing. ALLOW means run
   it. The executor will refuse anything but ALLOW.
4. **Ignoring free text cuts both ways.** It makes the rules immune to prompt injection,
   but blind to a bank change written only in the notes. That is the baseline's 2 unsafe
   outcomes, and the agent's job in Phase 4.
5. **A test that cannot fail is worthless.** Mutation checks break the code on purpose and
   confirm a test notices; all 8 did.

**Next phase plan (Phase 2: Databricks data layer and governed tools):**

- Load the same dataset into Unity Catalog Delta tables with one idempotent setup script
  or notebook.
- Add read-only tools as Unity Catalog functions where it makes sense, and a Databricks
  adapter for `APDataReader`.
- Run the same parity tests against Databricks.
- First verify the Free Edition open items: whether Unity Catalog Python functions run
  there, and whether PyPI is reachable.
- I'll send the detailed plan for approval first.

## Phase 0 — Plan and scaffold — 2026-10-25

**Status:**

| Component | Status |
|---|---|
| Repo scaffold (layout, package skeleton, CLI stub) | implemented |
| Toolchain (uv, ruff, mypy strict, pytest, pre-commit + gitleaks) | implemented |
| Platform research (Databricks Free Edition, MLflow, LangGraph) | recorded in [ADR 0001](docs/adr/0001-platform-constraints-and-toolchain.md) |
| Workspace model-endpoint check | listed: 12 READY endpoints (not yet queried) |
| Everything from Phase 1 onward | planned |

**What I built:** The empty skeleton of the project and the safety rails around it.

- An installable Python package (`invoiceflow`) with one empty folder per part of the architecture. Each folder's docstring says what will live there and in which phase.
- A tiny command-line tool (`uv run invoiceflow`) that will grow a subcommand per phase.
- Smoke tests proving the package installs and every folder imports.
- Git hooks that check every commit: lint, formatting, strict typing, a secret scanner, and a guard that refuses any `.env` file.
- The working rules (`CLAUDE.md`), a copy of the full spec (`docs/SPEC.md`), a README skeleton, and ADR 0001 with every platform fact checked against today's docs.

**How to run it:**

```bash
uv sync
uv run pytest --cov
uv run pre-commit install
uv run pre-commit run --all-files
uv run pre-commit run gitleaks-history --hook-stage manual --all-files
```

**Evidence:** [docs/evidence/phase-0/acceptance-2026-10-25.log](docs/evidence/phase-0/acceptance-2026-10-25.log), run at commit `d6e5ffe`.

- All 9 acceptance commands exit 0: `uv sync --locked`, `uv build`, `invoiceflow --version`, `ruff check`, `ruff format --check`, `mypy`, `pytest --cov`, `pre-commit run --all-files`, and the full-history gitleaks scan.
- Both negative probes were blocked with exit code 1. A staged file with a random fake GitHub token was caught by gitleaks rule `github-pat`, and a force-staged `.env.probe` was rejected by the `.env` guard. Both probe files were deleted afterwards.
- Workspace endpoints: [docs/evidence/phase-0/serving-endpoints-2026-10-25.log](docs/evidence/phase-0/serving-endpoints-2026-10-25.log). The workspace host is omitted from the log.

**Measured results:**

- Product metrics: `[NOT YET MEASURED]`. No invoice logic exists yet.
- `uv run pytest --cov` on 2026-10-25: 17 tests passed. Line coverage is 100% of the 14 statements in `__init__.py` and `cli.py`. That number covers skeleton code only and says nothing about the product.
- `databricks serving-endpoints list --profile invoiceflow` on 2026-10-25: 12 READY endpoints, 9 chat and 3 embeddings, all open-weight models. The full list is in ADR 0001.

**What is NOT done / known limitations:**

- The workspace endpoints were listed but never queried. Tool calling, structured output and rate limits are unverified. They get checked in Phase 3 (embeddings) and Phase 4 (chat), before a default model is picked.
- There is no GitHub remote, nothing is pushed, and CI doesn't exist yet (Phase 5). Creating the repo, and choosing public vs private and a license, needs Manoj's approval.
- On commit, gitleaks scans only staged changes. The full-history scan is a manual hook today and will run in CI from Phase 5.
- The mypy hook runs through `uv run`, so anyone committing needs uv on their PATH.
- Docker isn't used yet (Phase 1).

**Risks and failure modes found:**

- **The spec is partly out of date.** ADR 0001 lists four corrections. The biggest: serving an agent through `ResponsesAgent` + MLflow AgentServer is now the legacy path on Databricks.
- **Only open-weight models in the workspace.** There are no GPT, Gemini or Claude endpoints. If the Phase 4 eval shows that open-weight models aren't good enough at investigating and explaining, the only alternative is the optional Azure OpenAI provider, which costs money and needs your approval. The deterministic-first design limits this risk, because the LLM never decides the exception class.
- **Free Edition quota lockout.** Going over fair usage shuts compute off for the rest of the day, which could stall a live evaluation.
- **Restricted outbound internet on Free Edition.** A Databricks run can't reach a sandbox ERP on a laptop, so where the ERP runs matters (ADR 0009).
- **The repo path contains spaces.** uv and pre-commit handled it. Docker bind mounts and any shell scripts must quote paths.
- **uv cache on C:, repo on D:.** Hardlinks fail across drives, so `link-mode = "copy"` is set. Installs are a little slower; nothing breaks.
- **The machine's default Python is 3.13.** Running tools outside `uv run` could pick the wrong interpreter.

**Decisions made:** [ADR 0001](docs/adr/0001-platform-constraints-and-toolchain.md):

- Python 3.12 and the toolchain above
- `ports/` + `adapters/` layout
- Postgres + pgvector as the local backend
- On Databricks, the agent runs as a notebook or job first
- Model endpoint names come only from config

**What Manoj should understand before the next phase:**

1. **Ports and adapters.** The agent asks an interface for things ("give me PO 123") and never talks to Postgres or Databricks directly. Switching backend means switching the adapter behind the interface. That is how one set of tests can run on your laptop and the same agent code can run on Databricks.
2. **Pinned versions.** `uv.lock` fixes the exact version of every package, and `.python-version` fixes Python at 3.12, the same as Databricks serverless. Code that passes locally then behaves the same way there.
3. **Pre-commit is a gate, not a guarantee.** The hooks run before git accepts a commit, and we proved the scanner blocks a fake token. It still only catches patterns it knows, so secrets should never be typed into files in the first place. They belong in `.env`, Databricks secret scopes or Key Vault.
4. **Deterministic first.** In Phase 1, matching, GST checks and policy are plain Python with tests and no LLM. Later the LLM only investigates and explains; it can't overrule a deterministic check. That is what makes the measured numbers trustworthy.
5. **Status words are evidence levels.** "Implemented" means the code exists and its checks pass. It doesn't mean "tested on Databricks". Each step up the ladder needs its own recorded proof.

**Next phase plan (Phase 1: synthetic data + deterministic core):** I'll send a detailed plan for approval first. In outline:

- A seeded generator for vendors (GSTINs with a correct checksum, plus a few deliberately invalid ones), POs, GRNs, about 300 labeled invoices and about 25 adversarial ones, split into dev and held-out sets.
- Pydantic schemas + SQL DDL, Docker Compose Postgres + pgvector, and a loader.
- Test-first `core`: matcher, tolerance, GSTIN checksum, tax-type check, duplicate detection.
- `policy/control_matrix.yaml`, the v1 evaluator, and exhaustive tests including denial cases.
- A measured rule-only baseline on the dev set, plus ADRs 0002 and 0003.

Questions I'll raise in that plan: whether the "≤ 2% and ≤ ₹5,000" tolerance is measured per line or per invoice total, and whether each limit boundary (₹1,00,000, ₹10,00,000) is inclusive.
