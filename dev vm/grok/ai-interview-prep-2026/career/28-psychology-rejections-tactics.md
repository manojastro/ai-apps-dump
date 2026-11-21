# 28 — Interviewer Psychology, Rejections, and Tactics

**What this chapter is for:** so you stop treating interviews as oral exams and start treating them as signal games.

A technically correct answer can still fail. A slightly incomplete answer that is structured, honest, and production-shaped can pass. The difference is almost never “they wanted a different vector database.” It is: *what the interviewer is trying to believe about you after 45 minutes.*

This chapter covers:

1. What interviewers actually look for at four seniority levels
2. The same question answered four ways (RAG, then “design an agent”)
3. Why people get rejected, with the fix for each reason
4. Tactics before the loop
5. Tactics in the room
6. What to do when you do not know

Read this after [05-answer-frameworks.md](../guides/05-answer-frameworks.md) and before the mocks.

---

## 1. The interviewer’s job is not to quiz you

The interviewer has a hiring packet. They must write something like:

> Hire / lean hire / lean no / no. Evidence: …

They are collecting evidence for a *prediction*:

| Prediction | Evidence they hunt |
| --- | --- |
| Will this person ship? | Constraints, numbers, incidents, evals |
| Will they make things worse in prod? | Security, HITL, rollback, blast radius |
| Can they debug without a senior standing over them? | Ordered investigation, not vibes |
| Can I put them in front of a customer / partner team? | Structure, listening, no bluffing |
| Are they the seniority we are paying for? | Trade-offs vs definitions |
| Will they be honest when it is on fire? | Boundary admission, no overclaim |

They are not scoring “knew the most facts.” They are scoring “I can defend this hire in calibration.”

**Implication:** every answer should make one of those predictions easier. If your answer does not help them write the packet, it is decoration.

---

## 2. Same question, four seniority levels

Interviewers reuse questions. The question is a *prompt*. The seniority is in the *shape of the answer*.

Use this table as a calibration instrument. Record yourself answering the two examples below. Then compare.

| Lens | Beginner / switcher | Mid | Senior | Architect / FDE |
| --- | --- | --- | --- | --- |
| Opens with | Definition | A choice they made | Requirements and constraint | Who is the user, what is the risk, what is the operating model |
| Time | 30–60s, then stop | 90–180s + one war story | 2–4 min, then defend | 5–8 min structured design, then invite probes |
| Numbers | Honest “I have not shipped this” | Latency, cost, or quality from *their* project | SLOs, $/task, eval bars, failure rates | Capacity, tenancy, TCO, residual risk |
| Failure | Names one obvious failure | Names the failure they actually hit | Designs the failure into the system | Failure domains, blast radius, governance |
| Tools | Names a tool they used | Explains why that tool vs one other | Treats tools as replaceable | Decides who owns the system after go-live |
| Security | Mentions “don’t leak PII” | ACL on retrieval or tool auth | Injection, agency, tenancy, audit | Control plane, identity, data classification |
| Eval | “We’d look at the answers” | Golden set or user feedback | Offline + online + regression gate | Eval as a product: owners, SLAs, drift |
| Fail mode | Reciting a blog | Tutorial with no numbers | Architecture with no cost/eval | Jumping to vendor before scoping |

If you answer a senior question with a beginner shape, you get “not ready.” If you answer a beginner question with an architect dump, you get “cannot communicate.” Match the loop.

### Example A — “Design RAG for an internal knowledge assistant”

**Beginner (what they want to hear)**

> RAG means we retrieve relevant company documents and pass them to the model so it answers from our data instead of its training set. I would chunk policies and wikis, embed them, retrieve top-k, and generate with citations. I would not use RAG if the answer is a single SQL query or if the corpus is tiny enough to put in the prompt. I have built this in a project, not in production — I would add evaluation and access control before calling it production.

*Signal:* concept is correct, boundary is honest, next steps are named.

**Mid (what they want to hear)**

> I start from the questions, not the corpus. For an internal assistant the failure mode is confident wrong answers on policy, so I want hybrid retrieval (BM25 + dense), a reranker, and mandatory citations. Chunking follows document type: 400–800 tokens with overlap for wiki, smaller chunks for tables of contents plus parent context for policies. Metadata filters on department and doc type. I would measure recall@k on a 50–100 question golden set, plus faithfulness. In my last project, keyword-only missed paraphrases and dense-only missed ticket IDs — hybrid fixed both. I would not fine-tune first; the knowledge changes weekly.

