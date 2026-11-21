# 22 — Troubleshooting Production AI Incidents

**What this chapter is for:** so you debug in a fixed order under a panel, instead of guessing “maybe the prompt.”

Troubleshooting rounds (and the production stories inside behavioral / FDE loops) score one thing: do you *observe* before you change a model.

If your first sentence is “I’d switch to GPT-whatever,” you failed, even if a model change would eventually help.

---

## 1. The method: OBSERVE → ISOLATE → HYPOTHESIZE → VERIFY → FIX → PREVENT

Say the method out loud. Interviewers listen for the order.

| Step | You do | You do not |
| --- | --- | --- |
| **OBSERVE** | What changed, who is hit, what the user saw, when it started | Jump to a root cause |
| **ISOLATE** | Which layer: client, gateway, retrieve, rank, generate, tools, vector, GPU, cloud bill | Blame “the LLM” as a blob |
| **HYPOTHESIZE** | 2–4 ranked causes that match the evidence | A single pet theory |
| **VERIFY** | A log, metric, trace, or replay that would *disprove* each cause | Ship a fix to “see if it helps” |
| **FIX** | Smallest change that stops the bleeding, then the real fix | Prompt soup + restart all pods |
| **PREVENT** | Gate, alert, test, or design change so this class cannot silent-fail | “We’ll watch it” |

**Interview cadence (90–180 seconds, then go deeper):**

> I would treat this as a production incident, not a modeling puzzle. First I want blast radius and what changed. Then I split the pipeline with traces: is the time in retrieve, generate, or tools? I would form two or three hypotheses that fit the timestamps, verify with a replay or a metric, ship a mitigation that limits damage, then a durable fix and a regression test.

That paragraph is the skeleton. The incidents below fill it.

### Questions you almost always ask

- When did it start? Who is affected (one tenant, one region, one model, everyone)?
- What shipped in that window (prompt, index, model version, chart, embedding model, feature flag)?
- Is it latency, quality, cost, security, or correctness of side effects?
- Can we still serve a degraded path?
- Do we have traces for a failing request id?

### Metrics and logs you should name without being prompted

| Signal | Where |
| --- | --- |
| End-to-end p50/p95, TTFB, tokens in/out | APM + LLM tracer |
| Time split: rewrite / retrieve / rerank / generate / tools | Trace spans |
| Retrieval: empty rate, recall proxy, k returned, filter match count | Search logs |
| Provider: 429, 5xx, latency, token errors | Gateway / vendor dashboard |
| Agent: step count, repeated tool+args, HITL wait, unsafe-action | Graph / trajectory store |
| K8s: restarts, OOMKilled, CPU throttle, node disk | `kubectl`, events, container logs |
| Cost: tokens, embedding calls, GPU hours, egress, search units | Cloud billing + per-request cost span |
| Security: authz denies, cross-tenant retrieval hits, tool allowlist rejects | Audit log |

If the company has no traces, say you would add them — then still debug with what exists: timestamps, logs, one reproduced request.

---

## 2. How to talk so you sound like the on-call, not a blog

- Rank hypotheses. “I’d check X first because the timestamp matches the index swap.”
- Separate **mitigation** (stop the bleeding) from **fix** (correct the cause).
- Name a **prevent** that is a test or gate, not a standup promise.
- Do not trash the previous team. Describe the missing alarm.
- If you have not seen this exact incident, say so, then use the method. That is honest and senior.

---

## 3. Incidents

Each incident is written as a drill. Cover the answer, speak the six steps, then read.

---

### Incident 1 — LLM latency doubled

**User-visible:** Chat p95 went from ~3s to ~7s in 40 minutes. Error rate is flat.

#### OBSERVE

Ask: global or one tenant? One model deployment? Started at a deploy, a traffic spike, or a provider incident? Streaming still first-token-fast or slow throughout? Input length up?

Pull: end-to-end p95, TTFB vs full completion, tokens in / tokens out histograms, provider latency vs your queue time, cache hit rate, concurrency.

#### ISOLATE

Split the trace:

- App queue / GPU queue vs vendor `inference_ms`
- Retrieval span vs generate span
- Token count vs time (is it just longer answers?)

