# 13 — Multi-Agent Systems

**Roles that score this chapter as core:** Agentic AI Engineer, Solutions Architect, AI Security (blast radius), Intelligent Automation (when someone proposes a “crew”).

**Roles that still get asked:** GenAI, FDE, Solutions Engineer — usually as a trap after Chapter 11. Cloud AI / AIOps get it only if the design round wandered into orchestration.

This chapter is an **overengineering detector**. The market is full of people who can draw a supervisor with five specialists. It is short of people who can say *that diagram is the bug*.

Default senior opinion, said early:

> One workflow, or one bounded agent, until a real specialty, a real trust boundary, or real parallelism forces a second mind. Two or three specialists can be justified. Five personas is a demo.

If Chapter 11 asked “when should this not be an agent?”, this chapter asks **when should this not be *agents*?** You will not pass a 2026 agentic loop by adding boxes.

---

## Interviewer intent

They have watched five-persona crews land in production as latency, duplicate tickets, and an un-evalable mess. They are scoring whether you treat multi-agent as a **cost you must earn**, not a badge.

| Signal | Pass | Fail |
| --- | --- | --- |
| Default | Single agent or graph; multi-agent is a last resort | “I’d use a crew of specialists” in sentence one |
| Justification | Disjoint tools, disjoint models, disjoint authz, or true parallel work | “Roles make the prompt clearer” |
| Control | Per-agent caps, one write owner, handoff contract | Shared god-tools, no owner |
| State | Handoff packet *or* shared state, chosen on purpose | “They just talk to each other” |
| Eval | Task success + misroute + duplicate-action + $/success | “The crew seemed collaborative” |
| A2A | Working knowledge: agents-to-agents, not a tool bus | A2A as a synonym for MCP or for LangGraph |

**The highest-signal 2026 question in this chapter:** *Why isn’t one agent enough?*

If you cannot answer with a constraint (tools, trust, parallelism, model), you should not propose a second agent. Simplest orchestration that works still applies one level up. Chapter 11 is a prerequisite.

---

## Probability ranking (applied AI loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | When *not* to go multi-agent / “five agents” trap | Almost certain on agentic/architect | Opinion + counter-design |
| 2 | When 2–3 specialists *are* justified | Very high | Constraint, not persona |
| 3 | Supervisor vs graph router vs sequential handoff | Very high | Bottleneck honesty |
| 4 | Handoff packet vs shared state | Very high | Contract + collisions |
| 5 | CrewAI-demo fail mode | High | What the demo hid |
| 6 | Multi-agent evals | High | Extra metrics beyond Ch. 11 |
| 7 | Duplicate actions / who may write | High | Single writer, locks, ids |
| 8 | A2A vs MCP vs in-process | Medium–high | Working knowledge |
| 9 | Cost and latency multiplication | Medium–high | Envelope per agent |
| 10 | Framework nouns (handoffs, crews, ADK sub-agents) | Medium | Translate to the pattern |

**MARKET OBSERVATION:** JDs that say “multi-agent” often mean “tool-using agent.” Treat the phrase as a prompt to *reduce*, then add back only what you can defend.

---

## How to study this chapter

Cover the answer. Speak 30 seconds, then 2 minutes, then the deep cut. Write a six-part card. Do not memorize crew names — “swarm,” “supervisor,” “A2A mesh” are the same test: **did you earn the second agent?**

---

## The one diagram you should be able to draw

```
User goal
   │
   ▼
Unknown step sequence? ──NO──► Deterministic workflow (Ch. 11)
   │ YES
   ▼
One bounded agent (tools T, policy P, caps, HITL)
   │
   ▼
Is a second mind forced by a real constraint?
   │
   ├─ NO  → STOP. You are done. This is the senior answer.
   │
   └─ YES → 2–3 specialists, not 5
             constraint is one of:
               disjoint tool catalogs
               disjoint models
               disjoint trust / write rights
               true parallel independent work
             ┌─────────────────────────────────────┐
             │ router (code or one supervisor)     │
             │ each specialist: own tools + budget │
             │ ONE writer for any side effect      │
             │ handoff packet XOR shared state     │
             │ A2A only across vendor/trust edge   │
             └─────────────────────────────────────┘
```

Most production “multi-agent” systems belong on the STOP branch, or are a **graph with LLM nodes** wearing agent costumes.

---

## Production multi-agent checklist (say this unprompted)

If you still ship more than one agent, you owe everything in Chapter 11 **per agent**, plus:

1. **Written justification** — the constraint that a single agent failed (eval evidence, not a blog).
2. **One router** — code, a tiny classifier, or one supervisor. Not a fully-connected chat.
3. **Disjoint catalogs** — specialists must not share overlapping write tools.
4. **Single writer** — only one identity may mutate a given resource in a run.
5. **Handoff contract** — goal, evidence, authority, already-done, budget remaining, accountability.
6. **Per-agent envelopes** — steps, tokens, $, wall time. A specialist cannot spend the fleet.
7. **Extra evals** — misroute rate, duplicate-action rate, handoff completeness, supervisor wait.
8. **Kill switch** — disable a specialist or freeze writes without taking the product down.

Missing the justification is a mid-level ceiling on an Agentic loop. Missing the single writer is an incident.