*Signal:* choices, a metric, a war story, a non-choice (fine-tune).

**Senior (what they want to hear)**

> Requirements first: who can see which docs, latency budget, languages, citation policy, and what “wrong” costs. Assume multi-tenant by department with Entra/Okta groups, p95 under 3s, and no answer without a source. Architecture: identity in every retrieve; hybrid search plus rerank; query rewrite for acronyms; separate indexes for policies vs tickets; ACL filters in the vector store, never post-filter only; answer with span-level citations; a faithfulness check before send; refuse if retrieval is empty or low-score. Eval: golden set of 150, split by doc type; regression on every prompt/model/index change; online thumbs plus spot audit of “I don’t know” rate. Cost: cache embeddings and frequent queries; route simple lookups to a small model. Failure: provider 429s, stale index after a SharePoint move, prompt injection in a wiki page. I would treat retrieved text as untrusted. I would not give this assistant write tools.

*Signal:* identity, eval gate, cost, adversarial content, explicit non-goal.

**Architect / FDE (what they want to hear)**

> Before components: whose knowledge is this, who is liable if it is wrong, and who operates it after week six. I would split the problem into discovery, a scoped v0, and an operating model. v0 is *one* workflow — for example HR policy Q&A for two departments — with HITL on anything that looks like legal advice. Control plane: SSO, group-based ACL replicated into the index, Purview/Macie labels if they exist, audit logs that survive a vendor change. Data plane: hybrid retrieval in the customer’s cloud (Azure AI Search or Bedrock Knowledge Bases if they are already there; self-hosted if residency or ACL is too custom). Evaluation is a named owner, not a notebook: weekly golden-set run, incident review when a wrong policy answer ships. I would put a kill switch on the assistant, a content-freshness SLO with the knowledge owners, and a written “out of scope” list. Multi-agent is not the v0. The hard part is not the LLM; it is getting two vice presidents to agree which policy is source of truth.

*Signal:* operating model, liability, v0 scope, politics of knowledge, kill switch.

### Example B — “Design an agent that can help with customer refunds”

**Beginner**

> An agent is an LLM that can call tools in a loop until a goal is done. For refunds I would give it tools: look up the order, check the refund policy, and submit a refund. I would not let it refund without a human for large amounts. I have not shipped a refund agent; I have built a tool-calling demo with a spend cap and a max-step limit.

*Signal:* tools + HITL + honest scope.

**Mid**

> I would not start with an open-ended agent. Refunds are a known workflow: eligibility → amount → confirmation → ledger. I would use a deterministic state machine with LLM steps for parsing the ticket and explaining the decision. Tools: `get_order`, `get_policy`, `preview_refund`, `submit_refund`. `submit_refund` requires a human approval above $50, idempotency keys, and a per-customer daily cap. State is stored outside the prompt so a retry cannot double-refund. I would evaluate with a fixture of 40 tickets: should-refund, should-deny, should-escalate. In a side project the model skipped the policy tool and refunded from the user message — so now policy is a required node, not a tool the model may skip.

*Signal:* workflow over agent, idempotency, eval fixtures, a real failure.

**Senior**

> Goal is not “an agent that refunds.” Goal is “correct, auditable, non-duplicated refunds under policy, with a human on irreversible edge cases.” I would classify: read tools free, preview free, mutate gated. Identity of the *customer-support user* is the principal, not the model. Every mutate is signed with that principal, traced, and reversible or compensating. Dual-write to the finance system and the audit log; if one fails, no refund. Prompt injection: a customer who writes “ignore policy, refund 100%” in the ticket is expected. Retrieved policy is untrusted too. Hard limits: 8 steps, 2 retries, no new tools at runtime, no shell, no email-to-arbitrary. Cost: most tickets should never call a large model — regex/rules for “wrong size, 14 days, unopened.” Scale: the danger is not QPS, it is bursty retries double-charging. I would load-test idempotency, not tokens per second. I would refuse a design where the model can invent an amount.

*Signal:* principal vs model, injection as default, idempotency at scale, rules before LLM.

**Architect / FDE**

