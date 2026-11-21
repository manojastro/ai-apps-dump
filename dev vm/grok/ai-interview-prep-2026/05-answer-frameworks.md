# 05 — Answer Frameworks

**What this chapter is for:** generating a professional answer under pressure without memorizing essays.

Pick a framework the way you pick a data structure: by the shape of the question. Say the structure out loud in one sentence (“I’ll cover what it is, why we use it, how it works, and the trade-off”), then fill it. Interviewers relax when they can see the shape.

---

## 0. Universal rules (all frameworks)

1. **Lead with the point**, then explain. Do not build up to a definition for 90 seconds.
2. **Time-box.** Default 45–90 seconds unless they say “go deep” or it is a design round.
3. **Name one trade-off** in every technical answer. This is the senior tell.
4. **Use one example.** Prefer your project. If you lack one, say “in a typical support RAG…” — never fake “we shipped.”
5. **Stop.** Invite: “I can go into evals, security, or scaling — which is most useful?”
6. **If you don’t know:** use the Boundary framework at the bottom. Do not bluff.

---

## 1. Technical definition — WHAT / WHY / HOW / EXAMPLE / TRADE-OFF

**Use when:** “What is RAG?”, “What is MCP?”, “What is a vector index?”, “What is an agent?”

| Step | You say | Time |
| --- | --- | --- |
| WHAT | One sentence in plain language | 10s |
| WHY | The problem it exists to solve | 10s |
| HOW | 3–5 moving parts | 20–30s |
| EXAMPLE | One concrete system | 10s |
| TRADE-OFF | Cost, latency, complexity, or failure mode | 10s |

### Worked: “What is RAG?”

**30-second**

> RAG retrieves relevant snippets from a knowledge source and puts them into the model’s context so the model can answer with current, citable private data instead of relying only on training weights. We embed chunks, retrieve by hybrid search, optionally rerank, then generate with instructions to use only that context. The trade-off is we now have a retrieval quality problem, not just a prompt problem.

**Keywords they listen for:** grounding, chunking, embeddings, hybrid, rerank, citations, evals, ACL.

**Weak:** “RAG connects LLMs to documents.” That is a slogan. It does not prove you could build or debug it.

**Follow-up you should already have:** Why not fine-tune? Because knowledge changes, we need citations, and fine-tuning is for *behavior*, not a wiki.

---

## 2. Comparison — DEFINE / SIMILARITY / DIFFERENCE / USE CASE / TRADE-OFF / RECOMMEND

**Use when:** RAG vs fine-tune, BM25 vs dense, agent vs workflow, MCP vs function calling, Pinecone vs pgvector, Bedrock vs Foundry.

Template:

1. Define both in one line each.
2. What problem they share.
3. The actual axis they differ on (knowledge vs behavior, lexical vs semantic, control vs flexibility).
4. When you pick A. When you pick B. When you combine.
5. Recommendation *for the interviewer’s implied product*, or ask one clarifying question first.

### Worked: Agent vs workflow

> A **workflow** is a predetermined graph; the LLM fills slots or makes local decisions. An **agent** chooses the next action at runtime from tools and observations. Both can call tools. They differ in who owns control flow. I use a workflow when the business process is known — refund eligibility, KYC, invoice coding — because I can test, budget tokens, and audit. I use an agent when the step sequence is genuinely unknown — research, messy IT troubleshooting. Default in production is workflow with LLM steps. Multi-agent is a last resort for specialization or parallelism, not a badge.

---

## 3. “How would you implement X?” — CONTEXT / DESIGN / IMPLEMENT / VERIFY / OPERATE

**Use when:** practical questions (“How do you chunk?”, “How do you do HITL?”, “How do you eval?”).

| Step | Meaning |
| --- | --- |
| CONTEXT | Ask 1–2 constraints (data type, latency, risk) |
| DESIGN | Chosen approach and why |
| IMPLEMENT | Concrete components / sketch |
| VERIFY | Metrics and tests |
| OPERATE | Failure, monitoring, cost |

