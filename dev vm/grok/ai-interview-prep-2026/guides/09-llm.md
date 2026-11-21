# 09 — LLMs (tokens, context, serving, judgment)

**Roles that score this chapter as core:** GenAI Engineer, Agentic AI Engineer, Solutions Architect, Cloud AI (routing, quotas, pins), FDE (explain context and cost to a customer without a slide deck).

**LLM Engineer is not a ninth primary title.** It is the serving track *inside* GenAI / Agentic. If the JD says inference, vLLM, KV cache, LoRA, or “model platform,” go deep on Q12–Q14. Everyone else still needs Q1–Q11 and Q16 at fluency — screens ask “what is a token?” and “why not dump the PDF into a 1M window?”

**Roles that still get asked:** every applied-AI loop. Fine-tuning appeared in **8.5%** of the ~889 January 2026 AI Engineer JDs; “should we fine-tune the wiki?” appears in far more interviews as a trap. RAG was **35.9%**; agents **14.4%** and rising. This chapter is the substrate those topics sit on.

---

## Interviewer intent

They are not hiring you to recite the transformer paper. They are hiring you to **budget the window, the bill, and the failure modes** of a non-deterministic next-token machine.

| Signal | Pass | Fail |
| --- | --- | --- |
| Tokens are a contract | You count, cap, and know tokenizer pitfalls | “A token is a word” |
| Context is scarce | You design what enters the window | “The model has 200k, paste it” |
| Sampling is a product knob | Temp/top-p tied to task; greedy for facts/JSON | “We use 0.7 because that’s the default” |
| Serving literacy | Prefill vs decode, KV growth, TTFT vs TPOT | “The API is just slow sometimes” |
| Decision tree | Prompt → RAG → route → fine-tune last | Fine-tune first, or LLM for everything |
| When *not* | Named substitutes (SQL, rules, regex, HITL) | “We can prompt it to be accurate” |

**The highest-signal 2026 question in this chapter:** *When should this not be an LLM?*

If you cannot answer that, the rest of the vocabulary is decoration.

---

## Probability ranking (applied AI loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | Tokens / what you actually pay for | Almost certain | Count + pitfalls + cap |
| 2 | Context window vs usable context | Almost certain | Budget the window |
| 3 | RAG vs fine-tune vs prompt | Very high | Decision tree, not a preference |
| 4 | Cost math (in vs out vs cache) | Very high | Back-of-envelope + $/task |
| 5 | Structured output / tool calls | Very high | Schema + validate + runtime |
| 6 | Sampling for facts vs creative | High | Task-specific knobs |
| 7 | Prompt vs context engineering | High | What enters the window |
| 8 | Lost-in-the-middle | High | Position + rerank + cap k |
| 9 | Prefix / prompt cache | High | Identical prefix + tenant key |
| 10 | Model routing small→large | High | Cascade + escalation rate |
| 11 | TTFT / TPOT / prefill vs decode | High on infra; medium otherwise | Waterfall, not “streaming fixes it” |
| 12 | KV cache / batching / quant | Medium; **core on serving JDs** | Math-lite + OOM story |
| 13 | Attention intuition | Medium | Why long context costs; not a derivation |
| 14 | Embeddings vs generators | Medium–high | Different models, different jobs |
| 15 | Streaming / stop / logprobs | Medium | UX + parse + cancel |
| 16 | When *not* to use an LLM | High as a closer | Blacklist + alternative |

**MARKET OBSERVATION:** LLM internals are ~20% of technical signal in applied loops (Chapter 01). That is not “derive attention.” That is tokens, context degradation, sampling, serving, and cost. Training GPT from scratch is not the job.

---

## How to study this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Then the deep cut. Write *your* six-part card: concept → logic → structure → keywords → example → trade-off. Invent one follow-up.

Do not memorize tokenizer names. Interviewers change the wording: “context limit,” “why is this $4k this week,” “JSON keeps breaking,” “first token is slow.” The test is: can you **attribute** tokens, latency, and quality to a stage.

---

## The one diagram you should be able to draw

```
User / tool / retrieved text
        │
        ▼
 Tokenize  ──►  count + cap  ──►  refuse or compact
        │
        ▼
 Assemble window (context engineering, not “the prompt”)
   [system | tools | static policy]  ← prefix-cacheable, tenant-keyed
   [history compact | memory]
   [retrieved chunks: gold at head+tail, not a dump]
   [user]
        │
        ▼
 Route:  rules/small model  ──hard/uncertain──►  large model
        │
        ▼
 PREFILL (compute-bound) → KV for the prompt → TTFT
        │
        ▼
 DECODE (memory-bound)  → sample (temp/top-p/greedy)
                        → structured decode if JSON/tools
                        → stop: EOS / stop seq / max tokens / schema done
        │
        ▼
 Stream tokens (SSE) ──► validate ──► cite / tool runtime / user
```

Most production “prompting” problems are **window-assembly** problems. Most “the model is slow” problems are **prefill on a fat context** or **decode under KV pressure**.

---

## Production LLM checklist (say this unprompted)

If you call a model in production, you owe:

1. **Pinned model ID** — not `latest`. Rollback is a pin flip (Chapter 17).
2. **Token budgets** — max input, max output, max $/task, per tenant.
3. **Tokenizer that matches the model** — count before send; fail closed on overflow.
4. **Window policy** — what is allowed in, in what order, with what truncation.
5. **Sampling policy per route** — greedy/low-T for facts and JSON; higher T only where evals say so.
6. **Structured outputs validated in code** — schema, then Pydantic; never `json.loads` and hope.
7. **Cache keys that include tenant + prompt version** — prefix cache is a leak if they do not.
8. **Streaming with cancel** — TTFT SLO; do not stream partial tool JSON into an executor.
9. **Traces** — tokens in/out/cached, TTFT, TPOT, finish_reason, model pin (Chapter 17).
10. **A “not an LLM” path** — lookup, SQL, rules, regex, HITL. Written down.

Missing the budget or the pin is a mid-level ceiling. Missing “when not” is a senior ceiling.

---

## Q1. What is a token, and why does tokenization matter in production?

**Why they ask.** Billing, context caps, and a class of silent bugs (truncated JSON, multilingual blow-ups, “this UUID ate 20 tokens”) all live here. Juniors say “a word.” Seniors count.

**What they expect.** Token ≠ word ≠ character. The tokenizer is model-specific. You count before send, you cap, you know what tokenizes *badly*.

**Answer structure keywords.** subword · BPE · model-specific · count before send · cap · numbers/code/CJK · tokenizer mismatch · finish_reason=length.

**30-second.** A token is a subword unit the model actually consumes and emits. English is often ~0.75 words/token; code, UUIDs, numbers, and CJK can be much worse. Each model has its own tokenizer — you cannot reuse GPT counts on Anthropic or a self-hosted Llama. I count with the matching tokenizer, cap input and output, and treat `finish_reason=length` as a product bug, not a curiosity.

**2-minute.** Production effects:

- **Cost.** Input and output are priced per token, not per character. Output is usually several times input. A verbose system prompt is a recurring tax.
- **Context.** The window is in tokens, including system, tools, history, retrieved chunks, and reserved output. A “120k context” with 80k of RAG and 30k of tools has almost no room for the user.
- **Quality.** Truncating the *end* of a JSON schema or a table is how structured output “randomly” fails. Truncating a retrieved clause is how RAG misses the exception paragraph.
- **Pitfalls.** Leading spaces, markdown fences, and repeated punctuation can be surprising. A 36-char UUID is not 36 tokens. Splitting on characters then embedding can cut a token in half and hurt retrieval (Chapter 14).

