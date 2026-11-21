# 24 — Behavioral Interviews

**What this chapter is for:** so your stories survive a senior panel. “Tell me about yourself” is Chapter 25. This chapter is everything else they use to decide whether they can trust you on a team.

Behavioral rounds in 2026 AI loops are not a rest stop between system design and coding. They are where the panel tests judgment: will you overclaim, panic under ambiguity, silently ship an unsafe agent, or blame the last company.

---

## 1. STAR, used properly

STAR is not a format you announce. It is how you stop rambling.

| Letter | Meaning | Time | Content |
| --- | --- | --- | --- |
| **S** | Situation | 15–20s | Context a stranger needs. No company history. |
| **T** | Task | 10–15s | Your job, the constraint, what “done” meant |
| **A** | Action | 50–70s | What **you** did, in order, with trade-offs |
| **R** | Result | 20–30s | Number, ship bar, or honest qualitative + what you learned |

Total: **90–150 seconds**. Then stop. If they want more, they will ask.

Speak Action in first person. “I wrote the eval gate” is a story. “We aligned stakeholders and leveraged synergies” is a rejection.

### STAR on a card (fill this once per story)

```
Prompt this story covers:
S: When / where / users (one sentence)
T: I needed to ___ under constraint ___
A: I did 1) ___ 2) ___ 3) ___
   I chose not to ___
R: Metric / outcome:
   What I learned:
   What I would do differently:
Honest boundary (what was not mine):
```

---

## 2. Five ways this round dies

These match Chapter 23 because interviewers hear the same failure modes in project defense and behavioral.

| Fail mode | What it sounds like | What to do instead |
| --- | --- | --- |
| **Overexplaining** | 4 minutes of architecture before a result | Timer. Situation in two sentences. |
| **Trashing employers** | “My manager was incompetent.” | Name the constraint: unclear owners, no evals, conflicting SLAs. Leave names out. |
| **Weak results** | “It went well and the team was happy.” | A number, a decision that stuck, or “we killed it, and that saved $X.” |
| **Generic answers** | Any Amazon STAR blog | Your corpus, your outage, your disagreement |
| **Unclear contribution** | Only “we” | “I owned X. Nisha owned Y. I did not do Z.” |

Additional AI-specific fail: **claiming production you did not have**. If it was a pilot, say pilot. Chapter 26 is how to frame a transition without lying.

Do not memorize the EXAMPLE stories below. They teach shape. Your facts go in the templates.

---

## 3. How many stories you actually need

You do not need twelve perfect novels. You need **six stories** that can stretch onto multiple prompts:

| Story | Prompts it can cover |
| --- | --- |
| A hard delivery with a trade-off | Difficult project, pressure, ambiguity |
| A production incident | Production issue, failure, learning |
| A disagreement you handled like an adult | Disagreement, leadership, influence |
| A miss you owned | Failure, learning, integrity |
| A time you taught yourself something fast | Learning quickly, why AI |
| A time you led without the title | Leadership, ambiguity |

Map your six onto a sheet. If two stories are the same “we worked weekends” anecdote, replace one.

---

## 4. Prompts

For each prompt: what they want, a fill-in template, and one EXAMPLE. The EXAMPLE is labeled so you do not recite it as yours.

---

### 4.1 Why are you changing roles?

**They want:** a pull toward this work, not a push-and-rant. A coherent arc. No desperation, no “I want to get into AI because it’s hot.”

**Avoid:** trashing the current team; “there is no growth” with no evidence; sounding like you are fleeing a PIP.

**Template**

```
S: I am a [current role] on [domain]. The work I am strongest at is [production skill].
T: I want my next role to own [AI system type] in production, not only [adjacent work].
A: I already started that shift by [real project / on-call / evals / security work].
R: I am looking at teams where [constraint you want: evals, agents in prod, customer deploy].
   I am not running from [employer]. I am choosing [this problem class].
```

**EXAMPLE** (do not memorize)

> I have been a backend engineer on the billing platform for four years. The work I am strongest at is reliability: I have owned on-call, idempotent webhooks, and a 99.95% SLO. Over the last year the company asked us to put an LLM in the support-adjacent refund assistant. I ended up owning retrieval quality and the rule that the model cannot issue a refund without a human. That is the work I want as the job, not a side quest. I am looking at GenAI / agentic teams that treat evals and tool privilege as engineering. I am not leaving because billing is boring. I am leaving because I want to be measured on whether an AI system is safe and correct, not only whether a REST endpoint is fast.

