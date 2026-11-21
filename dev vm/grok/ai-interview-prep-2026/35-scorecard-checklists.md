# 35 — Scorecard, Role Checklists, Weakness Detection

**What this chapter is for:** to replace “I feel ready” with evidence.

Score after a timed mock (Chapter 29), not after reading. Reading inflates scores by 15–25 points.

---

## 1. Score /100

| Dimension | Max | What “full points” means |
| --- | --- | --- |
| Programming | 10 | Python that parses bad input, retries, tests; you can narrate while coding |
| APIs / backend | 10 | Auth, pagination, idempotency, timeouts, streaming, error contracts |
| LLMs | 10 | Tokens, sampling, context limits, serving knobs, cost; not paper-derivation |
| RAG | 10 | Hybrid, chunking, ACL, citations, eval metrics, failure modes |
| Agents | 10 | Tools, state, limits, workflow-vs-agent, HITL, trajectory eval |
| Cloud / DevOps | 10 | One cloud’s identity + networking + deploy; Docker; basic K8s debug |
| System design | 10 | Requirements → v0 → eval → failure → cost; you can defend it |
| AI Security | 5 | Injection, agency, tenancy, output handling; MCP if agentic |
| LLMOps | 5 | Traces, versions, golden set, regression gate, rollback, $/task |
| Projects | 10 | Your story, your decisions, numbers, incident, honest scope |
| Communication | 5 | Structure, time-box, interruptible, no ramble |
| Behavioral | 5 | Four STAR stories; conflict and failure included |
| **Total** | **100** | |

Security and LLMOps are 5 not because they are optional — they leak into every senior loop — but because junior/mid loops still overweight building. If you are targeting Security / LLM / platform senior, treat those 5s as must-get.

### How to convert a mock into numbers

For the 10-point dimensions:

| Score | Meaning | Evidence required |
| --- | --- | --- |
| 0–2 | Cannot answer or factually wrong | You froze or invented |
| 3–4 | Definition only, no choices | Blog shape |
| 5–6 | Can implement a happy path with one trade-off | Lab project or clear explanation |
| 7–8 | Production-shaped: failure, metric, alternative | You cited a number or a real incident |
| 9–10 | Defend under pressure; teach it; know when not to | Survived Chapter 30 on this topic |

For the 5-point dimensions: 0–1 fail, 2–3 partial, 4 strong, 5 excellent with evidence.

Use half-points only if you must. Prefer integers. Inflation is the enemy.

---

## 2. Bands (what the number means)

| Total | Band | Translation | Action |
| --- | --- | --- | --- |
| **< 50** | Not ready | You will fail a real loop on fundamentals or honesty | 2–4 weeks on the lowest two 10-point dimensions. Do not spam applications for this title. |
| **50–65** | Developing | Recruiter screens maybe; technical loop no | Daily spoken drill + one project with evals. Re-mock in 10 days. |
| **65–75** | Interview capable | Can pass some applied loops if the JD matches your spikes | Book loops for *matching* roles. Remediate security/evals if those are the holes. |
| **75–85** | Strong | Competitive for mid applied roles; senior still risky | Pressure-mode the weak dimension. Tighten project numbers. |
| **85–92** | Very strong | Senior-capable if projects and design hold | Calibrate level with the recruiter. Do not overclaim architect. |
| **92+** | Highly prepared | Ready to be picky | Still freeze new topics 24h before. Sleep. |

**Do not average two roles.** A 88 GenAI / 55 Agentic is “strong GenAI,” not “92 if I squint.”

**Do not add points for effort.** Hours studied are not evidence.

---

## 3. How to self-score honestly

You may only award a point if you can point to **one of**:

1. A timestamped mock recording where you said it
2. A repo artifact (eval JSON, trace screenshot, Dockerfile, test)
3. A production incident or metric you personally touched
4. A written design you can redraw from memory in 3 minutes

