# Core 20 — Full Interview Answers

These twenty questions appear, in some wording, in a large majority of 2026 applied AI loops. Learn them as **concept + structure + keywords**, not as scripts.

For each: what they test, 30-second, 2-minute, senior extension, weak answer, follow-ups.

---

## Q1. What is RAG?

**Testing:** Why retrieval exists; that you will not dump a corpus into the context window and call it architecture.

**Structure:** WHAT → WHY → HOW (ingest vs query) → EXAMPLE → TRADE-OFF.

**30-second**

RAG retrieves relevant pieces of external knowledge and places them in the model context so the answer can use private, current, citable information the weights may not contain. Ingestion chunks and embeds documents; query-time we retrieve, optionally rerank, then generate with instructions to stay grounded. The new failure mode is retrieval quality, not just prompting.

**2-minute**

Two paths. **Ingest:** parse, chunk with overlap or structure, embed, store vectors **and metadata** (source, ACL, time). **Query:** rewrite if conversational, embed the query, **hybrid** lexical + dense, fuse (RRF), rerank, pack context, generate with citation instructions, optionally verify claims against chunks. Use RAG when knowledge changes, is private, or must be cited. Do not use it to count or summarize an entire corpus.

**Senior**

Production RAG is an ACL-aware search system plus a generator. You version the index and the prompt together, measure recall@k and faithfulness separately, and treat retrieved text as **untrusted** (indirect injection). Multi-tenant means filters or namespaces **before** similarity, not after generation. Scale: ANN (HNSW/IVF), not brute-force cosine.

**Weak:** “RAG connects LLMs to documents.”

**Follow-ups**

| Follow-up | Strong reply |
| --- | --- |
| Why not fine-tune? | Fine-tune changes *behavior* (style, format). Wikis change weekly and need citations. Fine-tune last, often with RAG still in front. |
| Which vector DB? | Start from constraints: metadata filters, hybrid, ops, VPC. pgvector if Postgres is already the system of record and scale is modest; Qdrant/Milvus for heavy filter+ANN; managed Pinecone/OpenSearch if ops budget is the bottleneck. |
| How do you eval retrieval? | Golden queries with labeled sources. Recall@k, MRR, nDCG. Do not only score the final answer. |
| How do you secure docs? | Identity in the retrieve call; document ACLs as metadata; no cross-tenant cache keys; audit. |
| How reduce hallucinations? | Grounding instructions, refuse if retrieval weak, citations, faithfulness check, don’t overstuff context. |

---

## Q2. Walk me through a production RAG pipeline.

**Testing:** Real components, not a blog diagram.

**30-second**

Offline: connectors → parse (including tables) → clean → chunk → embed → index with metadata → version. Online: authn → query rewrite → hybrid retrieve → rerank → context assemble (budget tokens) → LLM → cite → post-filter (PII, policy) → log trace.

**Senior extras they want named:** dedup, incremental updates, tombstone deletes, embedding-model freeze, canary index, eval in CI, prompt cache with tenant-safe prefixes, fallback when retrieval empty.

**Weak:** “LangChain loads PDFs into Pinecone and ChatGPT.”

---

## Q3. How do you choose chunking?

**Testing:** Content-dependent judgment and measurement.

**30-second**

Chunking is not a universal 512 tokens. Prefer natural structure (headings, functions, rows) first; fall back to recursive character/token split with 10–20% overlap; use semantic splits for unstructured prose if you can measure a gain. Always A/B on recall@k. Small chunks: precise, easy to miss multi-sentence answers. Large chunks: more context, noisier retrieval, more tokens.

**Senior:** special cases — tables (don’t split a row), code (function/class), legal (clause), slide decks (one slide + title). Parent-child / small-to-big retrieval: retrieve small, expand to parent. Measure; a chunking change can move recall 10–20 points.

**Weak:** “I always use 1000 characters with 200 overlap.”

---

## Q4. BM25 vs embeddings. When hybrid?

**Testing:** Production retrieval literacy.

**30-second**

BM25 wins on exact IDs, error codes, names, rare tokens. Dense wins on paraphrase. Production default is **both**, union of top-k, **RRF**, then a **cross-encoder reranker** to top 5–10. Hybrid routinely beats either alone.

**Follow-up — skip rerank?** Only if p95 budget cannot afford 20–50ms and quality bar is low. For enterprise Q&A, rerank is usually worth it.

---

## Q5. Retrieval is right, the answer is still wrong. What do you inspect?

**Testing:** Isolation of retrieval vs generation. Highest-value debug question in 2026.

**Structure:** OBSERVE → ISOLATE.

**2-minute investigation order**

1. Confirm “right document” is actually in the **packed context**, not just retrieved at rank 27.
2. Rank position: need rerank if gold is at 15.
3. Chunk fragment: the answer span was split; try parent expansion.
4. Context stuffing / lost-in-the-middle: too many chunks, gold in the middle.
5. Prompt: model not instructed to prefer context over parametric memory.
6. Ablation: same question with/without retrieval. If identical, the model is ignoring context.
7. Conflicting chunks / stale index.
8. Generator too small or temperature too high for a factual task.
9. Faithfulness checker would have caught it — add one.

