# 2026 AI Interview Preparation Handbook

**A production-grade interview system for GenAI, Agentic AI, LLM, Cloud AI, AIOps, Security, FDE, and Solutions roles**

Version: 2026.09  
Research window: January–September 2026  
Audience: engineers entering or moving across modern AI production roles  
Objective: walk into an interview, recognize what is being tested, structure the answer, defend projects, solve scenarios, and handle follow-ups.

This is not a list of questions. It is a performance system.

---

## How this book is different

Most AI interview prep still trains you like a 2022 ML candidate: attention math, LeetCode, and a shallow RAG definition.

That is not the 2026 interview.

Across candidate reports from frontier labs, applied AI startups, consulting firms, and enterprise platform teams, the loop now tests:

| What interviewers actually test | What they are not testing |
| --- | --- |
| Can you ship a measurable RAG / agent system? | Can you derive attention from scratch? |
| Can you evaluate quality before users do? | Can you recite framework APIs? |
| Can you debug retrieval vs generation vs tools? | Did you finish a tutorial? |
| Can you design for ACL, cost, latency, and failure? | Can you name 12 vector databases? |
| Can you decide when *not* to use an agent? | Can you draw a multi-agent diagram? |
| Can you explain *your* contribution with numbers? | Can you describe a team project in the abstract? |

**The single biggest 2026 differentiator:** evaluation. Candidates who can build a pipeline but cannot say how they would know it works get filtered. Candidates who lead with measurement, failure modes, and trade-offs get offers.

---

## Target roles

1. GenAI Engineer
2. Agentic AI Engineer
3. LLM Engineer
4. AIOps Engineer
5. Cloud AI Engineer
6. Intelligent Automation Engineer
7. AI Security Engineer
8. Forward Deployed Engineer
9. Forward Deployed AI Engineer
10. AI Deployment Engineer
11. AI Solutions Engineer
12. AI Solutions Architect

Related titles you should still apply to: AI Engineer, RAG Engineer, LLMOps Engineer, AgentOps Engineer, Azure AI Foundry Engineer, Bedrock Engineer, Vertex / Gemini Agent Platform Engineer, Copilot Engineer, AI Platform Engineer.

---

## How to use this handbook

1. Read **01 Market Analysis** so you understand why the curriculum is shaped this way.
2. Study **02 Interview Process by Role**. Do not prepare one generic loop.
3. Use **03 Skill Matrix** to pick a primary role. Do not try to be all 12 at once.
4. Internalize **05 Answer Frameworks**. These are how you generate answers live, not scripts you memorize.
5. Drill the topic guides for your role’s **core (5)** and **very important (4)** cells.
6. Practice system design, troubleshooting, and project defense out loud.
7. Run mock interviews in **29**. Do not look at the model answer first.
8. Score yourself with **35**. Remediate the weakest two dimensions before the next loop.

### Answer depth by seniority

| Level | Interviewer wants | Typical answer length | Fail mode |
| --- | --- | --- | --- |
| Junior / career switcher | Correct concept + honest boundary | 30–60 seconds, then examples | Overclaiming production experience |
| Mid-level | Implementation choices you have made | 90–180 seconds + a war story | Tutorial-only answers |
| Senior | Trade-offs, failure modes, evals, cost | 2–4 minutes, then defend | Architecture without numbers |
| Architect / FDE | System-wide consequences, governance, customers | Structured 5–8 minute design | Jumping to tools before requirements |

---

## Book map