If generate span doubled and retrieve did not, stop looking at the vector DB.

#### HYPOTHESIZE (ranked)

1. **Context blew up** — prompt or retrieved k changed; tokens in doubled
2. **Provider degradation or noisy neighbor** on a shared endpoint
3. **Cache miss storm** (semantic cache or prompt cache invalidation)
4. **Concurrency / batching collapse** (batch size 1, no KV reuse, thread pool saturation)
5. **Retry amplification** (timeouts too tight; every request hits twice)

#### VERIFY

Compare median tokens in before/after. Diff the prompt version and `top_k`. Check vendor status and your 429/5xx (may still be “slow success”). Plot in-flight requests. Confirm whether streaming TTFB doubled (queue) or only total time doubled (longer generation).

#### FIX

Mitigate: pin previous prompt / `k` if you just shipped; route to a faster model for short queries; shed non-interactive load; raise timeouts only enough to stop retry storms, not to hide the issue.

Durable: cap retrieved tokens, rerank to smaller k, restore cache keys, separate interactive vs batch, fix pooling.

#### PREVENT

Alert on p95 **and** on tokens-in p95 (quality and cost will move together). CI check that prompt + max_k cannot exceed a token budget. Canary latency, not only error rate.

#### Interview 60s

> I would not switch models first. I would split retrieve vs generate vs queue, and check whether tokens-in doubled. Most “the LLM got slow” incidents I have seen were context growth, cache misses, or retry amplification. Mitigate by rolling back the prompt or k, then cap context and alert on token histograms.

---

### Incident 2 — RAG retrieval accuracy dropped

**User-visible:** Answers still fluent. Citations point at irrelevant docs. Support says “it used to find the right policy.”

#### OBSERVE

When? One collection or all? One language? After a reindex, embedding upgrade, parser change, or permission change? Empty rate vs wrong-hit rate?

#### Questions

- Did we rebuild the index?
- Did we change chunker, overlap, metadata, or embedding model?
- Are filters dropping the right docs (ACL too tight) or including junk (ACL too loose)?
- Is the eval set recall actually down, or are users asking a new intent?

#### Metrics / logs

Recall@10 / MRR on golden set; empty retrieval rate; average hits after filter; score distribution; % queries with no lexical overlap hitting dense-only; index doc count vs yesterday.

#### ISOLATE

Retrieval vs generation: if the right chunk is not in top-k, it is not a prompt problem. If it *is* in top-k and the model ignores it, that is generation / ordering / context packing.

#### HYPOTHESIZE

1. Embedding model or dimension changed and old vectors were not fully re-embedded (mixed index)
2. Chunker regression (tables split, titles stripped)
3. ACL / metadata filter wrong after a group-sync bug
4. Hybrid weights flipped; BM25 disabled; analyzer change
5. Corpus pollution (duplicate old policies ranked first)
6. Query rewrite now over-paraphrases IDs and part numbers

#### VERIFY

Run 30 golden queries through retrieve-only. Compare doc ids to last week’s stored traces. Inspect one failed query: scores, filters, chunk text. Check embedding model id on a vector and on the query.

#### FIX

Mitigate: point the alias at the previous collection. Durable: rebuild cleanly with one embedding version; restore hybrid; fix chunker; add canonical “in-force” metadata.

#### PREVENT

Index build writes `embed_model`, `chunker_version`, `doc_count` into the alias metadata. Eval recall is a release gate on indexer, not only on the app. Alert if recall proxy or empty-rate moves.

---

### Incident 3 — Agent repeatedly calls the same tool

**User-visible:** A 4-step task takes 30 tool calls. Cost spikes. Sometimes hits the step cap with no answer.

#### OBSERVE

Get one trace. Is it the *same tool + same args*, or same tool + slightly different args? Does the observation look empty, huge, or identical? Did a tool schema change?

#### Questions

- What does the model see after the first call?
- Is the tool erroring in a way that looks like “try again”?
- Is there a loop detector? A step budget? Idempotency?

#### Metrics / logs

Steps per successful task; duplicate (tool, args) rate; observation tokens; task completion; cost per task.

