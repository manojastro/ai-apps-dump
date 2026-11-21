# 10 — RAG

**Roles that score this chapter as core:** GenAI / Agentic AI Engineer, Forward Deployed / AI Deployment, AI Solutions Architect, AI Solutions Engineer (discovery + demo judgment).

**Roles that still get asked:** Cloud AI (managed RAG), AI Security (ACL, injection via docs), Intelligent Automation (grounded next-step), AIOps (runbook retrieval). RAG showed up in **35.9%** of the ~889 January 2026 AI Engineer JDs and in far more interviews than that number — it is the default architecture prompt.

This is the highest-probability topic in the book. Chapter 14 is the index. Chapter 17 is how you know it works. This chapter is the **pipeline and the judgment**.

---

## Interviewer intent

They are not hiring you to say “we embed documents and cosine-search.” They are hiring you to **ground answers in authorized, current snippets**, and to debug the system when it looks smart and is wrong.

| Signal | Pass | Fail |
| --- | --- | --- |
| Pipeline | Ingest → chunk → embed → index → rewrite → retrieve → rerank → generate → cite → eval | “LangChain RetrievalQA” |
| Retrieval first | You debug search before the prompt | “Maybe raise temperature” |
| ACL | Filter **before** the model sees text | “The model should not mention other tenants” |
| Evals | Separate retrieval metrics from generation metrics | “Users liked it” / one LLM-as-judge number |
| Citations | Span-level, verified against context | Footnotes the model invented |
| When *not* | Lookups, SQL, classic search, fine-tune-for-behavior | RAG on everything, including “what is 2+2” |

**The highest-signal 2026 question in this chapter:** *Retrieval is right, the answer is wrong — now what?*

If you cannot split retrieval failure from generation failure, you cannot operate RAG.

---

## Probability ranking (applied AI loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | End-to-end RAG design | Almost certain | Pipeline + ACL + evals |
| 2 | Retrieval-right / answer-wrong debug | Almost certain | Ordered investigation |
| 3 | Chunking | Very high | Structure, not a magic number |
| 4 | Hybrid + rerank | Very high | Why dense-only fails |
| 5 | Evaluate before shipping | Very high | Golden set + slices + ship bar |
| 6 | Citations / grounding | Very high | Verify, not “ask it to cite” |
| 7 | RAG vs fine-tune vs prompt | Very high | Decision tree (also Chapter 09) |
| 8 | Why not a 1M context dump | Very high | Cost, lost-in-the-middle, ACL |
| 9 | Multi-tenant / ACL retrieval | High; **critical in enterprise** | Query-time filter, fail closed |
| 10 | Empty retrieval | High | Abstain, not hallucinate |
| 11 | Latency | High | Waterfall: retrieve vs rerank vs LLM |
| 12 | Freshness / deletes / updates | High | Tombstones, version, rebuild |
| 13 | Query rewrite / multi-turn | High | HyDE as optional, rewrite as default |
| 14 | PDFs, tables, messy ingest | Medium–high | Parsers, not hope |
| 15 | Indirect injection via docs | Medium–high | Treat retrieved text as untrusted (Ch 19) |
| 16 | GraphRAG / RAPTOR / HyDE | Medium-low | When extra, never default |
| 17 | When RAG is the wrong tool | High as a closer | Lookups, transactions, code |

**MARKET OBSERVATION:** Fine-tuning was in **8.5%** of that JD set. “Let’s fine-tune on the wiki” is still a common interview *trap*. Agents were **14.4%** and rising; many “agent” prompts are RAG plus one tool. Prepare this chapter even if the title says Agentic or FDE.

---

## How to study this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Then the deep cut. Write *your* six-part card. Invent one follow-up.

Do not memorize vendor APIs. Interviewers change the wording: “knowledge assistant,” “chat over Confluence,” “grounded copilot,” “enterprise search.” The test is: **data → permission → retrieve → generate → measure.**

---

## The one diagram you should be able to draw

```
 INGEST (async)                         QUERY (sync, p95 budget)
 ──────────────                         ────────────────────────
 source systems                         user (+ identity)
   │                                      │
   ▼                                      ▼
 parse / OCR / clean                    authn → authz context
   │                                      │
   ▼                                      ▼
 chunk + metadata                       query rewrite / expand
   │                                      │
   ▼                                      ├─► BM25 (sparse)
 embed (pinned model)                   ├─► dense ANN (ACL filter)
   │                                      │
   ▼                                      ▼
 index + BM25 + ACL fields              fuse (RRF) → rerank → top k
   │                                      │
   ▼                                      ▼
 version: corpus_hash                   pack window (gold at head+tail)
                                        generate (cite-or-abstain)
                                        verify citations vs context
                                        eval / trace / $ 
```

Two pipelines. If you draw one box labeled “vector DB,” you have already failed the design round.

---

## Production RAG checklist (say this unprompted)

If you ship RAG, you owe the interviewer all of these:

1. **Identity-aware retrieval** — ACL/tenant filter in the query, not in the prompt.
2. **Hybrid + rerank** — BM25 + dense, then a cross-encoder (or equivalent) top 50 → 5–10.
3. **Pinned embedding model** — changing it is a rebuild, not a config flip.
4. **Citations with verification** — claim maps to a retrieved span; drop or flag unverified claims.
5. **Empty-retrieval policy** — abstain / ask / escalate; never “the model will know.”
6. **Golden set + slices** — retrieval metrics *and* answer metrics, in CI.
7. **Corpus version** — you can say which index digest answered this question.
8. **Untrusted context** — retrieved text is attacker-controlled (Chapter 19).

Missing any one of these is a mid-level ceiling on a GenAI, FDE, or Architect loop.

---

## Q1. What is RAG, and why not just a bigger context window?

