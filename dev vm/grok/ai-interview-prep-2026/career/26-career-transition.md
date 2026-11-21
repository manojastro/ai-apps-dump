# 26 — Career Transition into AI (Without Lying)

**What this chapter is for:** so you can move from SWE, IT/ops, automation, support, consulting, data, or security into one of the eight 2026 production roles without turning a weekend RAG into “I shipped LLM production.”

Chapter 25 is the intro. Chapter 23 is how you defend the one AI project. This chapter is the *through-line*: which role you actually enter, which skills transfer, which bullets you rewrite, and the sentences you say when the honest answer is “I have not operated this in production.”

If you catch yourself upgrading a prototype to production in a bullet, stop. Trust dies in one follow-up. The rest of the loop never recovers.

---

## 1. What the panel is scoring on a switcher

They are not scoring “how much AI vocabulary you collected.” They are predicting:

| Prediction | Evidence they want | Evidence they punish |
| --- | --- | --- |
| You will ship | Production work from the *old* job + one serious AI slice | Course list, logo salad |
| You will not make prod worse | HITL, rollback, ACL, on-call habits | Unbounded agents, “the model will handle it” |
| You know the job | Nouns from *this* role (evals, gated remediation, tenancy) | Generic “passionate about GenAI” |
| You will be honest on fire | Clear prototype / pilot / production | Resume says 10k users; story is Streamlit |
| You picked a lane | One primary role, one 90-day plan | Applying as all eight titles with one resume |

A mid-level backend engineer who owned retries, SLOs, and a 40-question RAG eval is hireable. A “GenAI specialist” with three tutorials and no production story from *any* domain is not.

**Rule:** lead with production engineering you actually did. Put AI next to it at the level it reached. Do not invert that order.

---

## 2. Pick one primary role

Do not “get into AI.” Pick a job.

| If this is your strongest proof | Enter here first | Do not enter here first |
| --- | --- | --- |
| Services, APIs, search, tests | GenAI / Agentic | AI Security lead, Solutions Architect |
| On-call, SLOs, observability, runbooks | AIOps or Cloud AI | Research-adjacent LLM Engineer |
| RPA / BPM / ITSM / HITL workflows | Intelligent Automation | Unbounded multi-agent IC |
| AppSec, identity, threat models | AI Security or Cloud AI | FDE if you have never sat with a customer |
| Customer ambiguity, scoping, messy data | FDE or Solutions Engineer | Closed-world product IC if you hate travel |
| Pipelines, SQL, data quality, lineage | GenAI (corpus) or FDE (glue) | “ML researcher” without papers |
| Reference architectures, ADRs, governance | Solutions Architect | Junior chatbot implementer |

Read [03-skill-matrix.md](../03-skill-matrix.md). Score yourself on **one** column. If two cells are 4–5 and the rest are 1, that is a role. If everything is a 2, you do not have a role yet — you have a study list.

Related titles fold in: LLM Engineer → GenAI/Agentic (or serving if the JD is KV-cache-heavy). FDAIE / AI Deployment → Forward Deployed / AI Deployment.

---

## 3. The honesty contract (words you are allowed to use)

Use this vocabulary on the resume, in the intro, and in project defense. Interviewers listen for it.

| Word | Means | You may use it if |
| --- | --- | --- |
| **Prototype / lab** | You, local or a shared sandbox, no real users | Weekend, course capstone, hackathon |
| **Internal pilot** | Teammates or a volunteer cohort; no SLO | N people used it; you measured something |
| **Production with users** | Real users, deploy path, someone gets paged | You can name rollback and an owner |
| **Production with SLO** | Error budget, on-call, change control | You were in the rotation or owned a gate |
| **I owned** | Design, implementation, or on-call for that slice | You can survive “show me the PR” |
| **I integrated** | Someone else’s control; you wired it | IAM, search, eval harness you did not invent |
| **I reviewed** | You found issues; you did not ship the component | Design review, red-team, code review |

**Never invent users, QPS, Kubernetes, or “we used Guardrails.”** A single follow-up (“walk me through the Helm chart”) ends the interview. Chapter 23 already said this. Switchers fail it more often because the gap between the old job (real) and the AI project (thin) is tempting to paper over.

If a layer never existed, the senior sentence is:

> This was an internal pilot. We did not have a rollback story. If I productionized it I would add an index alias, a pinned model id, and an eval gate in CI.