---

## Q1. When should you *not* use multi-agent?

**Why they ask.** This is the discriminator. They have been burned by crews that cost 8×, loop, and file three tickets. They want the default to be *no*.

**What they expect.** A hard default of one workflow or one agent. A short blacklist. What you would build instead. Cross-link to Chapter 11 without reciting it.

**Answer structure keywords.** one mind · overlapping tools · known SOP · eval surface · cost × N · personas ≠ specialties · graph first.

**30-second.** I do not start multi-agent. If the steps are known, it is a graph with LLM nodes. If the steps are unknown but the tools fit one catalog, it is one bounded agent. Multi-agent is unjustified when specialists would share tools, share a model, share write rights, and only differ by a system prompt. That is prompt theater. It multiplies tokens, latency, and the eval surface without adding a capability.

**2-minute.** Blacklist:

1. **Known SOP.** Invoice coding, refund-under-policy, KYC packet. Chapter 11 graph. Personas do not make an SOP “agentic.”
2. **One catalog.** If every “specialist” would call `search`, `get_ticket`, `draft`, you have one agent with a good prompt and a verifier node — not three agents.
3. **Tight SLA or cheap task.** Each extra model call is a distribution on latency and a multiple on $. A “writer + critic” on an FAQ is how you miss p95.
4. **You cannot eval one agent yet.** Two agents do not create measurement. They hide the lack of it.
5. **The PM asked for a ‘crew’ on the homepage.** Product word. Translate: one copilot, maybe a research pocket.

Instead: workflow; or one agent; or plan-and-execute with a critic *function* (cheap model, no tools) rather than a critic *agent* with a second tool belt.

**Senior / deep.** The hidden “do not” is **correlated failure**. Five agents on the same model, same retrieval, same poisoned document, fail the same way — louder, and with a debate that looks like diligence. Diversity of *prompts* is not diversity of *evidence*.

Another: **accountability fog.** When a wrong email goes out, “the crew decided” is not an audit answer. One writer identity, one trace parent, one owner.

A third: **org cosplay.** Mapping departments (legal, finance, eng) onto agents copies a meeting, not a system. If legal must sign, that is HITL, not a “legal agent” with `send_email`.

Interview-grade test: delete all but one agent. If task success on the golden set barely moves, you never needed the rest. I have run that ablation. It is the argument.

**Weak answer.** “Multi-agent is more powerful because specialists collaborate, so I’d use a supervisor with CrewAI.”

**Mistakes.**

- Treating “multi-agent” as the definition of production agents.
- Using Chapter 11’s *when not to use an agent* list and stopping — they want the extra *N minds* argument.
- Saying “it’s more modular” without a module boundary that is actually a process or a trust boundary.
- Jumping to A2A.

**Follow-ups + strong replies.**

- *“Isn’t a critic a second agent?”* — A critic that only scores text is a function. I give it no tools. The day it can also search and write, it is a second mind and I need a reason.
- *“Our design doc already has five agents.”* — I collapse to a graph, keep one agentic pocket, and put the rest of the names in the prompt or in node labels for the demo. Same UX, operable system.
- *“Won’t a smarter model remove the need for specialists?”* — Smarter models reduce *routing* errors inside one catalog. They do not merge two trust domains or give you free parallelism.

**Example.** Support “crew”: triage, knowledge, ticket, closer. All four had Jira + Confluence tools. We shipped one agent with 7 tools and a graph: classify → retrieve → draft → HITL close. Success up, cost down, traces readable. The crew was a slide.

---

## Q2. When are 2–3 specialists actually justified?

**Why they ask.** After you refuse the five-agent diagram they check you are not a zealot. Seniors can name the *few* constraints that earn a second mind.

**What they expect.** Three or four crisp justifications, a max of 2–3 specialists, and what you still refuse (open mesh, shared writes).

**Answer structure keywords.** disjoint tools · disjoint model · disjoint trust · true parallelism · 2–3 not 7 · eval proof.

**30-second.** I add a specialist when one of four things is true: the tool catalogs clash (code interpreter vs SAP vs web), the models should differ (small SQL head vs large writer), the trust domains must not share credentials, or independent work can run in parallel with a merge step. I still cap at two or three. I still wrap them in a graph. I still want an ablation that shows the split beat a single agent on task success or on risk, not on “it felt organized.”

**2-minute.** Justification table:

| Constraint | Why one agent fails | Shape |
| --- | --- | --- |
| **Disjoint tools** | 25+ overlapping tools destroy selection (Ch. 11 Q11) | Split catalogs; router by intent |
| **Disjoint model** | Code/SQL wants a different pin than prose | Specialist pin + shared router |
| **Disjoint trust** | Read-research must not hold `place_order` | Separate identities, one writer |
| **True parallel** | Three independent docs, wall-clock matters | Map-reduce, merge, then one writer |

Not justifications: “clearer prompts,” “the paper used a society of mind,” “CrewAI’s template has these roles,” “the customer said agentic workforce.”

How I prove it: take the golden set, run single-agent baseline, run 2-specialist, compare task success, misroute, duplicate writes, $/success, p95. If the split only wins on a slice (e.g. “hard SQL”), *route that slice* and leave the rest on one agent.