**Why they ask.** Definition plus the 2026 follow-up. “We have 1M context, dump the PDFs” is a live fail.

**What they expect.** Grounding as the *job*. Window as scarce. ACL, cost, freshness, citations.

**Answer structure keywords.** retrieve then generate · private/current data · citations · usable context ≠ advertised window · lost-in-the-middle · ACL · cost.

**30-second.** RAG retrieves relevant snippets from a knowledge source and puts them in the model’s context so the answer can use current, private, citable data instead of weights. A bigger window does not replace retrieval: you still pay prefill, you still lose the middle, you still must not dump another tenant’s files, and you still cannot cite 40k pages. Retrieval is how we *select* what the model is allowed to see.

**2-minute.** Training weights are frozen and public. Enterprises need yesterday’s policy, this tenant’s contracts, this cluster’s runbook. RAG is an engineering system: ingest, chunk, embed, index, retrieve, optionally rerank, generate with “use only this context,” cite, eval. A 200k–1M window is a *budget*, not a lake. Prefill cost and TTFT scale with tokens (Chapter 09). Lost-in-the-middle means the model under-uses the center of a dump. Permissions: if you paste SharePoint into the prompt, you have bypassed the ACL model of SharePoint. Freshness: a dump is a snapshot; an index can tombstone. I use long context for *the retrieved working set* (a few reranked sections), not for the corpus.

**Senior / deep.** The interesting design is **what retrieval is for**. Sometimes it is grounding (must cite). Sometimes it is routing (pick a tool or a subgraph). Sometimes it is memory (episodic). Those are different indexes and different evals. I also distinguish *context stuffing* (k too large, hope the model sorts it) from *context engineering* (k small, ordered, titled, ACL-legal). When a vendor brags about 1M tokens, I ask: what is p95 TTFT at 200k input, what is needle-in-haystack on *our* docs, and what is the ACL story. Extractive tasks (quote the clause) often want smaller, tighter chunks and may not need a clever generator at all.

**Weak answer.** “RAG connects LLMs to your data so they don’t hallucinate.” Slogan, no pipeline, no window argument.

**Mistakes.**

- Treating RAG as a vector DB product.
- Claiming long context “solves” retrieval.
- Ignoring ACL.
- Fine-tune as the first alternative.

**Follow-ups + strong replies.**

- *“Can’t we just search and show links, no LLM?”* — Yes, for navigational search. RAG is for *synthesis with grounding*. I still ship classic search as a mode.
- *“What goes in the system prompt vs retrieved?”* — Stable policy and output schema in the system prompt (prefix-cacheable). Facts from the corpus in retrieved chunks.
- *“Does RAG stop hallucinations?”* — It changes the failure mode to *bad retrieval* and *ungrounded generation*. You still need abstain + citation verify.

**Example.** Internal policy copilot: 40k docs, citations required. We retrieve 5 reranked sections, not the handbook. The 128k window holds system + 5 chunks + compact history — not 40k files.

---

## Q2. How do you choose a chunking strategy?

**Why they ask.** This is where tutorials die. They want data-dependent judgment.

**What they expect.** Structure first, token size as a cap, overlap, parent expansion, special types (tables, code, slides), eval.

**Answer structure keywords.** structure over tokens · overlap · parent/child · metadata prepend · version with embedder · eval on failures.

**30-second.** I chunk by document structure — headings, paragraphs, pages — and use a token cap so embeddings stay on one topic. I keep overlap so sentences on boundaries survive. I store a parent section so I can retrieve small and expand. I never treat “512 tokens with 50 overlap” as a philosophy.

**2-minute.** The vector is only as good as the text you embed. Too large: mixed topics, noisy neighbors. Too small: the matching sentence lacks the noun that made it relevant. Default for prose: split on Markdown/HTML headings, cap ~200–400 tokens, 10–20% overlap, prepend title + section path to the embedding text. Tables: keep a row (or a small row-group) with column headers; do not split a cell from its header. Code: symbol-aware. PDFs: layout-aware parser before chunking (Q13). I persist `doc_id`, `version`, `section_path`, `acl`, `byte_span` so citations can point at a span, not a vibe. Chunker + embedding model are versioned together; changing either rebuilds.

**Senior / deep.** Chunking is an eval surface. I keep a failure catalog: missed clause, split table, boilerplate that dominates cosine (headers, “confidential”). Fixes: smaller chunks + BM25 for exact tokens (policy IDs, error codes); parent expansion for the LLM; a second *section* index for routing. Late chunking (embed long, pool token vectors into chunk embeddings) is a tool, not a religion. For agents I often keep coarse chunks for “which doc” and fine chunks for grounding. Index bloat is real: aggressive overlap can 1.3–2× vectors and the bill. I measure recall@k on a labeled set after every chunker change — I do not A/B in production by hope.

**Weak answer.** “LangChain recursive splitter, 1000/200, works everywhere.”

**Mistakes.**

- One size for PDFs, tickets, and code.
- Embedding without the title.
- No plan to re-chunk on update.

**Follow-ups + strong replies.**

- *“Semantic chunking?”* — Embed-and-split on similarity breaks. Useful on unstructured blobs. Still eval; can be slow at ingest.
- *“Who deletes old chunks?”* — Ingestion worker: delete by `doc_id`+old `version`, write new, atomically swap the alias the query path reads.

**Example.** HR policy: one Markdown file per policy, H2 sections as chunks, title prepended, parent = full policy for expansion when the user asks “the whole leave policy.”

---

## Q3. BM25 vs dense vs hybrid vs rerank — what do you actually ship?

**Why they ask.** Dense-only is the 2023 demo. Production 2026 is hybrid.

**What they expect.** Exact tokens vs paraphrase, fusion, rerank as the quality lever, cost of the reranker.