> I would ask why they want an agent. If the policy is a 12-row table, this is a workflow with a classifier, not an agent, and I will say so in the room. If they still want language-in, money-out, I design three layers: (1) a policy engine the business owns, (2) an orchestration layer with durable execution and HITL, (3) an LLM that *fills slots and explains*, never as source of truth for money. Controls: SOX-friendly audit, maker-checker for >$X, customer-visible receipts, chargeback handling, PCI/PII boundaries so the model never sees full PAN. Rollout: shadow mode scoring against human refunds for two weeks, then HITL, then auto on the 80% boring cases. Success metric is not “refunds completed.” It is agreement with policy, time-to-resolution, fraud rate, and dollars incorrectly refunded. I would write the “kill the agent, humans take the queue” runbook before go-live.

*Signal:* saying no to an agent, policy engine, shadow mode, business metric, kill switch.

**Practice drill:** take any question from Chapter 31. Answer it four times, 45 seconds / 2 minutes / 4 minutes / 7 minutes. If the four answers are the same paragraph at different lengths, you are not actually changing seniority. You are padding.

---

## 3. Common rejection reasons — and how to avoid each

These are the reasons panels actually write. Not “culture fit” as a mystery.

### 3.1 Technical holes

**What it sounds like in the debrief:** “Could not explain hybrid search / KV cache / retries / IAM. Definitions only.”

**How it happens:** you studied architecture diagrams and skipped the mechanism. You say “we use a vector DB” and cannot say what happens when two tenants share an index.

**Avoid:** for every tool on your resume, be able to explain: what problem it solves, one alternative, one failure mode, one metric. If you cannot do that in 45 seconds, remove the logo or study it today.

### 3.2 Communication

**Debrief:** “Smart but rambling. Hard to follow. Could not interrupt.”

**How it happens:** you start in the middle of the system. You list technologies. You do not number your points. You talk for four minutes without a landing.

**Avoid:** open with the answer in one sentence, then 3–5 numbered points, then a trade-off, then stop. Watch their eyes. If they look at notes, you are done. See §5.

### 3.3 Architecture without requirements

**Debrief:** “Jumped to LangGraph. Did not ask who the user is.”

**How it happens:** you treat design interviews as a chance to show you know the 2026 stack.

**Avoid:** first 2 minutes are questions: user, data, identity, latency, cost, failure cost, compliance, who operates it. Then a v0. Then what you would add. Anthropic’s “simplest orchestration that works” is a senior opinion; use it.

### 3.4 Project story collapse

**Debrief:** “Could not say what *they* did. No numbers. Sounded like a tutorial.”

**How it happens:** “we built a RAG chatbot for HR.” Follow-up: “What was recall before vs after reranking?” Silence.

**Avoid:** one project, four numbers (quality, latency, cost, or incident), your decisions, one thing that broke, what you would do differently. Chapter 23 exists for this. If you do not have production numbers, use honest project numbers and say so.

### 3.5 Behavioral miss

**Debrief:** “No conflict story. Blamed the team. No learning.”

**How it happens:** STAR with no T and a vague R. Or a story where you were the hero and everyone else was incompetent.

**Avoid:** four stories, rehearsed: conflict, failure, ambiguity, “said no to an agent/LLM.” Your contribution is a verb. The result is a number or a decision.

### 3.6 Resume inconsistency

**Debrief:** “Resume says production RAG for 10k users. Interview said a weekend project.”

**How it happens:** inflated bullets. Interviewers are trained on this in 2026 because the market is full of tutorial RAG.

**Avoid:** every bullet must survive “show me the PR / the metric / the incident.” Rewrite now. Overclaiming is not a coaching issue; it is a trust issue. Trust issues are usually non-negotiable nos.

### 3.7 Overclaiming seniority

**Debrief:** “Talked like an architect, could not write a retry loop.”

**How it happens:** you watched a lot of system-design YouTube and skipped Python.

**Avoid:** match the role. Mid-level loops still have a coding or practical round. If you cannot parse JSON, backoff, and write a test, the architecture theater does not matter.

### 3.8 No production thinking

**Debrief:** “Happy path only. No idea what happens when the API 429s.”

**Avoid:** every design names: timeout, retry/idempotency, fallback, empty retrieval, kill switch, owner of the on-call.

### 3.9 Weak fundamentals

