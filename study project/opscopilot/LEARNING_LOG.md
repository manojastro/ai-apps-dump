# LEARNING_LOG — OpsCopilot P1 (condensed, M1–M5 of the P1 milestone map)

## M1 — Synthetic knowledge base + loaders — 2026-09-18
**Built:** `scripts/generate_corpus.py` (30 KEDB + 8 SOP, all `synthetic: true`) with traps:
conflicting pairs KB0007/KB0008 + KB0015/KB0016, retired KB0029/KB0030, near-dups KB0011/KB0012.
`src/opscopilot/corpus.py` parses front-matter into Pydantic `Document`s.
**New concepts:** metadata (service/status/date) filters retrieval before text is even scored;
front-matter is just YAML between `---` markers.
**Break-it result:** retired docs still retrieve — handled by preferring `active` in the composer.
**Quiz:** n/a (build slice) — gaps: none blocking.
**Open questions:** PDF runbooks deferred (no PDFs in P1 slice).
**Interview line I can now say:** "Metadata is a first-class retrieval signal: service and status filters cut the search space before any scoring."

## M2 — Chunking experiments — 2026-09-18
**Built:** heading-aware splitter (`src/opscopilot/chunk.py`): each chunk prefixed
`title > section`, long sections re-split at paragraph boundaries under `max_chars`.
38 docs → 190 chunks. Tests: prefix kept, long-section split, unique ids.
**New concepts:** chunk too small = lost context; too big = noisy retrieval; headings are free structure.
**Break-it result:** predicted 50-char chunks would scatter sections — kept default 1500 for the slice.
**Quiz:** n/a — gaps: overlap tuning deferred to M9-style evals.
**Open questions:** none.
**Interview line I can now say:** "Heading-aware chunks keep the section title with the text so a chunk is self-describing at retrieval time."

## M3/M4 — Storage layer, mock-first (LangChain/pgvector deferred) — 2026-09-18
**Built:** in-memory chunk store loaded from `data/corpus` at startup
(`ensure_loaded` in `app.py`); no external DB in P1. Stable `/v1/search` + `/v1/ask`
contract documented in `docs/api-contract.md` for P2/P3/P4.
**New concepts:** cosine similarity = angle between meaning-vectors; HNSW/IVF-PQ deferred with pgvector.
**Break-it result:** empty corpus → `/health` reports `"empty"` instead of crashing.
**Quiz:** n/a — gaps: real pgvector SQL comes with the DB milestone.
**Open questions:** HNSW `M`/`efSearch` tuning deferred to the index experiment.
**Interview line I can now say:** "We fixed the API contract first so P2 evals and the P3 MCP server can build against mocks."

## M5 — Hybrid retrieval with RRF — 2026-09-18
**Built:** `rrf_fuse(rankings, k=60)` + TF-IDF-ish keyword scorer (stopwords incl. corpus
boilerplate) + deterministic hash-embedding cosine mock; `docs/rrf-worked-example.md`
hand-verified against code output. Tests: both-lists-beats-one, empty, exact math, determinism.
**New concepts:** keyword wins on codes (`ERR_VPN_809`), vectors win on paraphrase;
RRF fuses ranks, never raw scores, so incompatible scales can't fight.
**Break-it result:** predicted vector-only would miss `0x0000011b` — confirmed via keyword rank-1 test.
**Quiz:** n/a — gaps: BM25 proper (we use TF-IDF-ish; Postgres `ts_rank_cd` comes with pgvector).
**Open questions:** none.
**Interview line I can now say:** "RRF(d) = Σ 1/(k+rank(d)): a doc at rank 1 in both lists scores ~2× one in a single list, with zero score calibration."

## M6 — Rerank (stub), generate (mock), cite, refuse — 2026-09-18
**Built:** `mock_rerank` (keeps order, flag-ready), refusal at best fused score < 0.029,
extractive composer citing `[DOC §Section]`, deterministic `validate_citations`,
conflict/near-dup dual citation, retired deprioritised.
Smoke: hit_rate@5 1.0 (12/12), refusal 0.933 (14/15), citations 1.0, p95 40.17 ms.
**New concepts:** refusal is a feature; hallucinated citations die by checking cited ids ⊆ retrieved ids.
**Break-it result:** predicted unanswerable q15 ("haiku … store opening") might slip through on the
word "store" — actual: scores 0.0323 and answers. Kept as documented failure demo.
**Quiz:** n/a — gaps: real cross-encoder + LLM judge deferred.
**Open questions:** retune threshold on a larger P2 eval set.
**Interview line I can now say:** "Every citation is validated in code against the retrieved set — an answer cannot cite a document it never saw."
