# services-gcc JD harvest log — 23 Aug 2026

**Agent:** JD mining (services / GCC India).  
**Output:** `research/jd-raw/services-gcc.tsv`  
**Unique N:** **99** (target 60–100). Zero fabricated listing IDs or salaries.

## Method

1. `web_search` with `site:naukri.com/job-listings`, `site:naukri.com/{company}-*-jobs`, `site:in.linkedin.com/jobs/view`, employer `careers.*` / `usijobs.deloitte.com` / `careers.dxc.com` / `careers.capgemini.com` / `careers.cognizant.com`.
2. Queries: GenAI OR Agentic OR LLM OR AI Engineer OR AIOps OR Copilot OR Now Assist, India, plus Chennai/Coimbatore.
3. Direct GET of Naukri HTML: **Akamai Access Denied** (same as A1/A3). Bodies for Naukri rows are **Google-indexed listing pages** or **SERP cards**. Status `INDEXED-LIVE` (full listing snippet) vs `INDEXED-LIVE-PARTIAL` (company-slice card only).
4. Opened employer careers where search returned a req URL. Capgemini Navi Mumbai **LIVE**. Cognizant `00067173931` **LIVE**. Several Cognizant/NTT/Capgemini reqs **404 or “position filled”** — filled pages not stored as ACTIVE.
5. LinkedIn guest pages: best full-text. Recency from guest “Xd ago” / applicant chips on 23 Aug 2026.
6. Same-day A3/W1 public IDs reused only when this pass still saw the ID in search (TCS `4407045907`, Infosys `4416389669`/`4441390349`, Accenture `4456383755`, Capgemini `4437769635`, Persistent `4453886301`, EY `4432756779`, UST `4441090818`).

## Recency / status tags in TSV

| status | Meaning |
|---|---|
| LIVE | Public body retrieved 23 Aug 2026 (careers still serving or LinkedIn guest with current chip). |
| INDEXED-LIVE | Listing URL still in Google/Naukri index (~last 30 days on card) with a job-description snippet; GET may 302/Akamai. |
| INDEXED-LIVE-PARTIAL | Company-slice SERP card (title, loc, YOE, skills, posted) — **no unique `job-listings-*` slug**. URL is the company jobs page. |

## Company coverage (99 rows)

| Company (as posted) | N | Notes |
|---|---:|---|
| TCS | 14 | Naukri listings + LI + Glassdoor + SERP (Chennai salary cards). |
| Infosys | 13 | LLMOps, Agentic 15–27.5 LPA, LI Bengaluru East **LIVE**. |
| Cognizant | 11 | Careers Chennai **LIVE**; FDE BLR/Chennai; LangGraph 7–13; architect MCP/A2A. |
| Wipro | 7 | Agentic mandatory 5–10; consultant-posted 24–30 / 35–40 LPA. |
| Accenture in India + Accenture | 8 | LLM architect, LLMOps Pune, LearnVantage trainer Hyd, RDE agentic. |
| KPMG India | 6 | Vertex/Gemini agents; Pune Senior Gen AI; Gurugram MCP/Copilot; full-stack. |
| EY | 5 | SAP BTP LLM Hyd; GDS AIA Manager/Senior BLR+Trivandrum; Azure Foundry 10+. |
| PwC / AC / India | 7 | Agentic automation lead; AIOps fleet SRE; Kolkata/BLR/Mumbai early joiners. |
| Capgemini + Invent | 4 | Navi Mumbai careers **LIVE** 16 Aug / 7 Aug; BLR LI; Azure AIFoundry. |
| Deloitte / USI / Consulting | 4 | USI L40 Hyd/BLR **LIVE**; Naukri Agentic developer; Chennai in pan-India GenAI. |
| DXC Technology | 3 | Careers Chennai MCP/RAG; Senior Gen AI pan-India; BLR full-stack agentic. |
| Tech Mahindra | 2 | Bedrock agentic WFH Hyd **Today**; Orion architect Mumbai. |
| LTIMindtree / LTM | 3 | MCP+Google ADK BLR; Agentic architect Hyd; Gen AI + Copilot/ADO. |
| Persistent / Persistent Systems | 3 | Hyd + BLR Agentic/GenAI twins; Senior AI OPS Pune. |
| Altimetrik | 2 | GEN AI Engineer **Today** BLR; Eng Manager GenAI. |
| Fractal | 2 | Uplers Agentic architect BLR; Shine Data Scientist GenAI/agentic. |
| Hexaware | 1 | GenAI+Agentic 12–22 LPA Hyd/BLR/Pune; NL2SQL. |
| NTT DATA | 1 | Mid-level GenAI Hyd (Glassdoor; careers twin later filled). |
| Tiger Analytics | 1 | Senior/Lead GenAI Chennai. |
| UST | 1 | AI Engineer BLR 3–5 / agents. |
| HCLTech | 1 | Generative AI Engineer 10–18 Hyd/BLR. |