**Weak:** “I’d tune the prompt” as the only step.

---

## Q6. How do you evaluate a RAG / LLM feature?

**Testing:** The 2026 hiring differentiator. No numbers = no ship.

**30-second**

Split **retrieval** and **generation**. Retrieval: recall@k, MRR on a golden set of 50–200 real queries with labeled sources. Generation: faithfulness, answer relevance, citation validity. Online: thumbs, task success, escalation rate, $/query, p95. Ship bar is numeric and written before the project, not after.

**Senior**

Three buckets in the eval set: production sample, adversarial (injection, out of scope, multi-intent), regression (known breaks). LLM-as-judge only after calibration to humans; watch position and verbosity bias; prefer a different model family for judging. Prompts and indexes are versioned; CI fails the deploy on metric drop. Agents add trajectory metrics: tool correctness, loops, cost per successful task.

**Weak:** “We’d look at quality and get user feedback.”

**Follow-up — evals flat, users angry?** Distribution mismatch. Sample live traffic into the set. Rubric missing tone/length. Traffic shifted.

---

## Q7. RAG vs fine-tuning vs prompting?

**Testing:** Decision tree, not a preference.

**Recommend**

1. Prompting first (cheapest iteration).
2. RAG when facts are external, changing, or must be cited.
3. Fine-tune (often LoRA) when you need stable **behavior**: format, tone, tool-use style, or a smaller model to replace a large prompted one.
4. Combine: RAG for knowledge, light SFT for style.

**Do not fine-tune a wiki.** You will retrain every update and still lack citations.

---

## Q8. What is an agent vs a workflow? When not to use an agent?

**Testing:** Anti-hype. Senior signal.

**30-second**

A workflow’s control flow is in code; the model fills steps. An agent chooses the next tool from observations until a stop condition. Use agents only when the step sequence is unknown. If you can write the process on a whiteboard, use a workflow. Agents cost more, are harder to eval, and have a larger blast radius.

**When not:** known business process; tight latency; irreversible actions without HITL; you cannot eval task success; you just wanted a chatbot.

**Weak:** “Agents are more advanced so we should use them.”

---

## Q9. How do you stop an agent looping?

**Testing:** Production agents, not ReAct slides.

**Defense in depth**

1. Hard max steps and max tokens / $ per task.
2. Repeat detector: same tool + same args twice → break and escalate.
3. Better tool errors so the model can change strategy.
4. Progress summary every N steps.
5. Timeouts per tool; circuit breaker.
6. Trace-driven taxonomy (loop vs bad schema vs bad planner).

**Weak:** “I’d prompt it not to loop.”

---

## Q10. How do you design tools? How do you validate calls?

**Testing:** API design for a non-human client + don’t trust the model.

**30-second**

Treat tools like public APIs: clear names, minimal args, excellent descriptions, structured returns, idempotent writes where possible, useful errors. Few tools beat 30 overlapping ones; at scale retrieve top-K schemas. **Always** validate against JSON schema and policy **before** execution. The model is not an authorization layer.

**Senior:** allowlists, per-tool IAM, dry-run, HITL on write, argument sanitization (no shell concat), rate limits, audit every call.

---

## Q11. What is MCP? Why not just function calling or REST?

**Testing:** Protocol literacy without cargo cult.

**30-second**

MCP is an open standard (Anthropic → Linux Foundation, late 2025) for exposing **tools, resources, and prompts** from a **server** to an AI **host** via a **client**. JSON-RPC. Use it when many apps must share the same integrations. Function calling is the in-app mechanism for one model runtime. REST is how tools talk to backends. MCP does **not** replace RAG.

**Security follow-up:** tool poisoning (malicious tool descriptions), token leakage in context, shadow servers, over-broad scopes, missing audit. Enterprise: MCP **gateway** — authn, allowlist, pin versions, inspect schemas, log, sandbox.

---

## Q12. Why five agents instead of one? When is multi-agent overkill?

**Testing:** Restraint.

**30-second**

Add agents for **genuine specialization** (retriever vs coder vs policy checker) or **parallelism**. Each extra agent multiplies cost, latency, failure modes, and handoff loss. A supervisor plus four workers is often a slower, more expensive single agent. Prefer a graph with typed nodes. If you cannot name a failure that specialists prevent, it is overengineering.

**Handoffs must carry:** goal, evidence, authority, accountability.

---

## Q13. How would you implement enterprise access control in RAG?

**Testing:** Whether you will leak tenant B’s data. Career-ending miss.

**Senior design**

