# AI Career Transition — Research Summary Report (everything harvested so far)

**Subject:** Manoj Kumar, Madukkarai / Coimbatore, Tamil Nadu  
**Current identity (honest):** Service Desk Lead / IT Operations / Enterprise Support, Cognizant, T-Mobile account  
**Tenure:** ~8.5 years **IT** — not 8.5 years AI  
**Last CTC:** ~₹11 LPA  
**Goal:** Full transition into applied AI engineering (GenAI / Agentic / LLM / AIOps / AI Automation)  
**Constraints:** No fabricated AI YOE. Not a fresher reset. Not Java-first or SQL-first. India metros + Coimbatore + Remote India.  
**Research window:** 16–24 August 2026  
**This file:** One-sitting consolidation of **all datasets produced so far**. It does not replace the machine-readable JD corpus (`research/jd-raw/MASTER-india-ai-jd-corpus.tsv`, N=455).

**Evidence labels used throughout**

| Label | Meaning |
|---|---|
| **VERIFIED FACT** | Quoted or tightly extracted from a retrieved page, dated index snippet, or named aggregator with n |
| **COMMUNITY EXPERIENCE** | Reddit / Glassdoor / YouTube / institute testimonial — signal, not census |
| **INFERENCE** | Pattern from multiple facts; not a guarantee |
| **RECOMMENDATION** | Action for this profile |
| **Insufficient reliable evidence (N=X)** | Claim would need more independent sources than found |

---

## 0. What was completed vs what was not

### Completed (on disk)

| Workstream | File | What it contains |
|---|---|---|
| Parent sources | `research/A0-parent-primary-sources.md` | Primary URLs, GCC, Coimbatore, Quess, upGrad |
| Job market | `research/A1-job-market.md` | Naukri keyword vs occupation hygiene |
| Salary | `research/A2-salary.md` | AmbitionBox / Glassdoor / Levels.fyi / disclosed JD bands |
| JD qualitative | `research/A3-jd-corpus.md` | 50 JDs / 37 full-body coded |
| Role map | `research/A4-role-map.md` | H1/H2/H3, ATS headlines, avoid list |
| Interviews | `research/A5-interviews.md` | N=72 sourced questions; DSA vs no-DSA |
| Switchers | `research/A6-transitions.md` | N=0 verified SD-Lead→external AI Engineer CTC |
| Skills / portfolio / certs | `research/A7-skills-portfolio.md` | Blocking skills, 6 project specs, cert ROI |
| Geo / hybrid / COL | `research/A8-geo-community.md` | City shares, Numbeo, GCC, Coimbatore |
| Wave-1 scoring | `research/W1-A1-role-fit-scoring.md` | 22 roles, 7-criterion 0–100 scores |
| Wave-1 JD mining | `research/W1-A2-jd-mining.md` | 85 inventory rows; N=52 full-body coded |
| Unique JD corpus | `research/jd-raw/MASTER-india-ai-jd-corpus.tsv` + `.csv` | **N=455 unique listings** |
| Skill freq on corpus | `research/jd-raw/SKILL-FREQ.json` | Frequency + co-occurrence on those 455 snippets |
| Long original synthesis | `AI-CAREER-TRANSITION-INTELLIGENCE-REPORT-2026.md` | 18-section first synthesis (pre-Wave-1 lock) |

### Not completed (interrupted Wave-2 / Wave-3 extras)

These were requested later and **were not fully rebuilt as separate agent dossiers**. This summary **does** compute skill frequency on the 455 corpus and restates interview/portfolio/cert findings from A5–A7. It does **not** invent a fake “Top 100 companies scored 0–100” or “Top 100 interview questions” beyond what A5 actually sourced (N=72 verified).

| Requested extra | Status |
|---|---|
| Top 100 must-prepare questions | **Partial** — A5 has **72 sourced** questions; rest would be SECONDARY blog themes |
| Top 30 system-design scenarios as a numbered list | **Partial** — themes exist in A5/A7; not a new 30-row scored table |
| Top 100 companies Tier 1–4 scored | **Partial** — company counts from corpus + A4 target list; no 100-row scorecard |
| Wave-2 Pattern Discovery (STOP-LEARNING list as a separate agent) | **This document’s §7 / §16** is the synthesis from existing data |
| LinkedIn miner TSV (fifth harvest agent) | **Cancelled mid-run**; LinkedIn still **94/455** of unique URLs via other harvests |

---

## PART 1 — Executive decision

**PRIMARY (H1, 0–6 months):** AIOps Engineer / AI Operations Engineer — **score 73**  
**SECONDARY (H1):** Copilot Studio / Copilot for Service — **score 70**  
**BACKUP wedge (H1):** TMUS-style AI Support / AI Agent Operations — **score 68**  
**Not Primary:** Cloud AI Engineer (Azure OpenAI / Bedrock) — **score 56** (demand is real; transferability and competition fail this CV)

**Single strategy (RECOMMENDATION):** Run two tracks in parallel for 90 days.

- **Track A (cashflow + relevant months):** Internal / account-internal move into AIOps, Copilot Studio / Now Assist, Cognizant IOA / Frontier operator-builder, or TMUS Hyderabad Engineer, AI (Support/Operations). These JDs treat 8.5 years of incident/ITSM as a **qualification**.
- **Track B (identity change):** Ship two public, eval-gated artefacts on **synthetic** IT-operations data (incident RAG + HITL runbook agent) in Python / FastAPI / Azure OpenAI or Bedrock / LangGraph. At day 60–90 apply to services/GCC GenAI as **8.5 years enterprise operations + N months relevant GenAI** — the formula Cognizant/Infosys already print.

**Do not:** reset as junior GenAI IC at TCS/Infosys ₹6–10 L; lead with Java or SQL; wait 18 months for Service Desk Lead to become AI Engineer; write “GenAI Engineer, 8.5 years.”

**N=0 independently verified Service Desk Lead → external AI Engineer offer with CTC** in this window (A6). Closest analogue: **Surender Arumugam**, 18+ YOE Cognizant Chennai, **internal** mainframes → Senior GenAI Manager after night projects. **COMMERCIAL TESTIMONIAL + named video.**

---

## PART 2 — Top 3 target roles (locked after Wave-1 re-score)

Scoring formula (non-negotiable):

```
TOTAL = 0.25*Demand + 0.20*Transferability + 0.15*Salary
      + 0.15*Growth + 0.10*LearningEase + 0.10*LowCompetition
      + 0.05*RemoteGeo
```

### League table (all 22 scored roles)

| Rank | Role | Score | Horizon | Shortlist now (this CV) |
|---|---|---:|---|---|
| **1 PRIMARY** | **AIOps / AI Operations Engineer** | **73** | H1 | High (ops-flavor JDs) |
| **2 SECONDARY** | **Copilot / Copilot Studio / Copilot for Service** | **70** | H1 | High-Med → High after 8–12 weeks Studio |
| **3 BACKUP** | **AI Support / AI Agent Operations (TMUS-style)** | **68** | H1 | High on-account / Med external |
| 4 | ServiceNow Agentic / Now Assist | 64 | H1–H2 | Med now / High after PDI+Glide |
| 5 | Agentic AI Engineer | 62 | H2 | Low now / Med after HITL agent |
| 6 | Intelligent Automation (GenAI-named) | 61 | H1 | Med-High if scripts exist |
| 6= | Observability Engineer + AI overlay | 61 | H1 | High **if** Splunk/Dynatrace/SNOW ITOM is on TMUS |
| 8 | GenAI / Generative AI Engineer | 60 | H2 | Low now / Med at day 60–90 |
| 9 | RAG / Applied AI Engineer | 59 | H2 | Skip SQL-first Deloitte flavor |
| 9= | LLMOps Engineer | 59 | H2 | Low / Med after deploy+observe |
| 11 | AI SRE / Observability + AI | 57 | H2–H3 | Low as “SRE hire” (K8s usually missing) |
| 12 | Cloud AI Engineer (Azure OpenAI / Bedrock) | **56** | H2 | **Not Primary** |
| 13 | LLM Engineer | 53 | H2 | Infosys-industrialised |
| 14 | AI Engineer (generic) | 51 | — | Title dilution |
| 15 | AI Solutions Engineer | 50 | H2 | Mix of pre-sales / embedded |
| 16 | ITSM + GenAI process-only | 47 | — | Wrong destination |
| 16= | AI Platform Engineer | 45 | H3 | GPU/K8s control plane |
| 16= | Forward Deployed / AI Customer Engineer | 45 | H2–H3 | Elite, 5-day onsite |
| 19 | MLOps Engineer (classic) | 42 | — | CUDA/PyTorch/Kubeflow |
| 20 | Context / Evals Engineer (as title) | 32 | — | N=0 dedicated India titles; skill yes |
| 21 | Prompt Engineer | 25 | — | **Do not apply** |
| 22 | Research Scientist / FM Trainer | 15 | — | **Avoid** |