I log `input_tokens`, `output_tokens`, `cached_tokens` on every span. I unit-test a fixture of ugly strings through the real tokenizer: SKUs, emails, CJK, code, HTML.

**Senior / deep.** Tokenizer mismatch is an incident class: you budget with `tiktoken` cl100k and ship to a model that uses another vocab — overflow in prod, undercount in staging. Pin tokenizer + model together. For serving, prefill cost tracks **input tokens**; decode tracks **output tokens**; KV tracks **input+generated so far**. A “cheap” 8k system prompt that never changes should be prefix-cached (Q8). A 8k prompt that is rebuilt with a timestamp every call will never hit cache and will look like a cost regression.

Do not build a chunker on characters (Chapter 10). Chunk on tokens of the *embedding* tokenizer for retrieve, and pack the generation window with the *generator* tokenizer. They are often different.

**Weak answer.** “A token is about four characters or three-quarters of a word.”

**Mistakes.**

- Using one tokenizer for every vendor.
- Caps only on output; input RAG unbounded.
- Ignoring `finish_reason`.
- Splitting chunks on `len(text)` and calling it token-aware.
- Putting a full base64 file in the prompt “because it is just text.”

**Follow-ups + strong replies.**

- *“How do you count before the call?”* — Matching tokenizer in the gateway. If the vendor exposes a count endpoint, still local-count for the hot path; the endpoint is a check, not the cap.
- *“Why did Japanese cost 3×?”* — Worse fertility. I budget per language slice, not a global English average.
- *“BPE vs WordPiece vs Unigram?”* — Interview-enough: most LLMs are BPE-family; the production fact is *incompatibility*, not the merge algorithm.

**Example.** A support bot stuffed raw HTML emails into context. Average 2.4k tokens/turn became 11k on threads with signatures and base64 logos. TTFT doubled, bill 4×. Fix: strip MIME, cap quoted history, hash attachments to object storage, never inline. Same model, different window.

---

## Q2. Context windows — advertised vs usable. Why not dump the corpus?

**Why they ask.** “We have 1M context, skip RAG” is a 2026 disqualifier (Chapter 04, Chapter 20). They want a budget, not a marketing number.

**What they expect.** The window is shared. Quality and cost degrade long before the hard limit. RAG still exists.

**Answer structure keywords.** advertised vs usable · reservation for output · tools+system+history · lost-in-the-middle · prefill cost · ACL · citations.

**30-second.** The advertised window is a maximum, not a strategy. Usable context is what remains after system, tool schemas, history, and reserved output. Dumping PDFs hits cost, TTFT (prefill), lost-in-the-middle, and ACL: you cannot paste tenant B’s drive just because it fits. I retrieve a handful of chunks, pack them on a token budget, and keep long context for *already-allowed* working sets — a single contract, a thread — not a corpus.

**2-minute.** I draw a budget on the board, e.g. 32k usable:

| Slice | Budget | Rule |
| --- | --- | --- |
| System + citation policy | 1–2k | Versioned, cacheable |
| Tool schemas | 1–3k | Few tools or retrieve schemas (Chapter 11) |
| History | 4–8k | Compact; never unbounded |
| Retrieved / files | 8–12k | Rerank to 3–8 chunks |
| User | 1–2k | Cap |
| Reserved output | 2–4k | Or JSON will truncate |

Long-context models help when the relevant text is already a small set (the 80-page agreement the user attached). They do not replace an index over 2 million docs. Prefill scales with input tokens: a 200k dump makes TTFT a product incident even if the model “supports” it. I also cannot cite “page 400 of the paste” as reliably as a chunk ID with a source URI.

**Senior / deep.** Three different limits people collapse: (1) **training / RoPE length** — quality past the length the model was trained or extended for; (2) **serving limit** — KV RAM, max_seq the engine allocated; (3) **product limit** — what you allow so p95 and $ hold. I set (3) well under (2). Position: instructions at the start *and* a short recap at the end; retrieved gold should not sit in the mushy middle (Q3). For agents, the window is a working memory with eviction, not a diary (Chapter 11). For multi-tenant SaaS, a huge window is a **leak surface** (OWASP LLM02 / LLM08): more tokens of other people’s data you might have retrieved by mistake.

**Weak answer.** “GPT-4o-class models have huge context so RAG is obsolete.”

**Mistakes.**

- Treating 128k/200k/1M as free.
- No reservation for output.
- Stuffing all tool results forever.
- Using long context to dodge ACL and chunking work.

**Follow-ups + strong replies.**

- *“Vendor says needle-in-a-haystack is solved.”* — Synthetic needles ≠ enterprise policies with conflicting clauses. I still retrieve and I still eval on *our* queries.
- *“User attached three PDFs.”* — If they are in-session and allowed, long context or a session index. If they asked about the company wiki, retrieve.
- *“Can we summarize the corpus into the prompt?”* — Lossy, stale, un-citable. That is a blog, not an architecture.

**Example.** A legal FDE demo: customer wanted “the whole matter file in the window.” 400 PDFs. We built a matter-scoped index (hybrid + rerank), packed ≤8 chunks, and used long context only for the single exhibit the lawyer opened. Citation accuracy became measurable; the dump demo was impressive and wrong.

---

## Q3. What is lost-in-the-middle, and what do you actually do about it?

**Why they ask.** It is the operational name for “we retrieved the right paragraph and the model still ignored it.” Rank 21 in Chapter 04; it shows up inside RAG debug (Chapter 10).

**What they expect.** U-shaped attention to position: models use the beginning and end of the window better than the middle. Fixes are packing and retrieval, not a pep-talk in the system prompt.

**Answer structure keywords.** U-shaped · position · pack gold at head+tail · rerank · cap k · recency · do not stuff.

**30-second.** Lost-in-the-middle: given a long prompt, models disproportionately use content at the start and end and under-use the middle. If your best chunk is rank-6 of 20, it may as well be missing. I rerank, send 3–8 chunks, put the highest-scoring evidence first *and* repeat the question plus citation rules at the end, and I refuse to stuff 30 snippets because “there is room.”

**2-minute.** Interview-safe actions:

1. **Retrieve less, better.** Hybrid + rerank so the right span is in the top 3 (Chapter 10, Chapter 14).
2. **Pack on purpose.** Descending score, or best-first + best-last with filler in the middle if you must send more.
3. **Repeat the task at the end.** “Answer using only the sources. If they do not contain it, say you do not know.”
4. **Parent expansion, not more neighbors.** One right section beats ten near-misses.
5. **Measure.** Ablate: move the gold chunk to position 1, middle, last on a frozen set. If middle tanks, your packer is the bug.

This is why “200k dump” fails even when the needle is present. Presence ≠ use.

**Senior / deep.** Lost-in-the-middle is an attention allocation problem, not a moral failing of the model. Long-context training and better positional schemes (RoPE scale, ALiBi-class, recency biases) *reduce* it; they have not made packing optional on enterprise RAG. Conflicting chunks in one window produce a different failure: the model averages or prefers pretraining. I would rather send two consistent clauses and abstain than ten that disagree without a recency/source-priority rule. For agents, a 40-page tool dump in the middle of the transcript is the same bug — cap and summarize observations (Chapter 11).

**Weak answer.** “We tell the model to read carefully.”

