# 14 — Vector Databases

**What this chapter trains:** embeddings, ANN indexes, distance metrics, filtered search, hybrid retrieval, vendor trade-offs, and scale failure modes — at the depth 2026 production interviews actually use.

This is not a product catalog. Interviewers do not hire people who can name twelve vector databases. They hire people who can explain why recall dropped after a metadata filter, why search got slow after a million documents, and why they would *not* introduce a new store.

If RAG (Chapter 10) is “can you make the answer right,” this chapter is “can you make retrieval survive production.”

**Roles that weight this heavily:** GenAI Engineer, RAG Engineer, Cloud AI / Platform, FDE, Solutions Architect. Agentic loops use it as a follow-up: “the agent is calling search — why is it wrong?”

---

## How this topic is scored

| Signal they want | How you show it |
| --- | --- |
| You understand embeddings as a contract | Same model, same metric, re-embed on change |
| You treat ANN as a trade-off, not magic | Recall@k, latency, RAM, rebuild cost |
| You have been burned by filters | Pre- vs post-filter, overfetch, tenant partitions |
| You default to hybrid, not pure vector | BM25 + dense + rerank, with a reason |
| You pick stores by constraint | Scale, tenancy, ops, data gravity — not a blog ranking |
| You can debug a slow/wrong index | Ordered investigation, not “switch to Pinecone” |

**Interview-safe stance:** “The vector database is an index, not the product. Chunking, embedding model, filters, and evals dominate quality. I pick the cheapest store that meets recall, latency, tenancy, and ops constraints, and I measure recall@k on *our* queries.”

---

## 0. The 60-second mental model

A vector database stores **embeddings** (numeric arrays) plus **payload/metadata**, and answers “which stored vectors are nearest to this query vector?”

Production RAG almost never does exact nearest neighbor over the whole corpus. It does **approximate nearest neighbor (ANN)** so p95 stays in tens of milliseconds, then **filters** by ACL/tenant/time, often **fuses** with lexical search (BM25 / sparse), then **reranks** a shortlist.

```
query
  → embed with THE SAME model as documents
  → (optional) BM25 / sparse lexical retrieval
  → ANN over dense vectors  (HNSW / IVF / DiskANN / …)
  → metadata filter (tenant, ACL, time, source)
  → fusion (RRF / weighted) → top N
  → cross-encoder rerank → top k
  → pack into context with citations
```

Everything that goes wrong in interviews lives in one of those arrows.

---

## 1. Embeddings

### Q1. What is an embedding, and what does a vector database actually store?

**Why they ask.** They are checking that you do not treat “the vector DB” as a magic semantic brain. Juniors describe cosine. Seniors describe a contract: model, dimension, metric, chunk identity, metadata, and invalidation.

**30s.** An embedding is a fixed-length float vector that places a chunk of content in a space where nearby points are semantically similar *according to the model that produced it*. The database stores that vector, an ID, the raw (or pointer to) text, and metadata used for filters and citations. Similarity is not meaning in the abstract — it is the geometry of one specific model.

**2min.** I treat embeddings as a derived index, like a search posting list, not as source of truth. Source of truth is the document store. On ingest I chunk, embed with a pinned model ID, write `{id, vector, text_or_uri, metadata}`. At query time I embed the query with the **same** model and metric the index was built for. If I change the embedding model, dimension, instruction prefix, or normalization, the old vectors are garbage and I re-embed. I also store enough metadata to enforce ACLs and to cite: tenant, source URI, chunk index, doc version, timestamp, classification. I never put secrets in payload that the retriever will stuff into a prompt.

**Senior.** Three contracts I pin in config, not in tribal knowledge: (1) **model identity** — name, revision, dimension, instruction format (`query:` vs `document:` for asymmetric models); (2) **space** — metric and whether vectors are L2-normalized; (3) **document identity** — how a chunk maps back to a source version so deletes and updates are exact. I evaluate retrieval with a labeled set: recall@k, MRR, and “did the cited chunk actually support the answer.” Embedding quality usually dwarfs index choice under ~10M vectors. I also watch for embedding drift: a silent model upgrade from the vendor that shifts the space and tanks recall without a code change. For multimodal, I am explicit about whether text and images share a space (e.g. a vision-text model) or I have two indexes.

**Weak answer.** “Embeddings turn text into numbers so we can search by meaning. We use OpenAI embeddings and Pinecone.” No model pin, no re-embed story, no metadata, no eval.

**Follow-ups.**
- *What happens if you mix `text-embedding-3-small` documents with a `text-embedding-3-large` query?* Dimensions and spaces differ; search is undefined. Reject at the API.
- *Do you store the text in the vector DB?* For RAG, usually yes or a pointer. Citations need the chunk. If payload is huge, store text in object storage and keep a pointer + hash.
- *How do you handle a model deprecation?* Dual-write or blue/green re-embed into a new collection, switch the query pointer, keep the old index until evals pass.
- *Sparse vs dense embeddings?* Dense captures paraphrase. Sparse (BM25, SPLADE, BGE-M3 lexical) captures exact tokens, SKUs, IDs. Production defaults to both.

---

### Q2. How do you choose an embedding model in 2026?

**Why they ask.** They want a decision, not a leaderboard recitation. MTEB rank is a weak answer by itself.

**30s.** I match domain, language, dimension/cost, and whether I need asymmetric query/doc encoders. I run a retrieval eval on *our* corpus and queries. I pin the model. I only switch if evals move and I can afford a full re-embed.

**2min.** Default path: start with a strong general model the team can actually call (cloud embedding API or a self-hosted E5/BGE/GTE/Voyage-class model), dimension in the 384–1024 range unless evals demand more. Check: multilingual need, code vs prose, instruction prefixes, max tokens, price per million tokens, and whether Matryoshka / dimension truncation is supported so I can store 256-d and still retrieve. I measure recall@10 and nDCG on a gold set of 200+ real queries before I care about ANN. I do not pick a 3072-d model to “be safer” — that 4× RAM and 4× distance cost for a 2-point MTEB bump is usually a loss.

**Senior.** The embedding model is a **migration**. Switching is a re-index of the whole corpus plus query-side cutover. I budget that. I also separate **retrieval embeddings** from **clustering / dedup embeddings** if needed. For enterprise, I care about: data residency of the embedding API, whether documents leave the VPC, rate limits during ingest, and whether the model is trained so that cosine on L2-normalized vectors is the intended metric. Late-interaction models (ColBERT-style) can beat single-vector on IR benchmarks but blow up storage and serving complexity; I only use them when a reranker on a hybrid shortlist is not enough. If the corpus is mostly IDs, error codes, and part numbers, I will beat a “better” dense model with BM25 + a cheap dense model.

**Weak answer.** “We use the latest OpenAI embedding because it is number one on MTEB.”

**Follow-ups.**
- *Asymmetric embeddings?* Some models encode queries and documents differently. Using the doc encoder for queries quietly drops recall.
- *Matryoshka?* Train/serve so the first D dimensions are a valid embedding. Lets you store compact vectors and optionally rerank with full dim.
- *Should you fine-tune embeddings?* Only with a real pair/triplet set and an eval that beats the base model. Most teams should rerank first.