**Senior / deep.** The interesting case is **trust**, not intelligence. A research specialist with retrieval-only MCP tools and a fulfillment specialist that can write — with HITL — is a security architecture. The supervisor must not be a confused deputy that forwards raw tool results as orders.

**Partial observability.** If specialist B cannot see what A already did, you get duplicate POs. The split creates a state problem you did not have. Budget the handoff packet (Q4) as part of the justification, not as an afterthought.

**Org ownership.** Two teams owning two catalogs (data platform vs core banking) is a reason for two *servers* (Chapter 12) and maybe two agents. It is not a reason for five conversational personas inside one repo.

I almost never justify more than three. The fourth agent is usually a verifier that should be code, or a “manager” that should be the graph.

**Weak answer.** “I’d use specialists for research, writing, and review because that’s how humans work.”

**Mistakes.**

- Listing roles instead of constraints.
- Parallelism that isn’t: writer waiting on researcher is sequential, so a pipeline, not a crew.
- Splitting then giving everyone the full tool belt “for flexibility.”
- No baseline.

**Follow-ups + strong replies.**

- *“What about 10 tools — split or retrieve schemas?”* — Retrieve top-K schemas first (Ch. 11). Split only if catalogs are semantically hostile (shell vs payments).
- *“Can specialists be the same model?”* — Yes if the split is tools or trust. Then you are paying extra tokens for isolation, which can still be worth it.
- *“When did a split lose?”* — Have a story: research+writer crew duplicated citations and contradicted itself; one agent with a notebook state won.

**Example.** Diligence assistant. Constraint: 40-page PDFs (extraction model) vs memo prose (large model) vs a read-only filings MCP vs a CRM write. Design: extractor worker (batch, no chat), research agent (filings + search, cap 8), writer agent (no search, no CRM write), graph merge, HITL, then `update_crm` as a graph node — not an agent. Three minds, one writer, ablation on 40 memos.

---

## Q3. Supervisor and specialists — how should the topology work?

**Why they ask.** “Supervisor pattern” is the phrase on JDs. They want you to know it *and* to name the bottleneck.

**What they expect.** Router options: code, classifier, one supervisor LLM. Specialists as workers with narrow tools. Why a fully-connected group chat is a fail. Where HITL sits (outside the debate).

**Answer structure keywords.** router · supervisor bottleneck · star not mesh · worker graphs · budget isolation · no group chat.

**30-second.** I use a star, not a mesh. A router — preferably code or a small classifier — picks one specialist. That specialist runs a bounded loop and returns a packet. A supervisor LLM is only needed when the route depends on unstructured observations I cannot enumerate. The supervisor does not hold write tools. Specialists do not talk to each other without going through the router. Group chat is a demo of entropy.

**2-minute.** Three routers, increasing cost:

1. **Deterministic / rules.** Intent classifier, ticket type, file MIME, “if SQL keywords → sql_agent.” Cheapest, most auditable. Default.
2. **LLM supervisor, no tools.** Sees the user goal + specialist cards (name, when to use, when not). Emits `route: sql | research | done`. One call. Then the worker runs.
3. **LLM supervisor with tools.** Almost always a mistake — it becomes a fourth agent that competes with specialists. If it must exist, tools are `delegate`, `ask_user`, `finish` only.

Workers should themselves be **graphs or tiny ReAct loops**, not recursive supervisors. Hierarchical “manager of managers” is how you get 40 LLM calls before a single retrieval.

Caps: supervisor has a *handoff* cap (e.g. 4), each worker has a *step* cap. The product envelope is the sum, enforced outside.

**Senior / deep.** **Supervisor bottleneck** is the production failure mode. Every turn waits on a large-model route. p95 dies. Mitigations: cache routes for a session (“this ticket is SQL until evidence otherwise”), skip the supervisor when confidence of the classifier is high, run independent workers in parallel when the plan is a list of unrelated subgoals.

**Mode collapse.** Supervisors love one specialist (“research” for everything). Eval must include a **misroute** slice, not only final BLEU-of-memo.

LangGraph: a supervisor node with conditional edges, or `Send` to workers, is this pattern. OpenAI Agents SDK **handoffs** are a transfer of control, not a chat room. Google ADK sub-agents and Microsoft Agent Framework workflows are the same star if you use them that way. CrewAI hierarchical process is the same idea with more role flavor — I still flatten it.

**Weak answer.** “A supervisor agent delegates to specialist agents and they collaborate until done.”

**Mistakes.**

- Fully-connected AutoGen-style group chat in production.
- Supervisor with the union of all tools.
- Recursive supervisors.
- No route cache, so every observation re-plans the org chart.

**Follow-ups + strong replies.**

- *“Who talks to the user?”* — One face: the host. Workers return packets; the host streams status. Users should not have to know which specialist is on.
- *“Can specialists call each other?”* — Only via the router, so the trace stays a tree and authz stays central. Peer-to-peer is A2A territory and a different threat model (Q8).
- *“What if the supervisor is wrong?”* — Worker can return `WRONG_SPECIALIST` with evidence; one re-route allowed; then escalate. Infinite re-route is a loop (Ch. 11 Q3).