**Mistakes.**

- k=20 “to be safe.”
- Chronological chunk order that buries the match.
- Deduping so hard you drop the only supporting table.
- Evaluating only with gold at position 0.

**Follow-ups + strong replies.**

- *“Does the U-shape still hold in 2026?”* — Less on some long-context pins, still enough that I eval position. I do not bet the product on a blog that says it is solved.
- *“Multi-hop?”* — Two retrieves beat one stuffed window. GraphRAG is optional (Chapter 10); a workflow with two retrieval nodes is usually enough.

**Example.** Policy bot: gold exception lived in chunk 12/20. Faithfulness 0.71. Rerank to 5, best chunk first, question restated at end: 0.89, +0 tokens of model, −60% input. The model did not get smarter; the window got honest.

---

## Q4. Embedding models vs generation models — what is the difference, and when do you use each?

**Why they ask.** People call “the LLM” for both retrieval and answers. Wrong model, wrong metric, wasted money.

**What they expect.** Different jobs, different weights, different evals. You do not generate with an embedding model; you do not embed a corpus with a chat checkpoint unless it has an embedding head you actually eval.

**Answer structure keywords.** bi-encoder · cross-encoder · decoder LLM · same-model contract · rerank · do not mix spaces.

**30-second.** An embedding model maps text to a fixed vector for *similarity*. A generation model maps a prefix to the next tokens. I embed with a pinned retrieval model, generate with a pinned chat/completion model, and I rerank with a cross-encoder (or a small LLM) that scores (query, passage) together. Mixing embedding spaces or using a chat model as a cheap embedder without a contract is how recall dies.

**2-minute.**

| Kind | Input → output | Use |
| --- | --- | --- |
| **Bi-encoder** | Text → vector; query and doc encoded separately | Fast retrieval, ANN (Chapter 14) |
| **Cross-encoder** | (query, doc) → score | Rerank 50–100 candidates |
| **Generative LLM** | Tokens → tokens | Answer, extract, plan, tool call |
| **LLM-as-embedder** | Hidden state pooled | Only if the vendor ships it and you eval; not “mean pool GPT” |

I pin three IDs: embedder, reranker, generator. Changing any one is a release (Chapter 17). Embeddings do not “understand” in the chat sense; they induce a geometry. Generators can ignore retrieved geometry entirely — that is why RAG still needs a grounding prompt and citations (Chapter 10).

**Senior / deep.** Asymmetric embedders (`query:` vs `document:` prefixes) are a silent recall bug if you encode queries with the doc prefix. Matryoshka models let you store 256-d and optionally rerank with full dim — a cost lever, not magic. Do not use the generator as a reranker on 100 chunks in the user path unless you have measured the extra tokens; a specialized cross-encoder is usually cheaper and more stable. Multimodal: a vision-text embedder and a vision-language generator are again different contracts. Security: embedding inversion and vector poisoning are OWASP LLM09 territory — treat vectors as sensitive if the corpus is.

**Weak answer.** “We use OpenAI for everything — embeddings and GPT.”

**Mistakes.**

- One model ID for embed and chat.
- Reranking by cosine only and calling it “semantic ranker.”
- Fine-tuning the generator to “remember” the wiki instead of embedding it.

**Follow-ups + strong replies.**

- *“Can the LLM rewrite the query instead of embedding the raw user text?”* — Yes, that is query rewriting (Chapter 10). Still embed the rewrite with the embedder.
- *“Late interaction / ColBERT?”* — Higher recall possible; storage and serving jump. Default is single-vector + hybrid + rerank.

**Example.** Team used the chat model to “score relevance” on 50 chunks every query. Cost 8× a cross-encoder, p95 +1.4s. Switched to bge-reranker-class model, kept the LLM for generation only. Recall@5 up, bill down.

---

## Q5. Explain attention at interview depth (no paper derivation).

**Why they ask.** They want to know whether long context, KV cache, and GQA are mysteries. Research loops derive. Applied loops want *consequences*.

**What they expect.** Q/K/V in words, causal mask, multi-head as subspaces, why decode can reuse K/V, why naive attention is expensive in sequence length.

**Answer structure keywords.** QKV · causal · softmax over keys · multi-head · KV cache · GQA/MQA · quadratic · prefill vs decode.

**30-second.** Each new token produces a query and compares it to the keys of tokens that are allowed to be visible — previous tokens in a causal LM. Softmax turns those scores into weights; the weighted values become the signal for that head. Multi-head means several of these in parallel, different subspaces. We cache keys and values so we do not recompute the whole prompt at every generated token. That cache is why long context and high concurrency eat GPU memory.

**2-minute.** What I actually use in design:

- **Prefill:** all prompt tokens attend (under the mask) in a chunk. Compute-heavy. Dominates TTFT when the RAG context is fat.
- **Decode:** one token at a time. Each step is a tiny matmul plus a read of the entire KV cache. Memory-bandwidth bound. Dominates TPOT.
- **Quadratic warning.** Naive attention is O(n²) in sequence. Serving stacks use optimized kernels and, at long n, sparse/linear tricks; I do not pretend I implemented FlashAttention, but I know *why* 8× context is not 8× free.
- **GQA/MQA.** Fewer KV heads than query heads so the cache is smaller. Interview-relevant because it changes the KV math (Q13).

I will write `softmax(QK^T / √d) V` if they want the formula. I will not spend five minutes on it unless they are a lab.

**Senior / deep.** RoPE / ALiBi are positional schemes; interview-enough: they encode *order* so the model is not a bag of tokens, and extending context is a training/serving choice with quality risk past the trained length. Cross-attention vs self-attention: only if they ask (encoder-decoder). For applied work, “the decoder is causal self-attention plus an MLP block, stacked.” Speculative decoding and sliding-window attention are optimizations; name them as follow-ups, not as the definition.

Attention is also why **lost-in-the-middle** exists: the softmax is a finite budget over n keys. It is why **prefix caching** works: the KV for a shared prefix can be reused if the prefix bytes match. It is why **injection** works: hostile text in the window gets to attend like any other token — the model does not have a hardware “trust bit” (Chapter 19).

**Weak answer.** “Attention lets the model focus on important words. Transformers replaced RNNs.”

**Mistakes.**

- Deriving for six minutes in an FDE loop.
- Saying KV cache stores *attention weights* (it stores K and V).
- Claiming 1M context is O(1).

**Follow-ups + strong replies.**

- *“Why is decode memory-bound?”* — Tiny compute per token, huge KV read. Utilization looks low; bandwidth is the constraint.
- *“What is a head?”* — One QKV set; d_model split across heads. More heads ≠ automatically better; architecture choice.
- *“Does the model ‘look at’ retrieved docs specially?”* — No. They are just tokens. Prompting and packing are how we *ask* it to prefer them.

**Example.** p95 TTFT jumped after “add more context.” Decode TPS unchanged. That isolates prefill/attention over a fatter prompt, not a slow sampler. We cut k and prefix-cached the system prompt.

---

## Q6. Sampling: temperature, top-p, top-k, greedy — what do you set in production?

**Why they ask.** Defaults leak into factual products. They want a policy per route, tied to evals.

**What they expect.** Greedy/low-T for extraction, JSON, citations. Nucleus for language that may vary. Never “0.7 everywhere.” How sampling interacts with structured decode.

**Answer structure keywords.** logits · greedy · temperature · top-k · top-p · seed · eval vs prod · constrained decoding.

