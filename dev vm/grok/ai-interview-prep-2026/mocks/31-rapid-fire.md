# 31 — Rapid-Fire (100 × 30–60s)

**What this chapter is for:** switching frameworks at interview speed. Definitions, traps, and “when not to.” Not essays.

Cover the **expected-hit key**. It starts only after question 100. If you peek, you are drilling recognition, not recall — useful the day before, illegal as a first pass.

Speak out loud. A typed answer is a different sport.

---

## How to run

| Mode | Time | Count | Pass bar |
| --- | --- | --- | --- |
| Daily (Ch 00) | 10 min | 8 questions, mixed sets | 6/8 hit the key words |
| Set drill | ~8 min | One set of 10 | 7/10 |
| Full mock | 50–70 min | All 100, 30–60s each | 70/100 first pass without peeking |
| Weak-dimension | 10 min | Only the set that maps to your Ch 35 hole | 8/10 |

**Timer:** 45 seconds default. Cut to 30s if you ramble. Allow 60s for questions that say “decision tree” or “debug order.”

**Partner:** they read the number and the question, say “stop” at the bell, mark Y/N against the key *after you finish the whole sitting*. Do not negotiate mid-set.

**Solo:** card over the page, one question visible. Record. Do not rewind mid-set.

**Scoring a single question:** 1 if you hit **most** of the key’s keywords (same idea, not the same nouns). 0 if you missed the trap, said the disqualifying thing, or never reached a trade-off when the question demanded one. No half points. Harsh on purpose.

**After the sitting:** total /100. Map misses to Chapter 35 dimensions. Two misses in the same set = that guide is tomorrow’s 20-minute card, not “I’ll reread later.”

---

## Rules while the clock is running

1. Lead with the point (Ch 05). You do not have time to build up.
2. Name a trade-off or a “when not” if the question is practical.
3. If you do not know: Boundary in 15 seconds, then stop. That can still score 1 if the reasoning is real.
4. Do not name LangChain / CrewAI / a vendor unless the question asks for a pick.
5. Traps are in the mix on purpose: multi-agent by default, fine-tune the wiki, dump PDFs into context, prompt-as-ACL, auto-kubectl. If you take the trap, 0.

Sets mix the eight primary roles and Chapters 06–22. Role tags in parentheses tell you whose mouth this question often comes from — answer as if that interviewer asked it, even if you are prepping a different title.

---

# LIVE — questions only

Work set by set. Do not scroll to the key.

---

## Set 1 — Python, APIs, SQL (Ch 06–08)  
*45s each. Narrate as if coding is about to start.*

**1.** The model returns truncated JSON. What does your parser do? What does it *not* do?

**2.** You retry a `POST` that creates a ServiceNow ticket on timeout. What bug are you about to ship? (Intelligent Automation / Agentic)

**3.** FastAPI chat: the product wants tokens on the wire as they generate. What do you actually return, and what do you still timeout?

**4.** SQL: `users`, `tickets`, `bot_turns`. Users who talked to the bot in 7 days but have no ticket. What’s the join trap?

**5.** Vendor API paginates with a cursor that can skip or duplicate under concurrent writes. How do you consume it?

**6.** Tool arguments: Pydantic schema vs `dict` and hope. Why, in 30 seconds?

**7.** You log the full prompt and tool payloads. Name two production problems. (Cloud / Security)

**8.** LLM HTTP call: connect timeout vs read timeout vs total deadline. Which one bites, and what does the user see if you get it wrong?

**9.** Who mints the idempotency key for an agent tool that refunds $20 — the model, the gateway, or the payment API caller in your service? (Agentic)

**10.** Chunk metadata filter: field missing vs `null` vs `""`. What happens to retrieval if you aren’t explicit?

---

## Set 2 — LLMs and serving (Ch 09)  
*45s. 60s on 14 and 19.*

