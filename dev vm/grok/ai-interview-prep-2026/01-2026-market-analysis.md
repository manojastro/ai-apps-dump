# 01 — 2026 AI Interview Market Analysis

**What this chapter is for:** so you stop preparing for the wrong job.

The title “AI Engineer” in 2026 covers at least three different jobs. Preparing as if they are one role is a common rejection reason.

This handbook’s **primary eight** are the titles you actually prepare: AIOps, Cloud AI, Intelligent Automation, AI Security, Forward Deployed / AI Deployment, GenAI / Agentic AI, AI Solutions Engineer, AI Solutions Architect. “AI Engineer” on a JD is usually GenAI / Agentic with extra nouns. Map it; do not invent a ninth generic prep track.

---

## 1. The working definition of the job

From ~889 unique “AI Engineer” listings analyzed in January 2026 (AI Shipping Labs):

- **95.6% production-oriented**, 4.4% research-oriented
- **~70% AI-first** (build RAG, agents, LLM apps)
- **~28.5% AI-support** (platforms, GPU, pipelines, monitoring)
- **<2% classical ML/DL** despite the title

Working definition used by hiring managers in 2026:

> An AI engineer owns the design, evaluation, and production operation of systems built on foundation models.

You are not hired to invent a new model. You are hired to make a model-backed product reliable, measurable, cheap enough, and safe enough to run.

---

## 2. What the market actually asks for

Skill frequencies from that JD set (share of roles mentioning the skill):

| Cluster | Skill | % of roles | Interview implication |
| --- | --- | --- | --- |
| Language | Python | 82.5% | Coding rounds are Python-first |
| Language | TypeScript | 23.4% | FDE / solutions / full-stack AI |
| Language | FastAPI | 10.7% | Build a service, not a notebook |
| GenAI | RAG | 35.9% | Highest-probability architecture topic |
| GenAI | Prompt engineering | 29.1% | System-level, not “write a clever prompt” |
| GenAI | LLM integration | 25.4% | APIs, tokens, latency, cost, fallbacks |
| GenAI | Agents | 14.4% | Fastest-growing; core for agentic titles |
| GenAI | Fine-tuning | 8.5% | Do not over-index unless JD is LLM infra |
| Infra | AWS | 40.1% | Default cloud in many loops |
| Infra | Docker | 31.0% | Expected, not a bonus |
| Infra | CI/CD | 29.3% | How you ship, not just how you demo |
| Infra | Kubernetes | 29.1% | Cloud AI, deployment, AIOps, platform |
| Infra | Azure | 23.9% | Enterprise / Foundry loops |
| Infra | GCP | 23.0% | Vertex / Gemini loops |
| ML | PyTorch | 22.0% | LLM Engineer and serving-heavy roles |
| Data | Vector DBs | 10.8% | Named less than RAG; still assumed |
| Data | PostgreSQL | 9.3% | Metadata, tenancy, pgvector |

**MARKET OBSERVATION:** Agents at 14.4% in January 2026 understates interview weight by September 2026. Agentic titles, MCP, tool calling, and “when not to use an agent” now appear in most applied AI loops even when the JD still says “GenAI / RAG.”

**MARKET OBSERVATION:** Evaluation is under-mentioned in JDs (~4.5% explicit) and over-weighted in interviews. Hiring managers use evals as a proxy for “has this person shipped.”

---

## 3. How interviews actually break down (applied AI, 2026)

Compiled from candidate reports across 25+ AI-native companies through May 2026:

| Block | Share of technical signal | Typical questions |
| --- | --- | --- |
| RAG / evals / agents | ~40% | Design RAG for X; why answers are still wrong; agent vs workflow |
| Production systems | ~30% | Latency, cost, multi-tenant isolation, provider outages, observability |
| LLM internals | ~20% | Attention intuition, KV cache, sampling, context degradation, serving |
| Behavioral / judgment | ~10% | Shipped story, when you did *not* use AI, production failure |

