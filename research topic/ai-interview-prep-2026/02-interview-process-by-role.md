# 02 — Interview Process by Role

**What this chapter is for:** so you stop preparing one generic loop.

A GenAI Engineer loop and a Forward Deployed loop can share RAG, but they score completely different behaviors. Map your calendar to the role you actually applied for. If the recruiter is vague, ask: “Is this closer to applied RAG/product, agent orchestration, platform/serving, customer deployment, or architecture/governance?”

Difficulty below is **relative to a mid-level production software engineer**, not to a research scientist.

---

## Master comparison

| Role | Typical rounds (order varies) | Difficulty | Main evaluation areas | Coding level | Architecture level |
| --- | --- | --- | --- | --- | --- |
| GenAI Engineer | Recruiter → tech screen → Python/practical coding → LLM/RAG round → system design → project deep dive → HM / behavioral | High | RAG, evals, prompts as systems, APIs, production failures | Medium (practical Python) | High (product RAG/agents) |
| Agentic AI Engineer | Recruiter → tech screen → coding (tools/state) → agent design → reliability/security → project → HM | High | Tool calling, state, loops, HITL, MCP, trajectory evals | Medium | High (orchestration) |
| LLM Engineer | Recruiter → internals screen → ML/Python coding → serving/cost → evals → design inference stack | Very high (infra track) | Transformers intuition, KV cache, batching, quantization, LoRA vs RAG | Medium–High | High (serving) |
| AIOps Engineer | Recruiter → observability screen → scenario RCA → automation/safety → platform design → behavioral | High | Correlation, topology, noise, gated remediation, ITSM | Low–Medium | High (ops architecture) |
| Cloud AI Engineer | Recruiter → cloud screen → IaC/K8s → Bedrock/Foundry/Vertex design → security/IAM → cost | High | IAM, networking, managed AI services, GPUs, landing zones | Medium (scripts/YAML) | High |
| Intelligent Automation Engineer | Recruiter → process discovery → workflow vs agent → HITL → integration (ITSM/CRM) → risk | Medium–High | BPM, connectors, human approval, evaluation of task completion | Low–Medium | Medium–High |
| AI Security Engineer | Recruiter → AppSec+AI screen → threat model → red-team scenario → design review → behavioral | Very high | OWASP LLM 2026, MCP, agents, RAG isolation, detections | Medium (exploits conceptually, tests) | High (controls) |
| Forward Deployed Engineer | Recruiter → HM → coding → system/data design → **deployment scenario** → customer behavioral | Very high | Ambiguity, scoping, messy data, stakeholders, v0 | Medium (practical) | High (customer-shaped) |
| Forward Deployed AI Engineer | Same as FDE + AI evals/safety baked into scenario | Very high | FDE skills + RAG/agents/evals/HITL | Medium | High |
| AI Deployment Engineer | Recruiter → CI/CD → containers/K8s → model serving → rollback/canary → on-call | Medium–High | Ship, observe, roll back, GPU/API ops | Medium | Medium |
| AI Solutions Engineer | Recruiter → product/tech screen → discovery role-play → light architecture → objection handling | Medium–High | Customer workflow, fit, demo judgment, translations | Low–Medium | Medium |
| AI Solutions Architect | Recruiter → architecture screen → enterprise design → governance/cost/security → stakeholder | Very high | End-to-end, integration, operating model, risk | Low | Very high |

---

## 1. GenAI Engineer

### Typical stages

1. **Recruiter / HR (20–30 min)** — role fit, location, comp, “what have you shipped?”
2. **Technical screening (45–60 min)** — RAG definition to mid-depth, Python, resume probe.
3. **Python / practical coding (45–60 min)** — JSON, chunking, retries, FastAPI; labs may add tokenizer/batching.
4. **LLM / RAG technical (60 min)** — full pipeline with real choices, hybrid search, evals.
5. **System design (45–60 min)** — “enterprise knowledge assistant” is the modal prompt.
6. **Project deep dive (45–60 min)** — they attack *your* repo/resume.
7. **Production troubleshooting (sometimes merged into design)** — latency, bad answers, cost spike.
8. **Hiring manager** — judgment, collaboration, when not to use an LLM.
9. **Behavioral / culture**

