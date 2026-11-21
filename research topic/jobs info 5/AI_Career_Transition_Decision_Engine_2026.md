# AI Career Transition Decision Engine 2026 - Synthesis of 5 Deep Research Streams
India | 8.5yr IT Ops/Service Desk + Testing/Automation (Java/Selenium/API) | Target 20-25+ LPA -> 30-35+ LPA
Date: 2026-09-06 | Source pack: Top_5_AI_Career_Transition_Deep_Research_Prompts_2026.docx

## 1. The 5 Streams (what was researched in parallel by 5 subagents)

1. **Interview Intelligence** - 5-stage loop (HR -> Python/SQL -> Track deep-dive -> System/Prod/LLMOps -> Behavioral). Startups add take-home RAG/agent. Services/GCC 2-4 rounds faster. Make-or-break: RAG eval + failure-mode reasoning, not framework names. "We'll improve prompt" = reject.
2. **Career-Transition Success Mining** - 20 anonymized patterns CP-01..CP-20. Winner meta-pattern: Current -> internal AI bridge (AIOps owner / RAG pilot / automation+LLM / Cloud AI lead) -> external AI title. Internal preserves seniority ~2x better than direct external.
3. **Skill-Gap & Learning ROI** - ROI /100 model (JD25+INT15+XRole15+Sal10+Trend10+Port10+Trans5+Eff10). Top: Python93, RAG92, FastAPI91, Prompt+Structured90, LangChain+LangGraph89, MCP88, Bedrock85, pgvector85, Evals85.
4. **Company Target Intelligence** - 115 employers mapped (Tier S12 / A28 / B45 / C30). Verified Sep 2026: Microsoft WTI 32% Frontier India, 400k+ Copilot seats Infosys/TCS/Wipro/LTIM; Inc42 170+ AI startups $1.5B+. No salaries invented - re-verify live JDs.
5. **System Design & Architecture** - 6-layer anatomy (data/context, model boundary, orchestration, eval, serving, recovery). 16 cases + 12 trade-offs. Senior edge: ACLs-in-query, freshness CDC+tombstones, gateway fallback, 4-layer guardrails, trajectory evals, KEDA-on-queue.

Common 8 roles: AIOps, Cloud AI, Intelligent Automation, AI Security, FDE/AI Deployment, GenAI/Agentic, AI Solutions Eng, AI Solutions Architect.

## 2. Decision: Primary / Secondary / Backup

**PRIMARY (82/100 AIOps, 80/100 Cloud AI - tie):**
- AIOps Engineer + Cloud AI Engineer dual-track (same prep, two titles). Closest to Ops, highest GCC+services volume, preserves Senior.
- Stack: AWS PRIMARY (Bedrock+KB+Guardrails+Lambda), Azure SECONDARY (OpenAI+AI Search+Foundry). pgvector primary, Qdrant secondary. LangChain+LangGraph primary, MCP required.

**SECONDARY (74/100 Solutions Eng, 71/100 Intelligent Automation):**
- AI Solutions Engineer / Intelligent Automation. Rewards stakeholder + troubleshooting + TCO storytelling. Needs 1 real RAG deploy + live debug.

**STRETCH step-2 (58 GenAI/Agentic, 55 Architect, 48 FDE, 42 AI Security):**
- Do after primary title + 2 prod repos. FDE Palantir-tier + AI Security need extra bar. ML Engineer out-of-scope.

Positioning: "Ops leader who ships observable, cost-controlled, secure agents on AWS/Azure" - not "8.5yr Ops trying AI".

## 3. Top 10 Cross-Role Skills (interview per hour)

1. Python+API+Pydantic 2. RAG full chain+hybrid+rerank 3. LangChain/LangGraph+HITL 4. MCP 5. Evals+RAGAS+golden sets 6. Docker+CI+Cloud obs 7. IAM/secrets+guardrails 8. Postgres/SQL+vector+RBAC 9. Event/queues/Step Functions 10. Discovery->demo->prod storytelling + cost/latency

Picks: AWS deep, Azure working; LangGraph runtime; pgvector default (<5M); Langfuse build + LangSmith read; OTel GenAI semconv.

STOP list (80 days): train transformers, TF/Keras mastery, adv math, AutoGen deep, custom vectorDB, React mastery, UiPath deep (unless IA lane), multi-cloud expert, CKA, Databricks admin, LoRA GPU runs.

## 4. Portfolio Bar (minimum for 20-25 LPA screens)