Frontier labs (OpenAI, Anthropic, DeepMind, and similar) still add 1–2 algorithmic or ML-coding rounds.

Applied AI teams (Cursor, Replit, Vercel, Glean, Harvey, most product companies) increasingly skip LeetCode-hard in favor of practical building: parse JSON, implement retries, write a chunker, design RAG with ACLs.

**Do not prepare only traditional ML interviews.** Classical training pipelines, XGBoost, and from-scratch backprop appear in a small minority of these titles.

---

## 4. Role cluster map (so you target the right loop)

```
                    +------------------+
                    |  LLM Engineer    |  serving, KV cache, quantization,
                    |  (model/runtime) |  vLLM, LoRA, eval harness
                    +--------+---------+
                             |
     +-----------------------+-----------------------+
     |                       |                       |
+----v-----+          +------v------+         +------v-------+
| GenAI    |          | Agentic AI  |         | Cloud AI /   |
| Engineer |          | Engineer    |         | Platform     |
| RAG,     |          | tools,      |         | Bedrock,     |
| prompts, |          | state,      |         | Foundry,     |
| evals,   |          | MCP,        |         | Vertex, K8s  |
| apps     |          | guardrails  |         +------+-------+
+----+-----+          +------+------+                |
     |                       |                       |
     +----------+------------+-----------+-----------+
                |                        |
         +------v-------+         +------v--------+
         | Solutions    |         | FDE / FDAIE / |
         | Eng + Arch   |         | Deployment    |
         | customers,   |         | on-site,      |
         | trade-offs,  |         | ambiguity,    |
         | governance   |         | messy data    |
         +------+-------+         +---------------+
                |
     +----------+-----------+
     |                      |
+----v-----+         +------v------+
| AI       |         | AIOps /     |
| Security |         | Intelligent |
| OWASP,   |         | Automation  |
| agents,  |         | correlation,|
| MCP      |         | RCA, HITL   |
+----------+         +-------------+
```

### GenAI Engineer vs Agentic AI Engineer

This split is now explicit in hiring (Uplers, September 2026). Resumes look similar. Interviews do not.

| Capability | GenAI Engineer | Agentic AI Engineer |
| --- | --- | --- |
| LLM API integration | Core | Core |
| Prompting | Core | Supporting |
| RAG | Core | Common |
| Tool calling | Supporting | Core |
| Planning / orchestration | Limited | Core |
| Memory and state | Supporting | Core |
| Evaluation | Output quality | Output + task completion |
| Guardrails | Important | Critical |
| Failure recovery | Supporting | Core |
| Observability | Application-level | Workflow / trajectory-level |

**Interview test that separates them:** “The API fails on step 3 of a 7-step task. What happens to state, retries, and the user?”

If you only talk about a better prompt, you are being scored as a GenAI generalist, not an agentic engineer.

### LLM Engineer

Closer to inference and model operations than to chat UX. Expect KV cache math, batching, quantization, LoRA vs RAG vs prompt, tokens-per-second, cost-per-million, eval gates when a vendor model version changes.

### Cloud AI Engineer / AI Deployment Engineer

You are scored on landing the model in a real account: IAM / Entra, private networking, Bedrock Knowledge Bases vs Azure AI Search vs Vertex AI Search, GPUs on EKS/AKS/GKE, cost alarms, rollback.

### AIOps Engineer / Intelligent Automation Engineer

2026 AIOps is not “we clustered alerts with k-means.” It is: topology-aware correlation, LLM-drafted RCA, ServiceNow tickets, and **gated** remediation. Interviewers punish unbounded self-healing.

### AI Security Engineer

OWASP LLM Top 10 **2026** is the shared vocabulary. Excessive Agency climbed to #3 because production agents caused real incidents. MCP security (tool poisoning, shadow servers, token leakage) is now a first-class topic.

### Forward Deployed Engineer / Forward Deployed AI Engineer

