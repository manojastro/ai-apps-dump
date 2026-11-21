# W1-A2 — Massive JD Mining — August 2026

**Agent:** Wave 1 Agent 2 (JD mining engine).  
**Access window:** 2026-08-23 (this harvest) plus A3 corpus captured the same day.  
**Persona:** Manoj Kumar — Service Desk Lead / IT Ops, Cognizant T-Mobile, Coimbatore, ~₹11 LPA, **8.5 YOE total IT**. No fabricated AI YOE. Python/GenAI/agents/RAG/AIOps first. Java/SQL **counted**, not led with.  
**Locations in scope:** Bengaluru, Hyderabad, Chennai, Pune, NCR, Coimbatore, Remote/Hybrid India.  
**Rule:** Zero fabrication. **VERIFIED FACT** = quoted or tightly extracted from a retrieved page or dated search-index snippet. If a URL 404s, expires, or login-walls, that is stated.

**Corpus size this file:** **85 inventory rows** (A3 JD01–JD50 refreshed + **35 new** JDs harvested 23 Aug 2026). **Full-body coded set N=52** (A3’s 37 full-body + 15 new pages with complete requirement text). PARTIAL/snippet rows stay labelled PARTIAL. Quality > invented volume.

---

## Method and harvest log

### What this pass did (do not duplicate A3 blindly)

1. Read `A3-jd-corpus.md`, `A1-job-market.md`, `A4-role-map.md`, `A7-skills-portfolio.md`.  
2. Re-opened high-signal A3 URLs (Infosys, TCS LinkedIn twin, Cognizant careers, Deloitte/EY/Hitachi/Convera/Google family via similar-jobs cards).  
3. Searched **new** titles: Agentic AI Engineer, Copilot Studio, Now Assist, ServiceNow Agentic, TMUS Engineer AI, LLMOps, AIOps, RAG Engineer, FDE, Coimbatore/Chennai.  
4. Preferred **LinkedIn public guest pages**, **employer careers**, **Shine**, **hirist**, **Glassdoor snippets**, **Naukri SERP cards**. Naukri listing URLs remain Akamai/302-fragile.

### Boards and career sites (23 Aug 2026)

| Source | What was opened | Result |
|---|---|---|
| LinkedIn guest `/jobs/view/{id}` | TCS 4407045907, CGI 4448458389, ServiceNow 4417470643, Siemens Energy 4409369794, Orion 4456093707, Cognizant 4415497554, Flexday, TOCUMULUS, BRATHON, Aivar, CGI, Infosys twins | **Best full-text.** Several IDs 302 to `expired_jd_redirect` (TMUS 4402223697, Cognizant 4415497554 guest, Optum 4387854369). Bodies for expired IDs taken from **Google/Bing-indexed LinkedIn snippets** and labelled **INDEXED-LIVE**. |
| Employer careers | Cognizant `00067173931` **LIVE**; Cognizant `00065789861` and `00068075121` **404**; Atos ServiceNow FDE **LIVE**; Vizuara openings **LIVE**; PepsiCo `452960` **JS shell (no JD body on fetch)**; PwC `724190WD` still **filled** (A3); Ecolab `R00295717` still **gone** (A3). |
| Shine | TMUS `Engineer,AI (Hyderabad)` **ACTIVELY HIRING** | Full body. |
| Naukri SERP / Google index | Agentic AI 9,938 (Aug 2026 title); AIOps 558; Coimbatore AIOps EY card 3–5 Yrs ₹8–15 LPA | Individual `job-listings-*` still 302/expired. SERP cards used as **PARTIAL**. |
| hirist | Engineering Lead Agentic AI, Coimbatore, 6–10 Yrs, posted 06 May 2026 | Search snippet had full requirements; direct page was a JS “Loading chat…” shell. **INDEXED-LIVE / PARTIAL page**. |
| Glassdoor | TCS Gen-AI/Agentic Chennai Job Id 388730; Qentelli SN Agentic ₹15–20 LPA | TCS body in snippet. Qentelli **Cloudflare-blocked** this pass; salary/body retained from **prior search snippet** (A4 already cited employer-provided ₹15–20 LPA). |
| Instahyre / Cutshort | JS walls | Existence-only; not in N=52. |

### Recency tags

| Tag | Meaning |
|---|---|
| **LIVE** | Public JD body retrieved 23 Aug 2026 (or employer careers still serving). |
| **INDEXED-LIVE** | Board/Google still showing the listing as current (~last 14–30 days) but the listing URL 302/expired/JS. Body from index snippet. |
| **RECENT-CLOSED** | “No longer accepting” / filled / 404; posted within ~6 weeks. |
| **OLDER** | Posted ~1–6 months; still readable. |
| **EXPIRED** | Explicitly expired / walk-in date past / careers 404. |

### Inclusion / exclusion

**In:** GenAI / Agentic / LLM / LLMOps / MLOps-with-LLM / AIOps / AI automation / RAG / Applied AI / Copilot Studio / Now Assist / ServiceNow Agentic / AI Support-Ops / FDE.  
**Out of full extract:** Pure Java/Spring + “plus ChatGPT”; unpaid internships aimed at students (red-flag section only).  
**Experience:** Prefer 6–12 YOE. Junior/red-flag JDs included when they disclose salary or show kitchen-sink vs LPA.

### Failed / blocked fetches (explicit)

- Naukri HTML GET: Akamai / empty JS shell (same as A1/A3).  
- LinkedIn `4402223697` (TMUS Engineer, AI) → `expired_jd_redirect`. Body from Shine twin + earlier Google snippet.  
- LinkedIn `4415497554` (Cognizant 7–13) → expired redirect. Body from Google snippet (A7 already quoted).  
- LinkedIn `4387854369` (Optum MCP) → expired redirect. Body from Google snippet.  
- PepsiCo careers `452960`: marketing shell, no JD. Body from earlier search-index of the same req.  
- Glassdoor Qentelli page: Cloudflare human-check.  
- hirist job `1633977`: JS shell.  
- Talent500 TMUS Principal Agentic: thin wrapper, no full JD.  
- Microsoft / Amazon / Zoho / Adobe / Salesforce / Oracle / Thoughtworks / Fractal / Tiger Analytics / Freshworks product GenAI IC: **still no full public IC body** this pass (ServiceNow product **was** captured).

### Harvest log (queries)

| # | Query / URL | Date | Used |
|---|---|---|---|
| 1 | LinkedIn “Generative AI Engineer India” | 23 Aug | Infosys, Recro, Goldman, WSP, Firstsource, Siemens Healthineers, Hired closed |
| 2 | LinkedIn “Agentic AI Engineer Bengaluru Hyderabad” | 23 Aug | TCS 4407045907 **LIVE**, CGI, Flexday, TOCUMULUS, Persistent 7–12, Infosys 6–10 closed |
| 3 | LinkedIn LangGraph Bengaluru | 23 Aug | Luxoft MCP, RoundCircle, Cognizant 7–13, Optum, Sandisk, Relanto, Red Hat, Wells Fargo, LTIMindtree closed |
| 4 | “Now Assist” / ServiceNow Agentic India | 23 Aug | Atos **LIVE**, ServiceNow Senior Staff **LIVE**, TEKsystems, Qentelli, PepsiCo Now Assist, Avensys, NOBL Q Vellore |
| 5 | TMUS / T-Mobile Engineer AI Hyderabad | 23 Aug | Shine **LIVE**; LinkedIn Support/Ops snippet; Principal 12–18 (SQL must-have chips) |
| 6 | Coimbatore / Chennai GenAI | 23 Aug | Orion **LIVE 2 days**; Aivar closed; NavaSys; COGNITBOTZ closed; Wellspring hirist; Naukri EY AIOps Coimbatore card |
| 7 | Copilot Studio India | 23 Aug | Siemens Energy **LIVE 21h**; BRATHON closed; TOCUMULUS closed; Lingaro/BMS similar-jobs cards |
| 8 | Vizuara openings + Cognizant careers | 23 Aug | Vizuara **LIVE**; Cognizant Chennai `00067173931` **LIVE** |
| 9 | Naukri agentic-ai-jobs / aiops-jobs | 23 Aug | Volume 9,938 / 558; PwC ITIL chip; ACS 20–27.5 LPA; Wissen 15–25 LPA |

---

## Inventory table (ALL JDs, one row each)

**Status column is 23 Aug 2026.** A3 IDs JD01–JD50 are the prior harvest, status refreshed. JD51+ are **new this pass**.