Inventing the rollback story is the junior sentence.

---

## 4. Transferable skill maps

Each row is a skill you already have, the AI job it maps to, and the sentence that makes the mapping *believable*. Fill the blanks with your facts. Do not recite the examples.

### 4.1 From SWE / backend

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| HTTP APIs, authn, retries, idempotency | Tool calling, MCP gateways, agent writes | GenAI, Agentic, FDE | “I treat a refund tool like a payment webhook: idempotency key, timeout, no double mutate.” |
| Postgres, transactions, tenancy | ACL metadata, eval runs, checkpoint state | GenAI, Agentic, Architect | “Tenant id is a column, not a prompt instruction.” |
| Tests and CI | Golden sets as release gates | All IC roles | “A prompt change that fails faithfulness does not merge.” |
| Search / Elasticsearch | Hybrid retrieval | GenAI, FDE | “I already know BM25 fails paraphrases and dense fails ticket IDs.” |
| Feature flags, canary | Prompt/model/index pinning | Cloud AI, Deployment | “Rollback is a config pointer, not a hope.” |
| On-call for a service | Incident order on RAG/agents | GenAI, AIOps | “Observe traces first. Do not swap the model because Slack asked.” |

**Do not claim:** you are an ML researcher; you “trained a model” because you called `fine_tune` on 40 rows; LangChain expertise because you imported it.

### 4.2 From IT / ops / SRE

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| SLOs, error budgets, paging | When *not* to auto-remediate | AIOps, Cloud AI | “A restart that extends an outage is why execute stays behind HITL.” |
| Metrics, logs, traces, cardinality | Correlation, RCA copilots | AIOps | “Topology before the LLM draft. The model does not invent edges.” |
| Runbooks, incident command | Grounded RCA, evals on real incidents | AIOps, Automation | “The copilot drafts; the human owns the change ticket.” |
| Change control, blameless postmortems | Prompt/index change control | Cloud AI, LLMOps | “Model id is a dependency like a library version.” |
| Capacity, cost, quotas | Tokens, PTU, 429s | Cloud AI | “I have fought noisy-neighbor quotas. LLM 429s are the same class.” |
| IAM, secrets, networks | Private model endpoints, key hygiene | Cloud AI, Security | “No public API keys on a laptop. Same rule as prod AWS keys.” |

**Do not claim:** k-means on dashboards is AIOps; you “built an autonomous healer”; you understand transformers because you ingested logs into a vector DB.

### 4.3 From automation / RPA / BPM

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| Process discovery, exceptions, SLAs | Workflow vs agent | Intelligent Automation | “If the steps are known, I will not put an agent on it.” |
| Human-in-the-loop queues | HITL on irreversible actions | Automation, Agentic | “Maker-checker is not a UX nicety. It is the control.” |
| Connectors (ServiceNow, SAP, Salesforce) | Tool allowlists, identity of the *user* | Automation, Solutions | “The bot uses the requester’s principal, not a god account.” |
| Audit logs, compensations | Idempotent writes, replay | Automation, Agentic | “A retried invoice must not double-post.” |
| Bot failure rates, exception taxonomies | Task-completion evals | Automation, Agentic | “I already label ‘should-do / should-escalate / should-refuse.’” |

**Do not claim:** every RPA bot is now an agent; UiPath plus an LLM call is “agentic AI in production” unless you can talk state, tools, and evals; you can skip Python because the studio is visual.

### 4.4 From support / support-engineering

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| Ticket taxonomies, macros, SLAs | Eval sets from real questions | GenAI, Solutions | “The golden set is last month’s tickets, not invented FAQs.” |
| Escalation, cost of a wrong answer | Refusal, citations, HITL | GenAI, FDE | “Wrong visa advice is worse than ‘I don’t know.’” |
| Customer language, objection handling | Discovery, teach-back | Solutions, FDE | “I can explain RAG to a VP without saying ‘embeddings.’” |
| Knowledge base rot | Freshness SLO, owners | GenAI, Architect | “Who owns the policy that went stale is the hard problem.” |
| Tools you already click (ITSM, CRM) | Copilot on a real workflow | Automation, Solutions | “I know the exception path because I lived in it.” |

**Do not claim:** you “built the assistant” if you only wrote macros; FDE on-site experience if you took support calls from a queue; Solutions Engineer quota ownership if you never ran a technical evaluation.