**30-second.** The model scores every next token. **Greedy** takes argmax — deterministic given the prefix, tends to loop on degenerate text, best starting point for facts and JSON. **Temperature** flattens or sharpens the distribution. **Top-k** keeps k tokens; **top-p** keeps the smallest set with cumulative probability p. For RAG answers and tool arguments I use T≈0–0.2, often greedy, plus schema constraints. I raise T only on routes where evals show diversity is the product.

**2-minute.** Practical table:

| Route | Setting | Why |
| --- | --- | --- |
| JSON / tool args | Constrained decode, T=0 | Invalid JSON is a P1 |
| Factual RAG | T=0–0.2, low top-p | Cite or abstain |
| Classification / routing | T=0, logprobs optional | Stable labels |
| Creative copy | T=0.7–1.0, top-p 0.9 | Variety |
| Evals | Frozen T, seed if API allows | Comparable runs |

Top-p and temperature **together** without a policy is how you get irreproducible bugs. I pin sampling in the prompt registry next to the model ID (Chapter 17). I never let the client pass `temperature=2`. Seed is not a guarantee across vendor versions or batching; I do not promise bit-identical legal text from an LLM.

**Senior / deep.** Sampling cannot fix a missing chunk. If faithfulness is low, do not raise T “to be more careful” — that is backwards. Constrained decoding *overrides* sampling for illegal tokens (Q7). Beam search is rare in chat APIs; I mention it for offline extractors. **Repetition:** presence penalty / stop sequences / max tokens; an agent that retries a tool is a loop cap problem, not a temperature problem (Chapter 11). For judges, T=0. For user-facing streaming, T low enough that the first 20 tokens are not a different product every refresh.

**Weak answer.** “We use temperature 0.7, top-p 1, that’s OpenAI’s default.”

**Mistakes.**

- High T on policy answers.
- Changing T to “fix hallucinations.”
- Different sampling in eval vs prod.
- Assuming T=0 is fully deterministic across providers.

**Follow-ups + strong replies.**

- *“Top-p or top-k?”* — I default top-p for open language; top-k if I need a hard vocab cap. For production JSON I want neither, I want a schema.
- *“Why did greedy loop ‘thank you thank you’?”* — Degenerate repetition. Stop sequences, max tokens, or a slightly higher T with a repetition penalty — and check the prompt is not empty of task.

**Example.** Extractor at T=0.8 produced different invoice totals on replay. Finance rejected the tool. T=0 + JSON schema + numeric validation against the source string. Variance went to zero on the field that mattered.

---

## Q7. Structured output, JSON schema, and function calling — how do you make the model reliably emit types?

**Why they ask.** Parsed JSON is how language becomes software. “Usually valid” is not an interface.

**What they expect.** Schema, constrained decoding when available, validate in code, typed errors back to the model, never execute invalid tool calls.

**Answer structure keywords.** JSON Schema · constrained decoding · function/tool calling · Pydantic · validate then execute · retry once · tool ≠ REST dump.

**30-second.** I do not prompt “respond in JSON” and pray. I give a schema, use the provider’s structured-output / tool-call mode (constrained decoding when the stack has it), parse into Pydantic, and **reject** on extra fields or type errors. Function calling is the model proposing a typed action; the **runtime** executes after allowlist, schema, and authz (Chapter 11). Invalid calls return a typed error; they never best-effort run.

**2-minute.** Layers:

1. **Interface.** Tools: name, description, JSON Schema. Final answers that a service consumes: same, with `additionalProperties: false`.
2. **Decode.** Constrained decoding (grammar / xgrammar / outlines / provider json_schema) makes illegal tokens un-sampleable. If the API is prompt-only, I still validate and allow **one** repair turn.
3. **Semantic checks.** Amounts in range, IDs match regex, enums closed.
4. **Execution boundary.** Tools go through the gateway. Structured *answers* go to the client only after schema + policy (PII, injection). OWASP LLM10: do not `eval` or `innerHTML` model output.
5. **Observability.** `finish_reason`, parse_fail rate, repair rate. Alert if parse_fail > 1%.

Fewer, non-overlapping tools beat 30 OpenAPI endpoints dumped into the schema list.

**Senior / deep.** Constrained decoding is not free: grammars can *force* a JSON shape that is semantically empty (`"amount": 0`). Schema-correct ≠ task-correct. I eval both. Unions and recursive schemas are where grammars get flaky — I flatten. For enums that change weekly, version the schema with the prompt. **Function calling vs JSON mode vs MCP:** function calling is the in-app contract with one model runtime; MCP is a bus for many hosts (Chapter 12); neither replaces validation. Parallel tool calls: validate each, cap fan-out. Streaming structured output: buffer until the object is closed; do not execute a partial `{"refund": 10` as 10.

**Weak answer.** “We use function calling so the JSON is always valid.”

**Mistakes.**

- `json.loads` in a try/except that then regex-scrapes.
- Executing unknown tool names.
- Schema in the prompt only, no runtime check.
- Letting the model invent SQL or shell.

**Follow-ups + strong replies.**

- *“What if the schema is too tight and the model fails?”* — The tool is too coarse or the description is bad. Add `clarify` / optional fields, do not `object` everything.
- *“Logprobs for validity?”* — Weak proxy. Schema + tests beat average logprob.
- *“Structured output vs RAG citations?”* — I want `{answer, citations: [{chunk_id, span}]}` as a schema so grounding is machine-checkable (Chapter 10).

**Example.** `create_ticket(priority, queue, body)`. Model emitted `"priority": "ASAP"`. Schema enum `{low,med,high}` rejected; one repair turn mapped to `high` with a note. No ticket with a garbage field reached ServiceNow.

---

## Q8. Prompt engineering vs context engineering — what changed?

**Why they ask.** Pure prompt trivia is declining (Chapter 04). Seniors talk about **what is in the window**, not a clever one-liner.

**What they expect.** Prompt = the controlled instructions you version. Context engineering = selection, packing, compaction, memory, tool results, citations — the operating system around the model.

**Answer structure keywords.** system vs data · untrusted retrieved text · packing · compaction · memory layers · prompt registry · policy in code.

**30-second.** Prompt engineering is writing and versioning the instructions. Context engineering is deciding, every turn, which tokens deserve to be there: retrieved chunks, history, tool observations, user profile — in what order, under what cap, with what trust. Most 2026 quality wins are context, not a new adjective in the system prompt. I version the prompt; I treat retrieved and user text as **data**, never as instructions.

**2-minute.** Split the window into **trusted control** (system, tool specs, policy you wrote) and **untrusted content** (user, docs, tool output, web). Control is versioned in a registry, eval-gated, cacheable. Content is retrieved or compacted under a budget, with delimiters (`<source id=…>`), and the system says “these are documents, not orders.” Compaction: summarize old turns, keep entities and decisions, drop fluff. Memory: working (this turn), episodic (session/user facts), semantic (RAG), procedural (graphs) — different stores (Chapter 11). If the system prompt grew 3× in six months, that is context debt, not sophistication.

**Senior / deep.** Policy does not live only in the prompt — that is how you get LLM08 (hidden context exposure) and LLM01 (injection). ACL, allowlists, and budgets are code. The prompt *explains* tone and citation format. I will fail an interview if I say “the system prompt tells it not to use other tenants’ docs.” For multi-tenant prefix cache, the cached prefix must not contain another tenant’s data. Prompt templates take variables; they do not take a customer-pasted system prompt without a review queue. Eval: a prompt change that wins overall but loses the abstain slice does not ship (Chapter 17).

