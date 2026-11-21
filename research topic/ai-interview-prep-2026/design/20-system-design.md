# 20 — How to Run an AI System Design Interview

**What this chapter is for:** so you walk a 45-minute AI design loop the way a senior engineer walks a design review — requirements first, numbers second, boxes third, evals and failure modes before anyone asks.

This is not a catalog of architectures. Chapter 21 has the problems. This chapter is the operating system you run on every problem: ChatGPT-for-docs, RAG, coding assistants, gateways, agents, AIOps, security monitoring. Same 17 steps. Different constraints.

If you only remember one sentence: **interviewers are not hiring you to name Pinecone. They are hiring you to decide what not to build, prove the rest works, and keep it cheap, private, and recoverable.**

---

## What the interviewer is actually scoring

An AI system design loop looks like classic distributed-systems design with four extra axes that did not exist in 2018: **tokens, identity-aware retrieval, evaluation, and model unreliability.**

| Signal | How you show it in 45 minutes | How you fail it |
| --- | --- | --- |
| Requirements discipline | You ask 6–8 clarifying questions before drawing | You start with LangGraph |
| Production judgment | You name QPS, corpus, p95, cost/query, ACL | Happy-path boxes only |
| AI-specific taste | Hybrid retrieval + rerank + citations + eval harness as defaults | “Just embed and cosine” |
| Safety | Identity-aware retrieval, HITL on writes, tenant isolation | Multi-tenant index with no filter |
| Measurement | Offline eval, online traces, regression gates | “We’ll look at user feedback” |
| Cost | Model routing, cache, context budgets | Frontier model on every token |
| Communication | Time-boxed, interruptible, labeled boxes | Monologue until minute 40 |
| Seniority | Trade-offs, what you would cut at 10×, failure story | Component shopping list |

**INTERVIEWER SIGNAL:** If they let you talk for 12 minutes without interrupting, they are often waiting to see whether you will *invite* constraints. Candidates who never pause to confirm assumptions score as junior even when the architecture is fine.

**MARKET OBSERVATION:** Evaluation is under-mentioned in JDs (~4.5% explicit in the January 2026 AI Engineer set) and over-weighted in on-sites. A design without an eval harness is treated as a demo, not a system.

---

## The 17-step framework

Use this in order. Skip a step only after you have named it and said why it is out of scope for *this* prompt. Interviewers forgive a thin data model. They do not forgive never mentioning ACL, evals, or cost.

Each step below answers three things: **what you do, why the step exists, what a strong sentence sounds like.**

```
 1 Clarify requirements
 2 Functional requirements
 3 Non-functional requirements
 4 Estimate scale
 5 Define APIs
 6 Data model
 7 High-level architecture
 8 Components
 9 Data flow
10 Scalability
11 Reliability
12 Security
13 Observability
14 Evaluation
15 Cost
16 Trade-offs
17 Failure handling
```

You will not spend equal time on all 17. You will *touch* all 17. Time-boxing is later in this chapter. First, why each step is there.

---

### 1. Clarify requirements

**What you do.** Repeat the prompt in one sentence, then ask questions that change the architecture. Do not ask questions that only make you look thorough.

**Why this step exists.** AI prompts are underspecified on purpose. “Design ChatGPT for our documents” can mean a read-only RAG chatbot, a write-capable agent with Jira tools, a multi-tenant SaaS, or an air-gapped legal assistant. The architecture for those four systems is not the same. Clarifying is how you avoid building the wrong one and how you show you have shipped.

**Questions that actually change the design:**

- Who is the user? Employee, customer, operator, developer, auditor?
- Read-only Q&A, or can it take actions (send email, merge PR, restart a pod)?
- One tenant or many? Same corpus or isolated corpora?
- What is the corpus: Confluence, tickets, code, PDFs, logs, PII?
- Latency budget: interactive chat (p95 < 5s), batch, or streaming first token?
- Must answers cite sources? Must they refuse when retrieval is empty?
- Human-in-the-loop on writes, or autonomous inside a policy box?
- Cloud / VPC / on-prem? Data residency?
- What happens on wrong answers — annoyance, lost money, safety incident?

**Strong sentence.** “I am going to assume an internal, identity-aware, read-only assistant over 50 million enterprise documents with citations required and no tool writes in v1. If writes are in scope I will add HITL and a separate action plane. Does that match what you want?”

**Weak sentence.** “So… like ChatGPT but with our files?”

Never invent a requirement silently. State the assumption, invite a correction, write it on the board.

---

### 2. Functional requirements

**What you do.** List 5–8 things the system *must do*, in user language, then star the ones that drive architecture.

**Why this step exists.** Interviewers use FR as a contract. If you later skip citations after listing “must cite,” they notice. If you never listed citations, they assume you forgot. Functional requirements also stop you from boiling the ocean: v1 vs v2 is a senior move.

**Template (almost every 2026 AI product):**

| ID | Requirement | v1 / v2 | Architecture driver |
| --- | --- | --- | --- |
| F1 | Authenticated user asks a question in natural language | v1 | Gateway, identity |
| F2 | Answer grounded in permitted documents only | v1 | ACL at retrieval |
| F3 | Citations with document, span, and permission check | v1 | Chunk IDs, rerank |
| F4 | Streaming tokens to the client | v1 | SSE / WS, cancel |
| F5 | Conversation memory within a session | v1 | Thread store |
| F6 | Explicit “I don’t know” when evidence is weak | v1 | Grounding policy |
| F7 | Tool / write actions with HITL | v2 unless stated | Action plane |
| F8 | Admin evals, traces, prompt/version rollback | v1 | LLMOps |

**Strong sentence.** “v1 is retrieval-grounded Q&A with citations, streaming, and refuse-on-low-evidence. Multi-agent orchestration and write tools are v2 unless you need them today — they change the trust boundary.”

**Why not dump 20 features.** You will not design 20 features in 45 minutes. Five well-chosen FRs beat a product-manager laundry list.

---

### 3. Non-functional requirements

**What you do.** Put numbers on latency, availability, freshness, quality, tenancy, and compliance. If the interviewer did not give numbers, propose them and ask.