### 4.5 From consulting / SI / internal transformation

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| Ambiguous SOWs, stakeholder maps | FDE scoping, Solutions discovery | FDE, Solutions, Architect | “I write in/out of scope before I draw a diagram.” |
| Security questionnaires | Tenancy, residency, HITL | Architect, Security, FDE | “I do not demo on mixed-ACL corpora.” |
| Thin slices, phased delivery | v0 with HITL | FDE, Solutions | “Week one is one department, not an enterprise agent platform.” |
| Executive narrative | 10-minute architecture story | Architect, Solutions | “Operating model and residual risk, not a logo slide.” |
| Saying no without losing the room | When not to use the product | Solutions, FDE | “We sold the read-only copilot, not the auto-remediator.” |

**Do not claim:** you implemented the system if you only staffed people who did; you are an IC GenAI engineer because you wrote a slide titled “RAG architecture”; you have production on-call because the client did.

### 4.6 From data / analytics / analytics engineering

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| Pipelines, freshness, quality checks | Corpus hygiene, index jobs | GenAI, Cloud AI, FDE | “Garbage chunks are a data-quality incident, not an LLM incident.” |
| SQL, warehouses, lineage | Eval stores, feedback tables, ACL joins | GenAI, AIOps | “I can join user → group → doc without putting that in the prompt.” |
| Labeling, experiment design | Golden sets, A/B, ship bars | GenAI, LLMOps | “I know a test set you wrote yourself is contaminated.” |
| dbt / Airflow / Spark (if true) | Index builds, backfills, re-embed jobs | Cloud AI, FDE | “Re-embed is a versioned collection swap, not a silent overwrite.” |
| Stakeholder metric fights | Online evals vs thumbs | Solutions, GenAI | “Thumbs are not faithfulness.” |

**Do not claim:** you are a research scientist; you “do ML” because you trained XGBoost in 2019; RAG is “just a vector index” you can skip retrieval metrics for.

### 4.7 From security / AppSec / IAM

| You already do | Maps to | Role(s) | Sentence shape |
| --- | --- | --- | --- |
| Threat models, STRIDE, reviews | OWASP LLM 2026 on a real pipeline | AI Security | “Retrieved text is untrusted. So is the ticket body. So is the tool description.” |
| Authn vs authz, SSO, groups | Identity in every retrieve and tool | Security, Cloud, GenAI | “ACL in the query, never post-filter only.” |
| Secrets, SSRF, injection | Prompt injection, MCP, SSRF via tools | Security, Agentic | “I will not give the agent a shell or a god token.” |
| Detection / response | Logging, redaction, kill switches | Security, AIOps | “We page on unsafe-action rate, not only on 500s.” |
| Pushing back on ship dates | HITL, deny-on-timeout | Security, FDE | “Timeout-as-approve is a finding, not a convenience.” |

**Do not claim:** you have operated LLM red teams if you only ran a jailbreak tweet; you “know OWASP LLM Top 10” if you cannot map a number to a control you would implement; you are a model-alignment researcher.

---

## 5. What you must not claim

These are the 2026 switcher lies panels are trained to hear. Each one is a trust no.

| Claim | Why it dies | Honest replacement |
| --- | --- | --- |
| “Production RAG for N thousand users” | They ask for SLO, ACL, rollback | “Internal pilot, N teammates, 40-question eval” |
| “I built a multi-agent system” | They ask for trajectory evals and why not a workflow | “Tool-calling app with one loop; I would not call it multi-agent” |
| “We used Kubernetes / Helm / EKS” | They ask you to debug a probe | Omit it. Name Docker Compose if that is what you ran |
| “Fine-tuned Llama for our domain” | They ask data size, eval, why not RAG | “I ran a tutorial LoRA. I would not ship facts into weights” |
| “Implemented Bedrock Knowledge Bases / Azure AI Search” | They ask IAM, private net, hybrid query | “Console wizard in a sandbox; I have not landed this in a customer VPC” |
| “Expert in LangGraph, CrewAI, AutoGen, ADK…” | They pick one and go deep | One orchestrator you can defend, plus “I can do v0 as a Python loop” |
| “I led the AI transformation” | They ask what *you* merged | “I owned X. Priya owned Y. I did not do Z.” |
| “Autonomous remediation in prod” | They ask blast radius | “Draft-only. Execute was feature-flagged off.” |
| Course certificates as experience | They ask for a metric | Delete the course line. Keep the project if it has evals |