**Example.** IT copilot. Classifier: password-reset → workflow (no agent). Laptop-unknown → research specialist (`search_kb`, `get_device`, cap 8). Procurement-ish → procurement graph, not a specialist. Supervisor LLM only on the 15% “other.” Writes (`create_ticket`) are graph nodes after HITL. Supervisor never saw ServiceNow credentials.

---

## Q4. Handoff vs shared state — how do agents share work?

**Why they ask.** This is the real design question hiding under “how do they communicate?” Wrong choice produces lost context or duplicate writes.

**What they expect.** Two mechanisms, when each wins, a handoff packet schema, and collision control for shared state.

**Answer structure keywords.** handoff packet · transfer of control · blackboard · single writer · already-done · locks · TOCTOU.

**30-second.** A **handoff** transfers the turn and a packet: goal, constraints, evidence, already-done ids, budget left, who is accountable. Clean ACL, easy audit, risk of information loss. **Shared state** is a blackboard every worker reads and writes — a LangGraph state object, a ticket, a notebook. Better for tight iteration, risk of races and confused deputies. I pick one as the source of truth. I do not let agents “just talk.”

**2-minute.**

| | Handoff | Shared state |
| --- | --- | --- |
| Control | One active agent | Many can read; one writer lock |
| Memory | Packet must be complete | Workers see the same notebook |
| Authz | Easy: next identity only | Hard: who may patch which field |
| Failure | Lossy if packet is prose | Collisions, stale reads |
| Fits | Different trust domains, A2A, sequential specialties | Tight graph, parallel map with merge |

**Handoff packet** (interview-grade fields): `goal`, `success_criteria`, `constraints_policy`, `evidence[]` (ids + hashes, not 40-page dumps), `already_done[]` (resource ids, idempotency keys), `budget_remaining`, `authority` (what the next agent may do), `accountability` (user, tenant, approver), `trace_id`.

Prose (“hey writer, make it good”) is not a packet. The writer will re-research and duplicate.

**Senior / deep.** Hybrid is what production actually is: **shared structured state** (the case file) plus **handoff of the write token**. Like a checkout lock. Agent A releases `writer_lock` on `case:123` when it returns. Agent B may not call write tools without the lock.

**TOCTOU.** Approving “refund $20” in the packet and executing $200 because the specialist re-sampled args — same Chapter 11 HITL bug. Execute the *approved payload*, or re-approve.

**Size.** Packets that dump full tool transcripts poison the next context (and are an injection highway). Store raw observations in the trace store; put pointers in the packet.

OpenAI SDK handoffs, LangGraph `Command(goto=...)`, ADK transfer — all are handoff. LangGraph state / MAF shared workflow state — blackboard. Name the primitive, then the contract.

**Weak answer.** “Agents communicate through natural language in a shared chat history.”

**Mistakes.**

- Shared chat log as the only state (unbounded, unauthzable, un-evalable).
- Handoff without `already_done` → duplicate emails.
- Every agent can write every field.
- Putting secrets in the packet (same energy as MCP01).

**Follow-ups + strong replies.**

- *“Blackboard vs event log?”* — Event log (append-only actions) plus a projection (current case) is the grown-up blackboard. Replayable. I like it when writes matter.
- *“What does the user see during handoff?”* — Status: “research complete, drafting.” Not the packet.
- *“Can the specialist refuse the handoff?”* — Yes: `blocked` + missing fields. Router may fill or ask the user. That is better than hallucinating the missing id.

**Example.** Research agent finishes with packet: `already_done: [doc:88, doc:91]`, `claims: [...]` with passage ids, `authority: draft_only`. Writer never got `search` or `send_email`. CRM write stayed a graph node with the packet’s claim list as the payload to HITL.

---

## Q5. The “five agents” trap and the CrewAI-demo fail mode

**Why they ask.** They have seen the demo: Researcher, Writer, Editor, Critic, Manager, sequential process, a blog post appears. They want you to autopsy it.

**What they expect.** What the demo hides (cost, loops, no eval, fake specialties). What you would ship instead. Fairness: crews are fine for a prototype.

**Answer structure keywords.** personas ≠ tools · sequential crew = workflow with tax · manager bottleneck · no trajectory eval · prototype only.

**30-second.** Five agents that share a model and a search tool are one agent wearing hats. A sequential CrewAI process is a workflow that pays a full LLM call at every hop and has no durable HITL. The demo fail mode is optimizing for a screenshot of collaboration. I will prototype in a crew if the team already knows the UX. I will not put it in front of a write path. I collapse hats into nodes, keep one agentic pocket, measure.

**2-minute.** Autopsy of the canonical demo:

- **Personas, not specialties.** Editor and critic have no unique tools. They are prompts. Make them grader functions.
- **Sequential process.** Researcher → writer → editor is a graph. Calling each an agent adds routing text and a chance to drop ids.
- **Manager.** Rephrases the user, becomes the bottleneck (Q3), and often re-does work.
- **Shared tools.** Everyone can search *and* write the doc, so you get four drafts and a race.
- **No caps that match production.** Demos love long chats.
- **Eval is “read the blog post.”** No task rubric, no duplicate-action metric, no $/success.
- **State is the transcript.** Restart = redo all side effects unless you were lucky.