**Why this step exists.** NFRs are where AI design diverges from “it works in the notebook.” A 200ms cache hit and a 12-second uncached RAG call are both “answers.” Only one is a product. NFRs also force you to pick a model class (small/fast vs large/smart) before you fall in love with a frontier API.

**Default NFR table you can reuse:**

| Axis | Interactive assistant default | Batch / RCA default | Why it matters |
| --- | --- | --- | --- |
| Latency | p50 TTFB < 800ms, p95 full answer < 8s | minutes OK | Streaming vs batch architecture |
| Availability | 99.9% query path | 99.5% OK | Multi-model failover |
| Freshness | docs searchable < 15 min after edit | hourly | Incremental index vs nightly |
| Quality | groundedness ≥ 0.9 on eval set; citation precision ≥ 0.95 | task-specific | Eval harness, not vibes |
| Tenancy | hard isolation of vectors + files + traces | often single-tenant | Index design, keys |
| Security | identity-aware retrieval, no cross-tenant leak | same | Filter *before* prompt |
| Cost | target $ / successful answer | $ / incident | Routing, cache |
| Retention | prompts/traces per policy (30–90d typical) | longer for audit | Store design |

**Strong sentence.** “I will treat p95 end-to-end under 8 seconds, 99.9% query availability with a degraded ‘search-only’ mode, 15-minute index freshness, and zero-tolerance for cross-ACL leakage. Quality is a first-class NFR: we ship behind an eval gate, not a demo.”

If you cannot name an NFR, you cannot later justify Redis, a reranker GPU, or two regions.

---

### 4. Estimate scale (QPS, corpus size, tokens, cost, storage)

**What you do.** Spend 3–5 minutes on back-of-envelope math. Round aggressively. Show the *method*.

**Why this step exists.** Scale is how you choose between “Postgres + pgvector on one primary” and “sharded hybrid index plus embedding workers.” Token math is how you show you will not bankrupt the company. Interviewers listen for whether you convert users → QPS → tokens → dollars, and documents → chunks → vectors → disk.

**Worked method (say this out loud):**

1. **Users and QPS.** 10k DAU, 8 queries/user/day → 80k queries/day → ~1 QPS average, ~10–20 QPS peak if traffic is 2-hour-spiky. Design the query path for 50 QPS to have headroom. Ingestion is a different number.
2. **Corpus.** 10 million docs, avg 8 pages, ~2k tokens/doc after extraction → 20B tokens raw. Chunking at 500 tokens with 50-token overlap → ~50M chunks.
3. **Vectors.** 50M chunks × 1024-dim float32 × 4 bytes ≈ 200 GB vectors before replicas and HNSW graph overhead. Plan 3–5× for graph + metadata + text → ~1 TB search cluster. Hybrid BM25 is extra inverted-index disk, usually smaller than dense.
4. **Embedding cost (ingest).** 20B tokens / 1M × $0.02 (example small embedding price) is a *budget line*, not a footnote. Call out incremental re-embed vs full re-embed when the model changes.
5. **Query tokens and cost.** Per query: retrieve 50 chunks → rerank to 8 → 8 × 400 tokens context = 3.2k prompt tokens + 400 completion + system prompt 800 ≈ 4.5k tokens. At a mid model $0.40 / $1.60 per 1M in/out, that is roughly $0.002–$0.01 per query before cache. At 80k queries/day that is $160–$800/day. A frontier model at 10× input price is a different product.
6. **Storage besides vectors.** Raw blobs, extracted text, conversation threads, traces, eval sets. Traces can exceed the corpus if you log full prompts. Budget them.

**Strong sentence.** “Peak 50 QPS, 50 million chunks, ~1 TB hybrid index, about half a cent per uncached answer on a mid-size model. Cache and routing are cost features, not niceties. I will not put a 405B model on the default path.”

**What interviewers ding.** Forgetting that metadata + text + HNSW ≫ raw float32. Forgetting output tokens. Forgetting that re-embedding 50M chunks is a project, not a flag flip.

Write the numbers on the board. You will point at them when you pick caches, queues, and model routing.

---

### 5. Define APIs

**What you do.** Sketch 4–7 endpoints or RPC methods. Include auth context, streaming, and the action/HITL APIs if writes exist. Keep payloads explicit enough that data model follows.

**Why this step exists.** APIs force you to decide the contract before the boxes. They surface missing pieces: cancel, feedback, citation click-through, admin reindex, eval run. They also show you think in products, not notebooks.

**Default query API:**

```
POST /v1/conversations
  { tenant_id, user_id, metadata }

POST /v1/conversations/{id}/messages
  { content, stream: true, tools_allowed?: [] }
  -> SSE: token | citation | tool_call | tool_result | done | error

POST /v1/messages/{id}/feedback
  { rating, comment, expected_doc_ids? }

GET  /v1/messages/{id}/citations
GET  /v1/conversations/{id}
```

**Default ingest API:**

```
POST /v1/sources
POST /v1/sources/{id}/sync          # webhook or crawler tick
POST /v1/documents:batchUpsert
POST /v1/indexes/{id}:rebuild
GET  /v1/indexes/{id}/status
```

**Default action / HITL API (only if writes are in scope):**

```
POST /v1/actions/{id}/approve
POST /v1/actions/{id}/deny
GET  /v1/actions?status=pending
```

**Auth.** Every call carries tenant, user, and a token that the retrieval layer can turn into a permission predicate. Do not bury identity only in the LLM prompt.

**Strong sentence.** “The query API is a streaming message endpoint that emits tokens, citations, and optional tool events on one SSE stream so the client can render incrementally and cancel. Ingest is a separate authenticated surface. Approvals are a different API with a different audit log.”

Mention idempotency keys on ingest and action APIs. Mention that internal tool APIs never go to the browser.

---

### 6. Data model

**What you do.** List the entities, the keys, and what is *not* in the vector store.

**Why this step exists.** Most RAG outages are metadata outages: missing ACL, missing version, missing checksum, missing tenant_id. The data model is where you prove you will not dump blobs into a vector DB and hope.

**Entities that show up in almost every design:**