---

### 4.2 Why AI? Why this field now?

**They want:** a specific problem you could not solve well without models, plus evidence you respect the failure modes. Not “ChatGPT is amazing.”

**Avoid:** hype; implying classical software is dead; implying you will leave AI in 12 months for the next wave.

**Template**

```
S: In [domain] we had [problem: unstructured text, RCA, search, copilot].
T: Rules / search / dashboards were not enough because [reason].
A: I learned [RAG / agents / evals / security] by [shipping a real thing], not by collecting tutorials.
R: I want to stay on the production side: [evals, ACL, cost, HITL]. That is why AI engineering, not a research MS by default.
```

**EXAMPLE**

> Support search was failing on policy IDs and German headings. Keyword search missed paraphrases; a rules engine could not keep up with weekly HR changes. I built a hybrid RAG pilot with a 40-question eval set from real tickets. The interesting part was not the model. It was that dense-only retrieval collapsed on the real corpus and a “be helpful” prompt caused uncited visa advice. That mix of language, evaluation, and fail-closed design is why I want AI engineering now. I would not have said that in 2022. I am saying it because I have seen the failure modes, not because of a blog.

---

### 4.3 Why this company? Why this team?

**They want:** proof you read more than the homepage. A match between their product constraint and how you like to work.

**Avoid:** “you are the leader in AI”; reciting the mission statement; “I want to learn from the best.” Those are website-generic. Chapter 34 has better questions; use what you learned from them here.

**Template**

```
S: You [specific product / customer / constraint: on-prem, regulated, FDE, agent platform].
T: That matches the work I want because [evals / messy data / HITL / cloud estate].
A: I looked at [JD + a talk + a post + the product] and noticed [non-obvious thing].
R: I want to be useful here on [role-shaped contribution], not at a generic LLM shop.
```

**EXAMPLE**

> You deploy into banks that will not let data leave their VPC, and your FDE loop is scoped around messy document ACLs rather than a single-tenant demo. That is the work I want. I read the role as “make retrieval correct under their identity system,” not “demo GPT.” I have done hybrid search with Entra-group filters on an internal assistant, and I care about fail-closed tenancy. I am not applying to every company with an AI logo. I am applying here because the constraint is production identity, not a playground.

If you do not know a non-obvious fact, do not invent one. Say what you *do* know from the JD and ask a sharp question (Chapter 34). “I want to confirm how you evaluate agents in production” is better than a fake compliment.

---

### 4.4 Tell me about a difficult project

**They want:** complexity, your slice, a trade-off, a result. Not “it was hard because of deadlines.”

**Template**

```
S: [Users] needed [outcome] with [nasty constraint: tenancy, latency, legacy data].
T: I owned [slice]. Success was [metric].
A: The hard part was [technical]. I tried [A], it failed because [reason]. I switched to [B].
   I aligned [person] by [showing eval numbers / a spike], not by arguing in the abstract.
R: [Number]. I would still [lesson].
```

**EXAMPLE**

> Situation: we had six weeks to put an internal policy assistant in front of 4,000 employees with Entra-group ACLs and a legal requirement to cite. Task: I owned chunking, retrieval, and the eval set. Action: the demo corpus looked fine with dense search. On 410k real chunks, recall@10 dropped to 0.63 because near-duplicate policies outranked the in-force one and German headings split across chunks. I did not switch models. I added section-aware chunking, hybrid BM25+dense, and an `as_of_date` canonical tag. I showed the 180-question set to legal instead of a happy-path demo. Result: recall 0.84, faithfulness 0.88, p95 6.9s. We still fail multi-hop questions. I did not own the UI.

---

### 4.5 Tell me about a production issue

**They want:** OBSERVE → ISOLATE → FIX → PREVENT (Chapter 22). Calm. No hero narrative. No blaming a vendor and stopping.

**Template**

```
S: Symptom, blast radius, when.
T: I was [on-call / owner]. Goal: stop bleeding, then find cause.
A: I looked at [metric/trace] first. Isolated [layer]. Ruled out [X] because [evidence].
   Mitigation: [rollback / disable tool / take retrieve down].
   Fix: [change].
R: [Time to mitigate]. Prevent: [alert/gate/test]. Lesson: [one line].
```

**EXAMPLE**