CrewAI’s value is *speed to a role-play prototype* and a mental model for non-engineers. Hierarchical/sequential processes map to supervisor/pipeline. That mapping is the interview. The fail is treating the library as a control plane (no substitute for schema validation, idempotency, HITL, traces). Chapter 11 said this; here you apply it to *N*.

**Senior / deep.** Fail modes I have actually had to unwind:

1. **Debate as delay.** Critic and writer ping-pong style comments until the cap. No progress metric.
2. **Responsibility laundering.** Nobody owns the final bytes sent to the API.
3. **Prompt injection amplifier.** One poisoned page in research becomes “instructions” the editor treats as style guide (intent-flow subversion, Chapter 12). More agents = more readers of untrusted text.
4. **Cost cliff.** Five verbose agents on a 20-page PDF. Finance notices before quality does.

AutoGen group chat is the same trap. Microsoft Agent Framework is the 2026 successor path; I still design a star + graph, not a salon.

**Weak answer.** “CrewAI isn’t production-ready.” True as a vibe, empty as a design. Say *which* control is missing.

**Mistakes.**

- Snobbery without an alternative architecture.
- Rewriting the demo as five LangGraph nodes that still call five LLMs for hats.
- Claiming you “would add memory” as the fix.

**Follow-ups + strong replies.**

- *“The JD lists CrewAI.”* — I can build a crew for the take-home. In the design round I say what I would throw away before prod: personas without tools, group chat, writes from more than one role.
- *“Is a writer+critic ever right?”* — Critic as a tool-less grader on a rubric, maybe. Second full agent, almost never for short text.
- *“Multi-agent papers show gains.”* — On benchmarks with disjoint skills or genuine debate on answers. Production SOP work is not HumanEval. I want *our* ablation.

**Example.** Marketing asked for a “content crew.” We shipped: outline node (small model) → one research ReAct (cap 6) → draft node → rubric grader → HITL editor in the CMS. Four graph nodes, one agent. They still called it a crew in the all-hands. Fine. The on-call runbook named a graph.

---

## Q6. What are the bottlenecks — and how do you keep N from exploding cost and latency?

**Why they ask.** Multi-agent is a multiplier. They want envelopes and topology, not “we’d monitor LangSmith.”

**What they expect.** Supervisor wait, sequential hops, context copying, duplicate tool reads, fan-out storms. Controls: route cache, parallel only when independent, per-agent budgets, shared retrieval cache.

**Answer structure keywords.** supervisor wait · hop tax · duplicate retrieval · fan-out · per-agent envelope · $/success.

**30-second.** Bottlenecks are the supervisor’s extra call every turn, sequential handoffs that could have been a pipeline, each specialist re-retrieving the same docs, and unbounded fan-out (“ask all five”). I put a budget on each agent and on the run, I cache retrieval by query hash, I parallelize only independent work, and I optimize **cost per successful task**, which usually argues *against* N.

**2-minute.** Levers:

1. **Do not go multi-agent** (Q1). Still the biggest win.
2. **Router cost.** Classifier ≪ supervisor LLM. Cache the route for the ticket.
3. **Hop tax.** Each handoff re-encodes the packet. Prefer one worker finishing over three polite transfers.
4. **Shared caches.** Retrieval, GET tools, prompt prefixes — keyed by tenant. Specialists must not each fetch the PDF.
5. **Parallelism with a join.** Independent reviews yes; “research while writing” no.
6. **Envelopes.** `research: $0.20 / 8 steps`, `writer: $0.10 / 2 calls`, run: `$0.40 / 45s`. Kill switch.
7. **Small models** for routing and extraction; large only where the ablation says so.

Show the same dashboard as Chapter 11, with `agent_name` as a dimension. A specialist that is 8% of successes and 60% of spend gets deleted or demoted to a function.

**Senior / deep.** **Fan-out storms** look like helpfulness: supervisor broadcasts to all specialists “in case.” That is N-fold spend and a merge nightmare. Explicit map over a list of *items*, not over a list of *roles*.

**Context copying.** Five agents with the full transcript is five times the prefill. Packets with ids beat transcripts.

**Head-of-line.** A slow specialist blocks the user even if the answer is already in another worker. Timeouts per worker, partial results, user-visible degraded mode.

Cloud knobs (Bedrock / Foundry / Vertex quotas, PTU) still do not replace application envelopes (Chapter 15). Multi-agent without caps is how you 429 the whole tenant.

**Weak answer.** “We’d set max_iter on each agent to 10.”

**Mistakes.**

- One global budget the supervisor can spend on retries.
- Parallel tool calls that are actually the same GET five times.
- Optimizing tokens per *call* instead of per successful *task*.

**Follow-ups + strong replies.**

- *“User wants all specialists to review.”* — That is a parallel map with a merge rubric, capped at 3, read-only. Not a debate club.
- *“Supervisor is the quality win.”* — Show me the slice metrics. If it only wins on 10% hard tickets, route those.

**Example.** Research crew averaged $1.80 because each persona fetched the same 8 URLs. Fix: one `fetch` cache in the host, research agent only, writer sees passage ids. $/success dropped without touching the model.

---

## Q7. How do you evaluate a multi-agent system?

