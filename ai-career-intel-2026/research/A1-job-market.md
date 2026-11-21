# A1 — India AI Job Market Scanner — August 2026

**Scanner:** Research Agent A1 (labour-market scan only; no career advice).  
**Access window:** 2026-08-23 (primary) with corroborating crawls 2026-08-16 to 2026-08-23.  
**Geography:** India, with city slices for Bengaluru, Hyderabad, Chennai, Pune, NCR (Delhi/Noida/Gurugram), Coimbatore, Remote/WFH India.  
**Targeting context (not advice):** 8.5-year IT Ops / Service Desk Lead background; GenAI / Agentic AI / LLM / AIOps / AI automation roles; **not** Java- or SQL-first positioning.

**How to read this document**

- **RAW counts** are what the board displayed (title / “1–20 of N” pager / “Apply to N jobs”) on the access date. They are **not** unique-person FTE demand. Naukri and Indeed match keywords anywhere in the JD, including company name, skill tags, and stuffed “AI” tokens.
- Every numeric claim is labelled **VERIFIED FACT | COMMUNITY EXPERIENCE | INFERENCE | RECOMMENDATION** and recency-tagged **LAST_30_DAYS | LAST_90_DAYS | LAST_6_MONTHS | LAST_12_MONTHS | OLDER**.
- **SECONDARY** blogs (Logicmojo, Futurense, Buildfastwithai, AlmaBetter, HeroHunt, Zedtreeo, Skillenai, Kaam.work) are cited only when labelled SECONDARY and, where possible, cross-checked against a primary board or official report.
- If a number could not be verified live, the cell says **Insufficient reliable evidence (N=X)** and lists what was searched.

---

## Method and search log (every query + URL + date)

### Method constraints

1. Prefer primary job boards and official reports.  
2. Capture **exact raw counts** from page titles / pagers, not rounded “10,000+” LinkedIn marketing headers when a more precise number exists.  
3. Record **intra-day fluctuation**. Naukri titles for the same URL differed by hundreds–thousands of jobs across crawls 16–23 Aug 2026.  
4. Treat “AI”, “LLM”, “prompt”, “RAG”, “automation” as **polluted keywords**. See Title-inflation section.  
5. Direct HTTP GET of Naukri HTML (PowerShell `Invoke-WebRequest`, 2026-08-23) returned ~34.7 KB JS shells **without** job counts. Counts below are from Google-indexed page titles, `open_page` renders, and search snippets that reproduced the live `<title>` / “1–20 of N” pager.  
6. LinkedIn public SERPs mostly return **“1,000+”** or **“10,000+”** buckets, not exact integers. Exact LinkedIn N is therefore often **Insufficient reliable evidence**.  
7. No login, no paid resume-display, no scraping beyond public HTML/search.

### Search log

| # | Query / action | URL or operator | Date (access) | Result used |
|---|---|---|---|---|
| 1 | `Naukri artificial intelligence jobs India` | https://www.naukri.com/artificial-intelligence-jobs | 2026-08-17 crawl / 2026-08-23 search | Title “57190 … August 2026”; meta 58338 |
| 2 | Direct open of AI jobs | https://www.naukri.com/ai-jobs | 2026-08-20 / 2026-08-23 | 82761 then 84313 |
| 3 | Direct open of AI/ML jobs | https://www.naukri.com/ai-ml-jobs | 2026-08-21 | 55527 |
| 4 | Direct open of AI engineer | https://www.naukri.com/ai-engineer-jobs | 2026-08-21 / 2026-08-23 | 49520 / 46957 / 46883 |
| 5 | Direct open of gen-ai | https://www.naukri.com/gen-ai-jobs | 2026-08-23 | 28722 then 28853; location facets |
| 6 | Direct open of genai | https://www.naukri.com/genai-jobs | 2026-08-23 | 7887; city facets |
| 7 | Direct open of generative-ai | https://www.naukri.com/generative-ai-jobs | 2026-08-22 / older Jul index | 10555 (Aug) vs 10091 (Jul title cache) |
| 8 | Direct open of generative-ai-jobs-in-india | https://www.naukri.com/generative-ai-jobs-in-india | 2026-08-23 | 12098 |
| 9 | Direct open of generative-ai-engineer | https://www.naukri.com/generative-ai-engineer-jobs | 2026-08-23 | 11132 |
| 10 | Direct open of genai-engineer | https://www.naukri.com/genai-engineer-jobs | 2026-08-23 | 7709 |
| 11 | Direct open of agentic-ai | https://www.naukri.com/agentic-ai-jobs | 2026-08-23 | 9938; city facets |
| 12 | Direct open of langchain | https://www.naukri.com/langchain-jobs | 2026-08-23 | 4122; city facets |
| 13 | Direct open of rag | https://www.naukri.com/rag-jobs | 2026-08-23 | 6876; city facets |
| 14 | Direct open of llmops | https://www.naukri.com/llmops-jobs | Jul 2026 indexed title (not re-rendered Aug 23) | 678 (July 2026 title) |
| 15 | Direct open of mlops | https://www.naukri.com/mlops-jobs | 2026-08-23 | 4207 |
| 16 | Direct open of ml-ops | https://www.naukri.com/ml-ops-jobs | 2026-08-23 | 5942 |
| 17 | Direct open of aiops | https://www.naukri.com/aiops-jobs | 2026-08-23 | 558 |
| 18 | Direct open of ai-automation | https://www.naukri.com/ai-automation-jobs | 2026-08-20 | 68385 (heavily polluted) |
| 19 | Direct open of prompt-engineer | https://www.naukri.com/prompt-engineer-jobs | June 2026 indexed title | 15585 (polluted by employer name “Prompt”) |
| 20 | Direct open of ml-engineer | https://www.naukri.com/ml-engineer-jobs | 2026-08-23 | 52071 |
| 21 | Direct open of machine-learning-engineer | https://www.naukri.com/machine-learning-engineer-jobs | 2026-08-23 | 26494 |
| 22 | Direct open of machine-learning | https://www.naukri.com/machine-learning-jobs | 2026-08-20 | 60625 (search meta) |
| 23 | Direct open of ai-developer | https://www.naukri.com/ai-developer-jobs | 2026-08-23 | 41855 |
| 24 | Direct open of ml-ai | https://www.naukri.com/ml-ai-jobs | 2026-08-23 | 29185 |
| 25 | City: AI jobs Bangalore | https://www.naukri.com/ai-jobs-in-bangalore | 2026-08-23 | 28091 |
| 26 | City: AI Bengaluru | https://www.naukri.com/artificial-intelligence-jobs-in-bengaluru | 2026-08-23 | 10826 |
| 27 | City: AI Bangalore | https://www.naukri.com/artificial-intelligence-jobs-in-bangalore | 2026-08-23 | 18545 |
| 28 | City: AI Hyderabad Secunderabad | https://www.naukri.com/artificial-intelligence-jobs-in-hyderabad-secunderabad | 2026-08-18 | 7938 |
| 29 | City: AI Chennai | https://www.naukri.com/artificial-intelligence-jobs-in-chennai | 2026-08-23 | 4208 (page-3 cache 4262) |
| 30 | City: AI Pune | https://www.naukri.com/artificial-intelligence-jobs-in-pune | 2026-08-23 | 6240 (page-58 cache 6111) |
| 31 | City: AI Delhi | https://www.naukri.com/artificial-intelligence-jobs-in-delhi | 2026-08-23 | 8941 |
| 32 | City: AI Delhi NCR | https://www.naukri.com/artificial-intelligence-jobs-in-delhi-ncr | 2026-08-23 | 4059 |
| 33 | City: AI Coimbatore | https://www.naukri.com/artificial-intelligence-jobs-in-coimbatore | 2026-08-23 | 527 |
| 34 | City: AI jobs Coimbatore | https://www.naukri.com/ai-jobs-in-coimbatore | 2026-08-23 | 681 |
| 35 | City: gen-ai Bangalore | https://www.naukri.com/gen-ai-jobs-in-bangalore | 2026-08-23 | 8919 |
| 36 | City: generative-ai Bangalore | https://www.naukri.com/generative-ai-jobs-in-bangalore | 2026-08-23 | 4053 |
| 37 | City: generative-ai Bengaluru | https://www.naukri.com/generative-ai-jobs-in-bengaluru | 2026-08-23 | 3843 |
| 38 | City: generative-ai Delhi NCR | https://www.naukri.com/generative-ai-jobs-in-delhi-ncr | 2026-08-23 | 1259 |
| 39 | City: generative-ai-engineer Chennai | https://www.naukri.com/generative-ai-engineer-jobs-in-chennai | 2026-08-23 | 866 |
| 40 | Remote: AI | https://www.naukri.com/remote-ai-jobs | 2026-08-23 | 29611 |
| 41 | Remote: artificial intelligence (keyword) | https://www.naukri.com/remote-artificial-intelligence-jobs | 2026-08-23 | 29791 |
| 42 | Location tag Remote | https://www.naukri.com/artificial-intelligence-jobs-in-remote | 2026-08-23 | 752 |
| 43 | Location tag Remote GenAI | https://www.naukri.com/generative-ai-jobs-in-remote-6 | 2026-08-23 | 167 |
| 44 | Exp band Bangalore 4–8 | https://www.naukri.com/artificial-intelligence-jobs-in-bangalore-4-to-8-years | 2026-08-23 | 18716 (filter nearly inert vs 18545) |
| 45 | Exp band Chennai 4–8 | https://www.naukri.com/artificial-intelligence-jobs-in-chennai-4-to-8-years | 2026-08-23 | 4202 vs 4208 all |
| 46 | Exp band Pune 4–8 | https://www.naukri.com/artificial-intelligence-jobs-in-pune-4-to-8-years | 2026-08-23 | 3500 vs 6240 all |
| 47 | Infosys AI slice | https://www.naukri.com/infosys-ai-jobs | 2026-08-23 | 4523 |
| 48 | LinkedIn AI engineer India | https://in.linkedin.com/jobs/artificial-intelligence-engineer-jobs | 2026-08-16 | “1,000+” (meta 9,000+) |
| 49 | LinkedIn GenAI engineer India | https://in.linkedin.com/jobs/generative-ai-engineer-jobs | 2026-08-19 | Title “1,000+”; meta “11,000+” |
| 50 | LinkedIn prompt engineer India | https://in.linkedin.com/jobs/ai-prompt-engineer-jobs | 2026-08-19 | “10,000+” (polluted) |
| 51 | LinkedIn AI jobs Bengaluru | https://in.linkedin.com/jobs/artificial-intelligence-jobs-bengaluru | 2026-08-11 | “1,000+” |
| 52 | LinkedIn AI jobs Pune | https://in.linkedin.com/jobs/artificial-intelligence-jobs-pune | 2026-08-07 | “1,000+” |
| 53 | LinkedIn agents AI India | https://in.linkedin.com/jobs/agents-ai-jobs | 2026-08-23 | 266 |
| 54 | Indeed AI engineer | https://in.indeed.com/q-ai-engineer-jobs.html | 2026-08-22 | “23,000” |
| 55 | Indeed GenAI engineer | https://in.indeed.com/q-generative-ai-engineer-jobs.html | 2026-08-23 | “4,000” |
| 56 | Indeed agentic AI engineer | https://in.indeed.com/q-agentic-ai-engineer-jobs.html | 2026-08-23 | “400” |
| 57 | Indeed GenAI engineer Bengaluru | https://in.indeed.com/q-generative-ai-engineer-l-bengaluru,-karnataka-jobs.html | 2026-08-23 | “2,000” |
| 58 | Indeed AI automation | https://in.indeed.com/q-ai-automation-jobs.html | 2026-08-21 | “21,000” |
| 59 | Instahyre Generative AI | https://www.instahyre.com/generative-ai-jobs/ | 2026-08-23 | Search snippet 5607; page JS “5606” |
| 60 | Instahyre GenAI Bangalore | https://www.instahyre.com/generative-ai-jobs-in-bangalore/ | 2026-08-23 | 3119 |
| 61 | Instahyre GenAI Hyderabad | https://www.instahyre.com/generative-ai-jobs-in-hyderabad/ | 2026-08-23 | 438 |
| 62 | Instahyre remote GenAI | https://www.instahyre.com/remote-generative-ai-jobs/ | 2026-08-23 | 559 |
| 63 | Cutshort AI India | https://cutshort.io/jobs/artificial-intelligence-ai-jobs | 2026-08-23 | “50+” |
| 64 | Cutshort AI Chennai | https://cutshort.io/jobs/artificial-intelligence-ai-jobs-in-chennai | 2026-08-23 | “30+” |
| 65 | iimjobs AI Bangalore | https://www.iimjobs.com/artificial-intelligence-jobs-in-bangalore | 2026-08-23 | 263 |
| 66 | hirist LLM | https://www.hirist.tech/k/llm-jobs | July 2026 | 2246 |
| 67 | AmbitionBox Prompt Engineer | https://www.ambitionbox.com/jobs/prompt-engineer-jobs-prf | Aug 2026 | 81 (listing page also said 87) |
| 68 | Foundit Prompt Engineer | https://www.foundit.in/search/prompt-engineer-jobs | 2026-07-28 | 61 |
| 69 | Foundit MLOps | https://www.foundit.in/search/mlops-jobs | 2026-07-24 | 22852 (likely inflated keyword) |
| 70 | Shine “prompt” | https://www.shine.com/job-search/prompt-jobs | Aug 2026 | 6935 (polluted) |
| 71 | Deloitte–Nasscom press | https://www.deloitte.com/in/en/about/press-room/bridging-the-ai-talent-gap-to-boost-indias-tech-and-economic-impact-deloitte-nasscom-report.html | 2026-08-23 (report dated 20 Aug 2024) | 600k–650k → >1.25M; 25–35% market |
| 72 | Deloitte report hub | https://www.deloitte.com/in/en/issues/generative-ai/advancing-india-ai-skills.html | 2026-08-20 | five skill segments |
| 73 | Nasscom community | https://community.nasscom.in/communities/data-science-ai-community/advancing-indias-ai-skills-interventions-and-programmes | 2026-08-22 (posted 19 Aug 2024) | 15% talent CAGR; 25–35% market |
| 74 | Nasscom publications | https://nasscom.in/knowledge-center/publications/advancing-indias-ai-skills-interventions-and-programmes-needed | listed Sep 2023 on site metadata; content is 2024 report | same figures |
| 75 | IndiaAI article | https://indiaai.gov.in/article/india-s-ai-talent-pool-to-grow-to-1-25-million-by-2027-nasscom-deloitte-india-report | published 22 Aug 2024; accessed 2026-08-22 | same figures; TCS 350k / Wipro 220k trained |
| 76 | ToI reprint | https://timesofindia.indiatimes.com/business/india-business/nasscom-deloitte-report-urges-rapid-upskilling-of-indias-tech-workforce-in-ai/articleshow/112637175.cms | 20 Aug 2024 | reprint |
| 77 | Nasscom×Indeed 2026 | https://community.nasscom.in/communities/nasscom-insights/indias-ai-talent-inflection-point-skill-gaps-competitive-advantage | 19 May 2026 | 86% employers saw AI impact on roles; 58% low applicant volume |
| 78 | Nasscom publication page | https://nasscom.in/knowledge-center/publications/indias-ai-talent-inflection-point-skill-gaps-competitive-advantage | listed 13 Jan 2026 / 19 May 2026 | same report |
| 79 | India Today / LinkedIn India Head | https://www.indiatoday.in/jobs/story/ai-jobs-in-india-rise-51-as-skills-first-hiring-and-tier-2-cities-reshape-workforce-india-linkedin-head-educ-2976508-2026-08-21 | 21 Aug 2026 | 51% AI engineering roles YoY; 311,000 AI-related jobs in India since 2023 |
| 80 | PIB Stanford AI Index | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2226912 | 12 Feb 2026 (PIB fetch 2026-08-23 returned Access Denied) | Secondary via search snippet: India ~33% AI talent acquisition rate |
| 81 | CBRE / Naukri Dec 2025 via News18 | https://www.news18.com/business/70-of-ai-jobs-located-in-these-3-indian-cities-naukri-com-report-ws-kl-9916184.html | 18 Feb 2026 | 64,500 AI-tagged Naukri listings Dec 2025; BLR 25.4%, NCR 24.8%, Mum 19.2% |
| 82 | New Kerala CBRE reprint | https://www.newkerala.com/news/a/bengaluru-delhi-ncr-emerge-as-primary-hubs-50-share-586.htm | 18 Feb 2026 | Hyd 12.5%, Pune 9.6%, Chennai 6.4%, Kolkata 2.1% |
| 83 | ET / Scaler workforce | https://m.economictimes.com/tech/artificial-intelligence/bengaluru-pune-hyderabad-mumbai-and-chennai-dominate-indias-ai-talent-map-report/articleshow/131818462.cms | 18 Jun 2026 | learner-base shares, N=11,444 (not job openings) |
| 84 | DD News 2.3M | https://ddnews.gov.in/en/indias-ai-sector-poised-to-surpass-2-3-million-job-openings-by-2027-report/ | 10 Mar 2025 | **not** the Deloitte 1.25M talent-pool number; different claim |
| 85 | NeGD MLOps | https://dic.gov.in/jobs/mlops-engineer/ | 2026-08-11 | 1 contractual MLOps post, last date 23 Aug 2026 |
| 86 | HTTP GET batch of 11 Naukri URLs | PowerShell Invoke-WebRequest | 2026-08-23 | HTTP 200, ~34.7 KB, empty `<title>` (JS shell) |
| 87 | Company/live JDs | Naukri listing URLs, LinkedIn `/jobs/view/`, Indeed viewjob, Glassdoor | 2026-08-16–23 | 25+ titled roles; recency sample |
| 88 | AIOps JDs | https://www.naukri.com/aiops-jobs | 2026-08-23 | 558; listing snippets |
| 89 | Secondary Futurense | https://futurense.com/blog/best-ai-engineering-roles | 9 Jun 2026 | SECONDARY salary bands; not used as primary counts |
| 90 | Secondary Skillenai “AI agents” | https://skillenai.com/data/skill/ai-agents | 16 Aug 2026 | 2,295 postings/90d **global**, Bengaluru 55 |
| 91 | Secondary Kaam.work city boom | https://www.kaam.work/blog/indias-ai-talent-boom | 26 Apr 2026 | SECONDARY; “126,000+ AI-aligned roles” claimed vs NASSCOM — not independently verified here |
| 92 | Cutshort / Instahyre JS | Instahyre page fetch 2026-08-23 | JS template; count from search index, not hydrated DOM | documented |