---

### Q3. How do chunking and embeddings interact? (They will ask this even in a “vector DB” round.)

**Why they ask.** Retrieval quality is usually a chunking problem blamed on the database.

**30s.** The vector is only as good as the chunk. Too big and you mix topics; too small and you lose the sentence that made it match. I chunk by structure (headings, paragraphs, tables), keep overlap, store parent context for expansion, and embed the chunk I will actually retrieve.

**2min.** I never “split every 512 tokens” as a philosophy. I use document structure first: Markdown/HTML headings, pages, sections. Token-size is a cap, not the unit. I store `parent_id` so I can expand: retrieve small chunks for precision, then send the parent section to the LLM. Tables and code get special chunkers; you cannot embed a split row and expect joins to survive. I keep the embedding input close to the retrieved text so the geometry matches what the LLM will see. I version chunker + model together.

**Senior.** I treat chunking as an eval surface. I keep a failure set: “policy clause not found,” “table cell missed,” “code symbol missed.” Fixes are usually smaller chunks + BM25, or parent expansion, or a metadata field (title, product, version) prepended to the embedding text. Prepending the document title to every chunk is a cheap recall win. I also watch **index bloat**: 200-token chunks with 50-token overlap can 1.3× the vector count and the bill. For agents, I often maintain two indexes: a coarse section index for routing and a fine chunk index for grounding.

**Weak answer.** “We use 1000-character chunks with 200 overlap, LangChain default.”

**Follow-ups.**
- *Late chunking?* Embed a long context then pool token vectors into chunk embeddings so each chunk still sees neighbors. Useful, not magic; still eval.
- *Who owns re-chunking on document update?* Ingestion worker: delete old chunk IDs for that `doc_version`, write new ones atomically from the app’s point of view.

---

## 2. ANN vs exact, HNSW, IVF, product quantization

### Q4. ANN vs exact nearest neighbor — when does each matter?

**Why they ask.** They want you to know that production search is approximate, and that “approximate” is a quality knob, not a bug.

**30s.** Exact kNN computes distance to every vector: correct, O(n), fine for thousands, too slow and too RAM-hostile at millions under a latency SLO. ANN indexes (HNSW, IVF, DiskANN, ScaNN) return *most* of the true neighbors most of the time. I report **recall@k** of the index against exact or a high-`ef` baseline, never just QPS.

**2min.** For a prototype of 10k chunks, I am happy with exact search (pgvector without an index, or `exhaustive` kNN). The moment p95 matters at >100k vectors, I add HNSW (or the platform default) and I **measure** recall@10 / recall@100 on a holdout. I tune `efSearch` / `nprobe` until recall meets the bar, then I stop. I do not brag about 2ms if recall@10 is 0.6 — the LLM will hallucinate the missing policy clause. For evals and for “this tenant has 2,000 docs,” I may still brute-force. Exact is also my **fallback** when a highly selective filter makes ANN unsafe.

**Senior.** ANN recall is not the same as RAG recall. Index recall@100 of 0.95 can still yield a wrong answer if the right chunk was never embedded well. I separate: (a) embedding/chunking quality, (b) index recall vs exact, (c) end-to-end answer faithfulness. When I tune ANN I use a ground set of query vectors with exact neighbors precomputed. I watch **tail latency** and **filtered recall**, not only unfiltered throughput from a vendor slide. At large scale I accept 0.90–0.97 index recall and recover with hybrid + rerank. I never run unindexed sequential scans in prod on millions of rows “because it is more accurate” — that is how you take down Postgres.

**Weak answer.** “ANN is faster so we always use it.” Or “I only use exact because I need 100% accuracy.”

**Follow-ups.**
- *What is recall@k for an index?* Fraction of the true k nearest neighbors that the ANN returned. Not user-facing answer quality.
- *Why can ANN miss a neighbor that is geometrically closest?* The graph/cluster probe never visited that region. Increase `efSearch`/`nprobe`, rebuild with higher `M`, or the filter removed the path.
- *When is exact cheaper than ANN?* Tiny corpora; extremely selective filters that collapse the candidate set; one-off audits.

---

### Q5. Explain HNSW at interview depth.

**Why they ask.** HNSW is the default index in pgvector, Qdrant, Weaviate, OpenSearch k-NN (often), and many managed stores. If you cannot sketch it, you cannot tune it.

**30s.** HNSW is a multi-layer proximity graph. The top layer is sparse for long-range jumps; lower layers are denser. Search starts at a top-layer entry point, greedily walks to a closer neighbor, then descends a layer, repeating until layer 0, where it explores a larger candidate heap (`efSearch`) and returns k. Build-time `M` (max edges per node) and `efConstruction` control quality vs RAM vs insert cost.

**2min.** Intuition: skip lists meet kNN graphs. Inserts sample a max layer from an exponential distribution, then connect the new point to `M` nearest neighbors at each layer it belongs to. Queries never scan the whole set; they walk edges. That is why **filters are dangerous**: if the graph edges ignore metadata, a walk can get stuck in the wrong tenant’s neighborhood or skip the only legal documents. Parameters I actually tune:

| Param | Raises it does | Cost |
| --- | --- | --- |
| `M` (e.g. 16–64) | Better graph, higher recall | RAM, slower inserts |
| `efConstruction` | Better edges at build | Longer index build |
| `efSearch` / `ef` | Higher query recall | Latency, CPU |

I start with library defaults, measure recall vs p95, then move `efSearch` first because it does not require a rebuild. I only rebuild with higher `M` if I cannot hit recall without blowing p95.

**Senior.** HNSW is RAM-hungry: you pay for the vectors *and* the graph. At 10M × 1536-d float32 you are already looking at ~60GB of vectors before graph overhead; that is why quantization and disk-backed graphs (DiskANN / Memory-mapped HNSW) appear. Inserts are not free: each insert is a search plus edge rewiring. High-churn workloads (constant deletes/updates) fragment the graph with tombstones; recall and RAM degrade until a rebuild. Deletes in many implementations are **soft**. I plan a periodic optimize/rebuild, and I avoid HNSW as a system of record. For multi-tenant, I prefer **separate graphs per hot tenant** (or per namespace) over one giant graph plus a filter. I know HNSW is excellent up to tens or hundreds of millions *if* it fits memory; beyond that I talk IVF-PQ, DiskANN, or a sharded cluster.

**Weak answer.** “HNSW is a fast algorithm Pinecone uses.” No parameters, no RAM, no delete behavior.

**Follow-ups.**
- *Why is the first query after deploy slow?* Graph and vectors not in page cache; cold start. Warmup or keep a replica hot.
- *Can HNSW be exact?* If `efSearch` is huge it approaches exact at exact-like cost. Not a strategy.
- *HNSW vs LSH?* LSH is rarer in 2026 RAG stacks. Know it exists; do not lead with it.

---

