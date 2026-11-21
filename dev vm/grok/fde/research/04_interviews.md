# 04 — Interviews: FDE + GenAI / Agentic AI

**Access date:** 2026-09-15  
**Scope:** Current interview loops for Forward Deployed Engineer (FDE) / Forward Deployed Software Engineer (FDSE) and adjacent GenAI / agentic AI / classic SWE roles.  
**Rule:** Official hiring pages and company blogs are labeled **Official / Verified**. Prep-site compilations, Glassdoor, Reddit, and coaching platforms are labeled **Candidate Reported**. Unverified pass-rate or “hidden filter” claims are **not** treated as confirmed process.

---

## How to read these notes

| Label | Meaning |
|---|---|
| **Official / Verified** | Published by the employer (careers site, official interview guide, engineering/hiring blog, official PDF). Process can still vary by team. |
| **Candidate Reported** | Aggregated from Aced/Exponent, interviewing.io, Glassdoor, IGotAnOffer, FDEnest, and similar. Useful for round flavor; not company policy. |
| **Engineering blog / role description** | Describes the *job*, not necessarily the interview loop. |
| **Unverified / rumor** | Circulating numbers (pass rates, “instant reject” rules) without a primary source. Do not treat as confirmed. |

**Standing caveats**

- Loops are team- and level-dependent. OpenAI, NVIDIA, Palantir, Databricks, and Scale all say this officially or via recruiters.
- AI-tool policy differs by company *and by round*. Ask the recruiter; do not assume.
- “FDE” is a family of titles: Palantir FDSE / Forward Deployed AI Engineer, Databricks FDE / RSA-adjacent, Scale FDE / Frontier Agents Engineer, Salesforce FDE, OpenAI FDE, Anthropic Applied AI Engineer (closest analog). Confirm the employer and title before prepping.
- Several 2026 FDE “guides” copy each other (decomposition pass rate ~40%, weight ~30%). Those figures are **not independently verified** here.

---

## 1. Cross-cutting loop shape

### Classic SWE (Google, Meta, Amazon, Microsoft, NVIDIA SWE)

Typical stages: recruiter → (OA) → 1–2 technical screens → onsite of 4–6 rounds mixing **DSA coding**, **system design** (mid+), **behavioral**. Hiring committee or bar-raiser often sits after the loop. LeetCode-medium/hard is a real gate.

### FDE / FDSE

The extra signal is **ambiguous customer work**: decomposition, deployment scenario, client simulation, learning/re-engineering, presentation of a messy dataset. Coding still exists, but it is usually **practical** (data, APIs, messy inputs) rather than contest-style graphs/DP. Behavioral and client communication are often **embedded in technical rounds**, not isolated.

A useful 2026 pattern across Palantir, Databricks, Scale, and AI-lab FDE postings (**Candidate Reported**, Aced / FDEnest):

1. Recruiter screen (motivation, travel, why FDE vs SWE)
2. Technical screen (coding OA or live; sometimes SQL + API)
3. Practical coding (notebook / CodePair / HackerRank project-style)
4. System / data / AI design
5. **Decomposition / deployment scenario / customer simulation** (the FDE differentiator)
6. Behavioral / values / hiring manager

### GenAI / Applied AI / Agentic AI engineer (labs + cloud)

Adds **ML/LLM production depth**: RAG, evals, tool use, agent loops, safety, cost/latency, observability. Coding is often practical Python plus a design round that looks like “deploy this model/agent under enterprise constraints.” Research-scientist loops add paper/presentation; SWE loops at labs still include coding + systems.

### Round-type map (what actually shows up)

| Round type | Classic SWE | FDE | GenAI / agents |
|---|---|---|---|
| LeetCode-style DSA | High | Medium (often dressed as a product task) | Medium, more practical |
| Practical coding / debugging / learning | Low–medium | High | High |
| Distributed system design | High (L4+) | Medium; more data/integration | Medium |
| RAG / agents / evals design | Rare except AI teams | Rising, especially AI-lab and Databricks FDE | Core |
| Ambiguous case / decomposition | Rare | **Signature** | Common in Applied AI / FDE |
| Customer / stakeholder simulation | Rare | High | Medium |
| Values / LP / Googleyness | Always | Always; often embedded | Always; labs probe safety/mission hard |
| Take-home / work trial | Occasional | Occasional (OpenAI, Scale, some Databricks) | Common at labs |

---

## 2. How much LeetCode is actually justified

This is the most common mis-allocation of prep time.

### Classic SWE — high justification

**Google (Official / Verified + Candidate Reported).** Google’s public hiring process still centers coding interviews on data structures, algorithms, complexity, and testing. Candidate reports for 2026 still describe 2–4 coding rounds at medium / medium-hard, plus (for many US teams) a code-comprehension or AI-assisted code-comprehension round. Grinding LeetCode is still the highest-ROI SWE prep at Google.

**Meta (Official / Verified + Candidate Reported).** Official SWE prep historically: two coding problems in a 45-minute screen on algorithms, data structures, recursion, binary trees. 2026 official FAQ: many interviews now include a **built-in AI assistant** in CoderPad; outside AI is banned. Candidate reports: coding remains the hire/no-hire gate; design sets level. LeetCode medium, **speed**, and two-problem-in-45-min pacing still matter. Also practice *with* an in-environment AI tool, because that is now the official format for many loops.

**Amazon (Official / Verified).** Official SDE topics include programming language, data structures, algorithms, coding, OOD, databases, distributed computing, OS, internet, and general ML/AI. Official OA sample is a HackerRank coding challenge. Leadership Principles are tested in **every** round. LeetCode medium + STAR LP stories is the justified split (~50/50 technical vs behavioral for SDE, per Amazon’s own interview-loop page).

**Microsoft (Official / Verified).** Official technical-interview page: problem solving, design, coding (runnable code in a third-party tool, **not** pseudocode), testing. Explicitly asks for algorithms, at least one n log n sort, Big-O, arrays/strings/queues/lists/trees/tries/hash maps/graphs, distributed systems / SOA, and (for relevant roles) AI/ML. LeetCode is justified; so is testing and design. Candidate reports add an “As-Appropriate” senior round.

**NVIDIA (Official / Verified + Candidate Reported).** Official: technical roles may complete a HackerRank coding exercise; **unapproved tools such as ChatGPT during the interview disqualify candidacy**; onsite in-person interview is required before an offer. Candidate reports: team-variable mix of LeetCode medium, C++/memory, CUDA/GPU domain, systems. LeetCode is a floor, not the job.

### FDE — moderate LeetCode, high practical + decomposition

**Palantir FDSE (Official process shape + Candidate Reported rounds).** Official: one or two phone interviews (20–45 min) including a coding question for engineers; personalized onsite; think out loud; start simple then expand. Candidate reports converge on: HackerRank or live CodePair/Karat (coding + often SQL + API); onsite drawn from **decomposition, learning, coding, re-engineering, system design**; behavioral embedded ~15–20 min per round; AI prohibited throughout the Palantir FDE loop (Aced, candidate-updated). Coding difficulty is commonly described as **LeetCode medium dressed as a real workflow** (dedupe, joins, pagination), not LeetCode hard graphs/DP. **Do not skip coding.** Do not *only* grind LeetCode.