| Entity | Key | Payload | Store |
| --- | --- | --- | --- |
| Tenant | tenant_id | plan, region, retention, model policy | OLTP |
| Principal | user_id / service_id | groups, roles | IdP / OLTP |
| Source | source_id | connector type, cursor, secrets ref | OLTP + secret manager |
| Document | doc_id, version | URI, hash, mime, owner, ACL list, status | object store + OLTP |
| Chunk | chunk_id | doc_id, version, span, text, tokens, ACL copy | search index + text store |
| Embedding | chunk_id + model_id | vector, model version | vector index |
| Thread | conversation_id | user, tenant, created | OLTP |
| Message | message_id | role, content, model, token counts | OLTP / cheap blob |
| Citation | message_id + chunk_id | score, span, verified_acl | OLTP |
| Trace | trace_id | spans, prompts (redacted), scores | observability store |
| EvalCase | case_id | query, allowed docs, gold answer, tags | eval store |
| Action | action_id | tool, args, status, approver | OLTP + audit log |

**Rules you should say:**

- ACL is stored on the document *and* denormalized onto chunks so retrieval can filter without a join in the hot path.
- `model_id` lives with the vector. Mixing embedding models in one index is a silent quality incident.
- Raw files stay in object storage. The index holds text + vectors + metadata.
- Conversation memory is *not* stuffed into the vector index by default. Session store first; long-term memory is a later, dangerous feature.
- Traces are isolated per tenant and redacted. They are production data, not debug leftovers.

**Strong sentence.** “The vector index is not the source of truth. Object store plus an OLTP catalog are. Chunks carry tenant_id, principal ACL, doc version, and embed_model_id so retrieval can be identity-aware and so we can rebuild one model version without corrupting another.”

---

### 7. High-level architecture

**What you do.** Draw 6–10 boxes, left to right, ingest on top or left, query on the bottom or right. Label arrows with the data that moves.

**Why this step exists.** This is the picture the interviewer will photograph in their head when they write the packet. If the picture is a vendor collage, you look junior. If the picture is a dataflow with a trust boundary, you look senior.

**Default 2026 picture (boxes, not logos):**

```
                    +------------------+
   Connectors  ---> | Ingest workers   | ---> Object store
   (drive, git,     | parse, chunk,    | ---> OLTP catalog
    tickets, logs)  | ACL snapshot     |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Hybrid index     |
                    | BM25 + dense     |
                    | ACL fields       |
                    +--------+---------+
                             ^
                             | retrieve
+----------+    +------------+-------------+    +----------------+
| Client   |--->| API gateway / LLM gateway|--> | Query orchestrator |
| stream   |    | auth, quota, route,      |    | rewrite, retrieve, |
+----------+    | policy, tracing          |    | rerank, generate,  |
                +------------+-------------+    | cite, ground       |
                             |                  +--------+---------+
                             v                           |
                    +------------------+                 v
                    | Model router     | <----->   Frontier / mid / local
                    | cache, fallback  |           embedding + rerank + LLM
                    +------------------+
                             |
                             v
                    +------------------+     +------------------+
                    | Thread + audit   |     | Eval + traces    |
                    +------------------+     +------------------+
```

Say out loud: **MCP gateway is optional, not mandatory.** If tools exist, an MCP or internal tool gateway sits behind the orchestrator with allowlists. Do not start the drawing with MCP. Start with identity, retrieval, generation, and policy.

**Strong sentence.** “Two planes: ingest and query, sharing a catalog and a hybrid index. All model calls go through a gateway so I can route, budget, trace, and fail over. Retrieval is identity-aware. Generation never sees a chunk the user could not fetch directly.”

---

### 8. Components

**What you do.** Zoom into each box: responsibility, input, output, failure mode, scaling axis. Two sentences per component, not a vendor review.

**Why this step exists.** High-level architecture proves you can decompose. Components prove you have operated the pieces. This is where you earn mid-level. Seniors keep going into data flow and evals.

**Component cheat sheet (reuse, then specialize):**

| Component | Does | Does not | Scale by |
| --- | --- | --- | --- |
| API gateway | Authn, TLS, tenancy, rate limit, request ID | Business logic | Horizontally, per region |
| LLM gateway | Model routing, keys, budgets, fallback, provider health | Prompts as source of truth | Per-model pools |
| Orchestrator | DAG or loop: rewrite → retrieve → rerank → generate → ground | Long-running jobs | Stateless workers + queue |
| Parser / chunker | MIME-specific extract, PII flags, structure-aware chunks | “split every 500 chars” as a religion | Worker pool, per source |
| Hybrid retriever | BM25 + dense, ACL filter, recency | Reranking | Shards, replicas |
| Reranker | Cross-encoder or LLM rerank top 50 → 5–10 | Replace retrieval | GPU or small-model pool |
| Generator | Grounded answer, structured citations | Tools by default | Streaming connections |
| Grounding checker | Entailment / citation overlap / refuse | Perfect truth | Inline, cheap model |
| Action broker | Tool allowlist, sandbox, HITL | Direct network from the model | Isolated egress |
| Eval service | Offline suites, canaries, regression gates | A spreadsheet | Batch jobs |
| Trace collector | Spans, token counts, retrieved IDs | Unredacted secrets | Cheap object + index |

When you name a technology, name the *job* first: “a hybrid search cluster — could be Elasticsearch + a dense index, or a single engine that does both — I care that BM25 and dense share ACL filters.”

---

### 9. Data flow (ingestion vs query; agent loop)

**What you do.** Walk one write path and one read path with a concrete example. If the product is an agent, walk one loop iteration including stop conditions. Do not wave your hands.

**Why this step exists.** Boxes without a walkthrough hide the bugs: ACL applied after generation, tools called before retrieval, memory written unfiltered, retries that double-bill. Interviewers who have been paged will listen for the order of operations.

**Ingest path (say it as a sequence):**

1. Connector emits `document_changed(doc_id, version, acl)`.
2. Worker fetches bytes, stores raw in object storage, records hash.
3. Parser extracts text/tables/images; PII detector tags spans.
4. Chunker splits on structure (headings, functions, ticket fields) with overlap.
5. Each chunk inherits `tenant_id`, ACL principals, `doc_version`, `embed_model_id`.
6. Embed async; write dense vector + BM25 posting + metadata atomically enough that query never sees half a document (versioned aliases or `visible=false` until complete).
7. Catalog marks document searchable; old version retired after TTL.