### What they are testing at each stage

| Stage | Hidden test |
| --- | --- |
| Recruiter | Can you describe a shipped system in one minute with a metric? |
| RAG round | Do you start with data, ACL, and evals, or with LangChain? |
| Coding | Would I trust this in a service, not a notebook? |
| Design | Identity-aware retrieval, citations, failure modes, cost |
| Project | Did *you* make the hard choices? |

### High-probability questions

- Design RAG for customer support / policies / tickets.
- Retrieval is right, answer is wrong — debug.
- RAG vs fine-tune vs prompt.
- How do you know it is ready to ship?
- How do you stop hallucinations (they want grounding + verify, not “better prompt” only)?

**Prep emphasis:** Chapter 10 RAG, 09 LLM, 17 LLMOps, 20–21 design, 23 project defense.

---

## 2. Agentic AI Engineer

### Typical stages

1. Recruiter
2. Technical screen — agent vs workflow, tool calling
3. Coding — parse tool calls, validate schema, retries, state machine
4. Agent system design — planner/executor or graph, budgets, HITL
5. Reliability & security — loops, prompt injection via tool output, excessive agency
6. Project deep dive — a real multi-step system, not a CrewAI demo
7. HM / behavioral — production cost stories

### Hidden tests

- Do you reach for multi-agent by default? (negative signal)
- Can you recover mid-task when a tool 500s?
- Do write actions require policy + approval?
- Can you eval trajectories, not just final text?

**Prep emphasis:** Chapters 11–13, 19 security, 17 evals, 22 troubleshooting.

---

## 3. LLM Engineer

### Typical stages

1. Recruiter
2. LLM internals screen — attention, tokens, sampling, RoPE/GQA at intuition+mechanism depth
3. Coding — numpy attention or batching variable-length sequences, or serving-adjacent Python
4. Inference / serving — KV cache memory math, continuous batching, quantization
5. Fine-tune vs RAG vs prompt — they want a decision tree, not a preference
6. Evals and guardrails
7. Design an inference gateway or RAG+serving hybrid
8. HM

Frontier-adjacent teams go deeper on internals. Product LLM engineers go deeper on cost and evals.

**Prep emphasis:** Chapter 09, 17, serving sections, light 10.

---

## 4. AIOps Engineer

### Typical stages

1. Recruiter — stack (Datadog, Dynatrace, Splunk, Prometheus, ServiceNow)
2. Observability fundamentals — metrics/logs/traces/profiles, cardinality
3. Scenario RCA — “p99 5x after deploy”
4. Correlation / noise — 10k alerts, topology
5. Automation safety — auto-remediate restart vs rollback vs never
6. Design an AIOps / RCA copilot (2026 flavor: LLM drafts, humans approve)
7. Behavioral — on-call trust, a wrong correlation

**Prep emphasis:** Chapter 18, 17 (telemetry), 16 (K8s symptoms), 22.

---

## 5. Cloud AI Engineer

### Typical stages

1. Recruiter — which cloud is real for this team
2. Cloud primitives — IAM, VPC, secrets, networking
3. Managed AI services — Bedrock / Foundry / Vertex deep dive matching the JD
4. Containers and orchestration — Dockerfile + a broken deployment
5. Architecture — private RAG, no public internet to model if required
6. Cost and quotas — 429s, PTU/provisioned throughput, logging costs
7. Security review — keys in prompts, training-data opt-out, residency

**Prep emphasis:** Chapter 15, 16, 19 (supply chain, secrets), 20.

---

## 6. Intelligent Automation Engineer

### Typical stages

1. Recruiter — RPA/BPM/ITSM background plus AI
2. Process intake — how you discover a workflow, exceptions, SLAs
3. Workflow vs agent — they will punish agent-everywhere
4. Integration — ServiceNow, Salesforce, SAP, email, identity
5. HITL and audit — who is accountable when the bot is wrong
6. Scenario — invoice / ticket / KYC automation with failure paths
7. Stakeholder communication

**Prep emphasis:** Chapters 11 (when not to agent), 18, 23, 24.

---

## 7. AI Security Engineer

### Typical stages