**Answer structure keywords.** BM25 exact · dense paraphrase · RRF · cross-encoder rerank · ACL on both legs · recall then precision.

**30-second.** BM25 finds exact tokens — error codes, policy IDs, product names, rare proper nouns. Dense finds paraphrases. Hybrid runs both, fuses (RRF or a learned mix), then a reranker turns a broad candidate list into the 5–10 the LLM should see. I almost never ship dense-only for enterprise text.

**2-minute.** Retrieval is two problems: *recall* (is the right chunk in the candidate set?) and *precision* (is it at the top?). Dense recall is weak on identifiers and new jargon the embedder never saw. BM25 is weak on “how do I take time off” vs “annual leave policy.” Hybrid covers both. I retrieve, say, 50 from each, fuse, then rerank to 5–10. The reranker is a cross-encoder or a small specialized model; it is more expensive per pair, so I do not rerank the corpus — I rerank a shortlist. Metadata filters (tenant, product, language) apply **before** or as part of search, not after the LLM. Chapter 14 is the index internals; this is the retrieval policy.

**Senior / deep.** I treat rerank as the highest-ROI quality knob after chunking. If the JD is cost-sensitive, I can skip rerank on navigational queries and keep it on synthesis queries (route by query classifier). I log `bm25_ids`, `dense_ids`, `fused_ids`, `rerank_ids` so I can see which leg saved the answer. I do not use the LLM as a first-stage retriever (too slow, too expensive) except as a *rewrite* (Q8). GraphRAG and HyDE are later (Q16). Default stack I will defend in 2026: hybrid + rerank + citations. Managed RAG (Bedrock KB, Azure AI Search, Vertex AI Search) is acceptable when it gives hybrid + filters; I still need to know what it *does not* give me (custom chunker, eval hooks).

**Weak answer.** “Embeddings are semantic so we don’t need keywords.” Or listing eight vector databases.

**Mistakes.**

- Reranking the entire corpus.
- Fusing without score normalization / RRF.
- Applying ACL only on the dense leg.

**Follow-ups + strong replies.**

- *“What is RRF?”* — Reciprocal rank fusion: combine lists by rank, not raw score, so BM25 and cosine are not on different scales.
- *“ColBERT / multi-vector?”* — Better matching, heavier indexes. Mention as an option for high-value corpora; not the first sketch.
- *“Would you use an LLM reranker?”* — For a tiny k, maybe. Usually a cross-encoder is cheaper and more stable. Eval it; don’t assume.

**Example.** Support RAG: user pastes `ECONNRESET`. BM25 hits the runbook; dense hits “connection dropped.” Fusion + rerank puts the runbook first. Dense-only ranked a blog post about TCP.

---

## Q4. Retrieval is correct, the answer is wrong. Debug.

**Why they ask.** This is the discriminator. Tutorial people blame the prompt. Operators split the pipeline.

**What they expect.** An ordered investigation. Traces. Separate retrieval vs generation metrics.

**Answer structure keywords.** inspect retrieved set · groundedness · instruction · packing · model pin · citation verify · then prompt.

**30-second.** I do not touch temperature first. I open the trace: what chunks were retrieved, ranks, scores, ACL, the packed prompt, the model ID. If the gold span is in context and the model ignored it, that is generation: packing, instructions, model, or a conflict in the chunks. If the gold span is missing, that is retrieval: query, chunking, hybrid, filters. If the span is there and the citation is fake, that is unverified generation — a product bug, not “hallucination vibes.”

**2-minute.** Order:

1. **Was retrieval empty or off-topic?** Empty → Q10. Wrong docs → query rewrite, filters, chunking, embedder drift.
2. **Was the right chunk retrieved but ranked 20?** Rerank / k too small / lost-in-the-middle packing.
3. **Right chunk in the window, wrong answer?** Conflicting chunks, weak “cite or abstain,” temperature > 0 on facts, model too small, instruction buried.
4. **Right answer, bad citation?** Verify citations in code; do not trust the model’s footnote.
5. **Right on golden set, wrong in prod?** Slice: language, new product name, tenant-specific jargon.

I compare offline retrieval metrics (recall@k, MRR) to answer metrics (faithfulness, correctness). If recall is high and faithfulness is low, I stop tuning HNSW.

**Senior / deep.** I want **span-level** labels on the golden set: this question needs these `chunk_id`s. Then I can say “retrieval hit, generator miss” as a count, not a story. Packing: put the highest-rerank chunks at the **head and tail**, question last (Chapter 09 lost-in-the-middle). If two policies conflict, the model will pick one; the product should surface both or prefer `effective_date`. For agents, “wrong answer” may be a **wrong tool result** stuffed into context — same debug, extra span. I never A/B a prompt while the index digest is moving.

**Weak answer.** “I’d improve the prompt and add more documents.”

**Mistakes.**

- Tuning the vector DB when the chunk never contained the fact.
- Raising k to 40 “to be safe” (lost-in-the-middle, cost, injection surface).
- No trace, so you are guessing.

**Follow-ups + strong replies.**

- *“Show me the 2 a.m. query.”* — `trace_id` → retrieve span (ids, scores, filter) → packed token count → model pin → citation verify result.
- *“Users say it’s worse after we added 1M docs.”* — Q12.

**Example.** Policy bot cites “unlimited PTO.” Trace shows the 2019 blog post retrieved; the 2025 policy was filtered out because `doc_type=blog` was not excluded. Retrieval bug, not a prompt bug.

---

## Q5. How do you evaluate RAG before shipping?

**Why they ask.** Evaluation is the 2026 differentiator. Building a pipeline without a bar is a demo.

**What they expect.** Retrieval metrics and generation metrics, golden set, slices, a numeric ship bar, human calibration.