### Q6. Explain IVF (inverted file) and when you pick it over HNSW.

**Why they ask.** IVF (and IVF-PQ) is the classic Faiss large-scale design and still shows up in Milvus, OpenSearch Faiss engines, and billion-scale systems.

**30s.** IVF clusters vectors (k-means) into `nlist` coarse centroids. Each vector is stored in its centroid’s inverted list. A query finds the nearest `nprobe` centroids and only scans those lists. You trade recall for less work. Combined with PQ you can keep billion-scale indexes on disk/RAM budgets that HNSW cannot.

**2min.** Build: train centroids on a sample, assign every vector to a list. Query: probe `nprobe` lists, optionally rerank a reordering buffer with exact or higher-precision distances. Knobs: `nlist` (too small = fat lists; too large = train/query overhead), `nprobe` (the recall/latency knob). IVF shines when the dataset is huge and mostly **append-only**, and you can afford a train step. It is weaker than HNSW at moderate scale on RAM-resident data, and filtered search is awkward if a filter correlates poorly with clusters (you probe lists that contain no legal rows).

**Senior.** I pick HNSW when the working set fits memory and I want simple high recall. I pick IVF/IVF-PQ/DiskANN when vectors are 100M–1B+, RAM is the constraint, or the platform’s GPU/disk story is built around it (Milvus, some OpenSearch modes). Training is a **batch job** with a representativeness requirement: if you train centroids on last week’s data and this week is a new product line, those vectors sit in the wrong lists. Incremental adds are fine; **distribution shift** wants a retrain. I mention product quantization in the same breath because IVF-PQ is the real production combo: IVF narrows lists, PQ compresses the residual so lists fit. I also know **ScaNN** (Google) and **DiskANN** (graph + SSD) as cousins of this design space.

**Weak answer.** “IVF is another index, similar to HNSW.” They are not similar.

**Follow-ups.**
- *What is `nprobe` vs `efSearch`?* Same role, different index: how much of the structure you visit at query time.
- *Why did recall collapse after adding a new language corpus?* Centroids trained on English; new cluster structure. Retrain.
- *GPU IVF?* Training and scan can be GPU-accelerated (Faiss-GPU, Milvus GPU). Worth it at huge QPS or build time, not for a 2M-doc RAG.

---

### Q7. Product quantization (and the other compression you should name).

**Why they ask.** Compression is how you afford 100M+ vectors. They want you to know you are approximating the *distance*, not just the neighbor set.

**30s.** Product quantization splits a vector into `m` subvectors and replaces each with the ID of the nearest codebook centroid. You store `m` bytes (or shorts) instead of `d` floats. Distances are approximated via precomputed tables. You win RAM and cache; you lose some recall, recovered partly by reranking a shortlist with full-precision vectors.

**2min.** A 1536-d float32 vector is 6 KB. PQ with 24 bytes is a ~250× compression on the stored vector (plus codebooks). That is the difference between “fits on one box” and “needs a cluster.” I always **rerank**: retrieve extra candidates (e.g. 10× k) with PQ distances, then exact-distance rerank if I kept original vectors or a higher-precision quantized copy. Other compression I actually use first, because it is simpler:

| Method | Typical compression | When I use it |
| --- | --- | --- |
| Scalar quant (int8) | 4× | First lever; often enough |
| Binary / 1-bit | 32× | Extreme scale, rerank required |
| PQ / OPQ | 8–64× | 100M+, RAM-bound |
| Matryoshka truncate | 2–8× | If the model supports it |

OPQ (optimized PQ) rotates the space before splitting so subspaces are more independent. I will mention it; I will not pretend I implement it by hand.

**Senior.** Quantization error is **not uniform**. Some queries, especially out-of-distribution or very short ones, suffer more. I eval recall **after** quantization, not before. I keep a hot full-precision replica for a gold tenant or for eval. Updates: you cannot always PQ-encode a new vector with an old codebook if the distribution shifted; same story as IVF retraining. For pgvector, halfvec / binary / iterative scanning and pgvectorscale (DiskANN-style) are the 2025–2026 levers I name instead of jumping to a new database. I refuse vendor claims of “no recall loss.” There is always a loss; the question is whether rerank + hybrid hides it on *our* queries.

**Weak answer.** “Quantization makes it faster with no downside.”

**Follow-ups.**
- *Why rerank after PQ?* PQ distance is a coarse score. Full-precision rerank on 100 candidates is cheap and recovers a lot of recall.
- *Can you PQ the query too?* Asymmetric distance computation: query stays float, DB stays PQ. Common and better.
- *int8 vs PQ?* int8 is simpler and SIMD-friendly. Try int8 first.

---

## 3. Distance metrics and normalization

### Q8. Cosine vs dot product vs L2 — and when normalization matters.

**Why they ask.** Wrong metric is a silent quality killer. This is a favorite mid-loop filter question.

**30s.** L2 (Euclidean) cares about magnitude and direction. Inner product / dot cares about both, and prefers longer vectors. Cosine cares only about direction: it is dot product on L2-normalized vectors. I use the metric the embedding model was trained with. If I L2-normalize all vectors, cosine and dot become equivalent, and L2 becomes a monotonic transform of cosine.

**2min.** Formulas I can write on a whiteboard:

- L2: \(\|x - y\|_2\)
- Dot: \(x \cdot y\)
- Cosine: \((x \cdot y) / (\|x\| \|y\|)\)

If \(\|x\| = \|y\| = 1\), then \(\|x-y\|_2^2 = 2 - 2 x\cdot y\), so ranking by cosine, by dot, and by L2 is the **same ranking**. That is why many pipelines normalize on ingest and query and then use dot (faster) or L2 (what the index implements). If I do **not** normalize, switching metric reorders neighbors. Some models (certain CLIP / inner-product trained models) intend raw dot; normalizing them can hurt. I check the model card. I also check the database: pgvector `vector_cosine_ops` vs `vector_l2_ops` vs `vector_ip_ops` must match. Building an HNSW with L2 ops and querying with cosine is a real production bug.

**Senior.** Normalization is a **contract** stored next to the model ID. I normalize once at write and once at query, in the same code path, not “sometimes in the SDK.” I never mix normalized and raw vectors in one collection. Magnitude sometimes carries useful signal (duplicate length, CLIP confidence); throwing it away is a choice. For hybrid fusion I do not compare raw cosine (0.2–0.8) to BM25 (0–40) without calibration; I use RRF or z-score. I am careful with **IP indexes** that assume higher is better vs L2 where lower is better — getting the sort direction wrong is an embarrassing outage. For quantized vectors, cosine on int8 needs consistent scale. Eval: I dump 20 query neighbor lists under each metric during model onboarding and read them; this catches metric mismatches faster than a dashboard.

**Weak answer.** “We use cosine because it is the standard for RAG.” No mention of training metric or normalization.

**Follow-ups.**
- *Angular distance?* Related to cosine; rarely the thing you configure.
- *Why did scores all become 0.99 after a model change?* Different calibration, not necessarily better retrieval. Rank, not absolute score. Use a reranker or threshold on eval, not a cargo-culted 0.8.
- *Max inner product search (MIPS)?* Dot-product retrieval. Some ANN structures are built for MIPS specifically.