**Why they ask.** Chapter 11 evals plus the extra failure modes N creates. “LLM-as-judge on the final memo” is the weak answer again.

**What they expect.** Task success first. Then misroute, handoff completeness, duplicate-action, supervisor hops, $/success. Ablation vs single agent. Traces with a parent span per agent.

**Answer structure keywords.** task success · misroute · duplicate-action · handoff completeness · hops · $/success · ablation.

**30-second.** I still grade **task success** against a rubric. Then I grade the *process*: did we route to the right specialist, was the packet complete, did two agents mutate the same resource, how many hops, what did a success cost. I will not ship a crew that wins the memo judge but double-sends email. I keep a single-agent baseline on the same golden set so multi-agent has to earn its keep.

**2-minute.** Extra metrics on top of Chapter 11:

| Metric | Question |
| --- | --- |
| **Misroute rate** | Wrong specialist / unnecessary supervisor hop |
| **Handoff completeness** | Packet has ids, constraints, already-done |
| **Duplicate-action rate** | Same write intent ≥2 in one run |
| **Cross-talk** | Specialist used a tool not in its catalog (policy fail) |
| **Supervisor wait / hops** | Latency tax |
| **Abort-with-partial** | Stopped cleanly vs silent drop |
| **$/success vs one-agent** | The business case |

Offline: same frozen tasks as the single-agent set, plus a **routing set** (labeled intents). Mock tools so duplicates are visible. Online: shadow the crew against the one-agent product on a slice of traffic.

Judges: deterministic checks for routing, tools, duplicates. LLM-as-judge only on the final artifact, calibrated (Chapter 17), never as the only gate.

**Senior / deep.** Credit assignment is worse with N. Tag spans `router`, `agent:research`, `agent:writer`, `handoff`, `write`. Quality review labels the *span*. Otherwise you will “improve the writer prompt” when the researcher dropped the citation ids.

**Lucky crews.** Final answer correct, trajectory illegal (writer searched after losing authority; critic called `send`). Trajectory fail = fail. Same as Chapter 11, enforced harder because more hands.

**Handoff completeness** can be schema-validated. If `already_done` is empty after a research agent that called `fetch`, that is an automatic fail — no judge required.

**Weak answer.** “We’d LLM-as-judge the conversation quality.”

**Mistakes.**

- No single-agent baseline.
- Golden answers that assume one path through the crew.
- Ignoring safety evals (injection now has more readers).

**Follow-ups + strong replies.**

- *“How big a set?”* — Routing set can be hundreds of short intents. Full tasks: 30–50 critical, same as Ch. 11, with duplicates and misroutes *planted*.
- *“Crew wins quality, loses cost.”* — Route only the hard slice. Publish blended $/success.

**Example.** Writer+researcher vs one agent. Success 78% vs 74%. Duplicate citation fetches 1.8 vs 0.2. $/success 4×. We shipped one agent plus a tool-less grader. The 4-point quality gap was not worth it except on the “long PDF” slice, which we split later (Q2 example).

---

## Q8. A2A vs MCP vs in-process multi-agent (working knowledge)

**Why they ask.** Google’s Agent2Agent is the other 2026 standard. Mixing it with MCP or with LangGraph handoffs is a common fail. They want literacy, not a protocol recitation.

**What they expect.** MCP = tools/data (Chapter 12). A2A = agent-to-agent across trust or vendor boundaries. In-process handoff = your graph. When *not* to use A2A.

**Answer structure keywords.** A2A · Agent Card · task · MCP southbound · in-process first · Linux Foundation / AAIF · trust boundary.

**30-second.** If both specialists are ours in one runtime, I use a graph edge or an SDK handoff — not a protocol. MCP is how an agent uses tools and data. A2A is how two opaque agents, possibly different vendors, discover each other (Agent Card) and collaborate on a **task**. I would not use A2A to call `get_order`, and I would not use MCP as a negotiation protocol between two firms.

**2-minute.** Stack:

```
User ↔ our host
         │  in-process handoff / graph     (same trust)
         │  A2A task                       (foreign agent)
         ▼
    our agent  ──MCP──►  tools, resources, prompts
```

A2A (originated at Google, donated to the Linux Foundation in 2025, 1.0 in 2026, moving into the Agentic AI Foundation alongside MCP) is task-oriented: discover capabilities via an Agent Card, send a task, get artifacts/status. It is complementary to MCP, not a rival. Clouds have been wiring it in (AgentCore, Foundry, Gemini Enterprise Agent Platform / ADK). I describe the *boundary* before the product name.

When A2A is justified: a partner’s collections agent, a vendor’s analysis agent we do not run, a marketplace of agents with separate identity. When it is not: two Python classes in one repo.

**Senior / deep.** A2A does not give you authorization, HITL, or evals. It gives you a **wire**. You still need: mutual TLS / identity, audience-restricted tokens, a task contract as strict as the handoff packet (Q4), audit, and a deny-by-default catalog of *which* foreign agents this host may call. Treat Agent Cards like tool descriptions — untrusted prompt text — pin them.

**Do not mesh.** An open A2A mesh of internal specialists is the five-agent trap plus a network. Internal star; A2A at the edge.