**Failed / blocked fetches (explicit):**

- Naukri live HTML GET: no counts in static HTML (N=11 URLs).  
- PIB `PRID=2226912`: HTTP Access Denied on 2026-08-23. Figure retained only as **search-snippet quote**, not as independently re-fetched HTML.  
- Instahyre `/generative-ai-jobs/` hydrated total: JS placeholders; integer from search snippet.  
- LinkedIn exact integers: generally unavailable without login.

---

## Live job-board snapshot tables (keyword × city × count × URL × access date)

### How Naukri “counts” work (read before the tables)

Naukri’s job-search URLs are **keyword retrieval**, not occupational classification. The pager “1–20 of N” and the `<title>` “N … Job Vacancies In August 2026” are the same N.

**Implication (INFERENCE, LAST_30_DAYS):** Broad tokens (`ai`, `ai automation`, `ml engineer`, `prompt engineer`, `llm`) **over-count** true AI-builder roles. Narrower tokens (`agentic ai`, `langchain`, `llmops`, `aiops`) are closer to applied-AI demand but still include mashup JDs.

### Table A — India-wide Naukri keyword snapshot (RAW)

| Keyword (Naukri slug) | RAW N | Title / pager text | URL | Access | Recency of index | Label |
|---|---:|---|---|---|---|---|
| `ai` | **84,313** | “Ai Jobs - 84313 Ai Job Vacancies In August 2026” | https://www.naukri.com/ai-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT (RAW board count). Alternate crawl 20 Aug: **82,761**. |
| `ai-automation` | **68,385** | “Ai Automation Jobs - 68385 … August 2026”; pager 1–20 of 68385 | https://www.naukri.com/ai-automation-jobs | 2026-08-20 | LAST_30_DAYS | VERIFIED FACT (RAW). **Polluted:** “AI” + generic automation. |
| `machine-learning` | **60,625** | search meta “60625 Machine Learning Jobs Available” | https://www.naukri.com/machine-learning-jobs | 2026-08-20 | LAST_30_DAYS | VERIFIED FACT (meta); full title not re-rendered 23 Aug. |
| `artificial-intelligence` | **57,190** (title) / **58,338** (meta) | “57190 Artificial Intelligence Job Vacancies In August 2026” | https://www.naukri.com/artificial-intelligence-jobs | 2026-08-17 title / 2026-08-23 meta | LAST_30_DAYS | VERIFIED FACT (two snapshots). |
| `ai-ml` | **55,527** | “55527 Ai Ml Job Vacancies In August 2026” | https://www.naukri.com/ai-ml-jobs | 2026-08-21 | LAST_30_DAYS | VERIFIED FACT |
| `ml-engineer` | **52,071** | “52071 Ml Engineer Job Vacancies In August 2026”; pager 1–20 of 52071 | https://www.naukri.com/ml-engineer-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT. **Polluted:** “ML” matches non-ML (PLM/MES). |
| `ai-engineer` | **46,957** (Aug title) / **49,520** (21 Aug title) / **46,883** (meta) | “46957 / 49520 Ai Engineer Job Vacancies In August 2026” | https://www.naukri.com/ai-engineer-jobs | 2026-08-21–23 | LAST_30_DAYS | VERIFIED FACT (fluctuating RAW). |
| `ai-developer` | **41,855** | “41855 Ai Developer Job Vacancies In August 2026” | https://www.naukri.com/ai-developer-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `ml-ai` | **29,185** | “29185 Ml Ai Job Vacancies In August 2026” | https://www.naukri.com/ml-ai-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `gen-ai` | **28,722** then **28,853** | “28722 / 28853 Gen Ai Job Vacancies In August 2026”; pager 1–20 of same | https://www.naukri.com/gen-ai-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT. **Best broad GenAI proxy on Naukri this week.** |
| `machine-learning-engineer` | **26,494** | “26494 Machine Learning Engineer Job Vacancies In August 2026” | https://www.naukri.com/machine-learning-engineer-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `prompt-engineer` | **15,585** | “15585 Prompt Engineer Job Vacancies In **June 2026**” | https://www.naukri.com/prompt-engineer-jobs | June 2026 index; live Aug render failed | LAST_6_MONTHS (stale title) | VERIFIED FACT of June title. **Heavily polluted** (employer “Prompt Info Services”, “Prompt consultant”). |
| `generative-ai-jobs-in-india` | **12,098** | “12098 Generative Ai Job Vacancies In India” | https://www.naukri.com/generative-ai-jobs-in-india | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `generative-ai-engineer` | **11,132** | “11132 Generative Ai Engineer Job Vacancies In August 2026” | https://www.naukri.com/generative-ai-engineer-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `generative-ai` (no “in-india”) | **10,555** (22 Aug) / **10,091** (July cached title) | August vs July titles | https://www.naukri.com/generative-ai-jobs | 2026-08-22 / July cache | LAST_30_DAYS / LAST_90_DAYS | VERIFIED FACT of two snapshots. |
| `agentic-ai` | **9,938** | “9938 Agentic Ai Job Vacancies In August 2026”; pager 1–20 of 9938 | https://www.naukri.com/agentic-ai-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT. **Tightest high-volume 2026 title cluster.** |
| `genai` | **7,887** | “7887 Genai Job Vacancies In August 2026” | https://www.naukri.com/genai-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `genai-engineer` | **7,709** | “7709 Genai Engineer Job Vacancies In August 2026” | https://www.naukri.com/genai-engineer-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `rag` | **6,876** | “6876 Rag Job Vacancies In August 2026” | https://www.naukri.com/rag-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT. Listings inspected were mostly Retrieval-Augmented Generation, not RAG-the-company. |
| `ml-ops` | **5,942** | “5942 Ml Ops Job Vacancies In August 2026” | https://www.naukri.com/ml-ops-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `mlops` | **4,207** | “4207 Mlops Job Vacancies In August 2026” | https://www.naukri.com/mlops-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `langchain` | **4,122** | “4122 Langchain Job Vacancies In August 2026” | https://www.naukri.com/langchain-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT |
| `llm` (India-scoped) | **19,238** | “19238 Llm Job Vacancies In India” | https://www.naukri.com/llm-jobs-in-india | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT. **Polluted by LLB/LLM law degrees** (see `llb-llm` 23,849 in July). |
| `llm` (unscoped June title) | **20,702** | “20702 Llm Job Vacancies In June 2026” | https://www.naukri.com/llm-jobs | June cache; Aug live render failed | LAST_6_MONTHS | VERIFIED FACT of June title only. |
| `llmops` | **678** | “678 Llmops Job Vacancies In **July 2026**”; pager 1–20 of 678 | https://www.naukri.com/llmops-jobs | July 2026 index; Aug live render failed | LAST_90_DAYS | VERIFIED FACT of July title. **Smallest specialised GenAI-ops cluster.** |
| `aiops` | **558** | “558 Aiops Job Vacancies In August 2026”; pager 1–20 of 558 | https://www.naukri.com/aiops-jobs | 2026-08-23 | LAST_30_DAYS | VERIFIED FACT. **IT-ops intersection, not GenAI-builder volume.** |

**Quote snippets (Naukri, LAST_30_DAYS, VERIFIED FACT):**

- Gen AI SERP header: “# Gen Ai Jobs - 28722 Gen Ai Job Vacancies In August 2026” and footer “Apply to 28722 Gen Ai Jobs on Naukri.com”.  
- Agentic SERP header: “# Agentic Ai Jobs - 9938 Agentic Ai Job Vacancies In August 2026” / “Apply to 9938 Agentic Ai Jobs on Naukri.com”.  
- LangChain SERP: “1 - 20 of 4122”.  
- RAG SERP: “1 - 20 of 6876”.  
- AIOps SERP: “1 - 20 of 558”.

### Table B — Naukri city × keyword (RAW). Target cities only.

**Note:** Location facets on a national SERP (e.g. “Filter jobs by location → Bengaluru 10123”) count JDs that **list that city among locations**, including pan-India/multi-city posts. City-slug URLs (`…-jobs-in-chennai`) are a different retrieval. Both are reported.

#### B1. National-SERP location facets (same-day 2026-08-23 unless noted)

| Keyword SERP | Bengaluru | Hyderabad | Delhi / NCR | Pune | Chennai | Source URL | Label |
|---|---:|---:|---:|---:|---:|---|---|
| `gen-ai` | **10,123** then **10,165** | **4,723** then **4,745** | **4,568** then **4,596** | **3,532** then **3,541** | **not in top-4 facet** | https://www.naukri.com/gen-ai-jobs | VERIFIED FACT (facet). Chennai exists but below Pune on this SERP. |
| `ai` | **27,664** | **12,804** | **13,570** | **10,499** | Insufficient on this SERP facet | https://www.naukri.com/ai-jobs | VERIFIED FACT (facet) |
| `agentic-ai` | **3,887** | **2,180** | **1,531** | **1,462** | not in top-4 | https://www.naukri.com/agentic-ai-jobs | VERIFIED FACT (facet) |
| `rag` | **2,650** | **1,348** | **1,102** | **997** | not in top-4 | https://www.naukri.com/rag-jobs | VERIFIED FACT (facet) |
| `langchain` | **1,564** | **844** | **755** | **628** | not in top-4 | https://www.naukri.com/langchain-jobs | VERIFIED FACT (facet) |
| `genai` | **3,221** | **1,747** | **1,031** | **1,298** | not in top-4 | https://www.naukri.com/genai-jobs | VERIFIED FACT (facet) |
| `genai-engineer` | **3,139** | **1,707** | **993** | **1,262** | not in top-4 | https://www.naukri.com/genai-engineer-jobs | VERIFIED FACT (facet) |
| `generative-ai` (Jul facet) | **3,855** | **2,326** | **1,362** | **1,502** | not in top-4 | https://www.naukri.com/generative-ai-jobs | VERIFIED FACT of July/early-Aug facet |
| `ai-developer` | **12,775** | **6,253** | **6,112** | **5,836** | not in top-4 | https://www.naukri.com/ai-developer-jobs | VERIFIED FACT (facet) |
| `ml-engineer` | **12,404** | not in top-4 (Delhi 8583, Mumbai 7191) | **8,583** | **6,272** | not in top-4 | https://www.naukri.com/ml-engineer-jobs | VERIFIED FACT (facet) |
| `machine-learning-engineer` | **9,241** | **3,948** | **4,360** | **3,115** | not in top-4 | https://www.naukri.com/machine-learning-engineer-jobs | VERIFIED FACT (facet) |
| `infosys-ai` (employer×keyword) | **2,923** | **1,994** | not in top-4 | **1,079** | **1,338** | https://www.naukri.com/infosys-ai-jobs | VERIFIED FACT (facet). Infosys volume is Chennai-heavy relative to Pune. |
| `remote-artificial-intelligence` (keyword, **not** WFH filter) | **10,300** | **4,789** | **4,663** | **3,708** | n/a | https://www.naukri.com/remote-artificial-intelligence-jobs | VERIFIED FACT of polluted “remote” keyword, not true WFH. |