The loop is not a standard SWE loop with extra AI. The discriminator is the **open-ended deployment scenario**: underspecified customer problem, compliance, messy data, stakeholders, v0 with HITL, evals, and a timeline. Jumping to architecture before scoping is the #1 fail.

### AI Solutions Engineer vs AI Solutions Architect

| | Solutions Engineer | Solutions Architect |
| --- | --- | --- |
| Primary job | Make the customer successful on the product | Design the system the customer can operate |
| Interview flavor | Discovery, demo, objection handling, light design | End-to-end architecture, governance, cost, integration |
| Coding | Sometimes practical, sometimes none | Rarely LeetCode; sometimes architecture decision records |
| Failure mode | Feature dump without customer workflow | Tool soup without requirements and operating model |

---

## 5. What “production GenAI” means in interviews

When a hiring manager says “production,” they mean all of the following, not “it ran on my laptop”:

1. **AuthN/AuthZ** — user identity reaches retrieval and tools.
2. **Evaluation** — golden set, regression on prompt/model change, ship bar in numbers.
3. **Observability** — traces for prompt, retrieval, tools, tokens, cost, latency.
4. **Failure handling** — timeouts, 429s, provider outage, empty retrieval, looping agent.
5. **Cost control** — cache, routing, budgets, $/successful task.
6. **Security** — prompt injection (including indirect), data leakage, least-privilege tools.
7. **Change management** — prompt/model/index versioning, canary, rollback.

If your project story cannot touch at least four of these, expect a mid-level ceiling even if the architecture diagram is pretty.

---

## 6. Current architecture patterns interviewers expect you to know

These are the 2026 defaults. You do not have to have used every product. You must know *why* the pattern exists.

| Pattern | When it is the default | When it is the wrong default |
| --- | --- | --- |
| Hybrid retrieval (BM25 + dense) + rerank | Almost every enterprise RAG | Tiny corpus you can scan; pure structured query |
| Citations + faithfulness check | Any answer users might trust | Pure creative generation |
| Deterministic workflow with LLM steps | Known business process | Truly open-ended research |
| Agent with tools + hard limits | Unknown step sequence | Refund / delete / email without HITL |
| MCP servers behind a gateway | Many tools, many apps, enterprise identity | One tight internal function |
| Model routing (small → large) | Cost/latency sensitive products | One ultra-hard reasoning task |
| Prompt + RAG before fine-tune | Changing knowledge, citations needed | Stable style/format the prompt cannot lock |
| Human approval on write tools | Anything irreversible | Read-only copilots |

Anthropic’s “Building effective agents” advice is still the senior opinion in 2026: start with the simplest orchestration that works; add agents only when the model must decide the next step.

---

## 7. Framework and protocol reality (do not marry a library)

Named in 2026 JDs and interviews, in rough interview-frequency order for applied roles:

**Orchestration:** LangGraph (state graphs, durable execution), OpenAI Agents SDK, Google ADK, Microsoft Agent Framework / Semantic Kernel, PydanticAI, CrewAI, AutoGen, Bedrock Agents / AgentCore, Azure Foundry Agent Service.

**Retrieval:** LlamaIndex, LangChain (still present, less of a differentiator), Haystack, native cloud search (Bedrock Knowledge Bases, Azure AI Search, Vertex AI Search / Gemini grounding).

**Eval / obs:** LangSmith, Langfuse, Arize Phoenix, MLflow, OpenTelemetry, cloud APM (Datadog LLM Observability, Azure Application Insights, CloudWatch, GCP Cloud Trace).

**Protocols:** MCP (tools, resources, prompts; host / client / server); A2A (agent-to-agent). MCP does **not** replace RAG. MCP does **not** replace function calling inside one app. Know the distinction cold.

**Interview-safe stance:** “I pick the orchestrator for state, durability, and control. I can implement the same pattern without a framework for a first agent, then adopt a graph/runtime when we need persistence, HITL, and replay.”

---

## 8. Cloud AI platforms in 2026 interviews