#### ISOLATE

Model policy vs tool contract vs missing memory of prior observation. If the observation is 20k tokens of logs, the model “forgets” it already searched.

#### HYPOTHESIZE

1. Observation too large or too similar across calls; no “already tried”
2. Tool returns a soft failure (“no results”) that invites another query
3. Prompt tells it to be thorough / never give up
4. No loop detector in the graph
5. State not checkpointed; each turn is amnesiac
6. Schema allows free-form queries so args never exactly match

#### VERIFY

Replay the trajectory. Hash tool+args. Measure observation size. Diff prompts. Confirm whether state is actually passed.

#### FIX

Mitigate: hard cap steps; cache tool+args → result; kill the run with a user-visible “I tried X and failed.” Durable: shrink observations (summary + URL); add a `attempts` list into state; change prompt to “do not retry the same query”; structured error codes instead of empty strings.

#### PREVENT

Eval on **redundant tool-call rate**. Unit test the graph with a stub tool that returns empty. Alert if median steps jump. This is a first-class agent reliability metric, not a curiosity.

---

### Incident 4 — API 429 (rate limited)

**User-visible:** Failures or huge latency. Logs full of HTTP 429 from the model or embedding API.

#### OBSERVE

Which API? Burst or sustained? All pods or one noisy job (reindex, eval, batch)? Did we ship a retry without jitter? Did a client start a new loop?

#### Questions

- What is the quota (RPM, TPM, concurrent)?
- Are retries stampedes (all pods retry at 1s, 2s, 4s together)?
- Is embedding backfill sharing the interactive key?

#### Metrics / logs

429 rate, TPM used vs quota, concurrency, retry count per request, which caller (interactive vs indexer vs eval).

#### ISOLATE

Interactive path vs background. One tenant vs all. Your gateway vs vendor.

#### HYPOTHESIZE

1. Traffic growth or a retry storm
2. Indexer / eval job sharing the same key and starving chat
3. Agent fan-out (multi-agent or high k rewrites)
4. Quota lowered or model deployment moved to a smaller PTU / provisioned unit
5. Missing cache → every FAQ hits the model

#### VERIFY

Break 429s by `caller_id`. Graph TPM. Check retry policy. Confirm provisioned throughput.

#### FIX

Mitigate: shed batch; exponential backoff **with jitter**; queue; serve cache; smaller model for rewrite. Durable: separate keys/quotas for interactive vs index vs eval; concurrency limiter; collapse agent fan-out; buy or reserve throughput if the business actually needs it.

#### PREVENT

Budget alarms at 70% TPM. Load test retries. Never share the interactive key with a backfill. Circuit-break agents when 429 rate exceeds N.

---

### Incident 5 — Embedding costs increased

**User-visible:** Bill for embeddings 3–10× week over week. Chat quality unchanged.

#### OBSERVE

Is it re-embedding the corpus, query-time embedding, or a new app? Did doc count grow or did we re-embed the same docs?

#### Questions

- Query embed vs document embed split?
- Cache for query embeddings?
- Did chunker shrink chunk size (more chunks × same corpus)?
- Nightly job re-embedding everything instead of deltas?
- New multilingual model with higher price?

#### Metrics / logs

Embed calls, tokens embedded, $/1M tokens, chunks written/day, cache hit rate, job duration.

#### ISOLATE

Serving path vs indexer vs accidental loop (embed on every search of the same query).

#### HYPOTHESIZE

1. Full-corpus re-embed on a schedule or on every config change
2. Chunk size halved → 2× vectors
3. Query embedding cache broken (cache key includes a timestamp)
4. A debug or eval job hitting production embed endpoint
5. Users or an agent embedding whole files per turn

#### VERIFY

Top callers of the embed API. Diff indexer: `docs processed` vs `docs changed`. Inspect cache keys. Price of the new model.

#### FIX

Stop the full re-embed. Delta-only indexer. Restore cache. Revert chunk size if it was accidental. Move eval embeddings to a batch SKU.

#### PREVENT