**11.** Prefill vs decode. For a 4k-token RAG answer with a 2k prompt, which dominates *latency*, which dominates *memory as you stream*?

**12.** “Temperature 0 is deterministic.” True or false in production APIs, and why evals care.

**13.** Lost-in-the-middle: you stuffed 40 chunks into a 128k window. What do you change besides “bigger window”?

**14.** Why does KV cache memory explode with long context? You may say the shape of the formula without fake numbers.

**15.** Temperature vs top-p, one sentence each. When do you touch them in prod vs in a demo?

**16.** Prompt prefix caching: what must stay byte-stable, and what silently kills the hit rate?

**17.** Structured output fails 8% of the time. Constrained decoding vs retry-with-repair vs turning it into a tool. Pick with a trade-off.

**18.** “Fine-tune the wiki so the model just knows policy.” 45 seconds. (Trap. Architect / GenAI / HM)

**19.** Route 80% of queries to a small model. How do you not tank quality? What do you measure?

**20.** Tokens are not words. Give one user-visible failure this causes in RAG or cost dashboards.

---

## Set 3 — RAG (Ch 10)  
*45–60s. This set is the 2026 default screen.*

**21.** Define RAG in 20 seconds without a framework name. Then 20 seconds on why it exists.

**22.** “We have 200k context. Dump the PDFs in. Retrieval is extra complexity.” Your answer. (Trap)

**23.** Chunking a 10-K with tables. One strategy, one failure mode. (GenAI)

**24.** Hybrid search: what does BM25 catch that dense embeddings miss? When would you skip hybrid?

**25.** Retrieval is correct, answer is wrong. First three checks, in order. (Troubleshooting)

**26.** Faithfulness vs answer relevancy vs context precision. One line each.

**27.** The UI citation points at the wrong paragraph. Two ways that happens.

**28.** Multi-tenant: one index, `filter tenant_id`. What’s the residual risk? What is the real ACL? (Security / Cloud)

**29.** When is RAG the wrong tool? Give two cases.

**30.** Index is 6 hours stale. Who feels it, and how do you version ingest vs query?

---

## Set 4 — Agents and control flow (Ch 11)  
*45s. 60s on 32 and 40.*

**31.** Agent vs workflow. The axis that actually matters. One example each.

**32.** “We’ll start with five specialist agents; it’s cleaner.” Default reply. (Trap)

**33.** Hard step cap. Why the model cannot be the component that enforces it.

**34.** Can the bot refund $20? State a policy in four bullets. (Agentic / Automation / Security)

**35.** Tool 500s at step 3 of 7. What must already be in the state store when you retry?

**36.** Evaluate an agent. Name three metrics that are not BLEU, ROUGE, or thumbs-up.

**37.** Two Jira tickets got created for one user ask. Root-cause *class*, not a framework bug.

**38.** Termination conditions. List four that are not “the model says done.”

**39.** Memory: working vs episodic vs semantic. Which belongs in the live prompt, which must not?

**40.** When should you **not** use an agent? Three bullets. (Highest-signal question in this set)

---

## Set 5 — MCP, tools, multi-agent (Ch 12–13)  
*45s.*

**41.** MCP vs function calling vs “just REST.” One sentence each. (FDE / Agentic)

**42.** MCP host, client, server. Who is the security boundary you actually implement?

**43.** Tool poisoning. What did the attacker change, and who sees it?

**44.** The model wants to download a new MCP server mid-task because a blog said to. Yes/no, and the control.

**45.** A2A in one sentence. When do you actually need it vs a function call?

**46.** Supervisor + specialists: name the bottleneck symptom and one fix that is not “smarter supervisor.”

**47.** Shared scratchpad vs message passing. One risk each.

**48.** Engineer installed a shadow MCP server on a bank laptop “just to try.” What do you do this hour? (Security / FDE)

**49.** Tool allowlist: enforced in the prompt, or in the gateway? What happens if only the prompt?