**Query path:**

1. Gateway authenticates, attaches `principal` and `tenant`.
2. Orchestrator may rewrite the query (hyDE / multi-query) *without* leaking other tenants.
3. Retriever runs hybrid search **with ACL filter in the query**, not after.
4. Rerank the allowed set only.
5. Pack context with a token budget; drop low-score chunks; include citation IDs.
6. Generate with a groundedness instruction; stream tokens.
7. Post-check: every citation ID still ACL-valid; if generation refers to missing IDs, strip or refuse.
8. Persist message, citations, token counts, trace. Return `done`.

**Agent loop (only if tools are in scope):**

```
state = {goal, budget_steps, budget_tokens, tools_allowlist}
while not done and steps < N and tokens < T:
    plan = model(state)           # or a cheaper planner
    if plan.action is write:
        create HITL ticket; wait or fail closed
    if plan.action is retrieve:
        identity-aware retrieval
    if plan.action is tool:
        policy check → sandbox → timeout → result
    observe, append to state (truncate)
    if grounding failed or policy denied: stop
emit answer + trace + audit
```

Say the stop conditions: max steps, max tokens, max wall clock, policy deny, user cancel, low confidence. Infinite ReAct loops are a junior tell.

**Strong sentence.** “Ingest and query are separate pipelines sharing a versioned catalog. ACL is a retrieval predicate, not a prompt instruction. If we add tools, the loop is budgeted and writes are HITL; I will not default to a multi-agent swarm.”

---

### 10. Scalability

**What you do.** Pick the bottleneck at the scale you estimated, and say how each hot component scales. Mention what *breaks first* at 10×.

**Why this step exists.** This is classic system design, still required. AI-specific bottlenecks are embedding backfill, context packing CPU, GPU rerank, provider rate limits, and trace volume — not just web QPS.

**Talk through four axes:**

| Axis | Technique | Watch-out |
| --- | --- | --- |
| Query QPS | Stateless orchestrators, index replicas, gateway cache of exact+semantic queries | Semantic cache can leak across ACL if keyed wrong |
| Corpus size | Shard index by tenant or hash(doc_id); tier hot vs cold | Cross-shard hybrid merge; ACL field on every shard |
| Ingest burst | Queue + workers; backpressure; snapshot isolation | A 10M-doc connector crawl must not starve query embeds |
| Model capacity | Routing, batch embeddings, provisioned throughput, local small models | Provider 429s are a first-class load problem |
| Context | Hard token budgets, rerank, map-reduce only when needed | “Stuff top 50 chunks” dies at quality *and* cost |

**10× question (they will ask).** “If DAU goes 10×, I scale replicas on the query path first, then provisioned model capacity, then shard the index. I do *not* 10× the frontier model bill — I raise cache hit rate, push more traffic to a mid model, and keep the frontier for hard queries. If corpus goes 10×, I shard and introduce collection-level routing so we do not run global ANN on everything.”

Name one thing you would **not** scale: multi-agent chatter, full-document prompts, re-embedding the world on every parser tweak.

---

### 11. Reliability

**What you do.** Define SLOs, degradation modes, and dependency failure.

**Why this step exists.** LLMs fail *openly*: hallucinations, timeouts, partial streams, provider outages. Reliability is not only “three replicas.” It is “what does the user see when the generator is dead but search is alive?”

**Degradation ladder (memorize this):**

1. **Full RAG + generate** (healthy).
2. **Skip rewrite and rerank** if those services time out; retrieve + generate still works, quality dips, latency holds.
3. **Extractive mode:** return cited snippets, no generation.
4. **Cached last-known answers** for frequent queries (ACL-keyed).
5. **Fail the request** with a typed error; never silently answer from the model’s parametric memory on an enterprise corpus.

**Other reliability points that score:**

- Dual model providers or a local fallback for the gateway.
- Queue retries with idempotency on ingest; exactly-once is hard, **at-least-once + version hash** is honest.
- Circuit breakers on tool egress.
- Blue/green index aliases for rebuilds.
- Cancellation: if the user hits stop, cancel the model call so you do not pay for abandoned tokens.

**Strong sentence.** “Availability SLO is on the query API, not on a single model vendor. If the LLM is down we degrade to cited extractive search. If the index is down we fail closed, because answering from the base model would violate the grounding requirement.”

---

### 12. Security

**What you do.** Walk the trust boundary: identity, ACL, prompt injection, data egress, tenancy, secrets, HITL.

**Why this step exists.** This is the highest-severity miss in 2026 loops. A beautiful RAG that retrieves another tenant’s payroll is a firing offense, not a follow-up. OWASP GenAI LLM Top 10 2026 is the vocabulary; you do not need to reciting all ten, but you must hit injection, data leakage, unbounded agency, and supply chain (tools/MCP).

**Non-negotiables to say:**

- **Identity-aware retrieval.** Filter in the search query using the principal’s groups. Never retrieve then hope the LLM ignores forbidden chunks.
- **Citations re-checked** against ACL before render.
- **Prompt injection.** Retrieved text is *data*, not instructions. Delimit it. Do not let documents set tool policy. Strip or ignore “ignore previous instructions” in retrieved content at the policy layer, not by hoping the model behaves.
- **HITL on writes.** Email, code merge, prod mutation, ticket close — queued for a human unless a tightly scoped playbook says otherwise.
- **Tenant isolation.** Separate encryption keys where the product requires it; at minimum `tenant_id` on every row, every index, every cache key, every trace. No shared semantic cache across tenants.
- **Secrets.** Model keys and connector tokens in a secret manager. Tools get short-lived scoped credentials, not the user’s God-mode token.
- **Egress.** Tool gateway allowlists hosts. MCP, if used, sits behind the same gateway: allowlisted servers, authenticated, audited. MCP is optional; unfiltered MCP is a vulnerability.
- **PII / residency.** Region pin; prompt/trace redaction; retention jobs.
- **Abuse.** Rate limits per principal; jailbreak classifiers on input; output filters for the domain (PII, malware in a coding assistant, medical over-claim).