---

## 4. Metadata filtering and filtered ANN pitfalls

### Q9. How does metadata filtering work, and what is pre- vs post-filtering?

**Why they ask.** This is the #1 production footgun. Multi-tenant RAG lives or dies here. OWASP LLM 2026 even lists vector/embedding weaknesses; leaking another tenant’s chunk is a security incident, not a quality bug.

**30s.** Filters restrict results by payload (tenant, ACL, time, source, language). **Pre-filtering** applies the predicate before or during ANN so only eligible vectors are considered. **Post-filtering** runs ANN first, then drops neighbors that fail the predicate. Post-filter is simple and fast until the eligible set is a tiny slice of the graph — then you return too few hits or the wrong ones. Pre-filter / in-graph filter is correct but can destroy HNSW connectivity or degrade to a scan.

**2min.** Example: 50M chunks, tenant has 20k. Query with `tenant_id = X`.

- Post-filter with `k=20`: ANN returns 20 global neighbors; maybe **zero** belong to X. You pad, retry with larger k, or look empty. Increasing `k` to 2000 to “overfetch” blows latency and still offers no guarantee.
- Pre-filter: only search X’s 20k. If the engine actually restricts the candidate set, recall is good and work is small. If it only marks nodes invalid while walking the **global** HNSW, the walk can hop through illegal nodes or get stuck.

I design tenancy so the common filter is cheap: **partition key** (collection / namespace / Postgres table partition / Milvus partition) for `tenant_id` or another high-selectivity field, and payload filters for low-selectivity fields (`lang`, `source`). ACLs that are user-specific (document-level permissions) are the hard case: I prefer a **precomputed allow-list of doc IDs** for that user (from the real ACL system) and `id IN (...)` or a bitmap, not a hope that ANN + `user = me` works.

**Senior.** Filtered ANN is an active research/engineering problem; Qdrant’s payload-aware HNSW, Weaviate’s filter strategies, Pinecone namespaces/metadata indexes, OpenSearch filter + k-NN, pgvector `WHERE` + HNSW (which historically planner-picks badly) all behave differently. I do not memorize every vendor flag. I state the failure mode and how I **measure filtered recall** with production-like predicates. Strategies I actually ship:

1. **Physical partition** by tenant (or by “hot tenant” vs shared pool).
2. **Overfetch + post-filter** only when filter selectivity is mild (e.g. 30%+ of corpus).
3. **Exact scan of the partition** when the eligible set is small (tens of thousands) — often faster *and* correct.
4. **ACL join outside the ANN**: retrieve candidates from a legal doc-ID set (boolean/BM25 on a permissioned index), then vector-rank that subset.
5. **Two-stage**: cheap metadata index (Postgres, inverted index) → IDs, then vector search those IDs (some engines support ID restriction).

I never enforce security only in the prompt (“you are not allowed to mention other tenants”). Filter is enforcement; prompt is theater.

**Weak answer.** “We just add a metadata filter for tenant_id. The DB handles it.”

**Follow-ups.**
- *What if a user can see 12 documents in a 20M corpus?* Do not ANN-then-filter. Search those 12 (exact) or filter a permissioned BM25 index first.
- *Time range filters?* Same selectivity issue. Partition by week/month for logs; do not HNSW a year of telemetry and post-filter `last 15 minutes`.
- *Why did recall drop after we added `status=published`?* Unpublished drafts were bridging the HNSW graph, or post-filter ate neighbors. Measure.

---

### Q10. Multi-tenant namespaces — how do you isolate customers?

**Why they ask.** SaaS RAG and enterprise assistants all have tenancy. This is a design question dressed as a vector-DB question.

**30s.** Three patterns: (1) metadata filter on one index, (2) namespace/collection/partition per tenant, (3) database-per-tenant. I pick by tenant count, size skew, compliance, and noisy-neighbor risk. Security isolation is a hard requirement; performance isolation is the reason I often pay for (2).

**2min.**

| Pattern | Pros | Cons |
| --- | --- | --- --- |
| Filter on shared index | Simple, cheap at small N | Filtered ANN pitfalls, noisy neighbor, blast radius |
| Namespace / collection / partition | Stronger isolation, easier deletes | Cardinality limits, ops overhead, cold tenants |
| Separate cluster / DB | Compliance, residency, customer-managed keys | Cost, migrations |

I use shared index + filter only when tenants are numerous and tiny and the engine’s filtered search is proven. I use namespaces when we have tens to thousands of tenants with uneven size. I use dedicated stores for regulated customers who contract for it. Deletes of a tenant must be **complete** (GDPR / contract): a metadata flag is not a delete. I prefer drop-namespace or `DELETE WHERE tenant_id` plus a rebuild if tombstones pile up.

**Senior.** Skew kills shared indexes: one tenant with 40% of vectors dominates RAM, caches, and HNSW shape. I split whales. I also split **by data class** (public knowledge vs customer private) so a filter bug cannot leak. For Postgres, RLS + `tenant_id` is a strong story if every query path sets the session variable — I demo that in FDE loops. For Pinecone-style namespaces, I know they are a product feature with cardinality limits; I do not promise a namespace per end-user in a 2M-user app. Per-user indexes are usually wrong; per-tenant plus doc-level ACL is right. I test isolation with a red-team query: user A asks for user B’s contract number.

**Weak answer.** “Each user has their own collection.” That will not scale, and you have not thought about shared corpora.

**Follow-ups.**
- *Noisy neighbor?* One tenant’s re-index saturates disk and p99 for everyone. Quotas, separate pods, or dedicated partitions for ingest.
- *Residency?* EU tenant vectors must not sit in a US index. Partition by region first, tenant second.

---

## 5. Hybrid search, BM25, sparse + dense

### Q11. Why isn’t vector search enough? Explain hybrid search.

**Why they ask.** Pure-vector RAG failing on SKUs, error codes, names, and policy IDs is the most common 2026 war story. Hybrid is the default architecture, not a bonus feature.

**30s.** Dense retrieval finds paraphrases and concepts. It is weak on rare tokens, IDs, exact quotes, and new jargon that was not in the embedding model. Lexical search (BM25 or learned sparse) nails those. Hybrid runs both, fuses ranks (usually RRF), then reranks. I ship hybrid unless the corpus is tiny or the queries are purely conceptual.

**2min.** Architecture: maintain a dense index and a lexical index on the same chunk IDs. Query → embed + tokenize in parallel → top 50–200 from each → **Reciprocal Rank Fusion**: `score(d) = Σ 1/(k + rank_i(d))` with k≈60 → take top 50 → cross-encoder rerank to 5–10 for the prompt. RRF avoids calibrating BM25 vs cosine. Learned sparse (SPLADE, BGE-M3 sparse, Elastic/OpenSearch ELSER-style, Pinecone sparse) can replace or complement BM25: still inverted-index fast, better on some synonyms. I keep BM25 even then for true exact match and operability. I log which branch contributed the cited chunk; that is how I know hybrid is earning its keep.