A. `rag-prod-pgvector` (hybrid RRF + rerank 50->5 + RAGAS + CI gate + cost log + citations + abstain)
B. `agent-itsm` (LangGraph + MCP + checkpointer + interrupt/HITL + step/budget caps + Langfuse + live deploy)
C. `llm-shield-lite` (OWASP LLM 2025 mapped + Presidio + red-team 10 payloads + audit log)
Each: ARCHITECTURE.md + EVALS.md + RUNBOOK.md + 2-min Loom (kill-primary demo).

AIOps bridge alt: Runbook RAG + log->action agent with HITL + cost/eval dashboard.

## 5. Where to Apply (Top 20 now)

Tier S core Wave1: ServiceNow + PagerDuty/Datadog/Dynatrace/Splunk, Fractal/Quantiphi/Tiger/Tredence, Infosys/TCS/Wipro/HCL/LTIM/Persistent AI practices, JPMC/Wells/HSBC/Walmart/Optum GCCs, UiPath.
Wave2 stretch: Microsoft/AWS/GCP, Databricks/Snowflake/Confluent/MongoDB, Salesforce Agentforce, Palo Alto/CrowdStrike/Zscaler, PhonePe/Flipkart, Jio/Airtel.
Wave3 moonshots: Krutrim/Sarvam/Neysa/Ema/DevRev/Observe/CodeRabbit/Atomicwork/Truefoundry + BCG X + remote-first.
Cities: Bengaluru + Hyderabad primary, Pune+Chennai secondary, Remote parallel only.

Sequencing: Wave1 (wks1-3, 30-35 apps for leverage) -> Wave2 (wks3-6, 20-25) -> Wave3 (wks5-8, 15-20). 10-12 tailored apps/week, 2 referrals/day.

Comp: No live JD salary extracted 05-Sep-2026 (429/JS blocks disclosed). Directional: Senior AI 19-34 LPA (4-7yr), Architect/Lead 34-58 (7-10yr). Verify per JD + Levels.fyi/AmbitionBox 20+ points.

## 6. 80-Day Roadmap (2-3h/day, 60% build /20% evals /20% prep)

Wk1 Python async/Pydantic/pytest | Wk2 FastAPI+Postgres+Docker/CI | Wk3 LLM core tokens/cost | Wk4 RAG naive pgvector | Wk5 RAG prod hybrid/rerank/RAGAS 50Qs | Wk6 LangGraph state/HITL ticket agent | Wk7 MCP + Bedrock KB (or Azure) | Wk8 Guardrails OWASP+Presidio | Wk9 OTel+Langfuse cost dashboard | Wk10 AWS Lambda/GW/IAM/CW + Terraform + eval gate live URL | Wk11 Capstone ITSM AIOps + RFP README + demo | Wk12 Interview sprint (5 designs out loud, resume metrics, 10 apps/day).

System-design whiteboard: Clarify->Req (QPS/P99/freshness/cost)->High-level offline vs online->Data flow->Deep dive 2 subsys->Security->Scale->Obs/eval->Cost->Alternatives->Risks.

## 7. Interview Cheat Lines

- RAG wrong? Isolate retrieval vs generation, check Retrieve, chunks, top-k, rerank, query - not "improve prompt".
- RAG vs fine-tune? Changing/citable -> RAG; style/behavior -> LoRA; version embeddings, measure Recall@5/faithfulness.
- Why LangGraph? State/routing/retries/checkpoints/HITL/audit; LangChain linear, CrewAI prototype overhead.
- MCP vs A2A? MCP agent->tool (80% prod), A2A peer delegation only.
- Security? Scoped creds + allowlist + human gates + output encode + assume leak, no secrets in prompt.
- Cost? Token attribution -> rerank cache + semantic cache -> small/large routing -> streaming.

## 8. Files & Next Steps

- This file = decision engine. Full subagent reports retained in session (Interview, Transition, Skills, Companies, System Design).
- Next: generate Excel/Word per original prompts (Master cases, Skills matrix, Companies 115, Cases 42Q) - say which stream to materialize first (recommend Skills + Companies).
- Re-verify: LinkedIn Jobs + ATS + Naukri per company on apply day; confirm cert names/prices (AWS ML Specialty retired Mar31-2026); pin MCP/OTel versions.

Anti-hallucination: no individual histories/salaries invented; anonymized patterns only; inferred stacks marked (Inferred); time-sensitive dated.
