# ADR-001 — Hybrid keyword + vector retrieval fused with RRF (mock-first)

Date: 2026-09-18 · Status: accepted · Slice: P1 mock-first (no DB, no network)

## Context

OpsCopilot must answer questions like *"VPN fails with ERR_VPN_809"* (exact
code) as well as *"can't get onto the network at home"* (paraphrase).
Keyword search wins on exact codes/IDs; vector search wins on meaning.
We need one ranking that benefits from both without calibrating two
incompatible score scales (TF-IDF weights vs cosine similarities).

## Decision

- Run **keyword** (TF-IDF-ish, pure Python) and **vector** (deterministic
  hash-embedding cosine mock) searches in-process over the chunked corpus.
- Fuse with **Reciprocal Rank Fusion**: `RRF(d) = Σ 1/(k + rank(d))`, `k = 60`.
- Rerank stub keeps RRF order (`rerank_enabled` flag exists for the real
  cross-encoder later); refusal when best fused score `< OPS_REFUSE_THRESHOLD`
  (0.029, tuned on the smoke set — see `reports/smoke_*.json`).

## Alternatives considered

- **Vector-only:** fails exact codes (`0x80070005`, `ERR_VPN_809`) — the mock
  embedding has no reason to rank the literal match first.
- **Keyword-only:** fails paraphrases and returns nothing useful for
  meaning-only queries.
- **Score-level fusion (weighted sum):** requires normalising incompatible
  scales per query; brittle without a tuning set. RRF uses ranks only.

## Consequences

- `+` Exact-code questions retrieve the right chunk at rank 1 (smoke q02/q04).
- `+` Fully offline/deterministic: evals reproduce byte-identical reports.
- `-` Hash embeddings carry no real semantics — vector wins over keyword only
  by token-bucket coincidence. Replaced by real embeddings + pgvector later
  without changing the `/v1/search` and `/v1/ask` contract.
- `-` Refusal threshold is tuned on 15 smoke questions; revisit with P2 evals.
  Known gap: single shared domain words (e.g. "store") can push an unrelated
  chunk over threshold (smoke q15) — documented failure demo in README.
