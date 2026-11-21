# 25 — Tell Me About Yourself

**What this chapter is for:** a role-shaped 30 / 60 / 90-second intro you can actually say, built from your facts, not a speech from this book.

This is almost always the first scored answer. It sets which loop they think they are running. A GenAI Engineer who opens with Kubernetes internals gets an infra grilling. An Agentic engineer who opens with “I love prompting” gets a chatbot loop. An FDE who opens with a framework list never reaches the customer scenario.

Do not memorize the templates as paragraphs. Memorize the **shape**, then drop in real facts. If a sentence is not true for you, delete it.

---

## 1. What they are listening for

| Signal | How the intro shows it |
| --- | --- |
| Fit to *this* role | You use that role’s nouns (evals, HITL, MCP, tenancy, on-site) |
| Production honesty | Prototype vs pilot vs production is clear |
| Ownership | One “I owned” |
| Judgment | One constraint or one “I would not” |
| Trajectory | Why you are here now, without trashing anyone |

They are not listening for your childhood, your GPA, or a complete resume recap. Walk backwards from the job you want, not forwards from university.

---

## 2. The only structure you need

**30 seconds — headline**

1. Who you are in role language (one line)
2. The strongest production-shaped proof (one line)
3. Why this conversation (one line)

**60 seconds — headline + evidence**

Add:

4. One project with a number or honest scope
5. One constraint you care about (ACL, cost, HITL, evals)
6. What you want next, in *their* words from the JD

**90 seconds — headline + evidence + judgment**

Add:

7. A failure or trade-off in one sentence
8. A clear boundary (“I have not operated X; I have done Y”)
9. Stop. Invite them: “Happy to go deeper on the assistant or the incident.”

If they already have your resume in hand, do not read it. Narrate the through-line.

### Fill-in skeleton (all roles)

```
I am a [role they are hiring] with a background in [true base: backend / SRE / data / support-eng].
I have [owned / built / deployed] [system type] with [constraint].
The part I am strongest at is [evals / retrieval / agents / cloud landing / customer scoping].
Recently I [one project: users, your slice, number or honest scope].
I am not looking to [anti-goal: unbounded agents / research-only / tutorial collecting].
I want this role because [their constraint], and I can help on [first-90-day shaped work].
```

### Customizing with real facts (mandatory)

Before you copy any template:

1. Write your actual title, years, and domain.
2. Write one project at the level it reached: notebook / internal pilot / production users / production SLO.
3. Write one number you can defend, or delete the number.
4. Write one thing you did not do (Terraform, GPU kernels, people management).
5. Replace every company-generic adjective (“passionate,” “cutting-edge”) with a noun from the JD.

If you are transitioning, read Chapter 26 first. Your intro should lead with **production engineering + one serious AI project**, not with a course list.

---

## 3. Role-specific templates

Each role has 30 / 60 / 90. They are **templates**, not biographies. Bracketed text is yours to fill. EXAMPLE lines show tone; they are not your story.

---

### GenAI Engineer

You are scored on RAG, prompts as systems, evals, grounding, cost/latency. Lead with retrieval quality and measurement, not with “I use LangChain.”

**30s**

> I am a GenAI engineer with a [backend/search/NLP] background. I build production RAG systems — hybrid retrieval, citations, and eval gates — not chat demos. I most recently [owned retrieval + evals on an internal assistant / shipped X]. I want this role because you need [grounded answers on private data], which is the work I already do.

**60s**

> I am a GenAI engineer. Before that I [backend]. For the last [N months/years] I have designed RAG pipelines: chunking, hybrid search, rerank, grounded generation, and a golden set that can block a release. On [project], I owned [slice]. We [recall / faithfulness / latency number, or: internal pilot with N users]. I care about fail-closed behavior when retrieval is empty — I do not let a helpful prompt invent policy. I am here because this team’s JD is [RAG + evals + production], not a fine-tune-first research seat.

**90s**

> I am a GenAI engineer focused on measurable retrieval systems. [Base career, 1 sentence.] On [project] I owned chunking, metadata, and a [N]-question eval set. Dense-only search failed on [IDs / language]; hybrid + rerank moved recall@10 from [a] to [b], and we killed a prompt that hurt faithfulness. Scope honestly: [pilot / production]. I did not own [infra]. I have not operated [100× QPS / multi-region], and I would load-test the ACL-filtered path before claiming that. I want to do this job where evals are a gate, which is how I read your team.