Vibes that do **not** count:

- “I read the LangGraph docs”
- “I watched a 2-hour video on RAG”
- “I would definitely add evals if I had time”
- “My team did it; I was around”

### Anti-inflation rules

1. If you have not spoken the answer out loud, cap the dimension at 4/10 (or 2/5).
2. If you cannot name a metric, cap RAG / Agents / LLMOps at 6 and 3 respectively.
3. If your project is a tutorial clone, cap Projects at 5.
4. If you have never drawn ACL on the retrieval path, cap RAG at 6 and Security at 2.
5. If you would not let a customer-support agent refund $20 without HITL, good — if you *would*, cap Agents at 5 and Security at 2.
6. After scoring, subtract 3 from the total if you peeked at model answers during the mock.
7. Have a friend or another candidate score the recording. If they are 8+ points lower, theirs is closer to a panel.

### Scoring worksheet (copy)

```
Date:
Role targeted:
Mock used (ch 29 mode):
Peeked? yes/no

Programming        /10   evidence:
APIs/backend       /10   evidence:
LLMs               /10   evidence:
RAG                /10   evidence:
Agents             /10   evidence:
Cloud/DevOps       /10   evidence:
System design      /10   evidence:
AI Security        /5    evidence:
LLMOps             /5    evidence:
Projects           /10   evidence:
Communication      /5    evidence:
Behavioral         /5    evidence:
TOTAL              /100  band:

Lowest two dimensions:
Remediation this week (specific):
```

Run this every 7–10 days during prep. Plot the total. If it does not move, you are consuming content, not practicing.

---

## 4. Role-specific final checklists

A role is “green” only if every box is true **with evidence**. Use these the week of the loop.

### 4.1 GenAI Engineer

Must be true:

- [ ] I can design hybrid RAG with rerank and citations on a whiteboard
- [ ] I can explain chunking by document type with one failure (split tables)
- [ ] I can define recall@k, faithfulness, and a ship bar
- [ ] I can debug “sounds right but wrong” vs “can’t find the doc”
- [ ] I treat retrieved text as untrusted
- [ ] I can discuss cost (cache, routing, max tokens) with numbers
- [ ] I know when *not* to use RAG (SQL lookup, tiny corpus, a transaction)
- [ ] I have one project story with a quality metric
- [ ] Python: chunker / retry / JSON parse in a coding round
- [ ] I will not propose multi-agent as the first architecture

Disqualifiers: no eval plan; “just use a 1M context window”; cannot explain embeddings vs BM25.

### 4.2 Agentic AI Engineer

Must be true:

- [ ] I can say when a workflow beats an agent, with an example
- [ ] I can design a tool gateway: allowlist, schema, authz, timeout
- [ ] Write tools are HITL or I can justify the exception with caps + audit
- [ ] State lives outside the prompt; retries are idempotent
- [ ] Hard step cap, budget cap, no dynamic untrusted tools
- [ ] I evaluate trajectories, not just final English
- [ ] I can debug a looping agent from traces
- [ ] MCP: host/client/server, and I will not skip the gateway
- [ ] I can describe excessive agency in OWASP terms
- [ ] I have a story where the model skipped a required tool — and the fix

Disqualifiers: “the LLM will figure out the tools”; refund/delete/email with no gate; multi-agent v0 for a linear process.

### 4.3 LLM Engineer

Must be true:

- [ ] Prefill vs decode, KV cache, why long context gets expensive
- [ ] Batching vs latency; I can reason about TTFT and TPS
- [ ] Quantization: why, quality risk, how I would eval a drop
- [ ] LoRA vs RAG vs prompt — I pick with data-change and citation needs
- [ ] Structured output / constrained decoding limits
- [ ] Serving stack awareness (vLLM or equivalent ideas): paged attention at a conceptual level
- [ ] Eval harness: versioned sets, regression on vendor model bumps
- [ ] Cost per 1M tokens in and out; cache hits
- [ ] I can write Python over tensors/arrays or tokenizer-ish problems if the loop is lab-like
- [ ] Failure: OOM, hot spots, noisy neighbors on GPU