If marketing wrote your LinkedIn, rewrite it before the recruiter call. Interviewers will read it.

---

## 6. How to rewrite resume bullets

**Formula**

```
[Verb you own] [system type] for [user] ([honest scope]).
[Constraint: ACL / HITL / latency / cost / ITSM].
[What you changed]. [Metric or qualitative + remaining fail class].
Not: [framework dump] [fake scale] [we].
```

One bullet, one owner, one constraint, one proof. Three AI bullets beat eleven.

### Before → after (steal the *shape*, not the numbers)

**SWE**

| Before (fail) | After (pass) |
| --- | --- |
| Built a GenAI chatbot using LangChain, OpenAI, and Pinecone | Owned retrieval + evals for an internal policy assistant (pilot, ~80 users). Hybrid BM25+dense after dense-only missed policy IDs. 40-question set; recall@10 improved on *our* corpus. Not multi-tenant production. |
| Developed microservices in Python | Owned the billing webhook path: idempotent retries, 99.9% success over 6 months, on-call for that service. This is the production bar I bring to tool writes. |

**SRE / ops**

| Before | After |
| --- | --- |
| Implemented AIOps with ML clustering | Built a topology-aware correlation rule that cut noisy pages on checkout by grouping deploy-related 5xx. LLM RCA copilot was a later *pilot*: draft-only, HITL on execute, 25-incident replay. |
| Managed Kubernetes clusters | On-call for a 40-service estate. I have rolled back a bad deploy and written the postmortem. I have not operated GPU node pools; I will not put that on the resume. |

**Automation**

| Before | After |
| --- | --- |
| Automated 50+ processes with UiPath and GenAI | Owned invoice exception workflow in [tool]: 4 known steps, human queue on amount > threshold, audit trail. Added an LLM *parse* step for messy vendor PDFs; posting stayed deterministic. Task-completion labeled on 60 fixtures. |
| Built AI agents for ITSM | ServiceNow catalog bot: classified intent, opened the right catalog item, never closed a change. I would call this a workflow with a classifier, not an agent. |

**Support**

| Before | After |
| --- | --- |
| Used ChatGPT to improve CSAT | Built a 75-question eval set from real tickets (PII stripped). Identified that the vendor bot invented refund policy. Wrote the “must cite or refuse” rule the engineering team shipped. |
| L2 support for SaaS | Owned escalation taxonomy for billing + access. I know which wrong answers cost money vs. a retry. Targeting Solutions / GenAI on support corpora, not a research seat. |

**Consulting**

| Before | After |
| --- | --- |
| Led AI strategy for Fortune 500 clients | Ran discovery for a bank knowledge assistant: mixed ACL, no document owners. Scoped v0 to one department, fail-closed untagged docs, 25 labeled questions. Did not implement the platform; I wrote the in/out of scope the engineers built against. |
| Delivered GenAI POCs | Three POCs. One died because legal would not accept uncited answers. I now start with citation + identity, not a demo. |

**Data**

| Before | After |
| --- | --- |
| Built LLM pipelines | Owned the index job: chunk, metadata from the warehouse ACL table, daily freshness check, versioned collection. 2k engineering docs, internal pilot. Faithfulness still fails on tables. |
| ML models for churn | Trained a classical churn model (XGBoost) on warehouse features. Separate from the RAG pilot. I will not blend them into “ML + GenAI expert.” |

**Security**

| Before | After |
| --- | --- |
| Performed LLM red teaming | Found cross-tenant retrieval when ACL was applied in the app after search. Wrote the finding; we failed closed until the filter moved into the query. Mapped to OWASP LLM data-leakage / vector class. |
| Knowledge of OWASP Top 10 | AppSec baseline: SSRF, IDOR, secrets. I am *learning* OWASP LLM 2026 by applying it to our assistant, not by reciting the list. |

### Resume header for a switcher

Weak: `GenAI Engineer | LangChain | LLMs | Transformers | Kubernetes`

Strong: `Backend engineer (4y) targeting GenAI — production APIs + one eval-gated RAG pilot`

Put the old title if that is still your job. Target role goes in the summary, not as a fake current title.

---

## 7. Honest scripts you can say out loud

These are **shapes**. Replace brackets. If a clause is false, delete it.

### 7.1 The master boundary