**INFERENCE (LAST_30_DAYS):** On every cleaner GenAI token (`gen-ai`, `agentic-ai`, `rag`, `langchain`, `genai`), **Bengaluru is ~2× Hyderabad**, Hyderabad ≈ NCR, Pune fourth, Chennai typically **outside the top-4 facet**. That is a demand-geography signal, not a headcount of unique roles.

#### B2. City-slug URLs (keyword, city)

| City | Keyword slug | RAW N | URL | Access | Label / caveat |
|---|---|---:|---|---|---|
| Bengaluru | artificial-intelligence | **10,826** | https://www.naukri.com/artificial-intelligence-jobs-in-bengaluru | 2026-08-23 | VERIFIED FACT |
| Bangalore | artificial-intelligence | **18,545** | https://www.naukri.com/artificial-intelligence-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT. **Bangalore ≠ Bengaluru in Naukri ontology.** |
| Bangalore+Bengaluru | artificial-intelligence | **18,013** | https://www.naukri.com/artificial-intelligence-jobs-in-bengaluru-bangalore | 2026-08-23 | VERIFIED FACT |
| Bangalore | ai | **28,091** | https://www.naukri.com/ai-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT (broad) |
| Bangalore+Bengaluru | ai | **27,692** | https://www.naukri.com/ai-jobs-in-bangalore-bengaluru | 2026-08-23 | VERIFIED FACT |
| Bangalore | gen-ai | **8,919** | https://www.naukri.com/gen-ai-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT |
| Bangalore | generative-ai | **4,053** | https://www.naukri.com/generative-ai-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT |
| Bengaluru | generative-ai | **3,843** | https://www.naukri.com/generative-ai-jobs-in-bengaluru | 2026-08-23 | VERIFIED FACT |
| Bangalore | generative-ai-engineer | **4,176** | https://www.naukri.com/generative-ai-engineer-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT |
| Bangalore | ai-agent | **1,853** | https://www.naukri.com/ai-agent-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT. Mix of **LLM agents** and **Salesforce Agentforce / BPO “AI agent”**. |
| Hyderabad Secunderabad | artificial-intelligence | **7,938** | https://www.naukri.com/artificial-intelligence-jobs-in-hyderabad-secunderabad | 2026-08-18 | VERIFIED FACT |
| Chennai | artificial-intelligence | **4,208** (page-3 cache **4,262**) | https://www.naukri.com/artificial-intelligence-jobs-in-chennai | 2026-08-23 | VERIFIED FACT |
| Chennai | ai | **7,790** | https://www.naukri.com/ai-jobs-in-chennai | 2026-08-23 | VERIFIED FACT (broad) |
| Chennai | generative-ai-engineer | **866** | https://www.naukri.com/generative-ai-engineer-jobs-in-chennai | 2026-08-23 | VERIFIED FACT |
| Chennai + TN | artificial-intelligence | **5,132** | https://www.naukri.com/artificial-intelligence-jobs-in-chennai-and-tamil-nadu | 2026-08-23 | VERIFIED FACT |
| Pune | artificial-intelligence | **6,240** (page-58 cache **6,111**) | https://www.naukri.com/artificial-intelligence-jobs-in-pune | 2026-08-23 | VERIFIED FACT |
| Pune | ai | **10,572** | https://www.naukri.com/ai-jobs-in-pune | 2026-08-23 | VERIFIED FACT (broad) |
| Delhi | artificial-intelligence | **8,941** | https://www.naukri.com/artificial-intelligence-jobs-in-delhi | 2026-08-23 | VERIFIED FACT. Broader than NCR slug. |
| Delhi / NCR | artificial-intelligence | **4,059** | https://www.naukri.com/artificial-intelligence-jobs-in-delhi-ncr | 2026-08-23 | VERIFIED FACT |
| Delhi / NCR | generative-ai | **1,259** | https://www.naukri.com/generative-ai-jobs-in-delhi-ncr | 2026-08-23 | VERIFIED FACT |
| Delhi / NCR | ai | **13,958** | https://www.naukri.com/ai-jobs-in-delhi-ncr | 2026-08-23 | VERIFIED FACT (broad) |
| Delhi | ai-engineer | **6,184** | https://www.naukri.com/ai-engineer-jobs-in-delhi | 2026-08-23 | VERIFIED FACT |
| Coimbatore | artificial-intelligence | **527** | https://www.naukri.com/artificial-intelligence-jobs-in-coimbatore | 2026-08-23 | VERIFIED FACT |
| Coimbatore | ai | **681** | https://www.naukri.com/ai-jobs-in-coimbatore | 2026-08-23 | VERIFIED FACT |
| Coimbatore | gen-ai-and-machine-learning | **71** | https://www.naukri.com/gen-ai-and-machine-learning-jobs-in-coimbatore-2 | 2026-08-23 | VERIFIED FACT (narrow AND query) |
| Remote (location tag) | artificial-intelligence | **752** | https://www.naukri.com/artificial-intelligence-jobs-in-remote | 2026-08-23 | VERIFIED FACT of **location=Remote** |
| Remote (location tag) | generative-ai | **167** | https://www.naukri.com/generative-ai-jobs-in-remote-6 | 2026-08-23 | VERIFIED FACT |
| Keyword “remote ai” | ai | **29,611** | https://www.naukri.com/remote-ai-jobs | 2026-08-23 | VERIFIED FACT of **token “remote”**, not WFH filter. Do not treat as 29k WFH AI jobs. |
| Keyword “remote artificial intelligence” | — | **29,791** | https://www.naukri.com/remote-artificial-intelligence-jobs | 2026-08-23 | Same pollution warning. |

**Coimbatore vs metros (INFERENCE, LAST_30_DAYS):** Coimbatore `artificial-intelligence` 527 is ~4.9% of Bengaluru-slug 10,826 and ~8.5% of Chennai 4,208. Live Coimbatore GenAI titles exist (NavaSys, Aivar, VentraGate, Integra, Bosch, Prognova) but **volume is thin**.

**Noida / Gurugram separately:** Insufficient reliable evidence of standalone city-slug totals (N=2 attempted via NCR rollup only). NCR combined is the usable proxy.

### Table C — Employer volume on Naukri SERP facets (not unique reqs)

| SERP | Accenture | Infosys | TCS | EY | Others quoted | URL | Date | Label |
|---|---:|---:|---:|---:|---|---|---|---|
| `gen-ai` | **3,442** | **420** | not in top-4 | **514** | Paytm 717 | https://www.naukri.com/gen-ai-jobs | 2026-08-23 | VERIFIED FACT (facet). Accenture dominates **tagged** GenAI volume. |
| `agentic-ai` | **1,878** | **179** | not in top-4 | — | Genpact 309; Salesforce 212 | https://www.naukri.com/agentic-ai-jobs | 2026-08-23 | VERIFIED FACT |
| `langchain` | **231** | **159** | **84** | — | PwC SDC 56 | https://www.naukri.com/langchain-jobs | 2026-08-23 | VERIFIED FACT |
| `rag` | **496** | **192** | **123** | **92** | — | https://www.naukri.com/rag-jobs | 2026-08-23 | VERIFIED FACT |
| `generative-ai` Bangalore | **1,138** | **170** | **71** | **69** | — | https://www.naukri.com/generative-ai-jobs-in-bangalore | 2026-08-23 | VERIFIED FACT |
| `generative-ai` Delhi NCR | **147** | — | — | — | Iris 77; Capgemini 45; EXL 35 | https://www.naukri.com/generative-ai-jobs-in-delhi-ncr | 2026-08-23 | VERIFIED FACT |
| AI Chennai | **324** | — | **83** | **52** | Capgemini 61 | https://www.naukri.com/artificial-intelligence-jobs-in-chennai | 2026-08-23 | VERIFIED FACT |
| AI Pune | **674** | **74** | — | — | Bajaj Finance 209; Capgemini 75 | https://www.naukri.com/artificial-intelligence-jobs-in-pune | 2026-08-23 | VERIFIED FACT |
| AI Delhi | **464** | — | — | **183** | Iris 94; Paytm 86 | https://www.naukri.com/artificial-intelligence-jobs-in-delhi | 2026-08-23 | VERIFIED FACT |
| AI Bengaluru+Bangalore | **4,559** | **225** | — | — | Capgemini 241; Google 194 | https://www.naukri.com/artificial-intelligence-jobs-in-bengaluru-bangalore | 2026-08-23 | VERIFIED FACT |
| Infosys × ai (national) | n/a | **4,523** | n/a | n/a | — | https://www.naukri.com/infosys-ai-jobs | 2026-08-23 | VERIFIED FACT |

**INFERENCE (LAST_30_DAYS):** Services firms (especially **Accenture**) industrialised “GenAI/Agentic” as a **staffing taxonomy**. Facet “Accenture 3,442 Gen AI jobs” is **not** 3,442 unique AI-scientist seats; it is tagged req volume, including Java+GenAI mashups (see red flags).

### Table D — LinkedIn Jobs India (public)

LinkedIn public SERPs **bucket** counts. Exact N is usually not exposed.

| Query | Public header | Meta / snippet | URL | Access | Label |
|---|---|---|---|---|---|
| Artificial Intelligence Engineer, India | **1,000+** | “9,000+ Artificial Intelligence Engineer jobs in India” | https://in.linkedin.com/jobs/artificial-intelligence-engineer-jobs | 2026-08-16 | VERIFIED FACT of bucket. Exact N Insufficient (N=1 public SERP). |
| Generative AI Engineer, India | **1,000+** | “11,000+ Generative Ai Engineer Jobs in India” | https://in.linkedin.com/jobs/generative-ai-engineer-jobs | 2026-08-19 | VERIFIED FACT of bucket + meta conflict. |
| AI Prompt Engineer, India | **10,000+** | same | https://in.linkedin.com/jobs/ai-prompt-engineer-jobs | 2026-08-19 | VERIFIED FACT of polluted bucket (prompt ≠ prompt-engineer occupation). |
| Agents AI, India | **266** | “266 Open Roles” | https://in.linkedin.com/jobs/agents-ai-jobs | 2026-08-23 | VERIFIED FACT (rarer exact integer). |
| AI jobs, Bengaluru | **1,000+** | — | https://in.linkedin.com/jobs/artificial-intelligence-jobs-bengaluru | 2026-08-11 | VERIFIED FACT of bucket |
| AI jobs, Pune | **1,000+** | — | https://in.linkedin.com/jobs/artificial-intelligence-jobs-pune | 2026-08-07 | VERIFIED FACT of bucket |
| AI jobs, Hyderabad (Head of AI SERP) | **1,000+** | leadership-skewed query | https://in.linkedin.com/jobs/head-of-artificial-intelligence-jobs-hyderabad | 2026-07-30 | VERIFIED FACT of bucket; query is title-inflated |
| Mumbai Metro AI | **3,000+** | — | https://in.linkedin.com/jobs/artificial-intelligence-jobs-mumbai-metropolitan-region | 2026-08-17 | VERIFIED FACT of bucket |

LinkedIn India Country Head (Kumaresh Pattabiraman), quoted by India Today, 21 Aug 2026 (**LAST_30_DAYS, VERIFIED FACT of the quote, not of LinkedIn’s microdata**):

> “Since 2023, 2 million new AI-related jobs have been added globally, including **311,000 in India**… **AI engineering roles in India alone have risen 51%** in the past year… Vijayawada… **46%** increase in AI engineering roles in just one year.”  
Source: https://www.indiatoday.in/jobs/story/ai-jobs-in-india-rise-51-as-skills-first-hiring-and-tier-2-cities-reshape-workforce-india-linkedin-head-educ-2976508-2026-08-21

**Caveat (INFERENCE):** “AI-related jobs” ≠ GenAI-builder jobs. 311,000 is a **cumulative LinkedIn-classified** figure since 2023, not open reqs on 23 Aug 2026.

### Table E — Indeed India (`in.indeed.com`)

Indeed public SERPs round to thousands.

| Query | Displayed N | URL | Access | Label |
|---|---:|---|---|---|
| `ai engineer` | **23,000** (title also “22000”) | https://in.indeed.com/q-ai-engineer-jobs.html | 2026-08-22 | VERIFIED FACT of rounded SERP |
| `ai automation` | **21,000** | https://in.indeed.com/q-ai-automation-jobs.html | 2026-08-21 | VERIFIED FACT of rounded SERP; polluted |
| `generative ai engineer` | **4,000** | https://in.indeed.com/q-generative-ai-engineer-jobs.html | 2026-08-23 | VERIFIED FACT of rounded SERP |
| `generative ai engineer` + Bengaluru | **2,000** | https://in.indeed.com/q-generative-ai-engineer-l-bengaluru,-karnataka-jobs.html | 2026-08-23 | VERIFIED FACT of rounded SERP |
| `agentic ai engineer` | **400** | https://in.indeed.com/q-agentic-ai-engineer-jobs.html | 2026-08-23 | VERIFIED FACT of rounded SERP |
| SimplyHired Hyd `agentic ai` | **2,340** | https://www.simplyhired.co.in/search?q=agentic+ai&l=hyderabad%2C+telangana | 2026-08-23 | VERIFIED FACT. SimplyHired syndicates Indeed; do not add to Indeed. |
| SimplyHired remote `gen ai` | **37** | https://www.simplyhired.co.in/search?q=gen+ai&l=remote | 2026-08-23 | VERIFIED FACT |

### Table F — Instahyre, Cutshort, IIMJobs, hirist, AmbitionBox, Foundit, Shine

