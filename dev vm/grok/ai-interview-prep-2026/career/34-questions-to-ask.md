# 34 — Questions to Ask the Interviewer

**What this chapter is for:** so the last five minutes of each round are a seniority test you pass on purpose, not a panic “so, what’s the culture like?”

You are not filling silence. You are collecting evidence for two decisions: *will I be measured on work I believe in, and can I do this job without lying about the operating model?* Chapter 28 already said that asking nothing reads as “I want any job.” This chapter is the question bank.

Prepare **six**. Ask **two or three** per round, matched to the person in front of you. Write the answers. Use them in later rounds and in the “why us?” story (Chapter 24).

---

## 1. How questions signal seniority

Interviewers score the *question* the same way they score answers: requirements before tools, failure before fashion.

| Lens | Junior / switcher | Mid | Senior / FDE / Architect |
| --- | --- | --- | --- |
| Opens with | Stack, training, “will I get to use LLMs?” | How quality is measured | Who is harmed by a wrong answer; who owns the system after week six |
| Time | 1 generic question | 2 specific, JD-tied | 2–3 that expose operating model |
| Follow-up | Accepts slogan | Asks for an example | Asks when they last rolled back / refused a demo |
| Fail mode | Compensation in round 1 IC; “what’s the tech stack?” after they spent an hour on it | Only tooling | Cross-examining; asking questions you could have Googled |

A strong question has:

1. A **constraint** (evals, ACL, on-call, travel, quota, GPU vs API)
2. A **decision** you would make differently depending on the answer
3. Room for them to tell a **story**, not a slogan

Weak: “Do you use LangGraph?”  
Strong: “When did you last choose a workflow over an agent, and what broke when someone did the opposite?”

---

## 2. What not to ask (and when it becomes OK)

| Do not ask | Why it fails | Ask instead / when |
| --- | --- | --- |
| “What does your company do?” | You had the JD and the homepage | One non-obvious product constraint |
| “What’s the tech stack?” after a design round | You were just in it | “What do you *not* want in the stack in the next year?” |
| “Is there work-life balance?” | Slogan bait | On-call rotation, travel days, incident load (specific) |
| “How much will I learn?” | You are asking them to parent you | “What does someone fail at in six months?” |
| “Do you use AI internally?” | Everyone says yes | “Where is the assistant *not* allowed to write?” |
| Comp, bonus, ESOP details in an IC technical round | Wrong audience | Recruiter / HM offer stage (Chapter 27) |
| Anything you could find in 90 seconds | Signals no research | Use the 10-line brief from Chapter 28 |
| Personal questions about the interviewer’s family, politics, or job-search | Unprofessional | Their published talk, if relevant to taste |
| “Will I get promoted in a year?” | Entitled | How level and scope actually move |
| Trapping them (“so you *don’t* have evals?”) | Cross-exam | “Who owns the golden set today?” |

**Compensation** belongs with the recruiter and the hiring manager at the times in Chapter 27. Asking an IC “what’s the band?” wastes a round that should have revealed whether evals exist.

**Culture** is a real topic. Ask it through incidents, not adjectives: “Tell me about the last time a prompt change was blocked.” That *is* culture.

---

## 3. How many, when, who

| Round | Ask about | Do not ask |
| --- | --- | --- |
| **Recruiter** | Level, loop shape, location, travel/quota, band timing, notice, “is this IC or solutions?” | Deep architecture they cannot answer |
| **Hiring manager** | 90-day success, team shape, on-call, what failed last quarter, why the seat is open | Gossip about the last person |
| **IC technical** | How they debug, eval, ship prompts, divide RAG vs agents | Comp, “will I be coding?” if you just coded |
| **System design** | Real constraints of *their* system (tenancy, QPS, cloud) | Hypotheticals you already covered |
| **Project deep dive** | Almost nothing unless time remains; one operating-model question | Restarting your bio |
| **FDE / customer scenario** | What a real deployment looked like; access to data; time on site | “Do I have to travel?” as the only question (ask it, but not only it) |
| **Solutions / demo** | Quota, SE vs AE split, security review path | “What’s the discount policy?” |
| **Security round** | Findings that actually blocked a launch | “Do you care about security?” |
| **Offer / HM close** | Comp components, success criteria, manager style | Relitigating every technical choice |