Cost per million embedded tokens on a dashboard with a hard budget. Indexer logs `full vs delta`. PR check: chunk size change estimates vector count. Version embeddings so you do not silently re-embed on every boot.

---

### Incident 6 — Vector search slow

**User-visible:** p95 retrieve 80ms → 800ms+. Generate unchanged.

#### OBSERVE

QPS? Index size? After a rebuild? Filter-heavy queries? One collection?

#### Questions

- nprobe / ef / overfetch settings changed?
- Unfiltered vs ACL-filtered latency?
- Memory pressure / cold index / compaction?
- Huge `$in` of 2,000 group ids in the filter?

#### Metrics / logs

Search p95, QPS, recall proxy, CPU vs memory of the search pods, filtered vs unfiltered, graph/HNSW params, disk I/O.

#### ISOLATE

ANN algorithm vs filter vs network vs client serializing huge payloads. Confirm the slow span is the search client, not embedding.

#### HYPOTHESIZE

1. Index grew; params still tuned for a 1M-vector demo
2. Metadata filters disable or constrain the ANN path (post-filter then over-retrieve)
3. Compaction / reindex on the hot collection
4. Under-provisioned replicas; GC; page faults
5. Query vector dim mismatch causing retries or brute force
6. Payload fetch of huge chunk text instead of ids then hydrate

#### VERIFY

Explain a query if the engine supports it. Compare filtered vs not. Check dim, replica CPU, and whether you fetch `_source` for 100 hits.

#### FIX

Mitigate: more replicas; reduce k; fetch ids first. Durable: retune ef/nprobe against a recall SLO; pre-filter by tenant into sharded collections if filters destroy ANN; compact off-peak; appropriate SKU.

#### PREVENT

Search latency SLO **with** a recall floor (so nobody “fixes” latency by searching worse). Load test the ACL-filtered path, not only unfiltered microbenchmarks.

---

### Incident 7 — Kubernetes pods restarting

**User-visible:** Intermittent 5xx, connections dropped, `CrashLoopBackOff` or frequent restarts on the inference or API deployment.

#### OBSERVE

`kubectl describe` / events: OOMKilled, liveness fail, node drain, image pull, config error? One deployment or node pool? After a chart change?

#### Questions

- Restart reason (`lastState.terminated.reason`)?
- Memory limit vs actual RSS (Python + torch + tokenizer)?
- Liveness probe hitting a slow `/health` that loads the model?
- GPU pods vs CPU API pods?

#### Metrics / logs

Restart count, OOM events, probe failures, memory working set, GPU HBM, throttling, deploy time.

#### ISOLATE

App bug vs probe vs resource limit vs node problem vs bad config. Do not “kubectl rollout restart” as the investigation.

#### HYPOTHESIZE

1. OOM from unbounded batch, unbounded agent context, or a memory leak in a client
2. Liveness timeout during JIT / model load / GC
3. Readiness vs liveness mixed up; killing healthy busy pods
4. ConfigMap/secret missing after deploy
5. Node disk or GPU error

#### VERIFY

Events, `OOMKilled`, probe logs, memory graphs vs limit, compare image digest to last good.

#### FIX

Mitigate: roll back chart; raise memory **once** if OOM is proven, not as a ritual; disable a bad probe path. Durable: fix leak; cap batch; startup probe for model load; liveness on a cheap endpoint; memory limit based on measured RSS + headroom.

#### PREVENT

HPA and memory alerts before restart. Load test with production-like context sizes. Startup probes for LLM containers. Never use a liveness probe that calls the model.

---

### Incident 8 — Model quality degraded

**User-visible:** “Answers got dumber / ruder / less grounded” after nothing *you* think you shipped.

#### OBSERVE

Is it grounding, tone, tool calling, or language? All prompts or one? Vendor model version? Temperature? Did a silent prompt PR merge?

#### Questions

- Pin of `model` / `deployment` / `revision`?
- Did the vendor swap the default?
- Did we change decoding (temp, top_p, max_tokens)?
- Did retrieval quality drop (fluent wrong answers)?
- Are we looking at a weekend traffic mix shift (harder questions)?

#### Metrics / logs

