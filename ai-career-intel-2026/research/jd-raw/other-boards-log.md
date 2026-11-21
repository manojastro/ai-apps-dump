# Other-boards JD harvest log — 23 Aug 2026

**Agent:** JD mining (other boards).  
**Output:** `research/jd-raw/other-boards.tsv`  
**Rule:** Zero fabrication. India-only. Employer-disclosed salary only (Glassdoor estimates excluded). Java/SQL counted from listing text/chips, else `Unk`.

## Result

| Metric | Count |
|---|---|
| **Unique rows (N)** | **119** |
| **Employer-disclosed salary** | **8** |
| Header columns | 13 (tab-separated, exact header) |
| Unique URLs | 119 (no duplicates) |

### Source mix

| source | N |
|---|---|
| instahyre | 35 |
| indeed | 20 |
| glassdoor | 17 |
| foundit | 16 |
| careers | 14 |
| hirist | 10 |
| cutshort | 7 |

### Status mix (23 Aug 2026)

| status | N | Meaning this pass |
|---|---|---|
| LIVE | 28 | Full/partial body retrieved from listing or employer careers |
| INDEXED-LIVE | 76 | Google/board still serving the listing; page JS-walled, 403, or Indeed login |
| RECENT-CLOSED | 13 | “no longer accepting” / EY careers “Job is no longer available” |
| EXPIRED | 2 | Indeed “expired” or Google Careers “Job not found” |

### Java / SQL flags

- Java **Y**: 8 (explicit Java / Spring Boot / Java as skill chip or primary skill)
- SQL **Y**: 7 (SQL, PostgreSQL, MySQL, or “database design” named)
- Remainder `N` (skills list present, Java/SQL not named) or `Unk` (body not fully visible)

### Eight disclosed salaries (employer-stated, not Glassdoor estimates)

1. Unique Occupational / MNC client (Cutshort) — GEN AI Engineer (Agentic AI), Gurugram — **₹32–35 LPA**
2. BigRio (Cutshort) — Generative AI Engineer, Chennai — **₹22–55 LPA**
3. Logikality (Cutshort) — Generative AI Engineer, Bengaluru — **₹15–20 LPA** (+ ESOP)
4. Sentiaflow (Cutshort) — Agent Application Engineer L1 — **₹24–35 LPA**
5. Indeed `jk=949ff68293f48d40` — Generative and Agentic AI Engineer, Bengaluru — **₹18–30 LPA**
6. Indeed `jk=d510a189195d54a0` — Generative AI Engineer (5+ yrs), Indore — **₹50,000–₹90,000 / month**
7. Eximietas NVIDIA ecosystem (Indeed `jk=180be82e82033c3e`) — Bangalore — **up to ₹28–29 LPA**
8. Kasmoprav (Glassdoor) — Lead GenAI / Agentic AI Engineer, Remote IST — **₹1.30 LPM + GST**

## Queries run (23 Aug 2026)

- `site:in.indeed.com Generative AI Engineer`
- `site:in.indeed.com Agentic AI`
- `site:in.indeed.com AIOps`
- `site:in.indeed.com/viewjob` variants (GenAI / Agentic / AIOps / Coimbatore)
- `site:www.instahyre.com generative-ai` and `/job` title filters
- `site:www.hirist.tech GenAI OR Agentic OR LLM`
- `site:www.foundit.in Generative AI Engineer` and `/job` cards
- `site:www.glassdoor.co.in/job-listing GenAI OR Agentic`
- `site:www.cutshort.io` GenAI / Agentic
- `careers.cognizant.com` Gen AI / Agentic India
- `careers.microsoft.com` / `jobs.careers.microsoft.com` India AI Engineer
- `google.com/about/careers` India Generative AI / FDE
- `www.amazon.jobs` India Generative AI / AI Engineer
- ServiceNow, Zoho, Freshworks, Bosch Coimbatore AI

## Fetch outcomes (explicit)