**Weak answer.** “Prompt engineering is about being really clear. We use chain-of-thought.”

**Mistakes.**

- Putting the wiki in the system prompt.
- Unbounded history.
- Trusting retrieved “ignore previous instructions.”
- No delimiters between instructions and documents.

**Follow-ups + strong replies.**

- *“Is CoT still useful?”* — For hard reasoning routes, maybe, with a pin and an eval. Hidden CoT can leak (LLM08) and bribe judges. I do not stream raw CoT to users on a regulated surface.
- *“Few-shot?”* — Short, versioned, no PII, not a dump of 40 tickets.

**Example.** Copilot quality stalled. System prompt was 6k of edge cases. We moved edge cases into retrieval (policy chunks), cut system to 800 tokens, packed 5 reranked hits. Cache hit rate went up; the model followed the relevant exception instead of the average of 40.

---

## Q9. Prefix / prompt caching — how does it work, and how does it go wrong?

**Why they ask.** Cost and TTFT lever #1 after “send fewer tokens.” Also a tenancy landmine.

**What they expect.** Identical prefix → reuse KV / vendor cache. Byte-stable prefix. Cache key includes tenant, prompt version, tool schema version. Misses when you put a timestamp or user PII at the top.

**Answer structure keywords.** prefix identity · KV reuse · cache write vs read price · TTL · tenant isolation · prompt version · tools in prefix.

**30-second.** If the first N tokens are identical to a recent call, the serving stack can reuse the prefilled KV instead of paying full prefill. Vendors expose this as prompt cache; vLLM-class engines do automatic prefix caching. I put the static system + tools first, keep them byte-identical, and I **never** share a prefix across tenants. Cache is a performance feature; isolation is a security feature.

**2-minute.** Rules I ship:

1. **Stable prefix.** System, tool schemas, static policy. No `datetime.now()`, no user name, no request id at token 0.
2. **Dynamic suffix.** User, retrieved chunks, session.
3. **Keys.** `tenant | prompt_ver | toolset_ver | model_pin | prefix_hash`. Cross-tenant hit is a P0.
4. **Economics.** Cache write is often pricier than a hit; high-churn unique prefixes do not pay. Measure hit rate.
5. **RAG tension.** Retrieved chunks in the prefix kill sharing. I cache the instructions, not the docs, unless the same doc set is reused (a course, a runbook) and ACL-identical.

If TTFT regresses after a prompt edit of one character at the top, I assume a cache stampede miss.

**Senior / deep.** Two layers: **vendor prompt cache** (billed cached tokens) and **engine automatic prefix cache** on a self-hosted replica (KV pages). Operationally both care about prefix identity. On multi-LoRA or multi-model gateways, cache is per `(model, adapter, prefix)`. TTL and eviction: a cold replica has no cache — autoscale looks like a latency incident. **Security:** cached KV is still residual information; isolate GPU tenants if that is the threat model; never log prefixes with secrets. OWASP LLM08: dumping “the cache” or the system prompt to the user is a disclosure bug. For Bedrock/Anthropic/OpenAI, I read the current cache breakpoint API — I do not memorize last year’s parameter names in the interview; I memorize the *identity* rule.

**Weak answer.** “We turn on prompt caching and save 90%.”

**Mistakes.**

- User-specific text at the start of the system prompt.
- Cache key = prompt text without tenant.
- Putting retrieved chunks before the static policy.
- Assuming cache survives a model pin change.

**Follow-ups + strong replies.**

- *“Can I cache RAG chunks?”* — Yes if the chunk set is a repeated, ACL-homogeneous working set. Default no.
- *“Why hit rate 0 after we added a tool?”* — Tools are in the prefix; schema change busts cache. Version deliberately.

**Example.** Multi-tenant SaaS put `You are helping {{company_name}}` as token 1. Cache hit 4%. Moved company name to a short suffix after a shared 2k prefix. Hit 70%, TTFT −40%, no cross-tenant keys.

---

## Q10. Cost math — how do you estimate and control spend?

**Why they ask.** Unbounded consumption is OWASP LLM06. Finance will ask. “Watch the dashboard” is not a control.

**What they expect.** Back-of-envelope with **in vs out vs cached**, cost per *successful task*, caps, routing, and what you cut first.

**Answer structure keywords.** $/1M in · $/1M out · cached rate · $/successful task · max tokens · routing · context cap · judge off the hot path.

**30-second.** I budget **cost per successful task**, not pride in token volume. Output tokens usually cost several times input; RAG context is the silent input killer; retries, tools, and judges multiply. I pin a price table, log tokens on every span, set max in/out and a hard $ cap, cache prefixes, route easy traffic to a small model, and I can shed to a cheaper pin without a code freeze.

**2-minute.** Whiteboard:

```
cost ≈  in_uncached * P_in
      + in_cached   * P_cache
      + out         * P_out
      + embed + rerank + tools + retries + online_judge
```

Example pin (illustrative, I would use the live table): $0.80/1M in, $4/1M out, $0.08/1M cached. A RAG turn with 4k in + 400 out ≈ $0.0048 uncached. 10k turns/day ≈ $48/day *before* a 10% retry tax and a 5% agent-loop tail. If we add 8k retrieved tokens, input triples. Levers in order: **cache → route small → shrink context → cap output → stop loops → batch embeddings → self-host only if volume/compliance says so.** I alert on spend *rate* and on cost/task drift, not only on the monthly invoice.

**Senior / deep.** Denial-of-wallet is security: injection or a recursive summarize should not print money. Per-session and per-tenant caps, independent of the model. **Reasoning/hidden tokens:** if the vendor bills them, they go in the table; I cap them per route. Agents: optimize $/success, which punishes loops that fail expensive (Chapter 11). Judges and nightly goldens have their own budget; they do not sit on every user request (Chapter 17). Provisioned throughput vs on-demand: buy PTUs when p95 is a product SLO and utilization is high; otherwise you are paying for idle. I will not “save money” by dropping traces.

**Weak answer.** “We’d switch to a cheaper model if the OpenAI bill is high.”

**Mistakes.**

- Counting only output.
- Unbounded max_tokens=4096 on a classifier.
- Online LLM-as-judge on 100% of traffic.
- No per-tenant cap.

**Follow-ups + strong replies.**

- *“How do you cost RAG?”* — Query embed (usually small) + retrieve infra + rerank + generation with chunks in the prompt + citation check.
- *“Output is 5× input price — so what?”* — Verbosity and “explain your reasoning to the user” are budget bugs. Schema + max_tokens.
- *“Self-host to save money?”* — Only with utilization math, GPU ops, and eval parity. Most mid-volume RAG teams lose.

**Example.** Agent averaged $1.80/task: full-page fetches + large model every step. Caps: 8 fetches, 15k chars/obs, small extract, large write, $0.60 hard stop. Success −3 points, $/success −4×. Product became viable.

---

## Q11. Model routing — why not always the largest model?

**Why they ask.** Rank 16 in Chapter 04. Cost/quality. “Always GPT-5-class” is a junior spend profile.

**What they expect.** A cascade: cheap first, escalate on uncertainty, hard slices, or policy. Measure escalation rate. Eval both rungs.

**Answer structure keywords.** cascade · classifier · uncertainty · hard slice · escalation rate · pin per rung · fallback · not a second brain.