**Customize:** swap in your corpus (code, policies, tickets). If you have no RAG, do not apply this template — use career-transition + the closest real system (search, recommendations, NLP classification).

---

### Agentic AI Engineer

You are scored on tools, state, loops, when *not* to use an agent, HITL, trajectory evals. Lead with control, not with a crew of personas.

**30s**

> I am an agentic AI engineer. I build tool-using systems with hard step limits, durable state, and human approval on writes — and I default to a workflow when the steps are known. I owned [graph / tools / evals] on [copilot]. I want this role because you are putting agents in [production task], which only works if agency is bounded.

**60s**

> I am an agentic AI engineer with a [backend/SRE] base. I design supervisors with typed tools, checkpoints, and task-completion evals, not multi-agent theater. On [project] I owned the graph, the loop detector, and a replay set of [N] tasks. We cut [time-to-draft / steps] and kept unsafe-action rate at 0 by refusing execute without HITL. I have used [LangGraph / Agents SDK / ADK] for state and interrupts; I can do a first agent as a Python loop. I am here to make agents operable: traces, caps, and when not to use them.

**90s**

> I build production agents as state machines, not as chat. [Base, 1 sentence.] On [ops/support/code copilot] I owned [tools + graph]. v0 looped the same search tool; I added cached tool+args, shrunk observations, and a step cap. Task completion on replay went [a] → [b]. We used one supervisor, not a crew, because eval and least privilege were harder with handoffs. Honest boundary: [pilot with N engineers / not unbounded self-healing]. I have not run A2A across vendors in production. I want this team because the JD names [MCP / HITL / AgentCore / Foundry Agent Service], which matches how I already think about tool gateways.

**Customize:** name your actual tools (Jira, metrics, browser, code exec). If your “agent” was a single LLM call with one function, call it a tool-calling app. Do not upgrade it in the intro.

---

### AIOps Engineer

You are scored on correlation, RCA, gated remediation, not on clustering dashboards with k-means. Lead with safe automation.

**30s**

> I am an AIOps engineer from [SRE/on-call]. I work on topology-aware correlation and LLM-drafted RCA with human-gated remediations — not auto-heal by default. I [owned a copilot / correlation rule / incident workflow] that [result]. I want this role because you page humans for [estate], and I know the failure mode of unbounded scripts.

**60s**

> I come from [SRE / platform] on-call and I am moving that craft into AIOps. I care about correlating pages with service topology, drafting RCA from metrics and runbooks, and opening tickets — with execute behind HITL because we have already seen a restart make an outage worse. On [project] I [slice + number: MTTD, time-to-draft, noisy-page reduction]. I use LLMs as drafters, not as operators. Your JD’s [ServiceNow / Prometheus / PagerDuty / AIOps] language is the job I want.

**90s**

> I am an SRE-shaped AIOps engineer. [Years on-call, estate size if true.] I built [copilot/workflow] that reads metrics, logs, and runbooks, then drafts RCA. I owned [graph or pipeline] and insisted execute was feature-flagged off. Time-to-first-draft [X → Y] on a pilot of [N] services. I also still do classical work: [SLOs, runbooks, incident command] — that is transferable and I will not pretend the LLM replaces it. I have not shipped fully autonomous remediation and I would push back if that were week-one scope. I am here to make on-call cheaper without making it scarier.

**Customize:** name monitoring stack you actually used. If you never did on-call, do not use this role template.

---

### Cloud AI Engineer

You are scored on landing models in a real cloud account: identity, network, Bedrock / Foundry / Vertex, GPUs, cost, rollback.

**30s**

> I am a cloud AI engineer. I land foundation-model apps on [AWS/Azure/GCP] with private networking, IAM/Entra, and cost controls — not public API keys on a laptop. I [shipped Knowledge Bases / Azure OpenAI + AI Search / Vertex RAG] for [team]. I want this role because your estate is already [cloud], and the work is operating the platform.

**60s**

> I am a cloud AI engineer with [platform/DevOps] background. I have taken a model from approved endpoint to an app with [VPC endpoints / private Link / CMEK], logging, and budgets. On [project] I owned [IaC / serving / Bedrock Guardrails / Foundry project / GPU node pool]. I pick a cloud by data gravity and identity, not by a leaderboard. I can talk [Bedrock Agents vs Knowledge Bases / Azure AI Search hybrid / Vertex Agent Engine] at the level of IAM and eval, not just the console wizard. I want to do that here at [their cloud].