**50.** Multi-agent for linear invoice GL-coding. Why is this a trap? (Intelligent Automation)

---

## Set 6 — Vector databases (Ch 14)  
*45s. 60s on 52 and 60.*

**51.** HNSW vs IVF. One trade-off sentence. Do not recap a paper.

**52.** You add `tenant_id = X` as a filter. Recall drops. Why, in filtered ANN terms?

**53.** Cosine vs dot vs L2. When are cosine and dot the same thing?

**54.** Where does a reranker sit, what it costs, when you skip it. (GenAI / Cloud cost)

**55.** Metadata filter vs stuffing “user is in Finance” into the chunk text. Which is authz?

**56.** pgvector vs a dedicated vector DB. The actual decision axis for a 2026 loop.

**57.** Delete a document the model must not be able to cite tomorrow. What else must die?

**58.** You swap the embedding model. Do you re-embed everything? What if you don’t?

**59.** Retrieve k=20, rerank to 5. Why not k=5 from the ANN in the first place?

**60.** Quality dropped after adding 1M documents. Rank three hypotheses. (Troubleshooting)

---

## Set 7 — Cloud + Docker/K8s (Ch 15–16)  
*45s. Cloud AI / Deployment interviewer voice.*

**61.** Bedrock vs Foundry vs Vertex. First question you ask before you pick. Not a benchmark.

**62.** Private RAG, no public internet to the model. Name four things that actually change.

**63.** GPU pod is Pending. First three looks. (Deployment / Cloud)

**64.** CrashLoopBackOff after a config change. Investigation order. Do not delete the pod first as a personality.

**65.** Access keys in the container image. How you talk about it, and the replacement.

**66.** On-demand vs provisioned throughput (PTU). When paying for idle is rational.

**67.** Readiness probe invokes the LLM every 5s. Why that is wrong.

**68.** 429 storm from the model API. Client behavior and platform behavior. (APIs + Cloud)

**69.** Dockerfile: non-root, pinned digest, multi-stage. Why each, one clause.

**70.** Canary a **prompt** vs canary a binary. What is different? (LLMOps + Cloud)

---

## Set 8 — LLMOps and evals (Ch 17)  
*45–60s. If you fail this set, you fail senior GenAI.*

**71.** Ship bar. Three numbers you would put on a launch doc for a support RAG.

**72.** Golden set of 80 questions, all from the founder’s favorite docs. What’s wrong?

**73.** Vendor silently updates the hosted model. What breaks, and what’s the harness?

**74.** Trace a bad answer. Name the spans you must have. (GenAI / AIOps)

**75.** Cost per successful task vs cost per 1M tokens. Why the first is the management metric.

**76.** Prompt versioning. What is the unit of rollback (prompt only, or what bundle)?

**77.** Offline eval vs online eval. One use each. What you must not do with thumbs alone.

**78.** Users complain; eval scores are flat. Three hypotheses. (Troubleshooting)

**79.** Evals are low, so we fine-tune. Why is this usually the wrong next step? (Trap-adjacent)

**80.** Traces vs PII. State a policy in four bullets. (Security + Cloud)

---

## Set 9 — AIOps + production incidents (Ch 18, 22)  
*45–60s. Debug order or you score 0.*

**81.** 10,000 alerts after a region blip. First 10 minutes. Not “feed them to GPT.” (AIOps)

**82.** Auto-`kubectl apply` from an LLM-guessed cause. Tell the failure story in 40 seconds.

**83.** Topology/CMDB vs embedding-similarity for correlation. When each lies.

**84.** p99 5×, error rate flat. Isolate TTFT vs retrieve vs tools vs infra. (GenAI on-call)

**85.** Why deploys and feature flags are first-class signals, not “context for the LLM.”

**86.** Incident ticket paste as LLM input. Injection angle and control. (Security + AIOps)

**87.** When rules beat LLMs in ops. Two cases.

**88.** RCA copilot hallucinated a causal link. What control should have fired?