## Searched, **no unique ACTIVE IC URL captured this pass**

Do not invent rows. Marketing/press exists; public IC JD did not land.

- **IBM** — Agentic AI Innovation Center Bengaluru (press); careers search did not yield a fetchable India GenAI IC req.
- **Mphasis** — Tria/NeoIP press; no `job-listings` / LI IC URL in this window.
- **Publicis Sapient** — US/product blogs; no India IC listing.
- **Thoughtworks** — whitepaper only.
- **Zensar** — ZenseAI press; no IC JD.
- **LatentView, Mu Sigma, Genpact, EXL** — no unique listing URL with GenAI/Agentic/LLM/AIOps in this harvest.
- **Coimbatore** — **0 rows** on this 30-company list. Chennai **28** rows (TCS, Infosys, Wipro, Cognizant, Altimetrik family, DXC, Deloitte pan-India, PwC Kolkata/BLR/Mumbai, Tiger Chennai).

## Failed / blocked fetches (explicit)

- `naukri.com/tcs-ai-jobs`, `infosys-ai-jobs`, `cognizant-ai-jobs`, `wipro-gen-jobs`, `agentic-ai-jobs` — Akamai Access Denied.
- Capgemini Pune C2, Bangalore HR Architect, Hyderabad Agentic AI developer, Noida Architect — **Sorry, this position has been filled** (excluded).
- NTT DATA Hyderabad `1387602600` and Mid-level `1326004100` — **filled** on careers GET; Glassdoor snippet retained as INDEXED-LIVE (SG080).
- Cognizant `00065637962` 404 (French careers); `00068075031` 404 on 23 Aug — JD from Google index.
- Tiger Analytics SenseHQ `56718` — **This Job Is No Longer Available**.
- Shine Fractal page JS-home on GET; body from Google snippet.

## Inclusion rules applied

**In:** GenAI / Agentic / LLM / LLMOps / AIOps / RAG / Copilot / MCP / Now Assist-adjacent agentic / FDE.  
**Out:** Pure Java/Spring + “plus ChatGPT”; unpaid internships; non-India locations (Capgemini Utrecht/NY, Cognizant Dallas/London skipped).  
**Salary:** Employer Naukri/Uplers figures only. Glassdoor bands labelled **EST (not employer)**.  
**Java/SQL:** Counted from captured text (`Y` / `N` / `Unk`). Many Python-first; TCS 4–8 lists Java **or** C++; Wipro SERP card lists java; Cognizant architect lists Java/C#; EY GDS and DXC Chennai require SQL.

## Harvest queries (this pass)

| # | Query | Used |
|---|---|---|
| 1 | `site:naukri.com/job-listings` TCS/Infosys/Wipro/HCL/TechM/LTI/Persistent Agentic OR Gen AI | Listing URLs + bodies |
| 2 | `site:naukri.com/tcs-ai-jobs` etc. | SERP cards (PARTIAL) |
| 3 | `site:in.linkedin.com/jobs/view` company + Agentic/GenAI India | TCS, Infosys, Accenture, PwC, EY, KPMG, Persistent, DXC, Tiger, UST |
| 4 | Capgemini / Cognizant / Deloitte USI / DXC careers URLs | LIVE + filled/404 |
| 5 | Hexaware, Altimetrik, Fractal Uplers/Shine, NTT Glassdoor | Salary-bearing rows |
| 6 | Coimbatore + Chennai + company | Chennai yes; Coimbatore none on list |
| 7 | IBM/Mphasis/Thoughtworks/Zensar/Genpact/EXL/LatentView/Mu Sigma/Publicis | Gap (press only) |

**Unique N = 99.**