You can skip CONTEXT if they already specified the product. Never skip VERIFY. That is the 2026 fail.

---

## 4. Architecture / system design — REQUIREMENT → TRADE-OFF

Full 17-step version lives in `design/20-system-design.md`. The **spoken skeleton** in a 45-minute interview:

```
1. Clarify  (2–4 min)   users, data, actions, risk, latency, budget
2. FRs      (2 min)     Q&A? citations? tools? tenancy?
3. NFRs     (2 min)     p95, $/query, residency, RPO
4. Scale    (2 min)     docs, QPS, tokens, storage
5. API + data model (3)
6. Diagram  (8–10)      ingest path vs query path; optional agent loop
7. Deep dives they pick: ACL, evals, failures, cost (remaining time)
```

**One-line opener that scores well:**

> “I’ll separate ingestion from query, make retrieval identity-aware, put evals in the ship path, and only add an agent loop if the user is asking the system to *do* something with unknown steps.”

**Never start with:** “I’d use LangGraph, Pinecone, and GPT.” That is a shopping list.

---

## 5. Troubleshooting — OBSERVE / ISOLATE / HYPOTHESIZE / VERIFY / FIX / PREVENT

**Use when:** anything broken: latency, quality, cost, 429, tenant leak, CrashLoop.

| Step | You do | Anti-pattern |
| --- | --- | --- |
| OBSERVE | What changed? When? Which slice of traffic? | Jump to “tune the prompt” |
| ISOLATE | Retrieval vs generation vs tools vs infra | Treat the system as one blob |
| HYPOTHESIZE | Ranked 2–3 causes | 12 unranked ideas |
| VERIFY | The metric or trace that would confirm | “I’d try a few things” |
| FIX | Mitigate now, then correct | Only a long-term rewrite |
| PREVENT | Eval, alert, gate, design change | “Be more careful” |

### Worked: “Latency doubled”

> Observe: start time, deploy, model change, index size, p50 vs p95, TTFT vs retrieval vs tools. Isolate: if TTFT up, provider/prefill; if retrieval up, k, rerank, filter; if tools, fan-out. Hypothesize: context length explosion, lost prompt cache, HNSW efSearch, agent loop. Verify with traces. Fix: cache, shrink context, cap tools, smaller model for easy traffic. Prevent: budgets, regression tests on p95, cost/latency SLOs.

---

## 6. Coding narration — RESTATE / EXAMPLES / PLAN / CODE / TEST / COMPLEXITY

**Use when:** live Python/SQL.

1. Restate the problem and I/O types.
2. Two examples including an empty/error case.
3. Plan in 20 seconds (functions, not cleverness).
4. Write working code first, then tighten.
5. Tests: happy path, empty, malformed JSON, timeout.
6. Complexity and production notes (retries, logging).

AI-engineer interviews punish silent LeetCode style. They want operable code.

---

## 7. Behavioral — STAR + YOUR DELTA

| Letter | Content | Trap |
| --- | --- | --- |
| Situation | Context, stakes, one sentence | Novel-length backstory |
| Task | *Your* job, not the team’s | “We were asked to…” |
| Action | 3–5 decisions you made | List of tools |
| Result | Number, learning, what you’d repeat | “It went well” |

**Add a delta line:** “If I did it again I would add X.” Senior interviewers listen for that.

Time: 90–150 seconds. If they want more, they will ask.

---

## 8. Project deep dive — LAYERED STORY

Keep four versions of every project:

| Length | Contents |
| --- | --- |
| 30s | Problem, your role, outcome metric |
| 2 min | Architecture boxes, why key choices, one hard problem |
| 5 min | Data flow, evals, security, deploy, failure |
| Defense | Pre-answered “why not X?” for model, DB, framework, cloud |

Never say “we used LangChain” as the achievement. The achievement is “citation faithfulness from 0.62 to 0.86 by hybrid + rerank + prompt that refuses ungrounded claims, at +40ms.”

---

## 9. Customer / FDE scenario — SCOPE / DISCOVER / OPTIONS / V0 / RISK / TIMELINE