**Strong sentence.** “Security is a retrieval problem first, a tool-policy problem second, and a prompt-wording problem last. I will not mitigate ACL with instructions to the model.”

---

### 13. Observability

**What you do.** Name traces, metrics, logs, and the debug question they answer.

**Why this step exists.** You cannot improve a stochastic system you cannot see. LLMOps interviews are often folded into design: “the bot got worse on Tuesday — what do you look at?” If you did not instrument retrieved chunk IDs, you cannot answer.

**Minimum viable observability for an AI system:**

| Signal | What it tells you |
| --- | --- |
| Trace per request (OpenTelemetry-style spans) | rewrite / retrieve / rerank / generate / tools with timestamps |
| Retrieved chunk IDs + scores + ACL decision | retrieval vs generation blame |
| Token in/out per model, $ estimate | cost incidents |
| TTFB, p95, queue depth, provider 429s | latency incidents |
| Grounding score, refuse rate, citation click | quality |
| Cache hit rate (keyed by tenant+acl+query hash) | cost and leakage risk |
| Tool success / deny / timeout | agent reliability |
| Index lag by source | freshness |
| Eval suite delta vs last release | regressions |

**Logs are not traces.** Do not say “we’ll log everything.” Full prompt logs are a compliance incident. Redact, sample, encrypt, tenant-isolate.

**Strong sentence.** “Every answer has a trace_id the support engineer can open: query, rewritten queries, chunk IDs, ACL filter, rerank scores, model, token counts, grounding score. If we cannot blame retrieval vs generation, we cannot debug.”

---

### 14. Evaluation

**What you do.** Design the harness as part of the system, not a later project. Offline + online + release gate.

**Why this step exists.** This is the 2026 differentiator. Candidates who draw eight microservices and no eval set lose to candidates who draw four boxes and a golden set of 400 labeled queries with citation F1. Interviewers use evals as a proxy for “has shipped.”

**Say this structure:**

1. **Gold set.** 200–2000 real queries (anonymized), each with: allowed doc IDs, must-cite IDs, forbidden doc IDs (ACL traps), gold answer or key facts, tags (simple, multi-hop, adversarial injection, empty-corpus).
2. **Retrieval metrics.** Recall@k, nDCG, ACL leak rate (must be 0 on trap cases).
3. **Answer metrics.** Groundedness / faithfulness, citation precision/recall, exactness, refusal correctness, toxicity/PII.
4. **Agent metrics** (if tools). Task success, extra tool calls, HITL miss rate, policy-violation rate, steps-to-done.
5. **Online.** Thumbs, citation clicks, edit distance of user corrections, escalation rate, shadow eval on live traffic.
6. **Release gate.** CI runs the gold set on every prompt, chunker, or model change. Quality drop > threshold blocks deploy. Canary 5% traffic.
7. **LLM-as-judge** is a *component* of eval, not the whole eval. Calibrate against humans; keep a human-labeled core.

**Strong sentence.** “I will not ship a prompt change that is not gated on retrieval recall, citation precision, ACL leak = 0, and cost per query. User thumbs are a lagging indicator.”

If you skip this step, skip any hope of a senior packet.

---

### 15. Cost

**What you do.** Point back at step 4. Show the levers. Pick a default model class.

**Why this step exists.** Token cost is the COGS of these products. Designs that always call the most expensive model read as amateur. Designs that ignore embedding backfill read as never-operated.

**Levers, in the order you should pull them:**

| Lever | Effect | Risk |
| --- | --- | --- |
| Prompt + context budget | Linear on every query | Over-truncation hurts recall |
| Hybrid + rerank so you send 5 chunks not 30 | Large | Under-retrieve |
| Exact and semantic cache (ACL-keyed) | Huge on FAQs | Stale or leaky cache |
| Model routing (small / mid / frontier) | Huge | Misroute hard queries |
| Distilled or local model for rewrite/classify/rerank | Medium | Quality of auxiliaries |
| Batch embeddings, smaller embed model | Ingest bill | Rebuild cost if you change models |
| Speculative decoding / provisioned throughput | Latency and unit price | Lock-in |
| Do not multi-agent the happy path | Avoid 5× tokens | Over-simple for hard tasks |

**Strong sentence.** “Default path is a mid-size model with 5–8 reranked chunks and an ACL-keyed cache. Frontier is a route for low-confidence or high-value tenants, not the default. Agents do not get to call tools in a loop without a token budget.”

Put a number on the board: “uncached $0.006, cached $0.0004, target blended $0.002.” Wrong numbers are OK. Missing numbers are not.

---

### 16. Trade-offs

**What you do.** Pick 3–4 real forks you considered and say what you chose. Do not list fake trade-offs (“SQL vs NoSQL”) that do not affect this problem.

**Why this step exists.** Senior engineers are paid to choose. Mid engineers are paid to implement a choice. If every option is “we could do either,” you have not designed.

**High-signal forks in 2026 AI designs:**

| Fork | Choose A when | Choose B when |
| --- | --- | --- |
| Workflow vs agent | Steps known, tools few | Steps unknown, research/ops exploration |
| Single agent vs multi-agent | One goal, one policy box | Distinct skills *and* you can eval each |
| Chunk small vs large | Precise citation, code, tickets | Narrative PDFs, need surrounding context |
| Fine-tune vs prompt+RAG | Stable style/schema, lots of labels | Corpus changes weekly, need citations |
| Shared index + ACL field vs index-per-tenant | Many small tenants, ops simplicity | Large tenants, residency, noisy neighbor |
| Extractive vs generative | Legal/compliance, high precision | Synthesis across many docs |
| MCP for tools vs internal tool API | Heterogeneous external tools, partners | First-party tools, stricter control |
| Local / VPC model vs frontier API | Air gap, PII, cost at scale | Quality on hard reasoning, time-to-market |

**Strong sentence.** “I am choosing a workflow with optional tools over a multi-agent graph because the happy path is retrieve-rerank-generate, which is a DAG. I will not pay multi-agent coordination tax until a named task needs it. If legal requires extractive answers, I will drop generation on that tenant.”