**89.** Cost 10× overnight. Four bills you look at before you blame the model. (Cloud)

**90.** Looping agent. The trace pattern you look for, and the kill that does not wait for the model. (Agentic)

---

## Set 10 — Security, design, customer judgment (Ch 19–21 + role mix)  
*45–60s. Last set on purpose: you are tired, they still score this.*

**91.** Direct vs indirect prompt injection. One example each, for a support RAG.

**92.** “The system prompt says ignore jailbreaks, so we’re safe.” Your reply. (Trap)

**93.** Model returns markdown with a `javascript:` link. What is the output-handling risk?

**94.** Unbounded consumption as an attack. Two controls that are not “hope they don’t.”

**95.** Design opener for “enterprise knowledge assistant.” First 30 seconds — no vendors. (Ch 20)

**96.** Customer: “we need AI on our notes.” First three questions. (FDE / Solutions Engineer)

**97.** InfoSec: “data cannot leave the VPC.” Options you actually offer, including *no deal*. (SE / Cloud)

**98.** Who owns evals at 02:00 when they fail? Why that answer is architecture. (Solutions Architect)

**99.** Hospital agent wants to send a message to a patient. HITL or not, and blast radius. (FDE / Security)

**100.** You don’t remember Bedrock AgentCore primitive names. Give the Boundary answer (Ch 05 §12).

---

**STOP.** Timer off. Write your /100 and the set numbers you failed. Do not “just glance” at a few keys. Score all 100 or you will only look up the ones you already know you missed.

---

# Only after you finish — expected-hit key

Keywords only. If you said the idea, mark 1. If you took the trap, 0 even if the rest was pretty.

**1.** validate/schema; repair or retry once; no silent `except`; don’t parse half-objects as truth  
**2.** idempotency key; timeout ≠ failure; duplicate ticket; retries on POST need a token  
**3.** SSE/stream; flush tokens; read timeout ≠ connect; cancel on client disconnect  
**4.** LEFT JOIN / NOT EXISTS; `COUNT` fan-out; filter dates on turns not inner-join drop  
**5.** cursor+idempotent upsert; detect dup ids; don’t skip on holes; bound pages  
**6.** schema/types/bounds; reject extra fields; model-safe errors; not “LLM will send JSON”  
**7.** PII/secrets in logs; cost of ingest; prompt=data; retention/legal  
**8.** read/idle timeout during stream; user sees hang or duplicate retry; total deadline  
**9.** **your service/gateway**, not the model; model must not mint money keys  
**10.** missing ≠ null ≠ empty; filter match count; silent zero-hits  

**11.** prefill=prompt/TTFT; decode=output tokens; KV grows with seq during decode  
**12.** false/not guaranteed; seeds, batching, vendor; evals need pinned model+params  
**13.** retrieve less; rerank; put gold in beginning/end; don’t stuff 40 chunks  
**14.** KV ~ layers×hidden×seq×batch×precision; long context = memory cliff  
**15.** temp=shape; top-p=nucleus; prod pin low; don’t tune live to hide retrieval  
**16.** byte-stable prefix; changing system prompt/tool JSON kills cache  
**17.** constrain if grammar-ok; retry/repair cheap; tool/schema for APIs; quality vs coverage  
**18.** **trap=0 if you agree**; RAG for changing knowledge+citations; FT=behavior; weekly stale  
**19.** router/confidence/abstain; shadow+eval slice; cost per *success*; not random 80%  
**20.** tokenizer inflation (code/lang); cost dashboards lie; chunk counts ≠ words  

