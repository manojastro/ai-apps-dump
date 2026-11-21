# Naukri Google-index harvest — ops / copilot / platform

**Agent:** JD mining (Naukri Google index).  
**Access window:** 2026-08-23.  
**File:** `naukri-ops-copilot.tsv`  
**Rule:** Zero fabrication. Rows are Google-index / Shine / Foundit cards only. Naukri HTML GET = Akamai 403. Individual `job-listings-*` URLs are permalinks from the index, not live-fetched bodies.

---

## Unique N and split

| Metric | N |
|---|---|
| Unique rows in TSV | **119** (target 80–120) |
| Unique URLs | 119 |
| Naukri | 109 |
| Shine twins | 5 |
| Foundit twins | 5 |
| **ops / ITSM-adjacent** | **68** |
| **core ML / GenAI-LLM IC** | **51** |

**ops/ITSM-adjacent (68):** AIOps, Observability+AI, SRE AI, Now Assist, ServiceNow Agentic, Copilot Studio, Intelligent Automation, Forward Deployed AI, AI Platform Engineer, plus MLOps cards whose chips also name AIOps/observability.

**core ML (51):** LLMOps/MLOps (model/pipeline), Data Scientist Azure OpenAI, AI/ML / Agentic / GenAI IC without ITSM language.

Java/SQL: **Y** only when the card named it (NK017 Java; NK060 Java OR Python). Else **Unk**. No SQL-Y on this harvest.

---

## Page-title RAW counts (verbatim Google titles, 23 Aug 2026)

Observed **more than once** as the index recrawled during the session:

| Query / URL | RAW page title (as indexed) | Count in title |
|---|---|---|
| `site:naukri.com aiops-jobs` | **Aiops Jobs - 558 Aiops Job Vacancies In August 2026 - Naukri.com** | **558** |
| same URL, later crawl | **640 Aiops Job Vacancies In August 2026** | **640** |
| same URL, later crawl | **680 Aiops Job Vacancies In August 2026** | **680** |
| `site:naukri.com llmops-jobs` | **Llmops Jobs - 678 Llmops Job Vacancies In July 2026 - Naukri.com** | **678** (July title still indexed) |
| same URL, later crawl | **877 Llmops Job Vacancies In August 2026** | **877** |
| `site:naukri.com mlops-jobs` | **Mlops Jobs - 4207 Mlops Job Vacancies In August 2026** | **4207** |
| same URL, later crawls | **4082** / **4012** / **4138 Mlops Engineer Job Vacancies In August 2026** | 4082 / 4012 / 4138 |
| `naukri.com/agentic-ai-jobs` | **Agentic Ai Jobs - 9938 Agentic Ai Job Vacancies In August 2026** | **9938** |
| agentic-ai-jobs page variants | 9753 / 10388 / 10138 / 9136 / 8960 | volume page churn |
| `naukri.com/openai-jobs` | **3897 Openai Job Vacancies In August 2026** | 3897 |
| `naukri.com/generative-ai-jobs` | **10503 Generative Ai Job Vacancies In August 2026** | 10503 |
| `naukri.com/llm-jobs` | **20450 Llm Job Vacancies In August 2026** | 20450 |
| `naukri.com/mlops-engineer-jobs` | **4138 Mlops Engineer Job Vacancies In August 2026** | 4138 |
| Foundit `aiops-jobs-in-pune` | **3404 Aiops Jobs in Pune** | 3404 (noisy aggregator) |
| Foundit `full-time-aiops-tooling-jobs` | **1011 Full Time Aiops Tooling Jobs in India** | 1011 |
| Foundit Copilot Studio PVA | **1475 Copilot Studio Power Virtual Agents Jobs in India** | 1475 |
| Foundit Now Assist | **52257 Now Assist Generative Ai Jobs in India** | 52257 (token-match noise) |
| Shine `aiops-jobs` | **225 Active aiops Jobs Openings (May 2026)** | 225 (stale month in title) |

**Primary volume anchors for this pass:** AIOps **558** (first Google title) then 640/680; LLMOps **678** (July title) then **877**; MLOps **4207**; Agentic AI **9938**.

---

## Queries run (ALL + city + recency)

### Required base queries