1. Recruiter — AppSec vs MLSec vs product security blend
2. Web/AppSec baseline — still required (authz, SSRF, injection)
3. OWASP LLM Top 10 2026 walkthrough with *mitigations you have implemented*
4. Threat model a RAG+agent product (60 min)
5. Red-team scenario — indirect injection via a wiki page; MCP tool poisoning
6. Detection/response — what you log, what you block, what you page
7. Design review with an architect
8. Behavioral — pushing back on a ship date

**Prep emphasis:** Chapter 19, 12 MCP, 10 RAG ACL, 21 secure assistant / security monitoring designs.

---

## 8. Forward Deployed Engineer

### Typical stages (Palantir / OpenAI / Anthropic / Salesforce-like, 2026)

1. Recruiter (30)
2. Hiring manager (45) — motivation for customer-facing engineering
3. Coding (45–60) — messy data, APIs, tests; not puzzle-hard
4. System / data design — pipelines, search, sometimes RAG
5. **Open-ended deployment scenario (60–90)** — the filter
6. Behavioral / customer (45–60)
7. Sometimes a learning-on-the-fly code reading round (Palantir)

### Deployment scenario scoring

They watch whether you:

1. Scope success criteria before tools
2. Name stakeholders including non-engineers
3. Surface compliance / residency / identity
4. Plan discovery in week 1–2
5. Offer 2–3 options with trade-offs
6. Define v0 with HITL
7. Name failure modes and unwind
8. Give a believable timeline

**#1 fail:** solutioning in minute two.

**Prep emphasis:** Chapters 20–21, 23, 24, 25 (FDE intro), 08 APIs, 06 Python.

---

## 9. Forward Deployed AI Engineer

Same skeleton as FDE, with these extra probes inside the scenario:

- How do you eval quality before the customer trusts it?
- What is the blast radius if the agent emails a patient / trades / deletes?
- How do you handle hallucination in a regulated workflow?
- What does rollback mean for a prompt + index + tool policy?

Prepare FDE *plus* RAG/agents/security/evals.

---

## 10. AI Deployment Engineer (GenAI Ops)

### Typical stages

1. Recruiter
2. CI/CD and environments
3. Docker/K8s debugging
4. Model/API rollout — pinning versions, canary, shadow
5. Observability and cost dashboards
6. Incident — pods OOM, GPU not scheduled, 429 storm
7. HM — on-call maturity

**Prep emphasis:** 16, 15, 17, 22.

---

## 11. AI Solutions Engineer

### Typical stages

1. Recruiter — travel, quota, technical depth
2. Product + light technical screen
3. Discovery role-play — a fake customer with a vague AI ask
4. Architecture on a whiteboard at “good enough” depth
5. Demo / teach-back — explain RAG to a VP and to an engineer
6. Objection handling — security, cost, “we tried a chatbot”
7. Panel / HM

Scoring: do you interview the customer, or pitch features? Do you recommend *not* using the product when it is a bad fit? That is a senior signal.

**Prep emphasis:** 25, 23, 20 (light), 34, 15, 10, 11.

---

## 12. AI Solutions Architect

### Typical stages

1. Recruiter
2. Architecture screen — current estate, integration patterns
3. Full enterprise design (60–90) — multi-tenant RAG or agent platform
4. Governance — EU AI Act-style risk, audit, model inventory, human oversight
5. Cost and operating model — who owns prompts, evals, incidents
6. Security architecture with InfoSec
7. Executive communication — 10-minute narrative
8. Sometimes a written design or ADR take-home

**Prep emphasis:** 20–21, 19, 15, 03 matrix (architect column), 05 frameworks, 23.

---

## How to read a job description and predict the loop

1. Circle the **verbs**: build, deploy, advise, secure, automate, own on-call.
2. Circle the **objects**: RAG, agents, Bedrock, ServiceNow, Foundry, MCP.
3. Circle the **constraints**: HIPAA, VPC, multi-tenant, 200ms, cost.
4. Predict 8 questions from those constraints. Example: “HIPAA” → zero retention, BAAs, PII redaction, no public training, audit logs.
5. Match to the table above. If the JD says “AI Engineer” but lists LangGraph, MCP, tool calling, and HITL, prepare the **Agentic** loop even if the title is GenAI.

Next: [03-skill-matrix.md](03-skill-matrix.md).