**Answer structure keywords.** recall@k · precision@k · MRR/nDCG · faithfulness · citation accuracy · golden set · slices · LLM-as-judge bias · CI gate.

**30-second.** I will not ship on “looks good.” I freeze a golden set of questions with labeled relevant chunks and acceptable answers. Offline I measure retrieval (recall@k, MRR) and answers (faithfulness, citation accuracy, correctness). I slice by doc type, tenant, and question class. CI fails the release if a gated slice drops. Humans calibrate the judge; they do not replace it.

**2-minute.** Two layers:

- **Retrieval:** Did we fetch the spans a good answer needs? Recall@5/@20, MRR, nDCG if we have graded relevance. Empty-retrieval rate on questions that *should* hit.
- **Generation:** Given that context, is the answer grounded (faithfulness), complete, and cited correctly? I score citation *accuracy* (claimed id was in context and supports the claim), not just “has a bracket.”

LLM-as-judge is allowed if I know the biases (position, verbosity, self-preference) and I measure agreement with a human sample. RAGAS / DeepEval / promptfoo / Phoenix are tools; the *product* is the dataset and the bar. Online: thumbs, escalation rate, groundedness on a sample, cost/task (Chapter 17).

**Senior / deep.** A 40-example notebook is eval theater. I want hundreds, with **hard slices**: tables, numeric policies, multi-hop, “not in corpus” (must abstain), new product names. Synthetic questions from chunks are a start; they overfit retrieval-to-same-chunk and miss real user wording — I mix them with logged anonymized queries. Promotion rule: production failures get labeled weekly into the set. Ship bar example for internal copilot: recall@5 ≥ 0.85, faithfulness ≥ 0.88, citation accuracy ≥ 0.90, abstain-on-unknown ≥ 0.95, p95 E2E ≤ 8s. If retrieval recall is the miss, I do not “train a better judge.”

**Weak answer.** “We use RAGAS” with no numbers and no slices.

**Mistakes.**

- One blended score that hides retrieval failure.
- Judging answers without freezing the index digest.
- No “should abstain” items.

**Follow-ups + strong replies.**

- *“How many gold items?”* — Enough for slices to be meaningful. I’d rather 200 labeled than 5,000 unlabeled.
- *“Offline vs online?”* — Offline gates release. Online catches drift and vendor model changes.

**Example.** Before enabling customer Slack, we blocked a release because the “pricing” slice faithfulness was 0.71. Root cause: stale rate-card PDF still in the alias. Index bug, caught by eval, not by the PM clicking around.

---

## Q6. How do you cite sources and verify them?

**Why they ask.** Trust. Legal. Support. Hallucinated footnotes are worse than no citations.

**What they expect.** Structured citations, verification in **code**, UI that can open the span.

**Answer structure keywords.** chunk_id · span · verify membership · fail closed · UI link · do not trust model footnotes.

**30-second.** The model may propose citations. Code checks that every cited `chunk_id` was actually in the retrieved set and that the claim overlaps the chunk text (or we treat it as uncited). The UI links to `doc_id` + byte span. If verification fails, we strip the citation or abstain — we do not show a decorative footnote.

**2-minute.** I force a schema: `{ answer, citations: [{chunk_id, quote}] }`. After generation I join `chunk_id` to the retrieve span. Missing id → drop or regenerate once. Quote not in chunk → flag. I prefer extractive quotes for policies and numbers. For synthesis, I still require *supporting* chunks, not invented URLs. I store citation outcomes on the trace so we can metric “citation fail rate” (Chapter 17 ship bar).

**Senior / deep.** Citation is an alignment problem *and* a packing problem. If k=20 and we ask for citations, the model will cite the shiny chunk. Keep k small. For regulated text I sometimes do **extractive first**: highlight spans, then optionally rewrite. Multi-tenant: the link must not be a universal URL that bypasses ACL — the app re-checks permission on click. I never let the model invent a URL. If we only have titles, we show titles from *our* metadata, not from the completion.

**Weak answer.** “We tell the model to list sources at the end.”

**Mistakes.**

- Clickable URLs the model typed.
- Citing documents that were retrieved but do not support the claim.

**Follow-ups + strong replies.**

- *“What if the answer is a blend of three chunks?”* — Three citations, each supporting a clause. If we cannot map a clause, we mark it as model commentary or delete it.

**Example.** Contract Q&A: UI shows the clause with page + highlight. The generator is not allowed to emit a page number that is not in metadata.

---

## Q7. Multi-tenant RAG with ACLs

**Why they ask.** One leak ends the company. Highest-severity enterprise question.

**What they expect.** Authorization **before** retrieval. Tenant isolation of indexes, caches, traces. Fail closed.

**Answer structure keywords.** query-time filter · tenant key · no prompt-as-ACL · cache keys · traces · fail closed.

**30-second.** The model is not the ACL. At query time I attach the caller’s identity and retrieve **only** chunks whose ACL matches. Other tenants’ vectors never enter the window, the prompt cache, or the trace body. If the filter fails closed to empty, we abstain — we do not retry without ACL.

**2-minute.** Patterns, strictest first: (1) **separate index / namespace per tenant** when isolation and residency demand it; (2) **shared index + mandatory filter** on `tenant_id` (and document ACL) with a database that can pre-filter (Chapter 14); (3) never “retrieve then drop in Python” as the only control — a bug or a retry will leak. Caches (embedding, response, prefix) include tenant in the key. Ingestion writes ACL from the source system (SharePoint, Drive, Git) as metadata, not from a human spreadsheet we forget to update. Deletes propagate. App re-checks ACL on citation click.

