# ADR 0004: Databricks as the data and AI platform (vs Snowflake)

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (spec), Claude Code

## Context

The agent needs governed tables, governed tool functions, vector or hybrid retrieval, a model
endpoint, tracing and evaluation. These pieces should share one governance model, and the
whole thing must be buildable for free.

## Options considered

1. **Databricks.** Unity Catalog governs tables, volumes and SQL functions. AI Search
   (Delta Sync, hybrid queries, filters) covers retrieval. Foundation Model APIs are
   pay-per-token, and MLflow handles tracing and evaluation. **Free Edition** costs
   nothing, with limits recorded in ADR 0001.
2. **Snowflake.** Snowflake Cortex (search, LLM functions) and Snowpark have a comparable
   governed-data story. The free trial is time-limited, and the agent framework, tracing
   and evaluation tooling would come from separate products.
3. **Plain Postgres + OSS.** It's cheap, but has no unified governance or managed model
   serving, which would undercut the "enterprise" story of the project.

## Decision

Databricks. Every Databricks dependency sits behind a port (ADR 0002). Snowflake could be
added as one more adapter set without changing the agent.

## Consequences

- Free Edition limits apply: serverless only, a single AI Search endpoint, no Direct
  Vector Access, open-weight models only, and quota lockouts (ADR 0001).
- Governed tools are Unity Catalog SQL functions (`adapters/databricks/setup.py`). They are
  read-only and mask bank accounts. Verified live: `get_vendor('V001')` returns
  `XXXXXXXX5846`.
- **Ran on the workspace (2026-10-25):** `invoiceflow databricks setup` (89 s), then `parity`
  with 0 mismatches over all 1,156 records and 325 labels
  (`docs/evidence/databricks/parity-2026-10-25.log`), then `index`.
- **Free Edition specifics found while running:**
  - Only the `workspace` catalog exists, so the schemas are `workspace.invoiceflow_ap` and
    `workspace.invoiceflow_eval`.
  - Per-record SQL reads take about 5 s on the 2X-Small warehouse, so batch work reads each
    table once (`Snapshot`).