**30-second.** I default small and specialized, escalate to large when a router (rules, classifier, or the small model’s own abstain) says the task is hard, high-risk, or low-confidence. Easy FAQ and extraction should never touch the frontier pin. If everything escalates, routing is theater. Both rungs are pinned and eval’d.

**2-minute.** Router designs, simplest first:

1. **Rules.** Path `/extract` → 8B; `/research` → large. Intent keywords. Latency-critical autocomplete → tiny.
2. **Classifier.** Cheap model or logistic on features (length, has_id, retrieval score).
3. **Generate-and-maybe-retry.** Small model answers; if faithfulness/citation check fails or it abstains, call large. Costs extra on the tail only.
4. **Risk.** PII, legal, money — force large *or* HITL, never the cheapest.

I log `route`, `escalated`, tokens, quality. Shadow the large model on a sample of small-model traffic to see missed wins. Fallback is not routing: if the large vendor 429s, a different large or a degraded small is a **reliability** path (Chapter 17), with a quality SLO that says we are in degrade.

**Senior / deep.** Routing is a product policy: which errors are acceptable on the cheap rung. I keep **hard slices** (numbers, dates, multi-hop, refusal) that always escalate until the small model beats the bar there. Multi-model gateways need fair queues so the cheap high-QPS path cannot starve the expensive interactive path. Do not let the *user* or the *agent* pick `model=best` unbounded — that is LLM06. For agents, route *per node*: extractor small, planner maybe large, verifier small (Chapter 11). Fine-tunes often exist *so that* the small rung can take more traffic (Q12).

**Weak answer.** “We always use the smartest model so quality is max.”

**Mistakes.**

- Router more expensive than the large model.
- No eval on the small rung.
- Escalation rate 90%.
- Different prompts per model with no versioning.

**Follow-ups + strong replies.**

- *“Semantic cache instead of routing?”* — Cache exact/near queries with ACL in the key. Complements routing; does not replace hard questions.
- *“Who owns the threshold?”* — Same as the ship bar. A 2-point quality drop for a 5× cost win is a PM signature, not a silent flag.

**Example.** 70% of copilot queries were “where is the form.” Distilled small model + RAG: p95 1.1s, $0.004. Remaining 30% escalate. Blended quality matched all-large; bill −55%.

---

## Q12. RAG vs fine-tune vs prompt — the decision tree.

**Why they ask.** Rank 8 in Chapter 04. Fine-tune-first is a negative signal. 8.5% of JDs mention fine-tuning; interviews use it as a judgment test.

**What they expect.** Prompt first, RAG for knowledge that changes or must be cited, fine-tune (often LoRA) for **behavior**. Combine when both exist. Never fine-tune a wiki.

**Answer structure keywords.** knowledge vs behavior · citations · change rate · eval · LoRA · still RAG after FT · cost of retrain.

**30-second.** If I can solve it with a better prompt and a tighter window, I do. If the model needs facts that are private, current, or citable, that is RAG (Chapter 10). If I need a stable *skill* — format, tone, tool-use style, domain dialect on a smaller model — I consider LoRA/SFT. Fine-tuning is not a knowledge base: it is slow to update, hard to cite, and bad at “forget this document.” Most enterprise assistants are prompt + RAG; FT is a later optimization.

**2-minute.** Tree I draw:

```
Need external / changing / citable facts? --yes--> RAG
        |
        no
Need a new behavior (schema, style, tools) that prompting cannot stabilize?
        |
        no  --> prompt + maybe few-shot
        yes --> consider SFT/LoRA on a small model, still keep RAG if facts move
```

Do **not** fine-tune for: weekly policy, SKUs, tickets, anything you must show a source for, anything you must delete on request (GDPR vs weights). Do consider FT for: JSON shape at high QPS on a small model, house style, language of a profession after RAG still sounds generic, distilling a large teacher. Prompting is the cheapest experiment; if 20 eval items do not move, more adjectives will not.

**Senior / deep.** LoRA vs full FT: LoRA is the default for cost and rollback (swap adapter). Full FT only with a platform team and a real corpus. RAG + FT is common: FT teaches *how to use* retrieved context (cite, abstain), RAG supplies the bytes. Preference methods (DPO etc.) are for alignment to a rubric, still not a wiki. Serving: adapters multiply memory; I cap how many hot LoRAs sit on a replica. Eval: a fine-tune that memorizes the golden set is leakage — hold out, and never drop the RAG eval. If the JD is LLM Engineer, I will discuss data mix, rank/alpha, and regression on a general bench so the adapter did not lobotomize the base. If the JD is GenAI/FDE, I stop at the tree unless they push.

**Weak answer.** “We’ll fine-tune on our documents so the model knows our business.”

**Mistakes.**

- FT as the first move.
- No citation plan after FT.
- Mixing train data with the eval set.
- Promising unlearning by “training a bit more.”

**Follow-ups + strong replies.**

- *“Vendor fine-tune API?”* — Same tree. Easier ops, worse control, data-handling review.
- *“Embeddings fine-tune?”* — Only with pairs and a retrieval eval that beats the base. Rerank first (Chapter 14).
- *“When did you refuse FT?”* — Have a story: 400-page policy pack. RAG + evals in two weeks; FT would have been a quarter and still stale.

**Example.** Sales copilot. CRM facts via RAG. Model kept writing casual email. 2k accepted emails → LoRA on a small model for tone; retrieval still for account data. Tone win without re-embedding the CRM nightly.

---

## Q13. Prefill vs decode, KV cache, TTFT, TPOT — explain with math-lite.

**Why they ask.** Rank 22 in Chapter 04. Serving-track core. Everyone else needs enough to debug “slow” and “OOM.” Chapter 17 asks the SLO version; this is the mechanism.

**What they expect.** Prefill = prompt → KV, compute-bound, drives TTFT. Decode = one token at a time, memory-bound, drives TPOT. KV grows with **batch × seq × layers × kv_heads × head_dim × dtype**. OOM at high concurrency is often KV, not weights.

**Answer structure keywords.** prefill · decode · KV cache · TTFT · TPOT · paged KV · continuous batching · GQA · concurrency × length.

**30-second.** Prefill reads the whole prompt and builds a key/value cache — that work dominates time-to-first-token. Decode writes one token, appends to KV, repeats — time-per-output-token is mostly loading that cache. Users feel TTFT as snappiness and TPOT as stream smoothness. E2E also includes retrieval and tools. I SLO all three. Fat RAG contexts hurt TTFT; high concurrency × long max length OOMs the GPU via KV.

**2-minute.** Formula I will write:

```
KV_bytes ≈ 2 * n_layers * n_kv_heads * head_dim * seq * batch * bytes
```

(`2` = keys and values.) GQA makes `n_kv_heads` ≪ query heads, which is why it exists. Example order of magnitude: tens to hundreds of KB per token per request, times concurrent sequences, times max length you *reserve*. If you allocate for 32k × 64 concurrent, you can blow HBM even if typical prompts are 2k.

**PagedAttention (conceptual):** KV in blocks, like virtual memory, so you do not pre-allocate a dense 32k slab per request. **Continuous batching:** iteration-level scheduling — a new request joins when another finishes a token, instead of waiting for the whole batch to complete. That is the difference between naive HF `generate` and a vLLM-class server on mixed lengths.

Debug: TTFT up, TPOT fine → prompt length, cache miss, queue, retrieval-before-first-token. TPOT up → GPU saturation, KV huge, throttle, wrong dtype. E2E up, token metrics fine → tools/rerank (Chapter 10, 17).