If they go protocol-deep: tasks, artifacts, status, Agent Card — then return to “we only cross that wire at a trust boundary.”

**Weak answer.** “A2A is Google’s MCP” or “we’d use A2A for all specialist calls.”

**Mistakes.**

- Using A2A as a tool bus.
- Using MCP to pretend a whole foreign agent is a function without a task/accountability contract.
- Reciting the spec instead of the boundary.

**Follow-ups + strong replies.**

- *“Which do I implement first?”* — MCP for tools, always. In-process graph for our specialists. A2A when a second product or vendor is real.
- *“Agent Card vs MCP tools/list?”* — Card advertises an *agent* (skills, endpoint, auth). `tools/list` advertises *functions*. Different layer.
- *“Can A2A replace the supervisor?”* — Not inside one app. A foreign agent is a worker with a slower, less trusted interface.

**Example.** Our underwriting agent uses MCP for the policy KB. A third-party fraud vendor exposes an A2A skill `score_application`. We send a redacted task, log the artifact, HITL if score > threshold. The vendor never got VPC MCP. Our “research” and “memo” workers stayed in-process.

---

## Q9. Who writes? Duplicate actions, failure, and recovery across agents

**Why they ask.** N minds plus retries is how you get two refunds. This is Chapter 11 Q7 with extra hands.

**What they expect.** Single writer per resource, idempotency keys in the packet, locks, compensation ownership, what the user sees.

**Answer structure keywords.** single writer · idempotency · lock · compensate · already_done · poison task.

**30-second.** Only one agent — better: only one **graph node** — may mutate a given resource in a run. Every write carries an idempotency key stored in shared state before the call. On failure I look, then retry the same key, or compensate. Other specialists are read-only. If two specialists need to write, they queue through one executor. I never restart the whole crew from turn zero.

**2-minute.** Rules:

- **Write owner** declared in the graph, not negotiated in prose.
- **Lock** on the case id for the run (or a lease with TTL).
- **already_done** in state/packet includes resource ids.
- **Retries** in the tool wrapper (Ch. 11), not by asking a second agent to “try.”
- **Compensation** listed next to the write tool; the *executor* runs it, not a “fixer agent” improvising.
- **User status** is host-owned: `in_progress / waiting / needs_you / failed_partial`.

Poison runs (5 failures) go to a dead letter with the parent trace. A human or a replay job, not a new specialist.

**Senior / deep.** **Two-phase:** specialist proposes a write intent object; the executor commits. That is how you keep HITL and single-writer when the proposer is a model.

**Identity.** Each specialist’s runtime identity should lack the other’s write IAM. Defense in depth: even a prompt injection in research cannot call `place_po` if the token cannot.

**Partial multi-agent failure.** Research succeeded, writer crashed. Resume: do not re-fetch (cache + already_done), re-run writer only. Durable execution of the *graph* matters more than durable chatter of the crew.

**Weak answer.** “Each agent would retry and then the supervisor would reconcile.”

**Mistakes.**

- Shared write tools on every specialist.
- Compensation invented by the model.
- Checkpointing the transcript but not the resource ids.

**Follow-ups + strong replies.**

- *“Two resources, two writers?”* — Saga in the graph: hold inventory (executor A), update order (executor B), compensate A if B fails. Agents propose; executors apply.
- *“A2A foreign agent wrote twice.”* — Your idempotency key must be part of the task; you reconcile on their artifact id. If they lack idempotency, they are not a write partner.

**Example.** Order-change: research specialist (read), writer drafts a change set, executor node `apply_change` with key `chg:{order}:{hash}`. Research died after apply? Checkpoint says applied; resume skips. User never saw two emails because `send` was a later node with its own key.

---

## Q10. Design a 2-specialist system on the whiteboard (and refuse a third)

**Why they ask.** Synthesis. FDE / architect / senior agentic. They want a reduction, a topology, a packet, evals, and a “no” to the extra box.

**What they expect.** Clarify the constraint that earns N=2. Draw a star or a pipeline, not a mesh. Place HITL and writes outside the agents. Name metrics. Decline agent #3.

**Answer structure keywords.** constraint · star · packet · single writer · caps · ablation · refuse the critic-agent.

**30-second.** I’d confirm why one agent failed — catalog clash, trust, or parallelism. I’d draw a router, two specialists with disjoint tools and budgets, shared case state, one write executor with HITL, traces under one parent id. I’d eval against a one-agent baseline. A third “critic agent” would be a tool-less grader node. A2A only if a foreign system appears.

**2-minute.** Spoken skeleton:

1. **Clarify.** What is the user task, write vs read, SLA, systems of record, who is accountable.
2. **Baseline.** Graph, or one agent. Say it.
3. **Earn N=2.** One sentence constraint.
4. **Diagram.** User → host → router → {A | B} → merge → HITL → write node.
5. **Contracts.** Tool catalogs, packet schema, locks, caps.
6. **Failure.** Tool 500, misroute, injection in retrieved text, budget kill.
7. **Eval.** Task success, misroute, duplicates, $/success, safety.
8. **Refuse extras.** No manager-of-managers, no group chat, no A2A mesh.

**Senior / deep.** Offer two options: (A) one agent + retrieved tool schemas, (B) two specialists. Recommend A unless the constraint is trust or true parallel. That optionality is the senior tell.