**21.** retrieve then generate; private/current/citable; not weights-as-wiki  
**22.** **trap=0 if you dump**; cost; lost-in-middle; ACL; stale; no retrieval eval  
**23.** table-as-unit / caption+raw; fail=split rows, orphan headers  
**24.** SKUs/error codes/rare tokens; skip if corpus tiny/semantic-only  
**25.** isolate generation; prompt/cite instruction; context packing; model; traces  
**26.** faithful=supported; relevancy=answers the ask; ctx precision=retrieved useful  
**27.** chunk offset wrong; rerank/reorder; model cites title not span; UI maps id≠text  
**28.** residual ANN leak; prompt is not ACL; prefilter/namespace; cache key includes tenant  
**29.** SQL lookup; tiny stable corpus; transaction/SoR write; deterministic calc  
**30.** users of new policy; watermark versions; query pin; dual-read  

**31.** who owns control flow; workflow=known graph; agent=runtime choose  
**32.** **trap=0 if you start with five**; default workflow; multi-agent last resort  
**33.** model is untrusted loop; cap in runtime/gateway; independent of tokens  
**34.** HITL or hard cap+audit; allowlist; idempotent; no loop; user principal  
**35.** checkpoint; inputs/outputs so far; idempotency keys; not “replay the prompt” only  
**36.** task success; trajectory/tool-correct; cost/steps; policy violations  
**37.** missing idempotency; double-retry POST; two agents; at-least-once without key  
**38.** max steps; budget; policy deny; user cancel; cannot progress; goal-met detector  
**39.** working=now; episodic=store; semantic=RAG; don’t dump history into every prompt  
**40.** known process; irreversible writes; no eval; no traces; linear invoice/KYC  

**41.** MCP=tool protocol; fn-calling=model API shape; REST=you still wrap  
**42.** **host/gateway**; not the model; not “the server is nice”  
**43.** descriptors/args/endpoints; model+host see poisoned spec; exfil/over-scope  
**44.** no; pin/allowlist; no dynamic untrusted tools  
**45.** agent-to-agent protocol; need only if two runtimes must collaborate; else tools  
**46.** supervisor serial bottleneck/cost; collapse to graph; parallel only real splits  
**47.** scratchpad=poison/leak; messages=drift/inconsistent state  
**48.** incident; isolate laptop; revoke; no prod data; don’t “just uninstall quietly”  
**49.** **gateway**; prompt-only=injection bypass  
**50.** **trap**; known steps; eval/audit/cost explode; LLM as node not fleet  

**51.** HNSW=RAM/low-latency; IVF=train/quantize/cheaper at scale; both approx  
**52.** pre/post filter; graph connectivity; recall vs latency; need partitioned indexes  
**53.** same if normalized; otherwise not  
**54.** after retrieve before generate; extra ms/$/GPU; skip FAQ/low-k/easy route  
**55.** **filter/index ACL is authz**; text is not; model will ignore  
**56.** ops skill, filtered-query, SLA, cost, not logo; pgvector if already Postgres+modest  
**57.** vectors, chunks, cache, replicas, object store; tombstones  
**58.** yes re-embed; mixed spaces=garbage retrieve  
**59.** ANN misses; rerank needs recall-in; k is a recall knob  
**60.** pollution/dupe; embedding drift; filter; k too small; eval mix; not “need GPT-5” first  

**61.** data gravity + identity + residency  
**62.** PrivateLink/VPC endpoint; training opt-out; private logs; lost playground features; IAM  
**63.** describe events; GPU resource/taint/driver; quota/selector; not “K8s will scale”  
**64.** events, previous logs, config/hash, probes, OOM; rollback; don’t flail restart  
**65.** incident; rotate; Secrets Manager/KMS; never image/env as end state  
**66.** steady high QPS; latency SLO; idle waste if bursty → on-demand/batch  
**67.** cost; 429; false ready; health=process+config not invoke  
**68.** backoff+jitter; idempotent; shed load; quota/PTU; don’t stampede retry  
**69.** non-root=blast; digest=repro; multi-stage=surface/size  
**70.** prompt is config; split traffic+eval gate; bundle with index/model; not replica% only  