**Senior.** Fusion is not the finish line. A **reranker** (cross-encoder, or a small LLM-as-reranker with a token budget) is the highest-ROI quality lever after chunking. I treat rerank as mandatory for user-facing RAG once query volume can afford ~50ms extra. I also do **query rewriting** (HyDE, multi-query, split compound questions) *before* retrieval when evals show intent mismatch — but I cap extra embeddings because cost. Failure modes: hybrid can promote keyword-heavy junk; the reranker or a metadata prior (`recency`, `source_trust`) has to push it down. For agents, I expose `keyword` and `semantic` as tools only if the agent is evaluated; otherwise I hide one hybrid tool so the agent cannot pick the wrong branch. Eval sets must include **exact-ID queries** and **paraphrase queries** or you will overfit to one mode.

**Weak answer.** “We use vector search because it understands meaning. Keyword search is old.”

**Follow-ups.**
- *What is RRF?* Rank-only fusion, robust when scores are incomparable.
- *DBSF / weighted sum?* Needs score normalization. Use when you have calibrated weights from eval, not as a first default.
- *When is BM25 enough?* Strongly named corpora (catalogs, ticket IDs) with little paraphrase. Still add dense if users ask in natural language.
- *Does hybrid belong in the vector DB or the app?* If the engine has native hybrid (Qdrant, Weaviate, OpenSearch, Azure AI Search, Elastic), use it. If not (classic pgvector), run BM25 in Postgres `tsvector` or OpenSearch and fuse in the app. Do not add a second vendor just to get RRF.

---

### Q12. Walk through a hybrid query that must also obey ACLs.

**Why they ask.** Combines the two hard parts. This is a senior design probe.

**30s.** Resolve identity → expand groups to an allow-list of document IDs or classification labels → run dense + lexical **inside that allow-list** → fuse → rerank → pack citations that still pass ACL.

**2min.** I do not retrieve first and hope the filter works. Order:

1. AuthN (Entra / IAM / IdP). AuthZ from the source system (SharePoint perms, GitHub, DB RLS), cached as `doc_id → principals`.
2. Query-time: `legal_ids = ACL.expand(user)`. If `|legal_ids|` is small, exact-rank those chunks (BM25+cosine in Postgres) and skip global ANN.
3. If large, search partitions the user can see (tenant namespace) **and** apply `doc_id IN legal` or security-trimming (Azure AI Search) / attribute filters.
4. Hybrid + rerank on the surviving set.
5. Before sending to the LLM, re-check ACL on the final k (TOCTOU). Strip chunks that failed.
6. Citations only to surviving IDs. Audit log: user, query hash, chunk IDs.

**Senior.** The ACL system is the system of record, not the vector payload. Payload `allowed_groups` goes stale the day someone leaves a group. I prefer **query-time trim** against a periodically synced permission index, plus a short TTL cache. For 2026 enterprise, Azure AI Search security trimming and Google/Vertex permission-aware search exist so I do not rebuild this naively on Microsoft or Google corpora. On AWS I am more likely to compose OpenSearch with document-level security or a custom allow-list. I load-test the `IN (10k ids)` path; it is often fine, the `IN (2M ids)` path is not — then I need a bitmap or partitioned indexes by group. I will fail closed: empty retrieval, not unfiltered retrieval, on ACL errors.

**Weak answer.** “We store `user_id` in metadata and filter on it.” That is not how enterprise ACLs work.

**Follow-ups.**
- *What if ACL sync is 15 minutes behind?* Document that SLA. For high-sensitivity corpora, query the source perms live or accept deny-stale (removed access lags) vs allow-stale (the dangerous one). Prefer deny-stale.
- *Public + private mix?* Two indexes. Never rely on a filter to hide private from a public endpoint.

---

## 6. Honest product comparison (2026)

Interviewers may ask “Pinecone vs pgvector.” The trap is a feature matrix from memory. The pass is a **constraint-driven** comparison plus one weakness for each.

### Q13. Compare pgvector, Qdrant, Pinecone, Weaviate, Milvus, OpenSearch/Elasticsearch, and cloud search.

**Why they ask.** They want judgment and operating-model fit. Reciting stars on GitHub fails. Declaring a universal winner fails.

**30s.** I pick by data gravity, ops team, hybrid/filter needs, and scale. Default for most RAG under ~10M vectors on a team that already runs Postgres: **pgvector**. Dedicated engine when filters/hybrid/QPS demand it: **Qdrant** or **Weaviate**. Zero-ops SaaS: **Pinecone**. Billion-scale / GPU: **Milvus**. Existing search org or AWS-heavy keyword+vector: **OpenSearch/Elastic**. Cloud-native enterprise RAG next to the LLM platform: **Bedrock Knowledge Bases, Azure AI Search, Vertex AI Search** — not because they are the best ANN, but because identity, ingestion, and residency already live there.

**2min / Senior — honest matrix.**

| Store | What it really is | Wins when | Loses when | Interview caveat |
| --- | --- | --- | --- | --- |
| **pgvector** (Postgres) | Extension: `vector` / halfvec + HNSW/IVF, SQL, joins, RLS | You already run Postgres; metadata is relational; <~10M vectors (more with care / pgvectorscale); one unit of backup/IAM/tx | Very high QPS ANN, huge RAM graphs, fancy filtered HNSW, you need a search team’s BM25 relevance lab | Planner can ignore the HNSW index with a selective `WHERE`; `EXPLAIN ANALYZE` is the skill |
| **Qdrant** | Rust vector DB, HNSW, first-class payload filters, native sparse+dense | Filtered ANN, self-host or cloud, hybrid, strong single-binary ops | You want SQL joins; you need a fully hands-off SaaS with enterprise contracts already signed elsewhere | Best “dedicated vector DB” answer in many 2026 loops if you can run it |
| **Pinecone** | Managed serverless (and dedicated) vector service, namespaces | Small platform team, bursty scale, you will pay not to operate graphs | Data residency / VPC constraints; cost at high QPS; you already have search | Do not say “Pinecone is HNSW” as if you run it; you do not. Talk SLOs, namespaces, sparse-dense, cost |
| **Weaviate** | Vector DB with schema, hybrid, modules, GraphQL/REST | Hybrid + schema + multi-tenant product features; managed or self-host | Ops complexity if self-hosted poorly; overkill for a 50k-chunk bot | Mention hybrid and tenancy, not GraphQL as the reason |
| **Milvus** (Zilliz Cloud) | Distributed vector DB (Faiss/HNSW/DiskANN, GPU) | 100M–1B+ vectors, sharded cluster, GPU index build | You do not have a platform team; a 2M-chunk RAG does not need it | Naming Milvus for a startup RAG is a smell unless scale is real |
| **OpenSearch / Elasticsearch** | Search engines with BM25 + k-NN / neural sparse | You already operate them; hybrid + aggregations + analyzers; AWS OpenSearch + Bedrock is a common pair | Cluster ops; k-NN RAM; people treat them as “just a vector DB” and ignore text analysis | Best answer when the company is already a search shop |
| **Bedrock Knowledge Bases** | Managed RAG on S3 (+ web, Confluence, etc.), embeddings, vector store of your choice or managed, `Retrieve` / `RetrieveAndGenerate` | AWS-native, you want ingestion+chunking+citations without a platform project | You need custom chunking/eval/ACL beyond what KB offers; debugging the black box | Interviewers probe when you would *not* use it |
| **Azure AI Search** | Keyword + vector + semantic ranker + security trimming; backs Foundry IQ | M365/SharePoint/Entra estate; hybrid+semantic ranker as one query | Cost at small corpora; Azure lock-in if you are not already there | Hybrid + semantic ranker is the actual differentiator |
| **Vertex AI Search** / Gemini grounding | Managed enterprise search / RAG on GCP | BigQuery/GCS/Workspace gravity; grounding Gemini | Same: lock-in and black-box retrieval; custom ACL edge cases | Pair with Agent Platform, not as a pet ANN |

