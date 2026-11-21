# Limitations

What InvoiceFlow does **not** do or prove, as of 2026-10-25.

## Not run yet

- **The agent as a job or endpoint on Databricks.** The full live eval uses the Databricks
  backend end to end (Unity Catalog data, AI Search, serving endpoint), but the graph runs on
  a laptop, not as a Databricks notebook, job or Agent Runtime deployment.
- **AI Search abstention.** The live index never abstains on off-topic questions (0 / 2); no
  score threshold is calibrated yet.
- **Embedding choice.** GTE Large was not compared with BGE or Qwen3-Embedding.
- **Postgres integration tests locally.** Docker Desktop would not start from the build
  session; CI runs them in a service container.
- **Entra ID.** OIDC validation is tested with a local key; no tenant is configured.
- **Phase 7 deployment** (Azure Container Apps, Key Vault, IaC, load tests, SLOs, cost
  model): not started, by decision.

## Measurement limits

- **The data is synthetic and clean.** Labels and matcher share written rules, so high
  scores show consistency with the spec, not real-world accuracy.
- **The stub model is not an LLM.** Stub-mode agent results measure the harness and the
  deterministic text screen. Live-model numbers cover only the subset in PROGRESS.md.
- **Citation relevance is a section map,** not a reading of the cited text.
- **The retrieval eval set is small** (31 questions) and was also used to choose the
  abstention rule.
- **The local retriever's embedder is hashing-based,** not semantic.
- **Tokens for the stub are estimated** from text length. Cost needs a price per token in
  configuration (default 0).

## Design limits

- One invoice per PO line; cumulative billing across several invoices is not modelled.
- Invoice-number normalization does not split glued digit groups ("CF20260042").
- A genuine repeat order with the same amount within 7 days would be flagged as a near
  duplicate.
- The audit chain is tamper-evident, not anchored to write-once storage.
- The approval inbox is minimal: no pagination, CSRF tokens or rate limits.
- The vendor-master GSTIN case has no "fix vendor master" action in the v1 taxonomy.
- The outbox is written but nothing publishes it.
- No OCR or PDF ingestion (v1 scope).