**Databricks FDE (Official company process + Candidate Reported FDE flavor).** Official engineering PDF (April 2025): recruiter 30 min → technical screen 1 hour → team matching → full panel 4–6 × 1 hour (coding, algorithms, system programming, architecture, domain deep dive, cross-functional) → hiring committee → references. Official FAQ: 2–3 months, 4–6 onsite interviews, virtual default. **Candidate Reported FDE-specific:** practical notebook coding (dicts/strings/lists, easy–medium), SQL + light AI screen, **decomposition** from a vague business goal, leadership/values. Graph/tree-heavy SWE questions are reported as uncommon on the FDE track. Databricks SWE (platform) is a harder DSA bar than Databricks FDE.

**Scale AI FDE (Candidate Reported).** Same technical bar as SWE: HackerRank project-style OA + screen, then onsite coding, **debugging an unfamiliar repo**, system design with RAG/ingestion, credo behavioral. LeetCode patterns (intervals, scheduling) appear, but volume-of-working-code and debugging beat puzzle hardness.

**Salesforce FDE (Official role description; interview loop not published).** Official blog (19 Nov 2025): FDE launched April 2025; pods of strategist + two FDEs; skills are problem-solving, technical range (Apex/JS/prompts/integrations), communication, business acumen, learning mindset. Trailhead / Agentblazer called out as skill-building, not as a hiring exam. **Gap:** no official round list. Treat as customer-scenario + platform technical, not LeetCode-hard, until a recruiter confirms.

### GenAI / lab SWE — practical coding + systems + mission; LeetCode is a floor

**OpenAI (Official / Verified).** Official interview guide: résumé review (~1 week) → intro calls → skills-based assessment (pair coding, take-home, technical tests; **varies by team**) → final 4–6 hours with 4–6 people over 1–2 days. Engineering bar: well-designed solutions, high-quality code, optimal performance, **good test coverage**. AI-tool policy **varies by interview**; recruiter materials say what is allowed. **Candidate Reported:** coding is more practical than stock LeetCode (file systems, versioned stores, coroutines, information-theory/probability twists); system design in Excalidraw; presentation of a past project with slides; possible paid/NDA work trial on some teams; **agentic coding round in beta** (existing codebase + authorized agent). Prep LeetCode medium for fluency, then spend more time on practical multi-part problems, tests, and talking while coding.

**Anthropic (Official / Verified).** Official careers: all interviews on Google Meet; technical roles use Colab and CodeSignal; **you may look things up**; be fluent in syntax/stdlib so lookup does not eat the clock; about half of technical staff had no prior ML. Official AI-usage policy (10 Jul 2025): Claude OK to refine résumé and to prep; **take-homes without Claude unless stated**; **live interviews are you, no AI unless indicated**. **Candidate Reported (interviewing.io, 2026 engineer conversations):** recruiter (non-trivial mission screen) → 60–90 min CodeSignal take-home or live (progressive spec, not stock LeetCode) → onsite of coding, system design, second coding, **company values** (often the hardest; therapy-like, ethics, disagreement). Concurrency/multithreading recur. Values fail more candidates than coding, per that source.

**Net:**  
- **Classic SWE at Google/Meta/Amazon:** 8–12 weeks of LeetCode is still rational.  
- **FDE:** 3–4 weeks of medium practical coding + 3–4 weeks of decomposition / customer scenarios is more rational than 12 weeks of LeetCode hard.  
- **GenAI lab SWE:** LeetCode medium fluency + production Python + LLM systems + evals/safety. Hard DP is low ROI unless the recruiter says otherwise.

---

## 3. Company interview loops

Each subsection: official process first, then candidate-reported flavor, then what to emphasize for FDE vs GenAI vs SWE.

### 3.1 Palantir — FDE / FDSE

**Titles (Official):** Forward Deployed Software Engineer (commercial, government, Warp Speed, tactical edge, new grad), Forward Deployed AI Engineer, Forward Deployed Infrastructure / Reliability / Security Engineer, Deployment Strategist (separate loop). Palantir originated the role.