> I have not shipped an LLM system with a production SLO. I have shipped [X: payments API / on-call estate / RPA workflow / data pipeline] with [users, rollback, metric]. On the AI side I have [pilot: what you owned, eval, remaining fail class]. I am applying because this role measures [evals / gated remediation / customer v0], which is the work I am already moving into — not because I collected tutorials.

### 7.2 Recruiter (30s)

> I am a [current role] moving into [primary role]. The production skill I am strongest at is [reliability / identity / process discovery / messy data]. I have [one AI project at honest scope]. I am not looking for a research scientist seat or a demo team. I want [their JD noun]. Notice period is [N]. Location is [city / remote constraint].

### 7.3 Hiring manager — “why AI, why now”

> In [domain] we could not solve [unstructured text / RCA / search / exceptions] with rules. I learned that by shipping a thin slice, not by watching keynotes. The interesting part was [evals / ACL / HITL / cost], which is engineering. I would not have said this in 2022. I am saying it because I have seen the failure modes.

Do not trash the current employer. Chapter 24 has the longer STAR. This is the switcher cut.

### 7.4 “Have you put an LLM in production?”

> No, not with an SLO. I have put [non-AI system] in production: [on-call, rollback, metric]. The LLM work reached [pilot / N users]. What transferred is [CI gates / IAM / incident order / HITL]. If your bar is “owned a 50-QPS assistant,” I am not there yet. If your bar is “can productionize a pilot without leaking data,” that is the work I am ready to do.

### 7.5 Role-shaped “I have not shipped LLM prod, but I have shipped X”

**GenAI / Agentic**

> I have not operated RAG at 50 QPS. I have operated a [service] with retries, tests, and on-call. I owned chunking, hybrid retrieval, and a [N]-question eval on a pilot. Dense-only failed on [IDs]. I did not own GPU serving. I default to a workflow when the steps are known; I will not sell you a crew of agents for a refund path.

**AIOps**

> I have not shipped a fully autonomous healer — and I would push back if that were week-one scope. I have [years] of on-call on [estate]. I have correlated noisy pages with topology and written runbooks. The copilot I built drafts RCA and opens a ticket. Execute is off. Unsafe-action rate on the replay set is the metric I care about.

**Cloud AI**

> I have not trained foundation models. I have landed [workloads] in [AWS/Azure/GCP] with [VPC / IAM / secrets]. I can take an approved model endpoint and put a private RAG path in front of it. I have [or: have not] used [Bedrock Knowledge Bases / Azure AI Search / Vertex RAG] beyond a sandbox — I will not fake a customer landing zone.

**Intelligent Automation**

> I have not built an unbounded agent platform. I have discovered processes, mapped exceptions, and shipped HITL bots that post into [ITSM/ERP] with audit. I added LLM extraction where PDFs were messy; the ledger write stayed deterministic. I will argue against an agent where a BPMN path already exists.

**AI Security**

> I have not published an AI red-team paper. I have done AppSec: [IDOR / SSRF / IAM reviews]. On our assistant I treated retrieved wiki text as untrusted, moved ACL into the query, and blocked a write tool that used a shared token. I can threat-model RAG+tools. I am not a weights-alignment researcher.

**Forward Deployed / AI Deployment**

> I have not lived on a customer site for Palantir-length deployments. I have sat with [internal stakeholders / one external customer] who had messy ACLs and no owners. I cut scope to one department, fail-closed untagged docs, and left a 25-question eval they could rerun. I can write the glue in Python. I will tell a VP their data is not ready.

**AI Solutions Engineer**

> I have not carried a quota. I have run [N] technical conversations where the ask was “make it AI.” I interview for user, cost of wrong, and HITL before I demo. I have killed a scope that would have leaked data. I can teach RAG to a VP and to a platform engineer. I will pull an architect when the estate is three clouds.

**AI Solutions Architect**

> I have not been the named architect on a multi-region agent platform. I have written [ADRs / reference designs / security reviews] that stuck: [hybrid search, no multi-agent, identity in retrieve]. I start from data gravity and the operating model. I will not put a logo slide where a CISO needs residual risk.

### 7.6 When they keep pushing

> I do not want to overclaim. Here is the boundary again: [X is mine, Y is not]. I can design the missing layer and tell you how I would eval it. I will not narrate a production incident I did not see.

Then stop. Repeating the lie with more adjectives is how switchers fail senior panels.

---

## 8. Role-by-role entry ramps