| Surface | What happened |
|---|---|
| **Indeed HTML** | Direct `web_fetch` of SERP → **Security Check**. Individual `viewjob` → **login redirect**. Rows are **INDEXED-LIVE** from Google-indexed Indeed cards (`jk=` kept). |
| **Foundit HTML** | Search and job URLs → **Akamai Access Denied**. Rows from **Google-indexed Foundit cards**. |
| **hirist.tech `/j/`** | **JS shell** (“Loading chat…”). Titles, exp, location, posted dates from **Google index**. |
| **Instahyre `/job-*`** | Title, company, location, YOE, skill chips retrieved. Full JD body often Angular-templated. Closed jobs labelled **RECENT-CLOSED**. |
| **Cutshort** | **Best salary disclosure** this pass. Full JD bodies retrieved. |
| **Glassdoor** | Listing pages JS-heavy; bodies from **indexed snippets**. Glassdoor Est. pay **not** written to `salary`. Kasmoprav **₹1.30 LPM** is employer budget language. |
| **Cognizant careers** | **LIVE** bodies: `00067173931`, `00067071131`, `00067697575`, plus Master Frontier / MLOps / Chief Architect / Responsible AI. |
| **ServiceNow careers** | **LIVE**: Senior Staff AI-Native SWE – Agentic Systems (Bangalore, 8+); AI Agent Engineer – Moveworks (Bangalore, 18 Aug 2026). |
| **Amazon.jobs** | **LIVE** 10373084 Senior SA Developer Transformation, Bengaluru (AI coding agents). Indexed 10426389 GenAI Data Engineer II Karnataka; 10422019 Principal AI Specialist BLR/Mumbai/Gurugram. |
| **Google Careers** | GECX FDE URL **404 “Job not found”** (row kept as EXPIRED; prior index said Bengaluru). FDE III page opened as **US locations only** — **not included**. |
| **EY careers** | Staff Agentic AI Engineer Bengaluru → **“The Job is no longer available.”** Body retained from prior index (Python, SQL, Azure OpenAI). |
| **Microsoft Careers** | No verified **India** GenAI IC listing with a public JD body this pass (Hyderabad hits were Search/Windows leadership or US pay bands). |
| **Zoho careers** | No verified GenAI / LLM IC JD on `zoho.com/careers` / `careers.zohocorp.com`. |
| **Freshworks** | No public GenAI IC listing on careers/Lever this pass. |
| **Bosch Coimbatore** | No verified Bosch career-site AI IC JD. Coimbatore AI/ML **did** appear on Indeed (Ventragate, Applogiq) and Instahyre (ShellKode closed). |

## Inclusion / exclusion

**In:** GenAI, Agentic, LLM, LLMOps, AIOps, RAG, Copilot Studio / ADK, Now Assist / Moveworks agents, FDE-style customer-deployed GenAI. India locations or India-remote.

**Out:** Non-India (Greece, Kraków, UAE Foundit). Google FDE III US-only. Glassdoor estimate bands. LinkedIn/Naukri as primary source (out of this file’s board list). Fabricated companies for hirist IDs without an indexed employer name (those IDs dropped rather than guessed).

**Company field:** `(Indeed listing)` used only when the indexed Indeed card did not name the employer; URL still unique (`jk=`). Hirist rows without an indexed employer were **dropped**.

## Coimbatore / requested employers

| Target | This pass |
|---|---|
| Cognizant | Multiple LIVE India careers rows |
| TCS / Infosys / Accenture | Present via Instahyre, Foundit, Indeed, Glassdoor (not always native careers HTML) |
| Microsoft | **Gap** — no India GenAI IC body |
| Google | GECX FDE **expired**; India FDE not serving |
| Amazon | Bengaluru SA + indexed GenAI DE / AI specialist |
| ServiceNow | Two LIVE Bangalore agentic rows |
| Zoho / Freshworks / Bosch | **Gap** on career pages |
| Coimbatore AI | ShellKode Gen AI Lead (Instahyre, closed); Ventragate + Applogiq Indeed |

## Quality notes

- N=119 is inside 80–120 unique. Volume was capped by dropping SERP-only Indeed query URLs, junior 0–2 YOE, and hirist pages with no indexed company.
- Many Instahyre “LIVE” rows still lack a full requirement paragraph (chips only) — treat as PARTIAL if used downstream.
- Indeed/Foundit/hirist **INDEXED-LIVE** can 302 or expire; re-open before applying.
- Recency: harvest date **2026-08-23**. Posted dates copied only when the index or page stated them.