Faithfulness, citation support, task completion, refusal rate, toxicity, tool-schema validity, eval subset vs last week. Model id in traces.

#### ISOLATE

Retrieval vs generation vs sampling vs mix shift. Run the **same** golden questions.

#### HYPOTHESIZE

1. Vendor model revision changed under a floating tag (`latest`, unpinned)
2. Prompt or system message regression
3. Retrieval regression (see Incident 2) blamed on the model
4. Decoding params
5. Fine-tune / adapter accidentally not mounted
6. User mix shifted; eval did not

#### VERIFY

Pin last known-good model id and replay. Diff prompts. Compare retrieval ids. Check temperature in config vs what the client actually sends.

#### FIX

Mitigate: pin previous revision; revert prompt. Durable: eval gate on model id change; never serve `latest` in production; canary new revisions.

#### PREVENT

Model id is config, not a default. Shadow eval on vendor announcements. Contract with the vendor about revision windows if you are at that scale.

---

### Incident 9 — Unexpected cloud cost spike

**User-visible:** Finance Slack. Yesterday 4×. No matching 4× users.

#### OBSERVE

Which SKU? Tokens, GPU, search units, egress, logs, NAT, Bedrock, Azure OpenAI PTU vs pay-go, storage of traces?

#### Questions

- Cost by service and by tag / caller
- Any job that ran longer: reindex, eval, training, log retention
- Debug logging of full prompts to a paid log product
- Agent loop (Incident 3) or 429 retries (Incident 4)
- Data egress from a vector DB or S3 cross-region

#### Metrics / logs

$/hour by product, token spend by model, GPU hours, indexer duration, log ingest GB, request count vs spend (spend up, requests flat → unit cost or a hidden job).

#### ISOLATE

AI path vs “we logged too much” vs data transfer vs a forgotten GPU node pool.

#### HYPOTHESIZE

1. Agent or retry loop
2. Unpinned expensive model on a fallback path
3. Full re-embed or full reindex
4. Trace/prompt logging at 100% to a vendor
5. GPU nodes that did not scale to zero
6. Cross-region embedding or search

#### VERIFY

Billing export + request traces joined by hour. `kubectl` for extra node groups. Indexer job history.

#### FIX

Kill the runaway job. Pin fallback models. Sample traces. Scale down idle GPUs. Stop cross-region.

#### PREVENT

Anomaly alert on **$ per successful task**, not only total $. Quotas on TPM and GPU. Tags on every client. Daily ingest of billing into the same dashboard as QPS.

---

### Incident 10 — Agent took an unauthorized action

**User-visible:** The copilot refunded a customer, restarted a service, emailed a client, or deleted a ticket without approval. This is a **security incident**, not a prompt tweak.

#### OBSERVE

What action, which identity, which tool, was HITL supposed to exist, was it bypassed or never wired? Blast radius: one run or a class of runs?

#### Questions

- What did the allowlist say?
- Did the tool run with a service account that was too privileged?
- Did HITL timeout-as-approve (see Chapter 23 example B)?
- Was the instruction in a retrieved doc (indirect prompt injection)?
- Can we revoke the side effect?

#### Metrics / logs

Audit: tool name, args, acting as whom, approval id. Unsafe-action counter (hopefully exists). Trace of the graph node that skipped wait.

#### ISOLATE

Excessive agency (tool too powerful) vs missing HITL vs HITL bug vs injection vs confused deputy (agent uses user token vs god token).

#### HYPOTHESIZE

1. Write tool exposed to the model without a human node
2. Timeout treated as approve
3. Indirect injection in a ticket or runbook
4. Tool implemented “dry run” that actually committed
5. Role check in the app, not in the tool server — attacker or model bypassed the app

#### VERIFY

Audit log for approval id. Replay. Read the tool server code. Inspect retrieved content for injection. Confirm which credentials were used.

#### FIX

Mitigate: disable write tools **now**; rotate credentials; reverse the action if possible; notify security. Durable: allowlist on the MCP / tool server; deny-on-timeout; dual control for irreversible actions; treat tool args as untrusted; strip or wrap untrusted retrieved text.

#### PREVENT