**Senior / deep.** I report TTFT **with** and **without** retrieval so a RAG regression does not look like a model regression. I separate interactive pools from long-context/batch pools so one 200k prefill does not stall chat. Quantizing KV (FP8/INT8) is a memory lever with a quality eval, same as weight quant (Q14). Speculative decoding: a small draft model proposes tokens, the large model verifies — helps TPOT when draft acceptance is high; it is not a TTFT miracle and it costs extra weights. For API-only GenAI roles I stop at: “TTFT≈prefill+queue, TPOT≈decode, KV grows with concurrent×length, I cap both.” For serving JDs I will talk `max_num_seqs`, GPU utilization target, and why the second 429 is sometimes self-inflicted concurrency.

**Weak answer.** “We stream so latency does not matter.” Or “KV cache is like Redis for prompts.”

**Mistakes.**

- One number called “latency.”
- Raising max context without recomputing KV headroom.
- Health checks that run a full generate.
- Batching interactive with offline summarization on one replica.

**Follow-ups + strong replies.**

- *“Why did we OOM after doubling context?”* — KV, not the 7B weights which already fit. Cut concurrency or KV-quant or GQA model.
- *“vLLM vs calling the vendor?”* — Vendor if ops/compliance dominate. Self-host if residency, unit economics at high utilization, or custom adapters. Not a religion.
- *“Time to first byte vs TTFT?”* — Headers can flush early. I measure first *model token*.

**Example.** GPU OOM at 40 concurrent, weights only 16GB on a 80GB card. Math: 32k reserved × 40 seqs × ~100KB/token-class cache. Fix: cap max_seq to 8k for that route, paged KV, separate long-doc worker. OOM gone; weights never moved.

---

## Q14. Quantization and batching — what literacy do they expect?

**Why they ask.** Serving and Cloud AI loops. They want trade-off language, not a CUDA résumé. Literacy, not a kernel paper.

**What they expect.** Why quantize (memory, throughput), what you eval after, how batching raises TPS and TTFT, continuous batching as the production default.

**Answer structure keywords.** weight INT8/INT4 · KV quant · quality eval · batch vs latency · continuous batching · utilization · not “no loss.”

**30-second.** Quantization stores weights (and sometimes KV/activations) in fewer bits so more model (or more KV) fits and bandwidth drops. INT8 is often near-parity; INT4 needs a real eval on *our* tasks, especially numbers and names. Batching groups requests to fill the GPU: throughput up, per-request wait can up. Production servers use **continuous** batching so short requests are not stuck behind long ones. I never claim “quantization has no quality cost.”

**2-minute.** I treat quant as a release: run the golden set, plus a numeric/code slice, plus a safety slice. If faithfulness drops more than the allowed delta, it does not ship (Chapter 17). Weight-only quant is the usual first lever; KV quant when OOM is cache (Q13). Batching: I set a max batch / `max_num_seqs` from measured HBM, not from a blog. Interactive SLO: smaller batches, more replicas. Offline embed/summarize: large batches. **Never** mix a 200k prefill into the interactive batch without isolation.

**Senior / deep.** GPTQ/AWQ/GGUF names are optional; the idea is calibration and which layers stay higher precision. MoE and very large models have their own serving story — I will not fake having sharded a 400B. For API users, “the vendor’s mini pin is a distilled/quantized product; I eval it as a different model, not as the same model cheaper.” Speculative decoding and quant compose: a quantized draft + fp16 target is a common pattern. Cloud: GPU instance choice is often “does KV+weights fit at our p95 context and concurrency,” not TFLOP theater.

**Weak answer.** “INT4 is 4× faster with the same quality.”

**Mistakes.**

- Quantizing without eval.
- One replica for interactive + batch.
- Tuning batch size on tokens/sec only, ignoring p95 TTFT.

**Follow-ups + strong replies.**

- *“When does batching hurt?”* — Low QPS (nothing to batch), or huge max wait for a full batch. Use a timeout to flush.
- *“CPU/GGUF in prod?”* — Edge, privacy appliance, or dev. Not my default for a 50-QPS RAG SLO.

**Example.** INT4 drop-in looked fine on chat vibes; invoice totals off by 10× on the numeric slice. Rolled back to INT8. Ship bar had the slice; vibes did not.

---

## Q15. Streaming, stop sequences, and logprobs — when do you use each?

**Why they ask.** Chat UX, JSON APIs, and “how confident is the model” as a trap.

**What they expect.** SSE/streaming for tokens the user reads; no streaming of partial tool JSON into executors. Stop sequences as hard halts. Logprobs as a weak signal for routing/classification, not a hallucination oracle.

**Answer structure keywords.** SSE · TTFT · cancel · stop sequences · EOS · logprobs · not a calibrated probability · buffer tool JSON.

**30-second.** I stream model text to humans so TTFT is the UX. I do **not** stream into a parser that executes tools — I buffer until the structured object is complete (or use a binary tool-call channel). Stop sequences end decoding at a fence, a delimiter, or a role token; they are a control, not a suggestion. Logprobs are the model’s token scores: useful for classifiers and sometimes routing; they are **not** calibrated P(true). I do not ship “if logprob < −0.5, abstain” as the only grounding strategy.

