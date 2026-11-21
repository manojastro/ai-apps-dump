# 2026 Forward-Deployed Engineer job-market brief

**Access date:** 2026-09-15  
**Census observation date:** 2026-09-12  
**Audience:** career handbook (India-first, with global comparison)

This brief is evidence-based. Counts, salaries, and skill frequencies are taken only from sources inspected on the access date. Nothing here should be treated as a complete market census of India.

## Sample sizes (read this first)

| Corpus | N | What it is | What it is not |
| --- | ---: | --- | --- |
| Plank FDE job-market census | **1,333** | Title/metadata snapshot of roles whose title contains “Forward Deployed” / FDE, observed 2026-09-12, license CC BY 4.0 | Not full JD text; not a count of unique reqs; not India-complete |
| Official / ATS JDs read in full | **24** | Complete posting text from company career pages or ATS APIs (Lever, Greenhouse, Ashby job-board API, Databricks careers) | Not a random sample of all 1,333 census rows |
| Additional India board / aggregator JDs with substantial qualification text | **12** | Naukri, LinkedIn, Instahyre, Indeed, Cognizant careers, Microsoft careers mirrors | Some aggregator pages are noisy; Naukri HTML pages themselves returned HTTP access-denied on 2026-09-15 |
| **Total unique JDs whose qualification sections were read** | **36** | Used for the skill-frequency table and India notes | Not 1,333 |

**India location rows in the Plank census:** 29 of 1,333 (2.2%). Bangalore/Bengaluru 14; India-remote / India-unspecified 12; Hyderabad 2; Chennai 1; Gurugram 1; Pune / Noida / Mumbai / Kochi / Coimbatore **0** in the census location string.

The census under-counts India. Naukri’s public `fde-jobs` index (search snippet retrieved 2026-09-15; the HTML page itself was blocked) listed **180** “FDE” vacancies with city filters Bengaluru 83, Hyderabad 36, Chennai 29, Delhi/NCR 26. That index was **not** re-audited listing-by-listing; it mixes true FDE roles with retitled services jobs. Treat 180 as a **board-index upper bound**, not a verified FDE headcount.

---

## 1. What the Plank census shows (N = 1,333)

Source: Plank FDE job-market census, observed 2026-09-12, `count: 1333`, license CC BY 4.0.

### 1.1 Geography

| Region (census field) | Roles | Share |
| --- | ---: | ---: |
| United States | 728 | 54.6% |
| Other / unspecified | 198 | 14.9% |
| UK & Europe | 198 | 14.9% |
| Asia-Pacific | 94 | 7.1% |
| Remote | 50 | 3.8% |
| Canada | 25 | 1.9% |
| Latin America | 24 | 1.8% |
| Middle East | 16 | 1.2% |

Geo bucket: Coastal hubs 546; International 357; Other / unspecified 228; Heartland & Sun Belt 111; Remote (US) 91.

Asia-Pacific is **not** India-heavy. Of 94 APAC rows, Singapore 19, Tokyo/Japan ~13, Seoul/Korea ~10, Sydney/Australia ~12, and India-tagged locations are a minority (see §3). Palantir’s APAC census rows are Seoul, Sydney, Tokyo — **none in India**.

### 1.2 Seniority and title family

Census `seniority` field (encoder labels, not company levels):

| Seniority | N |
| --- | ---: |
| Mid-level / unspecified | 935 |
| Senior | 195 |
| Leadership | 85 |
| Early career | 61 |
| Staff / Principal | 57 |

Title-family parse of the raw `title` string (this brief, not a census field): IC unspecified/mid 899; Senior/Sr. 195; Staff/Principal 57; Manager 52; Intern 34; Director/Head 28; Lead 26; Founding 22; New grad 20.

Exact title **“Forward Deployed Engineer”**: 319. Unique titles: 672. 1,331 of 1,333 titles contain “forward deployed” / FDE (2 do not).

### 1.3 Verticals and employer mix

| Vertical | N |
| --- | ---: |
| Enterprise software | 741 |
| Data & AI platforms | 164 |
| Defense & data platforms | 108 |
| Foundation models | 59 |
| Automotive & robotics | 38 |
| Healthcare & pharma AI | 30 |
| Fintech & financial services | 28 |
| Voice & video AI | 24 |
| Data labeling & evals | 23 |
| Industrial & logistics AI | 20 |
| Consulting & staffing | 19 |
| Developer infrastructure | 18 |
| Other verticals (each ≤9) | 61 |

Unique companies: **565**. 367 companies have 1 role; 84 have 2; 114 have ≥3. Top 10 companies = 333 roles (25.0% of the census). Databricks + Palantir = 196 (14.7%).

Stage bucket: Private / undisclosed 814; Series C+ / late 215; Public company 119; Seed / stealth 93; Frontier lab 51; Series B 18; Series A 12; Consulting / SI 11.

### 1.4 Named-company counts (as requested)

Counts are **census rows**, not unique reqs. OpenAI is split because the census stores “OpenAI” and “OpenAI Deployment Company” as different `company` values.

| Company (census `company`) | Rows | India-tagged rows | Notes from live ATS check on 2026-09-15 |
| --- | ---: | ---: | --- |
| Databricks | 121 | 4 | Careers page also lists additional India FDE-adjacent roles (Staff FDE Remote-India, Sr FDE Remote-India, Deployment Strategist India) that the 12 Sep census did not all capture |
| Palantir | 75 | **0** | Live Lever FDSE postings confirmed; APAC = KR/AU/JP |
| Salesforce | 26 (+2 Airkit) | **0** | Careers URLs exist; the Salesforce.com job page did **not** return JD body (JS). Skills for Salesforce are **not** in the frequency table |
| OpenAI | 21 | **0** | Ashby board API returned 21 FDE-titled jobs on 2026-09-15 |
| OpenAI Deployment Company | 5 | 0 | AUS/EU/SGP/UK/US |
| Cohere | 20 | **0** | Ashby board API: 20 FDE jobs (agentic platform + infrastructure specialist + managers) |
| ElevenLabs | 18 | 0 | Ashby: 19 FDE-titled jobs, no India |
| Scale AI | 10 | **1** (“India”) | Greenhouse JD live |
| Mistral AI | 10 | **0** | Ashby: 13 Applied AI / FDE / pentester rows; no India |
| Anthropic | 7 | **0** | Greenhouse FDE live (NYC/SF/Seattle); federal-civilian variant also listed |
| Microsoft | 6 | **0 in census** | A **Bangalore** Microsoft FDE posting (job 200029969, posted 2026-06-30) exists on Microsoft Careers and was **not** in the 12 Sep census |
| Google | 4 | 0 | US Google Cloud FDE URLs from the census **404 / “job not found”** on 2026-09-15 |
| Amazon (AWS Data Services) | 2 | 0 | “Forward Deployed AI Integrator” |
| Amazon (AWS ProServe) | 1 | 0 | “Forward Deployed Engineer, WWPS ProServe”; amazon.jobs page did not return a usable JD body |