**Senior / deep.** Real ACLs are more than `tenant_id`: groups, domain, “finance only,” time-bound shares. I prefer **ACL at the source of truth** and a sync job that projects allowed `principal_ids` onto chunks. At query: `filter: principal IN user_principals`. I load-test **filtered recall** — HNSW + restrictive filters can return nothing or the wrong neighborhood (Chapter 14). For highly sensitive tenants I pay for separate indexes. I threat-model prompt injection (Q14): even authorized docs can instruct the model to exfiltrate. Tool allowlists still apply. Traces store chunk IDs, not raw foreign documents, with the same ACL as the product.

**Weak answer.** “We tell the model not to mention other customers.” Or “we have two namespaces in Pinecone” with no cache/trace story.

**Mistakes.**

- Post-filtering after dense search as the only gate.
- Shared prompt-prefix cache across tenants.
- Putting another tenant’s chunk in a few-shot example.

**Follow-ups + strong replies.**

- *“User is in Finance only.”* — Principals include `group:finance`. Chunks tagged `acl:finance` or more specific. A company-wide FAQ may be tagged `acl:all-employees`.
- *“Can we use one big index for cost?”* — Yes, if filtered ANN is proven and residency allows. I still isolate traces and keys.

**Example.** Two hospitals, one product. Namespaces `t_a`, `t_b`. Clinician token → namespace from the session, not from the question text (“I’m from hospital B” does nothing).

---

## Q8. Multi-turn RAG and query rewriting

**Why they ask.** Chat is not a single keyword. “What about the other one?” must resolve.

**What they expect.** Rewrite with history, retrieve on the rewrite, do not stuff entire history into BM25.

**Answer structure keywords.** coreference · rewrite · retrieve on rewrite · compact history · don’t retrieve on pronouns.

**30-second.** I do not embed “what about the other one?” I run a cheap rewrite step: resolve pronouns using the last turns and the last citations, produce a standalone query, then retrieve. History for the *generator* is compacted; history for *search* is the rewrite.

**2-minute.** Multi-turn failures are usually retrieval on anaphoric queries. Pipeline: (1) rewrite / expand to a standalone question, (2) hybrid retrieve, (3) optionally include last cited `chunk_id`s as boosts, (4) generate with compact history + new chunks. HyDE (write a hypothetical answer, embed that) can help paraphrase-heavy queries; it can hurt identifier queries — I route. I cap rewrite tokens and pin the rewrite model (small). I log both raw and rewritten queries so evals are honest.

**Senior / deep.** Follow-up “summarize that” should **not** re-retrieve; it should operate on the last grounded context (workflow, not agent). Follow-up “compare to vendor X” should retrieve for X and keep the previous gold chunks. I treat those as **intents**. Conversation memory is not the corpus: I do not index chat into the org index without ACL and TTL (contamination). For FDE demos, showing the rewritten query in a debug panel builds trust with engineers.

**Weak answer.** “The context window holds the whole chat so RAG just works.”

**Mistakes.**

- Retrieving on raw follow-ups.
- Letting history crowd out retrieved chunks.

**Follow-ups + strong replies.**

- *“Multi-hop?”* — Decompose into sub-questions, retrieve per hop, then synthesize. That’s a workflow with two retrieve nodes, not an open agent, unless the hop count is unknown.

**Example.** “What’s the retention?” then “and for EU?” Rewrite: “What is the data retention period for EU customers?” BM25 hits the GDPR section.

---

## Q9. How do you reduce RAG latency?

**Why they ask.** p95 is a product feel. They want a waterfall, not “use a faster model.”

**What they expect.** Attribute retrieve vs rerank vs prefill vs decode. Then cache, k, parallelism, streaming.

**Answer structure keywords.** waterfall · parallel BM25+dense · smaller k · rerank shortlist · prefix cache · streaming · embedding cache.

**30-second.** I trace each stage. Typical wins: run sparse and dense in parallel, cap k, rerank a shortlist not 200, shrink packed tokens (prefill dominates TTFT), prefix-cache the system prompt, stream tokens, cache embeddings at ingest not at query. I do not start with a bigger GPU.

**2-minute.** Budget, example: 8s p95 E2E. Retrieve 200ms, rerank 150ms, prefill 400ms, decode the rest. If prefill is the bulk, cut packed tokens (better rerank, not larger k). If retrieve is the bulk, fix the index (Chapter 14), filters, or overfetch. If decode is the bulk, smaller model or routing (Chapter 09). Streaming hides decode, not retrieve — say that. Warm caches: embedding model is ingest-time; query embed is one short encode. Avoid chatty agent loops around RAG (Chapter 11).

**Senior / deep.** I set SLOs on **TTFT** and **E2E** separately. I pre-compute nothing user-specific except authorization context. For hot FAQs I cache *answers* keyed by tenant + rewrite-hash + index digest, with a short TTL and ACL. I do not cache across tenants. If we self-host the reranker, batch it. If we use a managed KB, I still measure; “serverless” tails can dominate. FDE: a 30s first-token demo loses the room even if the answer is perfect.

**Weak answer.** “We’ll stream and use GPT-4o-mini.”

**Mistakes.**

- Raising k to improve quality and wondering why TTFT died.
- Sequential BM25 then dense.

**Follow-ups + strong replies.**

- *“p95 doubled after adding rerank.”* — Shorten the candidate list, smaller reranker, skip rerank on navigational intents.

**Example.** Copilot p95 12s → 4.5s: parallel retrieval, k 40→8 after a real reranker, system prompt 4k→1.2k, prefix cache on.

---

## Q10. Empty retrieval — what should the system do?

**Why they ask.** This is where demos hallucinate. Production systems abstain.

**What they expect.** A policy: abstain, clarify, or search fallback — never silent generation from weights.

**Answer structure keywords.** threshold · abstain · clarify · escalate · don’t generate from params · eval the unknown set.