**How I say it in the room.** “If this company already has Postgres and 2 million chunks, I would not introduce Pinecone on day one. If they have 400 million vectors, 2k QPS, and a filter-heavy SaaS, I would not pretend RDS pgvector is a virtue. If they are an Azure shop with SharePoint ACLs, Azure AI Search is the default because of identity, not because HNSW is unique.”

**Weak answer.** “Pinecone is the industry standard.” Or a memorized 12-row feature table with no constraint.

**Follow-ups.**
- *pgvector vs Qdrant at 20M vectors?* Possible on pgvector with halfvec, enough RAM, and tuned HNSW — if QPS is modest and filters are partitions. Qdrant if filtered search and hybrid are the product. I would benchmark *their* QPS and filters, not Twitter anecdotes.
- *Can Bedrock KB use Aurora pgvector / OpenSearch / Pinecone?* Yes, KB can sit on several backends. The product you operate is still “managed ingest + retrieve,” with backend-specific limits.
- *Chroma / LanceDB?* Fine for local/dev, notebooks, edge. I do not propose Chroma as the enterprise multi-tenant store.
- *Redis / Valkey vector?* Good cache / session / low-latency feature store. Not my system of record for 50M documents.

---

### Q14. When do you use a cloud managed RAG (Bedrock KB, Azure AI Search, Vertex AI Search) instead of a vector DB you operate?

**Why they ask.** Cloud AI loops (Chapter 15) overlap here. They want you to avoid both “always build it ourselves” and “always use the wizard.”

**30s.** Use managed search when ingestion connectors, identity, citations, and ops matter more than index knobs. Operate your own when chunking, ACL, eval, or hybrid is the product and the managed path cannot express it.

**2min.** I start with the cloud’s RAG service in a brownfield enterprise: SharePoint → Azure AI Search, S3 + IAM → Bedrock KB, GCS/BigQuery → Vertex AI Search. I spike a 50-query eval. If recall/faithfulness is good enough and ACL works, I keep it and invest in evals/guardrails. I break out to pgvector/Qdrant/OpenSearch when we need custom chunkers (complex tables, code), document-level ACLs the connector cannot trim, multi-cloud portability, or index types the managed service hides. Hybrid is common: managed search for the 80% corpus, a specialist index for the 20% that is hard.

**Senior.** The hidden cost of managed RAG is **debuggability**. When a chunk is missing I need: source snapshot, chunk text, embedding model version, index time, filter applied. If the service does not export that, I cannot run an incident. I also watch **chunking opacity** and **re-index cost**. I refuse to promise “we will switch later” without an export path for IDs and metadata. For FDE work, I align with what the customer’s identity team will approve: Entra-trimmed Azure AI Search often beats a perfect Qdrant that cannot see SharePoint ACLs.

**Weak answer.** “Managed is always better in production.” Or “real engineers don’t use Knowledge Bases.”

**Follow-ups.**
- *Can you A/B managed vs custom?* Yes: same gold queries, same judge, freeze the corpus. Do not A/B on vibes.

---

## 7. Scale: 10k vs 10M vs 1B

### Q15. How does the design change at 10k, 10M, and 1B vectors?

**Why they ask.** They are testing whether you over-engineer a demo and under-engineer a platform.

**30s.** 10k: exact or default HNSW, pgvector, hybrid optional, evals matter more than the engine. 10M: HNSW in RAM or compressed, hybrid on, think about filters/partitions, backups, and ingest workers. 1B: sharding, quantization, disk-ANN/IVF-PQ, dedicated ops, ingest pipelines, hot/cold, you are running a search platform.

**2min / Senior.**

| Scale | Index | Hardware intuition | Ops | Typical store |
| --- | --- | --- | --- | --- |
| **10k** (pilot) | Exact or HNSW defaults | Fits a laptop | Migrations by rebuild | pgvector, local Qdrant |
| **~1M** | HNSW, measure `ef` | RAM-resident floats OK; watch cache | Ingest queue, idempotent upserts | pgvector / Qdrant / managed |
| **10M** | HNSW + int8/half; hybrid; partitions | Tens of GB RAM; p99 I/O if cold | Blue/green re-embed, filtered-recall evals, autoscale replicas | Qdrant/Weaviate/Pinecone/pgvectorscale/OpenSearch |
| **100M** | Shards, quantization, maybe DiskANN | RAM + SSD; rebuilds are projects | Dedicated search on-call | Milvus, OpenSearch, Pinecone dedicated, large Qdrant clusters |
| **1B** | IVF-PQ / DiskANN, GPU optional for build, multi-tier | Cluster, object storage for cold | Batch ingest, compaction, rebalancing, SLO burn | Milvus/Zilliz, large OpenSearch, specialist SaaS |

I also scale **QPS and ingest** independently. 10M vectors with 5 QPS is easy. 1M vectors with 5k QPS and 200-dimensional filters is not. **Update rate** is a third axis: a mostly-static corpus is a different system from a support-ticket index that mutates every second.

**Weak answer.** “We would use Milvus because it scales to billions” for a 30k-document internal bot.

**Follow-ups.**
- *How many GB is 10M × 1536-d float32?* \(10^7 \times 1536 \times 4 ≈ 61\) GB plus graph/payload. They want the back-of-envelope.
- *Replicas vs shards?* Replicas for QPS and HA. Shards for data size. Do not shard a 2GB index.

---

### Q16. Recall vs latency — how do you tune and talk about SLOs?

**Why they ask.** Seniors own a knob, not a myth of “both.”

**30s.** I set a quality bar (e.g. recall@20 ≥ 0.92 on the gold set, or “answer faithfulness ≥ X”) and a latency bar (e.g. retrieval p95 < 80ms). I use `efSearch` / `nprobe` / candidate depth / rerank depth as knobs. I do not max them. I report both numbers in the interview.