If time is short: **one** question that reveals the operating model. Quality over a list.

When they say “do you have questions?” and you have none because they already answered, say so:

> You already covered evals, on-call, and the cloud. I do not want to ask a decorative question. I would like to confirm [one precise cell that is still empty].

That is senior. Empty silence after “nope, I’m good” is not.

---

## 4. Universal high-signal questions

Use these on almost any of the eight roles. Pick the ones you do not already know.

### Quality and evals

- “What does a *wrong* answer from this system cost the business — money, safety, or embarrassment?”
- “Who owns the golden set, and who owns the knowledge in the corpus?”
- “When did you last block a prompt, model, or index change because evals failed?”
- “What still fails that you are honest with leadership about?”
- “Offline vs online: what is the ship bar, and what is just a dashboard?”

### Failure and operations

- “When did you last roll back a prompt, a model version, or an index?”
- “What does on-call look like for this system — who is paged, for what, how often?”
- “Where do you *not* want agents — or LLMs at all?”
- “What happens when the provider 429s during your peak?”
- “Who is the customer of this system on a bad day: end user, operator, or the on-call?”

### Data, identity, access

- “How does identity reach retrieval and tools — IdP group, row in Postgres, or hope?”
- “What data will I actually be able to see in week one (prod logs, customer corpora, none)?”
- “How do you revoke a document at 3pm and know it is gone from the index?”
- “Training / logging opt-out: which vendors, and who checks?”

### Scope of the role

- “What would make someone fail this role in six months?”
- “What does the first 90 days look like if I am hired — a system, a customer, or a platform gap?”
- “Is this closer to applied RAG/product, agent orchestration, platform/serving, customer deployment, or architecture/governance?” (use when the recruiter is vague; Chapter 02)
- “How much of the job is building vs integrating a vendor SKU vs sitting with users?”

### GPU vs API (reveals the real job)

- “Are we calling hosted APIs, provisioned throughput, or operating GPUs — and who gets the bill?”
- “If cost 10×s overnight, is that an engineering incident or a finance spreadsheet?”
- “What is the default model path: company-approved endpoint on our cloud, or whatever won a leaderboard last week?”

Write their answers in the 10-line brief (Chapter 28). If they cannot name a cost-of-wrong or an eval owner, you just learned more than a stack list.

---

## 5. Questions by round (scripts you can actually say)

### Recruiter (pick 2)

> Is this loop closer to GenAI product, agent orchestration, cloud landing, AIOps, security, FDE, solutions, or architecture? I want to prep the right one.

> What level are you hiring, and is the band for that level in this geo something we can share before I take a day off for the on-site?

> Does the role include on-call, customer travel, or quota? I want that explicit.

> You have seen candidates for this seat — what did the last “almost hire” miss?

### Hiring manager (pick 2–3)

> What does a wrong answer cost, in this product’s language?

> Why is the seat open — growth, backfill, or a project that burned people out?

> If I do well, what is true in 90 days that is not true now?

> Tell me about a time the team said no to an agent, a demo, or a model swap.

> How are evals staffed? A named owner, or “the intern has a notebook”?

### IC who just grilled you on RAG / agents

> When retrieval is right and the answer is wrong, what does your actual debug path look like here?

> What traces do you keep, and what are you not allowed to log?

> Which orchestrator do you run in prod, and what did you reject?

### After system design

> I assumed [Entra groups / p95 3s / no write tools]. Where does that diverge from what you actually run?

> What is the current bottleneck — quality, cost, latency, or data access?

### FDE / deployment scenario interviewer

> On a real deployment, how long until you had usable labeled questions on *their* data?

> What access did you actually get in week one vs what the SOW promised?

> When did you last walk away from a customer scope?

### Solutions / architect panel

> How do security questionnaires get answered — SE, SA, or a copy-paste matrix?

> When the product is a bad fit, are we allowed to say so in the room?

### Offer close