| Board | Query | RAW N | URL | Access | Label |
|---|---|---:|---|---|---|
| Instahyre | Generative AI (national) | **5,607** (search) / **5,606** (page fetch) | https://www.instahyre.com/generative-ai-jobs/ | 2026-08-23 | VERIFIED FACT of indexed count. Page DOM was JS-unhydrated. |
| Instahyre | Generative AI, Bangalore | **3,119** | https://www.instahyre.com/generative-ai-jobs-in-bangalore/ | 2026-08-23 | VERIFIED FACT |
| Instahyre | Generative AI, Hyderabad | **438** | https://www.instahyre.com/generative-ai-jobs-in-hyderabad/ | 2026-08-23 | VERIFIED FACT |
| Instahyre | Remote Generative AI | **559** | https://www.instahyre.com/remote-generative-ai-jobs/ | 2026-08-23 | VERIFIED FACT |
| Instahyre | All India jobs (platform total) | **12,489–12,521** | https://www.instahyre.com/jobs-in-india/ | 2026-08-21 | VERIFIED FACT of platform size. GenAI is a large share of Instahyre’s **curated** inventory. |
| Cutshort | AI jobs, India | **50+** | https://cutshort.io/jobs/artificial-intelligence-ai-jobs | 2026-08-23 | VERIFIED FACT of “50+” bucket. Exact N Insufficient (N=1). |
| Cutshort | AI jobs, Chennai | **30+** | https://cutshort.io/jobs/artificial-intelligence-ai-jobs-in-chennai | 2026-08-23 | VERIFIED FACT of bucket |
| iimjobs | AI, Bangalore | **263** | https://www.iimjobs.com/artificial-intelligence-jobs-in-bangalore | Aug 2026 | VERIFIED FACT. Mid/senior/leadership-skewed board. |
| hirist.tech | LLM | **2,246** | https://www.hirist.tech/k/llm-jobs | July 2026 | VERIFIED FACT of July title |
| AmbitionBox | Prompt Engineer, India | **81** (header) / **87** (body “jobs found”) | https://www.ambitionbox.com/jobs/prompt-engineer-jobs-prf | Aug 2026 | VERIFIED FACT. **This is the honest Prompt Engineer occupation count**, vs Naukri 15,585 polluted. |
| Foundit | Prompt Engineer | **61** | https://www.foundit.in/search/prompt-engineer-jobs | 2026-07-28 | VERIFIED FACT |
| Foundit | MLOps | **22,852** | https://www.foundit.in/search/mlops-jobs | 2026-07-24 | VERIFIED FACT of RAW; likely keyword inflation (compare Naukri mlops 4,207). |
| Shine | “prompt” jobs | **6,935** | https://www.shine.com/job-search/prompt-jobs | Aug 2026 | VERIFIED FACT of RAW; polluted (annotator, SQL+prompt, etc.). |

**INFERENCE (LAST_30_DAYS):** Instahyre’s **5.6k GenAI** vs Naukri’s **12k–29k** is the gap between a **curated product/startup/MNC board** and a **keyword-stuffed mass board**. Cutshort’s 50+ is a boutique startup board, not a market census.

### Salary facets on Naukri (not salaries paid)

These are **counts of JDs that selected a salary band**, not compensation surveys.

| Keyword | 0–3 L | 3–6 L | 6–10 L | 10–15 L | URL | Date | Label |
|---|---:|---:|---:|---:|---|---|---|
| gen-ai | 1,968 | 7,413 | 12,651 | 11,397 | https://www.naukri.com/gen-ai-jobs | 2026-08-23 | VERIFIED FACT (facet). Modal disclosed band **6–10 L**, large mass also **10–15 L**. |
| agentic-ai | 643 | 2,384 | 3,879 | 3,455 | https://www.naukri.com/agentic-ai-jobs | 2026-08-23 | VERIFIED FACT |
| rag | 378 | 1,072 | 2,298 | 2,743 | https://www.naukri.com/rag-jobs | 2026-08-23 | VERIFIED FACT. Modal disclosed band **10–15 L** (rarer pattern). |
| langchain | 270 | 677 | 1,398 | 1,674 | https://www.naukri.com/langchain-jobs | 2026-08-23 | VERIFIED FACT. Same 10–15 L modal. |
| genai | 314 | 1,879 | 3,482 | 2,900 | https://www.naukri.com/genai-jobs | 2026-08-23 | VERIFIED FACT |
| aiops | 31 | 62 | 150 | 187 | https://www.naukri.com/aiops-jobs | 2026-08-23 | VERIFIED FACT. Modal **10–15 L** on a small base. |
| ml-engineer | 8,670 | 23,450 | 26,734 | 17,245 | https://www.naukri.com/ml-engineer-jobs | 2026-08-23 | VERIFIED FACT (polluted keyword). |