### Component scores — Primary / Secondary / Backup

| Criterion (weight) | AIOps 73 | Copilot 70 | TMUS Agent Ops 68 | Cloud AI 56 (not Primary) |
|---|---:|---:|---:|---:|
| Demand ×0.25 | 58 (14.50) | 55 (13.75) | 42 (10.50) | 70 (17.50) |
| Transferability ×0.20 | **92 (18.40)** | **90 (18.00)** | **95 (19.00)** | 40 (8.00) |
| Salary ×0.15 | 58 (8.70) | 62 (9.30) | 55 (8.25) | 58 (8.70) |
| Growth ×0.15 | 78 (11.70) | 62 (9.30) | 75 (11.25) | 70 (10.50) |
| Learning ease ×0.10 | 88 (8.80) | **92 (9.20)** | 82 (8.20) | 60 (6.00) |
| Low competition ×0.10 | 78 (7.80) | 70 (7.00) | 85 (8.50) | 28 (2.80) |
| Remote/geo ×0.05 | 72 (3.60) | 68 (3.40) | 48 (2.40) | 55 (2.75) |

Cloud AI loses Primary because **transferability 40** and **low-competition 28** kill a Service Desk Lead who will not lead with Java/SQL. Demand alone is not enough.

### Why AIOps wins

- Naukri `aiops` = **558** (honest occupation, not `ai` 84k pollution). **VERIFIED FACT**, 23 Aug 2026.
- Live JDs quote **IT Operations, Service Management, ITIL, ServiceNow, Dynatrace, Moogsoft**.
- Hybrid Cloud AIOps Senior Engineer card: **Hybrid Pune / Coimbatore / Bengaluru**, 3–5 yrs, **₹8–15 L**.
- Filter: skip LangGraph-only “AIOps” (Aditi AIRA, Equinix Staff) — those are H2 software jobs wearing an H1 title.

---

## PART 3 — Job market intelligence

### Macro (VERIFIED FACT unless labelled)

| Claim | Number | Source / date |
|---|---|---|
| India tech FY26 expected | **$315 bn**; employment **~6 million**; +135,000 net | NASSCOM Strategic Review 2026 |
| Agentic systems | “moved AI from support to execution” | NASSCOM 2026 |
| AI workforce (Quess, via Hans India) | **~9.2 lakh** total; **2.57 lakh core** vs **6.63 lakh embedded**; >70% outside specialist titles | Mid-June 2026, SECONDARY journalism of Quess |
| NASSCOM × Indeed | 86% of roles impacted by AI; 40% skills>degree; 58% low applicant volume (their sample) | May 2026 |
| GCC H1 2026 hires | **227,991** (+11% YoY); ~2,120 GCCs; 64% of new 2026 GCC roles need AI/DS/IA (was 11% in 2021) | foundit Insights Tracker, ET 1 Jul 2026 |
| GCC YOE mix | **4–10 YOE = 56%** (4–6: 34%; **7–10: 22%**) | Same. **This 7–10 band is the demographic that matches 8.5 YOE** |
| Tier-2 GCC | **15%** of GCC hiring, **+23% YoY**; Coimbatore **named** | Same |
| LinkedIn India | +51% AI engineering roles; 311k India since 2023 | LinkedIn India head, 22 Aug 2026 |
| Naukri JobSpeak | AI +16% YoY vs IT −3% | June 2026 |

### Naukri RAW keyword vs occupation (do not confuse)

| Slug | RAW N (Aug 2026) | Hygiene |
|---|---:|---|
| `ai` | **84,313** | Unusable as occupation |
| `ai-engineer` | 46,957–49,520 | Broad |
| `ai-automation` | **68,385** | **Not AIOps** |
| `co-pilot` | 35,332 | Aviation + generic “pilot” pollution |
| `gen-ai` | **28,722–28,853** | Best *broad* GenAI proxy |
| `generative-ai-engineer` | **11,132** | Cleaner |
| `agentic-ai` | **9,938** | Tightest 2026 cluster |
| `rag` | **6,876** | Mostly RAG-pipelines |
| `langchain` | **4,122** | Framework demand |
| `mlops` | **4,207** | Mix classic MLOps |
| `llmops` | **678–877** | Small specialised |
| `aiops` | **558** (22 Aug title also 680) | **Honest IT-ops occupation** |
| `prompt-engineer` | 15,585 (June title) | Employer name “Prompt” pollution; occupation ~81 AmbitionBox |
| Coimbatore `artificial-intelligence` | **527** | Thin local IC market |
| `fde` | 158 | Includes true FDE |
| `servicenow` | 8,305 | Includes classic SN |

**Other boards (23 Aug 2026):** Indeed `agentic ai engineer` **400**; Indeed `generative ai engineer` **~4,000**; Instahyre GenAI **5,606–5,607**; Glassdoor India ServiceNow Agentic AI Developer **153**; Glassdoor AIOps platform engineer **272**; Foundit Microsoft Copilot **497**.

### Unique JD corpus (this harvest) — N=455

This is **not** Naukri’s 9,938. It is every unique listing URL/ID captured without board APIs.

| Metric | N |
|---|---:|
| Unique listing keys after URL/ID dedupe | **455** |
| LIVE (page retrieved 23 Aug 2026) | 182 (40.0%) |
| INDEXED-LIVE | 143 (31.4%) |
| INDEXED-LIVE-PARTIAL (card/snippet) | 110 (24.2%) |
| RECENT-CLOSED | 18 (4.0%) |
| EXPIRED / OLDER | 2 (0.4%) |
| Volume/search pages excluded | 31 |
| Java named Y on the row flag | 24 (5.3%) |
| SQL named Y on the row flag | 29 (6.4%) |
| Employer-stated salary nonempty | 41–45 |

**Source mix of the surviving URL**

| Source | N | % |
|---|---:|---:|
| Naukri | 233 | 51.2% |
| LinkedIn | 94 | 20.7% |
| Instahyre | 35 | 7.7% |
| Company careers | 26 | 5.7% |
| Glassdoor | 22 | 4.8% |
| Foundit | 18 | 4.0% |
| hirist | 11 | 2.4% |
| Cutshort | 7 | 1.5% |
| Shine / others | 9 | 2.0% |

**Role-family heuristic (title+snippet, INFERENCE)**

| Family | N | % |
|---|---:|---:|
| Agentic AI / Agents | 184 | 40.4% |
| GenAI / LLM Engineer | 95 | 20.9% |
| LLMOps / MLOps | 44 | 9.7% |
| Copilot Studio / Power Platform | 39 | 8.6% |
| RAG / Applied LLM | 25 | 5.5% |
| AIOps / Observability | 24 | 5.3% |
| ServiceNow / Now Assist / ITSM-AI | 22 | 4.8% |
| Other applied AI | 22 | 4.8% |

**Geography mentions (a listing can hit multiple cities)**

| City | Mentions | % of 455 |
|---|---:|---:|
| Bengaluru | 257 | 56.5% |
| Hyderabad | 121 | 26.6% |
| Pune | 87 | 19.1% |
| Chennai | 73 | 16.0% |
| NCR | 56 | 12.3% |
| Mumbai | 27 | 5.9% |
| Remote | 25 | 5.5% |
| **Coimbatore** | **6** | **1.3%** |

**Experience mid-point buckets (parsed from the exp field)**

| Band | N | % of 455 |
|---|---:|---:|
| 0–2 | 15 | 3.3% |
| 3–5 | 109 | 24.0% |
| **6–8** | **174** | **38.2%** |
| 9–12 | 64 | 14.1% |
| 13+ | 14 | 3.1% |
| Unspecified | 79 | 17.4% |

**6–12 YOE is the fat of this corpus.** 8.5 years is not “too senior.” The risk is **wrong title translation** (Service Desk Lead → junior AI Engineer 2–4 YOE), not age-out.

**Companies appearing most often (unique listings, not headcount)**

