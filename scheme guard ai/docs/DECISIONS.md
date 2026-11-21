# Decisions (short ADRs)

Each entry: context → decision → consequence.

## ADR-001 Deterministic core, LLM at the edges
Schema diffing, compatibility classification, lineage traversal, per-asset verdicts, build-impact
analysis, routing, guardrails and test execution are plain Python with unit tests. The LLM writes
the change explanation, the fix plan, file edits and the business summary. **Consequence:** verdicts
are reproducible and testable; an LLM mistake can at worst produce a patch that fails the sandbox or
the guardrails, and a human still has to approve.

## ADR-002 SQLite by default, Postgres optional (owner-approved 2026-11-15)
The build machine had no Docker. The checkpointer, run index and lineage store share a tiny
`Database` wrapper (SQLite or Postgres). `langgraph-checkpoint-postgres` depends on psycopg
(LGPL-3.0); the owner approved it as the optional `[postgres]` extra. **Consequence:** tests and
the demo run anywhere; the Postgres path is written but was not exercised on the build machine.

## ADR-003 File-backed schema registry behind the Confluent interface
`FileSchemaRegistry` and `ConfluentSchemaRegistry` implement one protocol. **Consequence:** the
poller and demo work offline; the Confluent client is built but not run against a live registry.

## ADR-004 The LLM returns full file contents, code makes the diff
LLM-written unified diffs often have broken hunk headers. `generate_patch` asks for whole files,
diffs them with `difflib`, and applies diffs with a strict, pure-Python applier.
**Consequence:** a patch always applies cleanly to the files it was made from, and guardrails see a
normalised diff.

## ADR-005 Column lineage = projections + join/filter/group references
`sqlglot.lineage` covers projected columns only. Columns in JOIN/WHERE/GROUP BY also change results,
so each output column gets a `DERIVES_FROM` edge with `via=join|filter|group` to them.
**Consequence:** the `status` filter in `daily_revenue` correctly reaches the revenue dashboard. The
cost is a wider blast radius for join keys, which is accurate (dropping a join key breaks the table).

## ADR-006 Build impact next to column verdicts
The DuckDB oracle in the eval showed that column-level lineage alone missed about 70% of the data
tests that actually fail: when `stg_orders` fails to build, every downstream table goes stale, and
tests on them fail too (including row-count tests with no column lineage). `aggregate` now reports
failing builds, stale tables, stale dashboards and blocked tests. **Consequence:** the oracle's
test recall went from 29.7% to 100% on the 25 scenarios.

## ADR-007 DataTest nodes in the lineage graph (extension to the spec's node types)
Tests are first-class assets: "the accepted-values test will fail" is often the most actionable
verdict. Added `DataTest` nodes and `TESTED_BY` edges.

## ADR-008 Fake LLM is a scripted engineer, labelled as such
CI must be deterministic and free. `FakeLLM` applies a strategy ladder and line-level SQL/YAML edits
from structured context. **Consequence:** fake-LLM eval numbers measure the pipeline, not model
quality; the README and summary say so.

## ADR-009 Workflows in `.github/workflows/`
GitHub only runs workflows from that path; `infra/github-actions/README.md` points there.

## ADR-010 Approval is an `interrupt()` inside the graph, not an external flag
The run's state, including the exact patch and test evidence, is checkpointed at the interrupt; the
resume value (`approve`/`reject`, reviewer, comment) becomes part of state and the report.
**Consequence:** a run survives an API restart (tested). Reviewer identity is self-declared in this
build; production needs real auth (Entra ID on Container Apps ingress).

## ADR-011 Idempotency key = sha256(topic + canonical new schema)
Works for API, CLI and poller submissions alike. The poller also remembers the last version per
subject. **Consequence:** resubmitting an identical schema returns the existing run, even if that
run was rejected; a deliberate re-run needs a schema change or a new key strategy.

## ADR-012 Sandbox = copy + subprocess + timeout + Python network guard
No container-in-container locally. The sandbox copies the pipeline, applies the patch, generates
data under the new schema, and runs transforms/tests in `python -I -m schemaguard.sandbox.runner`
with a timeout and sockets disabled. **Consequence:** it is best-effort isolation; it relies on the
patch guardrails (allowed paths, file types, size, secrets) as the primary control. In Azure the
worker container adds process isolation.

## ADR-013 Azure as the deployment target (per BUILD_PROMPT)
The owner's global defaults prefer Google Cloud Run, but this project's spec names Azure Container
Apps, Postgres Flexible Server, Event Hubs and Key Vault, so the Bicep targets Azure. ACR (Basic)
was added because images need a registry; Event Hubs has no Confluent-compatible schema registry,
so a Confluent-API registry (e.g. Apicurio or Karapace as a container app) or an Azure Schema
Registry adapter is needed (`planned`).

## ADR-014 Python 3.12 floor
`networkx==3.7` requires Python ≥ 3.12, so `requires-python = ">=3.12,<3.14"` instead of 3.11.