**30-second.** If scores are below a threshold or the filter returns nothing, I do not call the generator on an empty context (or I call it only to produce a *canned* “I don’t have this”). I may ask a clarifying question or fall back to keyword search UI. I never let the model answer HR policy from training data.

**2-minute.** Empty is a first-class outcome: metric it. Causes: over-strict ACL, bad rewrite, too-high threshold, missing ingest, identifier the embedder can’t see (turn on BM25). User-visible: “I couldn’t find this in the knowledge base. I can open a ticket or you can rephrase.” For FDE, showing *why* (no docs in scope) is better than a fluent wrong policy. Golden set must include “not in corpus” items (Q5).

**Senior / deep.** Thresholds on cosine are not calibrated across embedders. I prefer hybrid: if BM25 has a strong exact hit, don’t drop it because dense is low. I separate **no permission** (empty by ACL — do not tell the user the doc exists) from **no document**. Those are different UX and different security. Logging the difference matters for red-team (Chapter 19).

**Weak answer.** “The LLM will still answer helpfully.”

**Mistakes.**

- Filling empty context with a web search silently in an enterprise bot.
- Revealing that a classified doc exists via a different error.

**Follow-ups + strong replies.**

- *“What threshold?”* — Set on a validation set; monitor empty rate in prod; don’t copy 0.8 from a blog.

**Example.** New product name not ingested yet. Bot says it doesn’t have documentation; support macro offers a ticket. We do not invent an SLA.

---

## Q11. When is RAG the wrong tool?

**Why they ask.** Senior closer. RAG-everywhere is the new agent-everywhere.

**What they expect.** A blacklist and what you would build instead.

**Answer structure keywords.** lookup · transaction · deterministic · computation · tiny corpus · behavior vs knowledge.

**30-second.** RAG is for *unstructured knowledge that must be cited and changes*. Wrong for: account balances (SQL), “reset password” (workflow), math (code), stable style/behavior (prompt or fine-tune), ten-page corpus you can retrieve by rules, or questions that must be exact extracts with no synthesis.

**2-minute.** Decision:

- **Need a number from a system of record** → tool / SQL, not RAG.
- **Need to take an action** → workflow + HITL, maybe RAG to *draft*.
- **Need the model to talk like our brand** → prompt; FT if necessary (Chapter 09).
- **Need yesterday’s policy cited** → RAG.
- **Need to search 20 runbooks with IDs** → BM25 UI might suffice; add generation only if they want a summary.

I will say “classic search is enough” in a Solutions / FDE loop. That is a hire signal.

**Senior / deep.** RAG also loses when the user needs **guaranteed completeness** (“list every exception in the contract”). Retrieval can miss a clause; an extractive full-doc or a structured table is safer. Multi-hop over a knowledge graph may be justified when relations are first-class (Q16) — still not default. Cost: if 90% of queries are navigational, RAG is an expensive wrapper.

**Weak answer.** “RAG is always the first step for enterprise AI.”

**Mistakes.**

- RAG over a SQL warehouse of facts.
- RAG as a memory dump of user PII.

**Follow-ups + strong replies.**

- *“Can RAG replace our search team?”* — No. It consumes good search. Hybrid *is* search.

**Example.** “What’s *my* unused leave balance?” HRIS tool with the user token. RAG for “how does carry-over work?”

---

## Q12. Quality dropped after adding 1M documents

**Why they ask.** Scale is a retrieval problem. They want causes, not “buy Pinecone.”

**What they expect.** Recall vs pollution, ANN tuning, chunking, boilerplate, filters, eval slices.

**Answer structure keywords.** pollution · recall@k drop · ANN ef/nprobe · boilerplate · namespace · re-eval digest.

**30-second.** More docs increase the chance of near-miss chunks. I check: did recall@k on the old golden set drop? Did we change the embedder? Is ANN under-probing? Is boilerplate (headers, disclaimers) crowding semantic space? I freeze the old index alias and compare, I do not tune production by feel.

**2-minute.** Causes I walk in order: (1) **eval** — same questions, new digest; (2) **pollution** — k now filled with generic “contact support” chunks; (3) **ANN recall** — rebuild/tune (Chapter 14); (4) **chunker** — we split too small at ingest to finish the job; (5) **filters** — a default tenant filter now too wide; (6) **duplicates** — 1M is 200k unique + copies. Fixes: metadata filters (product, date), better chunking, hybrid so rare tokens still win, raise `efSearch` until index recall recovers, separate indexes per corpus (tickets vs policies).

**Senior / deep.** I keep a **canary golden set** that must not regress on ingest. I ingest in batches and run the set every N documents. Dedup by content hash. Boost `updated_at` only as a feature, not as a religion (old policy can still be the law). If the business added a noisy source (scraped web), I **un-ingest** it. FDE: customers will dump file shares; your job is to refuse garbage, not to embed it.

**Weak answer.** “The vector DB can’t scale; we need a better vendor.”

**Mistakes.**

- Changing embedding model and index size in the same week.
- Raising k to 50 to “get the right doc back.”

**Follow-ups + strong replies.**

- *“How do you know it’s pollution not ANN?”* — Exact-search a sample of queries; if exact still returns junk in top-k, it’s the representation, not HNSW.

**Example.** Adding all Jira comments buried the runbooks. We filtered `doc_type=runbook` for the ops copilot and left tickets in a second index used only when the query looks like an incident ID.

---

## Q13. Ingestion of PDFs with tables and charts

**Why they ask.** Real corpora are not Markdown. FDE loops live here.

**What they expect.** Parser choice, layout, tables as tables, OCR, eval on “read this cell.”

**Answer structure keywords.** layout parser · table structure · OCR · captions · don’t embed pixels blindly · human sample.