**2-minute.** Streaming: HTTP SSE or WebSocket; one trace stays open until `finish_reason` or client cancel. Cancel must abort GPU work or you pay. Backpressure: if the client is slow, buffer with a cap. **Stop:** e.g. stop at `\nUser:` so the model does not role-play both sides; stop at ` ``` ` when extracting a single block. Jailbreakers try to evade stops — still enforce max tokens. **Logprobs:** classification (argmax over label tokens), some speculative-decoding internals, debugging. For RAG, a high-confidence wrong answer is common — retrieval+faithfulness beat logprob (Chapter 10).

**Senior / deep.** Streaming and citations: you can stream tokens and attach citations at the end, or stream with delayed claim-check. I do not delay first token for a full judge. Improper output handling (OWASP LLM10): streamed markdown can XSS; sanitize on the client. Stop sequences in multiple encodings (with/without leading space) are a tokenizer footgun (Q1). For agents, `stop` is not a loop cap — runtime caps are (Chapter 11). Logit bias: rare, for forcing a yes/no token in a router; I prefer a schema.

**Weak answer.** “We stream everything and use logprobs to detect hallucinations.”

**Mistakes.**

- Executing partial JSON.
- No cancel path.
- Relying on stop strings the model can talk around, with no max_tokens.
- Showing logprobs to customers as “confidence 87%.”

**Follow-ups + strong replies.**

- *“What is finish_reason?”* — `stop` / `length` / `tool_call` / `content_filter`. `length` means I under-budgeted; I surface a truncated state, I do not parse half JSON as success.
- *“Should the API be sync for tools and stream for chat?”* — Yes, two response modes, one backend.

**Example.** Chat UI streamed a tool call as text; a flaky client concatenated two partial payloads and double-refunded. Fix: tool calls on a side channel, idempotency key, HITL above $50 (Chapter 11). Streaming stayed for the user-visible prose.

---

## Q16. When should you NOT use an LLM?

**Why they ask.** Senior closer. HM and FDE loops. The 2026 market is 95.6% production-focused; they have been burned by LLM-for-everything.

**What they expect.** A blacklist, a substitute architecture, and still using LLMs *around* the problem when they help.

**Answer structure keywords.** deterministic · lookup · SQL · latency · replay · math · ACL · eval-or-bust · workflow not generator.

**30-second.** I do not use an LLM when a deterministic system already solves it, when I need bit-identical replay, when the operation is arithmetic/aggregation over records, when latency is tens of milliseconds, when the answer is a single keyed lookup, or when I cannot evaluate success. I still might use an LLM to *draft* or *route* next to those systems. The model is not a database, not a calculator, not an ACL, and not a workflow engine.

**2-minute.** Blacklist:

| If the job is… | Use instead |
| --- | --- |
| Sum, join, filter rows | SQL / warehouse |
| Fetch order by ID | API + cache |
| Enforce who can see what | IAM + retrieval filters (Chapter 10, 19) |
| Stable regex / parse of a fixed format | Parser |
| Sub-100ms autocomplete of structured fields | Smaller specialized model or classical |
| Bit-identical legal boilerplate | Template |
| Known 8-step SOP | Workflow; LLM fills slots (Chapter 11) |
| No eval possible | Do not ship autonomy |
| Secrets that must never be in a prompt | Architecture change, not a promise |

Hallucinated SKUs, invented citations, and “GPT math” on invoices are predictable. I will use an LLM to *write* a SQL query I then run, not to *be* the database.

**Senior / deep.** The interesting “not” is **partial observability plus high blast radius** — same as agents (Chapter 11). Also **regulated replay**: if audit needs “why this exact sentence,” generate from a template + retrieved clause, or HITL freeze. Classification with abundant labels: gradient-boosted trees still win on tabular (classical ML is low probability in these titles — Chapter 04 — but it is the right tool). When I *do* use an LLM, I wrap it: schema, caps, RAG, abstain, traces. “LLM as the product” is rarely the architecture; “LLM as a bounded component” is.

**Weak answer.** “You shouldn’t use LLMs for simple chatbots.” Or “they hallucinate, so we won’t use them.”

**Mistakes.**

- Only citing cost.
- No alternative.
- Treating “not an LLM” as “not AI.”
- Using an agent to hide that the task was a lookup.

**Follow-ups + strong replies.**

- *“Can the LLM call SQL?”* — Yes, with allowlisted query templates or a read-only warehouse tool, validation, and row caps. The LLM still does not *be* SQL.
- *“Customer wants GPT on the homepage for order status.”* — Authenticated lookup, NL as a skin. Model never invents shipment state.
- *“What about coding?”* — Unknown path, reversible tools, tests as oracle — good LLM use with a sandbox. Still not prod credentials.

**Example.** A bank asked for “an LLM that decides refund eligibility.” Eligibility is a 12-rule table plus ledger balances. We implemented the table in code, used the model to extract fields from a letter, HITL on the edge cases. Zero autonomous money movement. That is also the agent answer (Chapter 11) — because it is the same judgment.

---

## Rapid-fire (30–45 seconds each)

**Token vs character?** Subword the model bills and attends over. Count with the matching tokenizer.

**Why not 1M-context dump?** Cost, prefill/TTFT, lost-in-the-middle, ACL, un-citable. Retrieve.

**Greedy vs temperature?** Argmax vs scaled sampling. Facts/JSON: greedy or ~0. Low T does not add missing evidence.

**What is a prefix cache key?** Tenant + prompt version + toolset + model pin + prefix bytes.

**TTFT vs TPOT?** First token (prefill+queue+sync work) vs per subsequent token (decode).

**Where does KV grow?** Concurrent sequences × length × layers × kv heads × dim × dtype.

**OOM after longer context?** Usually KV, not weights.

**Structured output without a schema?** Not production. Constrain + validate.

**Fine-tune the wiki?** No. RAG. FT is behavior.

**Always the largest model?** No. Route. Measure escalation.

**Logprobs = truth?** No. Uncalibrated token scores.

**Stop sequence enough to halt an agent?** No. Runtime step/$/time caps.

**Embedding model = chat model?** No. Different contracts. Pin both.

**When not to use an LLM?** Lookup, SQL, deterministic policy, hard real-time, no eval, ACL enforcement.

**OWASP hook for this chapter?** LLM06 unbounded consumption; LLM08 hidden context; LLM10 improper output; LLM01 injection via anything in the window.

---

## Weak vs strong posture (memorize the posture, not the paragraph)

| Weak | Strong |
| --- | --- |
| “A token is ~4 characters” | Matching tokenizer, count, cap, `finish_reason` |
| “1M context, skip RAG” | Usable budget, retrieve, pack, cite, ACL |
| “Temperature 0.7” | Per-route policy; greedy for facts/JSON |
| “Function calling is valid JSON” | Schema + constrained decode + Pydantic + authz |
| “We engineered a better prompt” | Context engineering: packing, caps, untrusted data |
| “Turn on caching” | Byte-stable prefix, tenant in the key |
| “Watch the bill” | $/successful task, kill switch, routing |
| “Fine-tune on our docs” | Prompt → RAG → FT for behavior |
| “Streaming fixes latency” | TTFT vs TPOT vs E2E; prefill on fat context |
| “The model is the ACL” | Code enforces; model explains |

---

## A complete example you can reuse in interviews

**Setting.** Internal policy copilot, 40k documents, 2k Q/day, citations required, p95 first token < 1.2s, cost cap $0.03/successful answer.

**Wrong design.** Frontier model, 80k pasted handbook, T=0.7, “reply in JSON,” no pin, no cap, fine-tune planned “so it knows policy.”

**Right design.**

1. **Not an LLM:** employee-id → HRIS lookup for *their* data. Policy *text* is RAG.
2. **Window:** 1.5k system (cite or abstain) + 5 reranked chunks ≤ 6k tokens + compact history. Gold chunk first, question last.
3. **Models:** embedder pinned; cross-encoder rerank; small generator default; large on low retrieval score or legal slice.
4. **Decode:** T=0, JSON schema `{answer, citations[]}`, validate; stream prose to UI after parse for the chat route.
5. **Cache:** static system+tools prefix, key includes tenant=`internal` + prompt_ver.
6. **Serving literacy:** TTFT includes retrieve; cap context so prefill holds SLO; if self-host, KV headroom at p95 length × concurrency.
7. **Evals:** faithfulness, citation accuracy, empty-retrieval abstain (Chapter 10, 17).
8. **Do not FT** the policy pack. If tone is wrong later, consider LoRA on the small rung.

**One sentence close:** “The model only sees a budgeted, ACL-legal window; code owns caps, schema, and lookups.”

That sentence is what a 2026 interviewer is listening for.

---

## Map to the rest of the handbook

- RAG packing, chunking, evals, empty retrieval: [10-rag.md](10-rag.md)
- Agents, tools, loops, HITL: [11-agentic-ai.md](11-agentic-ai.md)
- Embedding contract, ANN, hybrid: [14-vector-databases.md](14-vector-databases.md)
- TTFT/TPOT SLOs, pins, traces, cost dashboards: [17-llmops.md](17-llmops.md)
- Injection, tenancy, unbounded spend, output handling: Chapter 19 AI Security
- Design loops (“why not 1M context?”): Chapter 20–21
- Answer shapes: [05-answer-frameworks.md](../05-answer-frameworks.md)
- Probability: [04-topic-probability-ranking.md](../04-topic-probability-ranking.md)

Next drill: speak Q2, Q10, Q12, Q13, Q16 out loud. If those five are clean, you will survive most LLM screens. Add Q7 and Q9 for implementation rounds; add Q13–Q14 if the JD is serving-heavy.