Unsafe-action evals as a **release blocker at 0**. Table-top: “what if the model wants refund.” Least privilege per tool. Security review of any new write tool. See OWASP LLM 2026 Excessive Agency.

Do not say “we’ll add a better system prompt.” Prompt is a helper. Authorization is the control.

---

### Incident 11 — RAG returned another customer’s data

**User-visible:** Tenant A saw Tenant B’s contract. Stop everything else. This is a **P1 privacy incident**.

#### OBSERVE

One pair of tenants or a class? One collection? After a filter change? Confirm with the request id and retrieved chunk ids — do not debate whether the user “misread.”

#### Questions

- Was ACL applied in the search query or in Python after fetch?
- Shared collection with a `tenant_id` metadata filter that was omitted?
- Query rewrite dropped the filter?
- Cache key without tenant id?
- Agent tool that searches without passing tenant?

#### Metrics / logs

Retrieved `tenant_id` vs authenticated tenant; filter empty rate; cache hits; any query with missing filter field.

#### ISOLATE

Index-time mis-tag vs query-time missing filter vs cache vs UI bug that shows the wrong conversation.

#### HYPOTHESIZE

1. Post-filtering: fetched top-k globally, filtered in app, a bug skipped the filter under load
2. Cache of answers keyed by query text only
3. Metadata missing on a subset of chunks after a bad ingest
4. Superuser API key used by the app, relying on the model to “only see A” (the model will not)
5. Shared vector namespace in a multi-tenant Pinecone/pgvector table without RLS

#### VERIFY

For the failing request: raw search request body. Was `tenant_id = A` in the filter? Inspect chunk metadata. Reproduce with A’s token. Check cache keys.

#### FIX

Mitigate: take the assistant down or disable retrieve; purge cache; notify security/legal per policy. Durable: **filter in the query engine**; row-level security; fail closed if filter is absent (search library must reject unfiltered queries in prod); per-tenant collections if the engine cannot enforce; cache key includes tenant + authz version.

#### PREVENT

Automated test: tenant B doc must never appear for tenant A token — in CI and in prod canary. Alert on any retrieved chunk whose tenant ≠ caller. Pen-test this like you would an IDOR. Do not rely on the LLM to keep secrets that were in its context.

If you built the system that leaked, say what you missed and what the fail-closed design is. Do not minimize.

---

### Incident 12 — MCP server compromised

**User-visible:** Odd tool behavior, unexpected outbound traffic, secrets in a tool response, or security flags a poisoned tool definition. Treat as **compromise**, not “hallucination.”

#### OBSERVE

Which server (internal vs third-party)? What tools can it run? What credentials does it hold? When did the server image or tool metadata last change?

#### Questions

- Who is allowed to publish this MCP server?
- Do we pin hashes / signatures of tool descriptors?
- Did the tool schema change (classic tool poisoning: description says “send history to URL”)?
- Could the host be talking to a **shadow server** (same name, different endpoint)?
- What tokens were in env?

#### Metrics / logs

Gateway audit: tool schema versions, destinations, auth failures, unusual tool names, outbound IPs, token use.

#### ISOLATE

Poisoned descriptor vs compromised runtime vs DNS/name collision vs malicious third-party server vs leaked token reused.

#### HYPOTHESIZE

1. Tool metadata injection (instructions hidden in descriptions)
2. Shadow MCP server registered with a lookalike name
3. Supply chain: base image or npm/pip dep
4. Stolen gateway token; attacker invoking tools as the agent
5. Server path traversal / SSRF in a “fetch URL” tool

#### VERIFY

Diff tool JSON against last known-good. Verify signature/pin. Check registry. Rotate and see if odd calls persist. Inspect egress.

#### FIX

Mitigate: disconnect that server at the **gateway**; rotate all credentials it could see; revoke sessions; take write tools down. Durable: allowlist servers by hash; signed descriptors; no ambient cloud admin creds on MCP processes; sandbox network; human review of tool description changes; treat MCP as part of your threat model (OWASP MCP Top 10).

#### PREVENT

MCP gateway is mandatory in enterprise: authn, authz, schema pin, rate limit, audit. Do not let the model choose arbitrary MCP endpoints. New servers go through the same review as a new microservice with credentials.