**Official / Verified process** ([Getting Hired](https://www.palantir.com/careers/getting-hired/), [Phone Interview](https://www.palantir.com/careers/getting-hired/the-phone-interview/), students page):

- Process is **personalized** to skillset and role (FDSE vs SWE).
- Everyone starts with **one or two phone interviews**, typically **20–45 minutes**.
- Engineering phone screen includes a **coding question**. Every engineer is expected to work through one.
- If there is a fit: onsite, in-person or virtual.
- Official phone tips: think out loud; ask questions; start simple then expand.
- Feedback typically within a week or two.
- Recruiter provides prep material ahead of each step (students/early-talent page).
- Onsite: be yourself; discuss accomplishments and failures; ask clarifying questions on analytical/technical problems.

**Candidate Reported** (Aced Palantir FDE guide, updated by candidates; interviewing.io; Glassdoor FDSE reports):

| Stage | Format | Notes |
|---|---|---|
| Recruiter | ~30 min | Motivation filter is aggressive. Generic “interesting problems” fails. Name Gotham/Foundry/AIP and why forward-deployed. |
| Technical screen | HackerRank ~90 min (coding + SQL + API) **or** live CodePair/Karat ~60 min | Practical, often maps/strings/pagination, not graph-hard. |
| Onsite | **Three** 60-min rounds drawn from a **pool**: decomposition, learning, coding, re-engineering, system design | Two candidates rarely get the same trio. Decomposition is nearly universal. ~15–20 min behavioral inside each round. |
| Hiring manager | ~60 min | Often re-tests a weak onsite area; team matching. |

**Onsite pool (Candidate Reported):**

- **Decomposition:** Vague real-world prompt (traffic in NYC, sync two HR systems, catalog species). Scope, data model, APIs, what ships in weeks. Little or no code.
- **Learning:** Unfamiliar docs/codebase; extend it in stages. Python / Java / TypeScript.
- **Re-engineering:** 80–250+ lines of buggy code; find real defects vs red herrings.
- **Coding:** Product-framed DSA; then refactor for reuse.
- **System design:** Data-pipeline flavor, user-centric, trade-off defense.

**AI policy (Candidate Reported):** Palantir FDE loop **prohibits AI** in interviews.

**LeetCode vs other:** Coding is a gate, not the offer. Decomposition + communication + “why Palantir” decide FDE more often than a hard algorithm.

**Timeline (Candidate Reported):** commonly 3–4 weeks; company-wide average sometimes cited ~28 days. Confirm with recruiter.

**Gap:** Official pages do not publish the onsite pool names. Treat decomposition/learning/re-engineering as **candidate-reported names for official competencies** (open-ended questions, writing good code, working inside existing systems).

---

### 3.2 Databricks — FDE (and SWE contrast)

**Official / Verified** ([Interview prep](https://www.databricks.com/company/careers/interview-prep), Engineering interview-prep PDF, April 2025):

Company-wide stages: identify roles → apply → Talent Acquisition → skill assessments → interviewing → reference checks → decision/offer.

FAQ:

- Timeline **typically 2–3 months** (role/region/team; holidays and exec hiring stretch it).
- **Recruiter call** → **pre-onsite** (HM screen, technical assessment, or skill eval) → **onsite loop of 4–6 interviews** → **presentation** for some GTM/exec roles.
- Interviews **virtual** (Google Meet) unless recruiter says otherwise.
- Feedback target: 48 hours after final interview; contact recruiter if >1 week.
- Behavioral: STAR-style “tell me about a time…” against shared competencies.

**Backend SWE panel (Official PDF):** Coding; Algorithms; System Programming (concurrency, I/O, caching); Architecture (CoderPad Draw); Domain Deep Dive; Cross-Functional/Hiring Manager. Language-agnostic but fluency required. Coding expects production-quality code, tests, edge cases, Big-O.

**FDE-specific (Candidate Reported, Aced, candidate-updated ~Aug 2026):**

Databricks launched a named FDE org in 2026 (candidate/prep-site claim; **confirm on careers**). Reported FDE loop (remote, 4–6 weeks):

1. Recruiter ~30 min  
2. Technical screen 45–60 min — SQL, data manipulation, light design, high-level RAG  
3. Coding ~60 min — practical function in a **notebook**, dicts/strings/lists, easy–medium  
4. **Decomposition** ~60 min — vague business goal → KPI, data, app layer, optional AI  
5. Leadership / values — six values reported: customer obsessed, raise the bar, truth seeking, operate from first principles, bias for action, put the company first  

Some customer-facing loops add a take-home or presentation panel. Hiring committee can still no-hire after strong rounds.

**Posted FDE base bands (Candidate Reported from July 2026 JDs, Aced):** Sr. FDE ~$180.7k–$248.4k; AI Engineer (FDE) federal ~$185.9k–$255.6k. Equity + bonus extra. Treat as JD text, not an offer.

**FDE vs SWE prep:** FDE = SQL + practical Python + decomposition + customer stories. Platform SWE = hard DSA + Spark/distributed systems. Do not prep them as the same loop.

---

### 3.3 OpenAI

**Official / Verified** ([Interview guide](https://openai.com/interview-guide/)):

Hiring values: consistent process, **not credential-driven**, collaboration, communication, feedback, mission alignment.

Example process (experience **may differ**):

1. **Application / résumé review** — typically ~1 week to hear back  
2. **Introductory calls** — hiring manager or recruiter; discuss work, motivations, goals; read the blog, especially team-relevant posts  
3. **Skills-based assessment** — formats vary: pair coding, take-homes, technical tests; may be more than one; recruiting provides prep; result within ~1 week  
4. **Final interviews** — default virtual, optional SF onsite; **4–6 hours with 4–6 people over 1–2 days**; stretch beyond comfort zone  
5. **Decision** — within ~1 week; references possible  

Engineering: well-designed solutions, high-quality code, optimal performance, **good test coverage**, communication of reasoning.

AI tools: **some formats allow them, some do not.** Ask recruiter if materials are unclear.

Recommended reading (official): [OpenAI Charter](https://openai.com/charter/), research publications, blog; Deep Learning Book; Spinning Up in Deep RL.

**Candidate Reported** (interviewing.io conversations with OpenAI engineers; IGotAnOffer):

- Decentralized; recruiter is source of truth.
- Common SWE path: recruiter → 60 min practical coding (CoderPad) → 60 min system design (Excalidraw) → onsite of coding, design, behavioral, **slides presentation** of a hard past project, possible **agentic coding beta**.
- Coding: practical multi-part (versioned KV, iterators, rate limiters, filesystem traversal); sometimes information theory / probability.
- Work trial / take-home: **team-dependent**. Some blogs claim a paid 48-hour NDA trial; others say many teams skip it. **Do not assume you will get a paid trial.**
- FDE flavor (FDEnest / Aced, Candidate Reported): Python, RAG/evals/tool-use design, **customer-pitch / go-to-deployment** round. OpenAI has not published a separate FDE loop on the interview-guide page.
- Timeline: official “within a week” between stages; end-to-end commonly 4–8 weeks in candidate reports; can compress with competing offers.
- Downleveling of incoming titles is a recurring candidate warning.

**Prep split:** 40% practical coding + tests, 25% system/LLM-systems design, 20% project presentation + STAR, 15% mission/safety literacy. LeetCode hard is low ROI unless the recruiter’s prep doc says otherwise.

---

### 3.4 Anthropic

**Official / Verified** ([Careers — How we hire](https://www.anthropic.com/careers), [Candidate AI guidance](https://www.anthropic.com/candidate-ai-guidance), last updated 10 Jul 2025):

- Care about **what you can do**, not where you learned it. ~half of technical staff had **no prior ML**; ~half have PhDs; some never went to college. Put independent research, blog posts, OSS at the top of the résumé.
- Engineers do research and researchers do engineering. If your background is engineering, **apply as an engineer**.
- All interviews on **Google Meet**.
- Technical: **Colab and CodeSignal**; look things up; share screen; fluency in syntax/stdlib required.
- Non-technical: conversational.
- Recruiters only email from `@anthropic.com`.
- Re-apply after 12 months (or sooner if material change).
- **AI usage:** draft résumé yourself then refine with Claude; take-homes **without** Claude unless allowed; live interviews **no AI** unless indicated; prep with Claude is encouraged.

**Candidate Reported** (interviewing.io, 2026 engineer conversations; Aced SWE guide):

| Stage | Notes |
|---|---|
| Recruiter 30 min | Mission alignment is a real filter. “Why Anthropic, not OpenAI / why safety-first.” B Corp framing. |
| Coding challenge 60–90 min | Often CodeSignal progressive spec (e.g. bank/transactions). Not stock LeetCode. Time-management fails are common. Referrals may skip. |
| Onsite 4–5 hours | Coding; system design (shared doc; LLM-serving / chat / practical systems); second coding; **company values** (deep, personal, hypothetical ethics; they want skepticism, not fanboying). HM may be before or inside onsite. |
| References | Taken seriously; conflict and ethical friction. |

**Values round reading (Candidate Reported, strongly recommended):** Dario Amodei, *Machines of Loving Grace* (2024); *The Adolescence of Technology* (Jan 2026); Anthropic *Core Views on AI Safety* (2023). Interviewers allegedly punish memorized talking points.

**FDE / Applied AI:** Anthropic’s careers page does not publish an FDE loop. Closest public analog is Applied AI / deployment work. FDEnest claims safety, reliability, evals, and incident handling show up more than at OpenAI. Treat as **Candidate Reported**.

**AI in interview:** Officially banned in live rounds. Do not confuse Anthropic’s “use Claude to prep” with “use Claude in the interview.”

---

### 3.5 Google

**Official / Verified** ([How we hire](https://www.google.com/about/careers/applications/how-we-hire/), [Interview tips](https://www.google.com/about/careers/applications/interview-tips/), historical How We Hire videos):

- Apply to at most **three jobs / 30 days**.
- Possible **Google Hiring Assessment** before interviews.
- Typical onsite: **3–4 interviews in one day**, video or in person.
- **No brain teasers** (longstanding official statement).
- Four attributes commonly cited in Google hiring communication: **General Cognitive Ability, Role-Related Knowledge, Leadership, Googleyness**.
- After interviews: written feedback → **hiring committee** (does not meet you) → senior review → team match → offer.
- DeepMind careers page (related, not identical): recruiter intro → skills interviews → decision.

**Candidate Reported (2026):**

- Recruiter → GHA → 1–2 technical phone screens → virtual/onsite loop of ~4–5: coding (2–4), code comprehension or **AI-assisted code comprehension** (select US teams, 2026), systems architecture (experienced), Googleyness & leadership.
- L4 now commonly gets system design (was less consistent historically).
- Team matching can add weeks to months.
- Coding still DSA-heavy; some interviewers go first-principles instead of a stock prompt.

**FDE / Cloud applied:** Google Cloud customer-engineering / applied AI roles add scenario rounds (**Candidate Reported**, FDEnest). Core Google SWE remains LeetCode-centric. **Gap:** no official “Google FDE” loop page found.

**LeetCode:** Highest justification of any company in this set, plus (new) AI-assisted code reading.

---

### 3.6 Microsoft

**Official / Verified** ([How we hire](https://careers.microsoft.com/v2/global/en/hiring-tips.html), [Technical interviewing](https://careers.microsoft.com/v2/global/en/hiring-tips/technical-interviewing.html)):

- Structured interviews; values: respect, integrity, accountability, growth mindset.
- **Most interviews include 2–4 conversations**, each up to an hour (phone, Teams, or in person). Candidate reports for senior SWE often say 4–5; both can be true.
- May write code, share a portfolio, or provide work samples.
- **Candidate Code of Conduct:** honest representation; **responsible AI in prep**; during assessments/interviews **no outside assistance unless explicitly permitted**.
- Technical lifecycle: **problem solving, design, coding, testing**.
- Coding: language you are strong in; **no pseudocode**; third-party tool that **runs** code; test before saying done (security, stress, boundaries).
- Algorithms: recursion; at least one n log n sort (ideally two); Big-O.
- Data structures: arrays/strings, queues/lists, linked lists, trees/tries, hash maps/sets, graphs.
- System design: distributed systems, SOA, n-tier, resiliency, HA, auto-scaling, replication, CAP, partitioning.
- AI/ML and data science listed as role-dependent areas.

**Candidate Reported:** Recruiter → technical phone or OA → loop of coding + design + HM + **As-Appropriate (AA)** senior interviewer who calibrates the bar. AA is widely reported but **not named on the current public how-we-hire page**.

**GenAI / Azure AI:** Official technical page includes ML pipelines and applying AI/ML algorithms. Azure AI / Foundry roles will add product-specific depth; still expect the core coding+design loop unless recruiter says otherwise.

---

### 3.7 Amazon / AWS

**Official / Verified** ([Interviewing at Amazon](https://www.amazon.jobs/landing_pages/interviewing-at-amazon), [Interview loop](https://amazon.jobs/content/en/how-we-hire/interview-loop), [SDE topics](https://amazon.jobs/content/en/how-we-hire/interview-prep/software-development-topics), [About Amazon interview guide](https://www.aboutamazon.com/news/workplace/amazon-interview-guide), [Leadership Principles](https://www.aboutamazon.com/about-us/leadership-principles)):

Published steps: **Online application → Assessments → Phone screening → Interview loop**.

Loop (official About Amazon, 8 Apr 2025):

- **4–6 interviews**, 45–60 min each.
- Mix of hiring manager, teammates, cross-functional stakeholders.
- **Bar Raiser:** interviewer from **outside** the hiring team; maintains the hiring bar.
- Technical roles: **~half** the process is technical (live coding, system design, problem-solving); remainder Leadership Principles.
- Behavioral answers: **STAR**, “I” not “we”, metrics, customer impact.
- Typical feedback: ~2 business days after phone screens; ~5 business days after the loop (may extend for senior/peak).

**16 Leadership Principles (Official):** Customer Obsession; Ownership; Invent and Simplify; Are Right, A Lot; Learn and Be Curious; Hire and Develop the Best; Insist on the Highest Standards; Think Big; Bias for Action; Frugality; Earn Trust; Dive Deep; Have Backbone, Disagree and Commit; Deliver Results; Strive to be Earth’s Best Employer; Success and Scale Bring Broad Responsibility.

Each interviewer is typically assigned a subset of LPs (**Candidate Reported**, consistent with Amazon’s own coaching that LPs are assessed throughout).

**SDE topics (Official):** programming language, data structures, algorithms, coding, OOD, databases, distributed computing, OS, internet topics, general ML/AI. Official sample OA: HackerRank coding test. Amazon publishes SDE I / II / III prep pages and an SDE interview prep course.

**GenAI:** Official topics include “general machine learning and artificial intelligence.” Some candidate reports mention a GenAI fluency round on some engineering loops — **not** on the official SDE topics page as a named round. Treat as team-dependent.

**FDE analog:** AWS Professional Services / Prototyping / GenAI specialist roles are closer to FDE than retail SDE. Loop still LP-heavy; expect customer-scenario plus coding.

---

### 3.8 Meta

**Official / Verified** ([Hiring process](https://www.metacareers.com/hiring-process), SWE interview Q&A / prep blogs):

- Recruiter call (or prescreen form for select roles) → interviews with peers, XFN, leaders → offer.
- Typical process **~2–3 months**.
- **AI in interviews (Official FAQ, current page):** many interviews include an **AI assistant built into CoderPad**. Candidates are **expected to use it**. Outside AI unauthorized. Assistant includes Claude, ChatGPT, Gemini, and Meta models; candidate picks a model. Design interviews: CoderPad + Mermaid Markdown + same assistant.
- AI-native coding languages: Python, Java, TypeScript, C++, C#, Kotlin, Swift, Rust, Go.
- Prep materials and a practice environment live in Career Profile.

Older official SWE blog (still circulated): 45-min screen = intro + **35 min coding, two problems** (algorithms, DS, recursion, binary trees) + questions.

**Candidate Reported:** Recruiter → 45-min coding screen (two easy–medium) → onsite **Ninja** (coding) / **Pirate** (design) / **Jedi** (behavioral). Mid-level: two coding, one–two design, one behavioral. Coding = hire/no-hire; design = level. AI-enabled round rolling out 2025–2026, often replacing one traditional coding round (60 min). Hiring committee + team match.

**LeetCode:** Still justified for the non-AI coding round and for speed. Also practice **directing and verifying an in-IDE agent** — that is now official.

---

### 3.9 NVIDIA

**Official / Verified** ([How we hire](https://www.nvidia.com/en-us/about-nvidia/careers/how-we-hire/)):

1. Search & apply (top 3–5 roles recommended; no hard cap).  
2. Meet hiring manager, teammates, other groups (phone, video, in person).  
3. **Onsite, in-person interview at an NVIDIA office is required before an offer** (Onsite Policy).  
4. Technical: coding exercise, usually **HackerRank**, whiteboard or provided laptop.  
5. **Use of unapproved outside tools such as ChatGPT during the interview = disqualification.**  
6. Interviews 30–60 min; one-on-one, small group, or panel.  
7. Optional **Insider Chat** (15 min, CRG member, does not influence hiring).  
8. Decision in a few weeks; duration varies.

**Candidate Reported:** Recruiter → technical phone (DSA + often C++/systems) → optional HM → onsite 3–6 rounds (coding, system design, **domain**: CUDA/GPU/OS/compilers, behavioral). Highly **team-specific**. Timeline ~6–8 weeks. GPU/CUDA roles can ask kernels; consumer-software teams look more like generic SWE.

**GenAI relevance:** NCP / DLI certs (see §5) are **learning tools**, not substitutes for the coding + domain loop.

---

### 3.10 Scale AI — FDE

**Official:** Careers postings exist for Forward Deployed Engineer (GenAI) and adjacent Frontier Agents Engineer. **No public round-by-round interview guide found** on scale.com as of access date.

**Candidate Reported** (Aced Scale FDE guide, candidate-updated; Glassdoor FDE; third-party 2026 writeups). Reports **conflict** on length (6–7 interviews vs up to 10; 2–4 weeks vs ~2 months). Treat the following as a **composite, not a guaranteed sequence**:

- HackerRank **project-style** OA (~60 min, hard, working system)
- Recruiter (FDE vs SWE preference; end-to-end ownership)
- Technical screen (HackerRank, completion over Big-O)
- Onsite mix: **credo** behavioral, project-style coding, **debugging unfamiliar repo** (sometimes with a live model endpoint), system design (ingestion, RAG, evals, token cost), hiring manager
- Some reports: customer simulation / presentation of a messy dataset; backend practical

**Credos (Candidate Reported, Aced — “current six”):** Earn Customer Love; Team Flow; Quality is Our Cheat Code; Find the 20%; Write the Market; Three Moves Ahead. Older lists (Run Through Walls, Why Not Faster) may be stale.

**Bar:** Aced: FDE shares SWE technical bar; placement FDE vs SWE often decided at HM. Solutions engineer is a lower technical bar (do not confuse).

**Posted base (Candidate Reported from JDs):** FDE GenAI ~$179.4k–$224.3k; Frontier Agents Engineer ~$180k–$225k (SF/NY/Seattle). Equity extra.

**Gap:** Official process unpublished; Glassdoor FDE sample is thin. Confirm every round with the recruiter.

---

### 3.11 Salesforce — FDE

**Official / Verified role, not loop** ([Salesforce blog, 19 Nov 2025](https://www.salesforce.com/blog/forward-deployed-engineer/)):

- FDE team launched **April 2025**; company has committed to building toward **1,000 FDEs** (company statement in that post).
- Work: Agentforce agents for nominated **Momentum** customers (free investment; paid FDE services planned).
- Pods: 1 deployment strategist + 2 FDEs; ~3 months per client / 1–2 use cases; sometimes onsite.
- Distinct from SI partners: FDEs bring product-team access and feed field insight back (example: Agentforce Observability).
- Skills: puzzle-solving, technical range (Apex, JS, prompts, integrations), executive communication, business acumen, learning mindset.
- Skill-building: Trailhead, specialist exams, **Agentblazer Legend**; new-hire **Ready in Six** (technical + field + capstone).

**Interview loop:** **Not published.** FDEnest groups Salesforce with “structured loops + applied scenario / customer engagement.” Treat as **unverified structure**. Recruiter is the only reliable source. Reasonable prep (not confirmed): Salesforce platform + Agentforce + a customer-scenario round + behavioral. LeetCode-hard is unlikely to be the bar unless the posting is a core SWE req.

**Cert note:** Trailhead badges help **learning and internal mobility**; they are not evidence that Salesforce FDE interviews are a cert exam.

---

### 3.12 India — product companies and services firms

Two different markets. Do not prep Infosys like Flipkart, or Flipkart like Palantir FDE.

#### Indian product (Flipkart and peers) — Candidate Reported unless noted

**Flipkart SDE (Candidate Reported: Glassdoor Jun 2026; GeeksforGeeks process page updated 2026; multiple 2026 guides):**

Common experienced-hire shape:

1. Online assessment (HackerRank/HackerEarth, 2–3 DSA medium–hard)  
2. **Machine coding** (~90–150 min): build a working, extensible console app from a vague spec (parking lot, splitwise, inventory); then a design-review conversation  
3. DSA live  
4. LLD and/or HLD (SDE-2+)  
5. Managerial / HR  

Glassdoor (22 Jun 2026, accepted offer): five rounds including machine coding 2–2.5 h, machine-coding evaluation, DSA, system design, managerial.

This is the closest **Indian analog to FDE practical coding**: ship working software under a time box, then defend extensibility. Still not a customer-decomposition round.

**Other Indian product (Candidate Reported, industry roundups 2026):** Zoho (multiple programming rounds, often unique/on-campus flavor); Razorpay / similar fintech (DSA + LLD + system design, FAANG-like). **FDE-titled loops at Indian product firms:** insufficient primary evidence as of access date.

#### Indian IT services — mass hiring vs specialist GenAI

**TCS (Candidate Reported + long-standing public NQT structure):** TCS National Qualifier Test (foundation: verbal/reasoning/numerical + programming logic; advanced coding for Digital/Prime tracks) → combined technical/managerial/HR panel. Tracks historically: Ninja vs Digital (and Prime in some cycles). Technical depth: projects, OOP, DBMS, SQL, light coding — **not** Palantir decomposition.

**Infosys (Candidate Reported):** InfyTQ / HackWithInfy pathways; tracks System Engineer / Specialist Programmer / Power Programmer with different coding bars. Typical fresher: aptitude → technical (OOP, DBMS, DSA, projects) → HR. SP/PP closer to real coding.

**Accenture (Candidate Reported):** cognitive + communication assessment + coding (for engineering) → technical → HR. Separate **Applied AI Engineer** Glassdoor hits exist (2026) but describe recruiter screens, not a standard FDE loop.

**GenAI in services:** Accenture, TCS, Infosys, Wipro, HCL, Deloitte, etc. staff “GenAI / Agentforce / Databricks FDE” **partner** roles. Interviews are usually: client-scenario + platform knowledge (Azure OpenAI, Bedrock, Databricks, Salesforce) + mild coding. **Evidence quality is low** (drive-by Glassdoor, YouTube placement coaches). If targeting a partner FDE role, ask whether the loop is the **vendor’s** (Databricks/Salesforce) or the **SI’s**.

**LeetCode justification (India):**

| Target | LeetCode | Extra |
|---|---|---|
| TCS Ninja / Infosys SE / Accenture ASE | Low–medium (basics) | Aptitude, verbal, projects, SQL |
| Infosys SP/PP, TCS Digital/Prime | Medium | Coding contests (HackWithInfy, NQT advanced) |
| Flipkart / top product | Medium–hard + **machine coding** | LLD |
| Google/Amazon India | Same as US SWE | LP / Googleyness |
| Partner FDE (Accenture on Databricks, etc.) | Low–medium practical | Platform + client story |

---

## 4. Certifications ROI

**Principle:** For FDE / GenAI at Palantir, OpenAI, Anthropic, Google, Meta, a cert almost never substitutes for a shipped system. Certs help (a) ATS keyword screens at enterprises and SIs, (b) structured learning, (c) regulated/federal JDs that list them. Salary-premium blogs that promise +$15–25k from one exam are **marketing**, not causal evidence.

### Higher ROI (learning + some employer value)

| Cert | Official home | Learning value | Employer value | Notes |
|---|---|---|---|---|
| **AWS SAA-C03** (Solutions Architect Associate) | [aws.amazon.com/certification](https://aws.amazon.com/certification/) | High if you will design VPC/IAM/S3/Lambda | High in AWS shops, SIs, startups on AWS | Broadest job-posting keyword among cloud associate certs. |
| **AWS MLA-C01** (ML Engineer Associate) / older MLS specialty | same | High for Bedrock + pipeline literacy | Medium–high for AWS GenAI JDs | Prefer the current associate ML path over trivia dumps. |
| **Azure AI Engineer** (AI-102 or successor) | [learn.microsoft.com/credentials](https://learn.microsoft.com/credentials/) | High for Azure OpenAI / AI Foundry | High in Microsoft-heavy enterprises (India + Fortune 500) | Microsoft enterprise footprint makes this more useful than prestige SWE shops. |
| **GCP Professional ML Engineer** or **Professional Cloud Architect** | [cloud.google.com/learn/certification](https://cloud.google.com/learn/certification) | High for Vertex | Medium volume, slightly “harder” exam reputation | Fewer postings than AWS; useful if targeting Google Cloud / Vertex shops. |
| **Databricks** Data Engineer / Generative AI Engineer Associate | [databricks.com/learn/certification](https://www.databricks.com/learn/certification) | High **if** you will work on Lakehouse / Mosaic | High for Databricks FDE, RSA, partner FDE | Low value at Palantir/OpenAI. High value at Databricks and SI partners. |
| **CKA** (Certified Kubernetes Administrator) | [cncf.io/training/certification/cka](https://www.cncf.io/training/certification/cka/) | High (hands-on) | Medium–high for platform/SRE; medium for FDE | Performance-based exam; closer to real skill than multiple-choice cloud assoc. |
| **NVIDIA NCP-GENL** (Generative AI LLMs) / **NCP-AAI** (Agentic AI, coming soon / new) | [nvidia.com/en-us/learn/certification](https://www.nvidia.com/en-us/learn/certification/) | Medium–high for NVIDIA stack | Medium: GPU infra shops, NVIDIA partners; low at labs | NCP-AII/AIO ($400–$500) are **infra ops**, not FDE software. DLI course certificates ≠ NCP exams. |

### Lower ROI (common traps)

| Credential | Why low ROI for these roles | Evidence type |
|---|---|---|
| **AWS Cloud Practitioner / Azure AI-900 / GCP Digital Leader** | Foundational multiple-choice; hiring managers at Palantir/labs/FAANG do not treat as signal | Official level is “foundational”; candidate reports and SWE forums consistently dismiss them for IC engineering |
| **Multi-vendor badge collecting** (5+ associate certs, no production) | Signals studying for exams, not shipping | Inferred from JD language at target firms: they ask for *experience*, not badge lists |
| **Vendor “legend” / trailblazer ranks as a substitute for a portfolio** | Salesforce Agentblazer is useful **learning** (Official Salesforce FDE blog) but is not an interview waiver | Official blog lists it as skill acquisition, not hiring criterion |
| **Generic Coursera/Udemy “GenAI professional certificates”** | No employer standard; overlap with free official docs | Not listed on any target-company official hiring page reviewed |
| **NVIDIA DLI workshop attendance badges without NCP** | Fine as a course receipt; not a professional cert | NVIDIA distinguishes DLI certificates vs NCP exams on official certification pages |
| **Expired or annual-renewal certs you will not use** | Azure associate renewals are yearly; cost is time | Official Microsoft credential policy |

**FDE-specific:** One cloud associate **in the cloud the customer uses** + Databricks or Salesforce **if that is the platform** is enough. A second cloud cert is usually worse than building one production-ish RAG/agent with evals and a writeup.

**Classic SWE at FAANG/labs:** certs are near-zero for the loop. Skip unless a JD explicitly requires them (federal/NVIDIA partner infra).

---

## 5. What portfolios look like

Interviewers at these firms say they want **evidence of shipped work** (Anthropic official: OSS, blogs, independent research on the résumé). “Portfolio” here means artifacts a recruiter or HM can verify in 10 minutes.

### Toy (will not move a Palantir / lab / Databricks FDE recruiter)

- ChatGPT wrapper around a public PDF with no evals, no auth, no deployment story  
- Tutorial-clone RAG (LangChain quickstart + Pinecone free tier) with a README that says “built a RAG app”  
- Notebook-only experiments with no API, no tests, no failure analysis  
- Certificate screenshots as the hero of GitHub  

These are fine as **personal learning**. They are not hiring evidence.

### Recruiter-worthy (mid-level FDE / Applied AI)

A single repo or 2-page case study that shows **one customer-shaped problem** end to end:

1. **Problem and user** — who operates it, what “good” means (metric).  
2. **Data reality** — messy inputs, PII, access control, what you would not put in a prompt.  
3. **Architecture** — retrieval, tools/MCP, orchestration (LangGraph or equivalent), serving (FastAPI), where it runs (K8s or a named cloud AI platform).  
4. **Evals** — golden set, failure taxonomy (hallucination, tool error, latency, cost), not just “demo works.”  
5. **Security** — at least two OWASP LLM Top 10 items you actually mitigated (injection, sensitive disclosure, excessive agency, etc.).  
6. **Operations** — logging, tracing, rollback, human-in-the-loop.  
7. **Narrative** — 3-minute walkthrough you can do in a HM screen without slides (OpenAI onsite often **wants** slides; Palantir usually does not).

Quality bar: a skeptical customer could ask “what happens when the wiki is stale?” and you have an answer.

### Senior / staff

Not more toys — **fewer, larger, owned**:

- Production incident or eval-regression you diagnosed  
- Migration onto Bedrock / Azure AI Foundry / Vertex / Databricks Mosaic with cost and latency numbers  
- Multi-agent system with permissioning, audit, and a killed feature (judgment)  
- Design doc + RFC-quality writeup  
- Evidence you changed a customer’s workflow, not just their prototype  

Palantir/Databricks/Scale HM rounds probe **metrics, trade-offs, failures**. A senior portfolio without a failure story is incomplete.

### Mapping artifacts to loops

| Artifact | Helps most at |
|---|---|
| Decomposition one-pagers (3 industries) | Palantir, Databricks FDE |
| Messy-data pipeline + tests | Palantir re-engineering/coding, Scale debugging, Flipkart machine coding |
| RAG + eval harness | OpenAI/Anthropic Applied, Databricks FDE, Scale |
| Agent + MCP tool with least-privilege | Agentic roles, Anthropic safety questions |
| Customer-retro writeup | All FDE behavioral |
| CUDA kernel / inference perf | NVIDIA |
| Spark/Delta job with SLAs | Databricks SWE/FDE data side |

---

## 6. High-quality learning resources (official docs first)

Use these as **source of truth**. Courses are secondary.

### Python

| Resource | Type | URL |
|---|---|---|
| Python language reference / tutorial | Official | https://docs.python.org/3/tutorial/ |
| Python standard library | Official | https://docs.python.org/3/library/ |
| PEP 8 | Official | https://peps.python.org/pep-0008/ |
| typing docs | Official | https://docs.python.org/3/library/typing.html |

FDE/lab interviews assume fluent stdlib (collections, itertools, pathlib, concurrent.futures, asyncio). Anthropic and Palantir explicitly reward not burning time on syntax lookup.

### FastAPI

| Resource | Type | URL |
|---|---|---|
| FastAPI user guide | Official | https://fastapi.tiangolo.com/ |
| FastAPI tutorial — first steps | Official | https://fastapi.tiangolo.com/tutorial/ |
| Pydantic v2 | Official | https://docs.pydantic.dev/latest/ |
| Uvicorn | Official | https://www.uvicorn.org/ |

Build: authenticated service, streaming responses, dependency-injected clients, pytest.

### RAG

| Resource | Type | URL |
|---|---|---|
| AWS RAG on Bedrock (Knowledge Bases) | Official | https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html |
| Azure RAG / AI Search + Foundry | Official | https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview |
| Vertex AI RAG / Grounding | Official | https://cloud.google.com/vertex-ai/generative-ai/docs/grounding/overview |
| OpenAI RAG / file search guidance | Official | https://platform.openai.com/docs/guides/tools-file-search |
| Anthropic RAG cookbook / docs | Official | https://docs.anthropic.com/en/docs/build-with-claude/retrieval-augmented-generation |
| Databricks Mosaic AI RAG | Official | https://docs.databricks.com/aws/en/generative-ai/retrieval-augmented-generation |

Interview bar: chunking trade-offs, embedding vs hybrid search, citation/grounding, evals, access control on chunks, failure when corpus is wrong.

### LangGraph

| Resource | Type | URL |
|---|---|---|
| LangGraph documentation | Official | https://docs.langchain.com/oss/python/langgraph/overview |
| LangChain LangGraph conceptual guide | Official | https://docs.langchain.com/oss/python/langgraph/ |

Practice: durable state, cycles, human-in-the-loop interrupt, tool nodes, what **not** to put in a graph (simple chains).

### MCP (Model Context Protocol)

| Resource | Type | URL |
|---|---|---|
| MCP specification / docs | Official | https://modelcontextprotocol.io/ |
| MCP GitHub (spec + SDKs) | Official | https://github.com/modelcontextprotocol |
| Anthropic MCP docs | Official | https://docs.anthropic.com/en/docs/mcp |

Interview bar: tools vs resources vs prompts; least privilege; supply-chain risk (OWASP agentic ASI04); don’t expose a raw shell as a tool.

### Kubernetes

| Resource | Type | URL |
|---|---|---|
| Kubernetes documentation | Official | https://kubernetes.io/docs/home/ |
| kubectl cheat sheet | Official | https://kubernetes.io/docs/reference/kubectl/cheatsheet/ |
| Tasks: configure a Pod, Deployments, Services | Official | https://kubernetes.io/docs/tasks/ |
| CKA curriculum (CNCF) | Official | https://www.cncf.io/training/certification/cka/ |

FDE-relevant slice: Deployments, probes, ConfigMaps/Secrets, Resource limits, Ingress, rolling update / rollback — not operator internals.

### AWS Bedrock

| Resource | Type | URL |
|---|---|---|
| Bedrock user guide | Official | https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html |
| Converse API / agents | Official | https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html |
| Guardrails | Official | https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html |
| Knowledge Bases (RAG) | Official | https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html |

### Azure AI Foundry

| Resource | Type | URL |
|---|---|---|
| Azure AI Foundry documentation | Official | https://learn.microsoft.com/azure/ai-foundry/ |
| Azure OpenAI in Foundry | Official | https://learn.microsoft.com/azure/ai-foundry/openai/overview |
| Content safety / responsible AI | Official | https://learn.microsoft.com/azure/ai-services/content-safety/ |

(Product naming has shifted from “Azure AI Studio”; use current Learn docs, not 2023 blog posts.)

### Vertex AI

| Resource | Type | URL |
|---|---|---|
| Vertex AI generative AI docs | Official | https://cloud.google.com/vertex-ai/generative-ai/docs |
| Vertex Agent Builder / grounding | Official | https://cloud.google.com/products/agent-builder |
| Model Garden | Official | https://cloud.google.com/model-garden |

### OWASP LLM / GenAI / Agentic Top 10

| Resource | Type | URL |
|---|---|---|
| OWASP Top 10 for LLM Applications 2025 | Official | https://genai.owasp.org/llm-top-10/ |
| LLM Top 10 2025 resource PDF landing | Official | https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/ |
| OWASP Top 10 for Agentic Applications (Dec 2025) | Official | https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/ |
| OWASP GenAI LLM Top 10 2026 (listed on initiative page) | Official | https://genai.owasp.org/initiative/owasp-top-10-for-llm-and-genai/ |

**LLM01–10 (2025 list, Official):** Prompt Injection; Sensitive Information Disclosure; Supply Chain; Data and Model Poisoning; Improper Output Handling; Excessive Agency; System Prompt Leakage; Vector and Embedding Weaknesses; Misinformation; Unbounded Consumption (10th item on the 2025 list — confirm current numbering on the live page before quoting in an interview).

**Agentic (2025/26, Official examples):** Agent Goal Hijack; Tool Misuse; Identity & Privilege Abuse; Agentic Supply Chain; Unexpected Code Execution; plus additional items on the published Top 10 for Agentic Applications.

For FDE interviews: be able to map **one mitigation you actually implemented** to Prompt Injection, Excessive Agency, and Vector/Embedding (RAG) weaknesses.

### Secondary (high quality, not a substitute for official docs)

- Palantir [Interviewing at Palantir](https://blog.palantir.com/interviewing-at-palantir-advice-from-palantirians-88444a90e7c4) — Official engineering-adjacent advice: authenticity, deconstruct problems, business context.  
- Amazon official SDE prep course: https://www.amazon.jobs/software-development-interview-prep  
- Google interview prep page: https://www.google.com/about/careers/applications/interview-tips/  
- Microsoft technical interviewing: https://careers.microsoft.com/v2/global/en/hiring-tips/technical-interviewing.html  
- Databricks engineering interview PDF: https://www.databricks.com/sites/default/files/2025-04/engineering-careers-site-interview-prep-april-2025-002.pdf  

---

## 7. Prep allocation (practical)

If you have **6 weeks** and are targeting FDE + one lab + one FAANG:

| Week | FDE-heavy candidate | Classic SWE-heavy candidate |
|---|---|---|
| 1–2 | Practical Python (FastAPI, parsing, SQL), 1 RAG with evals | LeetCode medium daily + complexity |
| 3 | Decomposition drills out loud (3 industries); Palantir-style learning on an unfamiliar repo | System design (DDIA-level) |
| 4 | Customer STAR stories; one agent + MCP tool; OWASP mapping | Design + LP/Googleyness/Jedi bank |
| 5 | Company-specific: Palantir why/Foundry; Databricks SQL+decomp; OpenAI slides | Company-specific coding patterns |
| 6 | Full mock: coding + decomp + behavioral | Full mock loop |

Do **not** spend this block on Cloud Practitioner or collecting five badges.

---

## 8. Gaps and conflicts (explicit)

| Item | Status |
|---|---|
| Palantir official onsite round names | Official site describes phone + personalized onsite, not “decomposition/learning/re-engineering.” Those names are **Candidate Reported**. |
| OpenAI FDE-specific loop | Not on the official interview guide. FDE rounds are **Candidate Reported**. |
| OpenAI paid 48h work trial | Conflicting candidate blogs. Official guide only says take-homes **may** occur. |
| Anthropic FDE / Applied AI round list | Careers page has tools and AI policy, not round names. |
| Databricks FDE org “launched 2026” | Prep-site claim. Official interview PDF is still SWE-shaped. Confirm live JDs. |
| Scale official loop | Not published. Candidate reports disagree on length and presence of customer simulation. |
| Salesforce FDE interview rounds | **Not published.** Only role/skills blog. |
| Google / Meta / Microsoft named FDE loops | Weak or absent official pages. |
| Decomposition “~40% pass / ~30% weight” | Repeated on FDE prep blogs; **no primary source**. Do not cite as fact. |
| Blind threads | Not systematically accessible without login; not used as primary evidence. |
| NVIDIA onsite-before-offer | Official. Remote-only loops contradict this — believe the careers page. |
| Meta AI-native interview | Official FAQ says many interviews **expect** in-environment AI. Older “no AI” advice is stale. |
| Indian services GenAI FDE | Thin evidence; partner vs vendor loops mixed. |
| OWASP LLM Top 10 2026 vs 2025 | Initiative page lists a 2026 update; use the live genai.owasp.org list on interview day. |

---

## 9. Source list

Access date for all: **2026-09-15** unless a page itself carries an older “last updated.”

### Official / Verified

1. Palantir Getting Hired — https://www.palantir.com/careers/getting-hired/  
2. Palantir Phone Interview — https://www.palantir.com/careers/getting-hired/the-phone-interview/  
3. Palantir Students & Early Talent (engineering process varies FDSE vs SWE) — https://www.palantir.com/careers/students-and-early-talent/  
4. Palantir open positions / FDSE titles — https://www.palantir.com/careers/open-positions/  
5. Palantir Blog, “Interviewing at Palantir: Our advice” — https://blog.palantir.com/interviewing-at-palantir-advice-from-palantirians-88444a90e7c4  
6. Databricks interview prep — https://www.databricks.com/company/careers/interview-prep  
7. Databricks Engineering interview prep PDF (Apr 2025) — https://www.databricks.com/sites/default/files/2025-04/engineering-careers-site-interview-prep-april-2025-002.pdf  
8. OpenAI Interview Guide — https://openai.com/interview-guide/  
9. Anthropic Careers / How we hire — https://www.anthropic.com/careers  
10. Anthropic Guidance on Candidates’ AI Usage (10 Jul 2025) — https://www.anthropic.com/candidate-ai-guidance  
11. Google How we hire — https://www.google.com/about/careers/applications/how-we-hire/  
12. Google Interview tips — https://www.google.com/about/careers/applications/interview-tips/  
13. Microsoft How we hire — https://careers.microsoft.com/v2/global/en/hiring-tips.html  
14. Microsoft Technical interviewing — https://careers.microsoft.com/v2/global/en/hiring-tips/technical-interviewing.html  
15. Amazon Interviewing at Amazon — https://www.amazon.jobs/landing_pages/interviewing-at-amazon  
16. Amazon Interview loop — https://amazon.jobs/content/en/how-we-hire/interview-loop  
17. Amazon SDE interview topics — https://amazon.jobs/content/en/how-we-hire/interview-prep/software-development-topics  
18. About Amazon, interview process guide (8 Apr 2025) — https://www.aboutamazon.com/news/workplace/amazon-interview-guide  
19. Amazon Leadership Principles — https://www.aboutamazon.com/about-us/leadership-principles  
20. Meta hiring process (incl. AI-native FAQ) — https://www.metacareers.com/hiring-process  
21. NVIDIA How we hire — https://www.nvidia.com/en-us/about-nvidia/careers/how-we-hire/  
22. Salesforce, “Forward Deployed Engineer: 5 Skills for This New Role” (19 Nov 2025) — https://www.salesforce.com/blog/forward-deployed-engineer/  
23. NVIDIA certification programs — https://www.nvidia.com/en-us/learn/certification/  
24. OWASP LLM Top 10 — https://genai.owasp.org/llm-top-10/  
25. OWASP Top 10 for Agentic Applications announcement (9–10 Dec 2025) — https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/  

### Candidate Reported / compilations

26. Aced (formerly Exponent), Palantir FDE interview guide — https://www.tryexponent.com/guides/palantir-forward-deployed-engineer-interview  
27. Aced, Databricks FDE interview guide — https://www.tryexponent.com/guides/databricks-forward-deployed-engineer-interview  
28. Aced, Scale AI FDE interview guide — https://www.tryexponent.com/guides/scale-ai-forward-deployed-engineer-interview  
29. interviewing.io, OpenAI interview process — https://interviewing.io/openai-interview-questions  
30. interviewing.io, Anthropic interview process (based on 2026 engineer conversations) — https://interviewing.io/anthropic-interview-questions  
31. FDEnest, FDE interview guide (28 May 2026) — https://fdenest.com/guides/forward-deployed-engineer-interview/  
32. Glassdoor, Palantir FDSE interviews — https://www.glassdoor.com/Interview/Palantir-Technologies-Forward-Deployed-Software-Engineer-Interview-Questions-EI_IE236375.0,21_KO22,56.htm  
33. Glassdoor, Scale FDE — https://www.glassdoor.com/Interview/Scale-Forward-Deployed-Engineer-Interview-Questions-EI_IE1656849.0,5_KO6,31.htm  
34. Glassdoor, Flipkart Software Engineer (incl. 22 Jun 2026 machine-coding report) — https://www.glassdoor.sg/Interview/Flipkart-Software-Engineer-Interview-Questions-EI_IE300494.0,8_KO9,26.htm  
35. IGotAnOffer, Amazon / Google / OpenAI process guides (used as secondary compilations of Glassdoor + official)  
36. GeeksforGeeks, Flipkart recruitment process (page updated 2026) — https://www.geeksforgeeks.org/interview-experiences/flipkart-recruitment-process/  

### Engineering blogs / role context

37. Databricks careers interview-prep FAQs (timeline, round counts) — same as source 6  
38. OpenAI Forum recruiting talks (2025) — qualitative “what we look for” (owners, builders, curiosity); not a round list  

---

*These notes are a research snapshot for a handbook, not a promise of any company’s current loop. Recruiter materials override everything above.*
