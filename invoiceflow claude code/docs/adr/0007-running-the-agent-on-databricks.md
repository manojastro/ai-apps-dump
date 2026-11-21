# ADR 0007: Running the agent on Databricks

- **Status:** Accepted (direction chosen in ADR 0001; serving deferred)
- **Date:** 2026-10-25
- **Deciders:** Manoj (Phase 0 default; "deployment later"), Claude Code

## Context

Databricks now labels `ResponsesAgent` + MLflow AgentServer on Apps as *legacy*. It
recommends the Agent Bricks CLI (Beta) with DurableAgentServer on Agent Runtime, but that
path is unverified on Free Edition (ADR 0001).

## Decision

1. **Primary:** run the same graph from a serverless notebook or job with
   `INVOICEFLOW_BACKEND=databricks`, which selects the UC reader, AI Search and serving
   endpoints. On Databricks the ERP is the in-process adapter, because a laptop service is
   unreachable from serverless compute (restricted outbound internet).
2. **Wrapper:** `agent/responses_agent.py` (`InvoiceFlowResponsesAgent`) exposes the graph
   through MLflow's `ResponsesAgent` interface, for MLflow evaluation and for serving later.
3. **Serving** as a live endpoint (Agent Bricks CLI or the legacy AgentServer) is deferred,
   to be decided when deployment starts.

## Consequences

- **The full dev split ran on the Databricks backend** (Unity Catalog data, AI Search,
  `databricks-gpt-oss-120b`), with the graph driven from a laptop (PROGRESS.md, 2026-10-25).
  A notebook or job run on Databricks itself has **not** been done yet.
- Approvals still come from the approval service; a chat turn can never approve.