**90s**

> I land and operate AI on [cloud]. [Base.] On [project] I [private network + identity + one AI SKU]. We [cut cost / passed a security review / got p95 under N]. I fought a [PTU vs pay-go / GPU idle / 429] incident by [separate keys / scale-to-zero / quotas]. Honest scope: [I did not train models / I am not a researcher]. I have hands-on depth in [one cloud] and working knowledge of [others]; I will not fake a multi-cloud war story. I am here because this JD is an operator of [Bedrock/Foundry/Vertex], which is my lane.

**Customize:** pick the cloud on the JD as the lead even if you are stronger on another — but do not claim certifications you do not have or clicks you never made.

---

### AI Security Engineer

You are scored on OWASP LLM 2026, excessive agency, injection (incl. indirect), MCP, tenancy, secrets. Lead with threat model and controls, not with a red-team persona.

**30s**

> I am an AI security engineer. I treat prompt injection, data leakage, and excessive agency as product bugs with engineering controls — allowlists, ACL in the query, HITL on writes — not as a smarter system prompt. I [reviewed / built / broke] [assistant/agent] and [finding or control]. I want this role because you have [agents/MCP] in the threat model.

**60s**

> I come from [AppSec / platform / AI eng] and I specialize in securing LLM and agent systems. I map OWASP LLM Top 10 2026 onto actual pipelines: identity into retrieval, untrusted retrieved text, tool privilege, MCP gateways, logging redaction. On [project] I [owned ACL filters / killed a write tool / wrote injection evals]. We fail closed if a tenant filter is missing. I want to do this work where agents can call tools, because that is where the incidents are.

**90s**

> I secure AI systems as distributed systems with a confused-deputy problem. [Base.] On [project] I found [cross-tenant retrieve / HITL timeout-as-approve / poisoned tool description] and we [took retrieve down / deny-on-timeout / pinned MCP schemas]. I write evals for unsafe actions as a release blocker at zero. I am not a model-alignment researcher and I will not pretend to be. I am the person who asks “what credential does the tool use?” before we demo. That is why I am talking to you.

**Customize:** only cite OWASP numbers if you can explain them. A real tenancy bug you fixed is worth more than listing the Top 10.

---

### AI Solutions Engineer

You are scored on discovery, translation, light architecture, objection handling. Lead with customer workflow, not with a feature dump.

**30s**

> I am an AI solutions engineer. I take a customer’s workflow — [support, contract review, on-call] — and map it onto a product path that can pass their security and eval bar. I have [run N pilots / owned pre-sales technical / deployed a POC]. I want this role because you need someone who can say no to a demo that would leak data.

**60s**

> I sit between product and customers. My background is [SE / FDE / consulting / support-eng]. I run discovery until we know the user, the cost of a wrong answer, and whether we need HITL. Then I land a thin slice: often RAG with citations, not a multi-agent pitch. On [customer or internal analog] I [outcome: pilot success, blocked unsafe scope, taught evals]. I can demo, but I measure success as they can operate it next month. That is why I want this team’s [product].

**90s**

> I am a solutions engineer for AI products. [Base.] I have run [N] technical evaluations: security questionnaires, retrieval on *their* documents, and a written “in/out of scope.” One [EXAMPLE shape]: a customer wanted an auto-remediating agent; we sold a read-only RCA copilot first and kept the deal without taking on their production blast radius. I write enough architecture to be credible with their platform team, and I pull an SE Architect when the estate is a mesh of three clouds. I have not been a quota-carrying AE and I am not trying to be. I want to make *this* product successful in [their vertical] because [specific constraint you actually know].

**Customize:** if you have no customer-facing work, say “internal stakeholder” honestly or do not lead with this role.

---

### AI Solutions Architect

You are scored on end-to-end design, governance, operating model, cost, integration. Lead with requirements and the operating model, not a logo slide.

**30s**

> I am an AI solutions architect. I design systems customers can operate: identity, retrieval or tools, evals, cost, and an operating model — not a diagram of every vendor. I have [owned reference architectures / ADRs / a landing zone for Foundry or Bedrock]. I want this role because you sell into [regulated / complex estates].

**60s**

> I architect applied AI for [enterprise]. Background: [SE / platform / consulting]. I start from data gravity, IdP, and the cost of being wrong, then choose RAG vs workflow vs agent, and which cloud SKU actually fits. I write ADRs that include evals and fail-closed tenancy. On [program] I [decision that stuck: hybrid search, no multi-agent, MCP gateway]. I will not put a crew of agents on a refund path to win a slide. I want to do that work here.

