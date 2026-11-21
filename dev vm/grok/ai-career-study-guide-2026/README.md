# 2026 AI Career Study Guide

**A complete job-transition curriculum for production AI engineering roles**

Version: 2026.09 (research window: March–September 2026)  
Audience: software engineers, IT/automation professionals, and adjacent technical roles transitioning into AI engineering  
Objective: go from “I have heard of this technology” to “I can implement it, explain its architecture, troubleshoot it, interview on it, and ship it in a production-quality project.”

This is not a skills list. It is a teach-from-zero professional book.

---

## How to use this book

1. Read **Chapter 01** (job market) so you understand *why* the curriculum is shaped this way.
2. Study the **Master Skill Map** in **Chapter 02**. That is the source of truth for priority, depth, and demand.
3. Use the **Role-to-Skill Matrix** in **Chapter 03** to pick a primary target role. Do not try to become all 8 roles at once.
4. Follow the **dependency map and staged roadmap** in **Chapter 05**. Do not skip Python/API foundations to jump into agents.
5. For every major technology, study the dedicated chapter. Each major skill uses the same 25-point teaching template.
6. Build the **portfolio projects** in Chapter 20. Interviews in 2026 punish demo-only RAG.
7. Drill the **interview bank** and **knowledge tests**. Answers for tests are in a separate file.

### Label legend used throughout

| Label | Meaning |
| --- | --- |
| **FACT** | Verified from official docs, specs, or directly quoted job descriptions |
| **MARKET OBSERVATION** | Pattern seen across multiple 2026 job postings / hiring analyses, not a universal law |
| **RECOMMENDATION** | Curriculum advice for a job-transition learner |
| **EMERGING TREND** | Rapidly growing in 2025–2026; important, but still settling |

### Priority and proficiency labels

**Priority:** CRITICAL · HIGH PRIORITY · GOOD TO KNOW · OPTIONAL · DECLINING / LEGACY

**Market demand:** Low · Medium · High · Very High

**Expected proficiency:** Awareness · Beginner · Working Knowledge · Production Ready · Advanced · Architect Level

---

## Target roles (primary 8)

1. AIOps Engineer
2. Cloud AI Engineer / AI Platform Engineer
3. Intelligent Automation Engineer
4. AI Security Engineer
5. Forward Deployed / AI Deployment Engineer (FDE, FDAIE, GenAI Ops)
6. GenAI / Agentic AI Engineer (includes LLM Engineer as a related serving track)
7. AI Solutions Engineer
8. AI Solutions Architect

**Related titles with overlapping skill stacks (do not ignore these postings):**

AI Engineer · Senior AI Engineer (LLM/RAG/LangGraph) · RAG Engineer · Multi-Agent Engineer · AgentOps Engineer · LLMOps Engineer · GenAI Full-Stack Engineer · Azure AI Foundry Engineer · Bedrock Engineer · Vertex AI Engineer · Observability + Agentic Platforms Engineer · Copilot Engineer · AI Platform Engineer · Enterprise Knowledge Assistant Engineer

**MARKET OBSERVATION:** Many 2026 postings titled “AI Engineer” or “Software Engineer” are actually agentic/RAG production roles. Source on skill, not only on title. LangGraph as a skill signal is often larger than the title boolean.

---

## What this book is *not*

- Not an academic ML research curriculum.
- Not a “train GPT from scratch” program.
- Not a prompt-engineering-only course.
- Not a recitation of 2023 LangChain tutorials.

**RECOMMENDATION:** Employers in 2026 hire software engineers who can ship LLM systems. They do not hire people who can derive attention from first principles but cannot debug a retrieval failure, a looping agent, or a 3× cost spike.

---

## Book map

| Ch | File | Contents |
| --- | --- | --- |
| 00 | `README.md` | How to use this book |
| 01 | `01-job-market-analysis.md` | 2026 market analysis from current JDs |
| 02 | `02-master-skill-map.md` | Master skill inventory with priority, demand, depth, hours |
| 03 | `03-role-to-skill-matrix.md` | Role × skill matrix (0–5) |
| 04 | `04-prioritization-radar.md` | Tiers, technology radar, what NOT to learn yet |
| 05 | `05-dependency-map-roadmap.md` | Learning sequence, stages, hours |
| 06 | `06-engineering-foundations.md` | Python, Git, APIs, testing, SQL, FastAPI |
| 07 | `07-llm-fundamentals.md` | Transformers, tokens, inference, prompting, tools, cost |
| 08 | `08-rag-complete-study-guide.md` | Full RAG curriculum at production depth |
| 09 | `09-agentic-ai-complete-study-guide.md` | Agents, multi-agent, LangGraph, when not to use agents |
| 10 | `10-mcp-and-a2a.md` | Model Context Protocol + Agent-to-Agent protocol |
| 11 | `11-vector-databases-and-data.md` | Embeddings, indexes, pgvector/Qdrant/Pinecone, SQL |
| 12 | `12-cloud-ai.md` | AWS Bedrock / Azure AI Foundry / Vertex AI |
| 13 | `13-production-engineering.md` | Docker, K8s, CI/CD, Terraform, serving, gateways |
| 14 | `14-llmops-observability.md` | Evals, tracing, Langfuse/LangSmith/Phoenix, OTel |
| 15 | `15-aiops-study-guide.md` | AIOps vs LLMOps, ServiceNow, Dynatrace, Splunk |
| 16 | `16-ai-security.md` | OWASP LLM Top 10, agent/MCP/RAG security, red team |
| 17 | `17-system-design.md` | Production architecture patterns and interview designs |
| 18 | `18-enterprise-automation.md` | n8n, HITL, ServiceNow/Salesforce, identity |
| 19 | `19-labs-and-mini-projects.md` | Hands-on labs per stage |
| 20 | `20-portfolio-projects.md` | Five enterprise-grade portfolio projects |
| 21 | `21-interview-bank.md` | Question bank with model answers |
| 22 | `22-knowledge-tests.md` | MCQs and scenarios (no answers) |
| 23 | `23-knowledge-test-answers.md` | Answer key |
| 24 | `24-job-readiness-checklist.md` | Final readiness checklist |

---

## Study contract with yourself

A realistic full transition for a working software engineer targeting **GenAI / Agentic / LLM / FDE / Solutions** roles:

- **Foundations already strong (Python + APIs + Git):** ~420–520 focused hours
- **Foundations weak:** add ~120–180 hours first
- **Adding Cloud AI + LLMOps + Security to architect level:** +150–200 hours
- **AIOps specialization (ServiceNow/Splunk/Dynatrace path):** treat as a parallel track, ~200 hours on top of observability basics

Do not study everything to Architect Level. The matrix tells you where 3 (Production Ready) is enough.

---

## Research method (so you can trust the map)

This guide was built from:

- Job postings dated March–September 2026 across LinkedIn, company career pages, startup.jobs, consulting firms (Accenture, EY, Deloitte, EPAM, Cognizant, Avanade, CGI, NTT DATA)
- Official documentation: MCP (spec version `2026-07-28`), A2A Protocol, LangGraph/LangChain docs, Amazon Bedrock AgentCore, Azure AI Foundry, OWASP GenAI project
- Current GitHub/org status for MCP, Langfuse, agent frameworks
- Engineering and hiring analyses from 2026 (treated as **MARKET OBSERVATION**, never as single-source truth)

Where sources disagree, the guide says so.

---

## Start here

Open `01-job-market-analysis.md`, then immediately `02-master-skill-map.md`.