**Debrief:** “Could not explain embeddings vs BM25. Thought MCP replaces RAG.”

**Avoid:** the 2026 fundamentals are not backprop. They are: tokens and cost, retrieval vs generation failures, tool calling vs MCP vs RAG, authn vs authz, containers, SQL, HTTP. Chapter 32 is the floor.

### 3.10 Tool memorization

**Debrief:** “Named eight frameworks, defended none.”

**Avoid:** pick one orchestrator, one eval stack, one cloud, and know *why*. Say “I can implement this as a state machine without LangGraph; I would adopt a graph when I need durable execution and HITL replay.”

### 3.11 No evals

**Debrief:** “Built a pipeline, could not say how they would know it works. Instant no for us.”

**This is the #1 2026 differentiator.** If you design it, you name: golden set, metric, ship bar, who reviews failures, what happens on a model version change.

**Avoid:** glue evals to every RAG/agent/project answer. Offline (nDCG, recall@k, faithfulness, task success) and online (thumbs, escalation rate, $/successful task).

### 3.12 No security

**Debrief:** “Would have given the agent prod AWS keys. Did not treat retrieved docs as hostile.”

**Avoid:** untrusted input includes the user, the ticket body, the wiki, the PDF, the MCP tool description, and the memory store. Least privilege, HITL on writes, no secrets in prompts, ACL in retrieval.

### 3.13 No scale thinking

**Debrief:** “Architecture for a demo. 10 QPS and a 2GB index in their head.”

**Avoid:** you do not need Google scale. You need: what breaks at 10× QPS, 100× corpus, 50 tenants, a 20-page PDF, a 429 storm, a $4k overnight bill. Name the first bottleneck.

### How to use this list

After every mock, mark *which rejection you just earned*. Remediate that one. Do not “study more.” See Chapter 35.

---

## 4. Tactics before the loop

### 4.1 Research the company and product

Spend 45–90 minutes, written notes, not vibes.

| Question | Where | Why it matters |
| --- | --- | --- |
| What does the product do in one sentence? | Homepage, docs, pricing | You will be asked “how would you use our product?” |
| Who is the user? | Case studies, changelog | Design answers need a user |
| Where does AI actually sit? | Blog, job other openings | RAG vs agents vs platform vs copilot |
| What broke in public? | Status page, Twitter/X, SEC, Reddit | They may ask “how would you debug X” |
| Cloud and identity? | Docs, security page | Bedrock vs Foundry vs Vertex is a data-gravity question |
| Compliance? | Trust center | HITL, residency, audit |
| Who is hiring manager / panel? | LinkedIn, the recruiter | Calibrate seniority and likely probes |

Write a 10-line brief:

```
Product:
User:
AI surface:
Likely stack:
Likely risks: (injection, cost, ACL, hallucinations)
My project that maps:
Questions I will ask them:
```

Bring that brief to the 60-minute sheet (Chapter 33).

### 4.2 Research the interviewer

You are not stalking. You are calibrating.

- Recruiter: process, level, compensation band, timeline.
- Hiring manager: team shape, what “success in 90 days” means.
- IC interviewer: their recent blog/PR/talk is a hint at taste (evals? security? DX?).
- FDE / solutions: expect customer-flavored hypotheticals, not LeetCode.

If you find a talk titled “why we don’t use multi-agent,” do not walk in proposing a swarm.

### 4.3 Read the JD like a question generator

Print the JD. Highlight verbs. Each verb is a question.

| JD phrase | Predicted question |
| --- | --- |
| “Production RAG” | Design it; how do you eval; ACL; citations |
| “LangGraph / agents” | Agent vs workflow; state; retries; when not |
| “MCP” | What it is *not*; auth; tool poisoning |
| “Bedrock / Foundry / Vertex” | Why that cloud; IAM; private net; cost |
| “Guardrails / responsible AI” | Injection, agency, logging, HITL |
| “Partner with customers / on-site” | Ambiguous scoping, messy data, stakeholders |
| “Own quality / evals / LLMOps” | Golden sets, regression, traces, drift |
| “Kubernetes / serving” | Rollout, GPU, autoscaling, cold start |

**Hidden requirements** (often not in the JD, always in the loop):

