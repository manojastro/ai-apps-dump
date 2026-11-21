# Naukri GenAI JD harvest log

Harvest date: 2026-08-23  
Output: `research/jd-raw/naukri-genai.tsv`  
Unique rows written: **117**  
Source: Google `site:naukri.com` SERPs + `open_page` on volume URLs (Naukri origin often Akamai 403)

## Method

- Zero fabrication. Rows only from listings actually returned in `web_search` / `open_page` snippets.
- Prefer `https://www.naukri.com/job-listings-*` URLs.
- Volume SERP cards without a unique job-listings URL stored as `status=PARTIAL` (identity = volume URL + title + company).
- India only. Cities mixed: Bengaluru, Hyderabad, Chennai, Pune, NCR/Noida/Gurugram/Delhi, Coimbatore, Mumbai/Navi Mumbai, Remote/Hybrid, pan-India.
- `java`/`sql` = Y only when the skill appeared in the seen snippet; else U. N never assigned (full JD usually blocked).
- Deduped by job id / job-listings URL. Trimmed to 117 highest-signal unique rows (LIVE GenAI/Agentic/LLM/RAG first, plus Java/SQL Y, Coimbatore, PARTIAL cards).

## Queries run

### Required core
| Query | Result notes |
|---|---|
| `site:naukri.com/job-listings Generative AI Engineer` | Many job-listings URLs; volume bleed to `generative-ai-jobs` (10503) |
| `site:naukri.com/job-listings GenAI Engineer` | CGI, Docusign, Sia Partners, Franklin Templeton, Tredence, Parangat, Automationedge |
| `site:naukri.com/job-listings Gen AI Engineer` | Capgemini, Cloudseed, ADP, EY, Altimetrik, Tekskills, ZeMoSo, Involead |
| `site:naukri.com/job-listings Agentic AI Engineer` | Deloitte, PwC, Tech Mahindra, Blend360, NTT DATA, JPMC, The Glove, Amgen |
| `site:naukri.com generative-ai-engineer-jobs` | City + national volume; EaseMyTrip, PCDS, Einfochips, Infosys Pan-India |
| `site:naukri.com genai-engineer-jobs` | Title count **6691** Genai Engineer Jobs (`genai-engineer-jobs-1`) |
| `site:naukri.com agentic-ai-jobs` | Title count **9938** Agentic Ai Jobs (also 10281 in body copy) |

### City volume URLs
| URL / query | Raw count from page title / SERP |
|---|---|
| generative-ai-engineer-jobs-in-bangalore / bengaluru | **4032** / 4134 Generative Ai Engineer in Bangalore |
| generative-ai-engineer-jobs-in-hyderabad | SERP mixed with Hyderabad AI engineer volume; individual job-listings captured |
| generative-ai-engineer-jobs-in-chennai | **1178** / 1143 Generative Ai Engineer in Chennai |
| generative-ai-engineer-jobs-in-pune | **1660** / 1731 Generative Ai Engineer in Pune |
| generative-ai-engineer-jobs-in-noida | Via `generative-ai-jobs-in-noida` title **368** Generative Ai jobs in Noida |
| generative-ai-engineer-jobs-in-gurgaon / gurugram | Via `generative-ai-jobs-in-gurgaon` title **508** Generative Ai jobs in Gurgaon |
| Coimbatore | Zalway (Remote/Coimbatore), EY GDS Gen AI Specialist Manager, Nectar AI Engineer |

### Recency variants
| Query | Notes |
|---|---|
| `site:naukri.com/job-listings "Generative AI Engineer" "1 day ago" OR "3 days ago" OR "Today"` | Tekskills, United Techno, Purview, Involead, UST, PCDS, EaseMyTrip |
| `site:naukri.com/job-listings "Gen AI Engineer" Bengaluru OR Hyderabad OR Pune OR Chennai OR Noida OR Gurugram` | Tredence, EY Hyderabad, EPAM, Capgemini, Cognizant, CGI, Smart Source |
| `site:naukri.com/job-listings "Agentic AI" Engineer OR Developer Bengaluru OR Hyderabad OR Pune` | Capgemini, Advance Career, Blend360, NTT DATA, Tech Mahindra, PwC, Blackline |

