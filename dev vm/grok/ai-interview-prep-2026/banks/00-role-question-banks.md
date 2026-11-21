# Role-Specific Question Banks (Probability-Ranked)

Use this as a drill list. Full answers live in the topic guides. Practice out loud with Chapter 05 frameworks.

Legend: **L1** fundamentals · **L2** practical · **L3** production · **L4** troubleshooting · **L5** architecture · **L6** senior/architect

---

## GenAI Engineer (top 40)

| # | L | Question | Primary guide |
| --- | --- | --- | --- |
| 1 | L5 | Design RAG for a customer-support knowledge base | 10, 20 |
| 2 | L2 | How do you choose a chunking strategy? | 10 |
| 3 | L2 | BM25 vs dense vs hybrid vs rerank | 10, 14 |
| 4 | L4 | Retrieval is correct, answer is wrong. Debug. | 10, 22 |
| 5 | L3 | How do you evaluate RAG before shipping? | 10, 17 |
| 6 | L1 | What is RAG and why not just a bigger context window? | 09, 10 |
| 7 | L2 | RAG vs fine-tune vs prompt | 09, 10 |
| 8 | L3 | How do you cite sources and verify them? | 10 |
| 9 | L3 | Multi-turn RAG / query rewriting | 10 |
| 10 | L4 | Quality dropped after adding 1M documents | 10, 14 |
| 11 | L5 | Multi-tenant RAG with ACLs | 10, 21 |
| 12 | L3 | How do you reduce RAG latency? | 10 |
| 13 | L3 | When is RAG the wrong tool? | 10 |
| 14 | L1 | Temperature vs top-p | 09 |
| 15 | L2 | Structured outputs / function calling | 09, 08 |
| 16 | L4 | Hallucination measurement in production | 10, 17 |
| 17 | L3 | Prompt versioning and regression | 17 |
| 18 | L2 | Embedding model choice | 10, 14 |
| 19 | L3 | Index updates, deletes, freshness | 10 |
| 20 | L6 | Cost 10x over plan | 09, 17 |
| 21 | L4 | Provider 429 / outage | 08, 22 |
| 22 | L3 | Observability of an LLM feature | 17 |
| 23 | L2 | How does a vector DB actually search? | 14 |
| 24 | L5 | Ingestion of PDFs with tables/charts | 10 |
| 25 | L3 | Indirect prompt injection via retrieved docs | 19 |
| 26 | L2 | FastAPI streaming chat endpoint | 08 |
| 27 | L1 | Tokens, context window, lost-in-the-middle | 09 |
| 28 | L3 | Caching: embeddings, responses, prompt prefix | 09, 15 |
| 29 | L2 | Metadata filters | 10, 14 |
| 30 | L5 | Agent-lite: when to add tools on top of RAG | 11 |
| 31 | L4 | Empty retrieval | 22 |
| 32 | L3 | PII in prompts and logs | 19 |
| 33 | L2 | Cosine vs dot vs L2 | 14 |
| 34 | L6 | Ship criteria as numbers | 17 |
| 35 | L3 | Model routing | 09 |
| 36 | L4 | Eval scores flat, users complain | 17 |
| 37 | L5 | Design an LLM gateway | 21 |
| 38 | L2 | Pydantic schemas for tool/LLM output | 06 |
| 39 | L1 | Attention in one minute | 09 |
| 40 | L6 | What would you *not* use an LLM for? | 24 |

---

## Agentic AI Engineer (top 35)

| # | L | Question |
| --- | --- | --- |
| 1 | L1 | Agent vs workflow |
| 2 | L6 | When should you NOT use an agent? |
| 3 | L2 | How do you design tools for a model? |
| 4 | L4 | Agent loops on the same tool |
| 5 | L3 | Validate tool calls before execution |
| 6 | L3 | HITL before refund/email/delete |
| 7 | L3 | State recovery after a failed API at step 3 |
| 8 | L3 | Memory layers |
| 9 | L2 | MCP vs function calling vs REST |
| 10 | L5 | Enterprise MCP gateway |
| 11 | L4 | Debug an agent that is “sometimes wrong” |
| 12 | L3 | Evaluate agents (task, trajectory, tools, cost) |
| 13 | L6 | Five agents vs one |
| 14 | L3 | Idempotency of tools |
| 15 | L3 | Token/cost budgets and kill switches |
| 16 | L5 | Supervisor + specialists — bottleneck |
| 17 | L3 | Sandbox for code tools |
| 18 | L4 | Prompt injection via tool output |
| 19 | L2 | LangGraph vs a simple loop |
| 20 | L3 | Durable execution / resume |
| 21 | L6 | Excessive agency (OWASP LLM03) |
| 22 | L2 | Schema for tools |
| 23 | L4 | Duplicate side effects (double ticket) |
| 24 | L3 | Shared state vs message passing |
| 25 | L5 | Agent platform design |
| 26 | L2 | Termination conditions |
| 27 | L3 | Model for planner vs extractor |
| 28 | L4 | Cost runaway overnight |
| 29 | L3 | Audit log of every tool call |
| 30 | L6 | Governance of production agents |
| 31 | L2 | A2A at working knowledge |
| 32 | L3 | Retrieving top-K tools when catalog is large |
| 33 | L5 | Multi-agent ops copilot |
| 34 | L1 | ReAct loop |
| 35 | L4 | MCP server compromised |