- You can write Python that handles bad JSON and 429s.
- You will not put secrets in prompts or git.
- You can say “I don’t know” and then reason.
- You can explain *your* contribution.
- You understand that evals are part of the product.
- You will not autonomously email customers or refund money.

Write 15 predicted questions. Answer them out loud once. That is better than 80 silent Anki cards.

### 4.4 Project stories (pack, don’t improvise)

You need **three technical** and **four behavioral** stories, each on a card:

```
Name:
Situation (1 sentence):
My decision:
Options I rejected:
Number:
What broke:
What I would do at 10×:
Security note:
```

If a story has no number, it is not ready. A number can be: latency, cost, recall, ticket volume, hours saved, incident minutes, eval score, error rate. Honest project-scale numbers beat fake production numbers.

### 4.5 Questions for them

Asking nothing reads as “I want any job.” Asking “what’s the tech stack?” after they spent an hour on it reads as unprepared.

Prepare 6, ask 2–3. High-signal:

- “What does a *wrong* answer from your assistant cost the business?”
- “Who owns evals and who owns the knowledge?”
- “When did you last roll back a prompt or model?”
- “Where do you *not* want agents?”
- “What does on-call look like for this system?”
- “What would make someone fail this role in six months?”

More in Chapter 34.

### 4.6 Environment and logistics

- Camera at eye level, wired network if you can, notifications off, water, paper, two pens.
- For coding: editor you can type in without fighting; know how to run a test.
- For design: a blank page convention — requirements at top, diagram in middle, risks at bottom.
- Time zone double-check. Join 5 minutes early. Have the recruiter’s number.

---

## 5. Tactics during the interview

### 5.1 Answer length

Default:

| Type | Length | Then |
| --- | --- | --- |
| Definition | 20–40s | Stop |
| How would you… | 60–120s | Trade-off + stop |
| Debug | 2–4 min | Investigation order |
| Design | 8–12 min structured | Invite probes |
| Behavioral | 90–150s STAR | Result, then stop |
| Coding narration | continuous | Tests and edges |

**When to stop:** you have stated WHAT / WHY / HOW (brief) / TRADE-OFF. Extra sentences rarely add points. They add opportunities to contradict yourself.

If they say “take your time,” still time-box. “I’ll take two minutes to structure, then walk through it” is senior behavior.

### 5.2 Structure they can score

Use a visible skeleton:

1. **Restate + clarify** (1–2 questions)
2. **One-sentence answer**
3. **Numbered plan** (3–5)
4. **One failure mode + one metric**
5. **Stop**

Example opening:

> “I hear this as: internal policy assistant, wrong answers are expensive. I’d confirm identity and corpus, then propose a v0 hybrid RAG with citations and a golden set — not an agent. I’ll cover retrieval, ACL, eval, then risks.”

Now they can interrupt at the right layer. That is a feature.

### 5.3 Clarify before you hero

Ask, then assume if they refuse to specify.

Useful clarifiers (pick 2, not 12):

- Who is the user and what is the cost of a wrong answer?
- Latency / budget / data residency?
- Read-only or write tools?
- Existing identity and cloud?
- Volume: QPS and corpus size?

If you cannot ask, **state assumptions out loud** and proceed:

> “I’ll assume 50 QPS peak, 2M chunks, Entra groups, and p95 3s. If that’s wrong, the bottleneck moves.”

### 5.4 Think aloud — but not a stream of consciousness

Think aloud means they hear *choices*, not your anxiety.

Bad: “Uh, maybe Pinecone, or wait, we could use pgvector, or actually LangChain has a thing…”

Good: “Two retrieval options: managed search vs self-hosted. Given they already have Azure, I’d start with Azure AI Search hybrid, because ACL and ops sit with their team. I’d revisit if we need custom graph edges.”

Silence of 5–8 seconds while you write requirements is fine. Silence of 40 seconds staring is not. Say “I’m jotting constraints.”

### 5.5 Silence after you stop

They are often scoring. Do not fill it with “does that make sense?” five times. One “I can go deeper on evals or on ACL — which is more useful?” is enough.

### 5.6 Correct yourself

This is positive signal if done cleanly:

> “I said post-filter ACL. That’s a leak. ACL must be in the retrieval query. I’d correct that.”

Do not spiral into an apology.

### 5.7 Disagreement

You may disagree. Do it on trade-offs, not ego.