**2min.** Pipeline latency budget example for a 1.5s p95 chat SLO: embed query 30–80ms, hybrid retrieve 40–100ms, rerank 50–150ms, LLM 400–1200ms. Retrieval is rarely the majority unless the index is cold or unfiltered ANN is huge. So I do not “optimize HNSW” when the model is the budget. I *do* optimize when: p95 retrieve > 200ms, GPU embed queueing, or overfetch-for-filter exploded. I keep two configs: `interactive` (tight ef, k=20, rerank 50) and `deep` (agent research path, k=100, rerank 100, higher cost).

**Senior.** I plot recall vs p95 and pick the knee. I also plot **filtered** recall vs p95, which is the one users feel. I cap reranker batch size. I cache query embeddings and popular result lists with a short TTL for identical questions (careful with ACL in the cache key). I never cache across tenants. If the LLM is streaming, I can start generation after a first-pass retrieve and skip rerank on easy queries (router). That is a quality risk I eval.

**Weak answer.** “We need maximum recall and sub-10ms search.” Pick one, or pay for hardware.

**Follow-ups.**
- *k vs recall?* Retrieving k=5 is brittle. Retrieve more, rerank, send 3–8 chunks. Context stuffing hurts generation more than a missing 9th chunk sometimes — another eval.

---

### Q17. Updates, deletes, and re-indexing.

**Why they ask.** Demos only insert. Production mutates.

**30s.** Upserts must be idempotent on chunk ID. Updates are delete+insert of that document’s chunks. Deletes are first-class (tombstones + compaction). Re-embed is a dual-write or blue/green collection switch with eval gates.

**2min.** Document update: load new bytes → chunk with the same chunker version → hash chunks → write new IDs, delete IDs no longer present. I avoid “append forever” because stale chunks still retrieve. HNSW deletes are often **marked deleted** and still occupy RAM; I schedule optimize. For legal delete (tenant offboarding, GDPR), I need a path that is queryable-absent, not merely “flagged.” Rebuilds: I build collection `v_n+1` in the background, run eval, switch the alias, keep `v_n` until rollback window ends.

**Senior.** High-churn (messages, tickets) wants an index that likes inserts (IVF with small residuals, or partitioned-by-time HNSW) plus a compaction story. I separate **hot mutable** and **cold static** corpora so a Wikipedia-like dump is not compacted with chat logs. Write amplification: embedding APIs will rate-limit a naive 10M re-embed; I use batch APIs, backoff, checkpointed jobs, and I embed only changed bytes (content hash). I store `model_id` and `chunker_id` on every row so a mixed-version index is detectable. Consistency: if the app DB commits and the vector write fails, I have an outbox / queue, not two uncorrelated writes.

**Weak answer.** “We just upsert vectors.” No identity, no tombstones, no dual-write.

**Follow-ups.**
- *Eventual consistency window?* I state it. Search can lag the source by N seconds. Users who “just uploaded” need a read-after-write path (search that file directly).
- *Why did deleted docs still appear?* Tombstone not applied, CDN/cache, or the parent doc still had another chunk.

---

## 8. Why search got slow after 1M documents

### Q18. “It was fine at 100k. At 1M, p95 went from 20ms to 800ms. Why?”

**Why they ask.** This is the troubleshooting form of the scale question. They want an investigation order, not a vendor switch.

**30s.** At ~1M the working set often stops fitting in RAM/cache, ANN parameters that were “exact-ish” get expensive, filters start post-filtering huge candidate sets, and ingest contention shows up. I check: is it slow because of **I/O**, **CPU distance computations**, **lock/WAL** (Postgres), **overfetch**, or **the embedding call** misattributed to search?

**2min.** Ordered debug:

1. **Measure the right span.** Query embed vs ANN vs filter vs rerank vs network. Many “vector DB is slow” incidents are the embedding API.
2. **`EXPLAIN` / engine explain.** Is pgvector sequential scanning? Did the planner pick the wrong index because of `WHERE tenant_id =`?
3. **Working set.** RSS vs RAM. After 1M × 1536-d, vectors + graph may be 8–10GB+; on a 8GB box you swapped. Cloud “serverless” may be cold-starting.
4. **efSearch / k too high.** Defaults that were fine at 100k now walk too much graph.
5. **Filter.** Post-filter overfetch at 1M is brutal. Tenant with 0.1% of data.
6. **Payload fetch.** Returning 2KB text × 100 hits over the network.
7. **Locking / compaction / merge** (ingest during query).
8. **GC / noisy neighbor / CPU steal.**
9. **Quantize or partition**, then re-measure recall.

**Senior.** The 1M cliff is often **memory hierarchy**, not algorithmic Big-O. HNSW is ~log n * ef; n going 10× should not be 40× slower if RAM-resident. When it *is*, I assume cache miss, disk, or filter. Fix pattern: **partition by tenant or time**, **compress to int8**, **cap ef**, **pre-filter via partition**, **replica for query vs ingest**, **don’t store fat payloads in the hot index**. Hot/cold: last 90 days in RAM HNSW; older in compressed IVF or object-store + batch. I add SLOs and a load test *before* 1M, with production-like filters, not unfiltered random vectors.

**Weak answer.** “HNSW doesn’t scale past a million, we need Milvus.” False as a general claim.

**Follow-ups.**
- *Would sharding help at 1M?* Usually no. Fix RAM, filters, and planner first.
- *Why is the second query fast?* Page cache / JIT / connection warmup. Cold p95 is what users hit after autoscale.

---

### Q19. Hot/cold tiers and partitioning.

**Why they ask.** This is the grown-up version of Q18.

**30s.** Not all vectors deserve RAM. Hot: recently used, recently ingested, or high-value corpora. Cold: archive, rarely retrieved, compressed or even re-embedded on demand. Partition so queries only touch relevant slices (time, tenant, source).

**2min.** I partition on the filter we always have: `tenant_id`, `created_at` month, `corpus`. A query for “this week’s tickets for tenant A” should never walk last year’s graph. Hot tier: HNSW int8 in RAM. Warm: mmap / DiskANN. Cold: object storage + sparse index, or “rehydrate this project on demand.” Routing is application logic or the engine’s partitions. I keep a small **global** index of titles/summaries so “search everything” still works without loading cold vectors.

**Senior.** Partitioning is a product decision: what is the unit of retrieval? Time-based partitions need a query router (“how far back?”). Too many partitions (one per customer in a 50k-tenant free tier) will wreck file descriptors and memory. I bucket small tenants into shared shards and give whales dedicated ones (the Vitess idea, applied to vectors). Rebalancing is the hard part; I design for it (hash ranges, not “folder per tenant on disk” without a plan). For RAG, cold data might be cheaper to **leave in the source** (SharePoint, S3) and search via the platform connector when needed, instead of vectorizing 10 years of mail.

**Weak answer.** “We’ll put everything in one collection and add metadata for date.” That is how you get the 1M cliff.

**Follow-ups.**
- *Rebalancing live?* Dual-write a new partition map, copy, switch router, delete old. Same as any sharded store.
- *Embeddings of cold data stale?* Yes. Re-embed on rehydrate, or accept a frozen model on archive.