Disqualifiers: only chat-API experience with no serving vocabulary; fine-tune as the answer to every quality issue.

### 4.4 AIOps Engineer

Must be true:

- [ ] I correlate with topology and change, not just embedding similarity
- [ ] LLM drafts RCA with **evidence links**; humans or policy gate actions
- [ ] I will not auto-`kubectl apply` from a guessed cause
- [ ] I can design noise reduction that reports the false-negative risk
- [ ] Runbooks as tools: allowlist, dry-run, blast-radius cap
- [ ] Incident ticket text is untrusted (injection)
- [ ] Metrics: pages/hour, MTTD/MTTR, RCA agreement, auto-fix rollback rate
- [ ] I can walk a “CPU up on 40 services” investigation in order
- [ ] Integration: tickets (ServiceNow), chat, on-call
- [ ] I know when rules beat LLMs (known pages)

Disqualifiers: “k-means on alerts” as the whole design; unbounded self-healing; no mention of change events.

### 4.5 Cloud AI Engineer

Must be true:

- [ ] I pick Bedrock / Foundry / Vertex by data gravity and identity
- [ ] Private networking to the model API; no PII on the public internet as the default
- [ ] IAM/Entra least privilege for invoke, retrieve, logs
- [ ] Managed RAG (KB / AI Search / Vertex Search) vs DIY — I can trade off
- [ ] Guardrails / Content Safety are extra controls, not the architecture
- [ ] Cost: on-demand vs provisioned, alarms, budgets, routing
- [ ] Observability in-account
- [ ] Secrets in a manager; rotation; no keys in images
- [ ] I can debug a VPC endpoint / 403 / quota issue in order
- [ ] One IaC or console story that is real

Disqualifiers: model-leaderboard as the cloud choice; access keys in Lambda env as the end state; cannot explain IAM vs resource policy.

### 4.6 Intelligent Automation Engineer

Must be true:

- [ ] I map a business process before I pick an LLM
- [ ] System of record stays the SoR; the bot does not become a second ledger
- [ ] Classification / extraction / HITL queue are first-class
- [ ] Idempotent writes; compensating actions
- [ ] Exception paths > happy path in the design
- [ ] I can talk RPA + LLM without pretending RPA is an agent platform
- [ ] Eval on document types and exception rate, not demos
- [ ] Security: PII in docs, prompt injection in invoices/emails
- [ ] Change management with ops users
- [ ] A story with hours-saved or STP (straight-through processing) rate — honest

Disqualifiers: “GPT replaces the workflow engine”; no HITL on money/customer emails; cannot name the system of record.

### 4.7 AI Security Engineer

Must be true:

- [ ] OWASP LLM Top 10 2026 in my own words, especially injection, disclosure, excessive agency
- [ ] Direct vs indirect vs multimodal injection with examples
- [ ] Tool/MCP poisoning and shadow servers
- [ ] ACL in retrieval; vector residual leaks as a concept
- [ ] Output handling (XSS, markdown, code execution)
- [ ] Unbounded consumption as an availability/cost attack
- [ ] I can design a red-team set and a metric (ASR) plus “did the gateway hold”
- [ ] Identity: user principal on every tool call
- [ ] Logging vs privacy
- [ ] I will not run live attacks on their prod from the interview

Disqualifiers: “the system prompt forbids it”; no mention of indirect injection; treating jailbreak-as-party-trick as the job.

### 4.8 Forward Deployed Engineer (FDE)

Must be true:

- [ ] I start with stakeholders, constraints, and success metric — not a stack
- [ ] I can scope a v0 that a named user will touch this month
- [ ] Messy data plan: inventory, quality, owners, “what we will not ingest”
- [ ] I can say no to an agent when the data/process is not ready
- [ ] Compliance questions I will ask (residency, PII, retention, audit)
- [ ] I can run a room with mixed seniority without jargon-dumping
- [ ] I have a story of ambiguity or a blocked customer
- [ ] Technical enough to write the first integration, not only slides
- [ ] Eval with no labeled data: shadow, HITL, small golden set from SMEs
- [ ] Timeline honesty: 2-week demo vs production

Disqualifiers: architecture first; contempt for non-engineers; promising a 2-week production agent on SharePoint.

### 4.9 AI Deployment Engineer

Must be true:

- [ ] I can containerize a model or app: multi-stage, non-root, pinned digest
- [ ] K8s: probes, resources, rollouts, pending/OOM/CrashLoop debug order
- [ ] GPU: node selectors, drivers, utilization vs queue
- [ ] Rollout: canary, rollback, PDB
- [ ] Config/secrets: not baked into the image
- [ ] Health endpoints that do not invoke the LLM
- [ ] Autoscaling on a signal that matters (queue, tokens), not only CPU
- [ ] I can talk through an image-too-large / pull-timeout incident
- [ ] Observability: logs, metrics, traces hooked
- [ ] I coordinate with the app owner on versions (model, prompt, index)

Disqualifiers: `latest` tags as a lifestyle; one replica of a write consumer with no lock; “K8s will just scale the GPU.”

### 4.10 AI Solutions Engineer

Must be true:

- [ ] Discovery questions before a demo
- [ ] I can demo the *customer’s* workflow, not a feature dump
- [ ] Objection handling: hallucinations, data residency, cost, “we could build it”
- [ ] POC success criteria written down (metric, user, timebox)
- [ ] I can translate for a VP and for an engineer in the same hour
- [ ] Security questionnaire: I know when to pull an SE/SA
- [ ] Competitive: I don’t trash; I map requirements
- [ ] I know the product’s limits and say them early
- [ ] A story of a failed or at-risk POC and what I changed
- [ ] Light architecture is correct (RAG vs agent, identity)

Disqualifiers: lying about roadmap; demo of everything; no success metric; cannot say when *not* to buy.

### 4.11 AI Solutions Architect

Must be true:

- [ ] Reference architecture: identity, data plane, control plane, ops
- [ ] Build vs buy with TCO, not logos
- [ ] Governance: model catalog, prompt owners, eval owners, kill switch
- [ ] Multi-region / residency / tenancy
- [ ] Cost model: tokens, search, GPU, humans in the loop
- [ ] Integration map: SSO, DLP, SIEM, ticketing, data stores
- [ ] Operating model: who is on-call, RACI, knowledge freshness SLO
- [ ] Residual risk written, not “we’ll add security later”
- [ ] v0 vs 18-month roadmap without boiling the ocean
- [ ] I can defend “no multi-agent, no fine-tune” to an excited CIO

Disqualifiers: tool soup; no operating model; ignoring identity; architect-from-a-blog with no cost.

### 4.12 Forward Deployed AI Engineer (FDAIE)

Must be true — FDE *plus* you will be scored as an AI builder on-site:

- [ ] Everything in 4.8 (FDE)
- [ ] I can ship a v0 RAG or workflow-agent on their cloud in days, not months
- [ ] I can stand up evals with SMEs who have no labels
- [ ] I can debug retrieval vs generation in their messy corpus
- [ ] I can implement HITL on the customer’s actual write systems
- [ ] I understand their identity stack enough to not punch a hole in ACL
- [ ] I can explain trade-offs to a customer CTO without hiding behind vendors
- [ ] I have a story of production-shaped AI (traces, eval, failure), even if not FAANG-scale
- [ ] I will not install a random MCP server on a bank laptop
- [ ] I know when to escalate to core eng vs when to hack a safe adapter

Disqualifiers: FDE softness without AI depth, or AI depth without customer judgment. This title is the AND.