Interview stance: “I isolate at the gateway first, rotate, then forensics. I do not patch this with a prompt.”

---

### Incident 13 — Empty retrieval (nothing in top-k)

**User-visible:** “I don’t know” on questions you know are in the corpus. Or the model fabricates because the prompt still demands an answer.

#### OBSERVE

Empty rate by collection, language, query type (IDs vs natural language). Started at reindex, filter change, or analyzer change?

#### Questions

- Are we filtering so hard that zero docs survive?
- Is the query embedding in a different space (wrong model)?
- Is the collection alias pointing at an empty new index?
- Minimum score threshold too high?
- Query rewrite produced a blank or a 1-word query?

#### Metrics / logs

Empty retrieval %, hits-before-filter vs after, index doc count, threshold, rewrite output.

#### ISOLATE

Zero vectors in index vs vectors exist but filter/threshold/embedding mismatch vs rewrite.

#### HYPOTHESIZE

1. Alias swap to empty or half-built index
2. ACL filter uses wrong field name after a schema rename
3. Score threshold tuned on a different model
4. Embed model mismatch
5. Query rewrite bug

#### VERIFY

Count docs in the live alias. Run the same query with filters off in a **secure debug** path (never in prod logs for other tenants). Embed a known title and search it.

#### FIX

Mitigate: rollback alias; lower threshold temporarily only if ACL is still on; disable bad rewrite. Durable: indexer must not alias until doc count and smoke queries pass; fail the app closed if retrieval empty-rate > N for 5 minutes.

#### PREVENT

Smoke queries after every index build (known titles must return). Alert on empty-rate. Do not instruct the model to “always answer” when k=0.

---

### Incident 14 — Citation mismatch

**User-visible:** Answer looks right, citation link is the wrong doc, or the quoted span is not in the source. Trust dies immediately.

#### OBSERVE

Is the citation id swapped, the URL stale, or the quote fabricated? One source type (PDFs)? After chunker change?

#### Questions

- Does the model generate citations freely, or must it pick from a provided list of `[n]`?
- Are chunk ids stable across reindexes?
- Do we verify the cited span is a substring of the chunk?
- UI joining `doc_id` to URL with an off-by-one?

#### Metrics / logs

Citation precision (cited id in retrieved set); span support rate; human “wrong source” tickets.

#### ISOLATE

Generation (model invented a cite) vs retrieval (right idea, wrong near-duplicate doc) vs UI mapping vs unstable ids after reindex.

#### HYPOTHESIZE

1. Prompt allows free-form URLs
2. Near-duplicate policies; model cites the expired one
3. Chunk ids recycled
4. Faithfulness checker not covering citations
5. PDF page numbers off by cover pages

#### VERIFY

For failing answers: is `cited_id ∈ retrieved_ids`? Is the quote in the chunk text? Diff chunker.

#### FIX

Force cite-from-list (`[1]`…`[k]` only). Post-check: drop or regenerate if span not in chunk. Canonicalize duplicates with `as_of_date`. Stable document GUIDs.

#### PREVENT

Citation support is a ship bar. UI never hyperlinks a model-invented URL. Golden set includes “must cite doc X, not the 2022 duplicate.”

---

### Incident 15 — GPU OOM

**User-visible:** Inference pods die, 500s, `CUDA out of memory`. Sometimes only on long contexts or large batches.

#### OBSERVE

Max context, batch size, concurrent requests per GPU, model size vs HBM, whether it started after a max_tokens or context-window config change.

#### Questions

- What’s the GPU SKU and HBM?
- KV cache size at max concurrency × max context?
- Are multiple models on one GPU?
- Fragmentation from varying sequence lengths?
- Tokenizer / vision blobs on GPU by accident?

#### Metrics / logs

HBM used, batch, concurrent, sequence length histogram, OOM stack traces, preemptions.

#### ISOLATE

Model weights vs KV cache vs activation vs a memory leak vs a second process on the GPU.

#### HYPOTHESIZE

