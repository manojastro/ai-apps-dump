# A3 — Live JD Corpus — August 2026

**Corpus owner:** Research Agent A3 (live job-description corpus).  
**Access date (this harvest):** 2026-08-23.  
**Target persona:** ~8.5 years of experience (prefer 6–12 YOE postings); India locations Bengaluru, Hyderabad, Chennai, Pune, NCR, Coimbatore, Remote/Hybrid India; **Python / GenAI / agents / RAG / LLMOps / AIOps / automation first**. User refuses Java/SQL-first positioning — Java/SQL are still **counted** so the filter cost is known.  
**Rule:** Zero fabrication. Every requirement labelled **VERIFIED FACT** is quoted or tightly extracted from a captured JD. If a listing 404s, expires, or is login-walled, that is stated. Partial cards are labelled **PARTIAL**. Salary figures that are Glassdoor estimates (not employer-disclosed) are labelled **ESTIMATE, NOT EMPLOYER-DISCLOSED**.

---

## Method

### Boards and career sites searched (23 Aug 2026)

| Source | Query / surface | Result |
|---|---|---|
| Naukri | `generative-ai-engineer-jobs`, `genai-engineer-jobs`, `gen-ai-jobs`, `llmops-jobs`, `aiops-jobs`, `mlops-jobs`, plus individual `job-listings-*` URLs | Volume pages returned (11,132 “Generative Ai Engineer” vacancies; 7,709 “Genai Engineer”; 28,853 “Gen Ai”; 772–877 “Llmops”; 558 “Aiops”). **Individual listing URLs frequently 302 to search, render “Job you are looking for is expired”, or return an empty image.** Google-indexed snippets of those same URLs often still contain the JD body. |
| LinkedIn (public guest pages) | Individual `/jobs/view/{id}` URLs | **Best full-text source.** Many India GenAI/agentic/LLMOps JDs still public. Some IDs 302 to “expired_jd_redirect”. |
| Company careers | Deloitte USI, Cognizant, Ecolab, PwC Acceleration Centres, ServiceNow, Freshworks | Deloitte USI JD **live**. Cognizant `00068075121` **404**. Ecolab `R00295717` **“no longer available”**. PwC `724190WD` **filled**. Freshworks careers is marketing, not a GenAI IC JD. |
| Instahyre | `/job-437639-…`, `/job-432570-…`, `/job-421869-…`, `/job-385376-…` | JS shell only (“Loading…”). **No JD body.** Titles/snippets from Google index used only as existence evidence, not as full extracts. |
| Foundit | IRIS MLOps/AIOps GCP Lead | Listing indexed; direct fetch failed. Snippet used as **PARTIAL**. |
| Glassdoor | TCS / Infosys GEN AI Engineer | JD body in search snippets. Salary bands are **Glassdoor estimates**. |
| TAL / Grapevine | Allianz Technology AI Operations (Pune) | Full structured extract; page tagged **Expired**. |
| Cutshort | — | **No usable live JD body captured in this harvest.** Treat as evidence gap. |

### Recency tags used in this file

| Tag | Meaning |
|---|---|
| **LIVE** | Public JD body retrieved 23 Aug 2026 (or employer careers page still serving the JD). |
| **INDEXED-LIVE** | Naukri/Google still showing the listing as posted in the last ~14 days, but the listing URL itself 302/expired when opened. Body taken from the search-index snippet. |
| **RECENT-CLOSED** | Posted within ~4 weeks; “no longer accepting” / filled / 404. Body captured from cache or LinkedIn “Show more” residual. |
| **OLDER** | Posted ~1–4 months ago; still readable but not a current-week posting. |
| **EXPIRED** | Explicitly expired / walk-in date in the past / careers 404. Body only if independently cached. |

### Inclusion / exclusion

- **In:** Generative AI Engineer, GenAI / Agentic AI, LLM Engineer, LLMOps, MLOps with LLM, AIOps, AI Automation, RAG / Applied AI, AI Platform, Copilot / workflow+LLM, Support-copilot / ITSM+agentic.  
- **Out of full extract:** Pure Java/Spring backend with a “plus: ChatGPT” line and no GenAI delivery language; unpaid internships aimed at students (noted only in red-flag section if they target experienced people).  
- **Experience:** Prefer 6–12 YOE. Some 3–8 / 5–10 / 8–12 postings are included because they are the live market around 8.5 YOE. Junior 1–3 YOE roles are included **only** when they disclose salary or show the “kitchen-sink vs LPA” pattern.

### What this harvest could **not** do

- Naukri anti-bot blocked `web_fetch` (`Access Denied`, Akamai). Individual `job-listings` URLs often expire within days.  
- Instahyre and some Foundit pages are client-rendered.  
- LinkedIn seniority labels are frequently wrong (Infosys “Entry level” on a 6–11 YOE twin listing). Use the **JD text / Naukri twin**, not LinkedIn’s seniority chip.  
- **Microsoft / Amazon / ServiceNow / Zoho / Adobe / Salesforce / Oracle / Thoughtworks / Fractal / Tiger Analytics / Freshworks** product-engineering GenAI IC JDs with full public bodies were **not captured** in this pass (see Evidence gaps). Google Cloud FDE **was** captured.

---

## JD inventory table (all JDs, one row each)