Do not choose a cloud by model leaderboard in an interview. Choose by **data gravity, identity, and operating model**.

| Platform | Interview-safe fit | What they will probe |
| --- | --- | --- |
| AWS Bedrock | AWS-native, multi-model, IAM/VPC already exists | Knowledge Bases, Guardrails, Agents/AgentCore, IAM, CloudWatch, cost |
| Azure AI Foundry (Microsoft Foundry) | M365 / Entra / Purview estate | Azure OpenAI vs Foundry catalog, AI Search hybrid RAG, Agent Service, Content Safety, PTU |
| Vertex AI / Gemini Enterprise Agent Platform | GCP data (BigQuery, GCS), Gemini-first | Agent Engine, ADK, A2A, Vertex AI Search, evaluation, identity |

Hybrid is common: Foundry for M365-grounded internal agents, Bedrock or Vertex for a specific model family or data plane.

---

## 9. Security expectations that now appear in *every* senior loop

OWASP GenAI LLM Top 10 **2026** (published August 2026; incident-weighted):

1. Prompt Injection (expanded: cross-modal, memory, agent blast radius)
2. Sensitive Information Disclosure
3. **Excessive Agency** (biggest climb; agents in production)
4. Supply Chain
5. Data and Model Poisoning
6. Unbounded Consumption (cost/availability)
7. Misinformation
8. Hidden Context Exposure (not just system-prompt leakage)
9. Vector and Embedding Weaknesses
10. Improper Output Handling

OWASP MCP Top 10 (2025 numbering; next revision targeted October 2026) is fair game for agentic / FDE / security roles: token leakage, scope creep, tool poisoning, supply chain, command injection, intent-flow subversion, weak authz, missing telemetry, shadow MCP servers, context over-sharing.

You do not need to reciting numbers. You need to design as if these are real.

---

## 10. Coding expectations — calibrated, not LeetCode-maxed

| Company type | Coding flavor | What to practice |
| --- | --- | --- |
| Frontier lab | 1–2 algorithmic + ML coding (tokenizer, attention in numpy, batching) | Python + complexity + ML internals |
| Applied AI product | Practical: JSON, retries, chunking, FastAPI, async | Production Python |
| Palantir-style FDE | Medium DS&A dressed as messy data + tests | Parsing, SQL-ish, APIs |
| Consulting / SI | Light coding or none; more design + customer | Scenarios |
| Enterprise platform | Python + IaC + debugging a Dockerfile/K8s YAML | Ops-adjacent coding |

**Prioritize:** parsing API responses, exponential backoff, rate limiting, chunking, cosine similarity, SQL, FastAPI, tool schemas, structured logging, tests. Competitive programming is a side bet, not the core.

---

## 11. Compensation and leveling (directional, not a promise)

Public 2026 ranges vary wildly by city and company. Use them only to sanity-check recruiter screens:

- Applied AI Engineer (US, mid): roughly $150k–$320k total, wide band
- AI-first / frontier IC: $250k–$500k+ TC at the high end
- India / EU enterprise bands are lower in cash, still competitive vs local SWE
- Agentic production experience currently prices above “chatbot + RAG demo”
- FDE / FDAIE often pays like senior SWE plus a travel/customer premium

Never invent a number in a recruiter call. See Chapter 27.

---

## 12. What this means for *your* prep

1. **Pick a primary role.** The loops differ.
2. **Make RAG + evals + production failure modes automatic.** They leak into every title.
3. **Add agents, MCP, and security** even for GenAI roles — they are the 2026 follow-up.
4. **Do not over-study fine-tuning or training** unless you are targeting LLM Engineer / research-adjacent teams.
5. **Build one honest production-shaped project** with traces, evals, and a postmortem. Interviewers detect tutorials in under five minutes.
6. **Practice speaking trade-offs.** The market is full of people who can name LangGraph. It is short of people who can say when LangGraph is unnecessary.

Next: [02-interview-process-by-role.md](02-interview-process-by-role.md).