Use Chapter 27’s checklist out loud, as questions, not as a raid.

---

## 6. Role packs

Each pack is for *that* loop. Do not ask the FDE travel question in a closed-world GenAI IC round as if it were the job.

### 6.1 GenAI / Agentic AI Engineer

| Ask | What a real answer reveals |
| --- | --- |
| “Is the job retrieval quality, agent orchestration, or both — and which is the pager?” | Whether you prepped Chapter 10 or 11 |
| “Golden set size, who labels, ship bar?” | If evals are a product or a slide |
| “Citations mandatory, or ‘be helpful’ still wins demos?” | Safety vs sales |
| “Write tools in prod today? HITL on which actions?” | Excessive agency |
| “Prompt/model/index versioning — can you roll back in 15 minutes?” | LLMOps maturity |
| “Where did multi-agent die here?” | Taste; Chapter 11 alignment |
| “Context and cost: do you route, cache, or throw 128k at every FAQ?” | Senior engineering vs toy |

**Do not ask:** “Will I get to try CrewAI?” That is the opposite signal.

### 6.2 AIOps Engineer

| Ask | Reveals |
| --- | --- |
| “What is in scope: correlation, RCA draft, or execute?” | Whether they want a healer or a copilot |
| “When did auto-remediation last make an outage worse?” | Honesty; HITL culture |
| “Which topology source is source of truth — CMDB, service mesh, tribal knowledge?” | Whether RCA can work |
| “Alert volume and pages per on-call shift?” | The actual job |
| “ITSM: are we opening tickets or closing them?” | Blast radius |
| “Do you evaluate unsafe-action rate on a replay of real incidents?” | 2026 bar vs dashboard clustering |
| “Which observability vendors are real, not listed on the JD for SEO?” | Stack you must know |

**Red answer:** “The LLM will just remediates once it’s smart enough.” Believe them; leave.

### 6.3 Cloud AI Engineer

| Ask | Reveals |
| --- | --- |
| “Data gravity: why this cloud, and is a second cloud a real requirement?” | Whether they pick clouds by leaderboard |
| “Private endpoints, CMEK, training opt-out — which are actually enforced?” | Landing-zone maturity |
| “GPU vs API vs PTU/provisioned — what do we operate?” | Your on-call |
| “Who owns quotas and 429s — platform or the app team?” | Finger-pointing |
| “Model inventory: can we add a model without a security review?” | Shadow AI |
| “Cost alerts: has anyone actually been woken up by a token bill?” | Whether cost is engineering |

### 6.4 Intelligent Automation Engineer

| Ask | Reveals |
| --- | --- |
| “Show me a process that stayed a workflow on purpose.” | Agent vs BPM taste |
| “Where does the LLM sit: extract, classify, decide, or write to the ledger?” | Control design |
| “Maker-checker: timeout-as-approve or deny-on-timeout?” | Security adulthood |
| “Which systems of record (SAP / ServiceNow / Salesforce) are in the critical path?” | Integration job vs demo |
| “How do you measure task completion vs ‘bot hours saved’ theater?” | Eval culture |
| “Exception queue: who works it, and is that still the job in 12 months?” | Whether they are replacing you with a slide |

### 6.5 AI Security Engineer

| Ask | Reveals |
| --- | --- |
| “Have you mapped OWASP LLM 2026 onto this product with owners, or is it a lunch-and-learn?” | Job vs poster |
| “Last finding that blocked a launch — injection, tenancy, agency, MCP?” | Whether security has teeth |
| “Is retrieved content treated as untrusted in the threat model?” | Indirect injection literacy |
| “MCP / tool gateway: who runs it, and can an engineer add a server without review?” | Shadow tools |
| “Logging: prompts contain customer data — redaction, retention, who can grep?” | Hidden context exposure |
| “Red team: internal, vendor, or never?” | Detection vs hope |
| “How do you test ACL in the *query*, not in a slide?” | Engineering vs policy PDF |

**Do not ask:** “Do you jailbreak ChatGPT for fun?” They want controls, not a persona.

### 6.6 Forward Deployed / AI Deployment Engineer