**30-second.** I do not `pdftotext` and chunk. I use a layout-aware parser, keep tables as HTML or CSV with headers, OCR scanned pages, attach figure captions, and I eval on questions that need a cell, not only prose.

**2-minute.** Pipeline: detect digital vs scanned; OCR (with language) when needed; segment headers/footers (boilerplate) so they are metadata not chunks; extract tables as structured objects; chunk prose by heading; for a table-heavy page, a chunk may *be* the table plus caption. Multimodal: for charts, either a caption/summary at ingest (cheap) or a vision pass at query (expensive, rare). I store page numbers for citations. I sample pages into the golden set. If the parser mangles a column, RAG cannot recover.

**Senior / deep.** Ingestion quality is the ceiling. I would rather parse 10k pages well than 1M pages as a text sludge. For FDE week-1, I pick the 20 documents that matter and do them right. Tools change; the interview is the *pipeline*: classify → parse → validate (row counts, empty cells) → chunk → embed. I fail ingest on a document that produces zero tables when the PDF clearly has them, and I page a human. I do not put raw base64 images into the generator context by default.

**Weak answer.** “We dump PDFs into Unstructured / a loader and embed.”

**Mistakes.**

- Splitting a table down the middle by token count.
- Ignoring scanned PDFs until users complain.

**Follow-ups + strong replies.**

- *“Images of text?”* — OCR at ingest. Query-time vision only for ad-hoc pages not in the corpus.

**Example.** Rate card PDF: each row becomes a chunk with product + region + price, headers repeated. Questions like “price in EU for SKU-9” become BM25 hits.

---

## Q14. Index updates, deletes, freshness — and indirect injection

**Why they ask.** Stale policy and poisoned wikis are both production.

**What they expect.** Versioning, deletes that actually delete, freshness SLO, untrusted retrieved text.

**Answer structure keywords.** doc version · tombstone · alias swap · TTL · untrusted context · injection.

**30-second.** Every document has a version. Updates delete old chunk IDs and write new ones, then the query alias points at a consistent set. Deletes must remove vectors, BM25, and caches. Retrieved text is **untrusted** — it can contain instructions. The model does not get extra tools because a wiki said so (Chapter 19).

**2-minute.** Freshness SLO comes from the business (“policy within 15 minutes”). I ingest via webhook or crawl with cursors. I tombstone in the index; I do not “leave it, the new chunk will rank higher.” Response cache keys include `index_digest`. For injection: system prompt says retrieved content is data; tools are allowlisted in code; I strip obvious instruction tags in ingest if we must, but **filters are not the control** — tool policy is. I prefer a retrieve-only v1.

**Senior / deep.** Consistency: a user should not retrieve half old and half new of the same doc. I update by `doc_id` in a batch and swap. Legal hold vs GDPR delete are different paths. For injection evals I add a poisoned page to a staging tenant and assert the agent cannot email or fetch URLs. Hybrid helps: a poisoned semantic neighbor still has to beat BM25 on the real query. I still assume it will sometimes enter the window — hence no extra agency.

**Weak answer.** “We re-index nightly” (no deletes) and “the model is aligned so injection is fine.”

**Mistakes.**

- Soft-delete in SQL, live in the vector index.
- Crawling the public web into an internal assistant.

**Follow-ups + strong replies.**

- *“Wiki page jailbreaks the bot.”* — Expected. Retrieved = untrusted. Disable write tools; show the snippet to a human if it looks like an instruction.

**Example.** Policy v3 published; v2 chunks gone in 2 minutes; CDN answer cache TTL 60s keyed by digest. A “ignore previous instructions” paragraph in a vendor PDF cannot call `send_email`.

---

## Q15. Prompt vs RAG vs fine-tune — the decision tree

**Why they ask.** They have been burned by “fine-tune the wiki.” Also in Chapter 09; here you apply it to knowledge.

**What they expect.** Knowledge → RAG. Behavior/style → prompt then FT. Facts in systems of record → tools.

**Answer structure keywords.** knowledge vs behavior · citations · change rate · eval cost · FT last.

**30-second.** If the fact must be current and citable, RAG (or a tool). If we need tone, format, or a skill on stable data, prompt first, then consider LoRA. Fine-tuning is a poor wiki. I can walk one example of each.

**2-minute.** Wiki changes weekly → RAG. “Always answer as a table with these columns” → schema / prompt. “Extract purchase orders from our weird PDFs better than the base model” → maybe SFT/LoRA on *that skill*, still RAG for the vendor list. Cost: FT has a dataset and a regression harness; RAG has ingest. I refuse FT when the user really wanted permissions or freshness.

**Senior / deep.** Hybrid is common: RAG for facts, small FT (or a strong prompt) for output discipline. I will not FT to “remember customers” — that is a GDPR incident. If the JD is LLM Engineer, I can discuss LoRA vs RAG vs continued pretrain at one level deeper (Chapter 09 Q10). For this chapter, the hire signal is **refusing** the wiki-FT.

**Weak answer.** “Fine-tuning makes the model know our data.”

**Mistakes.**

- FT as a substitute for ACL.
- RAG as a substitute for SQL.

**Follow-ups + strong replies.**

- *“Our exec bought fine-tuning credits.”* — Use them on extraction or tone, not on the handbook. Show the eval that would prove FT won.

**Example.** Support: RAG on runbooks + tickets. A LoRA later, maybe, to extract `error_code` from messy logs — not to memorize runbooks.

---

## Q16. GraphRAG, RAPTOR, HyDE — when extra, never default

**Why they ask.** Depth spice and a trap. Seniors know the cost.

**What they expect.** A one-line what it is, when it helps, why you would *not* lead with it.

