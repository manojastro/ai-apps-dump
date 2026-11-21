# 04 — Most Frequently Asked Topics (Ranked)

Probability is **conditional on an applied AI / GenAI / Agentic / FDE / Solutions loop in 2026**, compiled from candidate reports, JD language, and hiring-manager write-ups. Frontier-lab research loops differ (more internals, more algorithms).

P = how often it appears. I = how much it moves the hire decision.

| Rank | Topic | P | I | Why they ask | Typical disguise |
| --- | --- | --- | --- | --- | --- |
| 1 | RAG end-to-end design | Very high | Critical | Default production pattern | “Knowledge assistant for X” |
| 2 | Evaluation / ship bar | Very high | Critical | Proxy for having shipped | “How do you know it works?” |
| 3 | Retrieval vs generation debug | Very high | Critical | Separates tutorials from operators | “Docs are right, answer is wrong” |
| 4 | Hybrid search + rerank | High | High | Production default | “BM25 vs embeddings” |
| 5 | Chunking strategy | High | High | Data-dependent judgment | “How would you split PDFs?” |
| 6 | Agent vs workflow | Very high | Critical | Anti-hype test | “Build an agent that…” |
| 7 | Hallucinations / grounding / citations | High | High | Trust | “How do you reduce hallucinations?” |
| 8 | Prompt vs RAG vs fine-tune | High | High | Decision tree | “Should we fine-tune?” |
| 9 | Cost control | High | High | Unit economics | “10x more expensive than planned” |
| 10 | Latency (TTFT, retrieval, tools) | High | High | Product feel | “p95 doubled” |
| 11 | Multi-tenant / ACL retrieval | High | Critical in enterprise | One leak ends the company | “Two customers, one index?” |
| 12 | Tool calling design | High | High for agentic | API design for models | “Design the tools” |
| 13 | Infinite loops / step budgets | High | High | Production agents | “It keeps calling search” |
| 14 | Prompt injection (esp. indirect) | High | High | OWASP LLM01 | “Wiki page jailbreaks the bot” |
| 15 | Observability / tracing | High | High | On-call | “How do you debug a bad answer?” |
| 16 | Model routing / small vs large | Medium-high | High | Cost/quality | “Always GPT-5?” |
| 17 | Provider failure / 429 / fallback | Medium-high | High | Reality of APIs | “OpenAI is down” |
| 18 | MCP | Medium-high | High for agentic/FDE | Standard for tools | “Why not just REST?” |
| 19 | Identity / IAM / Entra | Medium-high | High in enterprise | Who can see what | “User is in Finance only” |
| 20 | Vector index internals (HNSW/IVF) | Medium | Medium-high | Filter people who think it is brute force cosine | “How does the vector DB work?” |
| 21 | Context window / lost-in-the-middle | Medium | Medium | Context engineering | “We have 200k context, dump the PDFs” |
| 22 | KV cache / serving (LLM Engineer high) | Medium | High on infra track | Cost of decode | “Why is generation memory huge?” |
| 23 | Streaming (SSE) | Medium | Medium | UX + APIs | “Build the chat endpoint” |
| 24 | Docker/K8s failure | Medium | High for cloud/deploy | Ops | “CrashLoopBackOff” |
| 25 | HITL / approval | Medium-high | High for agents | Excessive agency | “Can it refund?” |
| 26 | GraphRAG / RAPTOR / HyDE | Medium-low | Medium | Depth spice | “Would you use a graph?” |
| 27 | Multi-agent | Medium | High as a *trap* | Overengineering detector | “Five specialists?” |
| 28 | Fine-tuning / LoRA | Medium-low | Medium | Know when *not* | “Let’s fine-tune on our wiki” |
| 29 | A2A | Low-medium | Low-medium | Protocol literacy | “How do agents talk?” |
| 30 | Classical ML | Low | Low for these titles | Don’t over-prep | “What’s XGBoost?” |

---

## Probability by round type

| Round | Top 5 topics |
| --- | --- |
| Recruiter | Shipped story, why this role, notice, comp, location |
| Tech screen | RAG definition+, agent vs workflow, Python comfort, resume probe |
| Coding | JSON, retries, chunking, SQL, FastAPI, tests |
| RAG / LLM | Chunking, hybrid, evals, hallucinations, cost |
| Agent | Tools, loops, HITL, MCP, eval trajectories |
| Design | Requirements, ACL, data flow, scale, evals, failures |
| Project | Why X not Y, your contribution, incident, metrics |
| HM | Judgment, collaboration, when not to use AI |
| FDE scenario | Scope, stakeholders, v0, compliance, timeline |
| Security | Injection, tenancy, excessive agency, MCP, audit |

---

## What is *declining* as an interview center of gravity

Still useful as context. Do not build your entire prep around them.

| Topic | Status | Keep this much |
| --- | --- | --- |
| Pure prompt-engineering trivia | Declining as a standalone round | System prompts, evals, versioning |
| LangChain API memorization | Declining | Patterns, not class names |
| Training GPT from scratch | Not the job | High-level transformer intuition |
| AutoGPT-style autonomous hype | Negative signal | Contrast with constrained graphs |
| “We use 12 agents” as a flex | Negative signal | Specialization + parallelism test |
| Fine-tune first | Negative signal | Decision tree in Chapter 09/10 |

---

## Hidden requirements (not always in the JD, always in senior follow-ups)

If the JD mentions any of the left column, prepare the right column even if unstated:

| JD phrase | Hidden interview topic |
| --- | --- |
| Enterprise / Fortune 500 | ACL, SSO, audit logs, residency |
| Healthcare / finance / public sector | HITL, citations, no-training clauses, DLP |
| Agents / copilot that *does* things | Excessive agency, idempotency, approvals |
| Multi-tenant SaaS | Namespace indexes, prompt-cache isolation |
| Reduce cost / scale | Caching, routing, smaller models |
| “Own production” | Tracing, on-call, rollback of prompts/indexes |
| MCP | Gateway, allowlists, tool poisoning |
| LangGraph | State, durability, HITL nodes — not a logo |

---

## A 12-topic core that covers ~80% of loops

If you can only go deep on a short list, use this order:

1. RAG architecture + hybrid + rerank
2. Evals and ship criteria
3. Debugging wrong answers
4. Agent vs workflow + loop control
5. Security: injection, tenancy, tool permission
6. Cost and latency
7. APIs: retries, 429, streaming
8. Project defense with numbers
9. System design framework
10. Cloud of the JD (one, deeply)
11. Observability traces
12. STAR stories (failure, conflict, shipped)

Everything else is a multiplier, not the base.

Next: [05-answer-frameworks.md](05-answer-frameworks.md).