| Ask | Reveals |
| --- | --- |
| “Travel: % of time on site vs remote, notice, regions, visa support?” | The life, not the title |
| “Week-one data access: do we get the corpus, or a sanitized sample two weeks late?” | Whether v0 is possible |
| “Who is the customer champion, and what happens when they leave?” | Deployment failure mode |
| “Are we allowed to cut scope in the room — one department, HITL, fail-closed untagged docs?” | Judgment vs “make it demo” |
| “What do we leave behind — code, eval harness, runbooks — and who operates it?” | Forward-deployed vs hit-and-run |
| “Security review: our laptop on their network, their VPC, or a vendor SaaS?” | Actual architecture |
| “GPU vs API in *their* estate — do we bring GPUs or use their Bedrock/Foundry/Vertex?” | What you must land |
| “On-call for customer systems after go-live: us, them, or a fight?” | Residual duty |

**Must ask travel and access before you celebrate the offer.** Chapter 27 will not save a surprise 60% on-site.

### 6.7 AI Solutions Engineer

| Ask | Reveals |
| --- | --- |
| “Is there quota or OTE? What % of my scorecard is revenue vs technical success?” | Sales vs SE |
| “AE / SE / SA split — who owns discovery, who owns the architecture, who discounts?” | Whether you will be a demo monkey |
| “Can I say the product is a bad fit and still be a good SE here?” | Ethics and seniority |
| “Do we eval on *their* documents in a tenant we can isolate, or on a canned corpus?” | POC honesty |
| “Security questionnaire SLA — who writes the answers?” | Hidden workload |
| “Travel and on-site POCs: days per month?” | Life |
| “What happened to the last POC that the customer loved and then could not operate?” | Your actual success metric |

If they will not say whether quota exists, assume it might, and get it in writing (Chapter 27).

### 6.8 AI Solutions Architect

| Ask | Reveals |
| --- | --- |
| “Do we write ADRs that include evals and operating model, or logo reference architectures?” | The job |
| “Who owns the system after we leave — customer platform, our managed service, nobody?” | Residual risk |
| “CISO path: can we put identity-in-retrieve and HITL on the first slide?” | Whether you will fight sales |
| “Multi-cloud: real constraint or a slide requirement?” | Design honesty |
| “EU AI Act / sector rules: do we have a risk classification for this product?” | Governance vs vibe |
| “Cost model: do we TCO tokens + search + people, or only licenses?” | Adult architecture |
| “When did you last refuse a multi-agent design in a customer meeting?” | Taste you must match |

---

## 7. Questions that reveal the six constraints people forget

These are the six you were told to hunt: **evals, on-call, data access, GPU vs API, customer travel, quota.** If you leave the loop without answers, you are guessing at the job.

| Constraint | Minimum question | Good answer sounds like | Bad answer sounds like |
| --- | --- | --- | --- |
| **Evals** | “Who owns the golden set and what is the ship bar?” | Named owner, size, last blocked release | “We look at thumbs” / “the model is great” |
| **On-call** | “Who is paged when the assistant is wrong or the pipeline is down?” | Rotation, severity, last incident | “It’s just APIs, nobody pages” (then they will) |
| **Data access** | “What will I be allowed to see in week one?” | Prod-adjacent with controls, or an honest ‘nothing yet’ | “You’ll have prod on day one” with no IdP story — or eternal sample data |
| **GPU vs API** | “Do we operate GPUs or call hosted models, and who pays 429s?” | A default path and a bill owner | “Whichever is cheapest this week” with no inventory |
| **Customer travel** | “What % of weeks am I on site, which geos, how much notice?” | A number, a region, a policy | “We’re flexible” for an FDE seat |
| **Quota** | “Is any part of my compensation or rating tied to revenue?” | Yes/no and the split | “We’re all salesy here” with no OTE, or “pure IC” that is actually SE |

Ask the row that matches the role even if it feels awkward. Awkward is cheaper than a wrong year.

---

## 8. How to ask without sounding like a checklist

**Do**