Infosys 27, Cognizant 23, Tekskills 19, TCS 18+5, Capgemini 14, EY 11, Accenture 7, CGI/HCLTech/KPMG India/Sonata 6 each, Persistent/PwC 5, DXC/Optum/Wipro/Zensar 4.

### Full-body Java/SQL (A3, N=37 — better than snippet flags)

| Signal | Count | % |
|---|---:|---:|
| Java required or co-equal | 4 | 11% |
| SQL/DBMS required or co-equal | 8 | 22% |
| **Neither named** | **25** | **68%** |

Wave-1 coded set N=52: Java 12% / SQL 23% / neither 65%. **Constraint is affordable** if mashups and SQL-first RAG are skipped.

---

## PART 4 — Top 50 skills with frequencies

Two datasets. Do **not** average them.

1. **letsinterview.me N=313 AI Engineer JDs (Feb 2026)** — full-body, generic “AI Engineer” mix. Best for “what a GenAI IC JD actually names.”
2. **This harvest N=455 snippets (23 Aug 2026)** — applied GenAI + AIOps + Copilot + SN. **Under-counts** Python/Docker/Git because 24% of rows are PARTIAL cards that never mention stack. **Over-weights** “Agentic” because the harvest targeted that cluster.

### A. Full-body AI Engineer JDs (letsinterview N=313) — VERIFIED FACT of that scrape

| Skill | % of 313 | n | Blocking for first GenAI shortlist? |
|---|---:|---:|---|
| Python | **83%** | 260 | **BLOCKING** |
| Azure (cloud) | **49%** | ~153 | Accelerator; blocking on MS accounts |
| RAG | **48%** | 149 | **BLOCKING** for GenAI/LLM titles |
| AWS (cloud) | **45%** | ~141 | Blocking on Infosys/Bedrock JDs |
| Agentic AI / agents | **43%** | 134 | **BLOCKING** for 2026 Agentic titles |
| LangChain | **42%** | 131 | Near-blocking on services GenAI |
| Fine-tuning | **37%** | 115 | Optional for ops→GenAI first hop |
| GCP | **37%** | ~116 | Optional unless Vertex/ADK |
| OpenAI/GPT | **34%** | 106 | Blocking as “call an LLM API” |
| CI/CD | **34%** | 105 | Accelerator |
| Prompt | **33%** | ~103 | Skill yes; title no |
| Embeddings | **31%** | ~97 | Blocking as a *concept* |
| Docker | **31%** | 98 | Near-blocking for “deployed” claims |
| PyTorch | **30%** | ~94 | Not blocking for applied GenAI |
| TensorFlow | **28%** | ~88 | Copy-paste on many services JDs |
| Git | **27%** | 84 | Blocking as hygiene |
| Hugging Face | **23%** | ~72 | Optional |
| Kubernetes | **23%** | 72 | Optional first hop; blocking MLOps |
| FastAPI | **22%** | 68 | Concept (APIs) blocking; framework accelerator |
| SQL | **20%** | 64 | Working knowledge, not a career bet |
| Pinecone | **19%** | ~59 | Brand interchangeable |
| LlamaIndex | **15%** | 47 | Optional |
| Weaviate / FAISS | **13%** each | ~41 | OR-list with Pinecone/Chroma/Milvus |
| Java | **12%** | 36 | **Do not pursue for this profile** |
| Azure OpenAI named | **12%** | ~38 | Accelerator |
| CrewAI | **11%** | 33 | Optional |
| Chroma | **12%** | ~38 | OR-list |

letsinterview line used as doctrine: *“If you only have time to learn two things, make it RAG and Agentic AI.”*

### B. This 455-snippet corpus (23 Aug 2026) — VERIFIED FACT of SKILL-FREQ.json

| Rank | Skill | N | % of 455 |
|---:|---|---:|---:|
| 1 | Agentic / agents | 216 | 47.5% |
| 2 | Python | 153 | 33.6% |
| 3 | RAG | 121 | 26.6% |
| 4 | LangChain | 95 | 20.9% |
| 5 | Azure (cloud) | 73 | 16.0% |
| 6 | Azure OpenAI / Azure AI | 72 | 15.8% |
| 7 | LangGraph | 68 | 14.9% |
| 8 | OpenAI API | 52 | 11.4% |
| 9 | Prompt engineering | 51 | 11.2% |
| 10 | Vector DBs (any) | 46 | 10.1% |
| 11 | AWS / Bedrock | 44 | 9.7% |
| 12 | GCP / Vertex | 44 | 9.7% |
| 13 | REST / APIs | 40 | 8.8% |
| 14 | Copilot Studio | 39 | 8.6% |
| 15 | MLOps | 32 | 7.0% |
| 16 | CrewAI | 29 | 6.4% |
| 17 | LLMOps | 27 | 5.9% |
| 18 | AutoGen | 26 | 5.7% |
| 19 | ServiceNow / Now Assist | 26 | 5.7% |
| 20 | SQL | 25 | 5.5% |
| 21 | TensorFlow | 25 | 5.5% |
| 22 | AIOps | 25 | 5.5% |
| 23 | PyTorch | 24 | 5.3% |
| 24 | Power Platform | 24 | 5.3% |
| 25 | LlamaIndex | 23 | 5.1% |
| 26 | Java | 22 | 4.8% |
| 27 | Bedrock | 22 | 4.8% |
| 28 | Claude / Anthropic | 22 | 4.8% |
| 29 | MCP | 19 | 4.2% |
| 30 | Now Assist | 18 | 4.0% |
| 31 | Semantic Kernel | 17 | 3.7% |
| 32 | Kubernetes | 15 | 3.3% |
| 33 | Docker | 14 | 3.1% |
| 34 | Hugging Face | 14 | 3.1% |
| 35 | Pinecone | 13 | 2.9% |
| 36 | CI/CD | 12 | 2.6% |
| 37 | C# / .NET | 10 | 2.2% |
| 38 | FAISS | 10 | 2.2% |
| 39 | FastAPI | 9 | 2.0% |
| 40 | Git | 9 | 2.0% |
| 41 | JavaScript | 8 | 1.8% |
| 42 | Weaviate | 8 | 1.8% |
| 43 | ITIL / ITSM | 7 | 1.5% |
| 44 | n8n / RPA | 6 | 1.3% |
| 45 | TypeScript | 5 | 1.1% |
| 46 | Chroma | 5 | 1.1% |
| 47 | Milvus | 5 | 1.1% |
| 48 | Observability (Dynatrace/Splunk/Datadog) | 5 | 1.1% |
| 49 | Evals / guardrails | 5 | 1.1% |
| 50 | Terraform | 4 | 0.9% |

**ITIL/SN/Dynatrace look “rare” here because the harvest is GenAI-heavy and many AIOps cards are PARTIAL.** Live AIOps JDs (EY, Naukri hybrid card) still name ServiceNow, Dynatrace, Moogsoft, IT Operations, Service Management as must-haves. Use **Door 2 JDs**, not this mixed %, to size ITSM skills.

### Skill co-occurrence (N=455 snippets)

Pairs with highest joint count:

| Both | % of 455 | Pair |
|---:|---:|---|
| 80 | 17.6% | Agentic × RAG |
| 76 | 16.7% | Agentic × Python |
| 61 | 13.4% | Agentic × LangChain |
| 61 | 13.4% | Python × RAG |
| 59 | 13.0% | RAG × LangChain |
| 56 | 12.3% | LangChain × LangGraph |
| 53 | 11.6% | Python × LangChain |
| 50 | 11.0% | Agentic × LangGraph |
| 50 | 11.0% | Azure × Azure OpenAI |
| 41 | 9.0% | RAG × LangGraph |
| 39 | 8.6% | Azure OpenAI × Copilot Studio |
| 36 | 7.9% | RAG × Vector DBs |
| 33 | 7.3% | Python × LangGraph |
| 28 | 6.2% | LangChain × Vector DBs |
| 25 | 5.5% | Agentic × CrewAI |
| 24 | 5.3% | Agentic × AWS/Bedrock |

**INFERENCE:** The 2026 applied stack that actually co-occurs is **Python + RAG + LangChain/LangGraph + one LLM API + one vector store**. Copilot Studio co-occurs with Azure OpenAI, not with LangGraph. That is two different H1 doors — do not mash them into one identity in week 1.

letsinterview also found LangChain+RAG together on **100 of 313** AI Eng JDs.

---

## PART 5 — Skill gap map (this profile)

Categories A–F for Manoj. Labels: **Have / Partial / Missing**.