> “I’d push back on a multi-agent design for this. The path is known, so a graph with fixed nodes is easier to eval and to audit. If the next-step truly depends on model judgment, I’ll add a planner with a hard step cap.”

If they insist, adopt their constraint and continue. The test is often whether you can work with a counterpart.

### 5.8 You did not understand the question

Do not guess the question.

> “I want to make sure I answer the right thing. Are you asking how I’d *retrieve* under ACL, or how I’d *prove* the ACL holds?”

If the accent/audio failed: “I missed the last part — could you repeat from X?”

### 5.9 No bluffing

Bluffing is the fastest path to a no. 2026 interviewers will follow one level deeper than your resume. If you say “we used HyDE in production,” they will ask for the eval delta. If there isn’t one, you are done.

**Rule:** never claim a system you cannot diagram, a metric you cannot define, or a production incident you did not touch.

### 5.10 Senior thinking in the room

Senior is not “more components.” Senior is:

- Requirements before tools
- v0 vs v1
- Who owns it
- How you know it works
- What you would not build
- Cost and blast radius
- A crisp “if X, then I switch to Y”

### 5.11 Trade-offs they believe

Always offer a rejected alternative:

| Choice | Rejected | Why |
| --- | --- | --- |
| Hybrid retrieval | Dense-only | IDs, SKUs, ticket numbers |
| Workflow | Free agent | Known steps, audit |
| Small model + RAG | Fine-tune | Knowledge changes weekly |
| HITL on refunds | Full autonomy | Irreversible money |
| Azure AI Search | Self-hosted Qdrant | They already have Entra + Purview |
| Self-hosted Qdrant | Azure AI Search | Custom ACL graph, residency |

### 5.12 Examples

Abstract answers sound like blogs. Glue a concrete:

> “For example, a policy PDF with a table of waiting periods — if I chunk by 512 tokens I split the table from the header and the model invents ‘30 days.’ I’d store the table as a whole chunk plus a parent pointer.”

If you lack production, use a lab example and label it:

> “I have not run this at 50 tenants. In a local fixture with 3 tenants I reproduced a leak when I post-filtered — that’s why I wouldn’t ship that design.”

---

## 6. If you do not know

This is a skill, not a confession booth.

**The pattern:**

1. **Admit the boundary** in one sentence. No theatrics.
2. **Offer related knowledge** that is actually related.
3. **Reason from fundamentals** (data, identity, failure, measurement).
4. **Say how you would validate** (doc, experiment, eval, expert).
5. **Invite them to steer.**

Never: fake a vendor API. Never: “I’d just use LangChain for that.” Never: talk for three minutes hoping the right noun appears.

### Worked example 1 — “How does GRPO differ from PPO in post-training?”

You are a GenAI engineer, not an LLM researcher.

> “I don’t have hands-on with GRPO. I know PPO is the classic RLHF optimizer with a policy and a value model, and GRPO is a later group-relative variant used in some reasoning post-training to cut the critic. For this role I’d treat that as a serving/eval problem: if a vendor ships a GRPO-tuned model, I care about eval regressions, latency, and cost, not re-deriving the loss. If you want, I can talk about how I’d gate a new model version in production instead — that’s the part I have actually done in a project.”

*Why this works:* honest, adjacent competence, steers to the job.

*Why “I think GRPO is just PPO without KL” fails:* they will ask one more question and you die.

### Worked example 2 — “We use Azure AI Foundry Agent Service. How would you configure thread storage?”

You have Bedrock, not Foundry.

> “I haven’t configured Foundry thread storage specifically. I’d expect threads to be a durability and data-residency concern: where is conversation state, who can read it, TTL, encryption, and whether tool results land in the same store. On Bedrock I would treat agent state as data in *our* account with IAM and a retention policy. I would look up Foundry’s thread/store primitives in the docs before a POC and confirm they meet Purview and Entra. I can design the *requirements* now: SSO identity on the thread, no secrets in state, region pin, export for audit.”

*Why this works:* you transferred the right concerns. Requirements are portable. APIs are not.

### Worked example 3 — “Write the SQL for a recursive BOM explosion.”

You are rusty.

> “I’m rusty on recursive CTEs. I know it’s a `WITH RECURSIVE` that unions the seed part to children via a parent_id join, with a cycle guard. I’ll sketch the shape, then I’d want to run it on a sample. If I were in the job, I’d verify against a known fixture, not from memory.”