| ID | Company | Title | Location | Exp (as posted) | Posted / recency | Source | Status 23 Aug 2026 | Java? | SQL? | Adjacent vs core | Segment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| JD01 | Infosys | GenAI / Agentic AI Engineer | Bengaluru East | Naukri twin 6–11 Yrs; LinkedIn chip “Entry level” (unreliable) | 1 week ago; Naukri twin also 4–9 Yrs (06 Aug) | LinkedIn + Naukri | **LIVE** | No | No | Adjacent (app/RAG/agents) | Services |
| JD02 | Infosys | Agentic AI Engineer | Bengaluru East | Mid-Senior (LinkedIn); related Naukri 3–5 Hybrid BLR/Hyd/Chennai | 2 weeks ago | LinkedIn | **LIVE** | No | No | Adjacent→core (LoRA listed) | Services |
| JD03 | Infosys | GEN AI Engineer | Bengaluru | 3–5 AI/ML with GenAI exposure | Glassdoor ~16 Aug 2026 | Glassdoor | **INDEXED-LIVE** | No | No | Adjacent | Services |
| JD04 | Infosys | Gen AI LLMOps Engineer | Bengaluru | 2–3 Yrs (title); DAU | ~1 day on Naukri (04 Aug listing id) | Naukri | **INDEXED-LIVE** | No | No | Adjacent (LLMOps, not research) | Services |
| JD05 | TCS | GEN AI Engineer | Bengaluru | Developer; Job Id 385214 | Glassdoor ~16 Aug 2026 | Glassdoor | **INDEXED-LIVE** | No | No | Adjacent (junior/agentic interest) | Services |
| JD06 | TCS | Agentic AI Engineer (text = Architect) | Hyderabad, Chennai, Bengaluru | 8–12 Yrs | ~1 week (listing `130826027970`) | Naukri | **INDEXED-LIVE** | No | No | Adjacent (architecture, not training) | Services |
| JD07 | Accenture in India | LLM Operations Engineer | Pune (PDC3C-SEZ) | Min 3 Yrs in LLMs; “15 years full time education” | 3 days ago | LinkedIn | **LIVE** | No | No | Adjacent (ops) | Services |
| JD08 | Capgemini | Agentic with Azure AIFoundry | Bengaluru | 5+ overall, ≥1 yr similar AI | ~1 month; 116 applicants | LinkedIn | **LIVE** | **Yes (or .NET/Python)** | No | Adjacent | Services |
| JD09 | Deloitte USI | GEN AI Engineer – Specialist Assistant Manager, AI and Data Science | Hyderabad / Bengaluru | Not numbered; SAM / L40 | Requisition 353050; page live | Deloitte USI careers | **LIVE** | No | No | Adjacent (LangChain/LlamaIndex/eval) | Services |
| JD10 | EY | AI Engineer-Agentic AI-Orchestration And Azure AI Foundry-Full-Stack-Azure-Native | Bengaluru | **10+ years Global IT**; 3+ global ops | 4 days ago | LinkedIn | **LIVE** | No (Python/C#/TS) | Implied data stores | Adjacent (ops+agents) | Services |
| JD11 | Persistent | Agentic AI Engineer | Hyderabad, Bengaluru (all Persistent) | 5+ / 5–10 Yrs | Walk-in 9 May 2026 (past) | Naukri | **EXPIRED walk-in; JD body indexed** | No | No | Adjacent | Services |
| JD12 | Persistent | Senior AI OPS Engineer | Pune (all Persistent loc) | **7 to 10 Years** (header); 5–7 relevant in body | 2 days ago | LinkedIn | **LIVE** | No | No | Adjacent (AI Ops + GCP agents) | Services |
| JD13 | HPE | DevOps, MLOps & GenAI Platform Owner (IC) | Bengaluru Hybrid (2 days/week office) | TCP_04 / IC+ | 2 weeks ago | LinkedIn | **LIVE** | **Yes (Python, Java, Selenium)** | No | **Adjacent (ITIL/SNOW/RPA+RAG)** | Product/GCC-ish ops |
| JD14 | NXP Semiconductors | Software DevOps Engineer - for Gen AI | Bengaluru | 5+ SWE; 1+ LLM prod | 2 weeks ago; 200+ applicants | LinkedIn | **LIVE** | **Yes (Python, Java, Node)** | **Yes (2+ yrs DBMS)** | Adjacent (SWE+LLM) | Product/GCC |
| JD15 | Qualys | Machine Learning Operations Engineer | Pune | **2–3 years** ML products | 4 days ago; 200+ applicants | LinkedIn | **LIVE** | No | No | **Core-ML** (train/CUDA/K8s) | Product |
| JD16 | Hitachi Energy | AI Automation Engineer | Bengaluru | **5–10 years** SWE/AI | Publication date **2026-08-18** | LinkedIn | **LIVE** | Advantage (Java/C#) | **Required** | Adjacent (CSS/SNOW/SAP+agents) | Product/GCC |
| JD17 | Smart Working (client) | LLM Systems / AI Agent Engineer (Remote, FT) [AS311] | Hyderabad / India remote | 5+ backend; 2+ prod agents | 4 days ago | LinkedIn | **LIVE** | No | **Postgres** | Adjacent (agent systems, not training) | Product (remote) |
| JD18 | MyAdvice | AI Engineer I (Generative AI) | Bengaluru / remote-first (may recall to BLR) | **1–3 years** | LinkedIn shows 2 months; salary disclosed | LinkedIn | **LIVE** (older posting) | No | No | Mixed (fine-tune + RAG) | Product |
| JD19 | StackNexus | GEN AI ENGINEER | Remote India, **US hours**, contract | **+5 Years** | 4 months ago | LinkedIn | **OLDER** | No | No | Adjacent | Product/contract |
| JD20 | Hired (client) | AI Engineer - Generative AI (Remote) | Remote India | Senior LLM (unspecified YOE) | 3 weeks; **No longer accepting** | LinkedIn | **RECENT-CLOSED** | No | **Yes (Python and SQL)** | Adjacent | Unknown client |
| JD21 | Ascendion | Lead Generative AI Engineer (5–12 Years) | Bengaluru (Bellandur walk-in 11 Jul 2026) | **5–12 years overall SWE** | Drive date past; LinkedIn ID expired | LinkedIn search cache | **EXPIRED drive** | No | No | Adjacent (prod GenAI) | Services |
| JD22 | Cirrus Labs | AI Engineer (agentic workflows LangGraph/LangChain, RAG) | Hybrid Hyderabad / Bengaluru | 3–8 years | 1 day on Naukri | Naukri | **INDEXED-LIVE; listing URL expired** | No | **SQL tools** | Adjacent | Services/startup |
| JD23 | 360DigiTMG (client: payments firm) | GenAI Engineer Agentic AI & RAG | Bengaluru | 4–8 overall; 1–2+ GenAI | 1 week | Naukri | **INDEXED-LIVE; listing URL expired** | No | No | Adjacent | Product client via staffer |
| JD24 | Infinity / Stamford Technology | GenAI / Agentic AI Engineer | Hybrid Hyd, Chennai, Bengaluru | **10–18 years** | 2 weeks | Naukri | **INDEXED-LIVE** | No | DBs mentioned | Adjacent | Services |
| JD25 | Cognizant | AI OPS: Integration/API Engineer with MLOps, AI-ML developer | Bangalore Hybrid | **7 to 13 years**; NP immediate–90 days | Date published **18 May 2026** | Cognizant careers | **EXPIRED (404)** | No | No | Adjacent (MLOps pipelines) | Services |
| JD26 | Allianz Technology | AI Operations / AI Automation Operations Engineer | Pune Onsite | 2–6 years | Posted 2 Jun 2026 | TAL/Grapevine | **EXPIRED** | No | **SQL/NoSQL** | **Adjacent (SNOW/ITSM/SRE)** | GCC |
| JD27 | IRIS Software | MLOps AIOps GCP - Lead | Noida Hybrid | **8–10 / 8–9 years** | ~3 days on Foundit | Foundit | **INDEXED-LIVE; page fetch failed** | No | Unknown | Adjacent (platform+agentic) | Product/IT |
| JD28 | Zealant Consulting (client CLM) | AI Engineer (Agentic AI Development) | Bengaluru | 3+ SWE, 1+ LLM prod | 1 month; 94 applicants | LinkedIn | **LIVE** | No | No | Adjacent (multi-agent prod) | Staffing→product |
| JD29 | ApTask | Agentic AI Engineer – Azure \| LLM \| RAG \| LangGraph | Pune / Bengaluru / Bhopal FTE | **6+ years** SWE/AI | 5 days ago; 200+ applicants | LinkedIn | **LIVE** | No | **SQL/NoSQL** | Mixed (LoRA + RAG + MLOps) | Staffing |
| JD30 | BNP Paribas | Agentic AI & DevOps | Bengaluru / Mumbai | **7–9+ years**; 5+ DevOps/AI, 2+ LLM agents | 2 weeks ago | LinkedIn | **LIVE** | No | No | **Adjacent (IT ops assistants)** | GCC/Bank |
| JD31 | UST | AI Engineer | Bengaluru | **3–5 years** ML/AI; ≥1 yr custom agents | 1 week ago; 200+ applicants | LinkedIn | **LIVE** | No | “Data layer” | Adjacent | Services |
| JD32 | Tech Mahindra | Agentic AI Engineer | Pune, Bengaluru | 5–10 Yrs | 3 days (listing `190826025169`) | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent | Services |
| JD33 | HCLTech | Agentic AI Engineer | Noida, Hyderabad, Bengaluru | 4–9 Yrs | 5 days | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Mixed (PyTorch/TF listed) | Services |
| JD34 | Altimetrik | Gen AI Engineer | Hybrid Hyd, Chennai, Bengaluru | 5–10 Yrs | 2 days | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Mixed (TF/PyTorch + RAG) | Services |
| JD35 | HP | AI and Automation Developer | Bengaluru | Typically **5–7 years** | 2 weeks ago; 200+ applicants | LinkedIn | **LIVE** | On knowledge list | No | **Adjacent (JIRA/SNOW/RPA)** | Product |
| JD36 | Convera | Agentic AI Engineer (ITSM & Enterprise Automation) | Pune | **3+ years** AI Ops / AI engineer | 4 days ago | LinkedIn | **LIVE** | **JavaScript required**; Python/PS plus | No | **Adjacent (ITSM/SNOW) — best first-screen fit** | Product |
| JD37 | Google Cloud | Generative AI Forward Deployed Engineer | Mumbai / Pune / Bengaluru | **8 years** cloud or technical customer-facing | 1 week ago; 200+ applicants | LinkedIn | **LIVE** | No | No | Mixed (prod agents + customer embed) | Product/GCC |
| JD38 | PwC | Agentic AI Engineer | Hybrid Hyd, Bengaluru | 6–9 Yrs | 2 days | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent (ITIL tagged) | Services |
| JD39 | PwC | AI Engineer | Hybrid Hyd, Bengaluru | 5–9 Yrs; ≥4 yrs | 4 days | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Unknown (Node/React/Python/GenAI) | Services |
| JD40 | PwC Acceleration Centres | Gen AI Engineer – Senior Associate | Bangalore | — | Careers `724190WD` | PwC TA | **RECENT-CLOSED (filled)** | — | — | — | Services |
| JD41 | ADP | Walk-in \|\| Gen AI Engineer | Hybrid Hyderabad | 3–8 Yrs | Walk-in **25 Aug 2026** | Naukri | **LIVE walk-in (PARTIAL)** | Unknown | Unknown | Adjacent (Agentic workflows quoted) | Product/GCC |
| JD42 | Blackstraw.ai | Walk-in \|\| Generative AI Engineer | Chennai WFO | 2–6 Yrs | Walk-in **24 Aug 2026** | Naukri | **LIVE walk-in (PARTIAL)** | Company also posting Java FS same week | Unknown | Mixed (CV + RAG + Agentic) | Product |
| JD43 | DXC Technology | AI Engineer (Generative AI) | Hyd / BLR / Chennai / Kolkata / Noida | 5–10 Yrs | 1 day | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent (Azure ML, FAISS) | Services |
| JD44 | Cognizant | AI Engineer | Hybrid BLR, Pune, Chennai | 6–11 Yrs | 4 days | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Unknown | Services |
| JD45 | Wissen Technology | SRE AI Engineer | Hybrid BLR, Pune, Mumbai | 5–9 Yrs | 1 day | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent (SRE+AI) | Services |
| JD46 | Advance Career Solutions (client) | Agentic AI Engineer | Hybrid BLR, Hyd, Pune | 8–13 Yrs | 1 day | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent | Staffing |
| JD47 | Qentelli | AI Engineer (LLM / Chatbot / RAG) | Hyderabad | 6–11 Yrs | 1 day | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent (LangChain/LangGraph/LLMOps) | Services |
| JD48 | Tekskills (leading client) | Gen AI Engineer / Generative AI Engineer | Bengaluru / Hyderabad / Pune | 4–8 / 6–11 | 1 day | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Mixed (MLOps + GenAI) | Staffing |
| JD49 | Ecolab | Lead AI Engineer | Bengaluru | Naukri shows 8–10 **and** 2–6 (two reqs) | Naukri 3–5 days; careers R00295717 gone | Ecolab careers + Naukri | **CAREERS EXPIRED; Naukri still listing** | Unknown | Unknown | Adjacent (legal GenAI/agents; ServiceNow on one card) | Product/GCC |
| JD50 | Infosys | Agentic AI Engineer (Pan-India) | Hybrid Hyd, Chennai, BLR / also NCR, Mumbai, Pune, Ahmedabad variants | 3–5 Yrs | 5 days / 11 Aug | Naukri | **INDEXED-LIVE (PARTIAL)** | Unknown | Unknown | Adjacent | Services |

**Inventory count:** 50 rows. **Full-body extracts below:** 37 JDs (JD01–JD31, JD35–JD37, plus JD04/JD05/JD06/JD11/JD21–JD27 where the indexed body is long enough). **PARTIAL-only:** JD32–JD34, JD38–JD50 except where noted. **Quality > invented volume:** partial rows stay partial.

Naukri **market-volume (not a JD):** as of this harvest, Bengaluru 3,139 GenAI engineer jobs, Hyderabad 1,707, Pune 1,262, Delhi/NCR 993. Salary-band job counts on the GenAI engineer SERP: 0–3 LPA 291; 3–6 LPA 1,863; 6–10 LPA 3,433; 10–15 LPA 2,835.

---

## Full extracts (company, quotes, URL)

Each extract: **VERIFIED FACT** quotes are verbatim from the captured page/snippet. Commentary is labelled as analysis, not JD text.

---

### JD01 — Infosys — GenAI / Agentic AI Engineer — **LIVE**

- **Company / title:** Infosys — GenAI / Agentic AI Engineer  
- **Location:** Bengaluru East, Karnataka, India  
- **Exp range:** LinkedIn seniority chip says “Entry level” (**do not trust**). Naukri twin `job-listings-genai-agentic-ai-engineer-infosys-limited-bengaluru-6-to-11-years-100726919193` = **6–11 Yrs**. Another twin `…-4-to-9-years-060826931040` = **4–9 Yrs**. Same must-have block.  
- **Posted:** “1 week ago”; 200+ applicants.  
- **URL:** https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669  
- **Naukri twin:** https://www.naukri.com/job-listings-genai-agentic-ai-engineer-infosys-limited-bengaluru-6-to-11-years-100726919193  
- **Source:** LinkedIn (primary), Naukri (exp band).  
- **Access:** 2026-08-23. Recency: **LIVE**.  
- **Salary:** Not disclosed.  
- **Degree / NP / mode:** Not on LinkedIn body. Full-time.  
- **Wording:** **IT + AI skills**, not “8+ years of AI research”. Must-haves are Python + Bedrock + prompting/RAG/LangGraph + DevOps basics.

**VERIFIED FACT — Must Have Skills (verbatim):**  
> “Must Have Skills Python - Core concepts: OOP, typing, modules, pytest/unittest, fixtures, basic async AWS Bedrock - Model invocation (Claude/Titan, etc.), Knowledge bases or retrieval integration, basic understanding of guardrails & access controls Generative AI - Prompting (system, few-shot), RAG types and approaches, Basic evaluation awareness, LangChain / LangGraph , Simple agent flows and routing DevOps Basics - Git, PRs, CI pipelines, Docker basics, artifacts”

**VERIFIED FACT — Responsibilities (verbatim bullets):**  
> “Develop GenAI features and workflows using Python and AWS Bedrock”  
> “Implement RAG pipelines (chunking, embeddings, retrieval, grounding)”  
> “Build single/multi-step agent workflows using LangChain / LangGraph”  
> “Integrate LLMs with APIs, tools, and enterprise applications”  
> “Write tested, maintainable Python code with CI/CD pipelines”  
> “Monitor basic latency, token usage, and cost metrics”

**Skill flags:** Python Y; LangChain Y; LangGraph Y; OpenAI N (Bedrock/Claude/Titan); Azure OpenAI N; Bedrock Y; Vertex N; HF N; RAG Y; vector DB implied (knowledge bases); agents Y; MCP N; eval “basic awareness”; guardrails Y; MLOps N (DevOps basics); K8s N; CI-CD Y; ITSM N. **Java N. SQL N.**

**First-screen plausibility for Service Desk Lead + GenAI portfolio:** **HIGH among services firms**, if the resume shows Python tests, one RAG pipeline, LangGraph agent, Bedrock or equivalent, Docker/CI. This JD does **not** demand years of model training.

---

### JD02 — Infosys — Agentic AI Engineer — **LIVE**

- **Company / title:** Infosys — Agentic AI Engineer  
- **Location:** Bengaluru East  
- **Exp:** LinkedIn Mid-Senior. Related Naukri “Agentic AI Developer (3-5 Years Experience) Location: Infosys, India” Hybrid BLR/Hyd/Chennai.  
- **Posted:** 2 weeks ago; 200+ applicants.  
- **URL:** https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-infosys-4441390349  
- **Access:** 2026-08-23. Recency: **LIVE**.  
- **Salary / degree / NP:** Not disclosed.

**VERIFIED FACT — requirements (verbatim):**  
> “Strong Python programming with hands-on AI/ML framework experience.”  
> “Working knowledge of LLMs, prompt engineering, and basic fine-tuning (LoRA/QLoRA).”  
> “Practical experience with agentic frameworks such as LangChain, AutoGen, or CrewAI.”  
> “Experience with API integration and tool-augmented agent development.”  
> “Understanding of responsible AI, safety guardrails, and LLM evaluation strategies.”  
> “Familiarity with vector stores, retrieval systems, and RAG architectures”

**VERIFIED FACT — responsibilities (verbatim):**  
> “Design and implement production-grade agentic architectures leveraging LLMs and reasoning engines.”  
> “Build and optimise multi-agent systems for complex task orchestration and collaboration.”  
> “Integrate external tools, APIs, and knowledge bases for robust agent augmentation.”  
> “Prototype advanced capabilities: persistent memory, goal planning, and self-correction loops.”

**VERIFIED FACT — Good to Have:**  
> “Exposure to MLOps practices — experiment tracking, model versioning (MLflow, DVC).”  
> “Experience with cloud AI services on Azure, AWS, or GCP.”

**Java N. SQL N.** Fine-tuning is **“basic” LoRA/QLoRA**, not a research scientist bar. Still more “core-AI-lite” than JD01.

---

### JD03 — Infosys — GEN AI Engineer (Controls Technology) — **INDEXED-LIVE**

- **Location:** Bengaluru. Glassdoor est. ₹5L–₹10L (**ESTIMATE, NOT EMPLOYER-DISCLOSED**).  
- **URL:** https://www.glassdoor.co.in/job-listing/gen-ai-engineer-infosys-JV_IC2940587_KO0,15_KE16,23.htm?jl=1010089163801  
- **Published:** 2026-08-16. Access 2026-08-23.

**VERIFIED FACT:**  
> “We are looking for a skilled Generative AI Developer to join our Controls Technology team”  
> “Hands on experience with at least one major machine learning framework PyTorch TensorFlow Keras”  
> “Familiarity with LLMs prompt engineering and fine tuning e.g. LoRA QLoRA”  
> “Exposure to RAG systems and basic knowledge of hybrid search techniques”  
> “Understanding of model deployment and containerization Docker”  
> “Proficiency in Python for AI development data preprocessing and scripting”  
> “3 5 years of professional experience in AI ML development with exposure to Generative AI”  
> “Exposure to cloud based AI ML environments AWS GCP or Azure is a plus”

**Java N. SQL N.** YOE is **3–5 in AI/ML**, not 8.5 IT. Filter cost: this is a **YOE-in-AI** wording, harder for an IT-ops switcher than JD01.

---

### JD04 — Infosys — Gen AI LLMOps Engineer — **INDEXED-LIVE**

- **Location:** Bengaluru. **Exp posted: 2–3 years.** Service Line: Data Analytics Unit.  
- **URL:** https://www.naukri.com/job-listings-gen-ai-llmops-engineer-infosys-limited-bengaluru-2-to-3-years-040826909325  
- **Access:** 2026-08-23. Direct listing fetch returned an empty image; body from Google/Naukri snippet.

**VERIFIED FACT — responsibilities:**  
> “LLM Deployment Productionization: Deploy and manage LLMs (OpenAI, Llama, Mistral, etc.) in production environments”  
> “Build scalable inference pipelines (real-time batch)”  
> “Integrate LLMs into applications via APIs and microservices”  
> “Design and implement end-to-end LLM pipelines: Prompt engineering”  
> “Retrieval-Augmented Generation (RAG)”  
> “Fine-tuning / embeddings”  
> “Work with frameworks like LangChain”

**VERIFIED FACT — What This Role Is NOT:**  
> “Not pure: Data Scientist (model building only)”  
> “Platform Engineer (infra-heavy role)”  
> “Traditional MLOps without LLM exposure”  
> “This role focuses on: LLM deployment + RAG + GenAI pipelines”  
> “Operationalizing GenAI applications”

**VERIFIED FACT — technical requirements:**  
> “Strong Python programming”  
> “Hands-on experience with LLMs / Generative AI”  
> “Experience with LangChain / LangGraph / LlamaIndex”  
> “Solid understanding of: RAG architecture, Prompt engineering, Embeddings vector search”

**Education:** “Bachelor of Engineering,BTech,BCA,BSc,MCA,MTech,MSc”. **Java N. SQL N.**

**Analysis:** Posted band is **2–3 YOE** while the skill list matches mid-level LLMOps. Classic services-firm band compression. An 8.5 YOE IT-ops candidate would be **over-index on YOE** and still need the Python/RAG artefacts.

---

### JD05 — Tata Consultancy Services — GEN AI Engineer — **INDEXED-LIVE**

- **Location:** Bengaluru. Role: Developer. Job Id **385214**.  
- **Glassdoor est.:** ₹5L–₹8L (**ESTIMATE, NOT EMPLOYER-DISCLOSED**).  
- **URL:** https://www.glassdoor.co.in/job-listing/gen-ai-engineer-tata-consultancy-services-JV_IC2940587_KO0,15_KE16,41.htm?jl=1009966161130  
- **Published:** 2026-08-16.

**VERIFIED FACT — required:**  
> “Good knowledge in Python, Generative AI models (LLMs, Image Generators, etc.), and Agentic AI concepts.”  
> “Agentic AI principles to build AI agents capable of autonomous decision-making.”  
> “Good understanding of Python programming fundamentals (functions, OOPs, basic libraries like pandas, numpy).”  
> “Basic knowledge or keen interest in AI/ML concepts.”  
> “Familiarity with ChatGPT, Generative AI tools, or understanding of LLMs is a plus.”  
> “Eagerness to learn about Agentic AI and AI agent design.”

**VERIFIED FACT — Preferred (Good to Have):**  
> “Basic understanding of Generative AI frameworks like OpenAI API, HuggingFace, LangChain,Langgraph etc.”  
> “Understanding of REST APIs and basic software development lifecycle.”  
> “Interest in building autonomous AI systems (multi-agent systems, AI orchestration).”

**Java N. SQL N.** Degree not in snippet.  

**Red-flag overlay:** Agentic/multi-agent language paired with **junior Python fundamentals** and a **₹5–8L estimate**. Kitchen-sink title, fresher/early bar. Not a realistic 8.5 YOE target (comp too low) unless TCS bands the same title across grades.

---

### JD06 — TCS — Agentic AI Engineer (JD text = Architect) — **INDEXED-LIVE**

- **Location:** Hyderabad, Chennai, Bengaluru. **8–12 Yrs.**  
- **URL:** https://www.naukri.com/job-listings-agentic-ai-engineer-tata-consultancy-services-hyderabad-chennai-bengaluru-8-to-12-years-130826027970  
- **Access:** 2026-08-23.

**VERIFIED FACT:**  
> “We are seeking an experienced Agentic AI Architect to lead the design and implementation”  
> “Minimum 3+ years of experience in Generative AI or AI Architecture roles. Strong expertise in: Agentic AI ; Multi-Agent Systems; Generative AI ; LLM Architectures”  

Naukri skill chips on the same listing: `Agentic AI`, `LangGraph`, `Generative AI`, `LangChain`, `LLM`, `AI Architecture`, `RAG`, `Azure OpenAI`.

**Wording:** **8–12 overall** with **3+ years in GenAI/AI architecture** — this is the dominant India pattern (“8+ IT + AI skills”), **not** “8+ years training models”. **Java N in captured text. SQL N.**

---

### JD07 — Accenture in India — LLM Operations Engineer — **LIVE**

- **Location:** Pune Division; “based at our PDC3C - SEZ location.”  
- **Exp:** “Minimum 3 Year(s) Of Experience Is Required”; “minimum 3 years of experience in Large Language Models (LLMs).”  
- **Education:** “15 years full time education” (Accenture template).  
- **Posted:** 3 days ago.  
- **URL:** https://in.linkedin.com/jobs/view/llm-operations-engineer-at-accenture-in-india-4456383755  
- **Access:** 2026-08-23.

**VERIFIED FACT:**  
> “Project Role Description : Utilize cloud-native services and tools for scalable and efficient deployment. Monitor LLM performance, address operational challenges, and ensure compliance and security standards in AI operations.”  
> “Must have skills : Large Language Models (LLMs), Generative AI, Agentic AI”  
> “Good to have skills : NA”  
> “The candidate should have minimum 3 years of experience in Large Language Models (LLMs).”

**VERIFIED FACT — professional skills:**  
> “Strong experience with cloud-native services and infrastructure for deploying and managing AI models.”  
> “Ability to monitor and analyze model performance metrics to ensure optimal operation.”  
> “Knowledge of compliance frameworks and security best practices relevant to AI systems.”  
> “Familiarity with automation tools and scripting to support operational tasks.”

**Java N. SQL N.** No LangChain/Python named — **ATS keywords are LLMs, Generative AI, Agentic AI, cloud-native, compliance**. Classic Accenture **keyword-thin** JD. First-screen for an ops person is plausible **if** the resume repeats those three must-haves and shows production monitoring.

---

### JD08 — Capgemini — Agentic with Azure AIFoundry — **LIVE**

- **Location:** Bengaluru. **5+ years overall, at least 1 year in a similar AI-focused role.** Degree Bachelors/Masters CS.  
- **Posted:** ~1 month; 116 applicants.  
- **URL:** https://in.linkedin.com/jobs/view/agentic-with-azure-aifoundry-at-capgemini-4437769635  

**VERIFIED FACT — role:**  
> “Design, develop, and deploy AI-powered solutions using Azure AI Foundry, Azure AI Services, and Azure Agent Services.”  
> “Build intelligent applications leveraging Azure OpenAI, Cognitive Services, and Azure Machine Learning.”  
> “Develop and manage AI Agents for automation, conversational experiences, and enterprise decision support.”

**VERIFIED FACT — profile:**  
> “Hands-on experience in .NET, Java, or Python and cloud-native application development using Azure PaaS services.”  
> “Proven track record of delivering AI/Agent-based projects using Azure AI Foundry, Azure AI Services, and Azure Agent Services.”  
> “Azure certification (preferably AZ-102) and working knowledge of GitHub Copilot”

**Java: YES as one of three languages (.NET, Java, or Python).** Not Java-only. **SQL N.** Filter cost: a Python+Azure OpenAI+Foundry profile still matches; a Java-only profile is equally welcome. User’s Java refusal is **not a hard reject** here if Python is strong.

---

### JD09 — Deloitte USI — GEN AI Engineer, Specialist Assistant Manager — **LIVE**

- **Location:** Hyderabad, Telangana (title also Bengaluru). Tax & Legal Digit@l Asset Factory.  
- **Requisition:** 353050.  
- **URL:** https://usijobs.deloitte.com/en_US/careersUSI/JobDetail/USI-EH27-MFBEL-GEN-AI-ENGINEER-L40-HYD-BLR/353050  
- **Access:** 2026-08-23. **LIVE on employer careers.**

**VERIFIED FACT — work you’ll do:**  
> “Design, develop, test, and deploy generative AI solutions for Tax & Legal use cases.”  
> “Build and maintain applications using Python and generative AI frameworks, including LangChain and/or LlamaIndex.”  
> “Integrate large language model solutions with internal and external platforms through REST application programming interfaces.”  
> “Support the evaluation, monitoring, and observability of AI solutions using tools such as Arize Phoenix, LangSmith, or similar platforms.”  
> “Contribute to cloud deployment, solution architecture, documentation, testing, version control, and continuous integration and continuous deployment practices.”

**VERIFIED FACT — Required:**  
> “Experience developing applications in Python.”  
> “Experience using LangChain and/or LlamaIndex.”  
> “Experience building or integrating REST application programming interfaces.”  
> “Experience working with cloud platforms, preferably Microsoft Azure.”  
> “Experience with source control tools, including Git.”  
> “Experience with testing, continuous integration, and continuous deployment practices.”  
> “Experience supporting AI solution evaluation, monitoring, or observability.”

**VERIFIED FACT — Preferred:** Arize Phoenix or LangSmith; Docker; Agile Scrum; security/compliance; “Exposure to generative AI, data engineering, or large language model-based solutions in production or pilot environments.”

**Java N. SQL N.** Degree not required in the required block. **Wording is application engineering + eval/observability**, not model training. Strong 8.5 YOE adjacent target **if** Python + LangChain/LlamaIndex + Azure + CI/CD + LangSmith/Phoenix are on the resume.

---

### JD10 — EY — AI Engineer, Agentic + Azure AI Foundry, full-stack Azure-native — **LIVE**

- **Location:** Bengaluru.  
- **Exp (verbatim):** “10+ years in a Global IT environment… 3+ Years Global delivery or transformation… 3+ Years in a global operations environment.”  
- **Posted:** 4 days ago.  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-agentic-ai-orchestration-and-azure-ai-foundry-full%E2%80%91stack-azure%E2%80%91native-at-ey-4432756779  

**VERIFIED FACT — job summary:**  
> “The AI Engineer is responsible for building, deploying, and operating production-grade AI and Agentic AI solutions across the enterprise. This is a hands-on engineering role focused on implementing LLM-powered applications, orchestration and multi-agent workflows, and secure API-driven integrations using Azure AI Foundry and Azure-native services (compute, storage, messaging, data, security, and observability).”  
> “A key expectation of the role is to embed evaluation, quality monitoring, and runtime security into AI systems, including the use of LLM-as-a-Judge patterns”

**VERIFIED FACT — core functions (compressed quotes):**  
> “Build Agentic AI Solutions using Azure AI Foundry (Core)”  
> “Develop Orchestration & Multi-Agent Systems (Core)”  
> “Full-Stack Engineering + API Development (Core)”  
> “Serverless & Asynchronous Processing with Azure Functions (Core)”  
> “Vector Databases & Knowledge Stores (Core): … Azure AI Search and/or other vector DB patterns (e.g., Cosmos DB / PostgreSQL pgvector / Redis)”  
> “Continuous Evaluation using LLM-as-a-Judge (Core)”  
> “Nice to Have: Experience integrating AI services into enterprise automation platforms (e.g., Power Platform, ServiceNow).”

**VERIFIED FACT — languages:**  
> “Strong hands-on development in Python / C# / TypeScript/JavaScript (or similar).”

**Certs listed:** “Python Certification; Azure AI Services; Azure Data Services.”

**Java N (C#/TS/Python). SQL not named; pgvector/Cosmos/Redis are.** This is **8+ years IT + 3 years ops/transformation + agentic Azure**, not 8 years of training. ServiceNow is **nice-to-have**. High adjacent fit **if** Azure Functions + Foundry + eval are built in a portfolio.

---

### JD11 — Persistent — Agentic AI Engineer — **EXPIRED walk-in, body indexed**

- **Walk-in date:** 9 May 2026 (past). Locations BLR (Karle Town Centre) and Hyd (Sattva Knowledge City).  
- **Exp:** 5+ / 5–10. All Persistent locations.  
- **URL:** https://www.naukri.com/job-listings-agentic-ai-engineer-persistent-hyderabad-bengaluru-5-to-10-years-050526015522  

**VERIFIED FACT:**  
> “We are seeking a skilled GenAI & Agentic AI Engineer with strong experience in building endtoend AI/ML solutions, Generative AI applications, and agentbased automation workflows. The ideal candidate will have a solid background in machine learning along with handson expertise in LLMs, RAG, embeddings, vector databases, and Agentic AI frameworks such as CrewAI, AutoGen, LangGraph, or LangChain Agents.”  
> “Build and deploy GenAI applications using LLMs (OpenAI, Azure OpenAI, Claude, Gemini, Llama, etc.).”  
> “Develop Agentic AI workflows using frameworks such as CrewAI, AutoGen, LangGraph, or LangChain Agents.”

**Java N. SQL N.** ML background is stated; delivery is still **apps + agents + RAG**.

---

### JD12 — Persistent — Senior AI OPS Engineer — **LIVE**

- **Location:** Pune City (header); “All Persistent Location”. Hybrid/flex mentioned in benefits.  
- **Exp:** Header **“7 to 10 Years”**; body **“5-7 years of relevant software engineering or AI operations experience.”**  
- **Posted:** 2 days ago.  
- **URL:** https://in.linkedin.com/jobs/view/senior-ai-ops-engineer-at-persistent-systems-4453886301  

**VERIFIED FACT:**  
> “The AI Ops Engineer III will design, build, deploy, and maintain AI agents and related software applications. The role requires strong Python engineering skills, experience with AI agent development, and hands-on capability in deploying and supporting solutions on Google Cloud Platform.”  
> “Design, develop, and maintain robust AI agents and software applications using Python and Agent Development Kit (ADK).”  
> “Deploy, monitor, and optimize AI agents and supporting infrastructure within Google Cloud Platform (GCP) environments.”  
> “Develop and manage cloud infrastructure as code using Terraform”  
> “Required Skills: AI Agent development; Python; Google Cloud Platform (GCP); Agent Development Kit (ADK); Terraform; Dev testing and troubleshooting”

**Java N. SQL N.** Title is **AI OPS** but the work is **agent engineering on GCP**, not Splunk/PagerDuty AIOps. Adjacent if the candidate can show Python agents + Terraform + GCP.

---

### JD13 — Hewlett Packard Enterprise — DevOps, MLOps & GenAI Platform Owner (IC) — **LIVE**

- **Location:** Bengaluru. **Hybrid, 2 days/week from an HPE office.** Job Level TCP_04.  
- **Posted:** 2 weeks ago; 200+ applicants.  
- **URL:** https://in.linkedin.com/jobs/view/devops-mlops-genai-platform-owner-ic-at-hewlett-packard-enterprise-4450233534  

**VERIFIED FACT — what you’ll do:**  
> “Own production systems: incidents, SLAs, stability, uptime”  
> “Drive RCA and eliminate recurring issues (sync, bots, latency)”  
> “Improve observability, monitoring, and reliability”  
> “Build and optimize CI/CD, MLOps, and GenAI pipelines”  
> “Deploy and tune ML/GenAI models (RAG, prompt optimization)”  
> “Own/Govern RPA platforms (WorkFusion/UiPath)”  
> “Improve retrieval accuracy, reduce hallucinations”  
> “Production support at scale, incident mgmt, change mgmt and ITIL governance”  
> “Data pipelines & enterprise integrations (SAP, ServiceNow, SharePoint, etc)”

**VERIFIED FACT — core tech:**  
> “DevOps/MLOps: Jenkins, GitLab, Azure DevOps”  
> “Cloud + Containers: Azure, Docker, Kubernetes”  
> “Programming: Python, Java, Selenium”  
> “RPA: WorkFusion / UiPath / Automation Anywhere”  
> “GenAI (RAG, prompt engineering, evaluation)”  
> “Monitoring: Prometheus, Grafana, ELK, Spark, Airflow”

**Java: YES (listed with Python, Selenium).** SQL not named. **This is one of the strongest adjacent JDs in the corpus** for a Service Desk / IT Ops lead: ITIL, incidents, ServiceNow, RAG, RPA, observability. Filter cost of avoiding Java: **medium** — Java is listed but the GenAI/ops story is Python+RAG+ITIL.

---

### JD14 — NXP Semiconductors — Software DevOps Engineer - for Gen AI — **LIVE**

- **Location:** Bengaluru. **5+ years** SWE backend; **1+ year** foundational LLMs in production; **2+ years** DBMS. BA/BS IT/CS or equivalent.  
- **URL:** https://in.linkedin.com/jobs/view/software-devops-engineer-for-gen-ai-at-nxp-semiconductors-4390640553  
- **Posted:** 2 weeks; 200+ applicants.

**VERIFIED FACT:**  
> “Develop, enhance and implement software systems designed to support generative AI initiatives.”  
> “Proficiency in Python, Java, Node.JS, React.js”  
> “Proven experience with Generative AI frameworks and Models”  
> “Experience working within cloud technologies such as AWS Lambda, CloudFront, S3, EC2, Bedrock”  
> “1+ year of experience working with foundational LLM models, including deploying, fine-tuning, and integrating models into production environments”  
> “2+ years experience on Database management systems”

**Java: YES (core proficiency list). SQL: YES via DBMS.** Fine-tuning is required (1 year). This is a **SWE kitchen sink + GenAI**. User’s Java/SQL refusal is a **real first-screen risk**.

---

### JD15 — Qualys — Machine Learning Operations Engineer — **LIVE**

- **Location:** Pune. **2–3 years** building/deploying end-to-end ML products.  
- **URL:** https://in.linkedin.com/jobs/view/machine-learning-operations-engineer-at-qualys-4417876201  
- **Posted:** 4 days; 200+ applicants.

**VERIFIED FACT:**  
> “Design, build, and deploy robust ML pipelines for training, fine-tuning, and inference of models (NLP-focused: NER, Classification).”  
> “Hands on with Helm deployment of ML Pipelines in Kubernetes cluster”  
> “Use MLflow, Kubeflow, and related tools for experiment tracking, model versioning, and reproducibility.”  
> “Write clean, efficient, and scalable code in Python using frameworks such as PyTorch and CUDA.”  
> “Experience with tuning, optimising LLM Applications performance in production.”  
> “Familiarity with CUDA for training models on GPU.”  
**Good to Have:**  
> “Experience with Generative AI systems in production.”  
> “Prior experience with building or deploying applications in Hardwares such as L40S, H100, H200.”  
> “Familiarity with LangChain, LangGraph, LangSmith for building LLM-powered agents and applications.”

**Java N. SQL N.** This is **core MLOps / training / GPU**. An IT-ops + RAG portfolio will **not** first-screen without PyTorch/K8s/Helm/MLflow evidence. LangGraph is only GTH.

---

### JD16 — Hitachi Energy — AI Automation Engineer — **LIVE** (publication date 2026-08-18)

- **Location:** Bengaluru. Common Shared Services / Business Process Automation. Two tracks: AI Delivery and AI Exploration.  
- **Exp:** **5–10 years** in software engineering, AI engineering, ML, or related. Bachelor’s/Master’s; PhD advantage for Exploration. **SQL required.** Java or C#/.NET **advantage**.  
- **URL:** https://in.linkedin.com/jobs/view/ai-automation-engineer-at-hitachi-energy-4455774089  
- **200+ applicants** in 4 days.

**VERIFIED FACT — impact (selected):**  
> “Design and build AI-powered and agentic solutions that automate complex, repetitive, or decision-driven tasks across Common Shared Services processes.”  
> “Develop applications leveraging large language models (LLMs) and multimodal foundation models using techniques such as Retrieval-Augmented Generation (RAG), tool calling, structured outputs, and context engineering.”  
> “Build, orchestrate, and govern AI agents using frameworks such as LangGraph, Semantic Kernel, Microsoft Agent Framework, Azure AI Foundry Agent Service, and Model Context Protocol (MCP).”  
> “Develop APIs, integrations, and event-driven pipelines that embed AI capabilities into enterprise platforms including SAP, ServiceNow, Microsoft 365, Power Platform, data lakehouse environments, and existing automation technologies.”  
> “Establish AI evaluation and observability practices including automated evaluations, regression testing, tracing, quality monitoring, cost governance, and performance measurement.”  
> “For AI Delivery, drive the industrialization of validated AI use cases through scalable architectures, LLMOps/MLOps practices, CI/CD automation, deployment standards, and production support models.”

**VERIFIED FACT — background:**  
> “Strong programming capabilities in Python, including testing, packaging, asynchronous programming, and software engineering best practices. Experience with SQL is required, while Java or C#/.NET is an advantage.”  
> “Hands-on experience with LLM and agent frameworks such as LangChain, LangGraph, LlamaIndex, Semantic Kernel, Microsoft Agent Framework, OpenAI Agents SDK, Google ADK, CrewAI, and MCP-based integrations.”  
> “Experience working with cloud AI platforms, particularly Azure AI Foundry and Azure OpenAI, along with exposure to platforms such as Google Vertex AI, Amazon Bedrock, or Databricks Mosaic AI.”  
> “Experience with AI evaluation and observability tools such as LangSmith, Langfuse, Ragas, MLflow, promptfoo, or Azure AI evaluation services.”  
> “Knowledge of Responsible AI, AI governance, OWASP Top 10 for LLM applications, prompt injection mitigation”

**SQL: REQUIRED. Java: advantage only.** Filter cost of avoiding SQL: **this JD fails a literal ATS SQL screen**. Content is otherwise the **best-in-corpus map** of the user’s preferred stack (RAG, agents, MCP, LangGraph, ServiceNow, LLMOps, eval). Adjacent **if** SQL is not a hard ATS gate.

---

### JD17 — Smart Working — LLM Systems / AI Agent Engineer (Remote) [AS311] — **LIVE**

- **Location:** Hyderabad, Telangana (also posted as India remote). Shifts **12:00–21:30 IST (summer) / 13:00–22:30 IST (winter)**. No weekend work. Laptop + medical Day 1.  
- **Posted:** 4 days ago; 61 applicants.  
- **URL:** https://in.linkedin.com/jobs/view/llm-systems-ai-agent-engineer-remote-full-time-as311-at-smart-working-4452583680  

**VERIFIED FACT — about the role:**  
> “As an LLM Systems / AI Agent Engineer, you will focus on building and evolving production AI agents on foundation models, covering orchestration, context engineering, evaluation pipelines, and production observability and monitoring. This is an LLM systems and AI agent engineering position rather than a traditional ML model-training role.”

**VERIFIED FACT — requirements:**  
> “2+ years of experience building production LLM agents, including tool-calling agent loops, streaming, context management, structured outputs and orchestration frameworks.”  
> “Production experience with an agentic framework such as LangGraph, LangChain or custom orchestration.”  
> “1.5+ years of experience with evaluation-driven development, including building and maintaining evaluation datasets and pipelines covering tool selection, trajectory evaluation and LLM-as-judge.”  
> “1+ year of experience with LLM observability, tracing and instrumentation using Langfuse, OpenTelemetry or similar tooling.”  
> “1+ year of experience with LLM cost optimisation, including prompt caching, model selection and routing, and LLM FinOps.”  
> “5+ years of backend engineering proficiency, including TypeScript/Node, Postgres and serverless AWS.”

**Nice to have:** Bedrock (or transferable OpenAI/Anthropic/Azure OpenAI/Vertex); guardrails; “6+ months of familiarity with MCP and multi-agent patterns.”

**Java N. SQL: Postgres required.** Primary language is **TypeScript/Node, not Python**. Filter cost: Python-only positioning **misses this JD**. Adjacent (explicitly **not** model-training). High bar on **production agents + eval + Langfuse**.

---

### JD18 — MyAdvice — AI Engineer I (Generative AI) — **LIVE** (older)

- **Location:** Remote to start; “we will prioritize candidates that are located in Bangalore or willing to relocate.” Schedule **11:00pm to 8:00pm IST** (US overlap).  
- **Exp:** **1–3 years** AI/ML or SWE.  
- **Salary (employer-disclosed):** **₹12–15 LPA**.  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-l-generative-ai-at-myadvice-4430414644  
- **Degree:** Bachelor’s CS/Eng/AI preferred.

**VERIFIED FACT — required:**  
> “Strong proficiency in Python (must)”  
> “Hands-on with LangChain, LlamaIndex, HuggingFace Transformers, or equivalent”  
> “Experience building RAG pipelines, embedding models, and vector database integrations”  
> “Familiarity with AI agent frameworks and multi-step generative workflows”  
> “Experience deploying ML systems on AWS / GCP”  
> “Proficiency with containerization: Docker, Kubernetes”  
> “Experience with MLOps tooling: MLflow, Weights & Biases, Sagemaker, Vertex AI, etc”  
> “Experience working with GPT, LLaMA, Claude, Gemini or similar LLMs”  
> “Fine-tune and evaluate large language models (LLMs), including GPT models, LLaMA, Gemini”

**Java N. SQL N.** Disclosed **12–15 LPA for 1–3 YOE** is a useful 2026 anchor. Night-shift. Fine-tuning is in the duty list → mixed core/adjacent. Not an 8.5 YOE target (under-levelled).

---

### JD19 — StackNexus — GEN AI ENGINEER — **OLDER** (4 months)

- **Location:** Remote (U.S. working hours). Contract. Immediate start. **+5 Years.**  
- **URL:** https://in.linkedin.com/jobs/view/gen-ai-engineer-at-stacknexus-4403195999  

**VERIFIED FACT:**  
> “5+ years of experience in Product development and AI/ML or NLP solution development.”  
> “Design, implement, and optimize AI agents leveraging frameworks such as LangChain, LlamaIndex, or Haystack.”  
> “Build and maintain RAG (Retrieval-Augmented Generation) pipelines combining LLMs, embeddings, and vector search.”  
> “Strong coding proficiency in Python with practical experience in libraries like FastAPI, Pandas, PyTorch, TensorFlow, or Transformers.”  
> “Familiarity with cloud AI services such as GCP Vertex AI (preferred) or AWS Bedrock, Azure OpenAI etc.”  
> “Hands-on experience with RESTful API development, microservices, and containerized deployments (Docker/Kubernetes).”  
GTH: multi-agent; MLOps/CI/CD; monitoring/cost.

**Java N. SQL N.** US-hours contract. PyTorch/TF listed — mixed.

---

### JD20 — Hired (unnamed client) — AI Engineer - Generative AI (Remote) — **RECENT-CLOSED**

- **Location:** Remote (Work from Anywhere) / India.  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-generative-ai-remote-at-hired-4446713048  
- **Status:** “No longer accepting applications.” Posted 3 weeks ago.

**VERIFIED FACT:**  
> “Proficient in Python and SQL for AI system development”  
> “Experience with LangChain and modern LLM frameworks”  
> “Deep understanding of LLM internals, including prompt tuning, embeddings, vector databases, and agent workflows”  
> “Design and develop generative AI and LLM-based systems using tools such as LangChain and retrieval-augmented generation (RAG) pipelines”  
> “Implement prompt engineering techniques and agent-based frameworks”

**SQL: YES (paired with Python as proficiency).** Java N. Closed. Useful only as a **SQL-prevalence data point**.

---

### JD21 — Ascendion — Lead Generative AI Engineer (5–12 Years) — **EXPIRED drive**

- **Location:** Bengaluru, Bellandur office. Drive **11 July 2026**; registration closed 9 July 2026.  
- **Exp:** **“5–12 years of overall software engineering experience.”** “Strong hands-on experience building and deploying production-grade GenAI/LLM applications.”  
- **LinkedIn job ID 4428493435** redirected to expired search on 23 Aug 2026. Body from LinkedIn search cache (published 2026-08-18 crawl).

**VERIFIED FACT:**  
> “Strong hands-on experience building enterprise GenAI applications, including LLM-powered solutions, RAG architectures, AI Agents, and real-time AI systems.”  
> “Design, develop, and deploy production-grade Generative AI applications using OpenAI (GPT/Codex), Azure OpenAI, Anthropic Claude, Google Gemini, Meta Llama, and Mistral.”  
> “Build scalable GenAI solutions including RAG pipelines, AI Agents, multi-agent workflows, enterprise copilots, and intelligent automation platforms using LangChain, LangGraph, Semantic Kernel, AutoGen, or CrewAI.”

**Wording is 5–12 SWE + production GenAI — not 5–12 years of AI research.** Java N. SQL N in captured text.

---

### JD22 — Cirrus Labs — AI Engineer (LangGraph / LangChain / RAG) — **INDEXED-LIVE**

- **Location:** Hybrid Hyderabad / Bengaluru. **3–8 years.**  
- **URL:** https://www.naukri.com/job-listings-ai-engineer-agentic-workflows-langgraph-langchain-rag-pipelines-cirruslabs-hyderabad-bengaluru-3-to-8-years-171225015734  
- **Direct open on 23 Aug:** “Job you are looking for is expired.” Body from Google snippet (also “1 day ago” on Naukri SERP).

**VERIFIED FACT:**  
> “Developing End-to-end agentic workflows (LangGraph, LangChain etc).”  
> “Design tool integrations: APIs, SQL tools, RAG pipelines, automations.”  
> “Build RAG pipelines: embeddings, chunking, indexing, hybrid search.”  
> “Optimize knowledge retrieval for accuracy + hallucination reduction.”  
> “Manage vector DBs (Pinecone/FAISS/We aviate/Chroma DB) and document ingestion.”

**SQL: YES as “SQL tools” for agents.** Java N. Highly adjacent.

---

### JD23 — 360DigiTMG (payments-modernisation client) — GenAI Engineer Agentic AI & RAG — **INDEXED-LIVE**

- **Location:** Bengaluru. **4–8 years.** Python mandatory; **1–2+ years real-world GenAI/LLM.**  
- **URL:** https://www.naukri.com/job-listings-genai-engineer-agentic-ai-rag-360digitmg-bengaluru-4-to-8-years-070426500532  
- Direct listing expired 23 Aug; body from index.

**VERIFIED FACT:**  
> “Design and build agentic AI solutions using LangChain, LangGraph, and RAG.”  
> “Develop LLM-powered workflows and intelligent automation systems.”  
> “Build Python-based microservices and orchestration layers.”  
> “Implement vector databases, embeddings, and retrieval systems.”  
> “Strong hands-on experience in Python (mandatory).”  
> “Expertise in RAG pipelines, embeddings, and vector databases.”  
> “Experience with LangChain / LangGraph or similar frameworks.”

**Java N. SQL N.** Classic adjacent IC JD.

---

### JD24 — Infinity (Stamford Technology) — GenAI / Agentic AI Engineer — **INDEXED-LIVE**

- **Location:** Hybrid Hyderabad, Chennai, Bengaluru. **10–18 years.** Education: B.Tech/B.E.  
- **URL:** https://www.naukri.com/job-listings-genai-agentic-ai-engineer-stamford-technology-hyderabad-chennai-bengaluru-10-to-18-years-090126021616  

**VERIFIED FACT:**  
> “Design and develop GenAI solutions using LLMs (OpenAI, Azure OpenAI, Anthropic, etc.)”  
> “Build Agentic AI systems using frameworks like LangChain, LangGraph, CrewAI, or AutoGen”  
> “Implement RAG pipelines with vector databases (FAISS, Pinecone, Weaviate, Chroma)”  
> “Optimize prompt engineering, tool calling, and memory management”  
> “Integrate AI models with APIs, databases, and enterprise applications”

**Java N. SQL not named; “databases” yes.** 10–18 YOE band can include 8.5. Chennai listed.

---

### JD25 — Cognizant — AI OPS / MLOPS Engineer — **EXPIRED (404)**

- **Location:** Bangalore, Hybrid. **7 to 13 years.** Notice **Immediate to 90 days.** Job `00068075121`. Date published **18 May 2026**.  
- **URL:** https://careers.cognizant.com/global-en/jobs/00068075121/ai-ops-integrationapi-engineer-with-mlops-ai-ml-developer/  
- **23 Aug 2026: 404.** Body from earlier index.

**VERIFIED FACT:**  
> “Role : AI OPS / MLOPS Engineer - AIML Developer”  
> “AWS SageMaker, Azure ML Studio, GCP Vertex AI”  
> “PySpark, Azure Databricks”  
> “MLFlow, KubeFlow, AirFlow, Github Actions, AWS CodePipeline”  
> “Kubernetes, AKS, Terraform, Fast API”  
> “Model Deployment, Model Monitoring, Model Retraining”  
> “Drift Detection, Data Drift, Model Drift”  
> “Wide experience with Kubernetes.”

**Java N. SQL N in captured keywords.** Core **MLOps platform**, not RAG-chatbot. Adjacent for someone with K8s/CI/CD/monitoring; **not** a first-screen win with only a LangChain demo.

---

### JD26 — Allianz Technology — AI Operations — **EXPIRED**

- **Location:** Pune, onsite. **2–6 years.** Posted 2 Jun 2026. TAL tagged Expired.  
- **URL:** https://www.grapevine.in/tal/jobs/21d24a2a-1753-44e4-9afb-760f3f23ecb6  

**VERIFIED FACT — must haves (TAL extract of JD):**  
> “Experience with Python or Node.js for automation”  
> “Hands-on experience with Grafana, Dynatrace, or Azure Monitor”  
> “Operational experience with Docker and Kubernetes”  
> “Experience with CI/CD tools like Jenkins, GitHub Actions, or GitLab CI”  
> “Knowledge of LLMOps and MLOps concepts”  
> “Experience with ITSM tools like ServiceNow”

**Tools listed:** python, node.js, grafana, dynatrace, azure monitor, application insights, log analytics, prometheus, azure, aws, gcp, docker, kubernetes, git, jenkins, github actions, gitlab ci, servicenow, **sql, nosql**, llmops, mlops. Nice to have: azure administrator/architect, cka/ckad, **itil**.

**SQL: YES in tools list. Java N.** **Best-in-class AIOps/SRE adjacent JD** (ServiceNow + observability + LLMOps). Expired as of harvest.

---

### JD27 — IRIS Software — MLOps & AIOps / GCP Lead — **INDEXED-LIVE (fetch failed)**

- **Location:** Noida, Hybrid. **8–9 / 8–10 years.** Full-time/contract. Posted ~3 days on Foundit.  
- **URL:** https://www.foundit.in/job/mlops-aiops-gcp-lead-iris-software-noida-54024539  
- Direct page fetch failed 23 Aug. Body from Foundit index.

**VERIFIED FACT:**  
> “We are seeking an experienced MLOps & AIOps / GCP Engineer to join the Gemini domain team. This role focuses on designing, building, and operating secure, scalable, production-grade ML and GenAI platforms on Google Cloud Platform (GCP), enabling reliable model training, deployment, monitoring, and incident response.”  
> “operationalize ML/GenAI use cases (including agentic workflows)”  
> “Experience: 8-9 years”  
> “Primary Tech Stack: Python, GCP, Vertex AI, GitHub CI/CD, LangChain, LangGraph”  
> “Python (production-grade development, packaging, testing, performance profiling)”

**Java/SQL:** not in captured snippet. NCR location. Adjacent platform+agentic. **8–9 YOE matches target.**

---

### JD28 — Zealant Consulting (CLM client) — AI Engineer (Agentic AI Development) — **LIVE**

- **Location:** Bengaluru. **3+ years SWE, 1+ year LLM systems in production.**  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-agentic-ai-development-at-zealant-consulting-group-4439984153  
- Posted ~1 month; 94 applicants.

**VERIFIED FACT:**  
> “This is an engineering role for someone who thinks in systems: multi-agent orchestration, tool use, state management, guardrails, and failure recovery.”  
> “Design and implement multi-agent pipelines using frameworks like Lang Graph, Crew AI, AutoGen, or equivalent—taking systems from design through production deployment.”  
> “Implement human-in-the-loop (HITL) checkpoints, escalation logic, and guardrail layers”  
> “Develop observability and tracing so the team can understand when an agent made the right call (and when it didn’t).”  
> “Create evaluation harnesses to measure agent behavior across edge cases—not just happy paths.”  
> “Hands-on experience building agentic or multi-agent systems (not just chatbots or RAG pipelines).”  
> “Strong Python skills; comfortable with async patterns, API design, and distributed systems fundamentals.”

**Preferred:** Pinecone/Weaviate/pgvector; Temporal/Airflow. **Java N. SQL N.** High-quality **adjacent-but-strict** (production agents, not demos).

---

### JD29 — ApTask — Agentic AI Engineer – Azure | LLM | RAG | LangGraph — **LIVE**

- **Location:** Pune / Bengaluru / Bhopal, FTE. **6+ years** SWE/AI. Also “hands-on AI (3+ years)” in summary.  
- **URL:** https://in.linkedin.com/jobs/view/agentic-ai-engineer-%E2%80%93-azure-llm-rag-langgraph-at-aptask-4452561905  
- 5 days ago; 200+ applicants.

**VERIFIED FACT:**  
> “Architect and build Agentic AI systems: orchestrate agents, action executors, retrieval layers, and feedback loops.”  
> “Design and implement LLM solutions (RAG, retrieval chains, prompt engineering, fine-tuning/LoRA/P-tuning) for production use.”  
> “Build MLOps & ModelOps pipelines: CI/CD for models and services, automated testing, monitoring, drift detection and rollbacks.”  
> “Deep experience with LLMs and RAG architectures: retrieval design, vector DBs (Pinecone/Weaviate/Milvus), embeddings.”  
> “Strong Azure AI stack experience: Azure OpenAI/GPT, Azure ML, AKS, Azure Functions, KeyVault, Data Factory/Synapse.”  
> “Expertise in Agentic frameworks and orchestration (LangChain, LangGraph, custom agent frameworks).”  
> “Backend engineering: Python, FastAPI, microservices, Docker, Kubernetes, gRPC/REST”  
> “Data engineering basics: SQL/NoSQL, ETL, schema design, data lineage and data privacy controls.”

**SQL: YES. Java N.** Fine-tuning **and** RAG **and** MLOps — kitchen-sink mid/senior. First-screen risk if fine-tune/LoRA is a hard gate.

---

### JD30 — BNP Paribas — Agentic AI & DevOps — **LIVE**

- **Location:** Mumbai / Bangalore. **Experience level: 7–9+ years** “production experience as Senior lead under Agent AI & Devops”. **5+ years in DevOps / AI/ML engineering, with 2+ years on LLM-based agentic systems in production.** Degree CS/IT.  
- **URL:** https://in.linkedin.com/jobs/view/agentic-ai-devops-at-bnp-paribas-4448761124  
- Posted 2 weeks; 109 applicants.

**VERIFIED FACT:**  
> “Lead technical delivery of AI agents and MVPs for cross-functional business units — IT ops, compliance, risk, business lines — within the group's established agentic framework”  
> “Drive pure innovation work in parallel: prototype emerging approaches (LightRAG, TigerRAG, graph-based RAG, advanced MCP patterns)”  
> “Design agentic workflows using LangChain, LangGraph, and LangServe — multi-agent reasoning, tool-calling, stateful orchestration, API/microservice exposure”  
> “Build production assistants on real infra datasets: incident investigation, RCA, change analysis, CMDB querying, run assistance, documentation search”  
> “Implement and enforce guardrails: hallucination control, access control, secrets management, output validation, sensitive data handling”  
> “Own end-to-end observability via LangSmith”  
> “Deploy and operate POC environments on cloud-native and containerized platforms (Docker, Kubernetes, Helm, GitOps, ArgoCD, GitLab CI/CD)”  
> “Mastery of containerized environments: Docker, Kubernetes, Helm, GitOps, GitLab CI/CD, ArgoCD”  
> “Solid classical observability: Prometheus, Grafana, ELK/OpenSearch, OpenTelemetry”  
> “Go or TypeScript alongside Python” (competency list)  
> “Knowledge of DPDP Act (India) and/or GDPR”

**Java N. SQL N in captured text (CMDB querying is ops data).** **Highest-fit GCC JD in the corpus for a Service Desk / IT Ops person who can actually ship LangGraph agents against ITSM/CMDB data.** Bar is high: 2+ years **production** agents, not a weekend RAG.

---

### JD31 — UST — AI Engineer — **LIVE**

- **Location:** Bengaluru. **3–5 years** ML/AI with production systems; **at least 1 year building custom Agentic AI applications.**  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-at-ust-4441090818  
- 1 week; 200+ applicants.

**VERIFIED FACT:**  
> “We are seeking a AI Engineer to build and deliver production-grade agentic AI systems for enterprise use. … The work centers on building agents, orchestration logic, and supporting infrastructure that performs under real production workloads, not on proof-of-concept or advisory work.”  
> “Build AI agents and multi-agent systems using frameworks with LangGraph and LangChain tools.”  
> “Develop and tune prompt engineering workflows across multiple LLMs (GPT, Claude, LLaMA), balancing reliability, cost, and latency.”  
> “Automate testing and releases through Jenkins CI/CD”  
> “Use AI-augmented development tools such as Claude Code and Codex to accelerate delivery.”  
> “Familiarity with at least one enterprise cloud AI platform … Azure AI Foundry, AWS Bedrock, or Google Gemini Enterprise”  
> “Good-to-Have: Familiarity with Databricks. Exposure to MLOps/LLMOps workflows and application monitoring.”

**Java N. SQL N.** Under-YOE vs 8.5 unless they hire seniors into the same req. Adjacent.

---

### JD32 — Tech Mahindra — Agentic AI Engineer — **PARTIAL**

- Pune, Bengaluru. 5–10 Yrs. Posted 3 days.  
- **URL:** https://www.naukri.com/job-listings-agentic-ai-engineer-tech-mahindra-pune-bengaluru-5-to-10-years-190826025169  

**VERIFIED FACT (must-have chips + snippet):** Agentic Ai, Langchain, OpenAI, Retrieval Augmented Generation, Python.  
> “Proven experience in developing and deploying Agentic AI systems solutions, preferably in Telecom Domain”

**Java/SQL unknown.** Full body not retrieved.

---

### JD33 — HCLTech — Agentic AI Engineer — **PARTIAL**

- Noida, Hyderabad, Bengaluru. 4–9 Yrs.  
- **URL:** https://www.naukri.com/job-listings-agentic-ai-engineer-hcltech-noida-hyderabad-bengaluru-4-to-9-years-140826022057  

**VERIFIED FACT:**  
> “Proficiency in Python and frameworks such as PyTorch or TensorFl…”  
Skill chips: Agentic Ai, Gen AI, Vector DB, Python.

**Core-leaning** if PyTorch is a must. Full body not retrieved.

---

### JD34 — Altimetrik — Gen AI Engineer — **PARTIAL** (includes **Chennai**)

- Hybrid Hyderabad, Chennai, Bengaluru. 5–10 Yrs. 2 days ago.  
- **URL:** https://www.naukri.com/job-listings-gen-ai-engineer-altimetrik-hyderabad-chennai-bengaluru-5-to-10-years-200826016294  

**VERIFIED FACT:**  
> “Proficient in LLMs & AI frameworks, including OpenAI, BERT, LLaMA, Gemini, RAG pipeline…”  
Chips: generative ai, Tensorflow, Vector DB, NLP, ML, Pytorch, Docker.

Mixed core (TF/BERT) + RAG.

---

### JD35 — HP — AI and Automation Developer — **LIVE**

- Bengaluru. Typically **5–7 years**. 2 weeks; 200+ applicants.  
- **URL:** https://in.linkedin.com/jobs/view/ai-and-automation-developer-at-hp-4449084177  

**VERIFIED FACT:**  
> “We are seeking a AI & Automation Developer to design and deliver cutting-edge solutions at the intersection of Agentic AI, automation, and opportunity discovery.”  
> “Design and develop Agentic AI systems using LLMs and multi-agent frameworks”  
> “Integrate AI-driven solutions with enterprise systems (e.g., JIRA, SharePoint, ServiceNow) via APIs and cloud platforms.”  
> “Strong programming background (Python required; JavaScript/TypeScript or other languages a plus).”  
> “Knowledge of agent frameworks (e.g., LangChain Agents, OpenAI Agents, AutoGen).”  
> “Experience building automation workflows using RPA tools, scripting, or custom logic.”  
> “Familiarity with RAG (Retrieval-Augmented Generation), vector databases, and enterprise data systems.”

**Knowledge & Skills laundry list includes Java, C++, TensorFlow, PyTorch** — typical HP Workday dump, **not** the same as “Python required” in Required Skills. Treat Java as **ATS noise**, Python as the real must. **SQL N.** Adjacent. ServiceNow named.

---

### JD36 — Convera — Agentic AI Engineer (ITSM & Enterprise Automation) — **LIVE**

- Pune. **3+ years as AI engineer or AI Ops Engineer.** 4 days ago.  
- **URL:** https://in.linkedin.com/jobs/view/agentic-ai-engineer-itsm-enterprise-automation-at-convera-4455712445  

**VERIFIED FACT:**  
> “Join us as AI Ops / IT Automation Engineer and help transform IT service delivery through agentic AI, workflow orchestration, and intelligent automation.”  
> “This role will help design, build, and run agentic AI workflows that improve selfservice adoption, reduce ticket volumes, and shorten timetoresolution while maintaining strong governance, auditability, and security.”  
> “Build, configure, and maintain AI Agents for IT incidents, service requests, and employee self-service”  
> “Design, build, and operate Agentic Workflows including branching logic, retries/timeouts, approvals, and humanintheloop handoffs”  
> “Implement and maintain integrations using MCP, APIs, webhooks, and eventdriven Triggers to connect ITSM, identity, endpoint, and collaboration systems”  
> “3+ years of experience as AI engineer or AI Ops Engineer.”  
> “Strong understanding of IT service management processes (Incident, Request, Change, SLAs)”  
> “Deep experience in integrating enterprise tools such as Nexthink, Zoom Contact Center (ZCC), IAM platforms (Okta, SailPoint), ServiceNow, and similar ITSM, identity, and observability tools”  
> “Excellent analytical skills and experience of JavaScript and automation scripting to streamline operations (Python or PowerShell is a plus)”  

**Preferred:**  
> “Hands-on experience working on Rezolve.ai, ServiceNow Agentic AI, Moveworks, Aisera, Kore.ai, or similar agentic AI / intelligent ITSM platforms”  
> “Experience implementing Retrieval-Augmented Generation (RAG) architecture and Vector Databases”

**Java N. JavaScript YES (primary). Python is a plus, not the must.** **SQL N.**  

**This is the single strongest first-screen-adjacent JD in the harvest for a Service Desk Lead:** ITIL processes, ServiceNow, ticket deflection, MCP, HITL, IAM. Filter cost of **Python-only** positioning: **you must also show JavaScript automation** or a ServiceNow/Rezolve/Moveworks artefact.

---

### JD37 — Google Cloud — Generative AI Forward Deployed Engineer — **LIVE**

- **Location note:** “preferred working location from the following: Mumbai, Maharashtra, India; Pune, Maharashtra, India; Bengaluru, Karnataka, India.” (This LinkedIn ID resolved to Mumbai header.)  
- **Min qual:** Bachelor’s Eng/CS or equivalent; **8 years** in cloud computing or a technical customer-facing role.  
- **URL:** https://in.linkedin.com/jobs/view/generative-ai-forward-deployed-engineer-google-cloud-at-google-4451133303  
- 1 week; 200+ applicants.

**VERIFIED FACT — minimum:**  
> “Experience building pipelines for structured and unstructured data using both vector databases and RAG-like architectures to power enterprise AI solutions.”  
> “Experience taking production-grade AI-driven solutions from conception to launch and architecting AI systems on cloud platforms (e.g., Google Cloud Platform (GCP)).”  
> “Experience leading technical discovery sessions.”

**VERIFIED FACT — preferred:**  
> “Master’s or PhD in AI, Computer Science, or a related technical field.”  
> “Experience implementing multi-agent systems using frameworks (e.g., LangGraph, CrewAI, ADK) and complex patterns (e.g., ReAct, self-reflection, hierarchical delegation).”  
> “Knowledge of \"LLM-native\" metrics (e.g., tokens/sec, cost-per-request) and techniques for optimizing state management and granular tracing.”

**VERIFIED FACT — responsibilities:**  
> “Serve as a developer for complex AI applications, transitioning from rapid prototypes to production-grade agentic workflows (e.g., multi-agent systems, model context protocol (MCP) servers) that drive measurable return on investment (ROI).”  
> “Build high-performance evaluation pipelines and observability frameworks to ensure agentic systems meet rigorous requirements for accuracy, safety, and latency.”

**Java N. SQL N.** **8 years cloud or customer-facing technical** — wording is **not** “8 years of model research”. Still a **Google bar** (discovery sessions, production GCP, eval). Adjacent-elite, not a first-screen walk-in.

---

### JD38–JD50 — PARTIAL / CLOSED (kept for inventory, not padded)

**JD38 PwC Agentic AI Engineer** — Hybrid Hyd/BLR, 6–9 Yrs, chips: Agentic Ai, Langgraph, LLM, **ITIL**, Python. URL: https://www.naukri.com/job-listings-agentic-ai-engineer-pwc-hyderabad-bengaluru-6-to-9-years-200826037654 — **ITIL on an Agentic JD is a verified chip**, full body not captured.

**JD39 PwC AI Engineer** — 5–9 Yrs Hybrid Hyd/BLR. “At least a Bachelors degree. At least 4 years of experience.” Chips: generative ai, Aiml, Node.js, React.js, Python. https://www.naukri.com/job-listings-ai-engineer-pwc-hyderabad-bengaluru-5-to-9-years-180826010128

**JD40 PwC AC Gen AI Engineer Senior Associate Bangalore** — https://jobs-ta.pwc.com/global/en/job/724190WD/Gen-AI-Engineer-Senior-Associate — **“the job you are trying to apply for has been filled.”** 23 Aug 2026.

**JD41 ADP Walk-in Gen AI Engineer** — Hybrid Hyderabad, 3–8 Yrs, walk-in **25 Aug 2026**. Snippet: “Experience designing and developing Agentic AI solutions, including autonomous workflow…” Chips: AWS Certified, Python, NLP, AWS, Deep Learning. https://www.naukri.com/job-listings-gen-ai-engineer-adp-private-limited-hyderabad-3-to-8-years-220826011986

**JD42 Blackstraw.ai Walk-in Generative AI Engineer Chennai** — 2–6 Yrs, walk-in **24 Aug 2026**. SERP snippet: “Bachelors or Masters degree in Computer Science, AI / ML, Data Science, or related fiel…” chips: Computer Vision, Image Recognition, Retrieval Augmented Generation, Python, Agentic Ai. Same week the company also posts **Java Fullstack Immediate Joiner** (red-flag kitchen-sink campus). https://www.naukri.com/job-listings-genai-engineer-blackstraw-technologies-chennai-2-to-7-years-110826014145 and related `…-generative-ai-engineer-blackstraw-ai-chennai-…`

**JD43 DXC AI Engineer** — “Generative AI Engineer. Job Location: Hyderabad / Bangalore / Chennai / Kolkata / Noida”. Chips: foundry, generative ai, azure machine learning, faiss. https://www.naukri.com/job-listings-ai-engineer-dxc-technology-bengaluru-5-to-10-years-210826503111

**JD44 Cognizant AI Engineer** — 6–11 Yrs Hybrid BLR/Pune/Chennai. “The ideal candidate should have successfully built data pipelines, deployed AI / ML mod…” https://www.naukri.com/job-listings-ai-engineer-cognizant-pune-chennai-bengaluru-6-to-11-years-180826040982

**JD45 Wissen SRE AI Engineer** — 5–9 Yrs, **15–25 Lacs PA** (employer-listed on Naukri), Hybrid BLR/Pune/Mumbai. “Infrastructure as Code (IaC) tools such as Terraform…” chips: Devops, SRE, Python, Ci/Cd, Cursor, Docker, Azure Cloud. https://www.naukri.com/job-listings-sre-ai-engineer-wissen-technology-pune-bengaluru-mumbai-all-areas-5-to-9-years-210826004877 — **salary disclosed 15–25 LPA** for SRE+AI. Adjacent.

**JD46 Advance Career Solutions Agentic AI Engineer** — 8–13 Yrs, **20–27.5 Lacs PA**, Hybrid BLR/Hyd/Pune. “We are seeking an innovative Agentic AI Engineer to design develop and deplo…” https://www.naukri.com/job-listings-agentic-ai-engineer-advance-career-solutions-hyderabad-pune-bengaluru-8-to-13-years-210826009123 — **salary disclosed**. Full body not captured.

**JD47 Qentelli AI Engineer (LLM / Chatbot / RAG)** — Hyd, 6–11 Yrs. Chips: LLM, Python, MLOps, Langchain, Langgraph, LLMOps, Aiml. https://www.naukri.com/job-listings-ai-engineer-llm-chatbot-rag-qentelli-hyderabad-6-to-11-years-210826008255

**JD48 Tekskills (client)** — Gen AI / Generative AI Engineer, 4–8 / 6–11, BLR/Hyd. “We are looking for a Generative AI Developer with strong hands-on experience in LLMs, R…” chips include mlops, python. Staffing intermediary.

**JD49 Ecolab Lead AI Engineer** — Bengaluru. Employer page https://jobs.ecolab.com/global/en/job/R00295717/Lead-AI-Engineer **“The job you’re looking for is no longer available”** (23 Aug). Naukri still lists 8–10 Yrs (`190826924117`) and 2–6 Yrs (`170826920749`) with chips **Servicenow**, large language models, workflows. Recruit.net cache: “you will own the architecture and delivery of GenAI-based systems that integrate large language models (LLMs), multi-agent workflows”. **Careers expired; do not treat as apply-now.**

**JD50 Infosys Agentic AI / AI Engineer Pan-India** — multiple 3–5 Yrs hybrid reqs (Hyd/Chennai/BLR, NCR, Mumbai, Pune, Ahmedabad). Chips: generative ai, Agentic Ai, RAG, LLM, Python. Existence verified; bodies not fully captured.

**Instahyre existence-only (no body — JS wall):**  
- Xponentium GEN AI Engineer Bangalore 5–7 YOE, LangGraph/LangChain/AutoGen/CrewAI — https://www.instahyre.com/job-437639-gen-ai-engineer-at-xponentium-india-bangalore/  
- Pierian Services Gen AI & Agentic Sys Engineer **Chennai** — “Design and build Retrieval-Augmented Generation (RAG) pipelines. Develop AI agents … LangChain / LangGraph” — https://www.instahyre.com/job-432570-gen-ai-agentic-sys-engineer-at-pierian-services-chennai/  
- Infosys Sr. Gen AI Engineer BLR/Chennai/Hyd — “agentic AI systems, RAG pipelines, and MCP-based” — https://www.instahyre.com/job-421869-sr-gen-ai-engineer-at-infosys-4-bangalore-chennai-hyderabad/  
- MOURI Tech GEN AI Engineer Bangalore 5–8 — “Implement and optimize RAG pipelines using LangChain”  
**These are not counted in the frequency table as full JDs.** MCP on Infosys Instahyre snippet is noted under evidence gaps as **unverified full JD**.

---

## Skill frequency table

**Denominator:** 37 JDs with enough requirement text to code skills (JD01–JD31, JD35–JD37). PARTIAL chips-only rows are **excluded** from % to avoid double-counting Naukri keyword spam. N = 37.

| Skill / concept | Count | % of 37 | Notes (VERIFIED FACT pattern) |
|---|---:|---:|---|
| Python | 33 | 89% | Almost universal. Exceptions: JD07 (Accenture keywords only), JD17 (TypeScript/Node primary), JD36 (JavaScript primary; Python “plus”). |
| RAG / retrieval / embeddings / chunking | 28 | 76% | Dominant architecture word. |
| Agents / Agentic / multi-agent / tool-calling | 32 | 86% | “Agentic” is the 2026 title fashion; quality varies from Accenture three-word must-have to Zealant/BNP production bars. |
| LangChain | 22 | 59% | Still the default framework named. |
| LangGraph | 18 | 49% | Now co-equal with LangChain on better JDs. |
| Vector DB (Pinecone/FAISS/Weaviate/Chroma/Milvus/Azure AI Search/pgvector) | 16 | 43% | Named stores cluster on product/staffing JDs. |
| Prompt engineering | 20 | 54% | |
| Azure OpenAI / Azure AI Foundry / Azure ML | 14 | 38% | Services + Hitachi + ApTask + EY + Capgemini + Deloitte. |
| AWS Bedrock and/or AWS generally | 12 | 32% | Infosys JD01, NXP, Smart Working, StackNexus, UST, ADP chips. |
| CI/CD (GitHub Actions, Jenkins, GitLab, Azure DevOps) | 18 | 49% | |
| Docker | 14 | 38% | |
| Kubernetes / AKS | 12 | 32% | Heavier on MLOps/AIOps/platform JDs. |
| Guardrails / Responsible AI / prompt injection | 12 | 32% | Infosys, Hitachi, Zealant, ApTask, BNP, Smart Working, EY. |
| Evaluation / LLM-as-judge / LangSmith / Langfuse / Ragas / Phoenix | 14 | 38% | **Discriminating skill** on better JDs (Deloitte, EY, Hitachi, Smart Working, Google, BNP, Zealant). |
| OpenAI API / GPT (explicit) | 12 | 32% | Often implied via Azure OpenAI. |
| LlamaIndex | 5 | 14% | Deloitte, MyAdvice, StackNexus, Hitachi, Infosys LLMOps. |
| CrewAI / AutoGen | 10 | 27% | |
| MCP (Model Context Protocol) | 5 | 14% | Hitachi, Smart Working (NTH), BNP, Convera, Google FDE. **Rising, not yet majority.** |
| Semantic Kernel / Microsoft Agent Framework | 4 | 11% | Hitachi, Ascendion, Capgemini/Foundry family. |
| HuggingFace / Transformers | 5 | 14% | TCS GTH, MyAdvice, StackNexus, Hitachi, Infosys JD03. |
| Fine-tuning / LoRA / QLoRA | 8 | 22% | Infosys JD02/JD03/JD04, NXP, MyAdvice, ApTask, Qualys, Hitachi (optional optimize). |
| MLOps / LLMOps named | 14 | 38% | |
| Vertex AI / GCP | 8 | 22% | Persistent AI OPS, IRIS, Google, StackNexus, MyAdvice, Cognizant, Qualys GTH. |
| ServiceNow / ITSM | 6 | 16% | HPE, Hitachi, Allianz, HP, Convera, EY NTH. **Sparse but high-signal for the user.** |
| Observability (Grafana, Prometheus, Dynatrace, ELK, OTel) | 8 | 22% | HPE, Allianz, BNP, Qualys, Hitachi (eval tools), IRIS, Smart Working, Cognizant. |
| ITIL | 3 | 8% | HPE, Allianz NTH, PwC chip (JD38, outside N if strict). Count 2 in N=37 (HPE, Allianz). |
| Terraform / IaC | 5 | 14% | Persistent AI OPS, Cognizant, Wissen partial, IRIS, Hitachi platform. |
| FastAPI / microservices / REST | 16 | 43% | |
| Splunk | 0 | 0% | **Not in any full-body JD in this harvest.** |
| Datadog | 0 | 0% | **Not named.** |
| PagerDuty | 0 | 0% | **Not named.** |
| Degree (CS/Eng named) | 14 | 38% | Many services JDs omit it; Google/Hitachi/HP/Capgemini/Deloitte/NXP/Allianz-adjacent require or prefer. Accenture uses “15 years full time education”. |

**ATS keyword gravity (what actually repeats):** `Python`, `RAG`, `LangChain`, `LangGraph`, `Agentic`, `LLM`, `Azure OpenAI`/`Bedrock`, `vector`, `prompt`, `CI/CD`, `Docker`. **Secondary differentiators on better roles:** `LangSmith`/`Langfuse`/`eval`, `guardrails`, `MCP`, `ServiceNow`, `Terraform`, `K8s`.

---

## Java/SQL prevalence (cost of avoiding them)

Coded on the same N=37 full-body JDs.

| Signal | Count | % | JDs |
|---|---:|---:|---|
| **Java named as required or co-equal language** | 4 | 11% | JD08 Capgemini (“.NET, Java, or Python”); JD13 HPE (“Python, Java, Selenium”); JD14 NXP (“Python, Java, Node.JS, React.js”); JD35 HP knowledge-dump includes Java (Required Skills say Python). |
| **Java advantage / optional** | 1 | 3% | JD16 Hitachi (“Java or C#/.NET is an advantage”). |
| **Java not mentioned** | 32 | 86% | Majority of GenAI/agentic JDs. |
| **SQL / DBMS / Postgres / SQL tools required or co-equal** | 8 | 22% | JD14 NXP (2+ yrs DBMS); JD16 Hitachi (“SQL is required”); JD17 Smart Working (Postgres); JD20 Hired (“Python and SQL”); JD22 Cirruslabs (“SQL tools”); JD26 Allianz (sql/nosql in tools); JD29 ApTask (SQL/NoSQL); JD19 “databases” not counted as SQL. |
| **Neither Java nor SQL named** | 25 | 68% | Includes Infosys JD01/02/04, TCS JD05/06, Accenture JD07, Deloitte JD09, Persistent JD11/12, MyAdvice, Ascendion, 360DigiTMG, Stamford, Cognizant MLOps, Zealant, UST, BNP, Google FDE, HP required-skills block, Convera (JS not Java). |

### Filter-cost interpretation (VERIFIED FACT arithmetic, not opinion dressed as data)

- **Avoiding Java as a primary skill excludes ~11% of this corpus** if “Java listed at all as a language” is a hard reject. If the user will still apply when Java is **one of three** (Capgemini) or **Workday noise** (HP), exclusion drops to **NXP + HPE** ≈ **5%**.  
- **Avoiding SQL as a named skill excludes ~22%.** The painful misses are **Hitachi Energy (SQL required)** and **Smart Working (Postgres)** — both otherwise excellent agent/RAG/eval JDs — plus Hired (closed) and ApTask.  
- **Joint avoid Java-first AND SQL-first:** still **~68% of full-body JDs do not name either**. The market the user wants (Python + RAG + agents + LLMOps) is **majority Python-first** in this harvest.  
- **Exception that matters for the user’s past:** **Convera ITSM** wants **JavaScript**, not Java/SQL. Python is plus. A Python-only resume can fail that ATS even though it is the best ITSM-adjacent role.  
- Naukri volume pages still mix `sql` into generic GenAI cards (e.g. a 5–8 Yrs Noida/Pune/Gurugram GenAI card with numpy/microservices/**sql**). Those kitchen-sink cards are **not** in the 37 but they inflate SERP noise.

---

## Adjacent vs core-AI JD split

**Definition used here (operational, not marketing):**  
- **Adjacent:** First-screen plausible for a Service Desk Lead / IT Ops person who built a **strong GenAI/AIOps portfolio** (Python or JS automation, RAG, agents, ITSM/observability, CI/CD) **without** years of model training/research.  
- **Core:** JD text requires training/fine-tuning as a primary duty, PyTorch/CUDA/GPU hardware, or “X years AI/ML development” as the experience clock.

| Bucket | JDs | First-screen note |
|---|---|---|
| **Adjacent — apply with portfolio** | JD01 Infosys Bedrock/RAG/LangGraph; JD04 Infosys LLMOps (“NOT a data scientist”); JD06 TCS Agentic Architect (8–12 IT + 3 GenAI); JD07 Accenture LLM Ops; JD09 Deloitte LangChain/eval; JD10 EY 10+ IT + Azure agents; JD12 Persistent AI OPS (GCP ADK); JD13 HPE ITIL/SNOW/RAG; JD16 Hitachi CSS/SNOW (SQL hurdle); JD22 Cirruslabs; JD23 360DigiTMG; JD26 Allianz SNOW/SRE (expired); JD30 BNP IT-ops assistants; JD35 HP SNOW/JIRA/RPA; JD36 Convera ITSM (JS hurdle); JD45 Wissen SRE+AI (partial, 15–25 LPA) | Resume must **quote the JD’s framework names**. Ops stories (incident, CMDB, ServiceNow) map to JD13/16/26/30/36. |
| **Adjacent — but production-agent bar is high** | JD02 Infosys (LoRA “basic”); JD17 Smart Working (2y prod agents + Langfuse); JD21 Ascendion; JD24 Stamford 10–18; JD28 Zealant (“not just chatbots”); JD31 UST; JD37 Google FDE | Weekend RAG will not pass. Need traces, eval sets, failure modes. |
| **Mixed / kitchen sink** | JD08 Capgemini (Java/.NET/Python); JD11 Persistent (ML background + agents); JD14 NXP (Java+DBMS+fine-tune); JD19 StackNexus (PyTorch+RAG); JD29 ApTask (LoRA+RAG+MLOps); JD34 Altimetrik (TF/BERT+RAG) | Apply only if the **primary** story matches one cluster. |
| **Core ML / training / GPU** | JD03 Infosys 3–5 AI/ML YOE + LoRA; JD15 Qualys PyTorch/CUDA/H100; JD25 Cognizant Kubeflow/drift (expired); JD18 MyAdvice fine-tune as essential duty (junior) | Do **not** first-screen without ML training evidence. |
| **Under-levelled / title inflation** | JD05 TCS 5–8 LPA est. + “eagerness to learn Agentic AI”; JD18 12–15 LPA for 1–3 YOE | Compensation/YOE mismatch for 8.5 YOE. |

**Headline:** For this harvest, **adjacent outnumbers core**. The 2026 India GenAI IC market as sampled is **application/agent/RAG/LLMOps engineering**, with a minority of true training roles. The catch: adjacent JDs still want **coded artefacts** (LangGraph, eval, CI/CD), not “used ChatGPT in the service desk”.

---

## Services vs product/GCC

| Segment | JDs in inventory | What the JD language does |
|---|---|---|
| **Indian services (TCS, Infosys, Wipro n/a, HCL, TechM, Cognizant, Capgemini, Accenture, Persistent, UST, Altimetrik, DXC, Qentelli)** | JD01–JD12, JD25, JD31–JD34, JD43–JD44, JD47–JD50 | High volume, cloned must-haves (`Python + RAG + LangChain + Agentic`), LinkedIn seniority chips wrong, **YOE often “overall IT”**. Accenture/TCS education templates. Walk-ins (ADP, Persistent past, Blackstraw). |
| **Big-4 / consulting (Deloitte, EY, PwC, KPMG n/a)** | JD09, JD10, JD38–JD40 | Longer, more eval/observability/governance. EY wants **10+ global IT + Azure Foundry + LLM-as-judge**. PwC Senior Associate **filled**. |
| **GCCs / banks / insurers** | JD16 Hitachi, JD26 Allianz, JD30 BNP, JD41 ADP | **Best overlap with IT ops** (ServiceNow, CMDB, incident RCA, CSS automation). BNP is explicit: “production assistants on real infra datasets: incident investigation, RCA, change analysis, CMDB querying”. |
| **Product / semiconductor / SaaS / Google** | JD13 HPE, JD14 NXP, JD15 Qualys, JD17 Smart Working, JD18 MyAdvice, JD35 HP, JD36 Convera, JD37 Google | Fewer posts captured with full text. Google FDE is **8 years cloud/customer-facing + RAG + agents**. Qualys is core MLOps. Convera is ITSM product. **Microsoft, Amazon, ServiceNow, Freshworks, Zoho, Adobe, Salesforce, Oracle, Thoughtworks, Fractal, Tiger Analytics: no full IC JD body in this harvest.** |
| **Staffing / contract** | JD19 StackNexus, JD20 Hired, JD21 Ascendion, JD28 Zealant, JD29 ApTask, JD46 ACS, JD48 Tekskills | US hours, kitchen-sink LoRA+RAG, disclosed 20–27.5 LPA (ACS). Quality variance extreme. |

**Services vs product skill difference in this corpus:** services name **LangChain/LangGraph/RAG** and stop; product/GCC add **eval, tracing, MCP, ServiceNow, FinOps, ITIL**. Compensation signal: disclosed **15–25 LPA** (Wissen SRE AI), **20–27.5 LPA** (ACS Agentic 8–13), **12–15 LPA** (MyAdvice 1–3 YOE). TCS/Infosys Glassdoor estimates **5–10 LPA** on similarly titled roles — **do not treat estimates as offers**.

---

## Location notes (Coimbatore / Chennai / Tamil Nadu / remote)

### Chennai / Tamil Nadu (VERIFIED FACT)

| JD | Evidence |
|---|---|
| JD06 TCS Agentic 8–12 | Location string “Hyderabad, Chennai, Bengaluru”. |
| JD24 Stamford/Infinity 10–18 | Hybrid “Hyderabad, Chennai, Bengaluru”. |
| JD34 Altimetrik 5–10 | Hybrid Hyd, Chennai, Bengaluru. |
| JD42 Blackstraw.ai walk-in | **Chennai WFO**, walk-in 24 Aug 2026, 2–6 Yrs, RAG + Agentic + Computer Vision. |
| JD43 DXC | Locations include Chennai. |
| JD44 Cognizant AI Engineer | Hybrid BLR, Pune, **Chennai**, 6–11 Yrs. |
| JD50 Infosys Agentic 3–5 | Hybrid Hyd, **Chennai**, BLR. |
| Instahyre Pierian Services | **Chennai** Gen AI & Agentic Sys Engineer — body not fully captured; snippet has RAG + LangChain/LangGraph. |
| Freshworks | HQ/large office Chennai exists; **no GenAI IC JD body captured**. Staff Full Stack mentions Copilot fluency only. |

### Coimbatore

**Insufficient reliable full JD evidence.** Naukri AIOps SERP card: “AIOps Engineer … Hybrid - Pune, Coimbatore, Bengaluru … 3–5 Yrs … 8–15 Lacs PA … Servicenow · Cloud Monitoring · AIOps · Azure” attributed to **EY 3.4**. That is a **SERP card**, not a retrieved JD body. No Coimbatore GenAI Engineer full extract in this harvest.

### Remote / Hybrid India (full-body)

- JD17 Smart Working — **remote**, Hyd-tagged, US-evening IST shift.  
- JD18 MyAdvice — remote-first, may recall to Bangalore; **11pm–8am IST**.  
- JD19 StackNexus — remote, **US working hours**, contract.  
- JD20 Hired — remote anywhere (closed).  
- JD13 HPE — **hybrid 2 days/week Bengaluru**.  
- JD22 Cirruslabs — Hybrid Hyd/BLR.  
- JD01/JD10/JD16/JD30/JD37 — office/hybrid Bengaluru (Google allows Mumbai/Pune/BLR).  
- JD36 Convera — Pune (mode not explicitly remote).  
- JD26 Allianz — **Pune onsite**.

**Practical note:** “Remote India” GenAI JDs in this harvest often mean **US-timezone**. Night-shift is a hidden requirement (MyAdvice, Smart Working, StackNexus).

---

## Screening-bar analysis (what ATS/keywords actually appear)

### Pattern A — Services clone (highest volume)

Must-have string looks like Infosys JD01 / Persistent JD11 / Stamford JD24: **Python + LLM vendor list + RAG + LangChain/LangGraph + CrewAI/AutoGen + vector DB**. Experience clock is **overall SWE/IT**, plus “hands-on GenAI”.  

**ATS tokens to put in a resume (verbatim from JDs):** `LangChain`, `LangGraph`, `RAG`, `embeddings`, `chunking`, `vector`, `Bedrock` or `Azure OpenAI`, `guardrails`, `CI/CD`, `Docker`, `agent workflows`, `LangSmith`/`evaluation`.

### Pattern B — LLMOps / platform

Infosys JD04, Cognizant JD25, IRIS JD27, Qualys JD15, Persistent JD12: `MLflow`, `Kubeflow`, `SageMaker`/`Vertex`/`Azure ML`, `Kubernetes`, `drift`, `inference pipelines`. Infosys JD04 explicitly **rejects** “Traditional MLOps without LLM exposure”.

### Pattern C — AIOps / ITSM / support copilot (user’s wedge)

Convera JD36, HPE JD13, Allianz JD26, BNP JD30, Hitachi JD16, HP JD35: `ServiceNow`, `ITIL`, `incident`, `CMDB`, `self-service`, `HITL`, `MCP`, `Grafana`/`Dynatrace`/`Prometheus`, `RCA`. **These tokens are rare in the 37 (ServiceNow 16%) but they are the ones that make an ops background a feature.** Splunk/Datadog/PagerDuty **did not appear** in full bodies — do not assume they are ATS-critical for GenAI titles in this sample.

### Pattern D — Eval / observability as the senior bar

Deloitte (Arize Phoenix, LangSmith), EY (LLM-as-a-Judge), Hitachi (LangSmith, Langfuse, Ragas, promptfoo), Smart Working (Langfuse, trajectory eval), Google (eval pipelines), BNP (LangSmith), Zealant (evaluation harnesses). **If targeting 8.5 YOE / 20+ LPA, eval+tracing is the keyword gap** versus a basic RAG demo.

### Pattern E — “8+ years AI” vs “8+ years IT + AI skills”

| Wording | Examples |
|---|---|
| **Overall SWE/IT + GenAI hands-on** (majority) | Ascendion “5–12 years of overall software engineering”; TCS JD06 “8–12” + “Minimum 3+ years in Generative AI or AI Architecture”; EY “10+ years in a Global IT environment” + 3 years ops; HPE production/ITIL owner; Google “8 years … cloud computing or a technical customer-facing role”; IRIS 8–9 years Python/GCP/LangGraph. |
| **Years in AI/ML as the clock** | Infosys JD03 “3 5 years of professional experience in AI ML development”; Qualys “2–3 years … ML products”; Accenture “3 years … in Large Language Models”; UST “3-5 years in Machine Learning, AI”. |
| **Split clock (best for switchers)** | Smart Working “5+ years backend” + “2+ years production LLM agents”; BNP “5+ DevOps/AI/ML” + “2+ years on LLM-based agentic systems in production”; Hitachi “5–10 years in software engineering, AI engineering, machine learning, or related”. |

**No JD in the full-body set said “8+ years of AI research” as a hard gate.** Google prefers Master’s/PhD but minimum is 8 years cloud/customer-facing + RAG production.

### Pattern F — Notice period / hybrid

Cognizant JD25: **Immediate to 90 days** (expired). Naukri senior GenAI cards in SERP noise included “Notice Period: Immediate to 20 days ONLY” (Senior Generative AI Engineer 5–8 Yrs 17–32 LPA Hybrid Bangalore) — that specific listing was **not** fully extracted. Hybrid is default for services; GCCs mixed; Allianz onsite Pune.

---

## Red-flag JDs

| Flag | Evidence |
|---|---|
| **Kitchen-sink title, junior pay** | JD05 TCS GEN AI Engineer: Agentic AI + LangGraph GTH + Python fundamentals; Glassdoor **₹5–8L est.** |
| **Kitchen-sink skills, thin JD** | JD07 Accenture: must-haves only “LLMs, Generative AI, Agentic AI” + “15 years full time education”. |
| **YOE band vs skill list mismatch** | JD04 Infosys LLMOps posted **2–3 Yrs** with LangGraph + production RAG + “what this role is NOT”. |
| **Java + GenAI same-week factory** | Blackstraw Chennai walk-in GenAI **and** Java Fullstack Immediate Joiner. |
| **US-hours contract, stale** | JD19 StackNexus 4 months old, US hours, +5 years, PyTorch+RAG+K8s. |
| **Closed / 404 while SERP still ranks** | Hired JD20 closed; Cognizant careers 404; Ecolab R00295717 gone; PwC AC filled; Naukri listing URLs expire while Google still quotes them. |
| **Low LPA AIOps** | Naukri card “DevOps (MLOps+AIOps) Engineer … Profex Tech … 8.5-9.5 Lacs PA … 2-7 Yrs” — not fully extracted; flagged as **volume-market junk** if real. |
| **UNIS LinkedIn similar-jobs chip** | “Agentic AI Engineer … $2,240.00 $3,440.00” on UNIS India cards seen adjacent to live JDs — contractor/monthly-looking numbers; **not extracted as a primary JD** (risk of mis-scraped currency). |
| **Walk-in for experienced titles** | ADP 25 Aug Hyd; Blackstraw 24 Aug Chennai; Persistent 9 May 2026 (already past). Walk-ins are a services-firm process, not automatically a scam, but they correlate with cloned JDs. |

**Unpaid “AI intern” for experienced people:** not captured as a live JD in this harvest. Insufficient evidence to claim it is common on these boards in Aug 2026.

---

## Evidence gaps

1. **Naukri anti-bot + listing expiry** prevented 35–50 **click-through full HTML** JDs from Naukri itself. Volume is real; many individual URLs die within days. Google snippets were used and labelled.  
2. **Instahyre / Cutshort / Foundit** full bodies largely inaccessible (JS or fetch fail). Cutshort = **zero**.  
3. **Product/GCC holes:** Microsoft India, Amazon, ServiceNow (as employer), Freshworks Freddy/ML, Zoho, Adobe, Salesforce, Oracle, Thoughtworks, Fractal, Tiger Analytics, Publicis Sapient — **no full GenAI IC JD** in this pass. Google Cloud FDE **was** captured. Freshworks careers page is brand, not a JD.  
4. **Coimbatore:** only an EY AIOps SERP card, no body.  
5. **Wipro / KPMG / LTIMindtree / Mphasis** named in the task list — **not captured**.  
6. **Splunk / Datadog / PagerDuty** did not appear in full-body JDs; absence may be harvest bias (ITSM roles may live under “ServiceNow”/“SRE” titles, not “GenAI Engineer”).  
7. **Salary:** employer-disclosed figures are scarce (MyAdvice 12–15 LPA; Wissen 15–25 LPA; ACS 20–27.5 LPA; Naukri walk-in/staffing bands). Glassdoor 5–10 LPA on TCS/Infosys are **estimates**.  
8. **LinkedIn seniority chips** are unreliable (Infosys “Entry level” vs Naukri 6–11).  
9. **MCP** is present on Hitachi, BNP, Convera, Google, Smart Working NTH, and an Instahyre Infosys snippet — too few full JDs to treat MCP as majority ATS.  
10. Target was 35–50 JDs: **50 inventory rows**, **37 full-body extracts**. Remaining rows are honest PARTIAL/EXPIRED. **Insufficient reliable evidence** for a Coimbatore-specific GenAI market and for Microsoft/ServiceNow/Freshworks/Zoho product IC JDs.

---

## Source appendix

| # | URL | Used for |
|---|---|---|
| 1 | https://www.naukri.com/generative-ai-engineer-jobs | Volume 11,132 (Aug 2026) |
| 2 | https://www.naukri.com/genai-engineer-jobs | Volume 7,709; location/salary facets |
| 3 | https://www.naukri.com/gen-ai-jobs | Volume 28,853 |
| 4 | https://www.naukri.com/llmops-jobs | Volume 772–877 |
| 5 | https://www.naukri.com/aiops-jobs | Volume 558 |
| 6 | https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669 | JD01 |
| 7 | https://www.naukri.com/job-listings-genai-agentic-ai-engineer-infosys-limited-bengaluru-6-to-11-years-100726919193 | JD01 twin YOE |
| 8 | https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-infosys-4441390349 | JD02 |
| 9 | https://www.glassdoor.co.in/job-listing/gen-ai-engineer-infosys-JV_IC2940587_KO0,15_KE16,23.htm?jl=1010089163801 | JD03 |
| 10 | https://www.naukri.com/job-listings-gen-ai-llmops-engineer-infosys-limited-bengaluru-2-to-3-years-040826909325 | JD04 |
| 11 | https://www.glassdoor.co.in/job-listing/gen-ai-engineer-tata-consultancy-services-JV_IC2940587_KO0,15_KE16,41.htm?jl=1009966161130 | JD05 |
| 12 | https://www.naukri.com/job-listings-agentic-ai-engineer-tata-consultancy-services-hyderabad-chennai-bengaluru-8-to-12-years-130826027970 | JD06 |
| 13 | https://in.linkedin.com/jobs/view/llm-operations-engineer-at-accenture-in-india-4456383755 | JD07 |
| 14 | https://in.linkedin.com/jobs/view/agentic-with-azure-aifoundry-at-capgemini-4437769635 | JD08 |
| 15 | https://usijobs.deloitte.com/en_US/careersUSI/JobDetail/USI-EH27-MFBEL-GEN-AI-ENGINEER-L40-HYD-BLR/353050 | JD09 |
| 16 | https://in.linkedin.com/jobs/view/ai-engineer-agentic-ai-orchestration-and-azure-ai-foundry-full%E2%80%91stack-azure%E2%80%91native-at-ey-4432756779 | JD10 |
| 17 | https://www.naukri.com/job-listings-agentic-ai-engineer-persistent-hyderabad-bengaluru-5-to-10-years-050526015522 | JD11 |
| 18 | https://in.linkedin.com/jobs/view/senior-ai-ops-engineer-at-persistent-systems-4453886301 | JD12 |
| 19 | https://in.linkedin.com/jobs/view/devops-mlops-genai-platform-owner-ic-at-hewlett-packard-enterprise-4450233534 | JD13 |
| 20 | https://in.linkedin.com/jobs/view/software-devops-engineer-for-gen-ai-at-nxp-semiconductors-4390640553 | JD14 |
| 21 | https://in.linkedin.com/jobs/view/machine-learning-operations-engineer-at-qualys-4417876201 | JD15 |
| 22 | https://in.linkedin.com/jobs/view/ai-automation-engineer-at-hitachi-energy-4455774089 | JD16 |
| 23 | https://in.linkedin.com/jobs/view/llm-systems-ai-agent-engineer-remote-full-time-as311-at-smart-working-4452583680 | JD17 |
| 24 | https://in.linkedin.com/jobs/view/ai-engineer-l-generative-ai-at-myadvice-4430414644 | JD18 |
| 25 | https://in.linkedin.com/jobs/view/gen-ai-engineer-at-stacknexus-4403195999 | JD19 |
| 26 | https://in.linkedin.com/jobs/view/ai-engineer-generative-ai-remote-at-hired-4446713048 | JD20 |
| 27 | https://in.linkedin.com/jobs/view/genai-hiring-drive-2026-lead-generative-ai-engineer-5–12-years-at-ascendion-4428493435 | JD21 (expired redirect) |
| 28 | https://www.naukri.com/job-listings-ai-engineer-agentic-workflows-langgraph-langchain-rag-pipelines-cirruslabs-hyderabad-bengaluru-3-to-8-years-171225015734 | JD22 |
| 29 | https://www.naukri.com/job-listings-genai-engineer-agentic-ai-rag-360digitmg-bengaluru-4-to-8-years-070426500532 | JD23 |
| 30 | https://www.naukri.com/job-listings-genai-agentic-ai-engineer-stamford-technology-hyderabad-chennai-bengaluru-10-to-18-years-090126021616 | JD24 |
| 31 | https://careers.cognizant.com/global-en/jobs/00068075121/ai-ops-integrationapi-engineer-with-mlops-ai-ml-developer/ | JD25 (404) |
| 32 | https://www.grapevine.in/tal/jobs/21d24a2a-1753-44e4-9afb-760f3f23ecb6 | JD26 |
| 33 | https://www.foundit.in/job/mlops-aiops-gcp-lead-iris-software-noida-54024539 | JD27 |
| 34 | https://in.linkedin.com/jobs/view/ai-engineer-agentic-ai-development-at-zealant-consulting-group-4439984153 | JD28 |
| 35 | https://in.linkedin.com/jobs/view/agentic-ai-engineer-%E2%80%93-azure-llm-rag-langgraph-at-aptask-4452561905 | JD29 |
| 36 | https://in.linkedin.com/jobs/view/agentic-ai-devops-at-bnp-paribas-4448761124 | JD30 |
| 37 | https://in.linkedin.com/jobs/view/ai-engineer-at-ust-4441090818 | JD31 |
| 38 | https://www.naukri.com/job-listings-agentic-ai-engineer-tech-mahindra-pune-bengaluru-5-to-10-years-190826025169 | JD32 |
| 39 | https://www.naukri.com/job-listings-agentic-ai-engineer-hcltech-noida-hyderabad-bengaluru-4-to-9-years-140826022057 | JD33 |
| 40 | https://www.naukri.com/job-listings-gen-ai-engineer-altimetrik-hyderabad-chennai-bengaluru-5-to-10-years-200826016294 | JD34 |
| 41 | https://in.linkedin.com/jobs/view/ai-and-automation-developer-at-hp-4449084177 | JD35 |
| 42 | https://in.linkedin.com/jobs/view/agentic-ai-engineer-itsm-enterprise-automation-at-convera-4455712445 | JD36 |
| 43 | https://in.linkedin.com/jobs/view/generative-ai-forward-deployed-engineer-google-cloud-at-google-4451133303 | JD37 |
| 44 | https://jobs-ta.pwc.com/global/en/job/724190WD/Gen-AI-Engineer-Senior-Associate | JD40 filled |
| 45 | https://jobs.ecolab.com/global/en/job/R00295717/Lead-AI-Engineer | JD49 expired |
| 46 | https://www.naukri.com/job-listings-sre-ai-engineer-wissen-technology-pune-bengaluru-mumbai-all-areas-5-to-9-years-210826004877 | JD45 |
| 47 | https://www.naukri.com/job-listings-agentic-ai-engineer-advance-career-solutions-hyderabad-pune-bengaluru-8-to-13-years-210826009123 | JD46 |
| 48 | https://www.naukri.com/job-listings-gen-ai-engineer-adp-private-limited-hyderabad-3-to-8-years-220826011986 | JD41 |
| 49 | https://www.instahyre.com/job-432570-gen-ai-agentic-sys-engineer-at-pierian-services-chennai/ | Chennai existence |
| 50 | https://www.freshworks.com/company/careers/ | No IC GenAI JD |

**Harvest complete. Access date 2026-08-23. Do not treat expired URLs as currently applyable.**