| Cat | Skill | Status now | Evidence | 90-day target |
|---|---|---|---|---|
| **A Blocking H1 AIOps** | Incident / problem / change / SLA / major-incident comms | **Have** | 8.5 YOE Service Desk Lead | Translate to JD language (ITIL, ticket deflection, TTR) |
| A | One observability / ITOM platform | **Unknown — user must map TMUS tools** | EY/Naukri cards name Dynatrace, Splunk, Moogsoft, ServiceNow ITOM | Name **one** real account tool in writing this week |
| A | Python enough to call an LLM API + pytest | **Missing / Partial** | Infosys must-have: OOP, typing, pytest, basic async | Days 1–21 FastAPI `POST /summarize` |
| A | Git + GitHub public repo | **Assumed missing as proof** | SuperSourcing: no GitHub = refuse senior GenAI screen | Repo v0 week 1 |
| **B Blocking H2 GenAI** | RAG (chunk, embed, retrieve, cite) | **Missing** | 48% of 313; 26.6% of 455 | Project 1 on synthetic tickets |
| B | LangChain **or** LangGraph (one, then the other) | **Missing** | 42% / rising on 2026 agentic JDs | LangGraph HITL agent Days 51–75 |
| B | One vector DB | **Missing** | Concept blocking; brand OR-list | Chroma or FAISS locally; know Pinecone exists |
| B | One LLM API (Azure OpenAI **or** Bedrock **or** OpenAI) | **Missing** | Provider interchangeable | **Pick Azure OpenAI first** (see Part 7) |
| **C Accelerator** | Docker basics | Missing | Infosys “Docker basics”; 31% of 313 | Containerize Project 1 by day 75 |
| C | Evals / golden set / cost | Missing | Infosys “basic evaluation awareness”; differentiator vs clones | Project 5 mini-harness |
| C | Copilot Studio | Missing | Secondary role; TCS IT-support Copilot JDs | Parallel 8–12 week builder skill |
| C | FastAPI | Missing | 22% of 313 | Same as Python bar |
| **D Optional / later** | Kubernetes, Terraform, CKA | Skip 90 days | 23% of 313; almost never “CKA required” | H3 / MLOps only |
| D | LoRA / QLoRA / PyTorch training | Skip | Fine-tune 37% is generic-ML copy-paste | Push back: RAG first |
| D | CrewAI / AutoGen / LlamaIndex | Awareness | OR-lists with LangGraph | One sentence in interview: “I chose LangGraph because state/HITL” |
| D | MCP | Awareness | Named on Optum, TCS, Workfall, Hartford | Demo one MCP tool **after** agent v1 |
| **E Do not learn as identity** | Java / Spring | **Skip** | 11–12% of corpora; constraint | Close the tab |
| E | SQL-first data-eng RAG | **Skip as career** | 20–22%; Deloitte GCP RAG, Hitachi | Literacy only (read a ticket table) |
| E | Prompt Engineer as title | **Skip** | Occupation ~81; Indeed avg ₹4.95 L | Prompt **inside** RAG |
| **F Hidden tax on best ITSM JDs** | JavaScript / Glide | Partial/Missing | Convera, NOBL Q, Booking SN CAD | Only if Door 2 = ServiceNow build |

**Two-door thesis (A7, RECOMMENDATION):** Use Door 2 **content** (ITSM/incidents/on-call) and Door 1 **implementation** (Python, RAG, agents, FastAPI, Docker). Almost none of the 313 AI Eng JDs asked for ServiceNow **and** LangChain together. That rarity is the conversion thesis.

---

## PART 6 — Learning roadmap (P0–P3)

Hours assumption: **12–15 hrs/week** from an ops-lead job (8 hrs is still a start). **No T-Mobile client data.** Synthetic tickets only.

### Phase 1 — Days 1–21 — P0: Python bar + one LLM API

| P | Skill | Why |
|---|---|---|
| P0 | Python venv, typing, pytest, one FastAPI route | Infosys must-have; Deloitte live coding is even/odd + prime |
| P0 | Azure OpenAI **or** OpenAI API chat + system prompt | “Call an LLM” is the actual blocking skill |
| P0 | GitHub repo with README that says **synthetic data** | SuperSourcing production-proof filter |
| P0 | 20 synthetic incidents (P1–P4, CI classes, fake CMDB ids) | Domain content |

**Deliverable:** `POST /summarize` returns a 5-line incident summary + next-action. pytest ≥3 tests.

### Phase 2 — Days 22–50 — P0: RAG on ops data

| P | Skill | Why |
|---|---|---|
| P0 | Chunking types, embeddings, one local vector store | TCS/Deloitte interview Qs |
| P0 | Citations / “I don’t know” | Hallucination is the senior signal |
| P1 | Hybrid search one-pager (you can explain, not implement Elasticsearch) | TCS similarity techniques Q |

**Deliverable:** Incident Copilot v1 — retrieve from runbook+KB+tickets, answer with source ids, eval on 15 golden questions.

### Phase 3 — Days 51–75 — P0: HITL agent

| P | Skill | Why |
|---|---|---|
| P0 | LangGraph state machine: plan → tool → human approve → execute mock | Cognizant/Infosys agent flows; Deloitte “failed agents” reject |
| P0 | Tool calling (create ticket, search KB, post summary) | 2026 agentic must-have |
| P1 | Token/cost log | Infosys “latency, token usage, cost” |

**Deliverable:** Runbook agent that **cannot** close a P1 without human approval. Demo GIF.

### Phase 4 — Days 76–90 — P1: evals + applications + one exam *or* CSA decision

| P | Skill | Why |
|---|---|---|
| P1 | RAGAS-style or custom golden-set scores in README | Clone filter |
| P1 | Docker one-command run | Infosys Docker basics |
| P1 | 15 saved H1 JDs applied (AIOps ops-flavor, Copilot, TMUS, Now Assist) | Not 200 GenAI sprays |
| P2 | AI-103 **only if** saved JDs are Azure-heavy | See certs |
| P2 | CSA **only if** Door 2 = ServiceNow script | Else skip |

**Single best cloud to prioritise first: Azure.**  
**VERIFIED FACT:** Azure is **49%** of 313 AI Eng JDs vs AWS 45% vs GCP 37%. Copilot Studio (Secondary) and many Cognizant/Accenture MS accounts are Azure. Bedrock is **blocking on Infosys** specifically — add as P1 in month 3 if Infosys/AWS JDs dominate the saved list. Do **not** learn three clouds in 90 days.

---

## PART 7 — Technology stack

| Bucket | Tools | Why |
|---|---|---|
| **Must master (90 days)** | Python, pytest, FastAPI (or Flask), Git, one LLM API (**Azure OpenAI first**), RAG (chunk/embed/retrieve/cite), **one** of LangChain/LangGraph (prefer LangGraph for HITL), one vector store (Chroma/FAISS), Docker basics, evals on a golden set | Blocking on H2 GenAI + portable to AIOps overlay |
| **Working knowledge** | Azure AI Search / Foundry names, Bedrock Knowledge Bases (read the Infosys JD), Copilot Studio topics/actions, ITIL language, REST to ServiceNow (not Glide), Bash, prompt patterns (system/few-shot), cost/latency | Secondary role + AIOps JDs |
| **Awareness** | CrewAI, AutoGen, LlamaIndex, Semantic Kernel, MCP, Pinecone/Weaviate/Milvus/Qdrant as OR-list, Vertex ADK, Now Assist Skill Kit, Dynatrace Davis / Splunk AI Assistant | Interview “why I did not pick X” |
| **Ignore for 90 days** | Java/Spring, SQL warehouses, CUDA/PyTorch training, LoRA, CKA/Kubernetes deep, Terraform, n8n-as-identity, prompt-only certs, GAN/VAE/foundation-model training, DSA grinding for FAANG | Constraint + ROI |

**STOP-LEARNING LIST (justification)**

| Stop | Why |
|---|---|
| Prompt Engineer courses as a career | Occupation ~81; pay ~₹5 L |
| Java + GenAI mashup JDs | Become a Spring dev with a ChatGPT wrapper |
| Fine-tune-on-300-PDFs | Interview answer is RAG, not LoRA |
| CKA in the next 90 days | ₹36–42k and 8–12 weeks; experience > CKA for this hop |
| Three agent frameworks at once | LangGraph + HITL is enough; CrewAI is OR-list |
| AI-900 / AI-102 | Retired Jun 2026 |
| MLS-C01 | Retired 31 Mar 2026 |
| Fake 8.5 years LangChain | BGV-lethal; Cognizant prints total vs relevant |