Map workers to Foundry Agent Service / AgentCore / Gemini Agent Platform **as runtimes**, not as an excuse for five hosted agents. Identity still OBO/IAM per specialist (Chapter 15). MCP still southbound (Chapter 12).

**Weak answer.** Walks to the board and draws five named personas before asking what the product does.

**Mistakes.**

- Starting with CrewAI.
- Writes inside both specialists.
- No eval.
- A2A between internal workers.

**Follow-ups + strong replies.**

- *“PM wants a visible ‘team’ in the UI.”* — Animate node names in the UX. Keep one writer in the runtime.
- *“Legal wants a legal agent.”* — Legal is HITL + a policy retrieval tool. Not `send_letter`.
- *“This worked in a hackathon.”* — Hackathons optimize for a story. Production optimizes for a ship bar.

**Example.** “Enterprise research-to-CRM.” Option B: research specialist (search + KB, cap 8, $0.25), writer specialist (no search, draft memo, cap 2), merge, manager HITL, `update_crm` executor. Option A (recommended first): one agent with those tools retrieved top-K, same HITL. We only split when eval showed tool oscillation between CRM write and web search. That sentence is the close.

---

## Rapid-fire (30–45 seconds each)

| Prompt | Answer |
| --- | --- |
| Default N? | Zero (workflow) or one. Then earn two. |
| When is two justified? | Disjoint tools, models, trust, or true parallel work — with an ablation. |
| Five-agent trap? | Personas that share tools and a model, sequential hats billed as a crew. |
| CrewAI in prod? | Prototype UX; not the control plane. Collapse to a graph + one loop. |
| Supervisor’s tools? | `delegate`, `ask_user`, `finish`. Not the union of worker tools. |
| Handoff packet? | Goal, evidence ids, already-done, authority, budget, accountability, trace id. |
| Shared chat as state? | No. Unbounded, unauthzable, lossy. |
| A2A vs MCP? | A2A = agents across a trust/vendor edge. MCP = tools/data. In-process otherwise. |
| Extra evals? | Misroute, duplicate-action, handoff completeness, hops, $/success vs one agent. |
| Who may write? | One executor identity per resource per run. |
| Critic? | Tool-less grader. A critic with tools is another agent and needs a constraint. |
| Foreign partner agent? | A2A task + redaction + audit + HITL. No partner MCP on your VPC by default. |

---

## Weak vs strong posture (memorize the posture, not the paragraph)

| Weak | Strong |
| --- | --- |
| “A crew of specialists” | “One agent or a graph until a constraint forces a split” |
| “Supervisor delegates and they collaborate” | “Star topology; supervisor is a router; workers don’t mesh” |
| “They share the conversation” | “Handoff packet or structured state; single writer lock” |
| “CrewAI hierarchical process” | “Prototype; production is a graph with caps and HITL” |
| “We’ll use A2A between our agents” | “In-process handoff inside; A2A at the vendor/trust edge” |
| “LLM-as-judge on the transcript” | “Task success, misroute, duplicates, $/success, ablation” |
| “More agents = more reliable” | “More agents = correlated failure, more injection readers” |

---

## A complete example you can reuse

**Setting.** Insurer wants an “AI claims team”: intake, coverage, fraud, reserves, customer-comms — five agents.

**Wrong design.** CrewAI five personas, all with claims-core + email + KB tools, group chat, manager agent, `set_reserve` in the catalog.

**Right design.**

1. **Workflow first.** Intake → coverage retrieve → recommendation → HITL adjuster → core write. That is Chapter 11.
2. **One agentic pocket:** “gather missing evidence” (search, fetch attachment, ask insured), cap 8, no writes.
3. **Earn a second specialist only if** fraud scoring is a *different system* (vendor A2A or separate model pin) with no email tools.
4. **Refuse** reserves agent, comms agent, manager agent. Reserves = core API + two-person HITL. Comms = draft node + HITL send. Manager = the graph.
5. **State:** case file in the workflow checkpointer; handoff packet into the evidence agent; `already_done` attachment ids.
6. **Eval:** cycle time, recommendation agreement with adjusters, unauthorized-tool rate (must be 0 on reserve/email), $/claim vs the one-pocket baseline.
7. **Close:** “You do not have a claims team of agents. You have a claims workflow with at most two bounded minds, and the adjuster still owns money and letters.”

That close is what a 2026 interviewer is listening for.

---

## Map to the rest of the handbook

- When not to agent, loops, tools, HITL, single-agent evals: [11-agentic-ai.md](11-agentic-ai.md)
- MCP southbound tool bus, poisoning, gateway: [12-mcp.md](12-mcp.md)
- Cloud runtimes (AgentCore, Foundry Agent Service, Gemini Enterprise Agent Platform): [15-cloud-ai.md](15-cloud-ai.md)
- Trace spans, cost/task, judges: [17-llmops.md](17-llmops.md)
- Excessive agency, injection: Chapter 19
- Full designs: Chapters 20–21

Drill Q1, Q2, Q5, Q4, Q7 out loud. If those are clean, you survive — usually by *removing* boxes. Then add Q8 so A2A does not ambush you.