Invite disagreement: “I would flip this if the interviewer wants write-heavy ops.” That is not weakness; that is design under constraints.

---

### 17. Failure handling

**What you do.** Name concrete failures, user-visible behavior, and how you repair. Close the interview here if time is short — it leaves a senior aftertaste.

**Why this step exists.** Happy-path architecture is a take-home. Failure handling is the on-call interview hiding inside the design loop. AI systems fail in ways unique to them: hallucinations with high confidence, retrieval of the wrong ACL, embedding model mismatch, agent loops, poison documents.

**Failure catalog you should be able to rattle off:**

| Failure | Detection | Response |
| --- | --- | --- |
| Provider 429 / 5xx | Gateway health, error budget | Retry with jitter, fail over model, degrade extractive |
| Hallucinated citation | Post-check IDs against retrieved set | Strip or refuse; log as eval miss |
| Empty retrieval | Recall, chunk count = 0 | “I don’t know”; optionally web/tool if allowed |
| ACL miss (too few docs) | User with broad perms vs narrow | UX: not found, not “access denied” leaking existence if policy says so |
| ACL leak | Eval trap cases, audit | Page, rewind index, kill cache |
| Poison / injected doc | Classifier, canary queries | Quarantine source, reindex |
| Agent loop | Step/token/time budget | Kill, return partial + trace |
| Write tool error | Tool span status | Compensating action or HITL; never retry blindly on payments |
| Stale index | Source lag metric | Show freshness badge; boost recency; backfill |
| Embed model mixup | model_id mismatch checks | Block query against wrong index alias |
| Cost spike | $ / min anomaly | Shed to cheaper model, disable rewrite, raise cache |
| Partial stream drop | Client disconnect | Cancel generation; do not bill silently if you can avoid |

**Strong sentence.** “Fail closed on permission and grounding; fail over on model vendors; fail partial on agents. I will not retry a mutating tool without idempotency, and I will not answer from parametric memory when retrieval is empty.”

---

## Time-boxing a 45-minute interview

You will not finish a textbook design. You will finish a *defensible* one. The packet is written in the last ten minutes of the interviewer’s memory. Budget like this:

| Minutes | Step | Output on the board |
| --- | --- | --- |
| 0–4 | Clarify (1) | Users, writes?, tenancy, corpus, latency, HITL |
| 4–8 | FR + NFR (2–3) | 5 FRs, 5 NFRs with numbers |
| 8–12 | Scale (4) | QPS, chunks, TB, $ / query |
| 12–16 | APIs + data model (5–6) | 5 endpoints, 8 entities |
| 16–26 | Architecture, components, data flow (7–9) | One picture, ingest vs query (vs loop) |
| 26–34 | Scale out, reliability, security (10–12) | 10×, degrade ladder, ACL + injection |
| 34–40 | Observability, eval, cost (13–15) | Trace fields, gold set, routing |
| 40–44 | Trade-offs + failure handling (16–17) | 3 forks, 4 failures |
| 44–45 | Recap + invite follow-ups | “Where do you want to drill?” |

**If they interrupt at minute 6 with “just draw it.”** Draw the high-level picture, then *backfill* FR/NFR/scale in one minute while pointing at boxes. Do not fight the interviewer for the agenda. Do not skip ACL and evals even if they rushed you.

**If they want depth on one box at minute 20.** Park the framework: “I will deep-dive retrieval; I am parking evals and cost and will return if time.” Then actually return. Parking without returning looks like you forgot.

**If you are mid-level and freeze on time.** Cut components to the six that matter: gateway, ingest, hybrid index, orchestrator, model router, eval/trace. A complete thin design beats an incomplete beautiful ingest pipeline.

**If you are senior.** Spend extra minutes on security, evals, cost, and what you would cut. Do not spend extra minutes on the chunker algorithm unless they ask.

Practice this with a timer. The first three times you will hit minute 45 still drawing the index. That is the practice; the interview is not the practice.

---

## How to draw (boxes, not logos)

The whiteboard is a communication tool, not a vendor exhibition.

**Do:**

- Rectangles, arrows, labels. Six to ten boxes. One trust boundary (dashed line) around model + tools.
- Label arrows: `chunks + ACL`, `top 50`, `SSE tokens`, `approve/deny`.
- Write numbers on the side: `50 QPS`, `50M chunks`, `$0.006/q`.
- Separate ingest (top) from query (bottom) so data flow is visible.
- Write `fail closed` on the ACL filter and `HITL` on the write path.
- If you need a vendor as an example, put it in parentheses: `hybrid index (OpenSearch / pgvector / proprietary)`. The box name stays a job.

**Do not:**

- Draw the LangChain / LangGraph / CrewAI logo and sit down.
- Draw eight vector-DB logos as if the design is a bake-off.
- Draw a neural net.
- Write “AI magic” or a single “LLM” box that also does ACL, tools, and storage.
- Fill the board so there is no room for failure modes.
- Copy a blog architecture you cannot defend.

**A drawing is done when** a new engineer could implement a walking skeleton from it: they know the request path, the stores, and the policy checkpoints.

If the interview is virtual, use the tool they provide. Do not apologize for ugly boxes. Ugly and labeled beats pretty and vacant.

---

## How to invite follow-ups

Senior candidates run a conversation. Mid candidates deliver a TED talk.

**Tactics:**

- After clarifying: “I’ll lock those assumptions; please kick me if you want writes in v1.”
- After the picture: “I can drill retrieval, the agent loop, or tenant isolation — which is highest value for you?”
- After a number: “I’m using $0.40 / 1M input as a mid-model placeholder; the shape of the design does not change if the price is 2×.”
- When you skip multi-agent: “I’m deliberately not starting with a swarm. Happy to design the supervisor if the task is open-ended ops.”
- At minute 40: “Three places I’d drill in a real design review: ACL cache correctness, eval gate false positives, and provider failover. Want one?”

**Why this works.** Interviewers have a hidden rubric. Inviting them to pick the drill lets them score the dimension they care about. It also prevents you from spending 15 minutes on chunk overlap while they wanted gateway tenancy.