- Authenticate the user (SSO). Resolve groups.
- Store ACL on **each chunk**.
- Filter in the vector query (pre-filter or a store that guarantees filter+ANN correctness).
- Never retrieve then filter in Python on a large candidate set as the only control.
- Separate indexes or namespaces per tenant when legally required.
- Cache keys include tenant/user.
- Prompt-prefix cache must not mix tenants.
- Test with canary documents: user A must never see tenant B’s canary.
- Audit retrievals.

**Weak:** “We’ll add a note in the prompt to only use allowed docs.”

---

## Q14. LLM latency doubled. Walk the incident.

**Testing:** OBSERVE/ISOLATE on AI systems.

**Order**

1. When, which model, which endpoint, p50 vs p95, TTFT vs decode vs retrieval vs tools.
2. Change: deploy, prompt length, index, traffic mix, provider incident.
3. Hypotheses: context explosion, cache miss on system prompt, reranker k increased, agent extra steps, cold GPU, region fail-over, rate-limit retries.
4. Mitigate: route to smaller model, cap context, disable rerank temporarily, shed load.
5. Prevent: SLO on TTFT and E2E, trace spans, prompt size lint in CI.

---

## Q15. API returns 429. What do you do?

**Testing:** Production HTTP, not AI magic.

**30-second**

Honor `Retry-After`. Exponential backoff with jitter. Idempotent retries only. Shed or queue non-interactive work. Circuit breaker. Multi-provider fallback if the product allows. Reduce tokens (smaller model, cache, fewer agent steps) because 429s are often self-inflicted. Monitor RPM/TPM vs quota. For cloud: provisioned throughput if sustained.

---

## Q16. How do you secure a tool-using assistant?

**Testing:** OWASP LLM01 + LLM03 Excessive Agency.

**Layers**

- Untrusted: user text, retrieved docs, tool outputs, images.
- Validate tool name/args against schema and policy.
- Least privilege credentials per tool.
- HITL for irreversible actions.
- Sandbox code/shell.
- Output encoding if rendered in HTML.
- Budgets against unbounded consumption.
- Immutable audit log.

**Weak:** “System prompt says you are a helpful assistant who never does anything bad.”

---

## Q17. How does a vector database work? (They will reject brute-force cosine.)

**Testing:** ANN literacy.

**30-second**

At millions of 768–3072-d vectors, exact kNN is too slow and distances concentrate. We use **approximate** indexes. **HNSW:** layered proximity graphs; search descends from coarse to fine; typical tens-to-hundreds of hops, not millions of comparisons. **IVF:** cluster, search nprobe buckets. Metadata filters can destroy recall if applied naively. Hybrid adds a sparse index.

**Trade-off:** recall vs latency vs memory vs update rate. Tune `efSearch` / `nprobe`. Measure recall@k on a holdout.

---

## Q18. Design ChatGPT for enterprise documents. (skeleton)

**Testing:** System design framework. Full versions in Chapter 20–21.

**Spoken skeleton (first 8 minutes)**

1. Clarify: Q&A only or actions? Citations? Which sources? Tenancy? Latency? Regulated?
2. FR: ask, retrieve, cite, refuse, feedback. NFR: p95, residency, 99.9%, $/query.
3. Scale napkin: docs × chunks × dim × bytes; QPS; tokens.
4. APIs: `POST /query`, `POST /ingest`, admin index.
5. Diagram: ingest pipeline || query path; identity service; hybrid search; rerank; LLM gateway; eval worker; traces.
6. Deep dive invitation: ACL, evals, or failures.

**Do not** open with vendor names.

---

## Q19. Tell me about a project you shipped. (pattern)

**Testing:** Ownership and numbers.

**30-second pattern**

> I built [system] for [user] to [job]. I owned [slice]. We moved [metric] from X to Y by [one technical choice]. The hard part was [failure mode], which we caught with [eval/trace].

**They will then ask why not the other stack.** Pre-answer model, DB, framework, cloud, eval.

If you have not shipped production AI, say so and describe a production-*shaped* project (evals, traces, ACL, failure) without calling it production. Lying dies here.

---

## Q20. Why should we hire you for AI if your years in AI are few?

**Testing:** Career transition honesty. Full treatment in Chapter 26.

**Structure:** production muscle → mapped to AI systems → proof artifact → humility.

**60-second pattern**

> I have [N] years shipping [APIs / data / cloud / automation] with on-call. AI engineering in 2026 is those systems with a non-deterministic component. I have [one serious project]: RAG/agent with hybrid retrieval, traces, and a golden set of [n] questions; faithfulness [x]; we handled [incident]. I will not pretend I trained a foundation model. I will own evaluation, failure handling, and integration — which is what this JD describes.

**Never:** inflate a weekend tutorial into “led enterprise GenAI.”

---

## Rapid self-test

Cover the page. Answer Q1, Q5, Q6, Q8, Q13, Q16 in 60 seconds each. If any answer lacks a **trade-off** or a **metric**, you are not done.

Then go deep in the matching topic guide.