### 1.5 Salary bands **in the census** (posted ranges only)

388 of 1,333 rows (29.1%) include a numeric `[low, high]` salary. **0 of 29 India-tagged census rows have a salary.** Currency is not labeled in the JSON; US-region bands are consistent with USD. One Latin America row is `[5000, 6500]` (Handoff, São Paulo) and is almost certainly not annual USD — excluded from USD summaries below.

| Slice | N with salary | Median of band midpoint | Band-mid p10 / p90 | Min low – max high |
| --- | ---: | ---: | --- | --- |
| All numeric bands | 388 | $192,500 | — | $5,000 – $500,000 (includes non-USD outlier) |
| United States | 319 | $196,000 | $148,250 / $266,000 | $80,000 – $400,000 mid |
| Other / unspecified | 40 | $177,500 | — | — |
| Remote | 16 | $180,000 | — | — |
| Canada | 7 | $185,000 | — | — |
| UK & Europe | 4 | $211,000 | — | — |
| Asia-Pacific | **1** | $200,000 | — | n=1; **not India** |

US salary by census seniority (band midpoint):

| Seniority | N | Median mid | Min mid | Max mid |
| --- | ---: | ---: | ---: | ---: |
| Mid-level / unspecified | 243 | $185,000 | $80,000 | $355,500 |
| Senior | 34 | $203,000 | $130,000 | $300,000 |
| Staff / Principal | 21 | $241,944 | $175,045 | $330,000 |
| Leadership | 18 | $268,000 | $175,000 | $400,000 |
| Early career | 3 | $180,000 | $154,000 | $200,000 |

These are **posted ranges**, not accepted offers. They are overwhelmingly US.

Named-company posted ranges **when present in the census or live ATS**:

| Company | Posted base / salary (source) |
| --- | --- |
| Palantir FDSE (NY commercial; US Gov DC) | $135,000–$200,000 + RSUs / sign-on (Lever, accessed 2026-09-15) |
| Palantir FDSE New Grad Commercial (Chicago) | $135,000–$145,000 (TealHQ / Lever secondary, 2026-06-30 listing) |
| OpenAI FDE NYC/SF/Seattle | $185,000–$300,000 + equity (Ashby, 2026-09-15) |
| OpenAI Forward Deployed Software Engineer NYC | $153,000–$325,000 + equity (Ashby) |
| OpenAI FDE Gov | $145,800–$280,000 + equity (Ashby) |
| OpenAI Forward Deployed Security Engineer | $266,000–$445,000 + equity (Ashby / census) |
| Anthropic FDE | $280,000–$320,000 (Greenhouse, 2026-09-15; also in census for NYC) |
| Cohere FDE Agentic Platform | USD $140,000–$325,000 (CA/NY/WA); $120,000–$275,000 other US; CAD $175,000–$385,000 Canada (Ashby) |
| Microsoft FDE (US IC3, posting 1876152) | $100,600–$199,000 US typical; $131,400–$215,400 SF Bay / NYC (AnitaB mirror of Microsoft posting; **no longer accepting applications**) |
| Microsoft FDE (census US row) | $100,600–$215,400 |
| Google FDE IV GenAI (census, Detroit) | $207,000–$301,000 — **live Google Careers URL was down on 2026-09-15** |
| Amazon WWPS ProServe FDE (census) | $131,300–$177,600 |
| Amazon Forward Deployed AI Integrator (census) | $127,100–$172,000 |
| Cartesia FDE India (Bangalore) | **₹70,00,000–₹90,00,000 + equity** (Ashby compensation object, INR, 2026-09-15) |
| Databricks | Almost no salary in census (1 US National Security row $182,000–$250,208) |

---

## 2. Official JDs: required vs preferred skills

Read in full on 2026-09-15 unless noted. Quotes are paraphrased into requirement bullets; URLs are the live posting.

### Palantir — Forward Deployed Software Engineer (the origin role)

