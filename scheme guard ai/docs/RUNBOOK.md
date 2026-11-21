# Runbook

All commands from the repo root. State lives in `SCHEMAGUARD_HOME` (default `.schemaguard/`).

## Health

```bash
curl -s localhost:8000/health
```
Returns lineage version, LLM provider, database kind and run count. Logs are JSON lines on stderr
with `run_id`, `node`, `duration_ms`, `tokens`, `cost_usd`. Set `SCHEMAGUARD_OTEL_CONSOLE=true` to
print OpenTelemetry spans (`node.<name>`, attribute `schemaguard.run_id`).

## Find out why a run failed or escalated

```bash
uv run schemaguard runs list
uv run schemaguard runs show <run_id>      # prints the report, or status + pending approval
```
* `failed`: an exception escaped a node. `runs.error` holds the message; the checkpoint holds the state up to the failing node.
* `escalated`: read `escalation_reason` in the report (budget, `pin_schema_version` strategy, retries exhausted, plan rejected by guardrails).
* Sandbox output for each attempt: `.schemaguard/sandbox/<run_id>/{baseline,attempt-N}/_sandbox_result.json`.

## Replay a run

Runs are idempotent on (topic, new schema), so "replay" means one of:

1. **Resume** a paused run after a restart: just approve/reject; state comes from the checkpointer.
   ```bash
   uv run schemaguard runs approve <run_id> --reviewer you --comment "..."
   ```
2. **Re-run the same change from scratch** (for example after fixing a rule): use a fresh home so
   the idempotency key is not found, or delete the row.
   ```bash
   SCHEMAGUARD_HOME=.schemaguard-replay uv run schemaguard change --topic orders.v1 --ops '[{"op":"rename_field","field":"amount","to":"total_amount"}]'
   ```
3. **Inspect any step**: LangGraph keeps every checkpoint for the thread (`thread_id = run_id`):
   ```python
   from schemaguard.service import SchemaGuardService

   svc = SchemaGuardService()
   for snap in svc.graph.get_state_history({"configurable": {"thread_id": RUN_ID}}):
       print(snap.next, list(snap.values))
   ```

The report records the lineage graph version used, so a replay with a different graph version is visible.

## Rebuild the lineage graph

The service rebuilds lineage from `demo_pipeline/` at startup and stores a new version only if the
content hash changed. To rebuild explicitly:
```bash
uv run schemaguard lineage build
uv run schemaguard lineage paths field:orders.v1.amount
```
Warnings (unparseable SQL, unknown upstream tables, dashboards referencing missing columns) are logged as `lineage warning`.

## Schema registry is down

* The poller logs `registry unavailable; backing off` and retries with exponential backoff (capped at 5 minutes). No runs are lost: it compares against the last version it saw, so missed versions are processed once the registry is back.
* Meanwhile, changes can be submitted directly: `POST /changes` with `topic` + `new_schema` (or `mutations`), or `schemaguard change`.
* Check: `curl -sf $SCHEMAGUARD_REGISTRY_URL/subjects`.

## Budget exceeded

Per-run limits: `SCHEMAGUARD_RUN_BUDGET_USD` (default 0.50) and `SCHEMAGUARD_RUN_BUDGET_TOKENS` (200k).
When exceeded the run escalates with the analysis so far. Raise the limit only after checking the
token counts in the run report.

## Postgres

Set `SCHEMAGUARD_DATABASE_URL=postgresql://...` and install the extra (`uv sync --extra postgres`).
The checkpointer tables are created by `PostgresSaver.setup()` on startup.
Integration against Postgres was not exercised on the build machine (no Docker); start with
`docker compose --profile core up -d postgres` and run the test suite with the env var set.

## Rotate the GitHub token

Draft PRs are only opened when `SCHEMAGUARD_GITHUB_TOKEN` and `SCHEMAGUARD_GITHUB_REPO` are set and a human approved. Use a fine-grained token limited to that repo with `contents:write` and `pull_requests:write`.