**What not to do.** “That’s all I have” at minute 22. “Any questions?” with a shrug. Both read as empty.

If they stay silent, self-drill: pick the riskiest part of *your* design and attack it. “The dangerous bit is semantic cache vs ACL. Here’s how I’d key it…” That is senior.

---

## Senior vs mid answers

Same 17 steps. Different altitude.

| Dimension | Mid-level (what they want) | Senior (what they want) |
| --- | --- | --- |
| Clarifying | Asks 4 reasonable questions | Asks the questions that *fork* the design; states v1 vs v2 |
| Scale | Rough QPS | QPS + tokens + $ + disk + 10× bottleneck |
| Architecture | Correct RAG/agent boxes | Two planes, gateway, policy checkpoints, degradation |
| Retrieval | Embeddings + vector DB | Hybrid + rerank + ACL filter + citations + versioning |
| Agents | Can draw ReAct | Budgeted loop, HITL on writes, when *not* to use agents |
| Security | AuthN on the API | Identity-aware retrieval, injection, tenant keys, tool egress |
| Evals | “We’d measure quality” | Gold set, ACL traps, CI gate, LLM-as-judge calibrated |
| Cost | Mentions tokens are expensive | Routing table, cache keys, blended $ target |
| Trade-offs | Lists options | Chooses, names what is sacrificed, names the revert trigger |
| Failure | Retries | Fail closed vs fail over vs fail partial; poison docs; cancel |
| Communication | Completes a tour | Time-boxes, invites drills, leaves a recap |
| Ownership | “We would…” | “I would ship v1 as… I would refuse to ship if…” |

**Mid-level winning packet:** a working system, hybrid retrieval, basic ACL, some tracing, honest “I haven’t operated this at 50M chunks but here is how I’d start.”

**Senior winning packet:** the above, plus eval harness as a product surface, cost as a design input, threat model, 10× plan, and a clear “we are *not* doing multi-agent / fine-tuning / MCP in v1 because…”

**Architect / FDE winning packet:** the above, plus customer constraints (residency, existing IdP, existing search cluster, change management), rollout, and how you would say no to a stakeholder who wants autonomous prod restarts on day one.

Do not fake seniority by name-dropping. Fake seniority is “we’ll use a multi-agent MCP mesh on Bedrock AgentCore with a custom reranker.” Real seniority is “v1 is a DAG with identity-aware hybrid search; here is the SLO and the eval gate.”

---

## Common fail modes

These are the rejection patterns. Memorize them as negative tests for your own practice.

### Jumping to LangChain (or LangGraph, CrewAI, ADK, “just use Bedrock Agents”)

**What it looks like.** Minute 1: “I’d use LangGraph with a supervisor and Pinecone.” Minute 15: still listing integrations.

**Why it fails.** Frameworks are implementation details. They do not encode ACL, evals, cost, or failure. Interviewers hear “I have completed tutorials.”

**Fix.** Job names first, optional framework in parentheses, plus “I would not mind writing the DAG in plain Python if the workflow is retrieve-rerank-generate.”

### Skipping evals

**What it looks like.** Beautiful boxes. “Quality would be monitored via user feedback.”

**Why it fails.** User feedback is late, sparse, and missing ACL traps. 2026 hiring uses evals as a shipped-or-not proxy.

**Fix.** Gold set, retrieval + grounding + ACL leak metrics, CI gate, online canary. Put `eval service` on the board.

### Skipping ACL / identity-aware retrieval

**What it looks like.** One index to rule them all. “The prompt says only use the user’s documents.”

**Why it fails.** Models do not enforce security. This is a data-leak design.

**Fix.** ACL on chunks, filter at query time, re-check citations, tenant on every cache key, trap cases in the gold set.

### Multi-agent by default

**What it looks like.** Supervisor, researcher, critic, writer, all for “ask a question about a PDF.”

**Why it fails.** You multiplied cost, latency, and failure modes without a task that needs it. 2026 senior taste: **prefer workflows over agents unless the steps are unknown.**

**Fix.** Start with a DAG. Promote to a single budgeted agent if tools and unknown plans exist. Multi-agent only when specialists have separate evals, tools, and policies.

### Other high-frequency misses

| Fail mode | Fix |
| --- | --- |
| Fine-tune first | RAG + prompts + evals; fine-tune when the task is stable and citations are not the point |
| Dense-only retrieval | Hybrid is the 2026 default; keywords still win on SKUs, error codes, names |
| No rerank | Top-k from ANN is not a context pack; rerank |
| No citations | Enterprise answers without spans are rumors |
| No HITL on writes | Action plane + approve API |
| MCP mandatory | Optional tool gateway; allowlisted; not the architecture |
| Stuffing chat history into the vector DB | Session store; long-term memory is a threat model |
| One giant context window instead of retrieval | Cost, latency, and lost-in-the-middle |
| Ignoring ingest | Query-only designs rot in a week |
| Vendor bake-off as the design | Pick jobs; mention 1–2 examples |
| No token budget on agents | Infinite loops, infinite bills |
| Semantic cache without ACL in the key | Cross-user leakage |
| Logging full prompts forever | Compliance incident |
| “The LLM will refuse” as a safety control | Policy engine + retrieval filters + tool allowlists |
| Drawing logos, talking until minute 45, no recap | Time-box; leave failure modes on the board |

If you catch yourself in one of these live, say so: “I jumped to a framework. Let me restart from requirements.” That recovery scores better than doubling down.

---

## 2026 defaults (unless the interviewer forbids them)

Internalize these so you do not waste clarifying questions on settled taste. Override them when the domain demands it (air-gap, ultra-low latency, extractive legal).

1. **Hybrid retrieval** (BM25 + dense), not dense-only.
2. **Rerank** top 50 → 5–10 before generation.
3. **Citations** with document + span, verified against ACL.
4. **Eval harness** as a product surface: gold set, CI gate, online traces.
5. **Identity-aware retrieval**; ACL is a query filter.
6. **HITL on writes**; read-only v1 unless the prompt is an action system.
7. **Model routing** through an LLM gateway: small / mid / frontier / fallback.
8. **Tracing** with retrieved IDs, token counts, and $ .
9. **Tenant isolation** on indexes, caches, traces, keys.
10. **MCP gateway optional**, never mandatory; if present, allowlisted and audited.
11. **Workflows over agents; single agent over multi-agent** until proven otherwise.
12. **Fail closed** on grounding and permission; **fail over** on vendors.