---

## LLM Engineer (top 25)

| # | L | Question |
| --- | --- | --- |
| 1 | L1 | Attention / multi-head intuition |
| 2 | L2 | Prefill vs decode |
| 3 | L3 | KV cache memory math |
| 4 | L3 | Continuous batching / PagedAttention |
| 5 | L2 | Quantization INT8/INT4 trade-offs |
| 6 | L2 | GQA / MQA why |
| 7 | L3 | Speculative decoding when it helps |
| 8 | L3 | Prompt caching |
| 9 | L2 | LoRA vs full FT vs RAG |
| 10 | L3 | vLLM vs naive HF generate |
| 11 | L4 | Quality drop after vendor model update |
| 12 | L3 | Tokens/sec vs concurrency vs latency |
| 13 | L5 | Design an inference platform |
| 14 | L2 | Temperature/top-p for eval vs prod |
| 15 | L3 | Long-context degradation |
| 16 | L4 | GPU OOM |
| 17 | L3 | Structured decoding constraints vs quality |
| 18 | L6 | Self-host vs API |
| 19 | L2 | BPE / tokenization pitfalls |
| 20 | L3 | Eval harness for a model swap |
| 21 | L3 | Routing cascade |
| 22 | L4 | Tail latency |
| 23 | L2 | RoPE vs ALiBi at interview depth |
| 24 | L5 | Multi-model gateway with fair queues |
| 25 | L3 | Safety evals / refusal |

---

## AIOps Engineer (top 25)

| # | L | Question |
| --- | --- | --- |
| 1 | L1 | Metrics vs logs vs traces |
| 2 | L1 | Monitoring vs observability |
| 3 | L3 | Cardinality explosion |
| 4 | L4 | 10,000 alerts in an outage |
| 5 | L4 | Root cause vs symptom alerts |
| 6 | L3 | Topology / CMDB in correlation |
| 7 | L6 | Safe automated remediation |
| 8 | L3 | Rebuild on-call trust after a wrong group |
| 9 | L5 | Design an RCA copilot |
| 10 | L2 | OpenTelemetry |
| 11 | L3 | SLI/SLO/error budget |
| 12 | L4 | p99 5x after deploy |
| 13 | L2 | ServiceNow incident enrichment |
| 14 | L3 | LLM hallucination in RCA text |
| 15 | L3 | Alert quality / runbooks |
| 16 | L4 | Missing traces |
| 17 | L2 | Prometheus vs vendor APM |
| 18 | L5 | AIOps platform architecture |
| 19 | L3 | Change intelligence (deploys as a signal) |
| 20 | L6 | When not to auto-remediate |
| 21 | L3 | Noise reduction without dropping true pages |
| 22 | L2 | Anomaly detection failure modes |
| 23 | L4 | Remediation loop causing outage |
| 24 | L3 | Multi-account telemetry |
| 25 | L1 | AIOps vs LLMOps vs MLOps |

---

## Cloud AI Engineer (top 25)

| # | L | Question |
| --- | --- | --- |
| 1 | L5 | Bedrock vs Foundry vs Vertex — how do you choose? |
| 2 | L3 | Private RAG, no public internet |
| 3 | L3 | IAM/Entra for model and data |
| 4 | L2 | Knowledge Bases / AI Search / Vertex Search |
| 5 | L3 | PTU / provisioned throughput vs on-demand |
| 6 | L4 | GPU pods pending |
| 7 | L4 | Cost spike (tokens + logs + NAT) |
| 8 | L3 | Secrets: no keys in prompts or images |
| 9 | L5 | Landing zone for enterprise GenAI |
| 10 | L2 | Guardrails / Content Safety |
| 11 | L3 | Cross-region inference / residency |
| 12 | L4 | 429 from the platform |
| 13 | L3 | Canary a prompt/model/index |
| 14 | L2 | CloudWatch / App Insights / Cloud Trace for LLM |
| 15 | L5 | Multi-model gateway on one cloud |
| 16 | L3 | S3/Blob/GCS ingestion pipeline |
| 17 | L2 | Dockerfile for a FastAPI RAG service |
| 18 | L4 | CrashLoopBackOff after config change |
| 19 | L6 | Hybrid cloud (M365 agents + AWS data) |
| 20 | L3 | Network egress cost of embeddings |
| 21 | L2 | Step Functions / Durable Functions vs agent loop |
| 22 | L3 | Key Vault / Secrets Manager + rotation |
| 23 | L5 | GPU vs API for this workload |
| 24 | L3 | Audit (CloudTrail / Activity Logs) |
| 25 | L2 | Terraform vs console — what you version |