| # | File | What it trains |
| --- | --- | --- |
| 00 | [00-how-to-use.md](00-how-to-use.md) | Study method, 4-week / 8-week plans |
| 01 | [01-2026-market-analysis.md](01-2026-market-analysis.md) | What companies hire for in 2026 |
| 02 | [02-interview-process-by-role.md](02-interview-process-by-role.md) | Round-by-round loops for all 12 roles |
| 03 | [03-skill-matrix.md](03-skill-matrix.md) | Role × topic importance 0–5 |
| 04 | [04-topic-probability-ranking.md](04-topic-probability-ranking.md) | What actually gets asked, ranked |
| 05 | [05-answer-frameworks.md](05-answer-frameworks.md) | Reusable structures for every question type |
| 06 | [guides/06-python.md](guides/06-python.md) | Python for AI engineers, not competitive programming |
| 07 | [guides/07-sql.md](guides/07-sql.md) | SQL that shows up in AI interviews |
| 08 | [guides/08-apis.md](guides/08-apis.md) | REST, auth, streaming, retries, gateways |
| 09 | [guides/09-llm.md](guides/09-llm.md) | Transformers, tokens, sampling, cost, serving |
| 10 | [guides/10-rag.md](guides/10-rag.md) | The highest-probability topic in 2026 |
| 11 | [guides/11-agentic-ai.md](guides/11-agentic-ai.md) | Agents, tools, loops, when not to use them |
| 12 | [guides/12-mcp.md](guides/12-mcp.md) | Model Context Protocol, enterprise MCP |
| 13 | [guides/13-multi-agent.md](guides/13-multi-agent.md) | Supervisor, specialists, overengineering |
| 14 | [guides/14-vector-databases.md](guides/14-vector-databases.md) | ANN, hybrid search, vendor trade-offs |
| 15 | [guides/15-cloud-ai.md](guides/15-cloud-ai.md) | Bedrock, Azure AI Foundry, Vertex / Gemini |
| 16 | [guides/16-docker-kubernetes.md](guides/16-docker-kubernetes.md) | Containers, GPU workloads, troubleshooting |
| 17 | [guides/17-llmops.md](guides/17-llmops.md) | Evals, tracing, cost, regression, drift |
| 18 | [guides/18-aiops.md](guides/18-aiops.md) | Correlation, RCA, safe remediation |
| 19 | [guides/19-ai-security.md](guides/19-ai-security.md) | OWASP LLM 2026, MCP Top 10, agents |
| 20 | [design/20-system-design.md](design/20-system-design.md) | How to run an AI system design interview |
| 21 | [design/21-architecture-problems.md](design/21-architecture-problems.md) | 13 full design problems with ideal answers |
| 22 | [banks/22-troubleshooting.md](banks/22-troubleshooting.md) | Production incidents and RCA method |
| 23 | [career/23-project-defense.md](career/23-project-defense.md) | How to explain and defend projects |
| 24 | [career/24-behavioral.md](career/24-behavioral.md) | STAR stories that survive senior panels |
| 25 | [career/25-tell-me-about-yourself.md](career/25-tell-me-about-yourself.md) | Role-specific 30/60/90-second intros |
| 26 | [career/26-career-transition.md](career/26-career-transition.md) | Moving into AI without lying |
| 27 | [career/27-hr-salary.md](career/27-hr-salary.md) | Recruiter screen, offers, negotiation |
| 28 | [career/28-psychology-rejections-tactics.md](career/28-psychology-rejections-tactics.md) | Interviewer psychology, fail modes, tactics |
| 29 | [mocks/29-mock-interviews.md](mocks/29-mock-interviews.md) | Role-specific mocks. Do not peek. |
| 30 | [mocks/30-pressure-mode.md](mocks/30-pressure-mode.md) | Adversarial senior defense |
| 31 | [mocks/31-rapid-fire.md](mocks/31-rapid-fire.md) | 100 questions, 30–60 seconds each |
| 32 | [cheatsheets/32-cheat-sheets.md](cheatsheets/32-cheat-sheets.md) | Compact revision sheets |
| 33 | [cheatsheets/33-24h-60min.md](cheatsheets/33-24h-60min.md) | Final day and final hour |
| 34 | [career/34-questions-to-ask.md](career/34-questions-to-ask.md) | High-signal questions for the interviewer |
| 35 | [35-scorecard-checklists.md](35-scorecard-checklists.md) | Readiness score, weakness detection, role checklists |

---

## Research basis (so you can trust the map)

This handbook was built from:

- ~889 AI Engineer job descriptions analyzed in January 2026 (AI Shipping Labs): 95.6% production-focused; Python in 82.5% of roles; RAG in 35.9%; agents in 14.4% and rising; fine-tuning in only 8.5%.
- Candidate-reported loops through May–September 2026 (frontier labs, applied AI startups, enterprise/consulting).
- Current role splits: GenAI vs Agentic AI hiring (Uplers, Sept 2026); FDE loops (Palantir / OpenAI / Anthropic, 2026); LLM engineer serving-heavy loops.
- Official / community security baselines: OWASP GenAI LLM Top 10 **2026** (published August 2026); OWASP MCP Top 10 (2025 list, next release targeted October 2026).
- Cloud platforms as of 2026: Amazon Bedrock, Azure AI Foundry / Microsoft Foundry, Vertex AI evolved toward Gemini Enterprise Agent Platform (Cloud Next 2026).
- Agent frameworks actually named in 2026 JDs and interviews: LangGraph, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework / Semantic Kernel, PydanticAI, CrewAI, Bedrock Agents / AgentCore.
- Protocols: MCP (open standard; Anthropic donated to the Linux Foundation in late 2025) and A2A for agent-to-agent communication.

Where sources disagree, the handbook says so and tells you how to answer anyway.

---

## Non-negotiable rules while you study

1. **Do not memorize paragraphs.** Learn concept → logic → structure → keywords → example → trade-off. Generate the answer in the room.
2. **Never invent production experience.** Position transferable work honestly. Interviewers catch overclaiming in one follow-up.
3. **Lead with evaluation.** If you design it, say how you would know it works.
4. **Name a failure mode in every architecture answer.** Happy-path designs fail senior loops.
5. **Prefer workflows over agents unless the steps are unknown.** This is one of the highest-signal 2026 opinions you can hold.

Start at [00-how-to-use.md](00-how-to-use.md), then [01-2026-market-analysis.md](01-2026-market-analysis.md).