1. Concurrency too high for context length (KV cache)
2. `max_model_len` raised without lowering max batch
3. A request with huge image or pasted log
4. Two workers pinned to one GPU
5. Memory leak in custom CUDA / pytorch cache not released

#### VERIFY

Reproduce with a long prompt. Check `nvidia-smi` during traffic. Confirm worker × GPU mapping. Compute KV cache math roughly: concurrent × layers × dim × seq × dtype.

#### FIX

Mitigate: reduce max concurrency; reject over-long requests; roll back context window. Durable: set `max_num_seqs` / memory utilization in vLLM or equivalent from measured HBM; chunk long inputs; separate small/long traffic; one worker per GPU unless you know otherwise.

#### PREVENT

Admission control on tokens in. Load test at p99 context, not average. Alert at 80% HBM. Startup fails if configured max_len cannot fit.

You do not need to recite exact KV formulas. You do need to say KV cache grows with concurrent × sequence length and that OOM is often cache, not weights.

---

### Incident 16 — Webhook duplicate side effects

**User-visible:** Double refunds, double tickets, double emails, double Slack pages. The agent or workflow “worked twice.”

#### OBSERVE

Provider retries, our retries, user double-click, two graph workers resuming the same checkpoint, webhook at-least-once delivery.

#### Questions

- Is the webhook handler idempotent?
- Do we have an idempotency key (event id, incident id, refund id)?
- At-least-once from Stripe / GitHub / Slack / ServiceNow?
- Did we timeout and retry after the side effect already committed?
- Two replicas processing one Kafka message without a lock?

#### Metrics / logs

Duplicate event ids, handler duration vs provider timeout, unique constraint violations, two `execute` spans with the same business key.

#### ISOLATE

Provider replay vs our retry vs graph replay vs user vs missing unique index.

#### HYPOTHESIZE

1. Handler did the side effect then timed out; provider retried
2. Agent step retried after the tool actually succeeded (lost 200 OK)
3. Checkpoint resumed on two workers
4. No unique constraint on `external_event_id`
5. HITL “approve” delivered twice

#### VERIFY

Find two writes with the same event id. Check HTTP traces. Check for `ON CONFLICT` / idempotency table.

#### FIX

Mitigate: stop the worker; reverse extras if possible; feature-flag the write tool. Durable: **idempotency key** stored before the call; unique constraint; tool returns the same result on replay; graph nodes are at-least-once and you design for it; deny duplicate approvals.

#### PREVENT

Every write tool documents idempotency. Eval/replay of incidents must not create real tickets — use a dry-run environment. Contract tests: deliver the same webhook twice, expect one side effect.

This is a distributed-systems incident that happens to involve an agent. Talk about it that way.

---

## 4. Four more patterns you should be ready to map onto the same method

Interviewers invent variants. Map them; do not memorize 16 scripts.

| They say | Treat it as |
| --- | --- |
| “First token is fast, last token is late” | Incident 1, tokens-out / slow decode |
| “Only German queries fail” | Incident 2 / 13, analyzer + embedding language |
| “Bill is embeddings, quality is fine” | Incident 5 |
| “It refunded after I closed Slack” | Incidents 10 + 16, HITL timeout |
| “Answers cite a URL 404” | Incident 14 + stale index |
| “Pods healthy but GPU idle, latency high” | Queueing in the app, not GPU OOM |
| “Only one tenant is slow” | Noisy tenant, huge ACL filter, or their corpus size (Incident 6) |

---

## 5. Cheat sheet you can say in any incident

```
OBSERVE   when, who, what changed, user-visible symptom
ISOLATE   which span / which tenant / which caller
HYPOTHESIZE  2–4 causes that fit the clock
VERIFY    a trace, replay, or metric that would kill each cause
FIX       mitigate first, then the real change
PREVENT   gate + alert + test for this class
```

If you only remember one production sentence for AI systems:

> Quality, latency, cost, and safety incidents are isolated with **traces that split retrieve / generate / tools**, not with opinions about models.

Drill: pick three incidents, time-box 2 minutes each, out loud. Then go to Chapter 23 and attach one of these as the “failure” layer of your project. A project with a real incident story beats a project that “went smoothly.”