> Situation: p95 on the assistant jumped from 3s to 7s in forty minutes; errors were flat. I was on-call for the API. Action: traces showed generate time doubled and retrieve was unchanged. Tokens-in p95 had gone 1.8k → 4.1k after a prompt PR that stuffed 20 chunks instead of 6 and disabled the reranker. I rolled the prompt back in 15 minutes, then restored rerank to top-6 with a token budget in CI. Result: p95 returned to 3.1s. We now alert on tokens-in, not only latency. I did not change the model, which is what Slack was asking for.

If you have never been on-call for an AI system, use a real non-AI incident and add how you would apply the same order to RAG/agents. Do not invent an LLM outage.

---

### 4.6 Tell me about a disagreement

**They want:** you can disagree in public, change your mind on evidence, and not punish people. Especially useful when the disagreement is “agent vs workflow” or “ship without evals.”

**Template**

```
S: We disagreed about [decision]. Their view: ___. Mine: ___.
T: We needed a decision by [time] because [risk].
A: I [asked for their constraint / ran a spike / brought a metric].
   I did not [go around them / CC the org].
   I [conceded X / held Y] because [evidence].
R: We did [outcome]. Relationship: [still work together]. I learned [steelman of their view].
```

**EXAMPLE**

> Situation: a product manager wanted a multi-agent “researcher, writer, critic” on a refund flow. I wanted a single workflow with a human approval node. Task: we had to choose before a customer pilot. Action: I did not say “multi-agent is hype.” I asked what failure we were buying. They wanted better tone. I showed a 15-case replay: the crew used 4× tokens, once skipped the approval narrative, and tone improved on a rubric by 0.2. I proposed a single graph plus a style prompt and HITL. They still wanted a critic later for emails. Result: we shipped the simple graph. Unsafe-action rate stayed 0 on the set. Two months later we added a second node for email tone, not a crew. I was wrong that tone did not matter; I was right that it was not worth unbounded agents.

Never: “I was right and they were political.”

---

### 4.7 Tell me about a failure

**They want:** a real miss, owned, changed behavior. Not a humble-brag (“I worked too hard”).

**Template**

```
S: I was trying to ___.
T: I owned ___.
A: I decided ___. That was wrong because ___. I noticed when ___.
   I [fixed / rolled back / told N people].
R: Cost of the miss: ___. What is now true: [process, test, personal habit].
```

**EXAMPLE**

> Situation: first RAG release. I owned the prompt. I added “always be helpful and never say you don’t know” because a demo looked timid. Task: keep support deflection up. Action: I did not put faithfulness on the dashboard — only thumbs. A support lead pinged that the bot had invented a visa rule. Faithfulness on the golden set was 0.71. I reverted the prompt the same day, required “I don’t know” when snippets did not support the answer, and made faithfulness a release gate. Result: 0.71 → 0.88; we delayed a launch by a week. I told my manager it was my prompt, not “the model.” I now treat helpfulness instructions as a safety bug until proven otherwise.

If your only failures are “the sprint slipped,” pick a quality, safety, or estimation miss. Interviewers discount deadline-only failures.

---

### 4.8 Tell me about leadership (with or without a title)

**They want:** you moved people or a system, not that you had reports. For staff/architect: org-level. For IC: you unblocked, set a bar, or took the ugly on-call.

**Template**

```
S: The team needed [bar / decision / rescue] and it was not happening because [gap].
T: I was [IC / lead]. I did not wait for [title].
A: I [wrote the eval bar / ran the incident / paired / said no to a demo].
   I made it easy for others: [doc, harness, on-call notes].
R: [Adoption / metric / fewer incidents]. I did not [take credit for their work].
```

**EXAMPLE**

> Situation: three teams were shipping prompt changes into the same assistant with no shared eval. Quality swung every week. I was a mid-level engineer, not the manager. Action: I pulled 80 real questions from tickets, labeled with two support leads, and put a 40-question subset in CI on the prompt repo. I sat with each team for one hour so the gate was not a surprise. When a launch failed the gate, I helped them read the traces instead of saying “blocked.” Result: two bad prompts never hit production; the third team adopted the harness for their own bot. My name is on the harness, not on their features.

---

### 4.9 Tell me about learning something quickly

**They want:** how you learn production skills, not that you binge courses. For career switchers this is a high-weight prompt.

**Template**

```
S: I needed [skill] in [time] because [delivery].
T: The bar was [I can debug X / I can defend Y], not “finish a Udemy.”
A: I [read one primary source / built a thin slice / added evals / asked N].
   I skipped [framework tourism].
   I knew I was competent when I [debugged an incident / explained a trade-off].
R: [What shipped]. I still do not [honest boundary].
```

**EXAMPLE**