---

## PART 8 — Portfolio strategy

### What not to build

Chat-with-PDF clones, FIFA/bike-rental/rice-leaf institute capstones (they **recur in vendor success stories and get discounted**), image-gen galleries, prompt libraries with no evals, anything using **real T-Mobile tickets**.

### Six specified projects (A7) — build 1, 2, 5 in 90 days; 3 or 4 if time

| # | Project | Why it scores for this CV | Horizon |
|---|---|---|---|
| **1** | **Incident Copilot** — RAG on synthetic tickets + runbooks + KB | Domain + RAG 48% | Days 22–50 |
| **2** | **Agentic runbook executor, HITL** | Agentic 43%; Convera/TCS ops-agent language | Days 51–75 |
| **3** | ServiceNow-shaped REST integration (not a SN plugin unless PDI) | Door 2 without Glide | Optional |
| **4** | Log / major-incident summarizer | AIOps overlay; no APM license needed | Optional |
| **5** | Eval harness + cost dashboard | Senior signal; clone filter | Days 76–90 |
| **6** | On-call assistant (PagerDuty-shaped) | Stretch | Later |

### Top 5 for this user (scored informally: transferability × interview ask × 90-day feasibility)

1. Incident Copilot (RAG + citations)  
2. HITL runbook agent (LangGraph)  
3. Eval + cost README (makes 1 and 2 senior)  
4. Copilot Studio IT-support agent (Secondary role)  
5. Major-incident summarizer (AIOps story)

**Anti-clone checklist (every README):** synthetic data disclaimer; golden-set score; failure modes (images in PDFs, stale CMDB, P1 without HITL); cost per 100 tickets; one-command Docker; what you would **not** send to production.

---

## PART 9 — Flagship project (design)

**Name:** **OpsCopilot — HITL Incident Copilot for Enterprise ITSM**

**One line:** A retrieval-grounded, human-in-the-loop agent that summarises incidents, suggests runbooks, and **refuses to close P1s without approval** — on synthetic ITSM data.

**Why this is the flagship:** It is the only artefact that is simultaneously (a) AIOps-transferable, (b) Copilot/Now Assist-analogue, (c) GenAI-interviewable (RAG, agents, evals), (d) honest for an 8.5 YOE ops lead, (e) not a PDF chatbot.

### Architecture

```
Synthetic ITSM store (tickets, CMDB stubs, runbooks, KB)
        │
        ▼
Ingest → chunk (by ticket field + recursive on KB)
        → embed → vector store (Chroma/FAISS) + keyword metadata
        │
        ▼
FastAPI
  POST /summarize          LLM summary + next action
  POST /ask                RAG + citations (ticket/KB ids)
  POST /agent/plan         LangGraph: retrieve → propose tools → HITL gate
  POST /agent/approve      human approve/reject
  GET  /evals              golden-set scores + token cost
        │
        ▼
Azure OpenAI (primary) / OpenAI fallback
Guardrails: P1 cannot auto-close; no real PII; tool allow-list
```

| Stage | What “done” means |
|---|---|
| **MVP (day 21)** | `/summarize` + 20 synthetic incidents + pytest |
| **POC (day 50)** | `/ask` RAG with citations; 15 golden questions; “I don’t know” path |
| **Production-shaped (day 90)** | LangGraph HITL; Docker; eval table; cost per 100 tickets; demo GIF; README failure modes |

### Resume / LinkedIn / GitHub language (allowed)

> Built a human-in-the-loop incident copilot on **synthetic** ITSM data: RAG over tickets/runbooks/KB, LangGraph tool-calling with P1 approval gates, FastAPI, Azure OpenAI, golden-set evals (accuracy / citation / cost). 8.5 years leading enterprise service-desk operations at Cognizant (T-Mobile account) informed the process model — **not** production client data.

**Forbidden:** “Production AIOps platform for T-Mobile”; “8 years LangGraph”; screenshots of real tickets.

---

## PART 10 — Interview intelligence

**A5 sourced N=72 questions** from candidate reviews (Glassdoor, Taro, GFG, LinkedIn). Prep-blog lists are SECONDARY and are **not** counted as “asked.”

### Process maps (compressed)

| Employer type | Typical loop | DSA? |
|---|---|---|
| TCS / Infosys / Wipro / CTS / Accenture / Capgemini / IBM / Deloitte | Recruiter → 1–2 tech (RAG/agents/Python) → HM → **client/partner** | **Usually no LeetCode grind.** Deloitte India: even/odd + prime + RAG/agents. Capgemini: YOE-mismatch reject. |
| Fractal / Tiger | Live Python + RAG; sometimes DSA | Mixed; longer (Fractal community: ~6 months) |
| Microsoft / Amazon / Google FDE / Adobe | SWE/ML loops | **Yes.** Not year-1 from this CV. |
| TMUS Support/Ops | Domain + bot/ops language | Python nice-to-have |

### Highest-probability themes for **your** target roles (INFERENCE from sourced Qs)

**Top 30 to actually rehearse** (sourced or tightly implied by sourced loops):

1. What is RAG? Components and flow. (CTS, Deloitte, IBM, TCS)  
2. Types of chunking. (Deloitte)  
3. How do you deal with PDFs / images / unstructured docs? (Deloitte)  
4. Vector DB — what it is; FAISS vs Chroma vs Pinecone vs Weaviate. (TCS)  
5. Similarity: cosine vs dot-product vs Euclidean. (TCS)  
6. How to improve a RAG QA bot (rerank, hybrid, citations, evals). (TCS)  
7. RAG vs Agent; shared memory; design an agent. (Deloitte Bengaluru)  
8. What are agents? Tool/function calling. (Deloitte — candidate **failed agents**)  
9. Prompt techniques you have used. (Deloitte)  
10. LangChain vs raw API — when each. (theme in TCS/Infosys JDs + interviews)  
11. Hallucination — how you measure and stop it.  
12. Human-in-the-loop — why P1 must not auto-remediate. (**your** story)  
13. Python: decorators, comprehensions, inheritance vs polymorphism, class vs static. (TCS)  
14. pytest — how you test an LLM call (mock the API).  
15. Explain **your** GitHub project end-to-end. (Deloitte Q2)  
16. Token cost / latency — what you logged. (Infosys JD language)  
17. Guardrails / prompt injection.  
18. Azure OpenAI vs Bedrock vs raw OpenAI — why you picked one.  
19. ITIL: incident vs problem vs change; major-incident comms. (AIOps JDs)  
20. How would you reduce ticket volume with a copilot without leaking PII?  
21. Observability: what signal goes into an AIOps correlation engine?  
22. When would you **not** use an LLM (runbook is deterministic)?  
23. “You have 8.5 years — where is the GenAI?” — **total vs relevant** answer.  
24. Why not Java? Why not SQL-first?  
25. Walk through a Sev1 you owned — then how an agent would assist, not replace, you.  
26. Client round: RAG + agentic framework **application** (Deloitte client reject after 3 clears).  
27. Imbalanced data / F1 — classical ML still appears inside “GenAI” loops (Deloitte).  
28. Even/odd + prime live coding — do not freeze. (Deloitte)  
29. Notice period 90 days — how you handle it.  
30. “This repo looks like a tutorial” — eval table + synthetic disclaimer + failure modes.

**DSA finding:** Services GenAI loops in the sourced set are **Python basics + RAG/agents**, not graph/DP. Product/FAANG is a different profession. **Do not spend 90 days on LeetCode** for the Primary/Secondary/Backup stack.

**Rejection patterns (A5/A6):** YOE mismatch (Capgemini); client round after tech clear (Deloitte, Wipro); no production/RAG proof; failed agents; fake AI YOE (BGV). EY *The First Firewall* (29 May 2025) — forensics on credential fraud.

The remaining ~42 sourced questions (Q31–Q72) live in `research/A5-interviews.md` (Python OOP, NLP, DL one-bit quantization, SCD/dedup, etc.). Use that file as the full bank. Do **not** treat this summary’s Top 30 as a claim that A5 only found 30.

---

## PART 11 — System-design scenarios (themes)

Not a scored 30-row table (that extra was not completed). These are the **architectures interviewers and JDs actually probe**:

1. RAG over a knowledge base (chunk → embed → retrieve → generate → cite)  
2. RAG over tickets + runbooks (metadata filters: CI, assignment group, severity)  
3. Hybrid search (keyword + vector)  
4. Images/scanned PDFs in the corpus  
5. Very large RAG (hierarchical index / routing)  
6. Multi-agent planner-executor with shared memory  
7. HITL approval gate for write tools  
8. Tool allow-list / MCP server for ITSM APIs  
9. Copilot Studio topics + Power Automate + ServiceNow REST  
10. Now Assist / Virtual Agent on ITSM (config-first vs custom skills)  
11. Incident summariser in the major-incident bridge  
12. Event correlation (AIOps) vs LLM summarisation — when each  
13. Auto-remediation with StackStorm/Rundeck **and** a kill switch  
14. Eval harness (golden set, LLM-as-judge, regression)  
15. Cost/latency/token budgets and caching  
16. Prompt-injection / data-exfil via retrieved docs  
17. PII redaction before the LLM  
18. Azure OpenAI vs Bedrock vs self-host (data residency)  
19. Blue/green prompt+index versions  
20. Observability of the **AI app** (traces, quality, drift) vs infra APM  
21. Multi-tenant GCC isolation  
22. Fallback when the model is down  
23. Deterministic runbook vs LLM (don’t LLM a password reset)  
24. Memory: session vs long-term vs none  
25. Embedding model choice and re-index cost  
26. Reranking  
27. Guardrails / Azure content filters / Bedrock Guardrails  
28. Human feedback loop into the golden set  
29. Change-management for an agent that can open tickets  
30. Why this should not go to production on day 1 (your README)

---

## PART 12 — Company target list (from evidence, not a fake 100-score)

**Insufficient reliable evidence to publish a scored Top 100.** Below is the **evidence-backed targeting list** plus corpus concentration.

### Tier logic for *this* CV

| Tier | Meaning | Examples |
|---|---|---|
| **1 — Apply now (H1 ops-flavor)** | JDs that name ITSM/ITIL/observability/Copilot-for-IT | EY AIOps (incl. Coimbatore hybrid card), Accenture Run-ops, HPE DevOps/MLOps/GenAI Platform Owner, Convera ITSM Agentic (Pune; JS tax), CGI Copilot 6–9Y, TCS Copilot Studio (IT support + SN REST), CDK Global Copilot **₹15–20 L** Hyd, IBM AIOps consultant, Persistent LLMOps+AIOps (filter stack), TEKsystems Now Assist, Booking Holdings SN AI CoE |
| **1-account** | Named door on T-Mobile / CTS | **TMUS Hyderabad Engineer, AI (Support/Operations)** Tess IT Help bot; CTS IOA / Copilot / SN Agentic / Frontier / Chennai Gen AI Engineer `00067173931` |
| **2 — Day 60–90 with artefacts** | Python+RAG+agents, 6–12 YOE, no Java-first | Infosys GenAI/Agentic (Bedrock must-have), Cognizant Python LangGraph 7–13, Altimetrik, Hexaware GenAI+Agentic **₹12–22 L**, Wipro GenAI Lead **₹24–30 L** (recruiter-posted — verify), PwC Agentic (ITIL chip), Optum LangGraph+MCP, UST Google ADK, RoundCircle LangGraph, Orion Innovation Chennai, Sonata Copilot/M365 |
| **3 — GCC stretch after proof** | Coding + domain | PepsiCo Now Assist/agentic Hyd (senior), Deloitte USI GenAI (client round), Freshworks Lead SWE ML 6–9 (LangGraph), UnitedHealth RAG/LangGraph, Hartford Agentic, Silicon Labs Hyd, ServiceNow product Bangalore (Staff — stretch) |
| **4 — Watch / avoid as first hop** | Pay cut, Java/SQL-first, research, fake volume | TCS GenAI **₹2–7 L** / Glassdoor est. ₹5–7 L; Infosys GenAI pages ₹6–8.5 L (2–5 YOE); SysTechCorp AIOps **max 10 LPA**; Qualys CUDA MLOps; Deloitte SQL-first RAG; Sarvam GPU platform; Prompt shops; TestUnity ₹4.5–5 L |

**Coimbatore-named in harvest:** EY GDS Gen AI Specialist Manager; EY Hybrid Cloud AIOps card; Systango GenAI; Techify Gen AI; ShellKode Gen AI Lead (closed); Bosch / XaasIO / Aivar in A4/A8.

---

## PART 13 — Salary strategy

**₹11 LPA at 8.5 YOE is at/above Service Desk Lead, behind CTS software 6–9.**

### Baseline (VERIFIED FACT)

| Series | Band | n | Source |
|---|---|---:|---|
| Service Desk Lead India 6–9 | **₹7.6–8.4 L** | 268 | AmbitionBox |
| CTS Service Desk Team Lead 8–10 | **₹9.3–12.9 L** | 4 (small) | AmbitionBox |
| Glassdoor Service Desk Lead India | avg ₹8.0 L; P25 ₹6.56 L; P75 ₹10.0 L | 21 | Glassdoor |
| CTS Software Developer 6–9 | **₹14.3–15.8 L** | 1.1k | AmbitionBox |
| CTS Senior Software Developer 6–9 | **₹17.1–18.9 L** | 529 | AmbitionBox |
| IT Operations Engineer India 6–9 | ₹10.1–11.9 L | 229 | AmbitionBox |
| Stay, IT services hike | **6.9%** → ~₹11.8 L | — | Deloitte India Talent Outlook 2026 |

### AI / adjacent (do not average)

| Series | Band | n / note |
|---|---|---|
| Artificial Intelligence Engineer 6–9 | ₹16.2–23.5 L; FAQ avg ₹19.8 L | **n=20 small**; IT Services industry slice **₹11.1 L** |
| AI Engineer 6 YOE | ₹20.9–26.9 L | n=90 mixed titles |
| Glassdoor India AI Engineer median | **₹11 L** | 20 Aug 2026 |
| Glassdoor GenAI Engineer India | ~₹9.5–9.9 L | n=23 |
| Infosys Generative AI Engineer | **₹6.2–8.5 L** | n=20+, **2–5 YOE** |
| Accenture GenAI 6–9 | ₹9.4–13.8 L | n=3 |
| DevOps 6–9 | **₹12.7–14.1 L** | n=5.9k |
| SRE 8 YOE | **₹19.9–22.0 L** | n=474 |
| IBM SRE 6–9 | ₹18.9–21.8 L | n=107 |
| IBM AI Engineer 6–9 | ₹27.2–30.2 L | n=133 — **IBM AI Engineer, not a desk conversion** |
| Naukri AIOps disclosed modal | **₹10–15 L = 187 of 558** | VERIFIED FACT of filter |
| CTS MLOps 6–9 | ₹16.8–18.6 L | n=3 |
| India Technical Lead 6–9 | ₹18.2–20.1 L | n=79.6k (all companies, not AI) |

### Employer-stated on this 455 corpus (sample; not Glassdoor estimates)

| CTC | Role | Company |
|---|---|---|
| **2–7 Lacs PA** | Generative AI Engineer 4–8 | TCS — **pay-cut trap** |
| max **10 LPA** | AIOps 6+ | SysTechCorp — **below ₹11 L** |
| 8–15 L | Hybrid Cloud AIOps 3–5 | EY card Pune/CBE/BLR |
| 9–15 / 9.5–15 / 10–15 | LLM infra / GenAI / MLOps | Zippyops, Cloudxtreme, Bluvin |
| **12–22 L** | GenAI + Agentic | Hexaware (employer) |
| **12–45 L** | Power Platform / Copilot | SourcingXPress (wide) |
| **14–20 L** | MLOps | Adecco Pune/BLR |
| **15–20 L** | Copilot Studio Engineer 6–10 | **CDK Global Hyderabad** |
| **15–20 L** | GenAI Engineer | Logikality (ESOP) |
| **15–25 L** | ML & GenAI | Nisum |
| **15–27.5 L** | Agentic AI Engineer | Infosys (employer on one card) |
| 15–26 L / 15–20 L | Now Assist / SN Agentic | Avensys / Qentelli (prior harvest) |
| **18–27.5 / 18–30** | Salesforce AI / Agentic | Randstad / Indeed Infosys card |
| **20–27.5 L** | Agentic 8–13 | Advance Career Solutions; Stack Digital |
| **20–30 L** | AI/ML 8–13; Now Assist Sr | Alois; Solarix |
| **20–35 L** | LangGraph / Agentic DS / MLOps | Aspyra |
| **22–55 L** | GenAI backend 10–15 | BigRio Chennai (Cutshort) |
| **24–35 L** | Agent Application Engineer | Sentiaflow |
| **24–30 / 35–40 L** | Wipro GenAI Lead / Architect | Recruiter-posted — verify |
| **25–40 L** | Copilot Studio Architect | Cyclotron remote |
| **25–40 L** | MLOps remote | ZeroToOne.AI (closed) |
| **30–45 L + equity** | ML & LLM Ops | MantriAI (closed; 30–45 day NP) |
| **30–60 L** | Agentic AI Architect 10–17 | Air India — not first hop |
| **₹32–35 L** | GEN AI Engineer Agentic 7–9 | Unique Occupational (Cutshort) |
| **1 LPM** contract | Copilot Studio | VGreenTEK; Kasmoprav ₹1.30 LPM + GST |