**90s**

> I am a solutions architect for production AI. [Base + domain.] I have led [N] designs from discovery to a landing zone: [network, keys, search, model, obs, HITL]. Example decision: [Postgres + pgvector until N chunks, then dedicated search; or Foundry because Entra]. I partner with security on OWASP LLM 2026 controls and with ops on who owns the eval set after we leave. Honest boundary: I am not your day-2 SRE for GPU kernels, and I am not a researcher. I am the person who can put a governable architecture on one page and defend it to a CISO and a platform lead in the same hour.

**Customize:** name one ADR-quality decision you actually made. If you have only implemented, not designed for a customer, use GenAI or Cloud templates instead of inflating “architect.”

---

### Forward Deployed Engineer

You are scored on ambiguity, messy data, on-site (or on-customer) delivery, scoping, HITL v0. Lead with a deployment, not with LeetCode.

**30s**

> I am a forward deployed engineer. I go into an underspecified customer problem, scope a v0 they can trust — usually HITL, evals on *their* data — and leave something operable. I have [done N deployments / internal analog with stakeholders]. I want this loop, not a closed-world product-only IC role.

**60s**

> I am an FDE / FDAIE. Background: [SWE + customer or consulting or internal platform with political stakeholders]. I do not start with architecture. I start with who is wronged by a bad answer, what data we can actually get, and what we will not automate. On [deployment] I cut scope to [one department / one intent], because ACL tags were not there, and we still [got a pilot metric]. I write the glue: RAG, auth, eval notebooks, and the ugly ETL. I want Palantir-style / OpenAI-style / your-style deployment work where the discriminator is judgment under ambiguity.

**90s**

> I deploy AI into real environments. [Base.] A typical story: the customer asked for an agent over all documents; I found mixed tenancy and no owners. I scoped one department, fail-closed untagged docs, 25 labeled questions, and a weekly eval the champion could run. We did not leak. We did not over-demo. I can code the path (Python, retrieval, a thin service) and I can tell a VP their data is not ready. I have not done [classified / healthcare] specifically; I have done [what you have]. I am here because your FDE loop is the job, not a bolt-on “customer plus.”

**Customize:** if you have never sat with a customer, do not claim FDE. Use internal platform + messy stakeholder stories, and say “internal deploy.” Lying about on-site work dies in the first scenario round.

---

## 4. Length control and delivery

| Version | When | Stop after |
| --- | --- | --- |
| 30s | Recruiter screen, “quick intro” | Why you are here |
| 60s | Default hiring-manager open | JD match + one project |
| 90s | On-site when they say “walk me through your background” | Boundary + invite |

Practice with a timer. If 30s is 50s, you are reciting a resume.

Delivery:

- Sit still. Do not list ten technologies.
- One number, not four.
- No “passionate about AI.”
- No trashing the current employer in sentence two (that is a later, careful story).
- Match energy: recruiter gets 30s clean; hiring manager gets 60s with a trade-off.

If they interrupt, do not restart from childhood. Ask: “Do you want more on the project or on why this role?”

---

## 5. Common wrecks

| Wreck | Example | Fix |
| --- | --- | --- |
| Resume recitation | 2018 internship → 2024 | Start at the role you want |
| Framework dump | “LangGraph, CrewAI, AutoGen, LlamaIndex…” | One stack you can defend |
| Overclaim | “I ran production multi-agent at scale” | Pilot / N users / your slice |
| Underclaim | “I just helped a bit” | One owned piece |
| Wrong role | FDE intro that never mentions a customer | Switch templates |
| Course list | “I finished DeepLearning.AI, LangChain, …” | Project + evals |
| No landing | Trail off into “yeah, so…” | Last sentence = why this job |

---

## 6. After the intro

They will pick a thread. Plant the threads on purpose:

- A project you can defend (Chapter 23)
- An incident (Chapter 22)
- A disagreement or “I said no to an agent” (Chapter 24)

Do not plant a thread you cannot survive for 15 minutes.

Write your three lengths in a notes app, say them out loud until they are slightly boring, then stop rehearsing wording. In the room, generate from the skeleton. If you sound memorized, they will poke until you break. If you sound structured and honest, they relax — and the rest of the loop gets easier.