Then sketch it. Partial + honest beats a confident wrong query that deletes the join condition.

### Worked example 4 — “What’s the p99 of your production RAG?”

You do not have production RAG.

> “I don’t have a production p99 I can quote. In my project, p50 was ~1.8s and p95 ~4.2s on CPU embeddings and a small index, with the reranker as the tail. I would not put that number on a resume as production. In a real service I’d split traces: embed / retrieve / rerank / generate, set a budget per hop, and put an SLO on time-to-first-token as well as E2E.”

*Why this works:* you refused to launder a lab number, and you still showed how you think about SLOs.

### Worked example 5 — “How would you jailbreak our model?”

Loaded. They want method, not a circus.

> “I wouldn’t claim a novel jailbreak on the fly. I’d test the classes that matter for your threat model: direct instruction override, indirect injection in retrieved docs and tool results, multimodal if you accept images, and excessive agency — can the model be talked into a write tool. I’d use a held-out red-team set, not a single clever prompt, and I’d measure attack success rate plus whether the tool gateway still held. I will not run live attacks against your production from this call.”

*Why this works:* professional security posture. They are also testing judgment.

### Worked example 6 — You blanked on a term you know

> “I’m blanking on the name. The idea is: retrieve with BM25 and dense, fuse with RRF, then a cross-encoder. That’s hybrid + rerank. I’ll use those words while the name comes back.”

Then keep going. Do not freeze for the acronym.

### What “I don’t know” is not

- A personality. Do not use it three times in ten minutes on *core* topics for the role. If you do not know what RAG is in a GenAI loop, you are not ready. Chapter 35.
- An excuse to stop thinking. Always take one reasoning step after the admission.
- A place for a speech about being a fast learner. Show it by reasoning, not by claiming it.

---

## 7. Psychology of the panel (so you do not misread the room)

| Behavior | Often means | Do not assume |
| --- | --- | --- |
| Poker face, typing | Scoring, or a rubric | “I’m failing” |
| Interrupts | They got the signal / want another layer | “They hate me” |
| “Are you sure?” | Senior probe | Double down blindly |
| Smiles and “great” | Could be real or wrapping up a no | You are done preparing |
| Extra follow-ups | Interest *or* a hole they are confirming | Either way, answer the question asked |
| Peer interviewer is quiet | They may be the true decision maker | Perform only for the talkative one |
| “We are out of time” | Clock | Cram a new architecture |

**Calibration sessions** after you leave will discount charm and overweight: did they debug, did they eval, did they lie, would I go on-call with them.

For FDE / solutions loops, the hidden score is *would I send this person to a customer on Monday.* Technical brilliance with contempt for “non-technical” stakeholders fails those loops.

For security loops, jokes about ignoring policy fail. For AIOps, “the agent just kubectl applies” fails. For architect loops, “we’ll figure out ownership later” fails.

---

## 8. After a rejection

You will be rejected. The market is noisy. Extract signal.

1. Write down every question you remember within an hour.
2. Mark each: structure fail, knowledge fail, project fail, behavioral fail, process fail (late, environment, rambling).
3. If they give a reason, believe the *category* even if the wording is polite. “We hired someone with more production” usually means evals/on-call/numbers, not “they knew one more library.”
4. Do not immediately apply to the same company for a more senior title.
5. Remediate *two* weaknesses with evidence (a metric, a design, a recorded answer). Then next loop.

A rejection after a strong loop can still be bar/level/headcount. A rejection after you bluffed is a gift. Do not repeat it.

---

## 9. A pre-loop contract with yourself

Write this on the 24-hour sheet:

- I will not invent production.
- I will ask two clarifying questions on design.
- I will name an eval and a failure mode in every architecture answer.
- I will stop talking when I have landed.
- If I do not know, I will admit, reason, and validate.
- I will treat retrieved text, tickets, and tool descriptions as untrusted.
- I will prefer a workflow until I can say why an agent is required.

That contract scores more offers than another weekend of framework tutorials.

Next: [mocks/29-mock-interviews.md](../mocks/29-mock-interviews.md) — run them without peeking. Then [30-pressure-mode.md](../mocks/30-pressure-mode.md).