| # | Query | Result |
|---|---|---|
| 1 | `site:naukri.com/job-listings AIOps` | Google often **dropped the site operator** (AWS/Cisco AIOps explainers). Recovered via `naukri.com/job-listings AIOps Engineer Bengaluru OR Hyderabad OR Pune OR Chennai` and volume `aiops-jobs`. |
| 2 | `site:naukri.com/job-listings LLMOps` | Same operator drop. Recovered via `naukri.com/job-listings LLMOps Engineer …` and `llmops-jobs`. |
| 3 | `site:naukri.com/job-listings MLOps Generative` | Recovered via `mlops-jobs` + `Gen AI / Agentic AI / MLops` listing URLs. |
| 4 | `site:naukri.com/job-listings Copilot Studio` | Worked as `naukri.com/job-listings "Copilot Studio" Bengaluru OR Hyderabad OR Pune OR Gurgaon`. |
| 5 | `site:naukri.com/job-listings Now Assist` | Worked as `naukri.com/job-listings "Now Assist"` / TCS/Cognizant/Atos variants. |
| 6 | `site:naukri.com/job-listings ServiceNow Agentic` | Purview Pune/Hyd listings + Tekskills/Solarix. |
| 7 | `site:naukri.com/job-listings Intelligent Automation GenAI` | Cognizant GEN AI, Maersk, Tekskills Gen AI Automation, Zensar. |
| 8 | `site:naukri.com/job-listings AI Platform Engineer` | Sutherland, Experis, Quincy, Guardian, Randstad Salesforce AI, TCS GCP AI Platform. |
| 9 | `site:naukri.com aiops-jobs` | **Best AIOps surface.** RAW 558→640→680. Cards: EY Coimbatore 3–5 ₹8–15 LPA; EY 5–7; EY Noida 7–10; Premium Aerotec; S&P; TCS. |
| 10 | `site:naukri.com llmops-jobs` | RAW 678 July → 877 Aug. Infosys, Capgemini, Crescendo, Coforge. |
| 11 | `site:naukri.com mlops-jobs` | RAW 4207→4082. Adecco 14–20 LPA; Aspyra 25–35 LPA; Cloudxtreme 9.5–15 LPA; PwC; Capgemini; HCL walk-in. |
| 12 | `site:naukri.com/job-listings Azure OpenAI` | EY .NET Full Stack Azure OpenAI; Anlage Data Scientist; Cognizant GenAI GCP/Azure; Infosys Bedrock/Azure OpenAI. |
| 13 | `site:naukri.com/job-listings AWS Bedrock Engineer` | Gainwell listing **did** return a full Google-indexed JD (Mar listing, excluded as >30d). Kept Aug Tekskills + Infosys Bedrock cards. |
| 14 | `site:naukri.com/job-listings Forward Deployed AI` | Cloudera FDE BLR; Datavruti Agentic FDE; TCS Sr FDE. Atlassian Remote 15–20 **excluded** (India not confirmed). |

### City variants

Bengaluru / Bangalore, Hyderabad, Chennai, Pune, NCR (Noida, Gurugram, Delhi / NCR), Coimbatore, Remote, Hybrid — appended to listing queries. Coimbatore hit: **EY Hybrid Cloud AIOps Senior Engineer** 3–5 Yrs ₹8–15 LPA (SERP card on `aiops-jobs`; no `job-listings-*` permalink in the index this pass → URL is the volume page).

### Recency variants

`"1 day ago"` / `"3 days ago"` / `"week ago"` plus Freshness chips on volume SERPs: **Just now**, **Few hours ago**, **17 hours ago**, **1–6 days ago**, **3+ weeks ago**. Prefer last 30 days. Listing-id dates `DDMMYY` used as corroboration (e.g. `210826` = 21 Aug 2026).

### Foundit / Shine twins (when Naukri URL missing or to corroborate)

Shine: EY Senior AIOps 19275996; Neal Analytics LLMOps 19215647; Clowise Copilot Studio; Live Connections Azure Copilot Studio; RED Global Agentic+Copilot. Coforge LLMOps Shine twin folded into NK057 snippet (not a second row).  
Foundit: Accellor Copilot Studio Hyd; Astellas Copilot Studio BLR; OP Crypto Copilot Studio; Mythics Copilot Studio ops; TCS Now Assist Integration Hub Hyd.  
Foundit Chubb AIOps ServiceNow Hyd and Deloitte Copilot Studio Senior Analyst Hyd: **no longer accepting** — not in TSV.

---

## Method limits (explicit)

- `web_fetch` of `naukri.com/aiops-jobs`, `llmops-jobs`, `mlops-jobs` → **Access Denied** (Akamai `errors.edgesuite.net`). Same as A1/A3.
- Google `site:naukri.com/job-listings <keyword>` frequently ignored `site:` and returned vendor blogs. Workaround: `naukri.com/job-listings-<slug>` URL pattern + volume pages + quoted titles.
- Status **INDEXED-LIVE PARTIAL**: index still showing the card; listing URL not HTML-fetched this pass (would 302/Akamai). Snippet is the Google/Shine/Foundit card only.
- Salary only when the card showed it (employer LPA or AmbitionBox estimate labelled as such).
- Excluded: internships, Ahmedabad-only, Mumbai-only (unless Hybrid with in-scope city), Feb–May 2026 listings, walk-in dates in the past, US Remote without India.

---

## Recency mix in TSV (as posted on cards)

Most rows are **Aug 2026** or **“N days ago”** on 23 Aug 2026. A few late-Jul listing IDs remain indexed (`170726` EY 5–7, `250726` TCS Now Assist Specialist, `240726` Lecan / Iris). EY Coimbatore 3–5 card was **3+ weeks ago** on the 558/640 volume SERP.

---

## Not used (indexed but out of rule)

- Tech Mahindra AIOps Pune `100526004665` (10 May).
- Gainwell AWS Gen AI Engineer `060326010420` (Mar; full body in Google index).
- Logic Planet Copilot Studio Gurugram `200226502353` (Feb).
- Flexsin Microsoft Copilot Noida May 2025.
- Dhata Tech AIOps Pune 2023.
- Kinara AIOps Noida Feb 2026.
- Credence MLOps+LLMOps Pune Apr 2026.
- Redde ServiceNow Agentic Pune Mar 2026.
- Acara Now Assist Ahmedabad (city out of scope).
- Atlassian Senior Principal FDE Remote 15–20 (India not on card).