“Entry ramp” means the first job you can credibly win, the first project that proves it, and the interview risk that kills switchers for that title.

### GenAI Engineer

| | |
| --- | --- |
| **Typical feeders** | Backend, search, NLP-adjacent, support-eng with a real eval set |
| **First project** | Hybrid RAG on *your* corpus, citations, 40–100 real questions, faithfulness + recall, fail-closed on empty retrieve |
| **90-day hire bar** | Own retrieval quality and the eval gate on an internal assistant; not “learn LangChain” |
| **Interview risk** | Framework dump; no ACL story; cannot debug retrieve-right/answer-wrong |
| **Do not skip** | Chapters 10, 17, 23 |

### Agentic AI Engineer

| | |
| --- | --- |
| **Typical feeders** | Backend with workflows, SRE with tools, automation engineers who can code |
| **First project** | One supervisor, typed tools, step cap, durable state, HITL on writes, trajectory replay of N tasks. No crew of personas. |
| **90-day hire bar** | Make *one* tool-using flow operable: traces, caps, unsafe-action rate |
| **Interview risk** | Multi-agent theater; cannot say when *not* to use an agent |
| **Do not skip** | Chapters 11–13, 19, 17 |

### AIOps Engineer

| | |
| --- | --- |
| **Typical feeders** | SRE, NOC-plus-engineering, observability, ITSM with coding |
| **First project** | Correlation + RCA *draft* on a real service, runbook RAG, execute off, replay of real incidents |
| **90-day hire bar** | Time-to-draft down on a pilot of N services; zero autonomous restarts |
| **Interview risk** | Clustering dashboards; “the LLM will remediates”; no topology |
| **Do not skip** | Chapters 18, 22, 16 |

### Cloud AI Engineer

| | |
| --- | --- |
| **Typical feeders** | Cloud platform, DevOps, SRE with IAM/network depth |
| **First project** | Private endpoint to Bedrock / Azure OpenAI / Vertex; identity; logging; budget alert; one RAG or agent SKU you can defend |
| **90-day hire bar** | Land one app in the *company’s* cloud with a security review that passed |
| **Interview risk** | Console-only; fake multi-cloud; cannot explain 429s / PTU / CMEK |
| **Do not skip** | Chapters 15, 16, 19 |

### Intelligent Automation Engineer

| | |
| --- | --- |
| **Typical feeders** | RPA, BPM, ITSM, business-systems analysts who learned Python |
| **First project** | One process with exceptions labeled, LLM only where language is messy, HITL on money/access, task-completion eval |
| **90-day hire bar** | Production workflow with an LLM *step*, not a demo agent |
| **Interview risk** | Calling every bot an agent; no integration story; cannot code a retry |
| **Do not skip** | Chapters 11 (when not), 18, 08 |

### AI Security Engineer

| | |
| --- | --- |
| **Typical feeders** | AppSec, product security, cloud security, platform with threat-model muscle |
| **First project** | Threat model of an existing assistant; one real finding (tenancy, injection, excessive agency); a control that shipped; unsafe-action eval |
| **90-day hire bar** | You are in the design review path for any new tool |
| **Interview risk** | Reciting OWASP numbers; no baseline AppSec; jailbreak-as-personality |
| **Do not skip** | Chapters 19, 12, 10 (ACL) |

### Forward Deployed / AI Deployment Engineer

| | |
| --- | --- |
| **Typical feeders** | SWE who sat with messy stakeholders; consulting implementers who can code; internal platform “deployed” to other teams |
| **First project** | Deployment narrative: underspecified ask → scoped v0 → their data → eval they can rerun → what you refused to automate |
| **90-day hire bar** | One customer (or internal analog) live on a thin slice with HITL |
| **Interview risk** | Jumping to LangGraph in minute two of the scenario; claiming on-site you do not have |
| **Do not skip** | Chapters 20–21, 24 (ambiguity), 25 FDE intro |

If you have never sat with a customer, say **internal deploy**. Do not apply the Palantir-style FDE intro from Chapter 25 as if you had.

### AI Solutions Engineer

| | |
| --- | --- |
| **Typical feeders** | Support-eng, sales-eng, consulting, product-minded backend |
| **First proof** | Discovery notes + a “no” you said + a teach-back of RAG/agents to a non-engineer |
| **90-day hire bar** | Run a pilot evaluation on a customer’s documents without leaking |
| **Interview risk** | Feature dump; cannot say the product is a bad fit; fake quota |
| **Do not skip** | Chapters 25, 34, 10, 11 |