---

## 5. Weakness detection template

Fill this the same day as a mock. Be rude to yourself on paper; be professional in the room.

### 5.1 Snapshot

```
Date:
Role:
Total /100:
Band:
```

### 5.2 Top 5 weaknesses (ranked by *interview damage*, not by shame)

Damage = (how likely this JD probes it) × (how badly you fail it).

| Rank | Weakness (specific) | Dimension | Evidence from the mock | Damage 1–5 |
| --- | --- | --- | --- | --- |
| 1 | e.g. “Could not define faithfulness vs relevancy” | RAG | Q4 ramble | 5 |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

Not allowed as a weakness: “I need more confidence.” Translate to a behavior: “I filled silence with extra architecture.”

### 5.3 Strengths (keep using; do not abandon)

```
1.
2.
3.
```

In the room, lead with these when you have a choice of depth (“I can go into evals or into GPU — evals is where I’m strongest and it’s the risk for this design”).

### 5.4 High-risk topics for *this* JD

Copy verbs from the JD. Mark red if your score on that dimension is <7 (or <4 on a 5-point).

```
JD verb → topic → my score → red/yellow/green
```

### 5.5 Missing fundamentals (the ones that collapse senior talk)

Tick any that were true in the last mock:

- [ ] Could not explain tokens vs words
- [ ] Dense vs BM25 confused
- [ ] MCP vs function calling vs RAG confused
- [ ] Authn vs authz confused
- [ ] Retry without idempotency
- [ ] POST vs GET side effects
- [ ] Index vs filter vs rerank order
- [ ] Container vs pod vs node
- [ ] Prompt injection only as “user types ignore previous”
- [ ] Eval = “we’ll have users thumbs-up”

Each tick is a 2-day drill, not a course.

### 5.6 Weak project explanations

```
Project:
Where it died: (numbers / my role / failure / eval / security / 10×)
Rewrite of the 60-second version:
```

If you cannot rewrite today, that project is not interview-ready. Use another or go generate a real metric.

### 5.7 Weak behavioral

```
Missing story type: conflict / failure / ambiguity / said-no / customer
The story I tried:
What the interviewer would write: 
Fix: (add verb, add number, cut villains, cut speech)
```

### 5.8 Targeted remediation (not “study more”)

Pick **two** weaknesses. Write a 7-day plan with artifacts.

| Weakness | Artifact I will create | Drill | Done when |
| --- | --- | --- | --- |
| Faithfulness vs relevancy | 20-row eval sheet on my corpus | Speak the definitions daily; run the metric once | I can compute both and explain a disagreement |
| No HITL on writes | Sequence diagram + fake approval API | Pressure-mode refund dialogue | Strong-candidate version without peeking |
| Rambling | Record 10 answers, hard 90s cap | Chapter 31, timer | 8/10 stop cleanly |
| Project has no number | Measure p95 or eval score this week | Re-record story | A number appears in sentence 3 |

Forbidden remediation:

- “Watch 10 videos on agents”
- “Learn a new framework”
- “Rewrite resume with stronger adjectives”
- “Do 50 LeetCode unless the JD is a frontier lab”

### 5.9 Re-test

```
Re-mock date:
Expected dimension deltas:
Actual:
Keep / drop this role target:
```

If two re-mocks do not move a dimension, change the drill. Reading the same chapter harder is not a drill.

---

## 6. Pre-on-site one-pager

Fill this the morning of:

```
Role:
Band last mock:
Two things I will not mess up: (e.g. evals, HITL)
One thing I will admit if asked: (e.g. no Foundry hands-on)
First-sentence intro:
Project I will lead with:
Question I will ask them:
Contract: no bluff, stop when landed, docs are hostile.
```

That is the whole game. The rest of the handbook exists to make those lines true.

Next loop: [mocks/29-mock-interviews.md](mocks/29-mock-interviews.md). Do not peek.