Say the defaults in 20 seconds at the start of the architecture step so the interviewer can disagree early.

---

## A 90-second opening you can reuse on any prompt

Do not memorize a script. Memorize the *shape*:

> “I’ll clarify, lock FR/NFR, do scale math, then draw ingest vs query with a gateway, hybrid retrieval, rerank, citations, and an eval harness. v1 is read-only unless you need actions — if actions, HITL. I’ll keep agents as a budgeted loop, not a swarm, and MCP as optional. I’ll end on ACL, failure modes, and cost. First questions: who is the user, what may it write, one tenant or many, and what’s the blast radius of a wrong answer?”

Then ask the clarifying questions. Then shut up and listen.

---

## Worked skeleton (same framework, tiny example)

Prompt: “Design an internal Q&A bot over company docs.”

You do **not** start with a vector DB. You do this:

1. **Clarify.** Internal employees, read-only, 20k staff, Slack + web, citations required, Confluence + Google Drive + PDFs, 15-minute freshness, no customers in v1.
2. **FR.** Ask, stream, cite, refuse, session, feedback, admin reindex.
3. **NFR.** p95 < 8s, 99.9%, ACL leak = 0, groundedness ≥ 0.9, US residency.
4. **Scale.** 20k × 6 q/day ≈ 1.4 QPS avg, 15 QPS peak; 5M docs → ~20M chunks; ~400 GB index; ~$0.004/q uncached.
5. **APIs.** SSE messages, feedback, ingest webhook, rebuild.
6. **Data model.** Tenant=corp, principal from Okta groups, documents, chunks with ACL, threads, traces, eval cases.
7. **Architecture.** Connectors → ingest workers → object store + hybrid index; Slack/web → gateway → orchestrator → router.
8. **Components.** As in the cheat sheet; reranker in the query path; no action broker in v1.
9. **Flow.** ACL-filtered hybrid → rerank 8 → generate with citations → post-check IDs.
10. **Scale.** Replicas; shard later; cache FAQ.
11. **Reliability.** Degrade to extractive; dual model vendors.
12. **Security.** Group ACL on chunks; injection-resistant packing; no tool egress.
13. **Observability.** Traces with chunk IDs; index lag; $ / query.
14. **Eval.** 400 gold queries including ACL traps and “ignore previous instructions” docs.
15. **Cost.** Mid model default; frontier on low-confidence; cache.
16. **Trade-off.** No fine-tune; no multi-agent; shared index with ACL field because one tenant.
17. **Failure.** Empty retrieval → I don’t know; poison Confluence page → quarantine source.

That skeleton, spoken with numbers, already beats most candidates. Chapter 21 expands it into thirteen full problems.

---

## How interviewers probe (and how to answer without collapsing)

Expect these after your picture. Answer in 30–60 seconds, then offer to go deeper.

| Probe | They are testing | Shape of the answer |
| --- | --- | --- |
| “Why not just a 1M-token context?” | Cost, lost-in-the-middle, ACL | Retrieval + rerank; long context is a complement for the already-allowed set |
| “User says the answer is wrong.” | Debug order | Trace: retrieval empty vs wrong vs generation; check ACL, lag, chunking, eval tag |
| “How do you stop prompt injection from a PDF?” | Security taste | Retrieved = data; no tool policy from documents; allowlists; maybe quarantine |
| “Can we let it close incidents?” | HITL, agency | Not in v1; if yes, scoped playbooks + approve API + audit + sim env |
| “Pinecone vs pgvector vs OpenSearch?” | Whether you worship vendors | Hybrid + ACL + ops; pick from existing stack; name trade-offs |
| “Add ten more data sources.” | Ingest architecture | Connector interface, per-source parsers, shared catalog, backpressure |
| “It has to be air-gapped.” | Model routing, local evals | Local models, no egress, same retrieval/eval design |
| “Show me the schema.” | Data model seriousness | Chunk ACL, model_id, version, tenant_id |
| “What’s the SLO?” | Production | Query availability, freshness, grounding, leak = 0, p95 |
| “Multi-agent would be more robust, right?” | Hype resistance | Only if specialists are independently eval’d; otherwise more failure modes |

If you do not know a vendor API, say so and stay on the job: “I don’t remember that product’s exact replica syntax; I need a hybrid index with ACL filters and <80ms p50 retrieve.”

---

## Practice protocol for this chapter

1. Pick any Chapter 21 prompt. Set a 45-minute timer. Whiteboard or blank file.
2. Speak out loud. Silence is not practice.
3. Score yourself only on: Did I clarify? Numbers? ACL? Evals? Cost? Failure? Time-box?
4. Note which fail mode you entered (LangChain, swarm, skip evals).
5. Re-run the same prompt 48 hours later. The framework should feel boring. Boring is the point.

Do not memorize Chapter 21 answers. Memorize this chapter’s order, the 2026 defaults, and the degrade ladder. Generate the design in the room.

---

## Recap card (the only thing to memorize)

**Order:** Clarify → FR → NFR → Scale (QPS, chunks, tokens, $, disk) → APIs → Data model → Picture → Components → Ingest vs query vs loop → Scale-out → Reliability → Security → Observability → Evals → Cost → Trade-offs → Failures.

**Defaults:** hybrid, rerank, citations, eval harness, identity-aware retrieval, HITL on writes, model routing, tracing, tenant isolation, MCP optional, workflows before agents.

**Draw:** boxes and jobs, not logos. Numbers on the side. Trust boundary around model and tools.

**Talk:** time-box 45 minutes. Invite drills. Senior = what you will not build, how you know it works, how it fails, what it costs.

**Never:** LangChain first, evals never, ACL in the prompt, multi-agent by default.

Next: [21-architecture-problems.md](21-architecture-problems.md) — thirteen problems. Cover the answer. Run the 17 steps. Then read the ideal narrative.