### 12-month planning bands (INFERENCE, not an offer)

| Use | Cash CTC |
|---|---|
| Stay (6.9% hike) | **₹11.5–12.2 L** |
| Same-title external | ₹12.5–15 L |
| **Underwrite adjacent success** | **₹14–18 L** |
| Stretch GCC AIOps/SRE if interviews clear | ₹18–25 L (planning); ₹18–28 L stretch |
| Do **not** underwrite as year-1 base | **>₹30 L** / TeamLease ₹58–60 L specialists / Google L5 TC ₹112.1 L |
| Downside if junior GenAI IC accepted | **₹7–12 L** |

**Anchor script (RECOMMENDATION):** “Current CTC ~₹11 L cash, 8.5 years enterprise ops on a US telco account. I am not a fresher GenAI. Target **₹16–18 L** for an AIOps/Copilot/ITSM-AI IC in Hyd/Chennai/BLR hybrid; I will walk from ₹10 L caps and ₹6–8 L GenAI Engineer pages.”

---

## PART 14 — Resume strategy

**Forbidden (BGV-lethal):** “GenAI Engineer, 8.5 years” · “8 years LangChain” · “Prompt Engineer, 8 years.”  
Cognizant prints **Experience 4–13 / Relevant 2+** on the same line.

**Headline (RECOMMENDATION):**

> Service Desk Lead → Applied GenAI / AIOps | 8.5 yrs enterprise IT ops (Cognizant / T-Mobile) | Building RAG, ITSM copilots, agent workflows

**YOE formula on the résumé:** Total IT **8.5 years**. Relevant GenAI **N months** (count from first public repo / internal PoC). Never merge them.

**Skills order:** ITSM/incident leadership → Python/FastAPI → RAG/LangGraph → Azure OpenAI → Docker/evals. Java and SQL **absent** unless a single tool mention is strictly true.

**Proof section:** 2–3 bullets from OpsCopilot with metrics (golden-set %, cost/100 tickets, HITL gate). Zero Coursera as the lead.

---

## PART 15 — LinkedIn strategy

- Same headline as Naukri.  
- About: 8.5 years running major incidents / SLAs on T-Mobile via Cognizant → now building eval-gated ITSM copilots. **Ask for AIOps / Copilot / Now Assist conversations, not “open to AI Engineer fresher roles.”**  
- Featured: GitHub + 60-second demo.  
- Posts: one architecture note per artefact (chunking failure, HITL, cost) — not “day 47 of #100DaysOfAI.”  
- Open-to-work: India + Hyderabad/Chennai/Bengaluru/Pune/NCR + Remote; title filters **AIOps, Copilot, AI Operations, Generative AI** — not Prompt.  
- Recruiter Boolean you *want* to match: `(AIOps OR "Copilot Studio" OR "Now Assist" OR LangGraph) AND (ITSM OR ITIL OR incident) AND Python`.

---

## PART 16 — Certifications (ROI)

**Community verdict (independent):** SuperSourcing 2 Jun 2026 — *no cert verifies production GenAI; GitHub + scenario questions do.* OwnYourCareer 15 Aug 2026 — *if the posting does not name the cert, it is optional.*

| Cert | Verdict | Why |
|---|---|---|
| **Ship repo first** | **Do now** | Only reliable verification |
| ITIL 4 Foundation | **Keep/renew if lapsed** | Door 2 table stakes; ₹8.5–12k exam |
| **AI-103** Azure AI Apps and Agents | **Later / if Azure JDs dominate saved list** | AI-102 **retired 30 Jun 2026**; AI-103 is the live associate |
| **CSA** | **Later / only if SN-dev path** | $300; mandatory on SN build JDs; skip if no PDI/Glide |
| AIF-C01 AWS AI Practitioner | **Optional cheap keyword** | $100; not what Infosys wrote (they wrote Bedrock) |
| Hugging Face Agents Course | **Do the course, ship a Space, skip the PDF** | Free |
| LangChain Academy | **Labs only** | N≈0 India JDs requiring the new cert |
| AI-900 / AI-102 | **Skip — retired Jun 2026** | |
| MLS-C01 | **Skip — retired 31 Mar 2026** | |
| AIP-C01 / CKA / Databricks / Snowflake / Google ML Eng | **Skip 90 days** | Wrong stack or cost |
| Prompt-only certificates | **Skip** | 2023 residue |
| AB-620 / GH-600 | **Skip unless a named JD requires** | Too new; GH-600 beta noted not in India in one Hub post |

**90-day cert spend cap:** ₹0–₹20,000.

---

## PART 17 — Career-switcher intelligence (A6)

**Headline:** Insufficient independently verified evidence of a Service Desk Lead ~8.5 YOE (Coimbatore or close) landing an **external** AI Engineer title **with disclosed CTC**.

| Pattern | What the file actually contains |
|---|---|
| **Internal high-YOE** | Surender Arumugam, CTS Chennai, 18+ mainframes → Sr GenAI Manager after night projects + manager pitch |
| **Local Coimbatore AI title** | Sriram, graphic designer 5 YOE → AI Engineer at App Innovation Technologies (institute story) |
| **Vendor testimonials** | DataMites placement **~35% ±10% within 4 months** — their own disclaimer |
| **Failures** | Applying to GenAI without production proof; YOE mismatch; client-round rejects; fake Google/22-YOE claims on institute blogs |
| **Ops→MLOps analogue** | Support→SRE→platform is a **skills-overlap thesis**, not a Coimbatore placement proof |
| **External AI Engineer offers in the file** | Freshers, 1–5 YOE, or unnamed 2.5 YOE developers — **opposite** of “8.5 YOE desk lead walks into 25 LPA GenAI” |

**RECOMMENDATION:** Copy Surender’s **process** (night artefacts + internal pitch), not his title or YOE. Do not buy a course because a Coimbatore graphic designer got a local SME AI title.

---

## PART 18 — Job-search operating system

### Daily (weekday, ~90–120 min besides the build)

| Block | Minutes | KPI |
|---|---:|---|
| Build (repo) | 60–90 | Commits with tests |
| JD triage | 15 | 3 JDs read; 0–1 saved if first 10 bullets match |
| Applications | 15 | Only H1 ops-flavor / Copilot / TMUS / named CTS |

### Weekly

| Activity | KPI |
|---|---|
| Applications submitted | **8–12 quality**, not 80 spray |
| Internal/account conversation | 1 (HRBP / TMUS / IOA) |
| Artefact demo | 1 README or GIF update |
| Tracker hygiene | Status: saved / applied / rejected / interview |

### Funnel (INFERENCE targets, not industry benchmarks)

| Stage | 90-day target | Kill criteria |
|---|---|---|
| JDs read | 80–100 | First 6 bullets = CUDA/Java/SQL-first/PhD |
| Saved H1 | 25 | Pay < ₹11 L without stretch skill |
| Applied | 20–30 | Spray GenAI Engineer on desk CV |
| Recruiter screens | 6–10 | — |
| Tech loops | 3–5 | — |
| Offers | **1 adjacent** is success | Accepting ₹6–10 L junior IC |

**90-day notice** at Cognizant is community-standard — disclose on screen 1. Start internal + TMUS **now** because notice eats H1.

### City / hybrid (A8)

| Fact | Number |
|---|---|
| CBRE Dec 2025 AI-tagged Naukri share | BLR 25.4%, NCR 24.8%, Mum 19.2%, Hyd 12.5%, Pune 9.6%, Chennai 6.4% |
| Numbeo Coimbatore COL / rent | 17.6 / 3.5 (page 20 Aug 2026) |
| vs Bengaluru | ~20.5% cheaper excl. rent; rent ~59.4% lower |
| CTS Coimbatore | 3-day WFO (community + prior addendum); Madukkarai vs KGISL-SEZ Saravanampatti commute |
| Chennai | Nearest real metro; **relocate, do not weekend-commute** (~500 km) |
| Hybrid | Default 2026 policy is hybrid bait, not true remote. Naukri Remote GenAI ~167 |