**71.** faithfulness/citation; recall@k; p95; $/success; abstain rate — pick three  
**72.** demo-overfit; missing adversarial/tenant/tables; not production mix  
**73.** quality/latency/cost regression; pin versions; golden harness on bump  
**74.** rewrite; retrieve; rerank; generate; tools; tokens; tenant; cache hit  
**75.** includes failures/retries/HITL; tokens hide loops  
**76.** prompt+model+index+policy as bundle; not a gist paste  
**77.** offline=gate; online=drift; thumbs≠faithfulness  
**78.** distribution shift; metric blind spot; UX/latency; spam slice; label drift  
**79.** usually retrieval/prompt/eval set; FT last; **0 if FT-first**  
**80.** minimize; redact; retain policy; no training; access control on traces  

**81.** blast radius; what changed; dedup parent; freeze deploys; not 10k prompts  
**82.** wrong service; blast; injection via ticket; no dry-run; humans mute you  
**83.** topology lies if stale CMDB; embeddings lie on coincidental text; need **both + change**  
**84.** traces; TTFT=provider/prefill; retrieve=k/filter; tools=fan-out; infra=CPU/GPU  
**85.** time-align; RCA without change-intel is fanfic  
**86.** indirect injection; isolate from tools; allowlist; never “ticket is instructions”  
**87.** known pages; hard SLOs; safety interlocks; rate-limit; disk-full runbook  
**88.** evidence-link required; refuse ungrounded causality; human gate on actions  
**89.** tokens; log ingest; NAT/egress; embed backfill; idle PTU; looping key  
**90.** repeated tool+args; step count; **external kill**; cap missing  

**91.** direct=user override; indirect=wiki/ticket; both tool-abuse  
**92.** **trap=0 if you agree**; cannot prompt-away LLM01; gateway/ACL/HITL  
**93.** XSS; unsandboxed markdown; output encode; no privileged click-through  
**94.** max tokens/steps/$; rate limit; per-tenant quota; kill switch  
**95.** clarify users/data/risk; ingest vs query; identity-aware retrieve; evals; agent only if *do*  
**96.** who user; what job; where truth/ACL; success metric; **not** stack first  
**97.** VPC/PrivateLink; zero-retention; their IdP; or no-buy; don’t lie air-gap  
**98.** named owner+on-call; RACI; else evals are theater  
**99.** HITL send; SoR; audit; v0=draft only; never autonomous patient email  
**100.** boundary; related pattern (managed loop, IAM tools, traces, guardrails); validate docs; no bluff  

---

## Self-score grid

```
Date:
Peeked? yes/no
Set1  /10   (06–08 Programming/APIs)
Set2  /10   (09 LLMs)
Set3  /10   (10 RAG)
Set4  /10   (11 Agents)
Set5  /10   (12–13 MCP/multi-agent)
Set6  /10   (14 Vector)
Set7  /10   (15–16 Cloud/K8s)
Set8  /10   (17 LLMOps)
Set9  /10   (18/22 AIOps/incidents)
Set10 /10   (19–21 Security/design/customer)
TOTAL /100

Traps (18, 22, 32, 50, 79, 92):  /6   (six zeros here = not interview-capable on judgment)
```

**How to read the total**

| Score | Meaning |
| --- | --- |
| <60 | You are reading, not generating. Daily 8-question drill until a set is 8/10. |
| 60–74 | Interview-capable on definitions; still fail follow-ups. Drill missed sets out loud. |
| 75–87 | Strong rapid-fire. Pressure-mode (Ch 30) the sets you missed. |
| 88+ | Do not get cocky. Chapter 29 still exists. Speed ≠ design. |

Missed traps are worth more than missed HNSW trivia. If you scored 90 but took 18, 22, and 32, you are not ready for a senior panel.

Map misses back to Chapter 35. Then stop. Do not “do the 100 again” the same night — you will memorize the key. Wait 48 hours, shuffle the sets.

If this was the last drill before on-site: put the book down. Chapter 33 is the 24-hour sheet. Sleep.