| ID | Company | Title | Location | Exp (as posted) | Posted / recency | Source | Status 23 Aug | Java? | SQL? | Adjacent vs core | Segment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| JD01 | Infosys | GenAI / Agentic AI Engineer | Bengaluru East | Naukri twin 6–11; LI chip Entry (unreliable) | ~1 week; still on guest page | LinkedIn 4416389669 | **LIVE** (refresh) | N | N | Adjacent | Services |
| JD02 | Infosys | Agentic AI Engineer | Bengaluru East | Mid-Senior; related 3–5 pan-India | 2 weeks | LinkedIn 4441390349 | **LIVE** | N | N | Adjacent→core-lite (LoRA) | Services |
| JD03 | Infosys | GEN AI Engineer | Bengaluru | 3–5 AI/ML | ~16 Aug Glassdoor | Glassdoor | **INDEXED-LIVE** | N | N | Core-YOE-in-AI | Services |
| JD04 | Infosys | Gen AI LLMOps Engineer | Bengaluru | 2–3 Yrs | Naukri 040826909325 | Naukri index | **INDEXED-LIVE** | N | N | Adjacent LLMOps | Services |
| JD05 | TCS | GEN AI Engineer | Bengaluru | Developer / junior | ~16 Aug | Glassdoor | **INDEXED-LIVE** | N | N | Adjacent junior | Services |
| JD06 | TCS | Agentic AI Engineer (text=Architect) | Hyd, Chennai, BLR | 8–12 Yrs; 3+ GenAI | Naukri 130826027970 | Naukri | **INDEXED-LIVE** | N | N | Adjacent architect | Services |
| JD07 | Accenture in India | LLM Operations Engineer | Pune PDC3C-SEZ | Min 3 Yrs LLMs; 15 yrs education | 3 days (A3) | LinkedIn 4456383755 | **LIVE** (similar-jobs still 2d) | N | N | Adjacent ops | Services |
| JD08 | Capgemini | Agentic with Azure AIFoundry | Bengaluru | 5+ overall, ≥1 yr AI | ~1 month | LinkedIn 4437769635 | **LIVE** | **Y (or .NET/Python)** | N | Adjacent | Services |
| JD09 | Deloitte USI | GEN AI Engineer SAM L40 | Hyd / BLR | SAM / not numbered | Req 353050 | Deloitte USI | **LIVE** (A3 careers; not re-404’d) | N | N | Adjacent eval | Services |
| JD10 | EY | AI Engineer Agentic + Azure Foundry | Bengaluru | **10+ Global IT**; 3+ ops | 4 days (A3) | LinkedIn 4432756779 | **LIVE** (similar-jobs 4d) | N (Py/C#/TS) | Implied stores | Adjacent | Services |
| JD11 | Persistent | Agentic AI Engineer | Hyd, BLR | 5–10 | Walk-in 9 May 2026 | Naukri | **EXPIRED walk-in** | N | N | Adjacent | Services |
| JD12 | Persistent | Senior AI OPS Engineer | Pune / all Persistent | Header 7–10; body 5–7 relevant | 2 days (A3) | LinkedIn 4453886301 | **LIVE** | N | N | Adjacent (GCP ADK) | Services |
| JD13 | HPE | DevOps, MLOps & GenAI Platform Owner IC | BLR Hybrid 2d/wk | TCP_04 | 2 weeks | LinkedIn 4450233534 | **LIVE** | **Y (w/ Python, Selenium)** | N | **Adjacent ITIL/SNOW** | Product/GCC-ish |
| JD14 | NXP | Software DevOps Engineer - for Gen AI | Bengaluru | 5+ SWE; 1+ LLM prod; 2+ DBMS | 2 weeks | LinkedIn 4390640553 | **LIVE** | **Y** | **Y** | Adjacent SWE+LLM | Product/GCC |
| JD15 | Qualys | ML Operations Engineer | Pune | 2–3 ML products | 4 days | LinkedIn 4417876201 | **LIVE** | N | N | **Core ML** | Product |
| JD16 | Hitachi Energy | AI Automation Engineer | Bengaluru | 5–10 SWE/AI | Pub 2026-08-18 | LinkedIn 4455774089 | **LIVE** (similar-jobs 3–4d) | Advantage | **Required** | Adjacent CSS/SNOW | Product/GCC |
| JD17 | Smart Working | LLM Systems / AI Agent Engineer [AS311] | Hyd / India remote | 5+ backend; 2+ prod agents | 4 days | LinkedIn 4452583680 | **LIVE** | N | **Postgres** | Adjacent agents | Product remote |
| JD18 | MyAdvice | AI Engineer I (Generative AI) | BLR / remote-first | 1–3 | Older; salary disclosed | LinkedIn 4430414644 | **LIVE** (older) | N | N | Mixed junior | Product |
| JD19 | StackNexus | GEN AI ENGINEER | Remote India, US hours | +5 Years | 4 months | LinkedIn 4403195999 | **OLDER** | N | N | Adjacent | Product/contract |
| JD20 | Hired (client) | AI Engineer - Generative AI (Remote) | Remote India | Senior unspecified | 3 weeks | LinkedIn 4446713048 | **RECENT-CLOSED** | N | **Y** | Adjacent | Unknown |
| JD21 | Ascendion | Lead Generative AI Engineer | BLR Bellandur | 5–12 SWE | Drive 11 Jul 2026 | LinkedIn cache | **EXPIRED drive** | N | N | Adjacent | Services |
| JD22 | Cirrus Labs | AI Engineer LangGraph/LangChain/RAG | Hybrid Hyd/BLR | 3–8 | Naukri 1 day (A3) | Naukri | **INDEXED-LIVE; URL expired** | N | **SQL tools** | Adjacent | Services/startup |
| JD23 | 360DigiTMG (payments client) | GenAI Engineer Agentic & RAG | Bengaluru | 4–8; 1–2+ GenAI | 1 week | Naukri | **INDEXED-LIVE; URL expired** | N | N | Adjacent | Product via staffer |
| JD24 | Stamford / Infinity | GenAI / Agentic AI Engineer | Hybrid Hyd, Chennai, BLR | **10–18** | 2 weeks | Naukri | **INDEXED-LIVE** | N | DBs | Adjacent | Services |
| JD25 | Cognizant | AI OPS / MLOPS Engineer | BLR Hybrid | 7–13; NP imm–90d | Pub 18 May 2026 | Careers 00068075121 | **EXPIRED 404** | N | N | Core MLOps | Services |
| JD26 | Allianz Technology | AI Operations | Pune onsite | 2–6 | 2 Jun 2026 | TAL | **EXPIRED** | N | **SQL/NoSQL** | Adjacent SNOW/SRE | GCC |
| JD27 | IRIS Software | MLOps AIOps GCP Lead | Noida Hybrid | 8–9 / 8–10 | ~3 days Foundit | Foundit | **INDEXED-LIVE; fetch failed** | N | Unk | Adjacent platform | Product/IT |
| JD28 | Zealant (CLM client) | AI Engineer (Agentic) | Bengaluru | 3+ SWE, 1+ LLM prod | 1 month | LinkedIn 4439984153 | **LIVE** | N | N | Adjacent strict | Staffing→product |
| JD29 | ApTask | Agentic AI Engineer Azure/RAG/LangGraph | Pune/BLR/Bhopal | 6+ SWE/AI | 5 days | LinkedIn 4452561905 | **LIVE** | N | **SQL/NoSQL** | Mixed LoRA+RAG | Staffing |
| JD30 | BNP Paribas | Agentic AI & DevOps | BLR / Mumbai | 7–9+; 5+ DevOps/AI, 2+ LLM agents | 2 weeks | LinkedIn 4448761124 | **LIVE** | N | N (CMDB) | **Adjacent IT-ops assistants** | GCC/Bank |
| JD31 | UST | AI Engineer | Bengaluru | 3–5 ML/AI; ≥1 yr agents | 1 week | LinkedIn 4441090818 | **LIVE** | N | “Data layer” | Adjacent | Services |
| JD32 | Tech Mahindra | Agentic AI Engineer | Pune, BLR | 5–10 | 3 days | Naukri 190826025169 | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent | Services |
| JD33 | HCLTech | Agentic AI Engineer | Noida, Hyd, BLR | 4–9 | 5 days | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Mixed PyTorch | Services |
| JD34 | Altimetrik | Gen AI Engineer | Hybrid Hyd, Chennai, BLR | 5–10 | 2 days | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Mixed TF+RAG | Services |
| JD35 | HP | AI and Automation Developer | Bengaluru | Typically 5–7 | 2 weeks | LinkedIn 4449084177 | **LIVE** | Knowledge-list | N | Adjacent JIRA/SNOW | Product |
| JD36 | Convera | Agentic AI Engineer (ITSM & Ent. Automation) | Pune | 3+ AI / AI Ops | 4 days | LinkedIn 4455712445 | **LIVE** | **JS required** (not Java) | N | **Best ITSM first-screen** | Product |
| JD37 | Google Cloud | GenAI Forward Deployed Engineer | Mumbai / Pune / BLR | **8 years** cloud or customer-facing | 1 week | LinkedIn 4451133303 | **LIVE** | N | N | Mixed elite | Product |
| JD38 | PwC | Agentic AI Engineer | Hybrid Hyd, BLR | 6–9 | 2 days | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent (ITIL chip) | Services |
| JD39 | PwC | AI Engineer | Hybrid Hyd, BLR | 5–9; ≥4 | 4 days | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Mixed Node/React | Services |
| JD40 | PwC AC | Gen AI Engineer Senior Associate | Bangalore | — | Careers 724190WD | PwC TA | **RECENT-CLOSED filled** | — | — | — | Services |
| JD41 | ADP | Walk-in Gen AI Engineer | Hybrid Hyd | 3–8 | Walk-in **25 Aug 2026** | Naukri | **LIVE walk-in PARTIAL** | Unk | Unk | Adjacent agentic | Product/GCC |
| JD42 | Blackstraw.ai | Walk-in Generative AI Engineer | Chennai WFO | 2–6 | Walk-in **24 Aug 2026** | Naukri | **LIVE walk-in PARTIAL** | Co-posts Java FS | Unk | Mixed CV+RAG | Product |
| JD43 | DXC | AI Engineer (Generative AI) | Hyd/BLR/Chennai/Kol/Noida | 5–10 | 1 day | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent Azure/FAISS | Services |
| JD44 | Cognizant | AI Engineer | Hybrid BLR, Pune, Chennai | 6–11 | 4 days | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Unk | Services |
| JD45 | Wissen | SRE AI Engineer | Hybrid BLR, Pune, Mumbai | 5–9; **15–25 Lacs PA** | 1 day | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent SRE+AI | Services |
| JD46 | Advance Career Solutions | Agentic AI Engineer | Hybrid BLR, Hyd, Pune | 8–13; **20–27.5 Lacs PA** | 1 day | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent | Staffing |
| JD47 | Qentelli | AI Engineer LLM/Chatbot/RAG | Hyderabad | 6–11 | 1 day | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent LangGraph/LLMOps | Services |
| JD48 | Tekskills (client) | Gen AI Engineer | BLR/Hyd/Pune | 4–8 / 6–11 | 1 day | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Mixed | Staffing |
| JD49 | Ecolab | Lead AI Engineer | Bengaluru | 8–10 and 2–6 cards | Naukri vs careers | Ecolab + Naukri | **CAREERS EXPIRED** | Unk | Unk | Adjacent SN chip | Product/GCC |
| JD50 | Infosys | Agentic AI Engineer pan-India | Hybrid Hyd, Chennai, BLR + | 3–5 | 5 days | Naukri | **INDEXED-LIVE PARTIAL** | Unk | Unk | Adjacent | Services |
| **JD51** | **TCS** | **Agentic AI Engineer** | **BLR, Chennai, Hyd, Pune, Mumbai** | **5+ Years** | **3 weeks; 200+ applicants** | **LinkedIn 4407045907** | **LIVE NEW** | N | N | Adjacent + RPA/SRE | Services |
| **JD52** | **CGI** | **Software Engineer-Agentic AI Engineer** | **Hyderabad** | **6- Years**; Bachelors + min 3 relevant | **2 weeks; 200+** | **LinkedIn 4448458389** | **LIVE NEW** | N | **Y (Python, SQL, Pandas)** | Mixed DE+agents | Services |
| **JD53** | **TMUS Global Solutions** | **Engineer, AI (Hyderabad)** | **Hyderabad** | **7 to 11 Yrs; 7+ SWE** | **Shine “3 weeks” / “ACTIVELY HIRING”** | **Shine 19352130** | **LIVE NEW** | **Y or Python (both preferred)** | N | Adjacent platform/MCP | **GCC (T-Mobile)** |
| **JD54** | **TMUS Global Solutions** | **Engineer, AI (Support/Operations)** | **Hyderabad** | Bachelor’s + 3 yrs **or** 2–4 in listed skills | LinkedIn 4402223697 guest **expired** | Google snippet + A4 | **INDEXED-LIVE NEW** | Unk | Unk | **Adjacent AI-agent ops** | GCC |
| **JD55** | **Atos** | **Forward Deployed AI Engineer – ServiceNow** | **Mumbai / Chennai / Bangalore** | **7+ years ServiceNow platform** | Pub **Jul 28, 2026**; careers live | Atos 1409487633 | **LIVE NEW** | **JS/Glide (not Java)** | N | **Adjacent Now Assist** | Services |
| **JD56** | **Cognizant** | **GEN AI Engineer** | **Chennai Hybrid** | **Minimum of 3+ years of related experience** | Pub **Jul 24 2026** | Careers 00067173931 | **LIVE NEW** | N | DB design | Mixed (TF/PT listed) | Services |
| **JD57** | **Vizuara** | **Agentic AI Engineer** | **Pune in-person** | 3+; CTC **INR 18 LPA** | Closes 30 May 2026 on page header; page live | openings.vizuara.ai | **LIVE NEW** | N | N | Adjacent MCP/eval | Product |
| **JD58** | **ServiceNow** | **Senior Staff AI-Native SWE – Agentic Systems** | **Bengaluru** | **8+ years SWE**; production agents | **1 day ago; 200+** | LinkedIn 4417470643 | **LIVE NEW** | **Plus (Go/Java/C++)** | N | Core-product agentic | Product |
| **JD59** | **Siemens Energy** | **GenAI / Copilot Senior Developer** | **Gurugram; remote 2d/wk** | **6–8 years total IT; 1–2+ Copilot Studio** | **21 hours; 200+** | LinkedIn 4409369794 | **LIVE NEW** | N | N | **Adjacent Copilot** | Product/GCC |
| **JD60** | **BRATHON** | **Microsoft AI Engineer (Copilot Studio)** | **Remote; travel Hyd; US evenings** | **2–5 years** Power Platform/AI/Automation | 4 months; **No longer accepting** | LinkedIn 4405444251 | **RECENT-CLOSED NEW** | N | N | Adjacent Copilot | Staffing |
| **JD61** | **TOCUMULUS** | **Copilot & Agentic AI Engineer** | **Chennai preferred / Bangalore** | **3–8 years** | 4 months; **No longer accepting** | LinkedIn 4403937705 | **RECENT-CLOSED NEW** | N | DBs | Adjacent Copilot/ITSM | Services |
| **JD62** | **Flexday AI** | **AI Engineer, Agentic AI (India)** | **Remote; prefer BLR or Gurgaon** | **2 to 5+ years** Python SWE | 4 months; **No longer accepting** | LinkedIn 4403974923 | **RECENT-CLOSED NEW** | N | N | Adjacent FDE-ish | Product/services |
| **JD63** | **Aivar Innovations** | **Senior AI Engineer – Agentic & LLM Reasoning** | **Coimbatore** | **6+ yrs**; 2 openings | 6 months; **No longer accepting** | LinkedIn 4375632410 | **RECENT-CLOSED NEW** | N | N | Mixed (fine-tune must) | Product/startup |
| **JD64** | **NavaSys Technologies** | **AI Engineer – GenAI, Agentic AI and MLOps** | **Coimbatore** | **3+ years AI/ML** | “5 days” on one crawl; “4 weeks” on another; 179 applicants | LinkedIn 4442345026 | **INDEXED-LIVE NEW** | N | N | Mixed/core-lite | Product/startup |
| **JD65** | **COGNITBOTZ** | **Agentic AI Engineer** | **Chennai 5d WFO; 2PM–11PM IST** | **5 Years** | 3 weeks; **No longer accepting** | LinkedIn 4425595723 | **RECENT-CLOSED NEW** | N | N | Adjacent LangGraph mandatory | Services |
| **JD66** | **Optum India** | **AI/ML Engineer – LangChain, LangGraph and MCP** | **Bengaluru** | **6+ years total**; 15+ yrs education | Guest **expired** | Google snippet | **INDEXED-LIVE NEW** | N | N | Adjacent MCP | GCC |
| **JD67** | **Qentelli** | **ServiceNow Agentic AI Consultant** | **Hyderabad Hybrid** | **6–8 Years**; **₹15–20 LPA employer** | Glassdoor crawl | Search snippet (page CF-blocked) | **INDEXED-LIVE NEW** | **JS/Glide** | N | **Adjacent Now Assist** | Services |
| **JD68** | **TEKsystems Global Services** | **ServiceNow AI Developer / Engineer** | **Hyd/BLR Hybrid; NP imm–15 days** | **5+ SN; 3+ config; 1+ Now Assist** | LinkedIn 4427505026 | Search snippet | **INDEXED-LIVE NEW** | **JS** | N | Adjacent Now Assist | Services |
| **JD69** | **PepsiCo** | **AI Solutions and Platforms Operations Engineer** | **Hyderabad** | **3–5+ SWE; 1+ GenAI preferred** | Careers 452960 JS; body from index | PepsiCo + search | **INDEXED-LIVE NEW** | N | N | **Adjacent Agent Ops Center** | GCC |
| **JD70** | **PepsiCo** | **Developer – DEEx AI Search / NowAssist** | India (DEEx) | SN Developer + Now Assist | Bayt “4 days ago 2026/07/19” | Bayt | **INDEXED-LIVE NEW** | **JS** | N | Adjacent Now Assist | GCC |
| **JD71** | **Goldman Sachs** | **Engineering Division – GenAI and DocAI Associate** | **Hyderabad** | **5+ years hands-on AI/ML** | 1 week; 200+ | LinkedIn 4303600155 | **INDEXED-LIVE NEW** | N | N | Mixed (fine-tune+RAG) | GCC/Bank |
| **JD72** | **WSP in India** | **AI/ML Engineer – Generative AI** | **Bengaluru** | **3–5 AI/ML; 1–2 GenAI** | 4 days; 200+ | LinkedIn 4390952132 | **INDEXED-LIVE NEW** | N | N | Mixed PT+RAG | Services |
| **JD73** | **Siemens Healthineers** | **Generative AI Engineer** | **Bengaluru** | **3–5; min 3 SWE** | 1 week; 200+ | LinkedIn 4374278638 | **INDEXED-LIVE NEW** | N | N | Adjacent agents/FastAPI | Product/GCC |
| **JD74** | **Recro** | **Generative AI Engineer** | **Bengaluru** | Unspecified; card **₹45.00–₹55.00** (likely LPA) | 2 days | LinkedIn similar-jobs | **LIVE PARTIAL NEW** | Unk | Unk | Unk | Staffing |
| **JD75** | **HYrEzy Tech Solutions** | **Senior AI Engineer (Applied LLM / Agentic)** | **Bangalore; JST overlap** | **4–6 Years; Budget 35–50 LPA** | LinkedIn 4365914924 | Search snippet | **INDEXED-LIVE NEW** | N | N | Adjacent applied (not research) | Staffing |
| **JD76** | **Relanto** | **Full Stack AI Engineer** | **Bengaluru** | Hands-on ship LLM features | 3 months | LinkedIn 4416166583 | **OLDER NEW** | N | **NL2SQL / Postgres** | Adjacent evals | Product/services |
| **JD77** | **Luxoft** | **Senior Python AI Engineer (LangGraph, MCP)** | **Bengaluru** | **8+ years of experience in AI/ML development** | “57 minutes ago”; 200+ | LinkedIn 4395224289 | **INDEXED-LIVE NEW** | N | N | **Core “8+ AI/ML” wording** | Services |
| **JD78** | **Sandisk** | **Senior AI Developer (LangGraph agents 8 to 11 years)** | **Bengaluru** | **7–10 years SWE** with AI/ML | LinkedIn 4404089765 | Search snippet | **INDEXED-LIVE NEW** | N | N | Adjacent prod agents | Product/GCC |
| **JD79** | **Wells Fargo** | **Lead SWE – Python, Agentic AI, LangChain, ML** | **Bengaluru** | **12+ years SWE; 1+ years GenAI/Agentic** | LinkedIn 4392933451 | Search snippet | **INDEXED-LIVE NEW** | N | N | Adjacent (12 IT + 1 GenAI) | GCC/Bank |
| **JD80** | **Red Hat** | **Senior ML Engineer – GenAI/LLM, LangGraph, Python/Golang** | **Bengaluru** | Unspecified; 140 applicants 2 weeks | LinkedIn 4376714403 | Search snippet | **INDEXED-LIVE NEW** | **Y (Python/Java AI libs)** | N | Mixed platform | Product |
| **JD81** | **LTIMindtree** | **Gen AI/Agentic AI – Python, RAG, Prompt Engg.** | **PAN India** | **4–16 Years** | 2 weeks; **No longer accepting** | LinkedIn 4424656585 | **RECENT-CLOSED NEW** | N | N | Mixed kitchen-sink TF/PT | Services |
| **JD82** | **RoundCircle** | **GenAI Engineer – AI Agents, LangGraph & RAG** | **Bengaluru** | **3–5; at least 1 year enterprise GenAI** | LinkedIn 4424185456 | Search snippet | **INDEXED-LIVE NEW** | N | N | Adjacent | Product/services |
| **JD83** | **Workfall** | **AI Engineer (RAG & Multi-Agent)** | **Bengaluru** | **5–10+ overall; >1 year Agentic** | LinkedIn 4411006315 | Search snippet | **INDEXED-LIVE NEW** | Spring AI listed as OR | N | Adjacent MCP/A2A | Product |
| **JD84** | **Cognizant** | **AI Engineer Python, LangChain, LangGraph…** | **Bangalore** | **7 to 13 years; NP Immediate to 90 days** | Guest expired; snippet “1 week” | LinkedIn 4415497554 | **INDEXED-LIVE NEW** | N | DBs | Adjacent | Services |
| **JD85** | **Digital India / NeGD** | **MLOps Engineer (contractual)** | **Delhi** | 1 post; last date **23 Aug 2026** | dic.gov.in | Govt careers | **LIVE (closing today)** | N | N | Core MLOps | Govt |
| **JD86** | **Jobgether (partner)** | **Senior AIOps Engineer – Observability & Automation** | **Remote anywhere India** | Not numbered; SL1 + SNOW ITOM | Posted **Jul 22, 2026** | jaabz.com | **INDEXED-LIVE NEW** | N | N | **Adjacent AIOps** | Staffing/contract |
| **JD87** | **Ecolab** | **AI Operations and Optimization Analyst** | **Pune** | Unspecified analyst | **15 hours; 200+** | LinkedIn 4389918410 | **LIVE NEW** | N | N | Adjacent ops (not builder) | Product/GCC |
| **JD88** | **Infosys** | **Agentic AI Engineer** | **Bengaluru East** | **6–10 AI/ML; at least 2+ agentic/LLM apps** | 2 weeks; **No longer accepting** | LinkedIn 4447672179 | **RECENT-CLOSED NEW** | N | N | Mixed (“AI/ML engineering”) | Services |
| **JD89** | **Persistent** | **Agentic AI Engineer** | **Pune, Bengaluru** | **7 to 12 Years**; 7+ overall, 2+ GenAI | 6 days; 45 applicants | LinkedIn 4405968489 | **INDEXED-LIVE NEW** | N | N | Adjacent | Services |
| **JD90** | **TCS** | **Gen-AI/Agentic AI Engineer** | **Chennai** | Developer; Glassdoor est. **₹5L–₹7L** | ~16 Aug 2026; Job Id **388730** | Glassdoor | **INDEXED-LIVE NEW** | N | N | Adjacent junior/comp trap | Services |
| **JD91** | **Orion Innovation** | **GenAI Engineer** | **Coimbatore** | **5–8 years** AI and SWE | **2 days ago; 127 applicants** | LinkedIn 4456093707 | **LIVE NEW** | N | **Y (SQL + JSON)** | Adjacent Python/RAG | Services |
| **JD92** | **Avensys Consulting** | **ServiceNow AI Engineer** | **Remote; hybrid hours** | **7+ SWE; 2+ AI/LLM** | Posted 29 Jun 2026 | ZipRecruiter snippet | **INDEXED-LIVE NEW** | N | N | Adjacent Now Assist/MCP | Staffing |
| **JD93** | **NOBL Q** | **ServiceNow Agentic AI Engineer** | **Vellore, IN** | SN + JS | 6 days (Talent.com) | Talent.com | **INDEXED-LIVE NEW** | **JS/Glide** | N | Adjacent | Staffing |
| **JD94** | **Equinix** | **Staff Agentic AI Engineer** | **Bengaluru** | Staff (not numbered on card) | 2 days | LinkedIn similar-jobs | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent/staff | Product/GCC |
| **JD95** | **Highbrow Technology** | **Agentic AI / Automation Engineer** | **Hyderabad** | Card **₹12–21 LPA** | 2 weeks | LinkedIn people-also-viewed | **INDEXED-LIVE PARTIAL NEW** | Unk | Unk | Adjacent | Staffing |
| **JD96** | **Accenture in India** | **AI / ML Engineer** (and LLM Architect / AI Infra Architect clones) | **Coimbatore** (also BLR/Hyd) | Template; education 15 yrs typical | 2 weeks | LinkedIn similar-jobs flood | **LIVE PARTIAL NEW** | Unk | Unk | Keyword-thin | Services |
| **JD97** | **Bristol Myers Squibb** | **Senior AI Copilot Engineer** | **Hyderabad** | Unspecified on card | 1 day | LinkedIn similar-jobs | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent Copilot | GCC |
| **JD98** | **Lingaro** | **Power Platform AI Engineer + Copilot Studio** | **India** | Unspecified | 2 days | LinkedIn similar-jobs | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent Copilot | Services |
| **JD99** | **Wellspring Consultancy (client)** | **Engineering Lead – Agentic AI Engineering** | **Coimbatore** | **6–10 Years** | Posted **06/05/2026** | hirist 1633977 | **INDEXED-LIVE NEW** | N | N | Mixed lead+hands-on | Staffing→product |
| **JD100** | **MantriAI (search partner)** | **ML & LLM Ops Software Engineer** | **Remote India → BLR later** | **4 to 12 years total; ≥2.5 ML systems**; **₹30–45 LPA** | 3 weeks; **No longer accepting** | LinkedIn 4447780207 | **RECENT-CLOSED NEW** | N | N | Core MLOps/on-prem GPU | Product |
| **JD101** | **Nesoi AI** | **Agent Engineer \| AI** | **Remote India; US hours** | Hands-on owner; **Pay: 45 LPA (20 Base)** | 4 months | LinkedIn 4404328855 | **OLDER NEW** | N | N | Adjacent agents/evals | Product |
| **JD102** | **(unnamed) Contract** | **Generative AI Platform Engineer (Contract Remote)** | **Remote India** | **2–5 years** | LinkedIn 4438328240 | Search snippet | **INDEXED-LIVE NEW** | N | **PostgreSQL** | Adjacent FastAPI/RAG | Contract |
| **JD103** | **Firstsource** | **Generative AI Engineer / AI Systems Engineer IC** | **India** | Unspecified IC | 3 weeks; 200+ | LinkedIn 4390136254 | **INDEXED-LIVE NEW** | N | **SQL/NoSQL** | Adjacent Bedrock | Services |
| **JD104** | **BharatGen** | **Generative AI Engineer** | **Mumbai MMR** | **2 to 5 years applied ML** | 1 week; 200+ | LinkedIn 4453076575 | **LIVE NEW** | N | N | **Core foundation-model training** | Product |
| **JD105** | **Integra Global Solutions** | **Agentic AI Developer** | **Coimbatore** | **1–3 years**; Glassdoor est. ₹1–6L | 30d+ | Glassdoor Coimbatore SERP | **INDEXED-LIVE PARTIAL NEW** | N | DBs | Adjacent junior | Services |
| **JD106** | **Bosch** | **AI Expert – Generative AI Solutions Developer** | **Coimbatore** | Unspecified; est. ₹8–9L | 30d+ | Glassdoor | **INDEXED-LIVE PARTIAL NEW** | N | DBs | Adjacent GenAI lifecycle | Product |
| **JD107** | **Ventragate Technologies** | **AI/ML Engineer (GenAI & Agentic Systems)** | **Coimbatore** | **2–3 years** AI/ML shipping GenAI | Indeed | Indeed | **INDEXED-LIVE NEW** | N | N | Mixed LoRA+agents | Startup |
| **JD108** | **AXIORA / Work Booster AI** | **Gen AI Engineer – Fresher / Internship** | **Chennai on-site** | Fresher; stipend **₹5,000/mo**; FTE **₹15,000/mo** | 6 months | LinkedIn 4373663484 | **OLDER RED-FLAG NEW** | N | N | Junior intern | Startup |
| **JD109** | **DeepReachAI** | **AI Engineer (LLMs, RAG & AI Agents) Remote** | **India remote** | “You don’t need years”; **₹10,000/month** | LinkedIn 4442888187 | Search snippet | **INDEXED-LIVE RED-FLAG NEW** | N | Postgres | Underpaid | Startup |
| **JD110** | **Ananda / Ladder** | **AI Automation Engineer – LangChain & RAG** | **Remote** | Unspecified; **₹25,000–₹40,000/month** | LinkedIn 4296071346 | Search snippet | **INDEXED-LIVE RED-FLAG NEW** | N | N | Adjacent | Startup |
| **JD111** | **Hire Feed** | **Generative AI Engineer (Remote)** | **Remote India** | Task/hourly **USD $30–$50**; SQL + 2 languages | 3 months; **No longer accepting** | LinkedIn 4413296181 | **RECENT-CLOSED RED-FLAG NEW** | **Y (or Py/JS/Go)** | **Y** | Task work | Marketplace |
| **JD112** | **techjays** | **AI Lead Developer** | **Coimbatore** | Unspecified; card **₹30–50 LPA** | 5 months | LinkedIn similar-jobs | **OLDER PARTIAL NEW** | Unk | Unk | Unk | Product/startup |
| **JD113** | **SourcingXPress** | **Senior Artificial Intelligence Engineer** | **Coimbatore** | Card **₹5–18 LPA** | 1 month | LinkedIn | **INDEXED-LIVE PARTIAL NEW** | Unk | Unk | Unk | Staffing |
| **JD114** | **YMinds.AI** | **Agentic AI Engineer (3–5 Yrs Immediate Joiner Remote)** | **Bengaluru / remote** | 3–5 | 4 days | LinkedIn similar-jobs | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent | Startup |
| **JD115** | **ADP** | **Generative AI Engineer** | **Hyderabad** | Unspecified on CGI similar-jobs card | 2 weeks | LinkedIn similar-jobs | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent | Product/GCC |
| **JD116** | **PwC Acceleration Centers** | **AI/GenAI Engineer** | **Hyderabad** | Unspecified | 1 week | LinkedIn similar-jobs 4451639025 | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent | Services |
| **JD117** | **Qualcomm** | **Agentic AI Engineer / Senior Engineer** | **Greater Hyderabad** | Unspecified | 2 weeks | LinkedIn people-also-viewed 4449109607 | **INDEXED-LIVE PARTIAL NEW** | Unk | Unk | Unk (not the C++ SDK JD) | Product |
| **JD118** | **Novonesis** | **Copilot Studio Engineer** | **Bengaluru** | Unspecified | 1 week | LinkedIn similar-jobs 4442639158 | **LIVE PARTIAL NEW** | Unk | Unk | Adjacent Copilot | Product/GCC |
| **JD119** | **H2O.ai** | **AI Engineer – Forward Deployed** | **India** | Unspecified | 5 days | LinkedIn similar-jobs 4455301818 | **LIVE PARTIAL NEW** | Unk | Unk | Mixed FDE | Product |
| **JD120** | **Contract / platform (see JD102)** | — | — | — | — | — | Duplicate of JD102 | — | — | — | — |

**Inventory count:** 119 unique rows (JD120 is a duplicate marker, ignore). **Full-body extracts:** A3 JD01–JD37 family + new JD51–JD65, JD56, JD57, JD58, JD59, JD91, plus long snippets JD66–JD73, JD77–JD84, JD86, JD88–JD89, JD92, JD99, JD100, JD103–JD104, JD107. **PARTIAL-only:** remaining. **Do not treat PARTIAL as full extracts.**

Naukri **market-volume (not a JD, from A1/A3, still current 23 Aug):** Generative AI Engineer 11,132; Genai Engineer 7,709; Agentic AI 9,938; LangChain 4,122; RAG 6,876; LLMOps ~678 (Jul title); AIOps **558**. Bengaluru GenAI engineer ~3,139; Hyd 1,707; Pune 1,262; NCR 993.

---

## Full extracts (quotes + URLs)

A3 JD01–JD50 full quotes live in `C:\Users\manoj\ai-career-intel-2026\research\A3-jd-corpus.md`. This section **refreshes** those that changed and **quotes every NEW JD** with a retrieved body. Must-have vs good-to-have kept verbatim.

### Refresh notes on A3 LIVE set (23 Aug)

- **JD01 Infosys** still **LIVE** on https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669 — same must-haves (Python OOP/pytest, Bedrock, RAG, LangChain/LangGraph, Docker/CI).  
- **JD07/JD10/JD12/JD16/JD17/JD30/JD36/JD37** still appearing in LinkedIn similar-jobs as 2–4 days / 1 week. Treat as **still LIVE unless a later crawl 404s**.  
- **JD25 Cognizant MLOps 00068075121** remains **404**. Replacement live IC: **JD56** Chennai GenAI + **JD84** 7–13 LangGraph (guest expired, snippet live).  
- **JD40 PwC AC 724190WD** remains filled. New PwC AC card **JD116** Hyderabad AI/GenAI Engineer is PARTIAL existence only.

---

### JD51 — TCS — Agentic AI Engineer — **LIVE NEW**

- **Location:** Bangalore, Chennai, Hyderabad, Pune, Mumbai.  
- **Exp:** **5+ Years**. Seniority chip Mid-Senior.  
- **Posted:** 3 weeks ago; Over 200 applicants.  
- **URL:** https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-tata-consultancy-services-4407045907  
- **Access:** 2026-08-23. Recency: **LIVE**.  
- **Salary / degree / NP / mode:** Not disclosed. Full-time.  
- **Wording:** Skills list, **not** “8+ years of AI research”. RPA + Datadog/SRE is unusual and **adjacent**.

**VERIFIED FACT — job description (verbatim bullets):**  
> “Strong experience with LLMs, prompt engineering, and agent frameworks (LangChain, AutoGen, CrewAI).”  
> “Deep understanding of MCPs, ReAct, Tree of Thought, and AutoGPT-style reasoning.”  
> “Hands-on with Python, OpenAI APIs, Anthropic Claude, Vector DBs (FAISS, Pinecone, Weaviate).”  
> “Experience with A2A orchestration, agent memory strategies, and tool calling.”  
> “Proven integration experience with RPA platforms like UiPath, Automation Anywhere, or Blue Prism.”  
> “Familiarity with SRE/observability tools such as BigPanda, Datadog, Grafana, or New Relic.”  
> “Experience with cloud platforms (Azure, AWS, GCP) and MLOps pipelines.”

**VERIFIED FACT — Nice-to-Have:**  
> “BFSI domain expertise…”  
> “Knowledge of LLMOps, agent observability, and feedback loops.”  
> “Familiarity with Azure AI Studio, AWS Bedrock, or GCP Vertex AI.”

**Skill flags:** Python Y; LangChain Y; LangGraph N (AutoGen/CrewAI); OpenAI Y; Azure OpenAI NTH; Bedrock NTH; Vertex NTH; RAG implied via vector DBs; agents Y; **MCP Y**; eval NTH (LLMOps observability); FastAPI N; Docker N; K8s N; CI-CD N; **ITSM N**; **Splunk N**; **Datadog Y**; PagerDuty N; ITIL N; Copilot Studio N; Power Automate N; RPA Y. **Java N. SQL N.**

**8+ AI vs 8+ IT + skills:** **5+ Years** overall; AI skills listed, not “5 years of model training”.  
**First-screen for Service Desk Lead + portfolio:** **Maybe → Yes** if resume shows Python agents + one observability tool (Datadog/Grafana) + optional RPA. Kitchen-sink (MCP + ToT + RPA + SRE) is recruiter stuffing; still the **Datadog/BigPanda** line is a real ops wedge. **Chennai listed.**

---

### JD52 — CGI — Software Engineer-Agentic AI Engineer — **LIVE NEW**

- **Location:** Hyderabad. Position ID **J0626-1358**.  
- **Exp:** Header **“Experience: 6- Years”** (truncated); education “Bachelor's … **minimum 3 years of relevant experience**.” LI chip wrongly “Entry level”.  
- **Posted:** 2 weeks; 200+ applicants.  
- **URL:** https://in.linkedin.com/jobs/view/software-engineer-agentic-ai-engineer-at-cgi-4448458389  
- **Access:** 2026-08-23. **LIVE**.

**VERIFIED FACT (verbatim):**  
> “Must be strong in Azure Foundry/AWS Bedrock related agentic automation implemetation”  
> “Build AI agents capable of reasoning, planning, memory management, and autonomous task execution”  
> “Should have hands on workflow configuration in Azure Foundry/AWS Bedrock”  
> “Hands on data engineering development experience in Hadoop, and Hive interface”  
> “Excellent in data engineering using Python, SQL , Pandas”  
> “Develop multi agent workflows using frameworks such as LangChain, LangGraph, MCP Server or Semantic Kernel”  
> “Design Retrieval Augmented Generation (RAG) pipelines for context aware AI responses”  
> “Develop scalable backend services and APIs to support AI agent operations”  
> “Monitor agent performance, reliability and response quality”

**Java N. SQL: REQUIRED** (“Excellent in … SQL”). Hadoop/Hive is a **hard adjacent miss** for a service-desk profile unless portfolio includes data pipelines.  
**First-screen:** **No** unless SQL+Hadoop is honest. Filter cost of skipping SQL: **this JD dies**.

---

### JD53 — TMUS Global Solutions — Engineer, AI (Hyderabad) — **LIVE NEW**

- **Location:** Hyderabad. **7 to 11 Yrs** (Shine highlights). Body: **7+ years SWE** distributed/cloud-native.  
- **URL:** https://www.shine.com/jobs/engineerai-hyderabad/tmus-global-solutions/19352130  
- **Access:** 2026-08-23. Shine: **ACTIVELY HIRING**. LinkedIn twin 4402223697 **expired guest**.  
- **Degree:** Bachelor’s CS/SWE/IS or equivalent practical experience.

**VERIFIED FACT — What You'll Do (verbatim):**  
> “Design and develop agent orchestration frameworks and execution engines supporting complex AI-driven workflows.”  
> “Design and implement Model Context Protocol (MCP) integrations and frameworks that enable secure, scalable access to enterprise tools, APIs, data sources, and agent capabilities.”  
> “Architect microservices and event-driven systems that integrate AI reasoning with enterprise systems such as customer, billing, network, and support platforms.”  
> “Collaborate with AI/ML engineers to integrate foundation models, retrieval systems, evaluation frameworks, and agent capabilities into production platforms.”  
> “Drive platform reliability, scalability, observability, and performance across high-volume AI workloads.”

**VERIFIED FACT — What You'll Bring:**  
> “7+ years of software engineering experience building distributed systems and cloud-native applications.”  
> “Strong proficiency in Python or Java, with working knowledge of both preferred.”  
> “Experience with cloud-native technologies, including containers, Kubernetes, and service-based architectures.”

**VERIFIED FACT — Must Have Skills:**  
> “Python software engineering”  
> “Distributed systems, APIs, and microservices”  
> “LLM, AI service, and conversational platform integration”  
> “Cloud-native architecture, containers, and Kubernetes”  
> “Software architecture and technical leadership”

**VERIFIED FACT — Nice-to-Have:** MCP, vector DBs, evaluation frameworks, voice/real-time.

**Java: YES as co-equal with Python (“or Java, both preferred”).** Must-have block leads with **Python**. SQL N.  
**Wording is 7+ SWE + LLM integration, not 7 years of training.**  
**First-screen:** **Maybe**. Same employer as Manoj’s account (T-Mobile / TMUS GS Hyderabad). Bar is **platform SWE** (K8s, microservices, MCP), not service-desk. Internal referral still the strongest door; resume must show Python services + MCP/RAG artefact, not ticket metrics alone.

---

### JD54 — TMUS Global Solutions — Engineer, AI (Support/Operations) — **INDEXED-LIVE NEW**

- **Location:** Hyderabad. LinkedIn ID 4402223697 guest **expired** 23 Aug.  
- **Exp (snippet):** “Bachelor's Degree plus 3 years of related work experience OR advanced degree with 1 year … OR combination … deemed equivalent” plus “2-4 years of Experience in below mentioned skills”.  
- **Evidence:** Google/LinkedIn snippet captured 23 Aug (also A4).

**VERIFIED FACT (verbatim from snippet):**  
> “Engineer, AI (Support/Operations) at T-Mobile monitors, maintains, and optimizes production AI agents and enterprise AI systems to ensure high availability, performance, and reliability”  
> “supporting deployed AI solutions including LLM-based applications, Agentic workflows, and Retrieval-Augmented Generation (RAG) pipelines through incident response, troubleshooting, performance tuning, and operational monitoring”  
> “Supporting and troubleshooting production AI/ML systems, including monitoring, alerting, and incident response”  
> “Experience with enterprise AI platform administration, configuration management, and operational tooling using Python or similar languages”

**First-screen:** **Yes / highest TMUS fit.** This is the **AI-agent operations** twin of service-desk: incident response, monitoring, RAG/agent reliability. **Do not confuse with JD53 (build/platform).** Java/SQL not in captured snippet.

---

### JD55 — Atos — Forward Deployed AI Engineer – ServiceNow — **LIVE NEW**

- **Location:** **Mumbai / Chennai / Bangalore**. Ref 548487. Pub date on page **Jul 28, 2026** (header also showed Jun 29 on an earlier crawl).  
- **Exp:** **7+ years of relevant ServiceNow platform development**.  
- **URL:** https://jobs.atos.net/job/Bangalore-ServiceNow-forward-deployed-AI-engineer/1409487633/  
- **Access:** 2026-08-23. **LIVE on employer careers.**

**VERIFIED FACT — responsibilities:**  
> “Implement intelligent workflows using Now Assist, GenAI Skills, AI Agents, AI Search Predictive Intelligence, Flow Designer, Virtual Agent”  
> “Configure workflows, business rules, client scripts, UI policies, script includes, catalogs, and integrations.”  
> “Develop integrations using REST/SOAP APIs, IntegrationHub, MID Server”

**VERIFIED FACT — required:**  
> “7+ years of relevant ServiceNow platform development experience with expertise in intelligent workflow automation, enterprise integrations, CMDB/CSDM implementations, and AI-powered ServiceNow capabilities.”  
> “Expertise in JavaScript Glide APIs Flow Designer Script Includes Business Rules Client Scripts UI Policies”  
> “Experience with Now Assist GenAI Skills AI Agents / Agentic Workflows AI Search Predictive Intelligence”  
> “Familiarity with A2A and MCP-based AI integration approaches is an advantage.”

**Certs preferred:** CSA, CAD, CIS, Data Foundation CMDB/CSDM, micro-certs AI/GenAI.

**Java N (JavaScript/Glide). SQL N.** Python N.  
**First-screen:** **Maybe**. Domain (ITSM, CMDB, incident) is a feature. **Hard gate is 7+ years ServiceNow development**, which a Cognizant T-Mobile **service desk lead** typically does **not** have unless they scripted SN. Do **not** apply as “GenAI Engineer” without SN artefacts. **Chennai listed.** Title says FDE but body is SN platform + Now Assist.

---

### JD56 — Cognizant — GEN AI Engineer — Chennai Hybrid — **LIVE NEW** (employer careers)

- **Job:** 00067173931. Pub **Jul 24 2026**. Hybrid Chennai.  
- **URL:** https://careers.cognizant.com/india-en/jobs/00067173931/gen-ai-engineer-cognizant/  
- **Exp:** **“Minimum of 3+ years of related experience.”** Any Bachelor’s/Master’s CS/DS/ML.  
- **Note:** Sister req `00065789861` (A4 “4 to 13 / Relevant 2+”) **404** this pass.

**VERIFIED FACT — requirements (verbatim):**  
> “Minimum of 3+ years of related experience.”  
> “Experience in implementing LLMs and Generative AI models, including Prompt Engineering, Retrieval Augmented Generation (RAG); and Agent based Architecture (AgenticAI).”  
> “Proficiency in programming languages such as Python.”  
> “Experience with machine learning frameworks and libraries, particularly LangChan, LangGraph, TensorFlow, PyTorch, Keras etc.”  
> “Knowledge of Power BI and PowerAutomate would be a Plus.”  
> “Proficiency in database design and management.”

**Java N. SQL:** “database design and management” (not named SQL). TF/PT listed — services clone. Power Automate is **plus** (useful for Copilot path).  
**Wording is related experience, not 8.5 years AI.** Matches A4 “total vs relevant” doctrine.  
**First-screen:** **Maybe**. Internal Cognizant + Chennai (closest hub to Coimbatore). Resume must show Python + RAG + LangGraph **related** months, not 8.5 AI. Kitchen-sink TF/Keras is copy-paste.

---

### JD57 — Vizuara — Agentic AI Engineer — **LIVE NEW** (employer)

- **Location:** Pune, in-person. **3+ years**. CTC **INR 18 LPA**. Immediate start. Closes 30 May 2026 on header (page still serving 23 Aug — treat close date as possibly stale).  
- **URL:** https://openings.vizuara.ai/roles/agentic-ai-engineer  

**VERIFIED FACT:**  
> “You will own the ingestion pipelines, the agentic skills that maintain the knowledge base, the MCP servers that expose it to other systems, and the evaluation harnesses that grade every output the system produces.”  
> “You will write most of the code in Claude Code or OpenAI Codex”  
> “Working knowledge of Claude Code or OpenAI Codex as your daily driver. You have shipped at least one production system using them.”

Interview tests: context engineering, memory, **tool design and MCP**, Claude Code/Codex, inference/cost. **Java N. SQL N.**  
**First-screen:** **No** for first 90 days (in-person Pune + Claude Code production bar + 18 LPA may be below 8.5 YOE target after relocation). Useful as **eval/MCP language** for portfolio.

---

### JD58 — ServiceNow — Senior Staff AI-Native Software Engineer – Agentic Systems — **LIVE NEW**

- **Location:** Bengaluru. **1 day ago; 200+ applicants.**  
- **URL:** https://in.linkedin.com/jobs/view/senior-staff-ai-native-software-engineer-%E2%80%93-agentic-systems-at-servicenow-4417470643  
- **Exp:** **8+ years of software engineering**.

**VERIFIED FACT — core focus:**  
> “Agentic architecture. Design and ship multi-agent systems — orchestration, tool use, planning loops, memory, and failure recovery — that operate reliably in production, not in notebooks.”  
> “Enterprise-grounded reasoning. Build agents that leverage ServiceNow's data layer — CMDB, Workflow Data Fabric, and Knowledge Graph”  
> “Action Fabric opening our full system of action to any external agent via MCP”

**VERIFIED FACT — qualifications:**  
> “8+ years of software engineering with strong fundamentals in data structures, algorithms, and distributed systems.”  
> “Hands-on depth designing, shipping, and operating agentic systems in production — … Not prototypes.”  
> “Production-grade Python. Systems language (Go, Java, or C++) is a plus.”  
> “Familiarity with RAG and retrieval patterns in production”

**Java: plus, not must. SQL N.** CMDB named — domain overlap, **bar is Staff SWE at ServiceNow**.  
**First-screen:** **No.** Do not waste a week. Use quotes for **CMDB-grounded agents + MCP** in a portfolio narrative, not as an application target.

---

### JD59 — Siemens Energy — GenAI / Copilot Senior Developer — **LIVE NEW**

- **Location:** Gurugram. **Employees eligible for remote working arrangements up to 2 days per week.**  
- **Exp:** **6–8 years of total IT experience.** **1–2+ years** proven GenAI agent development, preferably Copilot Studio + Azure OpenAI Foundry.  
- **Posted:** 21 hours; 200+.  
- **URL:** https://in.linkedin.com/jobs/view/genai-copilot-senior-developer-at-siemens-energy-4409369794  

**VERIFIED FACT:**  
> “You will work as a Generative AI Agent Developer, designing and building custom Copilot agents using Microsoft Copilot Studio and Azure OpenAI Foundry.”  
> “6–8 years of total IT experience.”  
> “1–2+ years of proven experience in Generative AI agent development, preferably using Microsoft Copilot Studio and Azure OpenAI Foundry.”  
> “Hands-on experience with Microsoft Power Platform, including Power Apps and Power Automate.”  
> “Experience with Microsoft 365 and SharePoint integrations.”

**Java N. SQL N. Python N** (Power Platform path).  
**Wording is the canonical formula: 6–8 total IT + 1–2 Copilot.**  
**First-screen:** **Yes if Copilot Studio artefact exists**; **Maybe** without it (NCR relocation). Best **H1 Copilot** JD in this harvest. User-support consulting + RCA language maps to “analyze symptoms and identify root causes”.

---

### JD60 — BRATHON — Microsoft AI Engineer (Copilot Studio) — **RECENT-CLOSED NEW**

- Remote; occasional travel Hyderabad; **US timezone overlap (IST evenings)**; **2–5 years**.  
- **URL:** https://in.linkedin.com/jobs/view/microsoft-ai-engineer-copilot-power-platform-agent-developer-at-brathon-4405444251  
- Status: **No longer accepting applications.**

**VERIFIED FACT — must-have:** Copilot Studio “actual builds shipped to users”; Power Automate; M365; prompt engineering GPT-4/4.5; requirements gathering; REST/custom connectors. Example use case: **“Error resolution agent: OCRs screenshots of system errors… step-by-step troubleshooting in plain language.”**  
**First-screen if it reopens:** **Yes** — that use case is service-desk native. Closed this week’s apply list.

---

### JD61 — TOCUMULUS — Copilot & Agentic AI Engineer — **RECENT-CLOSED NEW**

- **Chennai (Preferred) / Bangalore. 3–8 years.**  
- **URL:** https://in.linkedin.com/jobs/view/copilot-agentic-ai-engineer-microsoft-ecosystem-at-tocumulus-4403937705  
- **No longer accepting.**

**VERIFIED FACT:** Copilot Studio + Power Platform; agents integrated with **ERP, CRM, ITSM**; Power Automate; Azure OpenAI RAG; Python / JavaScript / C#.  
**Chennai preferred.** Template for next Copilot req.

---

### JD62 — Flexday AI — AI Engineer, Agentic AI — **RECENT-CLOSED NEW**

- Remote; prefer Bengaluru or Gurgaon. **2 to 5+ years** Python. Fortune 500 FDE-style.  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-agentic-ai-india-at-flexday-ai-4403974923  

**VERIFIED FACT:**  
> “Communication and Stakeholder Management (Primary Requirement)”  
> “Agentic AI (Primary Technical Requirement)”  
> “Hands-on experience building agents using frameworks such as LangGraph, LangChain, OpenAI Agents SDK, Semantic Kernel, or equivalent (**professional or personal projects both count**)”  
> “Familiarity with Model Context Protocol (MCP) servers … is strongly preferred”

**First-screen if reopened:** **Maybe/Yes** because **personal projects count** and stakeholder management is primary. Closed.

---

### JD63 — Aivar Innovations — Senior AI Engineer — **Coimbatore — RECENT-CLOSED NEW**

- **Coimbatore. 6+ yrs. 2 openings.** 6 months old; not accepting.  
- **URL:** https://in.linkedin.com/jobs/view/senior-ai-engineer-agentic-ai-llm-reasoning-at-aivar-innovations-4375632410  

**VERIFIED FACT must-have:** LLM reasoning; multi-agent production; LangChain/CrewAI/AutoGen; **LLM Fine-Tuning**; **LangFuse / LangSmith**; advanced Python; LLM APIs (OpenAI, Anthropic, Bedrock); **MCP**.  
**First-screen:** **No** (fine-tune + 6+ AI-engineer identity + closed). **Existence proof Coimbatore has a 6+ YOE agentic employer.**

---

### JD64 — NavaSys Technologies — AI Engineer GenAI/Agentic/MLOps — **Coimbatore — INDEXED-LIVE NEW**

- **3+ years AI/ML.** 179 applicants. Recency 5 days vs 4 weeks across crawls.  
- **URL:** https://in.linkedin.com/jobs/view/ai-engineer-genai-agentic-ai-and-mlops-at-navasys-technologies-4442345026  

**VERIFIED FACT:**  
> “Develop and fine-tune Generative AI models (LLMs, Diffusion models).”  
> “3+ years of experience in AI/ML development.”  
> “Experience with Agentic AI frameworks (LangChain, AutoGPT, etc.).”

**First-screen:** **No** (YOE-in-AI/ML + fine-tune/diffusion). Local market noise.

---

### JD65 — COGNITBOTZ — Agentic AI Engineer — **Chennai — RECENT-CLOSED NEW**

- **Chennai 5 days WFO. Shift 2PM–11PM IST. Experience: 5 Years.**  
- **URL:** https://in.linkedin.com/jobs/view/artificial-intelligence-engineer-at-cognitbotz-4425595723  

**VERIFIED FACT must-have:** Python Advanced; Agentic AI & Multi-Agent; **LangGraph (Mandatory)**; LangChain; RAG & Vector DBs; FastAPI; OpenAI/Anthropic/Gemini; “Built and deployed at least **Two production-grade Multi-Agent AI application**”. Preferred: CrewAI, AutoGen, **MCP**, Neo4j, Docker, K8s.  
**Java N. SQL N.** Night-ish shift. Closed. Bar is **two production multi-agent apps** — not a first-screen for ops-only.

---

### JD66 — Optum India — AI/ML Engineer LangChain, LangGraph and MCP — **INDEXED-LIVE NEW**

- Bengaluru. Guest expired.  
- Snippet URL: https://in.linkedin.com/jobs/view/ai-ml-engineer-lang-chain-lang-graph-and-mcp-at-optum-india-4387854369  

**VERIFIED FACT:**  
> “B.Tech./MCA/Graduation (15+ years of formal education, Correspondence courses are not relevant)”  
> “6+ years of total experience”  
> “Hands-on expertise with: Lang Chain, Lang Graph and MCP (Model Context Protocol)”  
> RAG, vector storage, multi-agent, memory, tool-driven agents.

**Wording: 6+ total + MCP/LangGraph skills — not 6 years of AI research.** **First-screen:** **Maybe** with a real MCP server in GitHub. GCC. Java N. SQL N.

---

### JD67 — Qentelli — ServiceNow Agentic AI Consultant — **INDEXED-LIVE NEW**

- Hyderabad Hybrid. **6–8 Years. ₹15–20 LPA employer provided** (Glassdoor/A4). Page Cloudflare-blocked this pass.  
- Evidence: search snippet 23 Aug + A4.

**VERIFIED FACT:**  
> “Experience: 6–8 Years Location: Hyderabad Work Mode: Hybrid”  
> “Pay: ₹1,500,000.00 - ₹2,000,000.00 per year”  
> “ServiceNow Scripting (JavaScript, Glide APIs)”  
> “Virtual Agent and Conversational AI”  
> “Agentic workflows / autonomous agents”  
> “Now Assist”

**First-screen:** **Maybe** — pay band is a realistic step-up from ₹11 LPA **if** SN scripting is real. Java N. JS yes.

---

### JD68 — TEKsystems — ServiceNow AI Developer — **INDEXED-LIVE NEW**

**VERIFIED FACT (LinkedIn 4427505026 snippet):**  
> “Location: Hyderabad/Bengaluru Work Mode: Hybrid Notice Period: Immediate to 15 days only”  
> “5+ years of ServiceNow platform experience.”  
> “3+ years in ServiceNow configuration, scripting, and integrations.”  
> “1+ year of experience with Now Assist or AI capabilities.”  
> “Configure and deploy Now Assist AI capabilities and Moveworks integrations.”

**NP 15 days** is a hard gate for a employed lead. **First-screen:** **No** unless SN 5+ years is true.

---

### JD69 — PepsiCo — AI Solutions and Platforms Operations Engineer — **INDEXED-LIVE NEW**

- Hyderabad. Careers https://www.pepsicojobs.com/main/jobs/452960?lang=en-us fetched as **JS shell**. Body from search index of the same job.

**VERIFIED FACT:**  
> “The AI Observability Engineer (Agentic Frameworks & AI Agent Operations Center Developer) builds and operationalizes agentic AI solutions … and contributes to an AI Agent Operations Center”  
> “This role focuses on developing agent workflows (planning, tool execution, memory, and RAG), integrating guardrails and evaluations, and delivering operational capabilities such as run management, telemetry, and incident triage for production agents.”  
> “AI Agent Operations Center (70%): Build ‘operations center’ capabilities for agent runtime management: agent registry, versioning, deployment tracking, and run histories”  
> “Enable operational workflows such as incident triage, replay/debug runs, trace correlation, and root-cause analysis across agent steps”  
> “Experience: 3–5+ years of software engineering experience; 1+ years building and observe AI/ML or GenAI applications preferred”  
> “Hands-on experience with agentic frameworks (Crew.ai, LangChain, Semantic Kernel, AutoGen, or similar)”  
> “Proficiency in Python (primary)”  
> “Strong experience with RAG patterns”  
> “containerized deployments (Kubernetes/AKS/EKS)”

**Java N. SQL N.**  
**First-screen:** **Yes/Maybe** — **incident triage + RCA + agent ops** is the TMUS-ops twin at a GCC. Bar still wants Python + one agent framework + K8s familiarity. Hyderabad.

---

### JD70 — PepsiCo — Developer DEEx AI Search / NowAssist — **INDEXED-LIVE NEW**

Bayt https://www.bayt.com/en/india/jobs/developer-deex-ai-search-nowassist-servicenow-genai-74303169/ dated 2026/07/19.

**VERIFIED FACT:** Now Assist, AI Search, Virtual Agent; SN Developer; embeddings/semantic search; REST; ATF; preferred agentic AI. **JS/SN, not Python-first.**

---

### JD71 — Goldman Sachs — GenAI and DocAI Engineering Associate — Hyderabad — **INDEXED-LIVE NEW**

https://in.linkedin.com/jobs/view/engineering-division-genai-and-docai-engineering-associate-hyderabad-at-goldman-sachs-4303600155  

**VERIFIED FACT:**  
> “5+ years of hands-on experience in AI/ML development, with a proven track record of delivering end-to-end AI solutions”  
> “prompt engineering, fine-tuning, Retrieval Augmented Generation (RAG), and agentic frameworks.”

**First-screen:** **No** — 5+ **AI/ML development** clock.

---

### JD72 — WSP — AI/ML Engineer Generative AI — Bengaluru — **INDEXED-LIVE NEW**

https://in.linkedin.com/jobs/view/ai-ml-engineer-generative-ai-at-wsp-in-india-4390952132  

**VERIFIED FACT:**  
> “3–5 years of experience in AI/ML, with at least 1–2 years in Generative AI/LLMs/NLP.”  
> “Strong proficiency in Python, PyTorch, Hugging Face Transformers, LangChain/LlamaIndex.”  
> Guardrails, RAG on PDFs/Word/PPT, Azure AI.

**First-screen:** **No** (3–5 **in AI/ML**).

---

### JD73 — Siemens Healthineers — Generative AI Engineer — Bengaluru — **INDEXED-LIVE NEW**

https://in.linkedin.com/jobs/view/generative-ai-engineer-at-siemens-healthineers-4374278638  

**VERIFIED FACT:**  
> “We are seeking a Generative AI Engineer with 3-5 years of experience with strong background in developing agentic architectures”  
> “Hands-on experience with frameworks like Langchain and Langraph.”  
> “FastAPI, Flask, or Django REST Framework.”  
> “Minimum of 3 years of experience in software engineering or related fields.”  
> “Proven track record of developing generative AI applications.”

**Wording mixed: 3–5 GenAI vs min 3 SWE.** **First-screen:** **Maybe** if they honor SWE clock; FastAPI+LangGraph portfolio required.

---

### JD77 — Luxoft — Senior Python AI Engineer (LangGraph, MCP) — **INDEXED-LIVE NEW**

https://in.linkedin.com/jobs/view/senior-python-ai-engineer-langgraph-mcp-at-luxoft-4395224289  
Posted “57 minutes ago”; 200+.

**VERIFIED FACT:**  
> “8+ years of experience in AI/ML development.”  
> “Advanced proficiency in Python.”  
> “Experience with Agentic Workflows using LangChain-based agents.”  
> “Hands-on experience with LangGraph (e.g., hackathons or MCPs).”

**RED FLAG wording: 8+ years AI/ML.** **First-screen:** **No** without lying. Do not apply.

---

### JD78 — Sandisk — Senior AI Developer LangGraph — **INDEXED-LIVE NEW**

**VERIFIED FACT:**  
> “Bachelor's degree in Computer Science, Engineering, or related technical field”  
> “7-10 years of software development experience with demonstrated expertise in AI/ML technologies”  
> “Strong proficiency in Python with experience in asynchronous programming patterns”  
> LangGraph enterprise agents, ReAct, RAG.

**7–10 SWE + AI expertise, not 7–10 years training.** **First-screen:** **Maybe** (async Python bar).

---

### JD79 — Wells Fargo — Lead SWE Python Agentic — **INDEXED-LIVE NEW**

**VERIFIED FACT:**  
> “12+ years of overall software engineering experience with strong proficiency in Python for production-grade systems.”  
> “1+ years of hands-on experience building GenAI / Agentic AI solutions using Google ADK (GADK) or LangChain, LangGraph”

**Canonical 12 IT + 1 GenAI.** **First-screen:** **No** (12+ SWE; 8.5 under). Pattern still useful.

---

### JD80 — Red Hat — Senior ML Engineer GenAI — **INDEXED-LIVE NEW**

**VERIFIED FACT:** RAG pipelines; AutoGen, LangGraph, WatsonX; “LangGraph, LangChain, Autogen, WatsonX and/or **Python/Java-based AI libraries**”; enterprise copilots for **operational workflows**.  
**Java named.** Adjacent-ish ops copilots. **First-screen:** **Maybe** if Python path accepted.

---

### JD81 — LTIMindtree — Gen AI/Agentic PAN India — **RECENT-CLOSED NEW**

**4–16 Years.** Mandatory: Python, GenAI, Agentic, RAG, Prompt, AI/ML Deep Learning, TF/Keras/PT, LangChain, LlamaIndex, LangGraph, CrewAI, Docker, K8s. **Kitchen-sink 4–16 band.** Closed.

---

### JD82 — RoundCircle — GenAI Engineer LangGraph & RAG — **INDEXED-LIVE NEW**

**VERIFIED FACT:**  
> “3–5 years of experience in Machine Learning, Artificial Intelligence, or related software engineering roles.”  
> “At least 1 year of hands-on experience building enterprise Generative AI applications.”  
> LangGraph, CrewAI, AutoGen, or **PydanticAI**. Personal/professional not distinguished as Flexday was.

**First-screen:** **Maybe** via “related software engineering” + 1 year GenAI.

---

### JD83 — Workfall — RAG & Multi-Agent — **INDEXED-LIVE NEW**

**5–10+ overall, >1 year Agentic.** MCP servers, A2A, LangGraph/Strands. LangChain/LlamaIndex/Semantic Kernel/**Spring AI** OR-list. **Java via Spring AI optional.**

---

### JD84 — Cognizant — AI Engineer 7–13 YOE LangGraph — **INDEXED-LIVE NEW**

Guest expired. Snippet:

**VERIFIED FACT:**  
> “Role : AI Engineer Python, Langchain, LangGraph, Agentic AI, API, LLMs Location : Bangalore Experience : 7 to 13 years Notice Period : Immediate to 90 days”  
> “Design, develop, and deploy Agentic AI systems using Python”  
> “Build autonomous AI agents capable of planning, reasoning, and tool usage”  
> “Implement Retrieval-Augmented Generation (RAG) pipelines”  
> “Integrate LLMs with APIs, databases, and enterprise applications”

**7–13 overall + NP 90 days OK.** **First-screen:** **Maybe/Yes** internal + Python/RAG/LangGraph portfolio. Java N.

---

### JD85 — NeGD / Digital India — MLOps Engineer — **LIVE (closes 23 Aug 2026)**

https://dic.gov.in/jobs/mlops-engineer/ — 1 contractual Delhi post. CI/CD, model drift, observability. **Not a GenAI IC.** **First-screen:** **No** (govt MLOps, Delhi, 1 seat, closing today).

---

### JD86 — Jobgether — Senior AIOps Engineer remote India — **INDEXED-LIVE NEW**

https://jaabz.com/jobs/252920-aiops-engineer Posted Jul 22, 2026.

**VERIFIED FACT:** Fully remote India; SL1; **ServiceNow ITOM**; predictive analytics; AI-driven incident management; ITIL mentioned in skill chips.  
**First-screen:** **Yes** for H1 AIOps if SN ITOM/monitoring is honest.

---

### JD87 — Ecolab — AI Operations and Optimization Analyst — Pune — **LIVE NEW**

https://in.linkedin.com/jobs/view/ai-operations-and-optimization-analyst-at-ecolab-4389918410 — 15 hours; 200+.

**VERIFIED FACT:** Manage/optimize AI adoption; model training activities as **loading datasets/prompts**; daily AI operational performance. **Analyst, not engineer.** **First-screen:** **Maybe** as operations overlay, title/comp risk.

---

### JD88 — Infosys Agentic 6–10 + 2+ — **RECENT-CLOSED NEW**

https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-infosys-4447672179  

**VERIFIED FACT:**  
> “6–10 years of experience in AI/ML engineering, with at least 2+ years in building agentic AI systems or LLM-based applications.”

**This is the hostile formula** (“6–10 AI/ML”). Contrast JD01 (skills, no AI YOE clock). **First-screen:** **No**. Closed.

---

### JD89 — Persistent Agentic 7–12 — **INDEXED-LIVE NEW**

**VERIFIED FACT:**  
> “7+ years overall experience, with 2+ years in GenAI / LLM-based solutions”  
> “Location: Pune, Bengaluru Experience: 7 to 12 Years”  
> Python, LangChain, LangGraph, Crew, vector DBs, Streamlit, prompt libraries.

**7+ overall + 2+ GenAI.** **First-screen:** **Maybe** (2+ GenAI is the lie-risk; overall 7 matches).

---

### JD90 — TCS Chennai Gen-AI/Agentic — Glassdoor — **INDEXED-LIVE NEW**

https://www.glassdoor.co.in/job-listing/gen-ai-agentic-ai-engineer-tata-consultancy-services-JV_IC2833209_KO0,26_KE27,52.htm?jl=1009988712911  
Job Id **388730**. Est. **₹5L–₹7L** (**ESTIMATE, NOT EMPLOYER-DISCLOSED**).

**VERIFIED FACT:** Advanced Python; LangChain and LangGraph; AIML libraries. **Chennai.**  
**RED FLAG:** Agentic title + **₹5–7L estimate**. Not an 8.5 YOE target.

---

### JD91 — Orion Innovation — GenAI Engineer — **Coimbatore — LIVE NEW**

- **2 days ago; 127 applicants.** Mid-Senior.  
- **URL:** https://in.linkedin.com/jobs/view/genai-engineer-at-orion-innovation-4456093707  
- **Exp:** **5–8 years of relevant professional experience in AI and software development.**

**VERIFIED FACT — required (verbatim):**  
> “Mandatory:Proficiency in Python programming and FastAPI.”  
> “Expertise in langchain, prompt engineering, and retrieval-augmented generation (RAG).”  
> “Experience with Azure and AWS Bedrock cloud platforms.”  
> “Strong knowledge of REST API development and integration.”  
> “Hands-on experience with Git, Docker, SQL, and JSON.”  
> “Familiarity with AI tools such as Claude, GitHub Copilot, and Cursor.”  
> “Background in Agile development methodologies and agentic AI concepts.”  
> “5-8 years of relevant professional experience in AI and software development.”

Also: FastAPI, prompt/RAG, Azure/Bedrock, Docker, Git.

**Java N. SQL: YES (named with Git/Docker/JSON).**  
**First-screen:** **Maybe** — **only live full-body GenAI IC in Coimbatore this harvest.** Clock says “AI and software development” which recruiters may read as AI YOE. Stay-in-city option if Python+FastAPI+RAG+SQL literacy is real. Comp unknown.

---

### JD92 — Avensys — ServiceNow AI Engineer remote — **INDEXED-LIVE NEW**

**VERIFIED FACT:** 1-year extendable contract; Remote; **7+ years overall SWE, with 2+ years in AI / LLM / Generative AI**; Now Assist skills; RAG; AI Agents; **MCP servers** to expose ServiceNow; Claude skills/connectors.  
**First-screen:** **Maybe** (2+ GenAI + SN). Remote.

---

### JD99 — Wellspring / client — Engineering Lead Agentic — **Coimbatore — INDEXED-LIVE NEW**

https://www.hirist.tech/j/engineering-lead-agentic-ai-engineering-1633977 Posted 06/05/2026. **6–10 Years. Coimbatore.** Direct page JS.

**VERIFIED FACT (search snippet):** Hands-on lead; write code; architect; mentor 6–8 engineers; LLMs and agentic frameworks internals; ship production systems; preferred LangChain, LangGraph, vector DBs, Claude/OpenAI Agent SDK, MCP-adjacent “Agent Skills”, fine-tuning, RL, MLOps, Docker, K8s.  
**First-screen:** **No** (lead of 6–8 engineers + internals). Local senior demand exists.

---

### JD100 — MantriAI — ML & LLM Ops — **RECENT-CLOSED NEW**

**₹30–45 LPA**; remote → BLR end of 2026; **4 to 12 years total, at least 2.5 on ML systems in production**; vLLM/TGI/Triton/Ollama; on-prem GPU; NP 30–45 days. **Core MLOps.** **First-screen:** **No**.

---

### JD101 — Nesoi AI — Agent Engineer — **OLDER NEW**

**Pay: 45 LPA (20 Base)**; Remote India; US hours; owner of production agents, evals, POCs. Aggressive culture. **First-screen:** **Maybe** if US-hours OK and eval portfolio exists. 4 months old.

---

### JD102 — Contract GenAI Platform Engineer Remote India — **INDEXED-LIVE NEW**

**VERIFIED FACT:** 3–6 month contract; Remote India; **2–5 years**; Python, FastAPI, OpenAI, LangChain or LangGraph, RAG, **PostgreSQL**, Redis, Git; GTH AWS, Docker, pgvector/FAISS/Chroma.  
**SQL/Postgres yes.** Under-levelled for 8.5 unless contract fill.

---

### JD103 — Firstsource — Generative AI Engineer — **INDEXED-LIVE NEW**

Bedrock, SageMaker, Docker/K8s, RAG, embeddings, **SQL/NoSQL**, vector DBs, guardrails. **SQL yes.**

---

### JD104 — BharatGen — Generative AI Engineer — Mumbai — **LIVE NEW**

https://in.linkedin.com/jobs/view/generative-ai-engineer-at-bharatgen-4453076575  

**VERIFIED FACT:**  
> “Develop and train foundational generative AI models across modalities”  
> “Bachelor’s or Master’s … with 2 to 5 years of industry experience in applied machine learning or AI development.”  
> PyTorch/TF/HF/NeMo; DSPy, LangGraph, LangChain, LlamaIndex.

**CORE training. First-screen:** **No.**

---

### JD107 — Ventragate — AI/ML Engineer Coimbatore — **INDEXED-LIVE NEW**

Indeed `jk=139d07fd44b17dfa`. **2–3 years** AI/ML shipping GenAI; PyTorch/JAX/TF; LoRA/QLoRA; advanced RAG; agents. **First-screen:** **No** (junior + core).

---

### Red-flag extracts (short)

- **JD108 AXIORA Chennai intern:** stipend ₹5,000/month; FTE ₹15,000/month. **Unpaid-adjacent for “Gen AI Engineer” title.**  
- **JD109 DeepReachAI:** ₹10,000/month for RAG/agents/Python/FastAPI.  
- **JD110 Ladder:** ₹25–40k/month LangChain/RAG “full-time/contract”.  
- **JD111 Hire Feed:** $30–50/hr task work; **SQL + two languages (Python, JavaScript, Go, or Java)**.  
- **JD90 TCS Chennai:** Agentic + LangGraph with Glassdoor **₹5–7L**.  
- **JD05 TCS BLR:** Agentic + “eagerness to learn” + est. ₹5–8L (A3).  
- **JD77 Luxoft:** **8+ years AI/ML development** as mandatory.  
- **No “16–20 years RAG”** JD found this harvest. **Insufficient reliable evidence** for that specific meme in live India listings 23 Aug 2026.

---

## Skill frequency table (must-have vs mentioned)

**Denominator N=52** = A3’s 37 full-body JDs (JD01–JD31, JD35–JD37) **plus** 15 new full-page bodies: JD51 TCS LI, JD52 CGI, JD53 TMUS Shine, JD55 Atos, JD56 Cognizant Chennai, JD57 Vizuara, JD58 ServiceNow, JD59 Siemens Energy, JD60 BRATHON, JD61 TOCUMULUS, JD62 Flexday, JD63 Aivar, JD64 NavaSys, JD65 COGNITBOTZ, JD91 Orion.

**Must-have** = required / mandatory / “must have skills” / core qualifications. **Mentioned** = must-have + preferred/GTH/nice-to-have/knowledge-list.

| Skill / concept | Must-have count | Must-have % | Mentioned count | Mentioned % | Notes |
|---|---:|---:|---:|---:|---|
| Python | 42 | 81% | 45 | 87% | Exceptions must-have: Atos (JS), Siemens Energy (Copilot Studio), BRATHON (Copilot), TMUS “Python or Java”, Vizuara (Claude Code, Python unstated). |
| RAG / retrieval / embeddings / chunking | 36 | 69% | 41 | 79% | Still the dominant architecture word. Copilot JDs often imply knowledge sources instead. |
| Agents / Agentic / tool-calling / multi-agent | 45 | 87% | 48 | 92% | Title fashion; quality from Accenture 3-words to ServiceNow “not notebooks”. |
| LangChain | 28 | 54% | 34 | 65% | Default framework on services JDs. |
| LangGraph | 22 | 42% | 28 | 54% | **Mandatory** on COGNITBOTZ; co-equal on Infosys/Cognizant/CGI/Flexday/Aivar. |
| Vector DB (named store) | 18 | 35% | 26 | 50% | FAISS/Pinecone/Weaviate/Chroma/pgvector/Azure AI Search. |
| Prompt engineering | 24 | 46% | 32 | 62% | |
| Azure OpenAI / Foundry / Azure ML | 16 | 31% | 24 | 46% | CGI, Capgemini, EY, Hitachi, Siemens Energy, TOCUMULUS, Orion Azure. |
| AWS Bedrock / AWS | 12 | 23% | 20 | 38% | Infosys JD01 must; TMUS NTH; Orion must Azure **and** Bedrock. |
| OpenAI API / GPT explicit | 16 | 31% | 24 | 46% | |
| LlamaIndex | 5 | 10% | 8 | 15% | |
| CrewAI / AutoGen | 10 | 19% | 18 | 35% | TCS JD51 must AutoGen/CrewAI. |
| **MCP** | 8 | 15% | 16 | 31% | Must-ish: TCS JD51, CGI, TMUS NTH→body, Aivar, Flexday preferred, Vizuara, Hitachi A3, Convera A3, Google A3, ServiceNow product, Optum (outside N if strict). **Rising.** |
| Semantic Kernel / MS Agent Framework | 3 | 6% | 8 | 15% | |
| HuggingFace / Transformers | 4 | 8% | 8 | 15% | |
| Fine-tuning / LoRA | 8 | 15% | 14 | 27% | Aivar **must**; NavaSys must; most applied JDs optional. |
| Evaluation / LangSmith / Langfuse / LLM-as-judge | 12 | 23% | 22 | 42% | Discriminator on Deloitte/EY/Hitachi/Smart Working/Google/BNP/Vizuara/Aivar. |
| Guardrails / Responsible AI | 12 | 23% | 20 | 38% | |
| FastAPI / REST / microservices | 18 | 35% | 28 | 54% | Orion FastAPI **mandatory**. |
| Docker | 14 | 27% | 22 | 42% | |
| Kubernetes | 10 | 19% | 18 | 35% | TMUS must containers/K8s. |
| CI/CD | 16 | 31% | 24 | 46% | |
| MLOps / LLMOps named | 10 | 19% | 20 | 38% | |
| Vertex / GCP | 4 | 8% | 12 | 23% | |
| **ServiceNow / ITSM / Now Assist** | 6 | 12% | 12 | 23% | Atos, TEKsystems, Qentelli, PepsiCo Now Assist, Convera, HPE, Hitachi, HP, TOCUMULUS ITSM, Jobgether (if counted). Sparse, **high-signal**. |
| Copilot Studio / Power Automate / Power Platform | 3 | 6% | 6 | 12% | Siemens Energy, BRATHON, TOCUMULUS; Cognizant Power Automate plus. |
| Observability (Grafana, Prometheus, Dynatrace, ELK, OTel) | 6 | 12% | 12 | 23% | |
| **Datadog** | 1 | 2% | 2 | 4% | **TCS JD51 names Datadog** (A3 N=37 had 0). |
| **Splunk** | 0 | 0% | 0 | 0% | Still **absent** from N=52 full bodies. |
| **PagerDuty** | 0 | 0% | 0 | 0% | Absent. |
| ITIL | 2 | 4% | 5 | 10% | HPE; Allianz NTH; Jobgether chips; PwC PARTIAL chip. |
| Terraform / IaC | 4 | 8% | 8 | 15% | |
| Degree CS/Eng named | 18 | 35% | 24 | 46% | Accenture “15 years full time education”; Optum same. |
| Notice period named | 3 | 6% | 5 | 10% | Cognizant imm–90d; TEKsystems 15d; MantriAI 30–45d. |

**ATS gravity (repeats):** `Python`, `RAG`, `LangChain`, `LangGraph`, `Agentic`, `LLM`, `Azure OpenAI`/`Bedrock`, `vector`, `prompt`, `CI/CD`, `Docker`, `MCP` (rising).  
**Ops wedge (rare, high-signal):** `ServiceNow`, `Now Assist`, `ITIL`, `incident`, `CMDB`, `Datadog`/`Grafana`, `Copilot Studio`, `Power Automate`.

---

## Java / SQL filter-cost table

Coded on **N=52** full-body JDs.

| Signal | Count | % of 52 | JDs |
|---|---:|---:|---|
| **Java named as required or co-equal language** | 6 | **12%** | JD08 Capgemini (.NET/Java/**or Python**); JD13 HPE (Python, Java, Selenium); JD14 NXP (Python, Java, Node); JD35 HP knowledge-list; JD53 TMUS (**Python or Java, both preferred**); JD80 Red Hat (Python/Java AI libs). JD58 ServiceNow Java is **plus**. |
| **Java advantage / plus only** | 2 | 4% | JD16 Hitachi; JD58 ServiceNow. |
| **Java not mentioned** | 44 | **85%** | Majority of GenAI/agentic/Copilot/Now Assist JDs. |
| **JavaScript / Glide required (not Java)** | 4 | 8% | JD36 Convera; JD55 Atos; JD67 Qentelli; JD65 does not require JS. TEKsystems/PepsiCo Now Assist outside strict N. |
| **SQL / DBMS / Postgres / SQL tools required or co-equal** | 12 | **23%** | A3: NXP, Hitachi **required**, Smart Working Postgres, Hired, Cirrus SQL tools, Allianz, ApTask. **NEW:** JD52 CGI **“Excellent in … SQL”**; JD91 Orion **“Git, Docker, SQL, and JSON”**; JD56 “database design”; JD76 NL2SQL/Postgres (older); JD102 PostgreSQL; JD103 SQL/NoSQL. |
| **Neither Java nor SQL named** | 34 | **65%** | Python+RAG+agents majority. |

### Filter-cost arithmetic (VERIFIED FACT on this corpus, not advice dressed as data)

- **Skip Java as a primary skill:** exclude **~12%** if any Java-as-language is a hard reject. If the user still applies when Java is **OR Python** (Capgemini, TMUS) or Workday noise (HP), exclusion drops to **NXP + HPE + Red Hat ≈ 6%**.  
- **Skip SQL as a named skill:** exclude **~23%**. Painful misses: **Hitachi (SQL required)**, **CGI Hadoop+SQL**, **Orion Coimbatore (SQL named)**, **Smart Working Postgres**.  
- **Skip BOTH Java-first and SQL-first:** **~65% of full-body JDs name neither.** The market Manoj wants is still **majority Python-first**.  
- **Hidden third tax:** **JavaScript** (Convera, Atos, Qentelli, TEKsystems). A Python-only resume can fail the **best ITSM-adjacent** roles even though Java was skipped successfully.  
- **TMUS-specific:** Build role (JD53) wants **Python or Java**. Support/Ops role (JD54) snippet says **Python or similar**. Do not lead with Java; do not refuse JD53 solely for the “or Java” clause.

---

## Adjacent vs core split (for THIS profile)

**Adjacent** = first-screen plausible for a Service Desk Lead **with a strong GenAI/AIOps portfolio** (Python or JS automation, RAG, agents, ITSM/observability, CI/CD) **without** years of model training.  
**Core** = training/fine-tune as primary duty, CUDA/GPU, or “X years AI/ML development” as the clock.

| Bucket | JDs | First-screen |
|---|---|---|
| **Adjacent — apply with portfolio this week** | JD01 Infosys Bedrock; JD51 TCS Agentic (Datadog/RPA); JD07 Accenture LLM Ops; JD09 Deloitte eval; JD12 Persistent AI OPS; JD13 HPE ITIL/SNOW; JD30 BNP IT-ops assistants; JD35 HP SNOW; JD36 Convera ITSM; JD54 TMUS Support/Ops; JD59 Siemens Energy Copilot; JD69 PepsiCo Agent Ops Center; JD84 Cognizant 7–13 LangGraph; JD86 Jobgether AIOps remote; JD56 Cognizant Chennai (internal) | Must **quote JD framework names**. Ops stories map to JD13/30/36/54/69. |
| **Adjacent — high bar / Maybe** | JD10 EY 10+ IT; JD16 Hitachi (SQL hurdle); JD17 Smart Working (2y prod agents); JD37 Google FDE; JD53 TMUS platform MCP; JD55 Atos (7+ SN **dev**); JD62 Flexday closed; JD66 Optum MCP; JD67 Qentelli SN; JD73 Siemens Healthineers; JD78 Sandisk; JD89 Persistent 7+2; JD91 Orion Coimbatore (SQL + “AI and SWE”) | Weekend RAG fails. Need traces/eval/SN or Copilot artefact. |
| **Mixed / kitchen sink** | JD08 Capgemini; JD14 NXP; JD29 ApTask; JD52 CGI (Hadoop+SQL); JD63 Aivar (fine-tune must); JD64 NavaSys; JD80 Red Hat; JD81 LTIMindtree | Apply only if **one** cluster is true. |
| **Core ML / “N years AI/ML”** | JD03 Infosys 3–5 AI/ML; JD15 Qualys CUDA; JD71 Goldman 5+ AI/ML; JD72 WSP 3–5 AI/ML; JD77 Luxoft **8+ AI/ML**; JD88 Infosys 6–10 AI/ML; JD100 MantriAI GPU; JD104 BharatGen train foundation models; JD107 Ventragate LoRA | **Do not first-screen.** |
| **Under-levelled / title inflation** | JD05/JD90 TCS ₹5–8L / ₹5–7L est.; JD18 12–15 LPA for 1–3; JD108–110 intern/₹10–40k/mo | Comp/YOE mismatch. |

**Headline:** Adjacent still **outnumbers** core. New harvest **adds the ops/Copilot/Now Assist cluster** A3 under-sampled (TMUS Support/Ops, PepsiCo Agent Ops, Siemens Energy Copilot, Atos Now Assist, TCS Datadog). Catch unchanged: adjacent JDs want **coded artefacts**, not “used ChatGPT on tickets”.

---

## Services vs GCC vs product

| Segment | IDs | Language pattern |
|---|---|---|
| **Indian services** | JD01–12, 25, 31–34, 43–44, 47–50, **51, 52, 55, 56, 61, 65, 68, 81, 84, 88, 89, 90, 91, 96** | Cloned `Python + RAG + LangChain/LangGraph + Agentic`. LinkedIn seniority chips wrong. YOE often **overall IT**. Walk-ins (ADP, Blackstraw). Orion is services **in Coimbatore**. |
| **Big-4 / consulting** | JD09, 10, 38–40, 116 | Eval, Foundry, governance. PwC SA filled; new Hyd card PARTIAL. |
| **GCCs / banks / telecom** | JD16 Hitachi, 26 Allianz, 30 BNP, 41 ADP, **53–54 TMUS**, **69–70 PepsiCo**, 71 Goldman, 79 Wells, 87 Ecolab, 97 BMS | **Best overlap with IT ops.** TMUS is the account-internal door. PepsiCo Agent Ops Center is the playbook. Wells is 12+ SWE. |
| **Product** | JD13 HPE, 14 NXP, 15 Qualys, 17 Smart Working, 18 MyAdvice, 35 HP, 36 Convera, 37 Google, **57 Vizuara**, **58 ServiceNow**, **59 Siemens Energy**, 73 SHS, 78 Sandisk, 80 Red Hat, 104 BharatGen | ServiceNow product is Staff-level. Siemens Energy Copilot is the reachable product JD. Qualys/BharatGen/MantriAI = core. |
| **Staffing / contract** | JD19–21, 28–29, 46, 48, **60, 67, 74, 75, 86, 92, 95, 99, 102, 111** | Extreme variance: HYrEzy 35–50 LPA vs Ladder ₹25–40k/mo vs ACS 20–27.5 LPA. |

**Services vs product skill difference (this corpus):** services stop at LangChain/RAG; GCC/product add **eval, MCP, ServiceNow, Copilot Studio, FinOps, ITIL, Datadog**.

**Disclosed pay (employer or card, not Glassdoor estimates):** MyAdvice ₹12–15 LPA (1–3 YOE); Wissen 15–25 LPA; ACS 20–27.5 LPA (8–13); Qentelli SN ₹15–20 LPA; Vizuara ₹18 LPA; HYrEzy 35–50 LPA (4–6 YOE); MantriAI 30–45 LPA (closed); Nesoi 45 LPA (20 base); Highbrow 12–21 LPA; techjays Coimbatore 30–50 LPA (old card); Recro ₹45–55 (units unclear — **do not treat as verified LPA**). TCS/Infosys Glassdoor **₹5–10L** on similar titles = **ESTIMATE**.

---

## Location notes (Coimbatore / Chennai / Tamil Nadu / remote)

### Coimbatore (VERIFIED FACT — this was A3’s gap)

| JD | Status | Evidence |
|---|---|---|
| **JD91 Orion Innovation GenAI Engineer** | **LIVE** 2 days, 127 applicants | Full body. 5–8 YOE Python/FastAPI/LangChain/RAG/Bedrock/Azure/**SQL**/Docker. https://in.linkedin.com/jobs/view/genai-engineer-at-orion-innovation-4456093707 |
| JD63 Aivar Senior AI Engineer 6+ | Closed 6 months | Full body; fine-tune + LangFuse + MCP. Local agentic employer exists. |
| JD64 NavaSys 3+ AI/ML | INDEXED-LIVE | Fine-tune/diffusion; not a switcher JD. |
| JD99 Wellspring Engineering Lead Agentic 6–10 | INDEXED-LIVE hirist 06 May 2026 | Lead of 6–8 engineers. |
| JD96 Accenture AI/ML + LLM Architect + AI Infra Architect | LIVE cards 2 weeks | **Keyword-thin clones** flooding Coimbatore similar-jobs. Not unique IC bodies. |
| EY Hybrid Cloud AIOps Senior Engineer | Naukri SERP card | “Hybrid - Pune, Coimbatore, Bengaluru … 3–5 Yrs … 8–15 Lacs PA … Servicenow · Cloud Monitoring · AIOps”. **SERP card, not retrieved body.** |
| JD105 Integra Agentic 1–3 | Glassdoor est. ₹1–6L | Junior. |
| JD106 Bosch GenAI Solutions | est. ₹8–9L | 30d+. |
| JD107 Ventragate 2–3 | Indeed | Core-lite junior. |
| JD112 techjays AI Lead | ₹30–50 LPA card, 5 months | PARTIAL. |
| JD113 SourcingXPress | ₹5–18 LPA | PARTIAL. |

**INFERENCE:** Coimbatore is **not** an empty AI market, but **true 6–12 YOE applied-GenAI IC volume is thin**. The only **live full-body** 5–8 YOE GenAI IC this week is **Orion**. Accenture posts **title clones**. Stay-and-transition internally at Cognizant remains the volume path; Orion is the external local shot.

### Chennai / Tamil Nadu

| JD | Evidence |
|---|---|
| JD06 TCS 8–12 | Hyd, **Chennai**, BLR |
| JD24 Stamford 10–18 | Hybrid Hyd, **Chennai**, BLR |
| JD34 Altimetrik 5–10 | Hybrid Hyd, **Chennai**, BLR |
| JD42 Blackstraw walk-in 24 Aug | **Chennai WFO** 2–6 Yrs |
| JD43 DXC | Includes Chennai |
| JD44 Cognizant 6–11 | Hybrid BLR, Pune, **Chennai** |
| JD50 Infosys 3–5 | Hybrid Hyd, **Chennai**, BLR |
| **JD51 TCS Agentic 5+ LIVE** | **Chennai** in location string |
| **JD55 Atos SN FDE LIVE** | **Mumbai / Chennai / Bangalore** |
| **JD56 Cognizant GenAI LIVE careers** | **Chennai Hybrid**, 3+ related |
| JD61 TOCUMULUS Copilot | **Chennai preferred** / BLR (closed) |
| JD65 COGNITBOTZ | **Chennai 5d WFO**, 2PM–11PM (closed) |
| JD90 TCS Job 388730 | **Chennai**, est. ₹5–7L |
| JD93 NOBL Q | **Vellore** SN Agentic |
| JD108 AXIORA intern | Chennai ₹5k/mo |

### Remote / Hybrid India

- **LIVE/INDEXED remote:** JD17 Smart Working (US-evening IST); JD18 MyAdvice (11pm–8am IST); JD86 Jobgether AIOps anywhere India; JD53 TMUS (Hyd GCC, not remote); JD59 Siemens Energy **2 days remote/week Gurugram**; JD102 contract remote; JD92 Avensys remote SN.  
- **Closed remote:** JD60 BRATHON US evenings; JD62 Flexday; JD20 Hired; JD100 MantriAI.  
- **Pattern:** “Remote India” GenAI often means **US hours**. Night-shift is a hidden requirement.

**NCR:** Siemens Energy Gurugram Copilot (JD59) is the strongest new NCR row. IRIS Noida (JD27) 8–9 YOE MLOps/AIOps.

---

## Experience-formula patterns (total vs relevant)

| Pattern | Example JDs | Count in inventory (approx) | Switcher implication |
|---|---|---|---|
| **A. Overall IT/SWE + skills (no AI YOE clock)** | JD01 Infosys; JD51 TCS 5+; JD07 Accenture 3 yrs LLMs; JD35 HP 5–7; JD53 TMUS 7+ SWE; JD59 Siemens **6–8 total IT + 1–2 Copilot** | Common on better adjacent JDs | **Apply.** Honest 8.5 IT + portfolio. |
| **B. Total X + relevant Y GenAI** | Cognizant A4 “4–13 / relevant 2+”; JD89 Persistent **7+ overall, 2+ GenAI**; JD79 Wells **12+ SWE, 1+ GenAI**; JD06 TCS **8–12 + 3+ GenAI** | Dominant India services/GCC | **Apply if Y is months-to-2, not 8.** Do not write 8.5 GenAI. |
| **C. “N years AI/ML engineering”** | JD03 3–5 AI/ML; JD71 Goldman 5+ AI/ML; JD72 WSP 3–5 AI/ML; **JD77 Luxoft 8+ AI/ML**; **JD88 Infosys 6–10 AI/ML + 2+ agentic**; JD91 Orion “5–8 in **AI and software development**” | Minority but lethal | **Skip C** unless the rest of the JD is skills-only and recruiter is services-flexible. |
| **D. Relevant 2+ / 1+ GenAI / hands-on** | JD23 1–2+ GenAI; JD82 1 year enterprise GenAI; JD62 personal projects count; JD56 3+ **related** | Growing | Portfolio can create “related” months. |
| **E. Under-banded title** | JD04 Infosys LLMOps **2–3 Yrs**; JD05/90 TCS developer; JD18 1–3 | Comp trap | 8.5 YOE over-index. |

**Band counts (inventory, overlapping, posted ranges):**

| Band | Approx n (unique JDs listing a numeric band) |
|---|---|
| 6–9 / 6–10 / 6–11 | JD01 6–11; JD38 6–9; JD44 6–11; JD47 6–11; JD52 ~6; JD59 6–8; JD63 6+; JD66 6+; JD67 6–8; JD84 7–13; JD88 6–10; JD99 6–10 |
| 7–10 / 7–12 / 8–12 | JD06 8–12; JD12 7–10; JD13 TCP_04; JD27 8–9; JD30 7–9; JD45 5–9; JD46 8–13; JD53 7–11; JD55 7+ SN; JD58 8+ SWE; JD78 7–10; JD89 7–12 |
| 5–8 / 5–10 / 5–12 | JD08 5+; JD11 5–10; JD16 5–10; JD21 5–12; JD32 5–10; JD34 5–10; JD41 3–8; JD43 5–10; JD51 5+; JD65 5; JD91 5–8 |
| “Relevant 2+ / 1+ GenAI” explicit | JD06 3+; JD14 1+ LLM; JD23 1–2+; JD56 3+ related; JD59 1–2 Copilot; JD68 1+ Now Assist; JD69 1+ observe GenAI; JD79 1+; JD82 1; JD89 2+ |

**8.5 YOE is in-band for A and B. It is out-of-band for C (Luxoft/Infosys 6–10 AI/ML) and for 12+ SWE (Wells, TMUS Principal 12–18).**

---

## Red flags

| Flag | JDs | Why |
|---|---|---|
| Unpaid / stipend intern branded “Gen AI Engineer” | JD108 ₹5k/mo Chennai; JD109 ₹10k/mo RAG; JD110 ₹25–40k/mo | Experienced people should not apply. |
| Kitchen-sink Java+Spring+GenAI | Not dominant in **this** applied-GenAI corpus. Closest: JD14 NXP Java+Node+DBMS+fine-tune; JD52 CGI Hadoop+SQL+Foundry; JD81 LTIMindtree TF+K8s+CrewAI+4–16 YOE | Skip when Java is the job. |
| 15 skills for 4–8 LPA | JD05 TCS est. ₹5–8L; **JD90 TCS Chennai est. ₹5–7L** + LangChain/LangGraph | Title inflation. |
| “16–20 years RAG” | **None found.** Insufficient reliable evidence. | Do not cite. |
| Max ₹10 L for 6+ YOE | TCS/Infosys Glassdoor estimates on GenAI titles sit ₹5–10L; **not employer-disclosed**. Orion/Vizuara 18 LPA for 3–8 may compress 8.5 YOE. | Treat estimates as **ESTIMATE**. |
| “8+ years AI/ML development” | **JD77 Luxoft**; JD88 Infosys 6–10 AI/ML | Fraud trap if you apply with 8.5 IT. |
| US-hours sold as remote India | JD17, JD18 11pm, JD19, JD60, JD101 | Hidden night shift. |
| 200+ applicants in <1 week | Infosys JD01, Hitachi, Google FDE, Siemens Energy, ServiceNow, TMUS-adjacent | High competition; referral > portal. |
| NP Immediate–15 days | JD68 TEKsystems | Employed leads bounce. |
| Recro ₹45.00–₹55.00 | Units unclear | Do not quote as ₹45–55 LPA without employer confirmation. |

---

## Recency sample (this harvest, unique JDs)

Approximate, using posted language on retrieved pages (not Naukri’s entire 9,938).

| Window | Examples | n (this corpus, ~119 rows) |
|---|---|---|
| **Last 7 days** | JD59 Siemens Energy 21h; JD58 ServiceNow 1d; JD87 Ecolab 15h; JD91 Orion 2d; JD12 Persistent 2d (A3); JD51 still showing; JD07 Accenture 3d (A3); JD74 Recro 2d; JD97 BMS 1d; JD94 Equinix 2d; Naukri PARTIALs “1–2 days” (JD32–34, 45–48) | **~25–30** including PARTIAL Naukri cards |
| **Last 14 days** | JD10 EY 4d; JD16 Hitachi 18 Aug; JD17 Smart Working 4d; JD29 ApTask 5d; JD36 Convera 4d; JD37 Google 1w; JD52 CGI 2w; JD53 Shine 3w (border); JD55 Atos pub 28 Jul (outside 14d); JD56 pub 24 Jul | **~15 more** |
| **Last 30 days** | JD01 Infosys ~1w–3w; JD51 TCS 3w; JD86 Jobgether 22 Jul; many INDEXED Naukri “2–5 days” that may be recycled | **Majority of LIVE/INDEXED-LIVE** |
| Older / closed | Walk-ins past; Flexday/TOCUMULUS/BRATHON/Aivar 4–6 months; StackNexus 4 months | Remainder |

**INFERENCE:** Enough **true last-14-day** JDs exist to fill a weekly apply list (Orion, Siemens Energy, ServiceNow, Ecolab, TCS LI, CGI, TMUS Shine, Hitachi, Convera, Persistent AI OPS, Infosys JD01). Many Naukri “1 day ago” twins are **recycled clones**.

---

## First-screen shortlist: top 15 JDs Manoj should save this week

Ranked for **an 8.5 YOE Service Desk Lead with a strong (honest) GenAI/AIOps portfolio**, Coimbatore-based, Java/SQL not lead skills. **Yes/Maybe only.** Closed JDs listed as watch-if-relisted.

| # | JD | Why save this week | First-screen | Action |
|---|---|---|---|---|
| 1 | **JD54 TMUS Engineer, AI (Support/Operations) Hyd** | Same account family; incident/RAG/agent monitoring. 2–4 skill years, not 8 AI. | **Yes** | Find internal/TMUS GS posting; Shine/LinkedIn twin may be down — hunt requisition. |
| 2 | **JD36 Convera Agentic AI (ITSM) Pune** | Ticket deflection, HITL, MCP, ServiceNow, ITIL. Best ITSM JD in A3. JS hurdle. | **Yes/Maybe** | Apply if JS/SN artefact exists; else 2-week Copilot/SN script sprint first. |
| 3 | **JD13 HPE GenAI Platform Owner BLR** | ITIL, incidents, ServiceNow, RAG, RPA, observability. Java listed but Python+ops is the job. | **Yes/Maybe** | Apply with incident/RCA + RAG eval numbers. |
| 4 | **JD59 Siemens Energy Copilot Senior Gurugram** | **6–8 total IT + 1–2 Copilot.** RCA/consulting language. Live 21h. | **Yes if Copilot Studio demo** | Build one Copilot agent this week; apply. NCR move. |
| 5 | **JD69 PepsiCo AI Agent Operations Center Hyd** | 70% ops center: incident triage, traces, RCA on agents. Python+LangChain. Hyd GCC. | **Yes/Maybe** | Apply with observability+RAG; K8s literacy. |
| 6 | **JD01 Infosys GenAI/Agentic BLR** | Still LIVE. Python+Bedrock+RAG+LangGraph+Docker. No AI YOE clock. | **Yes** | Resume must quote pytest, Bedrock or equivalent, LangGraph. |
| 7 | **JD51 TCS Agentic 5+ pan-India incl. Chennai** | LIVE. MCP, Datadog, RPA, Python. Chennai option. | **Maybe/Yes** | Emphasize Datadog/Grafana + one agent; ignore ToT fluff. |
| 8 | **JD30 BNP Agentic AI & DevOps BLR** | Production assistants on **incident/RCA/CMDB**. 7–9 + 2y prod agents is the catch. | **Maybe** | Only if LangGraph+LangSmith traces exist. Highest GCC quality. |
| 9 | **JD84 / JD56 Cognizant LangGraph 7–13 BLR + Chennai GenAI** | Internal; NP 90d; 7–13 overall; Chennai hybrid. | **Maybe/Yes** | Internal apply. Headline: 8.5 ops + related GenAI months. |
| 10 | **JD09 Deloitte USI GenAI SAM Hyd/BLR** | LangChain/LlamaIndex + LangSmith/Phoenix eval. No Java/SQL. | **Maybe** | Apply if eval harness in GitHub. |
| 11 | **JD10 EY Agentic Foundry BLR** | 10+ Global IT + 3+ ops. ServiceNow NTH. LLM-as-judge. | **Maybe** | Stretch (10+); ops environment matches. |
| 12 | **JD91 Orion GenAI Coimbatore** | **Only live local full-body 5–8 IC.** Python FastAPI RAG Bedrock. SQL named. | **Maybe** | Apply if staying in CBE; show SQL literacy without becoming a DBA. |
| 13 | **JD07 Accenture LLM Ops Pune** | Keyword-thin; 3 yrs LLMs; ops/compliance. | **Maybe** | ATS: LLMs, Generative AI, Agentic AI, cloud-native. |
| 14 | **JD86 Jobgether Senior AIOps remote India** | SNOW ITOM + incident prediction. Remote. | **Yes** if monitoring/SN ITOM is real | Contract; check client. |
| 15 | **JD12 Persistent Senior AI OPS Pune** | Title AI OPS; work is Python agents + GCP ADK + Terraform. 7–10 header. | **Maybe** | Apply only with Python agents + IaC, not Splunk-only story. |

**Watch list (do not apply as primary this week):** JD55 Atos (needs 7+ SN **developer** years — Chennai listed); JD53 TMUS **build** (K8s platform SWE); JD58 ServiceNow Staff (no); JD37 Google FDE (elite); JD16 Hitachi (SQL required — excellent stack otherwise); JD67 Qentelli ₹15–20L SN (if JS/SN true).

**Do not apply:** JD77 Luxoft 8+ AI/ML; JD88 Infosys 6–10 AI/ML; JD15 Qualys CUDA; JD104 BharatGen training; JD108–110 stipend jobs; JD90 TCS ₹5–7L est.

---

## Evidence gaps

1. **Naukri listing bodies** still mostly unretrievable (Akamai/302). Volume counts ≠ unique FTE demand (A1).  
2. **Microsoft, Amazon, Zoho, Adobe, Salesforce, Oracle, Thoughtworks, Fractal, Tiger Analytics, Freshworks** product GenAI IC: **no full public body this pass**. ServiceNow product **was** captured (Staff — out of reach).  
3. **TMUS Support/Ops** LinkedIn guest expired; Shine captured the **build** role. Support/Ops body is **snippet-only**.  
4. **PepsiCo 452960** careers JS; body from index. Confirm on iCIMS after login.  
5. **Qentelli SN ₹15–20 LPA** Glassdoor Cloudflare this pass; salary from snippet/A4.  
6. **Recro ₹45–55** units unverified.  
7. **Splunk / PagerDuty** still **0/52** in full bodies — do not assume they are ATS-critical for GenAI titles.  
8. **Coimbatore Cognizant IOA / TMUS-internal mobility JDs** not captured as GenAI IC.  
9. **Salary employer-disclosed** remains scarce; most ₹ figures are Glassdoor **estimates**.  
10. **Instahyre / Cutshort** still JS walls.  
11. **“16–20 years RAG”** meme: not observed.  
12. Hirist Coimbatore lead: snippet only.

---

## Source appendix

**A3 baseline:** `C:\Users\manoj\ai-career-intel-2026\research\A3-jd-corpus.md`  
**Market counts:** `A1-job-market.md`  
**Role formulas:** `A4-role-map.md` (Cognizant “4–13 / relevant 2+”; TMUS Python or Java)  
**Skill priors:** `A7-skills-portfolio.md` (letsinterview.me N=313 Feb 2026: Python 83%, RAG 48%, LangChain 42%, Java 12%, SQL 20%)

**Primary URLs this pass (absolute):**

- https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669  
- https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-tata-consultancy-services-4407045907  
- https://in.linkedin.com/jobs/view/software-engineer-agentic-ai-engineer-at-cgi-4448458389  
- https://www.shine.com/jobs/engineerai-hyderabad/tmus-global-solutions/19352130  
- https://jobs.atos.net/job/Bangalore-ServiceNow-forward-deployed-AI-engineer/1409487633/  
- https://careers.cognizant.com/india-en/jobs/00067173931/gen-ai-engineer-cognizant/  
- https://openings.vizuara.ai/roles/agentic-ai-engineer  
- https://in.linkedin.com/jobs/view/senior-staff-ai-native-software-engineer-%E2%80%93-agentic-systems-at-servicenow-4417470643  
- https://in.linkedin.com/jobs/view/genai-copilot-senior-developer-at-siemens-energy-4409369794  
- https://in.linkedin.com/jobs/view/microsoft-ai-engineer-copilot-power-platform-agent-developer-at-brathon-4405444251  
- https://in.linkedin.com/jobs/view/copilot-agentic-ai-engineer-microsoft-ecosystem-at-tocumulus-4403937705  
- https://in.linkedin.com/jobs/view/ai-engineer-agentic-ai-india-at-flexday-ai-4403974923  
- https://in.linkedin.com/jobs/view/senior-ai-engineer-agentic-ai-llm-reasoning-at-aivar-innovations-4375632410  
- https://in.linkedin.com/jobs/view/ai-engineer-genai-agentic-ai-and-mlops-at-navasys-technologies-4442345026  
- https://in.linkedin.com/jobs/view/artificial-intelligence-engineer-at-cognitbotz-4425595723  
- https://in.linkedin.com/jobs/view/genai-engineer-at-orion-innovation-4456093707  
- https://in.linkedin.com/jobs/view/ai-automation-engineer-at-hitachi-energy-4455774089  
- https://in.linkedin.com/jobs/view/agentic-ai-engineer-itsm-enterprise-automation-at-convera-4455712445  
- https://in.linkedin.com/jobs/view/llm-operations-engineer-at-accenture-in-india-4456383755  
- https://www.naukri.com/agentic-ai-jobs  
- https://www.naukri.com/aiops-jobs  
- https://dic.gov.in/jobs/mlops-engineer/  
- https://jaabz.com/jobs/252920-aiops-engineer  
- https://www.hirist.tech/j/engineering-lead-agentic-ai-engineering-1633977  
- https://www.pepsicojobs.com/main/jobs/452960?lang=en-us  
- https://usijobs.deloitte.com/en_US/careersUSI/JobDetail/USI-EH27-MFBEL-GEN-AI-ENGINEER-L40-HYD-BLR/353050  

**Access date for all URLs in this file:** 2026-08-23 unless a publication date is quoted from the page itself.

---

*End of W1-A2 harvest. Do not treat Glassdoor salary estimates as offers. Do not write 8.5 years of GenAI.*