**Use when:** Palantir-style deployment, solutions role-play, “you’re on site Monday.”

1. **Scope:** What does good look like? Who signs off? What is out of scope?
2. **Constraints:** Data, identity, residency, systems of record, political landmines.
3. **Discover:** Week-1 questions and who you will sit with (including non-engineers).
4. **Options:** Two or three, with trade-offs. Recommend one.
5. **V0:** Narrow workflow, HITL, eval set, rollback.
6. **Risk:** Hallucination, leak, change management, on-call.
7. **Timeline:** Honest phases. No 2-week miracle.

Do not open with a architecture diagram.

---

## 10. Security answer — ASSET / ATTACK / CONTROL / DETECT / LIMIT BLAST

**Use when:** injection, MCP, tenancy, “is this safe?”

1. What is the asset (docs, tools, money movement, secrets)?
2. How does an attacker reach the model (user, retrieved doc, tool output, image)?
3. Control at that boundary (allowlists, schema validation, identity filters, sandbox).
4. Detect (denylist is insufficient; log tool args, canary docs, anomaly on tool mix).
5. Blast radius (read vs write, human approval, rate limits, per-tenant keys).

**Never:** “The model is aligned” or “we have a system prompt that says ignore injections.”

---

## 11. Cost answer — MEASURE / ATTRIB / CUT / GOVERN

1. Measure: $/query, tokens in/out, cache hit, cost per *successful task*.
2. Attribute: model vs embed vs rerank vs tools vs logs vs GPU idle.
3. Cut in order: cache → route to small model → shrink context → stop loops → batch → self-host only if volume/compliance justifies.
4. Govern: budgets, alerts, kill switches, per-tenant quotas.

---

## 12. “I don’t know” — BOUNDARY / RELATED / REASON / VALIDATE

This is not a failure if done in 20 seconds with composure.

1. **Boundary:** “I haven’t operated Milvus at a billion vectors.”
2. **Related:** “I have run pgvector and Qdrant at X scale; the issues I hit were filtered ANN and memory.”
3. **Reason:** “At a billion I’d expect partitioning, PQ compression, and a dedicated serving cluster rather than a single HNSW graph.”
4. **Validate:** “I’d confirm with a recall/latency bake-off on a 1% sample and the vendor’s filtered-query docs.”

### Worked examples

**Unknown API:** “I don’t know Bedrock AgentCore’s exact primitive names from memory. The pattern I would look for is a managed ReAct loop with IAM-scoped tools, CloudWatch traces, and Guardrails on I/O. I’d verify against current AWS docs before designing the landing zone.”

**Unknown paper:** “I haven’t read that paper. From the name, it sounds like hierarchical indexing. I’d compare it to RAPTOR-style trees: better for long reports, worse ops complexity. I’d want an ablation on their corpus before adopting.”

**Unknown number:** “I won’t invent GPU VRAM math. KV cache is `2 * layers * hidden * seq * batch * precision`. I can compute it if we pick a model, or I can reason qualitatively: long context plus large batch is the memory cliff.”

Bluffing dies on the next follow-up. Reasoning from fundamentals often *is* the test.

---

## Which framework to grab (cheat)

| You hear | Grab |
| --- | --- |
| “What is…” | WHAT/WHY/HOW/EXAMPLE/TRADE-OFF |
| “X vs Y” | Comparison |
| “How would you build/implement” | CONTEXT/DESIGN/IMPLEMENT/VERIFY/OPERATE |
| “Design a system…” | System design skeleton |
| “This is broken / p99 / cost spike” | OBSERVE…PREVENT |
| “Write a function…” | Coding narration |
| “Tell me about a time…” | STAR |
| “Walk me through your project” | Layered story |
| “You’re at the customer…” | SCOPE…TIMELINE |
| “How do you secure…” | ASSET…BLAST |
| Silence in your head | BOUNDARY/RELATED/REASON/VALIDATE |

Practice switching frameworks out loud. The content in later chapters is raw material. This chapter is the machine that turns it into an interview answer.