> Situation: we decided to add hybrid search three weeks before a pilot. I had never run BM25 in Azure AI Search. Action: I did not start with four vector-DB blogs. I read the query API, built a 30-question retrieve-only notebook, and compared dense-only vs hybrid vs hybrid+rerank on our corpus. I paired with a teammate who had run Elasticsearch. I knew it was working when I could explain why policy IDs failed dense-only. Result: recall@10 0.63 → 0.82 before we touched the generator. I still have not operated Search at 100× QPS; I would load-test the filtered query path before claiming that.

---

### 4.10 Tell me about working under pressure

**They want:** priorities, communication, no silent corners. Pressure is an incident, a deadline with a safety constraint, or a customer in the room (FDE).

**Template**

```
S: [Clock] and [risk if sloppy].
T: I needed to [mitigate] without [unsafe shortcut].
A: I ordered work: [stop bleed → communicate → fix → prevent].
   I said no to [scope] because [safety/quality].
R: [Outcome]. I did not [hide status / skip the gate].
```

**EXAMPLE**

> Situation: a customer demo in 48 hours on their documents. Their ACL tags were a mess; a naive index would have mixed departments. Task: I was the FDE on site. Action: I cut scope to one department, failed closed on untagged docs, and showed a retrieval eval on 25 of their questions instead of a flashy agent. I told the sponsor on hour one that a cross-department copilot would be a privacy incident, not a stretch goal. Result: the demo answered 18/25 with citations inside one department. We left with a contract for tagging, not a fake win. Pressure was the calendar; the failure mode was leakage.

“I drank more coffee and stayed all night” is not Action.

---

### 4.11 Tell me about ambiguity

**They want:** you can specify a problem. This is the FDE / solutions discriminator and a senior IC test. Jumping to LangGraph before the user and the cost of being wrong is the fail.

**Template**

```
S: The request was [vague: “make it AI,” “automate on-call”].
T: I needed a problem statement: user, cost of wrong, HITL, data.
A: I asked [N questions]. I wrote a one-pager: in / out of scope.
   I shipped a [thin slice] to learn [X], not a platform.
R: We learned [fact]. We did not build [the overdesigned thing].
```

**EXAMPLE**

> Situation: leadership said “build an AIOps agent that remediates.” Task: I was asked to propose an architecture in a week. Action: I interviewed two on-call rotations. They did not want remediations; they wanted a first RCA draft. A previous auto-restart had extended an outage. I wrote a one-pager: read tools only, draft ticket, HITL on execute, 40-incident replay eval, unsafe-action rate must be 0. I refused a multi-agent design in week one. Result: the pilot cut time-to-draft 25m → 7m and executed nothing. Ambiguity was the word “agent.” The job was a scoped copilot.

---

## 5. Follow-ups they will use to see if you lied

Expect these after any story. Prepare one line each.

| Follow-up | They are testing | Good move |
| --- | --- | --- |
| “What did *you* do?” | Unclear contribution | Restart with “I owned…” |
| “What would you do differently?” | Learning vs defensiveness | One concrete change |
| “What did the other person think?” | Empathy in disagreements | Steelman |
| “Was it production?” | Overclaim | Prototype / pilot / prod with users |
| “What’s the number?” | Weak results | Metric or honest “we did not measure X; we saw Y” |
| “How do you know it worked?” | Evals | Golden set, ship bar, remaining fail class |

If you do not remember a number, do not invent one. “I do not have the exact p95. It was over our 4-second budget and the trace said generate.” That is adult.

---

## 6. Special notes by seniority

| Level | They allow | They punish |
| --- | --- | --- |
| Switcher / junior | Small scope, honest ceiling | Fake production, framework lists |
| Mid | One or two owned incidents | “We” for everything |
| Senior | Trade-offs, saying no, teaching a bar | Only IC task stories, no influence |
| FDE / solutions | Customer ambiguity, politics without gossip | Jumping to tools, trashing the customer |

---

## 7. Drill

1. Write six cards. Cut each Action to five bullets.
2. Record the difficult-project story. If it is over 2:30, cut Situation.
3. Have a friend ask only “what did you do?” and “what’s the number?”
4. Remove every sentence that insults a former employer. Replace with a constraint.
5. Check that at least two stories show you *not* using an agent or *not* using a bigger model.

You are ready when you can tell any of the six in 90 seconds, remap it to a slightly different question, and admit a boundary without collapsing. Then customize Chapter 25 so the first 60 seconds of the loop already matches these stories.