**INFERENCE:** Cleaner GenAI tokens (`rag`, `langchain`, `agentic-ai`) skew **higher disclosed bands** than generic `ai`/`ml-engineer`. This is a JD-tagging pattern, not a paid-salary census. Glassdoor Pune “AI Engineer” median **₹9.47 L** total pay (https://www.glassdoor.com/Salaries/pune-india-ai-engineer-salary-SRCH_IL.0,10_IM1072_KO11,22.htm, 20 Aug 2026) sits **below** Naukri 10–15 L modal — consistent with title inflation and with Glassdoor’s mix of junior/services roles.

---

## Experience-band snapshot

### Naukri URL experience filters are often inert

| Filter URL | N | Comparator (unfiltered) | Access | Label |
|---|---:|---:|---|---|
| Bangalore AI `4-to-8-years` | **18,716** | Bangalore AI all **18,545** | 2026-08-23 | VERIFIED FACT. Filter **increased** N — not a working experience cut. |
| Chennai AI `4-to-8-years` | **4,202** | Chennai AI all **4,208** | 2026-08-23 | VERIFIED FACT. Essentially unfiltered. |
| Pune AI `4-to-8-years` | **3,500** | Pune AI all **6,240** | 2026-08-23 | VERIFIED FACT. This one **does** cut (~56% remain). |

**Insufficient reliable evidence** for Naukri national counts of exactly **6–9 / 7–10 / 8–12 years** as platform filters (N=3 city tests; 2/3 filters failed). What **is** evidenced is **employer-stated bands on individual JDs**.

### Employer-stated bands on live JDs (8.5-year-relevant window)

Observed repeatedly in 2026 India JDs (LAST_30_DAYS, VERIFIED FACT of each posting):

| Stated band | Example title | Employer | URL |
|---|---|---|---|
| 6–9 yrs | Data Scientist \| LLM \| RAG \| GenAI \| Langchain | Infosys | https://www.naukri.com/job-listings-data-scientist-llm-rag-genai-langchain-infosys-kolkata-chennai-bengaluru-6-to-9-years-060826015554 |
| 6–9 yrs | Agentic AI Engineer | PwC | https://www.naukri.com/job-listings-agentic-ai-engineer-pwc-hyderabad-bengaluru-6-to-9-years-200826037654 |
| 6–11 yrs | LLM Engineer \| RAG \| GenAI \| Python \| Langchain | Infosys | https://www.naukri.com/job-listings-llm-engineer-rag-genai-python-langchain-infosys-pune-chennai-bengaluru-9-to-14-years-050826038375 (posted band 9–14; sibling 6–11 exists on SERP) |
| 7–10 yrs | Lead Gen AI | C5i | https://www.naukri.com/job-listings-lead-gen-ai-c5i-bengaluru-7-to-10-years-090426023542 — **35–55 Lacs PA** |
| 7–12 yrs | Principal Engineer - Gen AI | (Bengaluru SERP) | https://www.naukri.com/gen-ai-jobs |
| 8–10 yrs | AI Engineer \| Gen AI, Agentic AI, Gemini, GCP & RAG | TCS | https://www.naukri.com/job-listings-ai-engineer-gen-ai-agentic-ai-gemini-gcp-rag-tata-consultancy-services-india-8-to-10-years-220826011668 |
| 8–12 yrs | AI Engineer | LTM, Pune | https://www.naukri.com/job-listings-ai-engineer-ltm-pune-8-to-12-years-200826019696 |
| 8–12 yrs | Gen AI (Azure) | HCLTech, Bengaluru | https://www.naukri.com/job-listings-azure-ai-gen-ai-hcltech-bengaluru-8-to-12-years-050825024397 — **15–20 Lacs PA** |
| 8–12 yrs | AI Agentic Engineer | Cognizant | https://www.naukri.com/job-listings-ai-agentic-engineer-cognizant-india-8-to-12-years-180826024284 |
| 8–13 yrs | Agentic AI Engineer | Advance Career Solutions (client), Hyd/Pune/BLR | https://www.naukri.com/job-listings-agentic-ai-engineer-advance-career-solutions-hyderabad-pune-bengaluru-8-to-13-years-210826009123 — **20–27.5 Lacs PA** |
| 9–12 yrs | GenAI & Agentic AI Lead / Architect (C2) | Capgemini | https://www.naukri.com/job-listings-genai-agentic-ai-lead-architect-c2-capgemini-technology-services-india-limited-navi-mumbai-9-to-12-years-180826941389 |
| 9–12 yrs | Gen AI (9–12 Years)-Pan India | Infosys | https://www.naukri.com/job-listings-gen-ai-9-12-years-pan-india-infosys-hyderabad-pune-bengaluru-9-to-12-years-270326034960 |
| 9–14 yrs | LLM Engineer \| GenAI \| Agentic Ai \| Langchain | Infosys | https://www.naukri.com/job-listings-llm-engineer-genai-agentic-ai-langchain-infosys-pune-bengaluru-delhi-ncr-9-to-14-years-060826037402 |
| 5–10 yrs | Agentic AI Engineer | Persistent (walk-in May 2026; still indexed) | https://www.naukri.com/job-listings-agentic-ai-engineer-persistent-hyderabad-bengaluru-5-to-10-years-050526015522 |
| 6–10 yrs | Agentic AI Engineer | Infosys (Glassdoor JD) | https://www.glassdoor.co.in/job-listing/agentic-ai-engineer-infosys-JV_IC2940587_KO0,19_KE20,27.htm?jl=1010089163760 |

**Pattern (INFERENCE, LAST_30_DAYS):** For 6–12 years’ total IT experience, India 2026 JDs typically demand **“N years IT + 1–3 years hands-on GenAI/LLM/agents”**, not 8 years of LLM production. Example — Advance Career Solutions Agentic AI Engineer: “Experience: 8 12 Years” with Agentic/LangChain as skills, not 8 years of LangGraph. Example — Infosys Agentic AI Engineer Glassdoor: “**6 10 years** of experience in AI ML engineering with **at least 2 years** in building agentic AI systems or LLM based applications”.

**Fake-experience flag (VERIFIED FACT of JD text):** Cognizant “Gen AI / RAG Engineer” listed as **16–20 years** (https://www.naukri.com/job-listings-gen-ai-rag-engineer-cognizant-kolkata-chennai-bengaluru-16-to-20-years-190826019426). RAG as a production pattern is ~3 years old in mainstream enterprise use. That band is **title/grade inflation**, not a 16-year RAG career.

**iimjobs (LAST_30_DAYS, VERIFIED FACT):** Bangalore AI = 263 roles, many **8–13 / 12–18 / 15–20** years (PwC Manager GenAI Architect 8–13; CGI Cloud Architect 12–18; Tredence Director 15–20). Leadership/architect inventory concentrates here, not on Naukri mass search.

---

## Real role-title taxonomy (25+ titles with company+URL)

Titles below are **copied from live 2026 India JDs**, not US blog taxonomies. Each has an employer and a URL. Access 2026-08-16–23 unless the listing itself is dated.

| # | Title as posted | Employer | Exp (as posted) | Location | URL | Recency on board |
|---|---|---|---|---|---|---|
| 1 | **Agentic AI Engineer** | Tata Consultancy Services | 5+ years | Bangalore, Chennai, Hyderabad, Pune, Mumbai | https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-tata-consultancy-services-4407045907 | LAST_30_DAYS (LinkedIn 19 Aug 2026) |
| 2 | **Gen-AI/Agentic AI Engineer** | TCS | — | Chennai | https://www.glassdoor.co.in/job-listing/gen-ai-agentic-ai-engineer-tata-consultancy-services-JV_IC2833209_KO0,26_KE27,52.htm?jl=1009988712911 | LAST_30_DAYS (16 Aug 2026) |
| 3 | **AI Engineer \| Gen AI, Agentic AI, Gemini, GCP & RAG** | TCS | 8–10 yrs | India | https://www.naukri.com/job-listings-ai-engineer-gen-ai-agentic-ai-gemini-gcp-rag-tata-consultancy-services-india-8-to-10-years-220826011668 | LAST_30_DAYS (“Today”) |
| 4 | **GenAI / Agentic AI Engineer** | Infosys | hands-on under senior guidance | Bengaluru | https://in.indeed.com/viewjob?jk=a2a2bc015a050bd0 | LAST_30_DAYS |
| 5 | **Agentic AI Engineer** | Infosys | 6–10 yrs AI/ML, 2 yrs agents | Bengaluru | https://www.glassdoor.co.in/job-listing/agentic-ai-engineer-infosys-JV_IC2940587_KO0,19_KE20,27.htm?jl=1010089163760 | LAST_30_DAYS (16 Aug 2026) |
| 6 | **GEN AI Engineer** | Infosys | — | Bengaluru | https://www.glassdoor.co.in/job-listing/gen-ai-engineer-infosys-JV_IC2940587_KO0,15_KE16,23.htm?jl=1010089163801 | LAST_30_DAYS |
| 7 | **LLM Engineer \| RAG \| GenAI \| Python \| Langchain** | Infosys | 9–14 yrs | Hybrid Pune/Chennai/Bengaluru | https://www.naukri.com/job-listings-llm-engineer-rag-genai-python-langchain-infosys-pune-chennai-bengaluru-9-to-14-years-050826038375 | LAST_30_DAYS (“1 day ago”) |
| 8 | **Data Scientist \| LLM \| RAG \| GenAI \| Langchain** | Infosys | 6–9 yrs | Hybrid Kolkata/Chennai/Bengaluru | https://www.naukri.com/job-listings-data-scientist-llm-rag-genai-langchain-infosys-kolkata-chennai-bengaluru-6-to-9-years-060826015554 | LAST_30_DAYS |
| 9 | **Python developer with RAG, Langraph, Langchain** | Infosys | 2–5 yrs | Bengaluru | https://www.naukri.com/job-listings-python-developer-with-rag-langraph-langchain-infosys-limited-bengaluru-2-to-5-years-120826935462 | LAST_30_DAYS |
| 10 | **AI Agentic Engineer** | Cognizant | 8–12 yrs | India | https://www.naukri.com/job-listings-ai-agentic-engineer-cognizant-india-8-to-12-years-180826024284 | LAST_30_DAYS |
| 11 | **Gen AI / RAG Engineer** | Cognizant | 16–20 yrs | Hybrid Kolkata/Chennai/Bengaluru | https://www.naukri.com/job-listings-gen-ai-rag-engineer-cognizant-kolkata-chennai-bengaluru-16-to-20-years-190826019426 | LAST_30_DAYS |
| 12 | **Agentic AI Developer** | Capgemini | 2–7 yrs | Hybrid Pune/Bengaluru/Delhi NCR | https://www.naukri.com/job-listings-agentic-ai-developer-capgemini-pune-bengaluru-delhi-ncr-2-to-7-years-190826012707 | LAST_30_DAYS |
| 13 | **GenAI & Agentic AI Lead / Architect (C2)** | Capgemini | 9–12 yrs | Navi Mumbai | https://www.naukri.com/job-listings-genai-agentic-ai-lead-architect-c2-capgemini-technology-services-india-limited-navi-mumbai-9-to-12-years-180826941389 | LAST_30_DAYS |
| 14 | **IN_Sr Associate_Azure AI/ML/Agentic AI Engineer _GCC** | PwC SDC | 3–8 yrs | Bengaluru | https://www.naukri.com/job-listings-in-sr-associate-azure-ai-ml-agentic-ai-engineer-gcc-pricewaterhouse-coopers-service-delivery-center-kolkata-bengaluru-3-to-8-years-200826502564 | LAST_30_DAYS |
| 15 | **Agentic AI Engineer** | PwC | 6–9 yrs | Hybrid Hyderabad/Bengaluru | https://www.naukri.com/job-listings-agentic-ai-engineer-pwc-hyderabad-bengaluru-6-to-9-years-200826037654 | LAST_30_DAYS |
| 16 | **AI/ML Engineer - Agentic AI, GenAI, RAG & LLMOps** | Bain Capability Centre India | 1–5 yrs | Gurugram | https://www.naukri.com/job-listings-ai-ml-engineer-agentic-ai-genai-rag-llmops-bain-capability-centre-india-private-limited-gurugram-1-to-5-years-210826932411 | LAST_30_DAYS |
| 17 | **Generative AI / Agentic AI Engineer – LLM, RAG & LLMOps** | Bain | 2–5 yrs | Gurugram, Delhi NCR | https://www.naukri.com/job-listings-generative-ai-agentic-ai-engineer-llm-rag-llmops-bain-gurugram-delhi-ncr-2-to-5-years-200826033213 | LAST_30_DAYS |
| 18 | **Senior AI/ML Engineer - LLM, RAG, Agentic AI** | Optum (UHG) | 2–7 yrs | Bengaluru | https://www.naukri.com/job-listings-senior-ai-ml-engineer-llm-rag-agentic-ai-optum-global-solutions-india-private-limited-bengaluru-2-to-7-years-190826927575 | LAST_30_DAYS |
| 19 | **AI or ML Engineer - LLMs, RAG, LangChain, LangGraph** | Optum | 5–10 yrs | Bengaluru | https://www.naukri.com/job-listings-ai-or-ml-engineer-llms-rag-langchain-langgraph-optum-global-solutions-india-private-limited-bengaluru-5-to-10-years-190826927721 | LAST_30_DAYS |
| 20 | **Manager AI/ML Engineering (LLM, RAG, Agentic AI)** | Optum | 12–17 yrs | Bengaluru | https://www.naukri.com/job-listings-manager-ai-ml-engineering-llm-rag-agentic-ai-optum-global-solutions-india-private-limited-bengaluru-12-to-17-years-190826927584 | LAST_30_DAYS |
| 21 | **Search Engineer - AI/ML** | Apple India | 5–10 yrs | Bengaluru | https://www.naukri.com/job-listings-search-engineer-ai-ml-apple-india-pvt-ltd-bengaluru-5-to-10-years-130326504104 | LAST_6_MONTHS (posted ~Mar 2026; still indexed) |
| 22 | **Generative AI Forward Deployed Engineer, Google Cloud** | Google | — | Pune / Hyderabad / Bengaluru / Mumbai | https://in.linkedin.com/jobs/view/generative-ai-forward-deployed-engineer-google-cloud-at-google-4451133303 | LAST_30_DAYS |
| 23 | **Agentic AI Architect** | Air India | 10–17 yrs | Gurugram; 30–60 Lacs PA | https://www.naukri.com/job-listings-agentic-ai-architect-air-india-gurugram-10-to-17-years-200826033590 | LAST_30_DAYS |
| 24 | **Sr Agentic AI Engineer** | Scopely | 5–10 yrs | Bengaluru | https://www.naukri.com/job-listings-sr-agentic-ai-engineer-scopely-bengaluru-5-to-10-years-210826501593 | LAST_30_DAYS |
| 25 | **Developer AIML** | Airtel | 4–9 yrs | Gurugram | https://www.naukri.com/job-listings-developer-aiml-airtel-gurugram-4-to-9-years-241125006899 | LAST_30_DAYS (“1 day ago” on 23 Aug SERP) |
| 26 | **RAG/LLM Specialist_ Manager/Sr. Manager** | EXL | 6–11 yrs | Bengaluru | https://www.naukri.com/job-listings-rag-llm-specialist-manager-sr-manager-exl-bengaluru-6-to-11-years-210826012525 | LAST_30_DAYS |
| 27 | **Agentic AI Developer** | Sutherland | 3–7 yrs | Chennai | https://www.naukri.com/job-listings-agentic-ai-developer-sutherland-global-services-inc-chennai-3-to-7-years-180826503482 | LAST_30_DAYS |
| 28 | **Lead / Manager Agentic AI Engineer - Claude Code & Codex** | Blend 360 | 5–10 yrs | Hyderabad | https://www.naukri.com/job-listings-lead-manager-agentic-ai-engineer-claude-code-codex-blend-360-hyderabad-5-to-10-years-190826501840 | LAST_30_DAYS |
| 29 | **GenAI-Hyderabad/Bengaluru/Chennai/Pune** | Deloitte | 3–12 yrs hands-on GenAI | Multi-city | https://www.glassdoor.co.in/job-listing/genai-hyderabad-bengaluru-chennai-pune-deloitte-JV_IC2940587_KO0,38_KE39,47.htm?jl=1010016317513 | LAST_30_DAYS (18 Aug 2026) |
| 30 | **Gen AI (Azure)** | HCLTech | 8–12 yrs | Bengaluru; 15–20 Lacs | https://www.naukri.com/job-listings-azure-ai-gen-ai-hcltech-bengaluru-8-to-12-years-050825024397 | LAST_30_DAYS |
| 31 | **HCL - Senior AI/ML Engineer/ Architect** | HCL | 10–20 yrs | Hybrid Bengaluru/Chennai; 40–50 Lacs | https://www.naukri.com/job-listings (SERP https://www.naukri.com/ai-jobs-in-bangalore-bengaluru) | LAST_30_DAYS |
| 32 | **Agentic AI Engineer** | Persistent | 5–10 yrs | Hyd/BLR walk-in | https://www.naukri.com/job-listings-agentic-ai-engineer-persistent-hyderabad-bengaluru-5-to-10-years-050526015522 | LAST_6_MONTHS (drive dated 9 May 2026; still indexed) |
| 33 | **GenAI Architect** | Persistent | 8–12 yrs | Pune | https://www.naukri.com/job-listings-genai-architect-persistent-pune-8-to-12-years-210826009482 | LAST_30_DAYS |
| 34 | **Principal Gen AI Engineer** | Turing | 8–13 yrs | Hybrid Bengaluru | https://www.naukri.com/job-listings-principal-gen-ai-engineer-turing-global-india-bengaluru-8-to-13-years-300726035073 | LAST_90_DAYS |
| 35 | **AI Engineer – GenAI & Multi-Agent Systems** | Innova ESI | 4–13 yrs | Bengaluru, UK shift | https://in.linkedin.com/jobs/view/ai-engineer-%E2%80%93-genai-multi-agent-systems-at-innova-esi-4439002153 | LAST_90_DAYS (25 Jun 2026) |
| 36 | **LLM Systems / AI Agent Engineer (Remote)** | Smart Working | 5–10 yrs | Bengaluru/New Delhi listed | https://in.linkedin.com/jobs/view/llm-systems-ai-agent-engineer-remote-full-time-as311-at-smart-working-4452587679 | LAST_30_DAYS (18 Aug 2026) |
| 37 | **Senior AI Engineer (Applied LLM / Agentic Systems)** | YO IT CONSULTING | 4–6 yrs | Bengaluru; ₹30–50 L | https://in.indeed.com/viewjob?jk=c8dae521f08ed811 | LAST_30_DAYS |
| 38 | **Generative AI Engineer** | Luxoft | 7+ yrs, 4+ GenAI | Bengaluru | https://in.indeed.com/viewjob?jk=856b1ad053f2c5bb | LAST_30_DAYS |
| 39 | **AI Expert – Generative AI Solutions Developer** | Bosch | — | Coimbatore | https://www.glassdoor.co.in/Job/coimbatore-ai-agent-developer-jobs-SRCH_IL.0,10_IC2836047_KO11,29.htm | LAST_90_DAYS (30d+ on Glassdoor) |
| 40 | **Senior AI Engineer - Agentic AI & LLM Reasoning** | Aivar Innovations | 6+ yrs | Coimbatore | https://in.linkedin.com/jobs/view/senior-ai-engineer-agentic-ai-llm-reasoning-at-aivar-innovations-4375632410 | LAST_30_DAYS (3 Aug 2026) |
| 41 | **AI Engineer - GenAI, Agentic AI and MLOps** | NavaSys Technologies | 3+ yrs | Coimbatore | https://in.linkedin.com/jobs/view/ai-engineer-genai-agentic-ai-and-mlops-at-navasys-technologies-4442345026 | LAST_30_DAYS (17 Jul 2026 posting still live) |
| 42 | **MLOps Engineer** | NeGD / Digital India Corporation | 1 post, contractual | Delhi | https://dic.gov.in/jobs/mlops-engineer/ | LAST_30_DAYS (closes 23 Aug 2026) |
| 43 | **Machine Learning Operations Engineer** | Qualys | 2–3 yrs | Pune | https://in.linkedin.com/jobs/view/machine-learning-operations-engineer-at-qualys-4417876201 | LAST_30_DAYS (19 Aug 2026) |
| 44 | **Engineer - MLOps / LLMOps - 7+ Years** | Crescendo Global (client) | 7–12 yrs | Hybrid Noida/Gurugram | https://www.naukri.com/llmops-jobs | LAST_90_DAYS (July SERP) |
| 45 | **AIOps Engineer** (Hybrid Cloud AIOps Senior Engineer) | (Pune/Coimbatore/Bengaluru listing) | 3–5 yrs; 8–15 Lacs | Hybrid | https://www.naukri.com/aiops-jobs | LAST_90_DAYS (“3+ weeks ago”) |
| 46 | **AIOPS and Automation Engineer** | multi-city | 5–7 yrs | Hyd/Gurugram/BLR | https://www.naukri.com/aiops-jobs | LAST_30_DAYS |
| 47 | **Tech S and T-Tech Cloud dev-AIOPS and Automation Engineer-Senior** | (Noida) | 7–10 yrs | Noida | https://www.naukri.com/aiops-jobs | LAST_30_DAYS |
| 48 | **Prompt Engineer** | Synechron | 4–9 yrs | Mumbai | https://www.ambitionbox.com/jobs/prompt-engineer-jobs-prf | LAST_30_DAYS (“1 day ago”) |
| 49 | **Prompt Engineer** | Accenture | 3–8 yrs | Bengaluru | same AmbitionBox page | LAST_30_DAYS |
| 50 | **AI Prompt Engineer** | TCS | 3–6 yrs | India | same AmbitionBox page | LAST_30_DAYS |
| 51 | **Lead Agentic AI Developer** | Synergy Maritime | 5–8 yrs | Chennai | https://www.naukri.com/job-listings-lead-agentic-ai-developer-synergy-maritime-chennai-5-to-8-years-300626001212 | LAST_30_DAYS |
| 52 | **Agentic AI/Copilot Developer** | Espire Infolabs | 3–8 yrs | Remote | https://www.naukri.com/job-listings-agentic-ai-copilot-developer-espire-infolabs-gurugram-3-to-8-years-190826012246 | LAST_30_DAYS |
| 53 | **Gen AI Developer(WALK IN FOR PUNE)** | TCS | 8–15 yrs | Pune Hinjawadi | https://in.linkedin.com/jobs/view/gen-ai-developer-walk-in-for-pune-at-tata-consultancy-services-4446999013 | LAST_90_DAYS (walk-in 8 Jul 2026) |
| 54 | **Senior Data Scientist - Agentic AI & LLMs** | (20–35 Lacs; Gurugram/BLR/NCR) | 4–9 yrs | Hybrid NCR | https://www.naukri.com/job-listings-senior-data-scientist-agentic-ai-llms-aspyra-hr-services-gurugram-bengaluru-delhi-ncr-4-to-9-years-210826004664 | LAST_30_DAYS |
| 55 | **Large Language Model Architect** | Accenture (ATCI IDs in JD) | 5–10 / 7–12 yrs | Bengaluru | https://www.naukri.com/chief-lead-jobs-307 | LAST_90_DAYS |

**Taxonomy actually used in 2026 India JDs (INFERENCE from the table, LAST_30_DAYS):**

1. **Agentic AI Engineer / Developer / Lead / Architect** — the breakout 2026 title. Frameworks named: LangChain, LangGraph, AutoGen, CrewAI, MCP, A2A, Claude Code, Codex.  
2. **Gen AI / GenAI / Generative AI Engineer** — services-firm default; often Python + Bedrock/Azure OpenAI/Vertex + RAG.  
3. **LLM Engineer / LLM Developer / LLM Model Developer** — Infosys/Accenture industrialised this; Accenture also uses **LLM Model Developer** and **Large Language Model Architect** as “Project Role” labels.  
4. **AI Engineer** with parenthetical stack (`Gen AI, Agentic AI, Gemini, GCP & RAG`) — TCS-style.  
5. **AI/ML Engineer** hyphenated with `LLM, RAG, Agentic AI` — Optum/Bain GCC style.  
6. **Forward Deployed Engineer (Generative AI)** — Google Cloud, product/cloud motion; **not** a services-staffing title.  
7. **RAG/LLM Specialist** (EXL Manager/Sr Manager) — analytics-services specialist, not generic DS.  
8. **Copilot Developer / Agentic AI/Copilot** — Microsoft-stack services (Espire, Happiest Minds Copilot Studio on hirist).  
9. **LLMOps / MLOps Engineer** — small specialised cluster (Naukri llmops 678 in July).  
10. **AIOps Engineer / AIOPS and Automation Engineer** — ITSM/observability, not LLM-builder. Tools: Dynatrace, BigPanda, Moogsoft, ServiceNow, Splunk.  
11. **Prompt Engineer** — **real but tiny** occupation (AmbitionBox 81; Foundit 61). Naukri 15k is a false positive.  
12. **Java Developer With Gen AI** — mashup, not an AI role (see red flags).  
13. Coimbatore-local: **Senior Developer - AI/ML & Agentic AI** (Prognova), **Agentic AI Developer Voice & Text** (Integra), **Automation & AI Workflow Specialist** (n8n-class, Vserve).

**US titles rarely used as-is on India mass boards:** “Forward Deployed Engineer” appears at **Google Cloud** and a few product firms, not at TCS/Infosys. “Context Engineer”, “AI Evals Engineer”, “AgentOps Manager” appear in SECONDARY blogs (Futurense, 9 Jun 2026) more than in Naukri titles. Insufficient reliable evidence of high volume for those exact strings on Naukri (N=keyword scan of SERPs; not in top listings).

---

## Primary macro reports (NASSCOM/Deloitte/IndiaAI/etc.) with original dates

### 1. Deloitte India × nasscom — “Advancing India’s AI Skills: Interventions and programmes needed”

| Field | Value |
|---|---|
| Original press date | **20 August 2024** (“National, 20 August 2024”) |
| Primary press URL | https://www.deloitte.com/in/en/about/press-room/bridging-the-ai-talent-gap-to-boost-indias-tech-and-economic-impact-deloitte-nasscom-report.html |
| Report hub | https://www.deloitte.com/in/en/issues/generative-ai/advancing-india-ai-skills.html |
| Nasscom community (19 Aug 2024) | https://community.nasscom.in/communities/data-science-ai-community/advancing-indias-ai-skills-interventions-and-programmes |
| Nasscom publications page | https://nasscom.in/knowledge-center/publications/advancing-indias-ai-skills-interventions-and-programmes-needed (site metadata showed “Sep 21, 2023” — **do not treat as report date**; press is 20 Aug 2024) |
| IndiaAI reprint | 22 Aug 2024, https://indiaai.gov.in/article/india-s-ai-talent-pool-to-grow-to-1-25-million-by-2027-nasscom-deloitte-india-report |
| ToI reprint | 20 Aug 2024 |

**Quoted figures (VERIFIED FACT of the 2024 primary text; recency of **source document** = OLDER / Aug 2024; recency of **this scanner’s access** = LAST_30_DAYS):**

From Deloitte press release (accessed 2026-08-23):

> “The Indian AI talent demand is projected to grow from **600,000–650,000 to more than 1,250,000 during 2022–27**. However, the AI market is expected to grow at **25–35 percent**, potentially signalling a demand-supply gap in the talent pool…”

From Nasscom community (19 Aug 2024):

> “Indian AI talent pool is expected to grow from **600k –650k to over 1.25 Mn by 2027, at a 15% CAGR**. Indian AI market is expected to grow at a rate of **25% –35%** during this time…”

From IndiaAI (22 Aug 2024):

> “The Indian AI talent pool is expected to grow from 600,000–650,000 to >1,250,000 over 2022-27.31.”  
> “Through 2027, the Indian AI market, particularly the software and services market, is expected to grow at a **25–35% CAGR**.”  
> “During 2023–24, **TCS trained 350,000** employees, while **Wipro trained 220,000** employees on AI. Microsoft has also agreed to provide AI skilling opportunities to **2 million people in India by 2025**.”

Sathish Gopalaiah (Deloitte South Asia), LinkedIn/press:

> “skills are growing at about **13 percent** whilst the AI market demand is growing at a CAGR of anywhere between **25 to 35 percent**.”

**Five skill segments (Deloitte hub, VERIFIED FACT of report taxonomy, OLDER):** AI-informed; AI users; AI integrators; AI builders/developers/architects; AI experts.

**2026 recycling warning (INFERENCE, LAST_30_DAYS):** Multiple 2025–2026 blogs and course-sellers still quote **600k–650k → 1.25M by 2027** as if it were a 2026 measurement. It is an **August 2024 projection covering 2022–27**. It is **not** a 2026 job-board census.

### 2. nasscom × Indeed — “India’s AI Talent Inflection Point: From Skill Gaps to Competitive Advantage”

| Field | Value |
|---|---|
| Community post | **19 May 2026** |
| URL | https://community.nasscom.in/communities/nasscom-insights/indias-ai-talent-inflection-point-skill-gaps-competitive-advantage |
| Publications page | https://nasscom.in/knowledge-center/publications/indias-ai-talent-inflection-point-skill-gaps-competitive-advantage (listed 13 Jan 2026 and 19 May 2026) |

**Quoted highlights (VERIFIED FACT of Nasscom page, LAST_6_MONTHS):**

- “only **Singapore** has a higher share of postings mentioning artificial intelligence; … share of job postings mentioning AI in India has **consistently increased since 2023**.”  
- “**86%** of employers have seen some impact of AI on job roles and responsibilities with **35%** witnessing significant redefinition or transformation.”  
- “**40%** of the employers preferring demonstrable AI skills/certifications over degree.”  
- “**58%** of employers cite **low applicant volume** as a key challenge, and **50%** identify skills mismatch.”  
- “**65%** of employees are learning or lack confidence or have no exposure to AI tools.”  
- “**73%** of employees learning through self-driven channels.”  
- “**42%** employees feeling anxious about AI disrupting their jobs.”

This 2026 report **does not republish** the 1.25M headcount. It is a **skills/employer-survey** document, not an open-req census.

### 3. CBRE Research on Naukri.com listings (December 2025 stock)

Primary analysis date: **December 2025 listings**; press **18 February 2026**.

Sources (LAST_6_MONTHS, VERIFIED FACT of press quotes):

- News18: https://www.news18.com/business/70-of-ai-jobs-located-in-these-3-indian-cities-naukri-com-report-ws-kl-9916184.html  
- New Kerala: https://www.newkerala.com/news/a/bengaluru-delhi-ncr-emerge-as-primary-hubs-50-share-586.htm  

Quoted:

> “based on a study of over **64,500** active job listings on Naukri.com as of **December 2025**”  
> Bengaluru **25.4%**; Delhi-NCR **24.8%**; Mumbai **19.2%** (top 3 ≈ **70%**).  
> Hyderabad **12.5%**; Pune **9.6%**; Chennai **6.4%**; Kolkata **2.1%**.  
> “Engineering, Data Science, and Customer Success as the top three domains for AI roles.”

**Cross-check vs this scanner (INFERENCE, LAST_30_DAYS):** August 2026 Naukri `artificial-intelligence` India is **57k–58k**, same order of magnitude as CBRE’s Dec 2025 **64.5k AI-tagged** stock. City rank order is consistent (BLR > NCR > Hyd/Pune > Chennai). Mumbai is large in CBRE (19.2%) but **not in Naukri’s top-4 location facet for `gen-ai`** in Aug 2026 (facet top-4: BLR, Hyd, NCR, Pune). Possible reasons: CBRE used a different AI-tag definition; Mumbai vs NCR ontology; or mix shift toward Hyd/Pune GCCs. **Not resolved here.**

### 4. LinkedIn India via India Today — 21 August 2026

URL: https://www.indiatoday.in/jobs/story/ai-jobs-in-india-rise-51-as-skills-first-hiring-and-tier-2-cities-reshape-workforce-india-linkedin-head-educ-2976508-2026-08-21  

**VERIFIED FACT of quotation (LAST_30_DAYS):** 311,000 AI-related jobs in India since 2023; AI engineering roles **+51%** YoY; Vijayawada AI engineering **+46%** YoY.

### 5. PIB / Stanford AI Index (12 Feb 2026) — fetch blocked

Search snippet (LAST_6_MONTHS): “As per Stanford AI Index Report 2025, India leads the world in AI talent acquisition, with an annual hiring rate of about **33%**.”  
URL attempted: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2226912 — **Access Denied** on 2026-08-23.  
Label: **Insufficient reliable evidence of the 33% figure from primary HTML (N=1 blocked fetch)**. Treat as unreverified until PIB or Stanford PDF is opened.

### 6. Competing 2.3 million figure (not Deloitte)

DD News, 10 Mar 2025: https://ddnews.gov.in/en/indias-ai-sector-poised-to-surpass-2-3-million-job-openings-by-2027-report/  
“AI sector is poised to surpass **2.3 million job openings by 2027**.”  
**LAST_12_MONTHS+.** This is **not** the Deloitte 1.25M **talent pool**. Do not conflate openings with stock of AI-skilled people. Primary methodology not re-fetched here.

### 7. ET / Scaler India AI Workforce Report 2026 (learner geography, not jobs)

https://m.economictimes.com/tech/artificial-intelligence/bengaluru-pune-hyderabad-mumbai-and-chennai-dominate-indias-ai-talent-map-report/articleshow/131818462.cms — 18 Jun 2026.

N=**11,444 AI learners**. Bengaluru **19%** of learner base; Pune **7%**; Mumbai **4%**; Hyderabad **4%**; Chennai **3%**.  
**VERIFIED FACT of ET’s report of Scaler.** This is **supply (learners)**, not demand (openings).

### 8. SECONDARY / do-not-treat-as-primary

| Source | Date | Claim | Why secondary |
|---|---|---|---|
| Futurense “Emerging AI Engineering Roles” | 9 Jun 2026 | India salary bands FDE ₹18–90+ LPA; LLMOps ₹12–40 LPA; Agentic ₹15–55 LPA | Training vendor; no methodology |
| Kaam.work | 26 Apr 2026 | “126,000+ AI-aligned roles as of 2025–2026, according to industry workforce tracking from NASSCOM” | Could not confirm 126k on nasscom.in in this scan (N=nasscom 2024+2026 pages above) |
| Zedtreeo WFH guide | 15 Jul 2026 | “Roughly 60% of AI openings are advertised as remote or hybrid” | Conflicts with Naukri location=Remote GenAI **167** vs gen-ai national **28k** |
| Skillenai AI agents | 16 Aug 2026 | 2,295 postings / 90 days **global**; Bengaluru 55 (2.4%) | Global index, not India board |

---

## Segment analysis (services vs GCC vs product vs startup vs consulting)

Evidence is **live JDs + Naukri employer facets + Instahyre mix + iimjobs**, not a census of India’s AI workforce.

### Services (TCS, Infosys, Wipro, Cognizant, HCL, Capgemini, Accenture, Tech Mahindra, Persistent, UST)

**Volume: highest. Prestige: mixed; industrialised titles.**

- Naukri `gen-ai` facet: **Accenture 3,442** (23 Aug 2026) — largest single-employer tag on that SERP. **VERIFIED FACT.**  
- Naukri `agentic-ai` facet: Accenture **1,878**; Infosys **179**; Genpact **309**. **VERIFIED FACT.**  
- Infosys × `ai` = **4,523** tagged jobs. **VERIFIED FACT.**  
- Live titles are factory-like: Infosys “LLM Engineer | RAG | GenAI | Python | Langchain”, TCS “AI Engineer | Gen AI, Agentic AI, Gemini, GCP & RAG”, Cognizant “AI Agentic Engineer”, HCLTech “Gen AI” 8–12 yrs ₹15–20 L, Capgemini “Agentic AI Developer”.  
- **Walk-ins** still exist in 2026: TCS Pune Gen AI Developer walk-in 8 Jul 2026 (8–15 yrs); Persistent Agentic AI walk-in 9 May 2026; Blackstraw.ai Chennai Generative AI Engineer walk-in 24 Aug 2026.  
- Pay on services JDs often **undisclosed** or **₹5–10 L Glassdoor est.** for Infosys Agentic/GEN AI Engineer (Glassdoor 16 Aug 2026) — **below** specialist 20–35 L listings.

**INFERENCE (LAST_30_DAYS):** Services = **hiring volume + training engine** (Deloitte/IndiaAI: TCS 350k / Wipro 220k trained in 2023–24, OLDER). Many reqs are **billable-skill tags** on delivery seats, not research labs.

### GCCs (capability centres: Optum, Bain CC, Apple, Google Cloud India, PwC SDC, Qualys, Scopely, Airtel, JPM, Citi)

**Volume: high in Bengaluru/Hyderabad/Gurugram. Prestige: higher than services mass hiring. JD quality: more stack-specific.**

Live examples (VERIFIED FACT): Optum LLM/RAG/Agentic ladder (engineer 2–7, 5–10, manager 12–17); Bain CC Gurugram Agentic+LLMOps; Apple Search Engineer AI/ML Bengaluru; Google Cloud **Generative AI Forward Deployed Engineer** (Pune/Hyd/BLR/Mumbai); PwC SDC “Azure AI/ML/Agentic AI Engineer _GCC”; Qualys MLOps Pune; Scopely Sr Agentic AI Engineer; Airtel Developer AIML.

CBRE (Feb 2026 press on 2025 data) attributes Bengaluru’s AI-job share to GCC leasing (“more than one-third of the country’s total GCC leasing activity”). **LAST_6_MONTHS, VERIFIED FACT of CBRE claim.**

### Product / AI-native / global product

**Volume: lower than services on Naukri. Prestige: highest when the title is FDE / Principal / applied LLM with evals.**

Examples: Google FDE; Turing Principal Gen AI Engineer; Databricks ML Engineer Gen AI & LLM (Naukri langchain SERP, **caution:** some Databricks posts look cloned across cities and may be stale — 3+ weeks / months); Scopely; Air India (airline product/ops, architect 30–60 L).

Instahyre 5.6k GenAI with Bangalore 3,119 vs Hyderabad 438 suggests **product/startup concentration in Bangalore** on that board (**VERIFIED FACT** of Instahyre city split).

### Startups / boutique (Cutshort, Coimbatore locals, specialist consultancies)

Cutshort AI India **50+** (**VERIFIED FACT** of bucket). Coimbatore: Aivar (Velogent APA, 6+ yrs, 2 seats), NavaSys, VentraGate, Integra, Prognova, Nelgates, GUHATEK. Glassdoor: **19** “ai agent developer” jobs in Coimbatore, Aug 2026. **VERIFIED FACT.**

Pay spread on Indeed/Naukri specialist posts: YO IT Consulting Senior AI Engineer **₹30–50 L**; Trinity Soft Solutions Generative and Agentic AI Engineer **₹18–30 L**; TestUnity “AI Developer – Generative AI & LLM Engineer” **₹4.5–5 L** for 3+ years — **the last is a red-flag underpay/title mismatch**.

### Consulting (Deloitte, EY, PwC, Bain, EXL, Genpact, Accenture Strategy/GDS)

Naukri facets: EY **514** on gen-ai; PwC SDC **56** on langchain; Bain CC live LLMOps JDs; Deloitte multi-city GenAI 3–12 yrs (Glassdoor 18 Aug 2026); EXL RAG/LLM Specialist Manager.  
Accenture sits in **both** services-factory and consulting. Facet volume should not be read as strategy-consulting seats.

iimjobs Bangalore 263 is where **Director / Manager / Architect** consulting reqs cluster (PwC Manager GenAI Architect 8–13 yrs).

### Segment × “true GenAI-builder” vs “AI-tagged”

| Segment | Naukri-visible volume | Typical 2026 title | Prestige / selectivity (INFERENCE) |
|---|---|---|---|
| IT services factories | Highest (Accenture 3.4k gen-ai tags) | Gen AI Engineer, LLM Engineer, Agentic AI Developer | High volume, wide quality variance, walk-ins, Java mashups |
| GCCs | High in BLR/HYD/GGN | AI/ML Engineer LLM RAG Agentic; FDE; LLMOps | Higher stack specificity; Optum/Bain/Apple/Google |
| Consulting/GDS | Medium-high | Agentic AI Engineer (PwC), GenAI Architect, RAG/LLM Specialist | iimjobs/leadership + delivery mix |
| Product | Medium on Instahyre; lower on Naukri mass | FDE, Principal Gen AI, Sr Agentic | Highest bar when evals/production LLM required |
| Startup / Tier-2 | Low counts, real titles | Senior AI Engineer Agentic; AI Workflow Specialist | Thin volume; Coimbatore is real but small |
| AIOps / IT Ops | **558** aiops vs **28k** gen-ai | AIOps Engineer, AIOPS and Automation | Adjacent to ITSM, not a GenAI gold rush |

---

## AIOps / IT Ops / Support × AI overlap

### Board counts (IT-ops flavoured)

| Query | Board | N | URL | Date | Label |
|---|---|---|---|---|---|
| `aiops` | Naukri | **558** | https://www.naukri.com/aiops-jobs | 2026-08-23 | VERIFIED FACT |
| `mlops` | Naukri | **4,207** | https://www.naukri.com/mlops-jobs | 2026-08-23 | VERIFIED FACT |
| `llmops` | Naukri | **678** (July title) | https://www.naukri.com/llmops-jobs | July 2026 | VERIFIED FACT of July |
| `ml-ops` | Naukri | **5,942** | https://www.naukri.com/ml-ops-jobs | 2026-08-23 | VERIFIED FACT |
| `ai-automation` | Naukri | **68,385** | https://www.naukri.com/ai-automation-jobs | 2026-08-20 | VERIFIED FACT RAW; **not** AIOps. Generic automation + “AI” token. |
| AIOps salary facets | Naukri | 31 / 62 / 150 / **187** in 0–3 / 3–6 / 6–10 / 10–15 L | same aiops URL | 2026-08-23 | VERIFIED FACT |

**INFERENCE:** AIOps as a labelled occupation is **two orders of magnitude smaller** than GenAI keyword volume (558 vs 28,853 gen-ai). It is a **niche IT-operations market**, not the GenAI hiring wave.

### Live AIOps / ops+AI JD fragments (LAST_30_DAYS / LAST_90_DAYS, VERIFIED FACT of text)

From https://www.naukri.com/aiops-jobs (23 Aug 2026):

1. **AIOps Engineer** — 3–5 yrs, 8–15 Lacs, Hybrid Pune / **Coimbatore** / Bengaluru. Skills listed: **ServiceNow, Cloud Monitoring, AIOps, Azure, GCP, Dynatrace, Moogsoft, Bash**. Posted “3+ weeks ago”. Title in body: “Hybrid Cloud AIOps Senior Engineer”.  
2. **AIOPS and Automation Engineer** — 5–7 yrs, Hybrid Hyderabad / Gurugram / Bengaluru. Snippet: “5-6 years of experience in **Observability, AIOps, IT Operations, Service Management**”.  
3. **Tech S and T-Tech Cloud dev-AIOPS and Automation Engineer-Senior** — 7–10 yrs, Noida. Skills: **aiops, bigpanda, cmdb, dynatrace, anomaly detection**. Posted “5 days ago”.  
4. SERP also showed **“Systems Engineering II SM AI / AIOps & GenAI Engineer”** (title only in search snippet).  

TCS Agentic AI Engineer LinkedIn JD (19 Aug 2026) **explicitly bridges agents and ops tooling**:

> “Proven integration experience with **RPA platforms like UiPath, Automation Anywhere, or Blue Prism**.”  
> “Familiarity with **SRE/observability tools such as BigPanda, Datadog, Grafana, or New Relic**.”  
URL: https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-tata-consultancy-services-4407045907

PwC Agentic AI Engineer (6–9 yrs) skill tags included **ITIL** alongside LangGraph/LLM/Python (https://www.naukri.com/job-listings-agentic-ai-engineer-pwc-hyderabad-bengaluru-6-to-9-years-200826037654).

Qualys Pune **Machine Learning Operations Engineer** (19 Aug 2026): classification, chatbot inference pipelines, Jenkins, Kubernetes, PyTorch — **MLOps**, not ServiceNow AIOps. https://in.linkedin.com/jobs/view/machine-learning-operations-engineer-at-qualys-4417876201

### Service desk / incident / observability + LLM

**Insufficient reliable evidence of a large labelled market** for exact phrases “service desk AI”, “incident management AI”, “observability LLM”, “AI SRE” as **job titles** (Naukri `aiops` = 558; no dedicated high-N SERP for those strings was obtained with a clean integer).  

What **does** exist (VERIFIED FACT of individual JDs):

- AIOps JDs named **incident management, anomaly detection, CMDB, ServiceNow, Dynatrace, BigPanda**.  
- TCS Agentic JD named **SRE/observability + RPA**.  
- Espire **Agentic AI/Copilot Developer** (Remote): “This role is **not part of RPA of power automate** but required to work with the team” — Microsoft Copilot adjacent to ops automation.  
- Vserve Coimbatore **Automation & AI Workflow Specialist** (n8n-class, 5–10 L, remote, hiring office Coimbatore) — workflow automation, **not** model training. https://www.naukri.com/job-listings-automation-ai-workflow-specialist-vserve-coimbatore-3-to-7-years-170226044717  

**INFERENCE (LAST_30_DAYS):** The IT Ops → AI bridge in India 2026 is **three thin layers**, not one job family: (1) classical **AIOps/observability** (~558 Naukri), (2) **MLOps/LLMOps** for model production (~4.2k / ~678), (3) **Agentic + ITIL/RPA/ServiceNow/Copilot** bolted onto services GenAI JDs. There is **no** evidence in this scan of thousands of “Service Desk Lead → AIOps Lead” titled reqs.

---

## Recency sample of 20 live postings

Sample drawn from first-page Naukri `agentic-ai`, `gen-ai`, `rag`, `langchain`, `aiops` SERPs and LinkedIn/Indeed view URLs on **2026-08-23**. “Posted X ago” is the board’s own freshness chip.

| # | Title | Employer | Board freshness chip | URL | 30d vs 90d |
|---|---|---|---|---|---|
| 1 | AI/ML Engineer - Agentic AI, GenAI, RAG & LLMOps | Bain CC | **1 day ago** | https://www.naukri.com/job-listings-ai-ml-engineer-agentic-ai-genai-rag-llmops-bain-capability-centre-india-private-limited-gurugram-1-to-5-years-210826932411 | 30d |
| 2 | Agentic AI - Senior Engineer | Iris Software | **2 days ago** | https://www.naukri.com/job-listings-agentic-ai-senior-engineer-iris-software-technologies-private-limited-noida-3-to-7-years-210826907308 | 30d |
| 3 | Sr Agentic AI Engineer | Scopely | **1 day ago** | https://www.naukri.com/job-listings-sr-agentic-ai-engineer-scopely-bengaluru-5-to-10-years-210826501593 | 30d |
| 4 | Agentic AI Engineer | Advance Career Solutions | **1 day ago** | https://www.naukri.com/job-listings-agentic-ai-engineer-advance-career-solutions-india-5-to-10-years-210826016506 | 30d |
| 5 | Senior Data Scientist - Agentic AI & LLMs | (20–35 L) | **2 days ago** | https://www.naukri.com/job-listings-senior-data-scientist-agentic-ai-llms-aspyra-hr-services-gurugram-bengaluru-delhi-ncr-4-to-9-years-210826004664 | 30d |
| 6 | LLM/Agentic AI Engineer | Zorba AI | **2 days ago** | https://www.naukri.com/job-listings-llm-agentic-ai-engineer-zorba-ai-kolkata-8-to-13-years-200826503231 | 30d |
| 7 | IN_Sr Associate_Azure AI/ML/Agentic AI Engineer _GCC | PwC SDC | **2 days ago** | https://www.naukri.com/job-listings-in-sr-associate-azure-ai-ml-agentic-ai-engineer-gcc-pricewaterhouse-coopers-service-delivery-center-kolkata-bengaluru-3-to-8-years-200826502564 | 30d |
| 8 | Agentic AI Architect | Air India | **2 days ago** | https://www.naukri.com/job-listings-agentic-ai-architect-air-india-gurugram-10-to-17-years-200826033590 | 30d |
| 9 | AI Engineer \| Gen AI, Agentic AI, Gemini, GCP & RAG | TCS | **Today** | https://www.naukri.com/job-listings-ai-engineer-gen-ai-agentic-ai-gemini-gcp-rag-tata-consultancy-services-india-8-to-10-years-220826011668 | 30d |
| 10 | Gen AI / ML Engineers | (pri; Hyd/BLR 5–8 yrs) | **Today** | https://www.naukri.com/gen-ai-jobs | 30d |
| 11 | GEN AI, Agentic AI, LLM Models, Python | MNC via Pracyva | **1 day ago** | https://www.naukri.com/gen-ai-jobs | 30d |
| 12 | Walk-in \|\| Gen AI Engineer | (25 Aug, Hybrid Hyderabad) | **Today** | https://www.naukri.com/gen-ai-jobs | 30d (event 25 Aug 2026) |
| 13 | Java Developer With Gen AI | The It Mind Services | **Today** | https://www.naukri.com/gen-ai-jobs | 30d — **mashup** |
| 14 | Data Scientist \| LLM \| RAG \| GenAI \| Langchain | Infosys | **1 day ago** | https://www.naukri.com/job-listings-data-scientist-llm-rag-genai-langchain-infosys-kolkata-chennai-bengaluru-6-to-9-years-060826015554 | 30d |
| 15 | Developer AIML | Airtel | **1 day ago** | https://www.naukri.com/job-listings-developer-aiml-airtel-gurugram-4-to-9-years-241125006899 | 30d |
| 16 | RAG/LLM Specialist Manager/Sr Manager | EXL | **1 day ago** | https://www.naukri.com/job-listings-rag-llm-specialist-manager-sr-manager-exl-bengaluru-6-to-11-years-210826012525 | 30d |
| 17 | Python Rag | Infosys | **2 days ago** | https://www.naukri.com/job-listings-python-rag-infosys-bengaluru-thiruvananthapuram-2-to-7-years-030826023270 | 30d |
| 18 | Tech … AIOPS and Automation Engineer-Senior | (Noida 7–10) | **5 days ago** | https://www.naukri.com/aiops-jobs | 30d |
| 19 | Agentic AI Engineer (TCS) | TCS | LinkedIn **~19 Aug 2026** | https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-tata-consultancy-services-4407045907 | 30d |
| 20 | Machine Learning Operations Engineer | Qualys Pune | LinkedIn **19 Aug 2026**; “4 days ago” / 200+ applicants | https://in.linkedin.com/jobs/view/machine-learning-operations-engineer-at-qualys-4417876201 | 30d |

**Stale-but-still-indexed (not in the 20, listed as freshness control):**

- Persistent Agentic AI walk-in **9 May 2026** still on Naukri (LAST_6_MONTHS).  
- Apple Search Engineer AI/ML dated **13 Mar 2026** in URL (`130326504104`) still on `ai-ml` SERP (“3+ weeks ago” chip vs months-old ID).  
- Databricks “ML Engineer Gen AI & LLM” chips **3+ weeks ago** on langchain SERP; URL IDs include `260425` / `180325` (Apr/Mar 2025) — **possible zombie postings**.  
- AIOps Engineer Pune/Coimbatore/BLR chip **3+ weeks ago**.

**Freshness conclusion (INFERENCE, LAST_30_DAYS):** Front pages of `agentic-ai` and `gen-ai` on 23 Aug 2026 are **dominated by 0–4 day chips** (Today, 1 day, 2 days). That is **high 30-day turnover** on services/GCC GenAI reqs. It does **not** prove net new demand (reposts, pan-India clones, walk-in spam). 90-day tail exists (walk-in leftovers, Apple/Databricks IDs).

---

## Title-inflation and JD-quality caveats

### 1. Keyword stuffing makes Naukri “AI jobs” unusable as occupational demand

- `ai` = **84,313** vs `agentic-ai` = **9,938** vs `llmops` = **678**. **VERIFIED FACT.**  
- `ai-automation` = **68,385** — larger than `artificial-intelligence` — because it ORs two generic tokens.  
- CBRE’s 64.500 “AI-tagged” Dec 2025 stock is the same phenomenon, professionally packaged.

### 2. Polluted occupation names

| Token | Honest occupation N (approx.) | Polluted N | Mechanism |
|---|---|---|---|
| Prompt Engineer | AmbitionBox **81**; Foundit **61** | Naukri **15,585** (June title) | Employer names “Prompt Info Services”, “Prompt consultant”; generic “prompt engineering” skill tag |
| LLM | hirist **2,246** (July) | Naukri `llm-jobs-in-india` **19,238**; `llb-llm` **23,849** | **Master of Laws** |
| RAG | Mostly GenAI on inspected SERP (**6,876**) | residual risk of other acronyms | Inspected listings were RAG-pipelines |
| AI Agent | Mix | Bangalore **1,853** | Salesforce **Agentforce**, BPO “AI agent”, true LLM agents |
| ML Engineer | mixed | **52,071** | “ML” in PLM/MES/manufacturing JDs (example: Pune ML Engineer “plm, mes”) |

### 3. Java + SQL + GenAI mashups (VERIFIED FACT of JD text)

From gen-ai SERP 23 Aug 2026:

> **Java Developer With Gen AI** — The It Mind Services, 5–8 yrs, Hybrid Bengaluru. Skills: “Java, generative ai, Agentic Ai, Design, Azure, DSA, Aiml, Spring Boot”. Posted **Today**.  
URL path on SERP: https://www.naukri.com/gen-ai-jobs

Infosys Gen AI Engineer (Glassdoor, Bengaluru) still lists **SQL** among must-haves in some variants; Tekskills “Gen AI Developer” clones list **sql** in skill chips. TCS Agentic JD requires **RPA (UiPath/AA/Blue Prism)** plus LangChain.

**INFERENCE:** A large fraction of services “GenAI” reqs are **backend/Java/SQL seats with a GenAI tag**, not LLM-system engineering.

### 4. Experience impossibility

- Cognizant Gen AI / RAG Engineer **16–20 years**. RAG is not a 16-year skill.  
- Infosys “Gen AI (9–12 Years)-Pan India” JD body still describes **classic ML** (regression, CNNs, RNNs, LSTMs, GANs) more than agents — **title/body mismatch**. URL: https://www.naukri.com/job-listings-gen-ai-9-12-years-pan-india-infosys-hyderabad-pune-bengaluru-9-to-12-years-270326034960  
- Advance Career Solutions: “Experience: 8 12 Years” for Agentic AI Engineer while Agentic production experience in the market is ~1–3 years for most candidates.

### 5. Pan-India clone spam

Tekskills “Gen AI Developer” repeated across Ghaziabad, Greater Noida, Gurugram, Faridabad, Noida, Sikandrabad, Chennai, Hyderabad on the same SERP with near-identical chips (“GCP Certification… BigQuery”). **VERIFIED FACT of SERP duplication, 23 Aug 2026.** Inflates city and national counts.

### 6. Pay fiction

Same title “Generative AI Engineer” on Indeed Bengaluru: **₹4.5–5 L** (TestUnity, 3+ yrs) vs **₹30–50 L** (YO IT Consulting, 4–6 yrs). **VERIFIED FACT.** Title is not a wage.

### 7. “Remote” fiction

Naukri `remote-ai-jobs` **29,611** vs `generative-ai-jobs-in-remote` **167**. The first is a keyword; the second is closer to a location tag. Instahyre remote GenAI **559** is the more credible curated remote stock.

### 8. LinkedIn “10,000+ Prompt Engineer”

Public LinkedIn header for `ai-prompt-engineer-jobs` is **10,000+**. AmbitionBox designation filter is **81**. **VERIFIED FACT of both.** LinkedIn’s public count is not an occupation census.

### 9. Walk-in theatre

TCS, Persistent, Blackstraw.ai still run **walk-in drives** for GenAI/Agentic titles in 2026. That is a **services staffing motion**, not a product-lab motion.

---

## Evidence gaps

1. **Exact LinkedIn integers** for India × keyword × city — Insufficient (N=public SERPs only; buckets).  
2. **Naukri experience filters 6–9 / 7–10 / 8–12 national** — Insufficient (N=3 city tests; 2 inert).  
3. **Standalone Noida vs Gurugram vs Delhi** — Insufficient (used NCR/Delhi slugs).  
4. **True WFH count** — only location-tag URLs (Remote GenAI 167; Remote AI 752) are usable; keyword “remote” is unusable.  
5. **Unique reqs vs multi-city clones** — not de-duplicated. All Naukri N are **posting-document counts**.  
6. **PIB Stanford 33%** — fetch denied 2026-08-23.  
7. **Nasscom 2026 PDF body** (Indeed partnership) — only HTML highlights, not the full table set.  
8. **Wipro / Cognizant / HCL national tagged volume** comparable to Infosys 4,523 / Accenture 3,442 — Infosys and Accenture facets captured; **Wipro employer facet not captured** (N=1 missed query). Live Cognizant/HCL JDs exist but no employer-facet N.  
9. **“AI SRE” / “observability LLM” as titles** — no clean high-N SERP.  
10. **Cutshort exact integer** — only “50+”.  
11. **TeamLease / Shine AI occupational taxonomy** — Shine prompt search polluted; TeamLease AI report **not fetched** (N=0 TeamLease primary).  
12. **Salary paid vs salary tagged** — Naukri facets ≠ CTC. AmbitionBox/Glassdoor samples are thin.  
13. **Databricks / Apple posting IDs vs freshness chips** — possible stale inventory; not audited at full-history depth.  
14. **Kaam.work 126,000 NASSCOM workforce figure** — not found on nasscom.in pages opened in this scan.  
15. **2.3 million job openings by 2027** (DD News) — methodology not verified.  
16. **Chennai gen-ai city-slug integer** — not captured (Chennai generative-ai-engineer **866** used instead).  

---

## Source appendix (full URLs)

### Job boards — Naukri

- https://www.naukri.com/ai-jobs  
- https://www.naukri.com/artificial-intelligence-jobs  
- https://www.naukri.com/ai-ml-jobs  
- https://www.naukri.com/ai-engineer-jobs  
- https://www.naukri.com/ai-developer-jobs  
- https://www.naukri.com/ai-automation-jobs  
- https://www.naukri.com/gen-ai-jobs  
- https://www.naukri.com/genai-jobs  
- https://www.naukri.com/genai-engineer-jobs  
- https://www.naukri.com/generative-ai-jobs  
- https://www.naukri.com/generative-ai-jobs-in-india  
- https://www.naukri.com/generative-ai-engineer-jobs  
- https://www.naukri.com/agentic-ai-jobs  
- https://www.naukri.com/langchain-jobs  
- https://www.naukri.com/rag-jobs  
- https://www.naukri.com/llm-jobs  
- https://www.naukri.com/llm-jobs-in-india  
- https://www.naukri.com/llmops-jobs  
- https://www.naukri.com/mlops-jobs  
- https://www.naukri.com/ml-ops-jobs  
- https://www.naukri.com/aiops-jobs  
- https://www.naukri.com/prompt-engineer-jobs  
- https://www.naukri.com/ml-engineer-jobs  
- https://www.naukri.com/machine-learning-jobs  
- https://www.naukri.com/machine-learning-engineer-jobs  
- https://www.naukri.com/ml-ai-jobs  
- https://www.naukri.com/infosys-ai-jobs  
- https://www.naukri.com/artificial-intelligence-jobs-in-bangalore  
- https://www.naukri.com/artificial-intelligence-jobs-in-bengaluru  
- https://www.naukri.com/artificial-intelligence-jobs-in-bengaluru-bangalore  
- https://www.naukri.com/ai-jobs-in-bangalore  
- https://www.naukri.com/ai-jobs-in-bangalore-bengaluru  
- https://www.naukri.com/gen-ai-jobs-in-bangalore  
- https://www.naukri.com/generative-ai-jobs-in-bangalore  
- https://www.naukri.com/generative-ai-jobs-in-bengaluru  
- https://www.naukri.com/generative-ai-engineer-jobs-in-bangalore  
- https://www.naukri.com/ai-agent-jobs-in-bangalore  
- https://www.naukri.com/artificial-intelligence-jobs-in-hyderabad-secunderabad  
- https://www.naukri.com/artificial-intelligence-jobs-in-chennai  
- https://www.naukri.com/ai-jobs-in-chennai  
- https://www.naukri.com/generative-ai-engineer-jobs-in-chennai  
- https://www.naukri.com/artificial-intelligence-jobs-in-chennai-and-tamil-nadu  
- https://www.naukri.com/artificial-intelligence-jobs-in-pune  
- https://www.naukri.com/ai-jobs-in-pune  
- https://www.naukri.com/artificial-intelligence-jobs-in-delhi  
- https://www.naukri.com/artificial-intelligence-jobs-in-delhi-ncr  
- https://www.naukri.com/ai-jobs-in-delhi-ncr  
- https://www.naukri.com/generative-ai-jobs-in-delhi-ncr  
- https://www.naukri.com/ai-engineer-jobs-in-delhi  
- https://www.naukri.com/artificial-intelligence-jobs-in-coimbatore  
- https://www.naukri.com/ai-jobs-in-coimbatore  
- https://www.naukri.com/remote-ai-jobs  
- https://www.naukri.com/remote-artificial-intelligence-jobs  
- https://www.naukri.com/artificial-intelligence-jobs-in-remote  
- https://www.naukri.com/generative-ai-jobs-in-remote-6  
- https://www.naukri.com/artificial-intelligence-jobs-in-bangalore-4-to-8-years  
- https://www.naukri.com/artificial-intelligence-jobs-in-chennai-4-to-8-years  
- https://www.naukri.com/artificial-intelligence-jobs-in-pune-4-to-8-years  

### Job boards — others

- https://in.linkedin.com/jobs/artificial-intelligence-engineer-jobs  
- https://in.linkedin.com/jobs/generative-ai-engineer-jobs  
- https://in.linkedin.com/jobs/ai-prompt-engineer-jobs  
- https://in.linkedin.com/jobs/agents-ai-jobs  
- https://in.linkedin.com/jobs/artificial-intelligence-jobs-bengaluru  
- https://in.linkedin.com/jobs/artificial-intelligence-jobs-pune  
- https://in.indeed.com/q-ai-engineer-jobs.html  
- https://in.indeed.com/q-generative-ai-engineer-jobs.html  
- https://in.indeed.com/q-generative-ai-engineer-l-bengaluru,-karnataka-jobs.html  
- https://in.indeed.com/q-agentic-ai-engineer-jobs.html  
- https://in.indeed.com/q-ai-automation-jobs.html  
- https://www.instahyre.com/generative-ai-jobs/  
- https://www.instahyre.com/generative-ai-jobs-in-bangalore/  
- https://www.instahyre.com/generative-ai-jobs-in-hyderabad/  
- https://www.instahyre.com/remote-generative-ai-jobs/  
- https://cutshort.io/jobs/artificial-intelligence-ai-jobs  
- https://www.iimjobs.com/artificial-intelligence-jobs-in-bangalore  
- https://www.hirist.tech/k/llm-jobs  
- https://www.ambitionbox.com/jobs/prompt-engineer-jobs-prf  
- https://www.foundit.in/search/prompt-engineer-jobs  
- https://www.foundit.in/search/mlops-jobs  
- https://www.shine.com/job-search/prompt-jobs  
- https://dic.gov.in/jobs/mlops-engineer/  

### Macro / official

- https://www.deloitte.com/in/en/about/press-room/bridging-the-ai-talent-gap-to-boost-indias-tech-and-economic-impact-deloitte-nasscom-report.html  
- https://www.deloitte.com/in/en/issues/generative-ai/advancing-india-ai-skills.html  
- https://community.nasscom.in/communities/data-science-ai-community/advancing-indias-ai-skills-interventions-and-programmes  
- https://nasscom.in/knowledge-center/publications/advancing-indias-ai-skills-interventions-and-programmes-needed  
- https://indiaai.gov.in/article/india-s-ai-talent-pool-to-grow-to-1-25-million-by-2027-nasscom-deloitte-india-report  
- https://timesofindia.indiatimes.com/business/india-business/nasscom-deloitte-report-urges-rapid-upskilling-of-indias-tech-workforce-in-ai/articleshow/112637175.cms  
- https://community.nasscom.in/communities/nasscom-insights/indias-ai-talent-inflection-point-skill-gaps-competitive-advantage  
- https://nasscom.in/knowledge-center/publications/indias-ai-talent-inflection-point-skill-gaps-competitive-advantage  
- https://www.indiatoday.in/jobs/story/ai-jobs-in-india-rise-51-as-skills-first-hiring-and-tier-2-cities-reshape-workforce-india-linkedin-head-educ-2976508-2026-08-21  
- https://www.news18.com/business/70-of-ai-jobs-located-in-these-3-indian-cities-naukri-com-report-ws-kl-9916184.html  
- https://www.newkerala.com/news/a/bengaluru-delhi-ncr-emerge-as-primary-hubs-50-share-586.htm  
- https://m.economictimes.com/tech/artificial-intelligence/bengaluru-pune-hyderabad-mumbai-and-chennai-dominate-indias-ai-talent-map-report/articleshow/131818462.cms  
- https://ddnews.gov.in/en/indias-ai-sector-poised-to-surpass-2-3-million-job-openings-by-2027-report/  
- https://www.pib.gov.in/PressReleasePage.aspx?PRID=2226912 (blocked 2026-08-23)  
- https://indiaai.gov.in/  

### Representative live JDs (non-exhaustive; see taxonomy table)

- https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-tata-consultancy-services-4407045907  
- https://in.linkedin.com/jobs/view/gen-ai-developer-walk-in-for-pune-at-tata-consultancy-services-4446999013  
- https://in.linkedin.com/jobs/view/generative-ai-forward-deployed-engineer-google-cloud-at-google-4451133303  
- https://in.linkedin.com/jobs/view/machine-learning-operations-engineer-at-qualys-4417876201  
- https://in.linkedin.com/jobs/view/llm-systems-ai-agent-engineer-remote-full-time-as311-at-smart-working-4452587679  
- https://in.linkedin.com/jobs/view/senior-ai-engineer-agentic-ai-llm-reasoning-at-aivar-innovations-4375632410  
- https://in.linkedin.com/jobs/view/ai-engineer-genai-agentic-ai-and-mlops-at-navasys-technologies-4442345026  
- https://in.indeed.com/viewjob?jk=c8dae521f08ed811  
- https://in.indeed.com/viewjob?jk=856b1ad053f2c5bb  
- https://in.indeed.com/viewjob?jk=a2a2bc015a050bd0  
- https://www.glassdoor.co.in/job-listing/agentic-ai-engineer-infosys-JV_IC2940587_KO0,19_KE20,27.htm?jl=1010089163760  
- https://www.glassdoor.co.in/job-listing/genai-hyderabad-bengaluru-chennai-pune-deloitte-JV_IC2940587_KO0,38_KE39,47.htm?jl=1010016317513  

---

**End of A1 scanner.** Counts are point-in-time RAW retrievals for 16–23 August 2026. Re-query the same URLs before using them as current inventory; Naukri `ai-engineer` moved **49,520 → 46,957** inside this window.