---

## 9. Scenario questions (use these in mocks)

### Q20. Design retrieval for an enterprise assistant over 80M chunks, 400 tenants, SharePoint + wiki + tickets.

**Why they ask.** System design with vectors. They want ACL, hybrid, and partition, not a logo.

**30s.** Identity first. Per-tenant partitions. Hybrid search. Separate indexes per source type if chunkers differ. Managed search if the identity plane is Azure/Google; otherwise OpenSearch/Qdrant + ACL service. Eval set per source. Rerank. Citations.

**2min.** Requirements I force out: latency SLO, languages, whether tickets mutate, residency, and whether users can see only their sites. Then: Entra/IAM-authenticated gateway → ACL expand → route to tenant partition → hybrid retrieve (wiki semantic-heavy, tickets lexical-heavy) → rerank → generate with citations. Ingest: queue workers, incremental, content-hash. Tickets in a hot time-partitioned index. SharePoint ACLs synced frequently; fail closed.

**Senior.** I would not put 80M chunks in one HNSW and filter `tenant_id`. I would not vectorize every ticket attachment on day one. I would put a **source router** (small classifier or metadata) so code-search is not mixed with HR policy. I would budget re-embed. I would show a failure mode: ACL sync lag, and another: one whale tenant. Evals: 100 queries per source type with labeled chunks. Cost: embedding + rerank + storage; I would int8 the cold wiki.

**Weak answer.** “Put it all in Pinecone with metadata.”

**Follow-ups.** They will change a constraint: EU-only, or 2k QPS, or “legal hold, nothing deleted.” Adapt the partitions and the delete path.

---

### Q21. We swapped embedding models and quality collapsed. Diagnose.

**Why they ask.** Change-management of the embedding contract.

**30s.** Mixed-space index, wrong metric, forgot to re-embed queries, instruction prefix change, dimension truncate, or eval set too small. I check model IDs on a retrieved row vs query path.

**2min.** Dump five queries: old neighbors vs new. If IDs are random, it is space mismatch. If they are shifted but plausible, it may be calibration; check downstream thresholds. Confirm query-side model. Confirm normalization. If dual-write was partial, some tenants are on v1. Roll back the alias while re-embedding.

**Senior.** I treat embedding upgrades like database migrations: expand/contract, not in-place. Feature flag the query model. I keep a canary tenant. I never “re-embed in place” without a snapshot.

**Weak answer.** “The new model is worse; go back forever.” Maybe, but first prove you are not in a mixed index.

**Follow-ups.** *Can two models coexist?* Yes, two collections or two fields (`vec_v1`, `vec_v2`) and a query pointer.

---

### Q22. Filtered search returns nothing for a customer who definitely has documents.

**Why they ask.** Filtered ANN + ACL.

**30s.** Post-filter overfetch too small, wrong tenant key, ACL deny, empty partition, or the filter field not indexed / type mismatch (`"123"` vs `123`).

**2min.** Reproduce with the customer’s identity. Count docs matching the filter without ANN (`COUNT(*) WHERE tenant_id=`). If count > 0, ANN+filter is the bug: switch to partition scan or exact on that tenant. If count = 0, ingest or ACL. Check case sensitivity and timezone on date filters.

**Senior.** Add a **fallback**: if filtered ANN returns < k and eligible count is below a threshold, exact search that subset. Alert on zero-hit rate by tenant.

**Weak answer.** “Increase k to 10,000.” That is a tax, not a design.

**Follow-ups.** *Could this leak if we disable the filter to debug?* Yes. Debug on a replica with synthetic data, not by removing ACL in prod.

---

## 10. Rapid-fire (30–45 seconds each)

Use these in Chapter 31 drills.

| Prompt | Target answer |
| --- | --- |
| Why pin the embedding model? | Vectors are only comparable inside one model/version/metric. |
| HNSW `M` vs `efSearch`? | `M` is build-time graph degree (rebuild to change). `efSearch` is query-time beam (no rebuild). |
| When is exact kNN correct *and* fast? | Eligible set is small (thousands), or corpus is tiny. |
| Cosine after L2-normalize equals? | Dot product ranking (and L2 ranking). |
| RRF in one sentence? | Combine rank lists without calibrating raw scores. |
| Why BM25 still? | IDs, SKUs, exact rare tokens, new jargon. |
| Namespace vs metadata filter? | Namespace = physical isolation; filter = predicate on a shared graph. |
| Tombstone? | Soft delete in HNSW; RAM and recall suffer until compacted. |
| First lever at 10M RAM pressure? | int8/halfvec, drop unused payload, partition, then PQ. |
| Security of retrieval? | ACL in the query path, fail closed, never prompt-only isolation. |
| Why not one vector per document? | Long docs mix topics; retrieve at chunk granularity, expand parent. |
| What is a collection alias? | Pointer you flip for blue/green re-index. |
| DiskANN in one sentence? | Graph ANN laid out for SSD; billion-scale without full RAM. |
| Why eval on *our* queries? | Vendor recall is unfiltered, no ACL, wrong domain. |
| Biggest 1M slowdown? | Working set left RAM, or filter post-processing, or planner missed index. |

---

## 11. Keywords interviewers listen for

embedding contract · dimension · re-embed · ANN · recall@k · HNSW · `M` · `efSearch` · IVF · `nprobe` · PQ · int8 · cosine vs IP vs L2 · normalize · pre-filter · post-filter · filtered ANN · overfetch · namespace · RLS · BM25 · sparse · dense · RRF · rerank · hybrid · tombstone · partition · hot/cold · p95 vs recall · pgvector · Qdrant · Pinecone · Weaviate · Milvus · OpenSearch · Azure AI Search · Bedrock KB · Vertex AI Search

If you say those in a structured answer, you sound like you have shipped. If you only list vendors, you sound like you have read landing pages.

---

## 12. Honest boundaries (say this rather than bluffing)

You do not need to have operated a billion-vector Milvus cluster. You do need to say:

> “I have not run 1B vectors in production. At that scale I would expect sharding, quantization, and a dedicated search team. I *have* [or: I would] measure recall@k, filtered recall, and p95, and I know HNSW RAM math and filter failure modes from [X]. I would not pick Milvus for a 50k-document pilot.”

Never invent “we used DiskANN at 2B vectors” if you indexed 8 PDFs in a notebook.

---

## 13. How this chapter connects

- **Chapter 10 RAG** — chunking, citations, evals, when retrieval is the failure.
- **Chapter 15 Cloud AI** — Bedrock KB, Azure AI Search, Vertex AI Search, identity, residency.
- **Chapter 16 Docker/K8s** — running Qdrant/OpenSearch, GPU embedding workers, ingest queues.
- **Chapter 19 Security** — OWASP vector/embedding weaknesses, tenant isolation, prompt injection via retrieved docs.
- **Chapter 20–21 Design** — enterprise assistant problems assume this material.

Drill: pick one vendor your JD names, and answer Q13 in 90 seconds **for that constraint set**. Then answer Q18 out loud with an investigation order.
