# ADR 0005: Retrieval: section chunks, scoped hybrid search, abstention

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Claude Code (Manoj approved the spec's retrieval design)

## Context

The agent must cite the AP policy and the vendor's contract. A user, or the agent working on
one vendor's invoice, must never see another vendor's contract. When nothing in the
documents answers a question, the retriever must say so instead of returning weak matches.

## Decision

- **Chunks are numbered sections (§x.y)** with metadata: doc_id, section, vendor_id, effective
  dates, and allowed_roles. Contracts are hidden from Platform Admins.
  (`retrieval/chunking.py`)
- **Access filtering happens before ranking.** Out-of-scope chunks are never scored. The
  agent's scope is one vendor (`tools/readonly.py`).
- **Local retrieval** is BM25 plus a deterministic **hashing embedder**, fused with
  reciprocal rank fusion (k = 60). The hashing embedder is a stand-in for a real embedding
  model: it keeps CI offline and reproducible, but it is not semantic.
- **On Databricks:** an AI Search Delta Sync index (Change Data Feed on), with embeddings
  from EMBEDDING_ENDPOINT, `query_type="hybrid"`, and metadata filters (role LIKE, vendor
  IN). Results are re-checked against the scope as defence in depth.
- **Abstention.** The best section must score at least BM25 2.0 **and** contain at least
  half of the question's content words.

## Evidence (measured 2026-10-25, 31-question set, local retriever)

| Abstention rule | Recall@1 | Recall@3 | Recall@5 | Off-topic abstained | Access violations |
|---|---|---|---|---|---|
| BM25 score ≥ 2.0 only (first version) | 0.893 | 1.000 | 1.000 | 1 / 2 | 0 |
| BM25 ≥ 2.0 **and** ≥ 50% term coverage (chosen) | 0.857 | 0.964 | 0.964 | 2 / 2 | 0 |

The coverage rule loses one answerable question (q18: its answer is split across GST-GUIDE
§2.1 and §2.2, and neither section alone covers half the question). It is kept on purpose:
an abstention routes the case to a human, which is safer than a confident wrong citation.
**Caveat:** this choice was made on the same small eval set it is reported on, so the
numbers may flatter it.

## AI Search on the workspace (measured 2026-10-25)

Index `workspace.invoiceflow_ap.policy_index` on endpoint `invoiceflow-search`: Delta Sync,
embeddings from `databricks-gte-large-en`, `query_type="HYBRID"`, role and vendor filters.
Same 31 questions (`docs/RETRIEVAL_REPORT_AISEARCH.md`):

| Retriever | Recall@1 | Recall@3 | Recall@5 | Off-topic abstained | Access violations |
|---|---|---|---|---|---|
| Local (BM25 + hashing + RRF) | 0.857 | 0.964 | 0.964 | 2 / 2 | 0 |
| AI Search hybrid (GTE Large) | 0.929 | 1.000 | 1.000 | **0 / 2** | 0 |

AI Search finds the right section more often, and the live filters keep scope (0
violations). It never abstains, because the adapter applies no score threshold. Inside the
agent every query is on-topic, so the impact is small, but a calibrated threshold, chosen
on a separate question set, is open work.

## Consequences

- GTE Large was used without comparing it to BGE or Qwen3-Embedding; that comparison is not
  done.
- The AI Search client package (`databricks-ai-search`) only accepts a PAT or a service
  principal from a laptop. The adapter therefore uses the Databricks SDK's vector_search
  services, which use the CLI login.