---

## AI Security Engineer (top 25)

| # | L | Question |
| --- | --- | --- |
| 1 | L1 | OWASP LLM Top 10 2026 — especially 01, 02, 03 |
| 2 | L3 | Direct vs indirect prompt injection |
| 3 | L4 | RAG returned another tenant’s data |
| 4 | L4 | Agent performed unauthorized action |
| 5 | L4 | MCP server compromised |
| 6 | L3 | Tool poisoning |
| 7 | L3 | RAG poisoning |
| 8 | L5 | Threat model a RAG+agent product |
| 9 | L3 | Output handling (XSS/SSRF via model output) |
| 10 | L3 | Unbounded consumption / cost DoS |
| 11 | L2 | Jailbreak vs injection |
| 12 | L3 | Hidden context exposure |
| 13 | L5 | Enterprise MCP gateway controls |
| 14 | L3 | Detections you would actually page on |
| 15 | L6 | Excessive agency controls |
| 16 | L2 | Secrets in traces |
| 17 | L3 | Supply chain (models, MCP servers, prompts) |
| 18 | L3 | Sandboxing code interpreter |
| 19 | L5 | AI security monitoring system |
| 20 | L3 | Red-teaming process |
| 21 | L2 | RBAC on retrieval |
| 22 | L4 | Canary documents |
| 23 | L6 | Governance / EU AI Act-style risk class |
| 24 | L3 | Logging without storing sensitive prompts |
| 25 | L1 | You cannot prompt-away injection |

---

## FDE / FDAIE (top 25)

| # | L | Question |
| --- | --- | --- |
| 1 | L6 | Underspecified customer: “use LLMs on our notes” — run the engagement |
| 2 | L2 | Messy CSV/JSONL parsing with tests |
| 3 | L5 | Search across SharePoint, Confluence, Slack |
| 4 | L3 | Week-1 discovery plan |
| 5 | L3 | v0 with HITL |
| 6 | L5 | Hospital / bank constraints (residency, identity) |
| 7 | L4 | Customer data is garbage — what now? |
| 8 | L3 | Hostile stakeholder |
| 9 | L5 | RAG with citations for claims review |
| 10 | L2 | SQL-ish over a fake schema |
| 11 | L3 | What does success look like? |
| 12 | L6 | When to say no to an agent |
| 13 | L3 | Handoff to customer team |
| 14 | L4 | Demo worked, production empty retrieval |
| 15 | L3 | Eval set from real tickets |
| 16 | L5 | Integration with system of record |
| 17 | L2 | Explain RAG to a non-technical director |
| 18 | L3 | Timeline you can defend |
| 19 | L6 | Safety incident at the customer |
| 20 | L3 | Scope cut to hit a date |
| 21 | L2 | Retry/pagination client |
| 22 | L5 | Design data pipeline + ontology-ish model |
| 23 | L3 | Logging in someone else’s VPC |
| 24 | L4 | SSO/SAML, no local users |
| 25 | L1 | Why FDE vs product SWE |

---

## AI Solutions Engineer / Architect (top 20)

| # | L | SE | SA | Question |
| --- | --- | --- | --- | --- |
| 1 | L5 | Y | Y | Design company-wide RAG |
| 2 | L6 | | Y | Operating model: who owns prompts, evals, incidents |
| 3 | L3 | Y | Y | Build vs buy vs cloud native |
| 4 | L3 | Y | Y | Security objection from InfoSec |
| 5 | L3 | Y | Y | Cost model for 10k employees |
| 6 | L2 | Y | | Discovery questions for a vague “we need AI” |
| 7 | L6 | | Y | Governance, model inventory, risk class |
| 8 | L5 | Y | Y | Multi-model strategy without lock-in theater |
| 9 | L3 | Y | Y | When the customer should *not* buy |
| 10 | L5 | | Y | Integration architecture (identity, data, tools) |
| 11 | L3 | Y | Y | Success metrics for a POC vs production |
| 12 | L4 | Y | Y | POC doesn’t survive real ACLs |
| 13 | L6 | | Y | Multi-region, residency, DR for GenAI |
| 14 | L2 | Y | | Explain agents to a VP in 3 minutes |
| 15 | L5 | | Y | Agent platform vs a pile of copilots |
| 16 | L3 | Y | Y | Data readiness assessment |
| 17 | L6 | | Y | Vendor lock-in: real vs fake |
| 18 | L3 | Y | Y | Change management / trust |
| 19 | L5 | | Y | Reference architecture with control planes |
| 20 | L2 | Y | Y | Questions you ask *them* (see Ch 34) |

---

## How to drill

1. Cover the answer. 60 seconds out loud.
2. Uncover only the “why they ask” line in the topic guide. Did you hit the signal?
3. Then read the senior answer.
4. Write a 6-part card (concept, logic, structure, keywords, example, trade-off).

Do not memorize this list as trivia. The same 12 core topics from Chapter 04 will reappear in new wording every time.