---

## 90-day week-by-week plan

| Week | Skills | Project | Interview | Network | Applications | Deliverable |
|---:|---|---|---|---|---|---|
| 1 | Python venv, pytest, FastAPI hello | Repo skeleton + 20 synthetic incidents | — | Map TMUS tools; HRBP 30 min | 0 spray; save 10 H1 JDs | Headline live on Naukri/LinkedIn |
| 2 | Azure OpenAI chat + system prompt | `POST /summarize` | Even/odd + prime drill | Account AI bot / Tess question | 2 AIOps ops-flavor if honest fit | pytest green |
| 3 | Chunking reading | Ingest pipeline | “What is RAG?” out loud | 1 CTS Copilot/SN owner | 2 | MVP README |
| 4 | Embeddings + Chroma/FAISS | `/ask` v0 | Chunking types | — | 2 Copilot/AIOps | First citations |
| 5 | Hybrid search + “I don’t know” | Golden set n=15 | Vector DB pros/cons | Chennai/Hyd GCC scout | 2 | Eval table v0 |
| 6 | Prompt injection + PII story | Incident Copilot v1 freeze | Project walkthrough | — | 2 | Demo GIF 1 |
| 7 | LangGraph tutorial **on your data** | Agent plan node | Agents vs RAG | TMUS JD re-read | 2 | Graph diagram |
| 8 | Tool calling + HITL | Approve/reject path | Sev1 story → agent assist | — | 3 | P1 cannot auto-close |
| 9 | Docker | Compose one command | Cost/latency | Recruiter screens if any | 3 | Docker README |
| 10 | Copilot Studio sandbox **or** SN REST | Side artefact | Copilot vs LangGraph “when” | Internal pitch #2 | 3 | Second demo |
| 11 | Evals + cost dashboard | Flagship freeze | Client-round application Q | — | 4 | Flagship v1 tag |
| 12–13 | AI-103 **only if** Azure-heavy list; else apply | Bugfix + blog post | Mock loop (RAG + HITL + ITIL) | Referrals | 4–6 | **2 public artefacts + 20–30 quality apps** |

---

## Final decision matrix

| Path | 0–6 mo shortlist | 12-mo cash if it happens | 36-mo if it compounds | Verdict |
|---|---|---|---|---|
| Stay SDL | High | ₹11.5–12.2 L | ₹13–15 L | Shelter, not strategy |
| Internal AI (CTS/TMUS) | Med if artefacts | ₹13–17 L (N=0 offer letters) | Relevant months start | **Highest EV H1** |
| External AIOps ops-flavor | High if filter bullets | ₹12–18 L services; ₹18–28 L GCC **INFERENCE** | ₹18–24 / ₹24–38 | **Best external door** |
| External GenAI IC | Low now; Med day 60–90 | ₹14–22 with portfolio; ₹7–14 junior | Identity rewrite | **H2, not day-1 spray** |
| GCC (TMUS first) | High on-account | Undisclosed; plan ₹18–28 if clear | ₹24–38 | **Best named GCC door** |
| Product/FAANG | Very low | Those jobs’ TC, not your EV | Career rewrite | Watchlist |

---

## MY 2026 CAREER STACK

| Layer | Choice |
|---|---|
| **Title to hunt** | AIOps Engineer → Copilot Studio Engineer → TMUS AI Support/Ops |
| **Title to grow into** | GenAI / Agentic / LLMOps **after** N months of artefacts |
| **Cloud** | **Azure first** (OpenAI + Copilot). Bedrock month 3 if Infosys/AWS list grows |
| **Language** | Python. Not Java. SQL literacy only |
| **Orchestration** | LangGraph (HITL). LangChain only as sibling |
| **Retrieval** | RAG + one local vector DB + citations |
| **ITSM** | Process fluency you already have + REST; Glide only if SN-dev |
| **Proof** | OpsCopilot on synthetic data + evals |
| **Cert** | Repo ≫ ITIL keep ≫ AI-103 maybe ≫ CSA maybe |
| **City** | Stay CBE if internal/hybrid AIOps; else Hyd (TMUS/GCC) or Chennai (CTS) before BLR same-CTC |
| **Pay underwrite** | ₹14–18 L first switch; walk from <₹11 L AI titles |
| **Honesty** | 8.5 years **IT ops**. Relevant GenAI = months |

---

## DO THIS / DON’T DO THIS

**Do this**

- Rewrite headline today.  
- Map T-Mobile tools this week.  
- Build on synthetic data.  
- Filter JDs by first 10 bullets (ITSM/ITIL/observability/Copilot vs CUDA/Java).  
- Count relevant GenAI in **months**.  
- Apply to EY/Accenture/HPE/CGI/CDK/TMUS/CTS Copilot-shaped seats.  
- Keep 90-day notice visible.

**Don’t do this**

- “8.5 years AI Engineer.”  
- Spray 200 Infosys GenAI links on a desk CV.  
- Accept TCS 2–7 L / SysTechCorp 10 L / Prompt ₹5 L.  
- Lead with Java, SQL warehouses, or CKA.  
- Fine-tune 300 PDFs.  
- Weekend-commute Coimbatore–Chennai.  
- Pay for retired exams (AI-102, MLS-C01).  
- Put real client tickets on GitHub.

---

## NEXT 10 ACTIONS (this week)

1. Change Naukri + LinkedIn headline to the allowed line in Part 14.  
2. Write the T-Mobile tool list (Splunk / Dynatrace / SNOW / SolarWinds / PagerDuty / Tess — yes/no/unknown).  
3. Book 30 minutes with Coimbatore HRBP / T-Mobile account lead: IOA, Copilot, Now Assist, Frontier, TMUS Hyd AI ops. Volunteer as **domain owner + builder**.  
4. Create GitHub repo `ops-copilot` with `synthetic/` and a pytest skeleton.  
5. Get an Azure OpenAI or OpenAI API key; ship `POST /summarize` in 7 days.  
6. Save 15 live H1 JDs (AIOps ops-flavor, Copilot Studio, Now Assist, TMUS) into a tracker — URLs from `MASTER-india-ai-jd-corpus.tsv` filtered by family.  
7. Do **not** apply to Infosys/TCS “GenAI Engineer 6–10 AI/ML + 2 years agents” until artefact v1 exists.  
8. Walk through Deloitte even/odd + prime in a notebook so live coding cannot freeze you.  
9. Confirm ITIL status (hold / lapsed). If lapsed, renew Foundation; do not start CSA yet.  
10. Calendar-block 12 hours this week for the build. If the lead job only allows 8, still start.

---

## Appendix A — Hostile / pay-cut flags (corpus)

- TCS Naukri GenAI Hyd/BLR 4–8 yrs **2–7 Lacs PA**  
- SysTechCorp AIOps Bengaluru 6+ **max 10 LPA**  
- APAS.AI remote Agentic **$1,500–$2,500** (unit unclear)  
- iSoftStone Copilot card **50,000 P.A.** — treat as Naukri data error  
- Infosys/Cognizant/TCS Glassdoor estimates ₹5–10 L — **not employer CTC**  
- Luxoft “8+ years AI/ML”; Infosys “6–10 AI/ML + 2+ agentic” — **hostile formulas, skip until artefacts exist**  
- TestUnity ₹4.5–5 L; Prompt Indeed avg ₹4.95 L (n=12)

## Appendix B — File index

```
C:\Users\manoj\ai-career-intel-2026\
  RESEARCH-SUMMARY-REPORT-AUG-2026.md          ← this file
  AI-CAREER-TRANSITION-INTELLIGENCE-REPORT-2026.md
  research\
    A0–A8 dossiers
    W1-A1-role-fit-scoring.md
    W1-A2-jd-mining.md
    W1-A2-JD-CORPUS-MASTER.md                  ← 455-row markdown inventory
    jd-raw\
      MASTER-india-ai-jd-corpus.tsv / .csv
      SKILL-FREQ.json
      naukri-genai.tsv
      naukri-ops-copilot.tsv
      other-boards.tsv
      services-gcc.tsv
```

**End of summary.** Research window 16–24 August 2026. Zero fabricated YOE. Zero fabricated offer letters. Unique JD N=455 is a capture ceiling under anti-bot boards, **not** the size of the India AI market.