### LLM / RAG / LangChain / LangGraph
| Query | Notes |
|---|---|
| `site:naukri.com/job-listings LLM Engineer India Bengaluru OR Hyderabad OR Pune OR Chennai` | TCS Python LLM, Optum Java+LLM, Zippyops LLM infra, HCLTech, Accenture LLM Ops, GlobalLogic |
| `site:naukri.com/job-listings RAG Engineer LangChain LangGraph` | Optum, Cloudxtreme, United Techno, Amantya, Bain, Nectar, Intelizign, Tekreant, Nisum, Cirruslabs |
| `site:naukri.com langchain-jobs` | Title **4122** Langchain Jobs. Infosys LLM/RAG/LangChain, Mount Talent, Turing, Airtel, Lancesoft |
| LangGraph / RAG / Java / SQL variants | EPAM Java+GenAI, CGI JAVA GenAI, Nagarro Spring AI, Cerebra Java+SQL, Zalway SQL, Sutherland SQL |

### Extra volume pages opened
- `https://www.naukri.com/agentic-ai-jobs` — **open_page OK**. Title: **9938 Agentic Ai Job Vacancies In August 2026**. Listing slice 1–20 of 9938. Location facets: Bengaluru 3887, Hyderabad 2180, Delhi/NCR 1531, Pune 1462.
- `https://www.naukri.com/gen-ai-jobs` — **open_page OK**. Title: **28722 Gen Ai Job Vacancies In August 2026** (search snippet also showed 28762). Location facets: Bengaluru 10123, Hyderabad 4723, Delhi/NCR 4568, Pune 3532. Many cards lacked job-listings URLs → PARTIAL where company was visible.
- `https://www.naukri.com/langchain-jobs` — **open_page OK**. Title: **4122 Langchain Job Vacancies In August 2026**.
- `https://www.naukri.com/generative-ai-jobs` — search snippet title **10503 Generative Ai Job Vacancies In August 2026**; direct `open_page`/`web_fetch` often empty or Access Denied.
- Direct `web_fetch` of naukri.com: **Access Denied** (Akamai). Individual `job-listings-*` pages frequently blocked; Google-indexed snippets used instead.

## Raw counts from page titles (as seen)

| Page | Count in title |
|---|---|
| Agentic Ai Jobs | **9938** |
| Generative Ai Jobs (Aug 2026) | **10503** |
| Gen Ai Jobs | **28722** (snippet 28762) |
| Genai Engineer Jobs | **6691** |
| Generative Ai Engineer Jobs in Bangalore | **4032** (snippet 4134) |
| Generative Ai Engineer Jobs in Chennai | **1178** (snippet 1143) |
| Generative Ai Engineer Jobs in Pune | **1660** (snippet 1731) |
| Langchain Jobs | **4122** |
| Generative Ai Jobs in Gurgaon | **508** |
| Generative Ai Jobs in Noida | **368** |
| Ai Engineer Jobs (national, mixed) | 46883–46972 (not used as GenAI-only count) |

These volume numbers are Naukri keyword-match totals (noisy; includes adjacent AI/ML roles), not unique GenAI-engineer JDs.

## TSV stats

| Field | Value |
|---|---|
| Unique rows | **117** |
| Unique ids | 117 |
| Unique URLs | 113 (4 PARTIAL rows share volume-page URLs) |
| source | naukri (all) |
| status LIVE | 101 |
| status INDEXED | 8 |
| status PARTIAL | 8 |
| java=Y | 12 |
| sql=Y | 12 |
| java=Y and sql=Y | 3 |
| java/sql unknown (U) | 105 / 105 |
| Blank snippet | 11 (listing seen; no JD text in snippet) |

## Caveats

- Naukri blocked most origin fetches. Recency/salary/skills are only what Google/open_page showed.
- `java=N` / `sql=N` not used; absence in a short snippet is not evidence of absence.
- Staffing posts (Tekskills, Purview, Advance Career) may be client-confidential; company field is the **posted-by** name seen on Naukri.
- Volume counts (9938 Agentic, 10503 Generative AI) are index sizes, not the harvest N.