- **NY commercial (hybrid):** [Forward Deployed Software Engineer](https://jobs.lever.co/palantir/dab396d4-2f14-4796-aac0-0d82883dccf0), Palantir Technologies, accessed 2026-09-15. Salary $135k–$200k.
- **US Government, Washington DC (on-site):** [Forward Deployed Software Engineer - US Government](https://jobs.lever.co/palantir/289ad049-7b4e-41e3-8a39-146fbeb6fb64), Palantir, accessed 2026-09-15. Same salary band.

**Required / “What We Require”**
- 1+ years post-college (NY posting).
- Strong engineering background (CS, math, software engineering, physics, data science preferred as fields).
- Strong coder in **Python, Java, C++, TypeScript/JavaScript, or similar**.
- Travel up to 25% (NY); “willingness and interest to travel as needed” (USG).
- USG only: **active Top Secret clearance or willingness to obtain**.

**Valued, not framed as hard gates:** data structures, storage systems, **cloud infrastructure**, front-end frameworks; large-scale data; collaboration with technical and non-technical people.

**Not in these JDs:** RAG, LangChain, Kubernetes, SQL, “agents” as a named skill (USG Federal Health variant elsewhere mentions “deploying AI agents” in responsibilities). Palantir’s public Dev vs Delta framing: Dev = “one capability, many customers”; Delta/FDSE = “one customer, many capabilities.” ([Palantir Blog, “Dev versus Delta,” 2019](https://blog.palantir.com/dev-versus-delta-demystifying-engineering-roles-at-palantir-ad44c2a6e87).)

**India:** no Palantir India FDSE in the census; none found on Lever in this pass.

### Databricks — FDE and AI-FDE (including India)

Live on [databricks.com/company/careers](https://www.databricks.com/company/careers/open-positions) 2026-09-15.

| Posting | Location | URL |
| --- | --- | --- |
| Forward Deployed Engineer (`CSQ227R36`) | Remote - India | https://www.databricks.com/company/careers/open-positions/job?gh_jid=8432827002 |
| AI Engineer - FDE (`CSQ326R35`) | Remote - India | https://www.databricks.com/company/careers/open-positions/job?gh_jid=8099751002 |
| Senior Forward Deployed Engineer (`CSQ427R228`) | Bengaluru, India | https://www.databricks.com/company/careers/open-positions/job?gh_jid=8629999002 |

**FDE / Senior FDE (India) — “What we look for” (treated as required; the posting does not split preferred):**
- 6+ years in data engineering / data platforms & analytics (Senior Bengaluru: 6+ in data engineering, AI, data platforms).
- Code in **Python, Scala, JavaScript/TypeScript**, modern frameworks.
- Deep **Apache Spark** including runtime internals.
- Working knowledge of **two or more of AWS, Azure, GCP**, expertise in one.
- **CI/CD**; **MLOps / ML/AI models / AI APIs**.
- Production end-to-end data architectures combining pipelines, ML/AI, user-facing interfaces.
- Technical project delivery, documentation, whiteboarding, enterprise-client conflict management.
- Travel ~**20%**; **Databricks Certification**.
- Explicit: **FDEs are billable**.

**AI Engineer - FDE (Remote - India):**
- Building GenAI apps: **RAG, multi-agent systems, Text2SQL, fine-tuning**; HuggingFace, LangChain, DSPy.
- Production GenAI including **evaluation and optimizations**.
- Hands-on data science: pandas, scikit-learn, PyTorch.
- Production ML on AWS, Azure, or GCP.
- Graduate quantitative degree or equivalent.
- Teaching technical concepts.
- **Preferred:** Databricks Intelligence Platform and Spark at large scale.
- Travel once every 4–8 weeks.

LinkedIn mirrors (2026-08-28 / 2026-09-03) showed **“Over 200 applicants”** on both the India AI-FDE and Sr FDE postings.

### OpenAI — Forward Deployed Engineer (FDE) - NYC

[Ashby posting](https://jobs.ashbyhq.com/openai/9471b38b-f65c-4a01-9626-bd33fca90f1d), OpenAI, accessed 2026-09-15 via Ashby job-board API. Compensation object: **$185,000–$300,000 + equity**. Hybrid, 3 days in office, **travel up to 50%**. SF/Seattle FDE postings are the same JD with location swapped.

**“You might thrive” (the closest thing to requirements):**
- **5+ years** engineering or technical deployment including **customer-facing** work.
- Scoped and delivered complex systems in ambiguous environments.
- Production-grade code **frontend and backend using Python, JavaScript, or comparable stacks**.
- Built or deployed **LLM / generative-model** systems; understand model behavior vs product experience.
- Communication with engineers, product, and customer stakeholders.

**Responsibilities (not a skill list):** discovery, scoping, system design, build, production rollout, eval-driven feedback into Research/Product, playbooks. No RAG/K8s/SQL named.

Ashby listed **no India OpenAI FDE** on 2026-09-15 (US, London, Madrid, Seoul, Singapore, Sydney, Tokyo, Gov DC).

### Anthropic — Forward Deployed Engineer

[Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5302966008), Anthropic, NYC / SF / Seattle, accessed 2026-09-15. **$280,000–$320,000**. Hybrid ≥25% in office; travel estimated **25%**.

**“You May Be a Good Fit If You Have”:**
- **4+ years** in a technical **customer-facing** role (FDE) or SWE with consulting; former technical founders encouraged.
- Production **LLMs**: advanced prompt engineering, **agent development**, **evaluation frameworks**, deployment at scale.
- Strong **Python**; ideally another language (**TypeScript, Java**, etc.); shipping production applications.
- High agency in complex orgs; communication for discovery.
- **Plus:** financial services / healthcare / life sciences; enterprise IT / AI deployment patterns; prior FDE or professional services.

**Responsibilities name artifacts:** MCP servers, sub-agents, agent skills, white-glove deployment, repeatable patterns.

No India Anthropic FDE in census or Greenhouse sample.

### Scale AI — Forward Deployed Engineer, Gen AI (India)

[Greenhouse](https://job-boards.greenhouse.io/scaleai/jobs/4549048005), Scale AI, location **India**, updated 2026-09-09. Full-stack customer-facing data/GenAI infrastructure.

**Requirements (posting):** ≥4 years *preferred*; shipping products at scale; independent problem-solving; turn business ideas into engineering; **strong coding** and communication to technical and non-technical audiences.

**Application form hard questions:** proficiency in **Python or JavaScript/TypeScript**.

**Preferred:** large-scale data processing / distributed systems; ML/AI concepts; enterprise customers; **cloud infrastructure**.

### Cohere — Forward Deployed Engineer, Agentic Platform

[Ashby](https://jobs.ashbyhq.com/cohere/b0bcef37-1d20-414f-aade-c54942d63df9), Cohere, United States (same template used across regions). Travel **20–40%**. Compensation: US CA/NY/WA **$140k–$325k**; other US **$120k–$275k**; Canada **CAD $175k–$385k**; all + equity.

**Good fit (required-like):**
- Production **Python**.
- Production **RAG and agentic** apps (ReAct / Plan-and-Execute).
- LLM stack: frontier models, **vector databases**, orchestration frameworks.
- **Evaluation frameworks** for accuracy, safety, latency.
- Direct customer technical discussions; end-to-end use-case ownership.

**Bonus:** architectural standards; frontend flexibility; regulated industries; **enterprise security / compliance / auditability**.

No India location on the Cohere FDE board (Singapore, Korea, UK, Middle East, North America).

### Mistral AI — Applied AI, Forward Deployed Machine Learning Engineer (Palo Alto)

[Ashby](https://jobs.ashbyhq.com/mistral.ai/2ec2dacd-1117-479b-a4c1-efa9df530798), Mistral AI, Palo Alto, accessed 2026-09-15. No compensation object.

**Looking for:**
- Fluent English; **PhD/master in AI/data science**.
- **2+ years** IC on AI products (DS or SWE).
- **Fine-tuning LLMs**, advanced **RAG or agentic** use cases.
- Deep ML/LLM concepts; deploying LLMs/NLP.
- APIs, **back-end and front-end**.
- **Python**; **PyTorch**.
- Agents frameworks such as **LangChain**, **vector DBs**.
- Communication to technical and non-technical audiences.
- Pre-sales through post-implementation customer work.

**Ideal:** open-source LLM work; prior **Customer Engineer / FDE / Sales Engineer / Solutions Architect / TPM**.

No India Mistral FDE.

### Microsoft

**US FDE (closed posting, still mirrored):** [Forward Deployed Engineer (FDE)](https://jobs.anitab.org/companies/microsoft/jobs/59269026-forward-deployed-engineer-fde), Microsoft via AnitaB.org, job 1876152, posted 2025-09-23, Mountain View, **no longer accepting applications**. Base $100,600–$199,000 ($131,400–$215,400 SF Bay/NYC).

**Required:** Bachelor’s CS + **2+ years** coding in C, C++, C#, Java, JavaScript, or Python (or equivalent); **2+ years DevOps** (CI/CD, containerization, IaC); **2+ years** system security, scalability, reliability, maintainability; **1+ year** designing/implementing **ML/LLM solutions in production**; Microsoft Cloud background check.

**Preferred:** Master’s + 3 years or Bachelor’s + 5 years; generative AI product features; **prompting and fine-tuning**; coaching engineers.

**India, Bangalore (live on Microsoft Careers, not in 12 Sep census):** job **200029969**, posted **2026-06-30**, location India, Karnataka, Bangalore, 3 days/week in-office, travel <25%. Required qualifications snippet: Bachelor’s CS **AND 1+ years** coding in C, C++, C#, Java, JavaScript, or Python *or equivalent*. Full remaining qualification list was not recoverable from the JS-heavy careers app on 2026-09-15.

### Salesforce, Google, AWS — verification status

| Employer | Status on 2026-09-15 |
| --- | --- |
| **Salesforce** Agentforce / Data 360 FDE | Career URLs exist (e.g. [JR357427 Agentforce Orchestration](https://www.salesforce.com/company/careers/jobs/JR357427/forward-deployed-engineer-fde-agentforce-orchestration/)). Page returned no JD body. **Skills not coded.** Census: 26 Salesforce + 2 Airkit rows; **0 India**. |
| **Google Cloud FDE** | Census had 4 US rows. Direct Google Careers URL for FDE II GenAI returned **“Job not found.”** A Naukri aggregator listing “Senior Forward Deployed Engineer, Cloud Applied AI - Bengaluru - Google” (5–10 years; Vertex AI, BigQuery, Cloud Storage, Dialogflow, agents) was **not** confirmed on Google Careers. |
| **AWS / Amazon** | Census: 3 US rows (AI Integrator + WWPS ProServe FDE) with posted USD bands. `amazon.jobs` apply URL did not yield a usable JD. **Skills not coded from official AWS text.** |

### India company JDs read in full (ATS)

| Company | Title / location | Distinct requirement highlights | URL |
| --- | --- | --- | --- |
| Cartesia | FDE (India), Bangalore | **4+ years** production systems; **backend**; APIs; **AWS, GCP, Kubernetes**; auth/networking/observability/**security reviews**. Nice: prior FDE, production AI/ML, real-time voice, on-prem, multilingual. **₹70–90 L + equity.** In-office SF/London/**Bangalore**. | https://jobs.ashbyhq.com/cartesia/6d860f5a-b9d9-4df2-b5e5-b12ac80632a4 |
| DevRev | FDE, Bangalore (also Chennai / India Remote) | **5+ years** SWE/integration; **TypeScript/JavaScript, Python** (Go nice); **LLMs, prompt, RAG, function calling, evals**; REST/GraphQL/webhooks; **AWS Lambda / GCF**, CI/CD, containers, observability; **SQL**; **MCP**. Customer-facing is a **plus**, not a gate. 50% client / 50% internal. | https://job-boards.greenhouse.io/devrev/jobs/6174459004 |
| MongoDB | Staff FDE, Gurugram | **9+ years**; production systems and complex customer/enterprise environments; travel **up to 30%**. **Preferred:** LLMs, agent frameworks, retrieval, evals, prior FDE. Hybrid Gurugram. | https://www.mongodb.com/careers/job/?gh_jid=8094522 |
| HackerRank | FDE, Hybrid Bengaluru | Customer-facing technical lead; full-stack enough to configure/debug; **Ruby or Python** + APIs. Even better: SE / solutions / sales engineer in HR tech. | https://job-boards.greenhouse.io/hackerrank/jobs/7461142 |
| Emergent Labs | FDE, Bangalore | Web apps, APIs, databases, integrations; **customer-facing**; **AI/LLM tools a plus**; **night shift** for US/EU hours. | https://job-boards.greenhouse.io/emergentlabsinc/jobs/4335496009 |
| Nanonets | FDE, Bengaluru | **2+ years** FDE/SWE/ML; chatbot / **agentic workflows / RAG**; frontend system design **and** backend APIs/auth. | https://jobs.ashbyhq.com/nanonets/c3715ba7-2924-4432-b78e-3acc56b8e823 |
| Handshake | FDE I, India | **3+ years**; **TypeScript, React**, modern backend; PostgreSQL/APIs; also lists **Kubernetes, Docker, AWS, GCP, CI/CD, RAG** in posting text. | https://jobs.ashbyhq.com/handshake/f632f0c3-0b9c-49a7-984b-de92e18e6d0b |
| LiveKit | FDE, India (Remote) | Customer engineering (remote or on-site); real-time / voice AI architectures; Python/backend in posting. | https://jobs.ashbyhq.com/livekit/2702511f-38b1-41b3-906d-6d1976c8789a |
| Blitzy | FDE, India HQ (JD text: **Pune HQ2**) | Embed with customer engineering; production code; agentic SDLC platform; Java/SQL/Docker/CI/CD/cloud/security appear in posting. | https://jobs.ashbyhq.com/blitzy/595eaf74-0388-470c-8efd-6f1cac5c2688 |
| Kognitos | FDE, Bengaluru | End-to-end account ownership (NPS, adoption, TTV); process discovery; Python/RAG/agents/LLMs in posting. | https://jobs.ashbyhq.com/kognitos/82c74eb6-5e5f-4aae-ba2c-02e764c40084 |
| Reltio (SAP) | Staff FDE, Bangalore | Staff-level customer + MDM/agent-flow; security/compliance/multi-cloud; Python/Java/TS/RAG/agents/LLM/CI/CD in posting. | https://job-boards.greenhouse.io/reltio/jobs/6136088004 |
| Arcesium | FDE, Bengaluru; Hyderabad | Internal+business FDE: agents, MCP, LLM prototypes, security partnership. | https://job-boards.greenhouse.io/arcesiumllc/jobs/5207754007 |
| Redwood Software | Forward Deployed Senior SWE, Hyderabad | Migration tooling for RunMyJobs; PS × product engineering hybrid — **not** a GenAI-first JD. | https://job-boards.greenhouse.io/redwoodsoftware/jobs/4129751009 |
| Augrade | FDE (Design + Modeling), Bangalore | BIM/design execution — **not** a software FDE. Included only as a census India row. | https://jobs.ashbyhq.com/augrade/a5772a05-3579-4ae7-ae42-7476d64ed0f7 |

Razorpay Bengaluru census URL 404’d on Greenhouse (2026-09-15).

### India services / product JDs with substantial text (not always official career pages)

These **12** were read from Naukri/LinkedIn/Instahyre/Cognizant/Microsoft snippets. Naukri HTML was access-denied; text comes from search-index extracts dated 2026-09-15.

| Employer | Location | YoE on posting | Skills named in the extract | Source |
| --- | --- | --- | --- | --- |
| Cognizant | Bangalore / Chennai onsite | Junior FDE originally; page now titled **AI Customer Engineer** | Google ADK or Copilot Studio / CrewAI / AutoGen; RAG; vector DBs; Python libraries; LangChain/HF/OpenAI API; FastAPI; Docker; GitHub; SQL; cloud | [Cognizant careers 00067697573](https://careers.cognizant.com/us-en/jobs/00067697573/ai-engineer-forward-deployed-engineer/), published 2026-06-03, accessed 2026-09-15 |
| Accenture | Hyderabad | 7–12; min 7.5 | Must: **Generative AI**. Good to have: **Python**, **AI Agents Workflow Integration** | Naukri search extract, 2026-09-15 |
| Adobe | Noida | 3–8 | Full-stack React/Next/Angular; Node/Java Spring; REST/GraphQL; Firefly APIs; GenAI apps | Naukri search extract |
| Infosys | Bengaluru | 6–15 | Client workshops; LLMs; agentic coding; APIs; cloud; “onshore anchor” for engineering pods | Naukri search extract |
| Kyndryl | Mumbai | 3–6 | ≥1 year agentic AI frameworks; ≥2 years GenAI | Naukri search extract |
| Cornerstone OnDemand | Hyderabad office | 2–7 | Azure OpenAI / AI Studio / ML / Cognitive; Copilot Studio; prompt, **RAG**, fine-tuning, **multi-agent** | Naukri search extract |
| Prodapt | Chennai / Bangalore / Hyderabad / Pune | 6–12 | Data eng + full-stack + DevOps; **≥1 year dedicated AI presales** (delivery-only does not qualify) | Glassdoor/Prodapt extract |
| Visionet | Bengaluru | 9–12 | Azure AI, Copilot, DevOps (GitHub, Jenkins, Docker), CI/CD | Naukri extract |
| Allianz Technology | Pune / Trivandrum | 6–8 | **Databricks** notebooks/jobs/pipelines, customer enablement | Naukri extract |
| Boomerang | Pune | 3–5 (Instahyre 2–6) | Python (Java/Go/JS ok); REST/GraphQL; SQL/NoSQL; AWS/GCP/Azure; Git/CI/CD; Voice/GenAI preferred | [Instahyre](https://www.instahyre.com/job-411617-forward-deployed-engineer-at-boomerang-pune/) |
| Google (unverified aggregator) | Bengaluru | 5–10 | Agents; Vertex AI, BigQuery, GCS, Dialogflow; GenAI/LLM/multimodal | Naukri extract — **not confirmed on Google Careers** |
| Microsoft | Bangalore | 1+ years coding | See Microsoft section above | Microsoft Careers job 200029969 |

**Cutshort:** no usable FDE posting was retrieved on 2026-09-15.  
**Instahyre:** 2 JDs with readable text (Boomerang Pune; Stable Money Bangalore — the Stable Money body looked **copied from HackerRank** and is treated as untrustworthy).

---

## 3. India vs global

### 3.1 Census India is a thin slice of a US-heavy market

Global FDE hiring in this snapshot is a **US coastal + Europe** market with a secondary APAC hub in Singapore/Tokyo/Seoul/Sydney. India is present as:

- **Remote-India delivery arms** of US platforms (Databricks, Scale AI, Handshake, LiveKit, Komodo).
- **India product companies** adopting the title (DevRev, Razorpay, Nanonets, Kognitos, Sarvam AI, Peakflo, HackerRank, Cartesia Bangalore office).
- **Staff+ seats in GCCs** (MongoDB Gurugram, Reltio Bangalore, Redwood Hyderabad, Arcesium Bengaluru/Hyderabad).

Frontier labs in the census (**OpenAI, Anthropic, Cohere, Mistral**) had **zero India FDE rows**. Palantir had zero. Salesforce had zero.

That is **not** the same as “they never hire in India.” Microsoft’s Bangalore FDE posting is a concrete counterexample that the census missed. It **is** evidence that as of 12–15 Sep 2026, the branded FDE title on lab career pages is still concentrated in US/EU/APAC financial hubs, while India demand is a mix of (a) platform FDEs, (b) startup FDEs, (c) IT-services jobs retitled FDE.

### 3.2 India city picture (two layers)

**Layer A — Plank census location strings (N=29):**

| City / tag | Census rows |
| --- | ---: |
| Bangalore / Bengaluru (including hybrid) | 14 |
| India / Remote-India / India HQ / India unspecified | 12 |
| Hyderabad (incl. dual Bengaluru; Hyderabad) | 2 |
| Chennai | 1 |
| Gurugram | 1 |
| Pune, Noida, Mumbai, Kochi, Coimbatore, Delhi | 0 |

Blitzy’s ATS text says **Pune HQ2** even though the census location is “India HQ.”

**Layer B — India job boards (not census, not fully audited):**

Naukri `fde-jobs` index snippet, 2026-09-15: 180 vacancies; Bengaluru 83, Hyderabad 36, Chennai 29, Delhi/NCR 26. Direct page fetch failed (Akamai access denied).

Inspected India JDs in this brief additionally name **Pune** (Blitzy, Boomerang, Allianz, Prodapt, Zensar aggregator), **Noida** (Adobe), **Mumbai** (Kyndryl; Z47 portfolio JD also listed Mumbai/Gurugram), **Gurugram** (MongoDB; Accenture also listed on Naukri), **Trivandrum** (Allianz), **Chennai** (DevRev, Cognizant, Prodapt). **Kochi and Coimbatore: no verified FDE JD** in this pass.

### 3.3 What “FDE” means in India vs at Palantir/OpenAI

| Employer type (India, from JDs actually read) | What the job is |
| --- | --- |
| Palantir-style / frontier lab (mostly **not India**) | Embed, write production code, own outcome, travel 25–50%, generalist SWE + customer |
| Databricks / MongoDB / Reltio India | Billable or staff field engineering on a **specific platform**; Spark/MDM/data; 6–9+ years |
| Cartesia / DevRev / Nanonets / LiveKit / Handshake | Startup FDE: backend + agents/voice/RAG + enterprise constraints |
| Infosys / Accenture / Cognizant / Kyndryl / Prodapt | Often **retitled** AI implementation / presales / Copilot / agent build-out; YoE bands 3–15; GenAI sometimes a “must have” with Python only “good to have” (Accenture Hyderabad extract) |
| Emergent Bangalore | Night-shift customer engineering for a coding-agent product |

The title is being used for at least four jobs. A Naukri “Forward deployment Engineer” at Han Digital (Chennai, 5–10 years) was generic boilerplate (“forward deployment strategies”) and is **not** treated as a real FDE role.

---

## 4. Skill-frequency table (inspected JDs only)

**Denominator:** 24 full-text official/ATS JDs listed in §2 (Palantir ×2, OpenAI FDE NYC, Anthropic, Databricks ×3, Scale India, Cohere Agentic, Mistral Palo Alto, Microsoft US closed posting, Cartesia, DevRev Bangalore, MongoDB, HackerRank, Emergent, Nanonets, Handshake FDE I, LiveKit India, Blitzy India, Kognitos, Reltio, Arcesium, Redwood). Augrade (BIM) is **excluded** as not a software FDE.

**Coding rules:** a skill is **Required** if it appears in a required / “what we require” / “what we look for” / “you may be a good fit” / “what you bring” section, or in an application-form hard question. It is **Preferred** if only in preferred / nice-to-have / bonus / plus / “even better.” Responsibilities-only mentions are counted in **Any mention**. A language listed as “Python, Java, C++, or TypeScript/JavaScript” counts for **each named language**.

| Skill | Required | Preferred only | Any mention (incl. responsibilities) | Required % of 24 |
| --- | ---: | ---: | ---: | ---: |
| Customer-facing / embed / on-site / travel | 22 | 1 | 24 | 92% |
| Python | 16 | 1 | 18 | 67% |
| Cloud (AWS and/or Azure and/or GCP) | 12 | 3 | 18 | 50% |
| Agents / agentic / MCP / multi-agent | 11 | 3 | 18 | 46% |
| LLM / GenAI | 11 | 3 | 17 | 46% |
| Backend / APIs / REST / GraphQL | 11 | 2 | 16 | 46% |
| TypeScript and/or JavaScript | 10 | 1 | 12 | 42% |
| RAG | 7 | 2 | 11 | 29% |
| Evaluation / evals | 7 | 2 | 12 | 29% |
| Security / compliance / clearance / auth | 6 | 3 | 14 | 25% |
| CI/CD | 6 | 1 | 10 | 25% |
| Docker / containers | 5 | 2 | 9 | 21% |
| SQL | 5 | 0 | 7 | 21% |
| Java | 5 | 0 | 6 | 21% |
| Frontend / React / full-stack | 5 | 2 | 10 | 21% |
| Prompt engineering | 5 | 2 | 8 | 21% |
| Kubernetes | 3 | 1 | 5 | 13% |
| Spark / Databricks platform internals | 3 | 1 | 5 | 13% |
| Fine-tuning | 3 | 1 | 5 | 13% |
| LangChain / DSPy / HuggingFace | 3 | 0 | 4 | 13% |
| Vector DBs | 3 | 0 | 4 | 13% |
| MLOps / LLMOps | 3 | 0 | 4 | 13% |
| C++ | 3 | 0 | 3 | 13% |
| Scala | 2 | 0 | 2 | 8% |
| Go | 0 | 2 | 3 | 0% |

**How to read this:** customer-facing work is the only near-universal requirement. Python is the default language but Palantir/Microsoft still list Java/C++/C# as acceptable. **RAG and agents are common in 2026 lab/startup/Databricks-AI JDs and rare in classic Palantir FDSE and in some platform FDEs (MongoDB Staff lists them as preferred).** Kubernetes is **not** a default FDE gate (explicit in Cartesia, Handshake; containers more often via Docker/CI/CD). SQL appears when the product is data-heavy (DevRev, Handshake, Cognizant) and is absent from OpenAI/Anthropic/Palantir core FDE text.

**Supplementary India-board JDs (N=12, not in the table):** they raise the weight of **Azure/Copilot**, **presales**, and **GenAI-as-must-have** (Accenture, Cornerstone, Visionet, Prodapt, Kyndryl). Including them would overstate Azure Copilot relative to the global branded-FDE market.

---

## 5. Pay: the Mint ₹1.55 crore figure, and what is actually posted

### 5.1 What Mint published (verified)

[“Plenty of coders, few AI implementers: Why Forward Deployed Engineers can earn up to ₹1.55 crore in India,”](https://www.livemint.com/ai/artificial-intelligence/plenty-of-coders-few-deployers-india-s-ai-skill-gap-sparks-rs-1-55-crore-salary-boom-11789442981155.html) Arshdeep Kaur, *Mint* / HT Media, **published 15 Sep 2026, 09:30 IST**. Accessed 2026-09-15.

The article attributes numbers to **FDE Academy**, *The Forward Deployed Engineer Talent Landscape in India* (not independently re-run here). It reports:

| Experience (study bands) | “Forward-deployed AI builders” indicative **median** |
| --- | --- |
| 0–3 years | ₹32 lakh |
| 4–8 years | ₹55 lakh |
| 9–15 years | ₹88 lakh |
| **Above 15 years** | **₹1.55 crore** |

Other study claims in the same article: employer demand 95% vs talent supply 45% (50-point gap); product/frontier platforms ₹1.35 crore median at 7+ years vs ₹85 lakh Big Tech, ₹80 lakh AI-first startups, ₹55 lakh IT services; junior 0–3 years ₹52 lakh product vs ₹22 lakh IT services; 30–50% premium for verified production-deployment experience.

**Do not treat ₹1.55 crore as typical.** In the article’s own table it is the **15+ year median** of one study’s “forward-deployed AI builders” family, not a modal India offer, not a new-grad number, and not a figure this brief could re-derive from offers or tax filings.

The underlying FDE Academy PDF/methodology (sample, employer mix, cash vs total comp, whether ESOPs are included) was **not located as a primary document** on 2026-09-15.

### 5.2 Posted / named India compensation that **was** verified

| Figure | What it is | Source |
| --- | --- | --- |
| **₹70–90 lakh + equity** | Cartesia FDE India, Bangalore, official Ashby compensation object (INR salary) | Cartesia ATS, 2026-09-15 |
| Census India salaries | **None** (0/29) | Plank census 2026-09-12 |
| Glassdoor New Delhi FDE | ₹1.1–1.6 million total pay, ₹1.4M median (~₹11–16 LPA) | Glassdoor search-result extract, page date 2026-09-12. **Small, noisy, not reconciled** |
| Glassdoor India FDE (older page) | ~₹12 LPA average base, 13 salaries, “as of November 2025” | glassdoor.co.in extract |
| India Today quotes (17 Jul 2026) | Bengaluru “average ~₹17 LPA, typical ~₹11–36 LPA”; senior large-enterprise “₹50–80 LPA (and higher)” — **named interviewees, not a dataset** | [India Today](https://www.indiatoday.in/technology/features/story/forward-deployed-engineers-are-in-demand-but-what-is-fde-and-how-to-become-one-2949961-2026-07-17) |
| TeamLease via Moneycontrol (21 Jul 2026) | Entry FDEs ₹18–25 LPA; mid ₹30–45 LPA | [Moneycontrol](https://www.moneycontrol.com/artificial-intelligence/entry-level-fdes-earn-up-to-7-times-more-than-software-developers-starting-at-rs-18-lakh-article-13979349.html) |
| TeamLease via *The Hindu* (15 Jul 2026) | Entry ₹10–12 LPA; mid ₹25–50 LPA; senior ₹50–80 LPA+ | [The Hindu](https://www.thehindu.com/education/forward-deployed-engineering-next-wave-of-ai-career-opportunity/article71216987.ece) |

**These secondary India bands contradict each other** (entry ₹10–12 vs ₹18–25 vs Mint’s ₹32 lakh median). This brief does **not** average them. The only **employer-posted** India FDE cash range verified in ATS is Cartesia’s **₹70–90 L**, which sits in Mint’s mid-to-senior study band and is **not** evidence for the 15-year ₹1.55 crore cell.

UnoJobs’ “Databricks India AI Engineer FDE · ₹18 Lacs” is an aggregator estimate and is **not** treated as Databricks compensation.

### 5.3 US posted ranges vs India

Using only posted ATS/census bands: US FDE mids cluster **~$150k–$250k** base (census US median mid $196k, n=319). Frontier-lab FDE bases are higher (OpenAI $185–300k; Anthropic $280–320k). Palantir still posts **$135–200k** for core FDSE. India official posting evidence is too thin to compute a median; Cartesia ₹70–90L is roughly 0.4–0.6× an OpenAI FDE base at 2026 FX, before equity, and is a **startup Bangalore** role, not a lab role.

---

## 6. Role comparison (FDE vs SWE vs SE vs SA vs CE vs implementation consultant)

Grounded in Palantir’s own Dev/Delta split, OpenAI/Anthropic/Databricks JDs, and the India services postings above.

| Dimension | **FDE / FDSE** | **SWE (product)** | **Sales Engineer / Solutions Engineer (SE)** | **Solutions Architect (SA)** | **Customer Engineer (CE)** (Google/cloud usage) | **Implementation consultant / PS** |
| --- | --- | --- | --- | --- | --- | --- |
| Primary job | Make **this customer** succeed in production, writing code in their environment | Make **the product** work for many customers | Win the deal: demo, PoC, technical close | Design the target architecture; often not the person who stays to build | Technical adoption of a cloud/product; mix of advise + light build | Configure a package / SI scope to a statement of work |
| Palantir frame | Delta: “one customer, many capabilities” | Dev: “one capability, many customers” | Adjacent (Palantir Deployment Strategist is closer to SE/DS than FDSE) | — | — | Palantir explicitly says a Delta is **not** a consultant |
| Code | Required in every branded JD in this sample | Required | Sometimes (PoCs); many SEs do not own production | Architecture diagrams > production code | Varies; Google CE historically less “write the app” than FDE | Config, mappings, sometimes scripts |
| Success metric | Production adoption, workflow impact, often **renewal / billable delivery** (Databricks: FDEs are billable) | Reliability, product metrics | Pipeline / win rate | Design sign-off | Consumption / adoption of the vendor platform | SOW completion |
| Travel | Palantir ~25%; OpenAI up to 50%; Anthropic ~25%; Cohere 20–40%; Databricks ~20%; MongoDB ~30% | Low | High (pre-sales) | Medium | Medium | High on SI projects |
| GenAI stack | Common in 2026 lab/startup JDs; **not** required on classic Palantir FDSE | Team-dependent | Demo-oriented | Reference architectures | Vertex/OpenAI/Azure how-to | Copilot/RAG build-outs in Indian SI JDs |
| Closest India confusing alias | “AI Deployment Engineer,” “Customer AI Engineer,” “Applied AI Engineer,” Cognizant “AI Customer Engineer” | Backend/SWE | Presales FDE (Prodapt explicitly requires 1 year **AI presales**; delivery-only does not qualify) | Cloud SA | Google Customer Engineer / Microsoft CE | Infosys/TCS/Accenture “FDE” pods |

**FDE vs SWE:** both write production code. FDE scope is customer outcome and integration with messy systems; SWE scope is a long-lived shared codebase. OpenAI’s JD still requires full-stack production code, not slideware.

**FDE vs SE:** SE is pre-sales; FDE is post-sales (or full-cycle at startups). Cohere/Mistral blur this by putting FDEs on pre-sales calls.

**FDE vs SA:** SA owns the blueprint; FDE owns the working system. Databricks splits Architect / Engagement Manager / FDE on the same careers page.

**FDE vs CE:** cloud CE is closer to “help them use our platform correctly.” Google’s (unverified Naukri) “Forward Deployed Engineer, Cloud Applied AI” is the company trying to pull CE toward FDE (agents + custom tooling + product feedback loop).

**FDE vs implementation consultant:** consultants leave after the SOW. Branded FDEs are measured on production and feed the product roadmap (every lab JD in this sample says so). Indian SI “FDE” postings often **are** implementation consultants with an AI toolchain — especially when Python is only “good to have.”

---

## 7. Demand-side claims that are **not** job-posting facts

Reported for context; **not verified as headcounts** in this brief:

- TCS plans to convert 1–1.5% of global workforce into FDEs (~5,900–8,900): *India Today* (17 Jul 2026) and *Moneycontrol* citing Reuters.
- Coforge 20 → 100 FDEs; EPAM India 50 → 100: *Business Standard* (2 Jun 2026), named CEO/VP quotes.
- FDE postings +729% YoY (643 in Apr 2025 → 5,330 in Apr 2026): *Hindustan Times* (15 Sep 2026).
- Indeed: +1,807% FDE postings in India Jun 2025–Jun 2026: *India Today* (15 Sep 2026).
- TeamLease: ~250–270 India openings at a point in time (mid-2026 press): *Business Standard* / OwnYourCareer secondary.
- OpenAI Deployment Company ~150 FDEs via Tomoro acquisition: *Hindustan Times* (15 Sep 2026).
- Wonderful (startup) plans to hire up to 1,000 FDEs in India: same HT piece — **aspiration, not current openings**.

None of these numbers appear in the Plank census or in the 36 JDs.

---

## 8. What this brief could **not** verify

- Salesforce FDE JD body (JS-only careers page).
- Live Google Careers FDE posting (US URLs 404; Bengaluru Naukri listing unconfirmed).
- AWS / amazon.jobs FDE JD body.
- Any Palantir, OpenAI, Anthropic, Cohere, or Mistral **India** FDE posting.
- Naukri HTML pages (HTTP 403/Akamai); Cutshort inventory.
- FDE Academy study microdata behind the Mint table (sample size, employer list, cash vs CTC vs equity).
- A typical India FDE salary. Secondary sources disagree by 2× at entry level. Only one official India ATS range (Cartesia ₹70–90L) was captured.
- Whether census `salary` units are always annual USD (Latin America `[5000, 6500]` suggests no).
- Unique-req vs multi-location duplicates (Databricks 121 rows are heavily multi-city / vertical slices of similar Sr FDE reqs).
- Kochi / Coimbatore FDE demand (no posting found).
- Whether Cognizant job 00067697573 is still an FDE role (career URL slug says FDE; on-page title on 2026-09-15 was **AI Customer Engineer**).

---

## 9. Practical takeaways for an India-based candidate

1. **The branded FDE market is still mostly not India.** In a 1,333-row global title census, 29 rows were India-tagged. Labs that defined the role are hiring FDE in NYC/SF/Seattle/London/Singapore/Tokyo, not Bengaluru — with Microsoft Bangalore as a documented exception.
2. **The India market that *does* exist is real but heterogeneous.** Databricks Remote-India / Bengaluru, MongoDB Gurugram, DevRev Chennai/Bangalore, Cartesia Bangalore (₹70–90L posted), Scale AI India, plus a large SI/Naukri layer using the same title.
3. **Do not optimize only for RAG keywords.** Palantir’s still-live FDSE JD does not mention RAG. It requires being a strong generalist coder who will sit with the customer. Lab JDs (OpenAI, Anthropic, Cohere, Mistral, Databricks AI-FDE) add LLMs, evals, and often agents.
4. **Python + customer proof + production systems** is the intersection of almost every JD that was actually read. Kubernetes is optional; security/compliance shows up whenever the customer is an enterprise.
5. **₹1.55 crore is a 15-year study median, not an offer letter.** Treat Mint as a ceiling anecdote until an employer posts it.
6. **Title arbitrage is aggressive in Indian IT services.** Read the JD: if Python is “good to have” and the must-have is “Generative AI,” it is closer to implementation consulting than Palantir Delta.

---

## Sources

Census  
- Plank FDE job-market census, observed 2026-09-12, N=1,333, license CC BY 4.0.

Official / ATS JDs (accessed 2026-09-15 unless dated in-text)  
- Palantir, Forward Deployed Software Engineer, New York, https://jobs.lever.co/palantir/dab396d4-2f14-4796-aac0-0d82883dccf0  
- Palantir, Forward Deployed Software Engineer - US Government, Washington DC, https://jobs.lever.co/palantir/289ad049-7b4e-41e3-8a39-146fbeb6fb64  
- Palantir, “Dev versus Delta: Demystifying engineering roles at Palantir,” Palantir Blog, 8 Apr 2019, https://blog.palantir.com/dev-versus-delta-demystifying-engineering-roles-at-palantir-ad44c2a6e87  
- Databricks, Forward Deployed Engineer, Remote - India, https://www.databricks.com/company/careers/open-positions/job?gh_jid=8432827002  
- Databricks, AI Engineer - FDE, Remote - India, https://www.databricks.com/company/careers/open-positions/job?gh_jid=8099751002  
- Databricks, Senior Forward Deployed Engineer, Bengaluru, https://www.databricks.com/company/careers/open-positions/job?gh_jid=8629999002  
- Databricks open-positions index (India FDE family listed), https://www.databricks.com/company/careers/open-positions  
- OpenAI, Forward Deployed Engineer (FDE) - NYC, https://jobs.ashbyhq.com/openai/9471b38b-f65c-4a01-9626-bd33fca90f1d (text via Ashby posting-api)  
- Anthropic, Forward Deployed Engineer, https://job-boards.greenhouse.io/anthropic/jobs/5302966008  
- Scale AI, Forward Deployed Engineer, Gen AI, India, https://job-boards.greenhouse.io/scaleai/jobs/4549048005  
- Cohere, Forward Deployed Engineer, Agentic Platform, https://jobs.ashbyhq.com/cohere/b0bcef37-1d20-414f-aade-c54942d63df9  
- Mistral AI, Applied AI, Forward Deployed Machine Learning Engineer, Palo Alto, https://jobs.ashbyhq.com/mistral.ai/2ec2dacd-1117-479b-a4c1-efa9df530798  
- Microsoft FDE (US, closed), job 1876152, via https://jobs.anitab.org/companies/microsoft/jobs/59269026-forward-deployed-engineer-fde  
- Microsoft FDE, Bangalore, job 200029969, https://apply.careers.microsoft.com/careers/job/1970393556823788  
- Cartesia, DevRev, MongoDB, HackerRank, Emergent, Nanonets, Handshake, LiveKit, Blitzy, Kognitos, Reltio, Arcesium, Redwood — URLs in §2 tables  
- Cognizant, https://careers.cognizant.com/us-en/jobs/00067697573/ai-engineer-forward-deployed-engineer/

Press / secondary (pay and demand; not used as skill frequencies)  
- Arshdeep Kaur, *Mint*, 15 Sep 2026, https://www.livemint.com/ai/artificial-intelligence/plenty-of-coders-few-deployers-india-s-ai-skill-gap-sparks-rs-1-55-crore-salary-boom-11789442981155.html  
- *India Today*, 17 Jul 2026, https://www.indiatoday.in/technology/features/story/forward-deployed-engineers-are-in-demand-but-what-is-fde-and-how-you-become-one-2949961-2026-07-17  
- *India Today* jobs, 15 Sep 2026, https://www.indiatoday.in/jobs/story/fde-jobs-in-india-forward-deployed-engineers-ai-jobs-with-business-coding-skills-educ-2994960-2026-09-15  
- *Business Standard*, 2 Jun 2026, https://www.business-standard.com/technology/tech-news/demand-for-forward-deployed-engineers-surges-as-companies-adopt-ai-126060201183_1.html  
- *The Hindu*, 15 Jul 2026, https://www.thehindu.com/education/forward-deployed-engineering-next-wave-of-ai-career-opportunity/article71216987.ece  
- *Moneycontrol*, 21 Jul 2026, https://www.moneycontrol.com/artificial-intelligence/entry-level-fdes-earn-up-to-7-times-more-than-software-developers-starting-at-rs-18-lakh-article-13979349.html  
- *Hindustan Times*, 15 Sep 2026, https://www.hindustantimes.com/ht-insight/future-tech/forward-deployed-engineer-is-ais-newest-job-title-101789465861875.html  

India boards  
- Naukri `fde-jobs` index snippet (HTML blocked), 2026-09-15  
- Instahyre Boomerang Pune, https://www.instahyre.com/job-411617-forward-deployed-engineer-at-boomerang-pune/  
- LinkedIn Databricks India FDE / Sr FDE applicant counts, pages dated 2026-08-28 and 2026-09-03