- Tie the question to something they already said: “You mentioned a bank pilot — how did identity land in retrieval there?”
- Ask for a *time*: “when did you last…” is harder to sloganize than “do you have…”
- Stop after two if they are talking. Let them run. That is the information.
- Note names of systems. You will need them in the next round.

**Do not**

- Read six questions from a notebook without listening.
- Interrupt their answer to ask the next item from this chapter.
- Use the question to show off (“given OWASP LLM 2026 item 6…” unless you are in the security loop and it is natural).
- Ask the same eval question of four people as a gotcha. Asking two people *on-call* vs *evals* is diligence; deposing the intern is not.

**If they dodge**

Once:

> I am asking because it changes how I would do the job — workflow vs agent, or whether I can actually see data. If it is sensitive, even a qualitative answer helps.

If they dodge twice, you have the answer. Write “unknown / defensive” in your brief. That is a Chapter 27 red flag if it clusters.

---

## 9. Using their answers later

Questions are not a courtesy ritual. They are ammunition.

| They said | You do later |
| --- | --- |
| “We do not really have evals yet” | In HM close: that is the 90-day job you want — or the reason you walk |
| “FDE is 40% travel, EU and US” | Recruiter: visa, notice, family constraint (Chapter 27) |
| “Execute is on for restarts” | Security / design: you push HITL; you decide if you accept the blast radius |
| “Quota is 20% of the SE scorecard” | You stop pretending this is a pure IC seat |
| “Default is Azure OpenAI in their tenant” | You prep Foundry/AI Search, not a generic LangChain demo |
| “Last person left because production ownership was unclear” | You ask who owns the pager, in writing if needed |

Update the Chapter 25 intro if you learn a non-obvious constraint. “You deploy into VPCs that cannot call public APIs” is a better “why you” than a mission statement.

Never invent a fact they did not say. If you only know the JD, Chapter 24 already told you: a sharp question beats a fake compliment.

---

## 10. Switcher and seniority notes

**Career switchers (Chapter 26):** ask questions that prove you understand production, not that you collected nouns.

Good: “How do you gate a prompt change the way you would gate a payment-API change?”  
Bad: “Will I be trained on LangChain?”

You may ask whether they have hired switchers and what those people owned in month three. That is fair. Do not ask them to lower the bar on the call.

**Senior / staff:** your questions should sound like you are already in the design review.

Good: “Who is accountable when the agent sends an email — the user, the team, or legal?”  
Bad: a list of vendor comparisons they did not ask for.

**Architect / FDE:** spend questions on operating model, residual risk, and politics of data. Tools are a follow-up.

---

## 11. Fail modes

| Fail | Sounds like | Fix |
| --- | --- | --- |
| **Zero questions** | “I’m good” after a 45-minute IC | Keep one operating-model question always |
| **Googleable** | “When was the company founded?” | 90-minute research brief |
| **Stack tourism** | “Do you use the new Agents SDK?” | Ask what they rejected |
| **Comp in the wrong room** | Band question to the staff engineer | Chapter 27 |
| **Work-life slogan** | “Is it chill?” | On-call, travel, incident rate |
| **Gotcha** | Smirking when they lack evals | You are deciding, not prosecuting |
| **Too many** | Six rapid-fire as they try to end | Two, then “I will save the rest for the HM” |
| **Wrong role pack** | GPU kernel questions on a Solutions loop | Use §6 for the calendar you have |

---

## 12. Drill

1. From the JD, highlight verbs. Write **six** questions, two of which are from the six-constraint table in §7.
2. Assign each question to a round (recruiter / HM / IC). You may not ask all six of the HM.
3. Record yourself asking two questions out loud. If you sound like you are reading this chapter, rewrite in your words.
4. After every mock (Chapter 29), the interviewer answers in character. Practice one follow-up on their answer.
5. Build a one-page “answers I need before I sign” list: evals, on-call, data access, GPU vs API, travel, quota, plus Chapter 27 money cells.

You are ready when you can walk out of a loop with those six cells filled, without having asked a single decorative question, and without having used the last five minutes to recap your resume. The questions are how you decide whether the job is real. The rest of the handbook is how you get it.