**Answer structure keywords.** default hybrid+rerank · graph for relations · RAPTOR for long summaries · HyDE for paraphrase · eval vs complexity.

**30-second.** Default is hybrid + rerank. GraphRAG helps when the question is about *relationships* (orgs, ownership, multi-hop entities) and we have a graph worth maintaining. RAPTOR-style trees help long-document summarization. HyDE helps some paraphrase queries and hurts identifiers. I add these after the default stack has evals.

**2-minute.** GraphRAG: extract entities/edges at ingest, retrieve a subgraph, then generate. Cost: extraction errors become retrieval errors; you now operate an NLP pipeline. RAPTOR: recursive summaries as extra nodes — good for “what is this 80-page report about,” redundant for FAQ. HyDE: generate a hypothetical passage, embed it — extra latency, extra hallucination into the query. I will mention them so the interviewer knows I read 2024–2026 papers; I will not draw them in minute two of a design (Chapter 20).

**Senior / deep.** If the customer already has a knowledge graph (ITSM CMDB, security graph), *use it as a tool* — that is often better than extracting a parallel graph from text. Multi-hop RAG as a **workflow** (two retrieves) beats an always-on graph for most FDE v0s.

**Weak answer.** “I’d use GraphRAG with agents and a knowledge graph” as the opening sentence.

**Mistakes.**

- Leading a 45-minute design with RAPTOR.
- HyDE on error-code lookup.

**Follow-ups + strong replies.**

- *“Would you use a graph?”* — If the question is “who owns service X and what depends on it?” and a CMDB exists, query the CMDB. If not, hybrid on runbooks first.

**Example.** “Summarize Q3 strategy deck” → section index / RAPTOR-like summaries. “What is error 5041?” → BM25.

---

## Rapid-fire (30–45 seconds each)

| Prompt | Hit these words |
| --- | --- |
| What is hybrid search? | BM25 + dense, RRF, then rerank |
| What is a chunk? | Embeddable span; structure; metadata |
| Cosine vs BM25? | Paraphrase vs exact tokens |
| Lost-in-the-middle? | Don’t dump; pack gold at head/tail; smaller k |
| Embedding model change? | Rebuild index; pin; eval |
| Metadata filter? | Apply in search, not in the prompt |
| Parent-child? | Retrieve small, expand section for the LLM |
| Faithfulness vs correctness? | Grounded in context vs true in the world |
| Citation fail? | Claimed id not in retrieve set or span |
| When not RAG? | SQL, workflow, tiny corpus, behavior/FT |
| Empty retrieval? | Abstain / clarify; don’t generate from weights |
| ACL? | Query filter; fail closed; no prompt-as-ACL |
| HyDE? | Optional rewrite; bad for IDs |
| Rerank? | Shortlist only; precision lever |
| Ingest vs query? | Two pipelines; async vs p95 |

---

## Weak vs strong posture (memorize the posture, not the paragraph)

| Weak | Strong |
| --- | --- |
| “We use a vector DB” | Hybrid + rerank + ACL + evals |
| “Hallucinations need a better prompt” | Split retrieval vs generation; cite-or-abstain |
| “Dump into 1M context” | Select; pack; pay for prefill |
| “Fine-tune the wiki” | RAG for knowledge |
| “The model won’t leak tenants” | Filter before retrieve |
| “RAGAS” | Numbers, slices, CI gate |
| “GraphRAG + agents” in sentence one | Defaults from Chapter 20; extras after evals |

---

## A complete example you can reuse in interviews

**Setting.** Internal policy copilot, 40k docs (Confluence + PDFs), 2k Q/day, citations required, multi-group ACL, p95 first token < 1.2s, cost cap $0.03/successful answer.

**Wrong design.** Frontier model, 80k pasted handbook, dense-only Pinecone, k=20, “please cite,” no pin, no eval, fine-tune planned.

**Right design.**

1. **Ingest:** layout parsers for PDFs; section chunks; title prepended; `acl` from Confluence groups; `doc_version`.
2. **Index:** BM25 + dense, pinned embedder, alias per digest.
3. **Query:** identity → principals → **filter first**; rewrite follow-ups; hybrid 50+50; RRF; rerank to 5; pack head+tail; question last.
4. **Generate:** T=0, cite-or-abstain schema; **verify** citations in code; stream after.
5. **Empty:** abstain. **Unknown slice** in the golden set.
6. **Evals:** recall@5, faithfulness, citation accuracy, ACL leak tests = 0. CI on prompt/index/model pin.
7. **Security:** retrieved = untrusted; no write tools in v1 (Chapter 19).
8. **Not RAG:** leave-balance lookup is HRIS.

**One sentence close:** “The model only sees a budgeted, ACL-legal working set; code owns retrieval, citations, and abstain.”

That sentence is what a 2026 interviewer is listening for.

---

## Map to the rest of the handbook

- Tokens, packing, FT vs RAG, lost-in-the-middle: [09-llm.md](09-llm.md)
- ANN, hybrid internals, vendors: [14-vector-databases.md](14-vector-databases.md)
- Agents on top of RAG: [11-agentic-ai.md](11-agentic-ai.md)
- Evals, traces, ship bar: [17-llmops.md](17-llmops.md)
- Injection, tenancy, output handling: [19-ai-security.md](19-ai-security.md)
- Design loops: [20-system-design.md](../design/20-system-design.md), [21-architecture-problems.md](../design/21-architecture-problems.md)
- Debug incidents: [22-troubleshooting.md](../banks/22-troubleshooting.md)
- Probability: [04-topic-probability-ranking.md](../04-topic-probability-ranking.md)

Next drill: speak Q1, Q3, Q4, Q5, Q7 out loud. If those five are clean, you will survive most GenAI / FDE screens. Add Q2 and Q13 for implementation; Q11 as your closer.