### AI Solutions Architect

| | |
| --- | --- |
| **Typical feeders** | Senior SE, platform, consulting architects — not a first AI job unless you already architect elsewhere |
| **First proof** | One ADR that includes identity, evals, cost, operating model, and an explicit non-goal |
| **90-day hire bar** | A landing-zone-shaped design a CISO and a platform lead both survived |
| **Interview risk** | Logo slides; no operating model; inflating implementer work to “architect” |
| **Do not skip** | Chapters 20–21, 19, 15 |

If you have only implemented, use GenAI or Cloud templates. Inflating “architect” is overclaiming seniority (Chapter 28).

---

## 9. Ninety-day transition (while you still have the day job)

This is not “quit and grind courses.” It is a production-shaped portfolio plus a resume that does not lie.

### Days 1–14 — lane and inventory

1. Pick **one** primary role from the table in §2.
2. Write a skill inventory: production proof from the old job (with numbers) vs AI proof (honest scope).
3. Rewrite the intro (Chapter 25) *before* you study more RAG.
4. Delete resume claims that cannot survive “show me the PR.”
5. Choose **one** project to deepen. Kill the second tutorial clone.

### Days 15–45 — one serious project (not a demo RAG)

Minimum bar for the project, regardless of role:

| Layer | Required |
| --- | --- |
| Real corpus or realistic fixture | Not the LangChain example docs |
| Eval set from real questions | 30+ ; say how you labeled |
| Ship bar | A number that can block a change |
| Identity story | Even if it is a stubbed `tenant_id` filter in the query |
| Failure class you still have | Tables, multi-hop, injection, loops |
| README honesty | Prototype vs pilot; what you did not build |
| Traces | Langfuse / Phoenix / OpenTelemetry / plain structured logs |

Role add-ons:

| Role | Add this or it is still a demo |
| --- | --- |
| GenAI | Hybrid search, citations, faithfulness |
| Agentic | Step cap, HITL write, trajectory replay |
| AIOps | Real metrics/logs fixture, execute off |
| Cloud AI | IaC or at least private-network *design* plus IAM diagram |
| Automation | Connector + audit + exception taxonomy |
| Security | Injection tests, tenancy test, deny-on-timeout |
| FDE | A scoped “customer” narrative and a data-mess you handled |
| Solutions / Architect | In/out of scope one-pager and operating model |

### Days 46–70 — production layers and spoken defense

1. Defend the project at 30s / 2min / 5min (Chapter 23).
2. Six STAR cards (Chapter 24). At least one story is from the *old* job.
3. One incident story: real non-AI on-call is allowed; inventing an LLM outage is not.
4. Fill the skill-matrix holes that are 5s for your role — only those.
5. Record the boundary script in §7. If you wince, it is still overclaiming.

### Days 71–90 — apply like an adult

1. 8–12 targeted applications, not 80 spray.
2. Recruiter 30s + HM 60s until they are slightly boring.
3. One mock for *that* role (Chapter 29). Score it (Chapter 35).
4. Do not switch primary roles because a recruiter used a cooler title.

If you only have evenings: one layer per week beats seven frameworks in a weekend.

---

## 10. Portfolio that is not demo-only RAG

Interviewers see fifty “ChatGPT over PDFs” repos a week. Yours needs a different shape.

### What to put in the repo

```
README
  Honest scope (prototype | pilot)
  Users / fixture
  What I owned vs copied
  Architecture (8 boxes)
  Eval: size, metrics, ship bar, remaining fails
  How to run the eval (not only the UI)
  What I would add for production
/eval
  questions.json (real or labeled-as-synthetic)
  scores.md (before/after one change)
/src
  retrieve / generate / tools as separate modules
  ACL filter in the query path
/traces or a screenshot of a trace
/postmortem.md  one miss
```

A Streamlit UI is optional. An eval you cannot rerun is a fail.

### What not to put

- API keys, customer PDFs, PII
- A README that says “production-grade enterprise RAG platform”
- Five frameworks in `requirements.txt` you cannot defend
- A fine-tune you cannot explain vs RAG
- Screenshots of a chatbot smiling

### Side projects vs work projects

Prefer a work pilot with numbers you can share. If legal says no, build a **public fixture** that reproduces the *class* of problem (duplicate policies, ticket IDs, hostile wiki page) and say:

> I cannot show the company corpus. This repo is the same retrieval failure I hit, on public data, with the same eval shape.

That is honest and senior. A fake “10k users” README is neither.

### One project, two stories

You need **one** deep AI project and **one** deep non-AI production story. Two shallow RAG clones is worse than one serious pilot plus four years of billing on-call. Chapter 23 said this; it is the switcher’s main advantage. Use it.

---

## 11. How the recruiter screen dies (and how it does not)

Switchers often pass or fail in 20 minutes.

| They ask | Fail | Pass |
| --- | --- | --- |
| Tell me about yourself | Course list, “I want to transition into AI” | Chapter 25 role template + honest scope |
| What have you shipped? | “A RAG app” | Users, your slice, metric, prototype vs prod |
| Why this role? | “AI is the future” | Their constraint + your feeder skill |
| Coding? | “I am more of an architect” | You write Python; you will take the practical round |
| Notice / location / work auth | Ramble | Facts. Chapter 27. |
| Current title vs target | Fake “AI Engineer” on LinkedIn | Real title + target role in one breath |

Practice the 30-second intro *with the boundary sentence*. Recruiter notes get forwarded. “Candidate has not shipped LLM prod; strong SRE; RAG pilot with evals” is a packet that survives. “GenAI expert, multi-agent, Kubernetes” that collapses on the HM call is how you get ghosted.

---

## 12. Fail modes (switcher-specific)

These match Chapters 23–24 and add the transition failure class.

| Fail mode | What it sounds like | Fix |
| --- | --- | --- |
| **Tutorial as production** | “We used LangChain in prod” | Scope word + eval + what you would add |
| **Title laundering** | LinkedIn: AI Engineer; W2: Support | Real title; target in summary |
| **Framework tourism** | Six agent libraries | One stack, one “why not the others” |
| **Erasing the old job** | No mention of on-call, SQL, IAM | That *is* the production proof |
| **Wrong role** | SRE applying as Solutions Architect with no ADRs | Use §2 and §8 |
| **Course-first intro** | “I completed DeepLearning.AI…” | Delete. Lead with shipped work. |
| **Fake FDE** | “I deploy to customers” = internal Slack | Say internal analog |
| **Agent inflation** | Classifier + one tool = “agentic platform” | Use the handbook’s agent vs workflow line |
| **Blaming the old industry** | “Support is a dead end” | Pull toward the work, not a rant |
| **Studying attention math instead of evals** | Unless the JD is LLM Engineer | Path C in Chapter 00 |

Overclaiming is not a coaching issue. It is a trust issue. Trust issues are usually non-negotiable nos (Chapter 28).

---

## 13. Mapping your week to the handbook

Path C in [00-how-to-use.md](../00-how-to-use.md) is the study order. This chapter is day 1, not day 20.

| You finished | You can now |
| --- | --- |
| This chapter + Chapter 25 | Recruiter screen without lying |
| Chapter 23 on *one* project | Survive project defense |
| Chapter 24 six cards | Behavioral as a switcher (old job + AI) |
| Role core topics from Chapter 03 | Technical screen |
| Chapter 34 | Ask questions that prove you know the job |

You are ready to *apply* when you can, without notes:

1. Name one primary role and why not the adjacent one.
2. Give a 60-second intro with production proof + honest AI scope.
3. Defend one project for 15 minutes of “why not X?”
4. Say the boundary script without flinching.
5. Point at a repo or internal artifact that has an eval, not only a UI.

Until then, do not spray applications. The market is full of switchers who learned the nouns. It is short of switchers who kept the production habits and told the truth about the AI slice.

---

## 14. Drill

1. Print your resume. Highlight every AI noun. For each, write prototype / pilot / production. If you cannot, delete the noun.
2. Write one page: old-job production story (numbers) and AI story (honest scope). These are your two pillars.
3. Record §7.1. If you used “we” for something you did not own, rerecord.
4. Pick the entry-ramp table for your role. Build the missing project layer this week — evals, HITL, or ACL — not a new framework.
5. Have a friend ask only: “Was it production?” “What did *you* do?” “What’s the number?” Stop when you can answer all three without upgrading the story.

Pass criteria: a hiring manager who has read this handbook would label you **honest, production-shaped, and in the right lane** — not “another RAG tutorial with a new title.”
