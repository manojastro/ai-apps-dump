# AI CAREER MARKET — MASTER RESEARCH REPORT (Global + India)
**Candidate profile:** Experienced enterprise IT professional (IT support / IT operations background)
**Research date:** August 2026 | **Method:** 10 parallel web-research workstreams, 100+ sources, pattern-discovery pipeline (Collect → Clean → Deduplicate → Normalize → Classify → Count → Compare → Cluster → Detect → Validate → Decide)

---

## 1. EXECUTIVE SUMMARY

1. **India will post ~380,000 AI jobs in 2026 (+32% YoY)** but can fill only ~30% of GenAI openings (TeamLease) — 1 qualified engineer exists for every ~10 open GenAI roles. Demand is real and supply-constrained.
2. **"AI Engineer", "GenAI Engineer", "LLM Engineer" are mostly the SAME job** (~80% of the market): Python + LLM APIs + RAG + vector DB + cloud + Docker. Search all titles together.
3. **Indian JDs price TOTAL IT experience + GenAI exposure — not "X years pure AI."** Cognizant literally posts "4–12 years total, 2+ relevant GenAI." An experienced IT professional can reposition laterally without an experience reset **if they carry 2–3 years of demonstrable GenAI work**.
4. **GCCs are the single best transition channel**: >2,100 centers, 56% of demand at 4–12 yrs experience, documented role-adjacent conversion paths (ops→platform, backend→applied AI), pay premium 15–25% (up to +40% for AI roles).
5. **For an IT-ops veteran, the lowest-friction doors into AI are:** AIOps/observability+AI, Cloud AI Engineer, AI Platform/LLMOps, ServiceNow+GenAI, and AI Security/Governance — NOT model-building roles (most attempted AND least successful pathway: first-line support → ML engineer).
6. **Cloud choice in India is segment-dependent:** Azure OpenAI dominates IT-services JDs; AWS+Bedrock dominates GCC/BFSI; startups split AWS Bedrock / GCP Vertex. Azure-first is the highest-volume bet for services; add Bedrock for GCCs.
7. **Agentic AI is a real skill market wearing an inflated title**: exact-title postings ≈1–10% of demand; the real signal is LangGraph/MCP/tool-calling/guardrails inside normal AI-engineer and architect JDs.
8. **The scarcest, best-paid differentiators in 2026 hiring are evals, observability, guardrails/governance, and cost engineering** — not model training. AI-governance hiring grows 3× faster than overall AI hiring in BFSI/pharma.

**Bottom line:** Target **Cloud AI Engineer → GenAI/AI Engineer (application layer) → AIOps/AI Platform as backup**, learn Azure OpenAI stack + Bedrock basics, build 3 production-grade deployed projects with evals, move laterally via GCCs or your current employer's AI practice.

---

## 2. RESEARCH METHODOLOGY

- **Pipeline:** COLLECT → CLEAN → DEDUPLICATE → NORMALIZE → CLASSIFY → COUNT → COMPARE → CLUSTER → DETECT PATTERNS → VALIDATE → IDENTIFY TRENDS → DISCOVER HIDDEN INSIGHTS → CONVERT INTO CAREER DECISIONS.
- **Sources used:** job boards & live counts (LinkedIn, Indeed US/IN, Naukri, Foundit, Glassdoor, Hirist, SimplyHired IN, Dice), scraped-JD benchmarks (InterviewStack n=3,449; Grigorev n=5,694; johal.in n=5,000; agentic-engineering-jobs.com n=1,135; Skillenai 90-day indexes), labor-market reports (Lightcast, Indeed Hiring Lab, LinkedIn Economic Graph, Stanford AI Index 2026, Gartner, Nasscom, TeamLease, Quess Corp workforce analysis (350K postings), Zinnov, ANSR, Everest Group, CIEL, ICRIER–OpenAI survey, Michael Page, Talenbrium HR pulse), salary aggregators (Levels.fyi, AmbitionBox, Taggd, MutualCS, 6figr), verbatim live JDs (Cognizant, Accenture, Infosys, TCS, Capgemini, BofA, PwC India, EY, Leidos), community evidence (Reddit r/MLOps, r/cscareerquestions, Hacker News, engineering blogs, recruiter posts), vendor/platform signals (Microsoft, Databricks, ServiceNow, NVIDIA careers).
- **Validation rule:** every pattern carries High/Medium/Low confidence based on independent-source count, JD volume, company count, geographic diversity, recency, community corroboration. Weak correlations are labeled, not promoted.
- **Separation of evidence:** anecdotal transition stories are reported separately from statistical hiring data throughout.

## 3. DATASET SIZE, COVERAGE & LIMITATIONS

| Dimension | Coverage | Limitation |
|---|---|---|
| Job volumes | Directional counts from public board searches; 3 independent JD scrapes (n=1,135–5,694) | Boards use fuzzy matching ("Agentic AI" keyword ≠ exact title); no audited India-normalized % splits |
| Salaries | Aggregator bands, recruiter placement data | Self-reported samples skew senior; startup equity rarely captured |
| Transitions | 1 statistical HR study (Talenbrium n=284 HR leaders) + multiple individual accounts | Individual stories are survivorship-biased anecdotes |
| Trend arrows | MoM/YoY deltas where published (Skillenai, Indeed, Lightcast) | Some trends rest on 2 independent sources only |
| Geography | Global (US-weighted) + India deep-dive | EU/APAC ex-India lighter coverage |
| Recency | Core data Mar 2025 – Aug 2026 | Fast-moving niches (MCP, agent frameworks) may shift within months |

**Not done (and therefore flagged wherever relevant):** no access to private ATS data, no paywalled LinkedIn Recruiter exports, no proprietary Naukri JobSpeak raw feeds. Counts marked [Medium]/[Low] should be treated as order-of-magnitude.

---

## 4. GLOBAL AI JOB MARKET

**Volume & growth**
- AI Engineer = #1 fastest-growing title on LinkedIn Jobs on the Rise **both 2025 and 2026** (+143% YoY in 2026). AI-engineering hiring +25% YoY (LinkedIn); ~7% of all technical postings (+63% YoY). Indeed US: ~52K open AI Engineer postings.
- GenAI Engineer postings grew 7× on Lightcast: 1,620 (2022) → 11,160 (2024), still rising through 2025. GenAI-skill postings: ~55/month (2021) → ~10,000/month (May 2025).
- Agentic-AI postings +280% YoY (~90K US fuzzy listings, Stanford AI Index 2026); agentic-skill mentions +986% (2023→24).
- Forward Deployed Engineer postings +800% (Jan–Sep 2025) but tiny absolute base (≈260 active US postings across 108 firms) — hot, niche.
- GenAI keywords appear in only ~0.3% of all US postings yet grow +170% YoY; total AI-term postings sit 134% above Feb-2020 baseline vs +6% for overall postings.
- **51% of AI-skill demand is now outside IT/CS departments** (Lightcast) — AI is diffusing into every function.

**Structure of demand**
- Scraped GenAI/LLM postings cluster into 4 genuine jobs: AI/ML Engineer (60), Research Scientist (52), Solutions Architect (48), MLOps/Infra (27) — i.e., **engineering >> research** in volume.
- Implementation beats model-building: management consultants alone were 12.4% of GenAI postings (Indeed, Jan 2025).
- AI added ~1.3M new jobs globally per LinkedIn/WEF data.

**Industry patterns (global):** BFSI & consulting lead enterprise GenAI deployment; gov-contractors drive the AWS Bedrock security-cleared niche; healthcare/pharma drive governed-RAG (compliance-heavy retrieval); retail/consumer drives recommendation + copilot stacks; cybersecurity vendors drive AI-security tooling demand. AI skills now appear most outside pure tech firms — manufacturing, insurance, telecom all posting double-digit growth.

## 5. INDIA AI JOB MARKET — DEEP ANALYSIS

**Macro**
- **290,256 AI vacancies posted in 2025 → ~380,000 forecast 2026 (+32%)**; GenAI/LLM-specific skill demand +60% YoY (Foundit tracker).
- Nasscom: AI-engineer roles +67% YoY; agentic AI = fastest-growing specialisation with acute unfilled shortage; ~2/3 of employers increased AI hiring (Nasscom–Indeed).
- Supply gap: **TeamLease reports it can fill only ~30% of client GenAI openings**; ~1 qualified engineer per 10 open GenAI roles. Only ~20% of India's IT workforce is AI-ready (industry estimates); Quess finds 36–53% AI-talent deficits by role family.
- Quess (350K-posting analysis): of 920K AI-skilled professionals, only 257K hold core-AI roles — **663K (72%) are people who ADDED AI to an existing function**. This is the structural proof that lateral repositioning works.
- Demand mix: majority of new AI-engineer postings ask RAG/vector-DB production skills; sharpest gaps in applied/production skills (RAG, MLOps, agentic), not theory.

**Experience language — the decisive finding**
Verbatim Indian JD formulas:
- Cognizant Gen AI Engineer (Jul 2026): "**Experience: 4 to 12 Years. Relevant Exp: 2+ Years**"
- Accenture Senior GenAI Engineer: "Min. **6 years commercial experience… including at least 2–3 years hands-on with LLMs**"
- Infosys: "**AWS Bedrock / Azure OpenAI with 2–5 years**"
- GlobalLogic: "Generative AI Engineer (**4 to 8 years**)" (stated on total experience)

→ Indian employers overwhelmingly ask **"total IT experience + some GenAI/LLM exposure"**, NOT "X years of pure AI experience". Corroboration: ICRIER–OpenAI survey — 63% of 650 firms demand hybrid domain+AI skills; Michael Page 2026 — 39% of managers prioritize skills over career history; datavaan hiring guide: "a senior backend engineer who has built two or three serious GenAI projects is more hireable than a fresh ML graduate."

**Experience-reset reality check**
- Risk is real but conditional: external switchers risk junior re-entry (age bias data point: 90% of US hiring managers consider under-35s for AI roles vs 32% for 60+); internal/lateral moves preserve level & comp.
- Counter-strategies observed repeatedly: (1) move internally first — redeployment costs employers 62% less than exit+re-hire, so they're motivated; (2) target ops-adjacent AI roles where tenure IS the qualification (Accenture hires "AIOps & Agentic Operations Advisory Senior Manager" requiring **8+ yrs running NOC/major-incident ops**); (3) carry a deployed portfolio to convert "support" into "platform" narrative; (4) avoid the most-attempted-least-successful path (first-line support → junior ML engineer).

## 6. INDIA CITY-LEVEL HIRING ANALYSIS

Live AI-job share (HireHire, 1,594 jobs / 270 companies, Aug 2026): **Bengaluru 44% | Hyderabad 15% | Pune 15% | Chennai 7% | Mumbai 4% | Noida 3%** — top-3 metros ≈ 74%.

- **Hyderabad = momentum leader**: +51% YoY AI postings (fastest in India), GCC Index #1 (71 new GCCs vs Bengaluru's 46).
- **Agentic/FDE concentration**: agentic postings +300% (Jan'25–Mar'26); FDE +700%; Gurugram/Noida active secondary hubs.
- Tier-2 rise: tier-2 GCC headcount **+35% YoY vs +12% metros** (Everest). Coimbatore 25+ GCCs (21% setup CAGR, ⅓ metro cost); Kochi 20+ (Infopark 450 firms incl. IBM GenAI Innovation Centre); Trivandrum Technopark 540+ firms (UST 3,000-role expansion); GIFT City Ahmedabad (HSBC GBS 200+ AI roles; Gujarat targets 250 GCCs by 2030).

### City × Role Matrix (methodology: triangulated live-board shares, employer footprints, HAN Digital/Zinnov/Quess city reports; Very High → top decile of national volume)

| City | AI Eng | GenAI | Agentic | AIOps | Cloud AI | AI Security | AI Architect |
|---|---|---|---|---|---|---|---|
| Bengaluru | Very High | Very High | High | High | Very High | High | Very High |
| Hyderabad | High | High | Medium | High | Very High | Medium | High |
| Chennai | Medium | Medium | Low | Medium | Medium | Medium | Medium |
| Pune | High | High | Medium | Medium | High | High (Rapid7 SOC) | Medium |
| Mumbai | Medium | Medium | Low | Medium | Medium | High | Medium |
| Delhi NCR (Gurugram/Noida) | Medium | Medium | Medium | Low-Med | Medium | High | Medium |
| Coimbatore | Low | Low | Very Low | Low-Med | Low | Low | Very Low |
| Kochi | Low-Med | Low-Med | Very Low | Medium | Low-Med | Low | Very Low |
| Trivandrum | Low | Low | Very Low | Low | Low | Low | Very Low |
| Ahmedabad | Low | Low | Very Low | Low-Med | Low | Low-Med (GIFT) | Very Low |
| Kolkata | Low | Very Low | Very Low | Low-Med | Low | Low-Med | Very Low |

Remote/hybrid: remote-first AI roles exist but minority (~10–15% of postings); hybrid 3-days dominant in metros; IT-services RTO tightening 2026; GCCs slightly more flexible; US-remote contracts for India-based engineers skew AWS-stack product startups.

## 7. INDIA COMPANY-TYPE ANALYSIS

| Type | Named employers actively hiring | Dominant demanded skills | Experience window asked | Interview difficulty | Cloud lean |
|---|---|---|---|---|---|
| IT Services | TCS, Infosys, Wipro, Cognizant, HCLTech, Tech Mahindra, LTIMindtree, Persistent, Hexaware | Python, RAG, LangChain, Azure OpenAI/Bedrock, prompt eng, MLOps basics | 2–12 yrs, "relevant 2+" | Tier 3 (lighter coding, client-fit) | **Azure OpenAI #1**, AWS close #2 |
| Consulting | Accenture, Deloitte, EY, KPMG, Capgemini, Genpact, PwC | Agentic architecture (LangGraph/ADK), vector DBs, pre-sales, Copilot/M365, certs atop stack | Min 5–6 yrs incl 2–3 hands-on LLM | Tier 2–3 (case + delivery depth) | Azure-leaning |
| GCC | JPMorgan (+1,000 Jul'26), Walmart GT, Goldman, Wells Fargo, BofA, HSBC, Intuit, Target, Optum, Lowe's, Bosch, Shell, Standard Chartered | Cloud architecture, AI data pipelines, DSA, regulated-industry design, FinOps (+55%) | **56% of demand at 4–12 yrs** | Tier 2 (HackerRank+DSA+design, 4–7 rounds) | AWS+Bedrock strongest, Azure rising |
| Product/SaaS | Razorpay, Zepto, Meesho, CRED, Sarvam AI, Krutrim, GlobalLogic, Turing | Production RAG, evals/observability (Langfuse), LoRA/QLoRA fine-tuning, cost routing | 4–8 yrs, portfolio-gated | Tier 2 (project deep-dive decisive) | Split AWS Bedrock / GCP Vertex |
| Big Tech India | Google, Microsoft, Amazon, Meta, OpenAI (26 openings B'luru) | DSA, distributed-system design, ML depth | Level-based | Tier 1 | Multi-cloud internal |

**Validated company-type patterns**
- Consulting over-indexes on Azure OpenAI + certifications + client-facing architecture: consultants jumped from 0.2% → **12.4% of GenAI postings in one year** (Indeed Hiring Lab).
- Startups emphasize full-stack AI engineering (product+LLM integration); product companies weight system design hardest.
- GCCs are minting dedicated AI platform/agentic teams fastest and hire mid-career conversions deliberately (Quess "role-adjacent reskilling": for every core-AI hire, GCCs add 5–6 platform/data engineers; 70% use skills-based filters, not degrees).
- Service companies demand breadth + certs (AI-102, AIF-C01) and client communication; salaries lowest but entry bar most accessible.
- BFSI GCC interviews add model-validation/compliance rounds (SR 11-7-style challenge).

## 8. INDIA GCC AI HIRING ANALYSIS

- Scale: **>2,100 GCCs, 2.36M workers, ~$100B revenue** (Reuters May 2026); ~110–150 new centers/year; 90+ opened in 2025.
- Aggressive AI hirers: JPMorgan (55K India staff; Asia's largest GCC campus, Mumbai, 30K jobs by 2029), Standard Chartered (largest global GCC in India, headcount growing WITH AI), Wells Fargo, Walmart Global Tech (Target DS median ₹42L), Optum, Lowe's, Home Depot, Shell, Chevron, Boeing; new 2025–26: Rapid7 Pune (SOC+AI), Amgen & Sanofi Hyderabad (AI/data), Under Armour AI-first Bengaluru, Revolut, ArcelorMittal.
- Stacks requested: Bedrock/EKS, Azure OpenAI, Vertex AI; Databricks lakehouse; Pinecone/Milvus; LangChain/LangGraph/Semantic Kernel; K8s, MLflow/Kubeflow; DPDP/GDPR governance; FinOps demand +55%.
- Economics: pay 15–25% above IT services; **AI roles up to +40%**; GenAI premium 30–60%; senior ML ₹55–80L (Bengaluru GCCs); hikes 9.8–10.2%/yr vs 5–6% in services; niche-skill P75 offers ~₹60L.
- **Transition verdict: STRONGEST channel for experienced enterprise-IT professionals.** They hire exactly the 4–12 yr cohort (56% of demand), run formal role-adjacent conversion paths (backend→Applied AI, cloud→Platform, DevOps→DevSecOps, cybersecurity→Cloud Security), and value regulated-industry context + SRE/ITSM instincts that veterans already have. Best cities: Bengaluru/Hyderabad (volume+premium), Pune (security-AI), tier-2 (lower competition, stable pivots). Caveat [Medium]: core ML-science roles remain credential-gated; veterans win in ops-adjacent AI, not research.

---

## 9. ROLE-BY-ROLE ANALYSIS (12 TARGET ROLES)

| # | Role | Demand reality | Core JD stack | Fit for IT-ops veteran | Verdict |
|---|---|---|---|---|---|
| 1 | **AI Engineer** | Largest single cluster; ~80% of "AI jobs" collapse into this | Python, LLM APIs, RAG, vector DB, Docker/K8s, cloud | Medium — needs real portfolio; junior-flooded entry tier but senior tier open to strong laterals | Primary demand pool |
| 2 | **GenAI Engineer** | Fastest-growing named title (+7× 2022→24); consulting's preferred label | Same as #1 + prompt eng, guardrails, Azure OpenAI/Bedrock | Medium — lateral-friendly in services/consulting ("total+2 relevant") | High-volume target |
| 3 | **Agentic AI Engineer** | Exact title rare (~1–10% of agentic demand); embedded everywhere else | LangGraph/CrewAI, MCP, tool calling, guardrails, HITL, evals | Low-Medium as first role; excellent as specialization label on top of #1/#2 | Skill, not first job |
| 4 | **GenAI Product Engineer** | Startup niche; full-stack AI + product sense | TS/Python, Next.js-style UIs, streaming UX, LLM APIs, evals | Low — product ownership expected | Skip unless PM-leaning |
| 5 | **AIOps Engineer** | Real, growing ($11B→$41B market path); India 646 Naukri openings; premium over generic ops | Splunk/Dynatrace/Datadog/BigPanda/Moogsoft/ServiceNow ITOM + Python + event correlation/RCA automation | **Very High** — tenure is the qualification (Accenture hires 8+ yr NOC vets) | Best low-friction door |
| 6 | **Cloud AI Engineer** | Very High and rising; every enterprise deployment needs this | Azure OpenAI or Bedrock, AI Search/OpenSearch, Functions/Lambda, IaC, K8s basics, FinOps | **High** — direct monetization of cloud/infra experience | **Top recommendation** |
| 7 | **LLM Engineer** | Converged with #1/#2; labs/product cos use it for app-layer too | Same as #1 + fine-tuning (LoRA), vLLM serving, eval harnesses | Medium | Search together with #1 |
| 8 | **Intelligent Automation Engineer** | Legacy RPA declining ($3.6B vs $22B projected) but hybrid RPA+agents roles rising at services firms | UiPath/Power Automate + GenAI agents, IDP, LangChain | High transfer from automation backgrounds | Decent backup |
| 9 | **Forward Deployed / AI Deployment Engineer** | +800% growth but tiny base (~260 US postings); labs + OpenAI-style firms | Full-stack + LLM APIs + customer scoping + evals | Low-Medium (client travel, startup pace) | Watchlist |
| 10 | **AI Security Engineer** | ~3,300 Indeed US, $184K median; India: EY GDS tracks, GCC SOC+AI; governance hiring 3× faster than AI overall | OWASP LLM Top 10, prompt-injection defense, NeMo/Bedrock Guardrails, NIST AI RMF, ISO 42001 | **High if security-adjacent experience exists**; nobody has >2 yrs ISO 42001 → instant leveling advantage | Strong differentiated bet |
| 11 | **AI Solutions Engineer** | Pre-sales/delivery hybrid; consulting-heavy | Architecture + demos + RAG patterns + communication | Medium-High (senior-friendly, values breadth) | Good for 10+ yrs profiles |
| 12 | **AI Solutions Architect** | Consistent senior demand; BFSI/GCC heavy | System design, cloud AI reference architectures, governance, cost | Medium-High — needs architecture narrative on top of ops history | 2nd-step role after landing |

## 10. HIRING DEMAND RANKING

Ranked by composite of volume × growth × breadth across sources [confidence in brackets]:

1. AI Engineer / application-layer cluster [High]
2. GenAI Engineer [High]
3. Cloud AI Engineer [Medium-High]
4. MLOps → LLMOps / AI Platform Engineer [High direction]
5. Data/AI Platform Engineer (GCC pattern: 5–6 hired per core-AI hire) [High]
6. AIOps / Intelligent Operations [Medium-High]
7. Agentic-capable AI Engineer (skill demand inside #1–3) [High direction]
8. AI Security / Governance [Medium, fastest-premium growth]
9. AI Solutions Architect [Medium-High senior segment]
10. Forward Deployed Engineer [Low volume, extreme growth]
11. Intelligent Automation (RPA+GenAI hybrid) [Medium-Low]
12. Pure ML Scientist / Research [stable, credential-gated]

## 11. SKILLS FREQUENCY ANALYSIS — TOP 50 SKILLS IN INDIAN AI JOBS

Methodology: triangulated from InterviewStack (n=3,449), Grigorev scrape (n=5,694), johal.in benchmark (n=5,000), Skillenai 90-day indexes, Foundit/Naukri keyword counts. "Jobs/Presence" = qualitative band where exact India-normalized % unavailable.

| Rank | Skill | Presence | Roles | Trend | Career ROI (India) |
|---|---|---|---|---|---|
| 1 | Python | ~71% of AI-eng postings | All | → | Critical |
| 2 | LLM APIs (OpenAI/Anthropic/Azure OpenAI) | ~66% | All GenAI | ↗ | Critical |
| 3 | Prompt engineering / context engineering | high but now baseline | All | → (as differentiator ↓) | Table stakes |
| 4 | RAG pipeline design | ~36–40% | AI/GenAI Eng | ↗ | Critical |
| 5 | Cloud platform (Azure/AWS/GCP) | ~45% combined | All | ↗ | Critical |
| 6 | Azure OpenAI + AI Search | top services combo | Services/Consulting | ↗ | Very High |
| 7 | AWS Bedrock (+Agents/KB/Guardrails) | near-universal in AWS reqs | GCC/BFSI | ↗ | Very High |
| 8 | Vector DBs (umbrella) | ~16–18% | AI Eng | ↗ | High |
| 9 | LangChain | ~19–34% | AI Eng | → | High |
| 10 | LangGraph | +22% MoM | Sr AI Eng | ↑ | Very High |
| 11 | FastAPI | ~8–15% | App-layer AI | ↗ | High |
| 12 | Docker | ~18% | All | → | High |
| 13 | Kubernetes | ~16% | Platform/Sr | → | High |
| 14 | PostgreSQL / SQL | ~19–24% | All | → | Critical |
| 15 | pgvector | rising default <10M vectors | App AI | ↗ | High |
| 16 | Tool/function calling | table stakes | All agentic | → | Critical |
| 17 | MCP | 1,012 postings/90d, +31% MoM | Agentic/Platform | ↑↑ | Very High (early) |
| 18 | Evals (RAGAS/LangSmith/Langfuse) | 56% of eval-tool mentions | Sr AI/QA-AI | ↗ | **Highest marginal ROI** |
| 19 | LLM-as-judge methodology | only eval method w/ hiring traction | Sr AI | ↗ | Very High |
| 20 | Guardrails (NeMo/Bedrock Guardrails) | top-5 AI-Sec skill | Sec/Platform | ↗ | Very High |
| 21 | Hybrid search (BM25+dense) + reranking | regulated-industry default | RAG Eng | ↗ | High |
| 22 | Chunking strategies / retrieval debugging | standard interview topic | RAG Eng | → | High |
| 23 | Databricks (Mosaic AI/Unity Catalog) | lakehouse enterprises | Data+AI Eng | ↗ | High |
| 24 | MLflow | 2,438 postings; cross-stack | MLE/LLMOps | → | High |
| 25 | vLLM / inference optimization | NVIDIA career ladders exist | LLMOps | ↑ | Very High (niche) |
| 26 | Terraform/IaC | bundled with Bedrock stacks | Cloud AI | ↗ | High |
| 27 | CI/CD for models & prompts | eval-in-CI pattern | LLMOps | ↗ | High |
| 28 | Observability/tracing (Langtrace/OpenTelemetry) | senior differentiator | LLMOps/Sr AI | ↗ | Very High |
| 29 | PyTorch | 73% of ML-posting framework share | MLE | ↗ | Medium-High |
| 30 | Fine-tuning LoRA/QLoRA | product/startup reqs | GenAI Eng | ↗ | Medium-High |
| 31 | Semantic Kernel (.NET estate) | 2.4–15% MS-shop reqs | Enterprise AI | ↘→ | Medium |
| 32 | CrewAI | 9.3% of agentic listings | Agentic | ↗ | Medium |
| 33 | Vertex AI + ADK + BigQuery | analytics-heavy shops | GCP AI Eng | ↗ | Medium-High |
| 34 | ServiceNow (ITOM/Now Assist) | under-supplied premium niche | AIOps/ITSM-AI | ↗ | **High for ops veterans** |
| 35 | Splunk / Dynatrace / Datadog | AIOps JD staples | AIOps/Obs | → | High (existing lever) |
| 36 | Event correlation / RCA automation | explicit AIOps requirement | AIOps | ↗ | High |
| 37 | Prompt-injection defense / OWASP LLM Top 10 | top-5 AI-Sec skill | AI Sec | ↑ | Very High |
| 38 | NIST AI RMF / ISO 42001 / EU AI Act | governance wave, 3× hiring growth | Gov/Risk | ↑ | Very High (early) |
| 39 | DPDP Act compliance (India) | Phase-1 Nov 2026 driving hires | Gov/BFSI | ↑ | High |
| 40 | GraphRAG / knowledge graphs | standalone titles emerging | Sr AI | ↗ | Medium (early) |
| 41 | Voice agents (Pipecat/LiveKit) | mandatory in India startup JDs | Voice AI | ↗ | Medium (early) |
| 42 | Multi-agent orchestration design | architect-level ask | Architect | ↗ | Medium |
| 43 | Cost/token optimization (FinOps for AI) | explicit JD phrases; +55% GCC FinOps | Platform/Architect | ↗ | Very High |
| 44 | AI coding tools (Copilot/Cursor/Claude Code) | now NAMED requirements; GCC benchmarks | All | ↑ | Medium (silent screener) |
| 45 | Snowflake Cortex / data-cloud RAG | warehouse-modernization reqs | Data+AI | ↗ | Medium |
| 46 | Pinecone/Weaviate/Qdrant | named-vendor options | App AI | → | Medium |
| 47 | Airflow / data pipelines | classic co-req (72% GenAI+ops pairing) | AI/Data Eng | → | Medium |
| 48 | Streamlit/Gradio demo craft | interview/take-home currency | Junior-mid AI | → | Low-Medium |
| 49 | TensorFlow-only deep learning | stalled growth | legacy MLE | ↘ | Low |
| 50 | Kaggle-style portfolio projects | explicit red flag | — | ↓ | Negative |

### India Top 15 Must-Learn Skills (employability-optimized)
Python(production-grade) · RAG engineering · Azure OpenAI+AI Search · AWS Bedrock · LangGraph · MCP/tool-calling · FastAPI · PostgreSQL/pgvector · Docker+Kubernetes(basics) · Evals(RAGAS/LangSmith/LLM-as-judge) · Guardrails+safety · Terraform+CI/CD · Observability/tracing · ServiceNow Now Assist(ops veterans) · Cost optimization.

## 12. SKILL CO-OCCURRENCE ANALYSIS — TOP 20 SKILL STACK PATTERNS

Evidence: two independent scrapes agree on framework ordering; stack rows verified against verbatim live JDs wherever possible.

| Rank | Skill Combination | Typical Roles | Company Types | Evidence Strength | Trend |
|---|---|---|---|---|---|
| 1 | Python + FastAPI + LangChain/RAG + vector DB + OpenAI API + Docker/cloud | AI Engineer | Startups, SaaS, fintech | High (n=3,449 & n=5,694 agree) | ↑ |
| 2 | .NET-or-Python + Azure OpenAI + Azure AI Search + Semantic Kernel/Agent Framework | Enterprise AI Eng | Microsoft estates, legal/gov, consultancies | High (verbatim JDs) | ↗ |
| 3 | Python + RAG + Azure OpenAI + Prompt Flow/embeddings (services flavor) | GenAI Eng | TCS/Cognizant/Happiest Minds JDs | High | ↗ |
| 4 | AWS Bedrock + Lambda + OpenSearch Serverless + Terraform (+ Agents/KBs/Guardrails) | Cloud AI Eng | Gov contractors, AWS-partner SIs, BFSI GCC | High (verbatim JDs) | ↗ |
| 5 | Bedrock + Lambda + SageMaker + OpenSearch kNN (BFSI GCC flavor) | Cloud/ML Eng | Banks, GCCs | Medium-High | ↗ |
| 6 | Databricks Mosaic AI + Unity Catalog + MLflow + Vector Search | Databricks AI Eng | Pharma, finance, lakehouse enterprises | High | ↗ |
| 7 | Snowflake Cortex + Snowpark + dbt/Fivetran + embeddings/RAG | Data+AI Eng | Warehouse modernizers | Medium | ↗ |
| 8 | vLLM/SGLang + Triton/Ray Serve + K8s + GPU cost tuning + MLflow registry | LLMOps/AI Platform | AI-native, GPU-heavy enterprise | High | ↗ |
| 9 | LangGraph + tool calling/MCP + PostgreSQL/FastAPI + Docker/K8s | Senior AI Eng | Product cos, scale-ups | Medium-High | ↑ |
| 10 | RAGAS/LangSmith/Langfuse + LLM-as-judge + eval-in-CI + tracing | Sr AI Eng, QA-AI | All types (differentiator) | High | ↗ |
| 11 | LlamaIndex + Pinecone (+Weaviate) inside others' orchestration | Retrieval/AI Eng | US-leaning startups→enterprise | High | → |
| 12 | CrewAI/multi-agent + Pinecone/Weaviate + LangChain substrate | Agentic AI Eng | SAP/Grafana-type product cos | Medium | ↗ |
| 13 | Vertex AI (Gemini/Agent Platform) + ADK + BigQuery/GKE + Gemini | Google-stack specialist | Consultancies, GCP shops | Medium | ↗ |
| 14 | Hybrid search (BM25+dense) + reranking (Cohere/bge-class) + chunking defenses | RAG Engineer | Regulated doc-heavy industries | Medium-High | ↗ |
| 15 | GraphRAG/knowledge graphs (Neo4j/Memgraph) + pgvector/Qdrant + agentic loops | Sr AI Eng – Knowledge Systems | Legal, medical, KM tools | Medium | ↗ |
| 16 | SageMaker + PyTorch + Step Functions + OpenSearch kNN + recall@K evals | AWS AI/ML Eng | Gov, fintech, consulting | Medium | → |
| 17 | Guardrails + responsible-AI governance + safety observability | AI Governance/Platform | Regulated enterprise, gov | Medium | ↗ |
| 18 | Named cloud cert (AIF-C01 / AI-102 / PMLE / Databricks GenAI) atop platform stack | Consultant/solution roles | Big consulting | Medium | ↗ |
| 19 | MLflow as cross-stack experiment/registry layer (2,438 postings) | MLE / GenAI | Anywhere with existing ML platform | High | → |
| 20 | ServiceNow Now Assist + IntegrationHub + JavaScript + agent building | ServiceNow Dev | ITSM-heavy enterprises | Low (roadmap+scattered JDs) | ↗ |

## 13. TECHNOLOGY STACK PATTERN ANALYSIS (TOOL REPLACEMENT PATTERNS)

Validated replacement waves (each backed by JD counts + production evidence):

| From | To | Evidence strength |
|---|---|---|
| Basic LangChain chains | Graph-based orchestration (LangGraph) | High — LangGraph #2 hiring rank, +22% MoM despite fewest stars |
| Notebook DS / manual deployment | Eval-driven CI/CD for LLM apps | High — eval-in-CI is the named senior differentiator |
| Pure vector search | Hybrid retrieval + rerankers | Medium-High — regulated industries default |
| Single-agent chatbots | Workflow-orchestrated agents + human-in-loop | High — production default per Anthropic/Cognition; multi-agent failure rates 41–87% cited |
| Classic MLOps | LLMOps (prompt/model registries, tracing, token cost) | High — title split documented; Foote Partners 20–24% pay premiums |
| Traditional RPA | AI-powered automation (IDP + agents) | Medium-High — RPA market $3.6B vs $22B forecast; UiPath rebranding to agents |
| TensorFlow-first | PyTorch + serving stack (vLLM/Triton) | High — 73% vs 56% posting share; TF growth stalled +3% |
| On-prem model hosting | Managed platform services (Bedrock/Azure OpenAI/Vertex) | High — enterprise default |
| AutoGPT-style hacks | Governed agent frameworks + guardrails | High — zero AutoGPT JD footprint |

## 14. JOB TITLE CONVERGENCE ANALYSIS

Recruiter audit of 35 titles found they describe ~three real jobs; the application-layer cluster alone ≈80% of the market.

### Job Title Similarity Map — SEARCH THESE TOGETHER

**Cluster A — Application layer (~80% of postings; interchangeable):**
AI Engineer = GenAI Engineer = Generative AI Engineer = LLM Engineer = Applied AI Engineer = AI Software Engineer = AI Product Engineer = Full-Stack AI Engineer = RAG Engineer = (legacy) Prompt/Context Engineer.
*Proof:* Accenture posts "LLM Operations Engineer" requiring the same agentic/RAG/vector-DB stack startups call "LLM Engineer"; Mastercard "SDE (LLM)", UST "ML Engineer (LLM)", Opkey "LLM Engineer", Mindlance "AI Engineer (LLM & GenAI)" all seek one profile.

**Cluster B — Agent-flavored variant:** Agentic AI Engineer ≈ AI Agent Developer ≈ "AI Engineer (Agentic AI)". Dedicated-title employers confirmed: Capgemini, Bank of America, PwC India (GCC Advisory), TCS (dedicated hiring page).

**Cluster C — Ops/Platform:** LLMOps Engineer ≈ AI Platform Engineer ≈ AI Infrastructure Engineer ≈ MLOps Engineer (LLM scope) ≈ LLM Operations Engineer.

**Cluster D — Customer deployment:** Forward Deployed Engineer ≈ Applied AI Engineer (at labs) ≈ AI Delivery Engineer.

**Cluster E — Pre-sales:** AI Solutions Architect ≈ GenAI Consultant ≈ AI Sales Engineer.

**Genuinely distinct:** AI/ML Research Scientist (credential-gated) · AI Security/Red Team · AIOps (a naming collision with legacy ML-for-IT-ops — verify scope per JD) · AI Product Manager (non-eng).

Segment preferences: consulting says "GenAI Engineer/Consultant"; startups say "AI Product/Full-stack AI Engineer"; enterprises/labs say "Applied AI Engineer"; GCCs increasingly mint "Agentic AI" titles fastest.

**Salary arbitrage within convergence [Medium]:** Levels.fyi medians show "AI Software Engineer" $245K vs "AI Engineer" $159K — near-identical work, $86K apart. Search and negotiate across the whole cluster.

## 15. CLOUD DEMAND

**India (JD-derived, not global market share):**
- IT Services: **Azure OpenAI #1**, AWS close second (TCS "Azure AI/RAG…Prompt Flow"; Cognizant default Azure Cognitive Services; Infosys dual Bedrock/Azure OpenAI).
- GCC/BFSI: **AWS+Bedrock strongest**, Azure rising fast (SBI Azure hybrid; AWS FSI adoption statements).
- Product/startups: split AWS Bedrock & GCP Vertex over Azure; remote-US roles skew AWS.
- Portal noise-counts [Medium]: Foundit "Azure OpenAI + GenAI" 39,159 vs "Azure OpenAI Bedrock" 31,322; Indeed India "Azure OpenAI" 2,535.
- Winning combos: **Azure OpenAI + AI Search + Functions** (enterprise RAG default) · **Bedrock + Lambda + SageMaker + OpenSearch** (BFSI GCC) · **BigQuery + Vertex + Gemini** (analytics shops).

**Global:** Azure OpenAI dominates Fortune-500 copilot estates; Bedrock dominates regulated/gov; Vertex strongest in data-analytics-native companies. Certificates: **AI-102 (Azure) and AIF-C01 (AWS) co-ranked #1–2 most-requested**; Databricks GenAI Engineer fastest-rising; GCP PMLE valued but least listed.

**Recommendation for candidate:** Azure-first depth + Bedrock working knowledge covers ~most Indian AI JDs across segments.

## 16. AGENT FRAMEWORK DEMAND

Two independent scrapes agree (agentic-board n=1,135 May'26; Skillenai 90-day):

| Framework | Board % (rank) | 90-day postings | Trend | Note |
|---|---|---|---|---|
| LangChain | 34.5% (#1) | 2,067 (+16%) | → | Connective tissue; pairs with everything |
| LangGraph | 22.6% (#2) | 1,248 (**+22% MoM**) | ↑↑ | Fewest stars, #2 hires — hype inversion |
| LlamaIndex | 13.2% | 549 (+26%) | ↗ | Highest vector-DB pairing rate |
| CrewAI | 9.3% | — | ↗ | Never solo; always paired |
| AutoGen | 6.5% | ~74 | ↘ | Sunset into MS Agent Framework yet still staffed (hiring lags roadmap) |
| Semantic Kernel | 2.4–15% (MS shops) | — | ↘→ | Absorbed into Agent Framework (Oct'25) |
| MCP | in 17–24% of framework postings | 1,012 (+31% MoM) | ↑↑ | Linux Foundation standard; 41% orgs run it in prod; 28% of F500 |

Modal JD asks **2.3 frameworks simultaneously**; all five framework skills pay ~$185–190K median. Production truth: single-agent workflows dominate; multi-agent is an architect-level design question, not a beginner skill.

## 17. RAG DEMAND

- Present in ~36–40% of AI-engineer JDs (two scrapes); majority of new Indian AI-engineer postings ask RAG/vector-DB production capability (Quess).
- Evolution visible in hiring: naive RAG → **hybrid BM25+dense + reranking** → chunking/eval discipline (recall@K, RAGAS) → GraphRAG/agentic retrieval (standalone titles appearing; asked in Accenture L2 rounds) → multimodal RAG (rarely named explicitly yet).
- Vector store reality: umbrella "vector databases" 16–18% of postings; Pinecone most-named vendor; **pgvector quietly becoming the default for <10M-vector workloads**; OpenSearch/AI Search ride in via cloud stacks rather than standalone keywords.
- Interview focus: chunking strategy, embedding choice, reranking, eval metrics, hallucination containment, cost/latency trade-offs.

## 18. MLOPS / LLMOPS DEMAND

- Title split documented: classic MLOps splitting into **LLMOps / AI Platform Engineering** — used almost interchangeably in postings; "these three titles get used interchangeably" (Futurense); Foote Partners: LLMOps/agent/risk-analytics skills earn 20–24%-of-base premiums.
- Pay: MLOps/AI-infra $150–230K US vs DevOps $100–165K; ML-platform SRE +15–25% over classic SRE.
- Stack demanded: MLflow (2,438 postings; cross-stack constant), Kubeflow/W&B, vLLM/Triton/Ray Serve on K8s, GPU cost tuning, model+prompt registries, drift monitoring + LLM tracing/evals in CI.
- GCC signal: for every core-AI hire, **5–6 platform/data engineers are added** — the platform side is the volume side.
- DevOps→LLMOps conversion repeatedly reported as smoothest tech-to-tech pivot (productive "within weeks" per practitioner accounts; 3–9 months to offers).

## 19. TOP 30 AI HIRING PATTERNS

| # | Pattern | Key evidence | Roles affected | India relevance | Trend | Confidence |
|---|---|---|---|---|---|---|
| 1 | One application-layer job wears ~10 titles | 35-title audit; verbatim identical JDs | All app-layer | High | → | High |
| 2 | Same-work salary gaps by title naming ($86K spread) | Levels.fyi medians | App-layer | Medium | → | Medium |
| 3 | "Total IT exp + 2–3 yrs GenAI" is India's real hiring formula | Cognizant/Accenture/Infosys JD quotes | Mid-senior all | **Critical** | → | High |
| 4 | GCCs hire 4–12-yr cohort deliberately; formal adjacent-conversion paths | Quess 56%; Reuters | Platform/AI Eng | **Critical** | ↗ | High |
| 5 | Platform/data engineers hired 5–6× more than core-AI staff | Quess GCC analysis | Platform | High | ↗ | Medium-High |
| 6 | Only 257K of 920K AI-skilled hold core AI roles — 72% are converts | Quess 350K postings | All | Critical | → | High |
| 7 | Consulting became 12.4% of GenAI postings in a year (0.2% before) | Indeed Hiring Lab | GenAI/Solutions | High | ↗ | High |
| 8 | Azure OpenAI owns services-sector JDs; Bedrock owns BFSI-GCC | Verbatim JDs + portal counts | Cloud AI | Critical | ↗ | Medium-High |
| 9 | Evals/observability = scarcest skill, biggest interview differentiator | Skillenai; interview guides | Sr AI | High | ↗ | Medium-High |
| 10 | LangGraph out-hires its hype (fewest stars, #2 demand) | Two independent scrapes | Sr AI Eng | High | ↑ | High |
| 11 | MCP went protocol→production→JD line in ~18 months | 41% orgs prod; +31% MoM JDs | Agentic/Platform | High | ↑↑ | High |
| 12 | Agentic exact-title postings ≈1–10% of true agentic demand | 142 exact vs 10K fuzzy | All | High | ↑ | High |
| 13 | Enterprises default to managed platforms, not OSS frameworks | JD composition vs social discourse | Cloud AI | Critical | → | High |
| 14 | Production = single-agent workflows; multi-agent = design discussion | Anthropic/Cognition; 41–87% failure cites | All | Medium | → | Medium-High |
| 15 | Gartner: only 17% deployed agents; >40% projects cancelled by 2027 | Gartner hype-cycle | All | Medium | ↗ then shakeout | Medium |
| 16 | Prompt-only engineering collapsed (−35% titles) | Fortune; posting deltas | — | High | ↓ | High |
| 17 | Ops tenure flips from liability to qualification in AIOps/architect tracks | Accenture 8+yr NOC JD | AIOps/Arch | **Critical** | ↗ | Medium-High |
| 18 | First-line support→ML-engineer is most-attempted, least-successful pathway | Talenbrium HR study | Transitions | Critical | → | Medium |
| 19 | Internal redeployment costs 62% less than exit+re-hire → internal-first works | Talenbrium | All | High | → | Medium |
| 20 | Age bias real for external AI switching (90% vs 32% willingness) | Generation survey | 40+ switchers | Medium | → | Medium |
| 21 | AI-governance hiring grows 3× faster than AI overall (BFSI/pharma) | Quess/EY tracks | Governance | High | ↑↑ | Medium-High |
| 22 | Nobody has >2 yrs ISO 42001 → instant seniority for early movers | InfosecJobBoard | AI Sec/Gov | High | ↑ | Medium |
| 23 | Voice-agent stack now mandatory in India startup JDs (Pipecat/LiveKit) | Sei/Tanla JDs | Voice AI | Medium | ↗ | Medium |
| 24 | AI-coding tools named as JD requirements; silent AI screening in interviews | Malaysia JD study; McKinsey/Kearney rounds | All | Rising | ↑ | Medium |
| 25 | Tier-2 India GCC headcount +35% YoY vs +12% metros | Everest/Zinnov | Cloud/Ops AI | High | ↗ | High |
| 26 | Hyderabad = momentum city (+51% YoY; 71 new GCCs) | LinkedIn/HAN/GCC Index | All | High | ↗ | High |
| 27 | GenAI pay premium India 30–60%; GCC AI up to +40% over services | TeamLease/Savanna/Taggd | All | Critical | ↗ | Medium-High |
| 28 | TeamLease fills only ~30% of GenAI reqs — chronic supply gap | Reuters May'26 | All | Critical | → | High |
| 29 | Legacy RPA budgets redirecting to agent orchestration | Beam.ai; vendor rebrands | Automation | Medium | ↘→↗ | Medium |
| 30 | Certs are "preferred," never hard requirements — portfolio beats paper | TrueCert; hiring guides | All | High | → | High |

## 20. HIDDEN MARKET PATTERNS

See Section 40 for the distilled 15; underlying mechanisms: fuzzy board matching hides real categories; JD language lags stack reality (AutoGen sunset yet staffed); compensation variance driven by title words not skills; supply gaps concentrated in production/applied skills rather than theory; employer type predicts stack better than job title does.

## 21. INDIA-SPECIFIC HIRING PATTERNS

1. Experience formula (see #3 above) — the defining Indian pattern.
2. Services ladder: join as GenAI developer → client-facing GenAI consultant in 18–24 months; certs + delivery narratives matter more than OSS contributions.
3. GCC re-entry: emphasize regulated-domain context (BFSI/healthcare) + platform reliability stories.
4. City arbitrage: Hyderabad momentum + Bengaluru volume + Pune security niche; tier-2 for low-competition stable pivots.
5. Silent AI screening: McKinsey/Kearney India mandate AI-tool use inside interview rounds; GCCs piloting Claude-Code productivity benchmarks — practice building WITH AI tools on camera.
6. RTO tightening in services (2026 rules) vs slightly softer GCC flexibility — factor commute into city targeting.
7. ATS keyword bar ~75–80% match needed at GCCs — resume must mirror JD vocabulary exactly.
8. Salary resets avoidable via lateral/internal moves; external product-company jumps work best after 2–3 yrs demonstrable GenAI delivery.

## 22. HYPE VS HIRING REALITY

| Topic | Social media says | Hiring data says |
|---|---|---|
| Agentic AI | Revolution imminent | Real but: exact titles 1–10%; Gartner 17% deployed; hiring targets durable stack (LangGraph, MCP, guardrails, evals) |
| Multi-agent systems | The future | Production default single-agent + subcalls; 41–87% failure rates; 15× token burn |
| Prompt engineering | Six-figure career | −35% postings; absorbed into AI Engineer; "context engineering" replacing it |
| AutoGen/CrewAI wars | Framework X will win | JDs ask 2.3 frameworks each; LangChain substrate + LangGraph graphs; hiring ignores star counts |
| "Learn transformers/math first" | Deep theory required | <10% of app-layer JDs require training math; eval/system-design questions dominate interviews |
| Vector DB startups vs Postgres | Dedicated DBs essential | pgvector default <10M vectors; dedicated DBs appear in specialist roles only |
| RPA dead | Killed by agents | Declining but hybrid RPA+AI roles actively hired in Indian services |

## 23. EMERGING SKILLS (EARLY HIRING SIGNALS)

| Signal | Strength | Evidence | India presence |
|---|---|---|---|
| MCP / tool calling | Very strong | +312–410% YoY; new job titles; EPAM/SAP/Salesforce reqs | Infosys/Tanla JDs; fresher curricula |
| Evals + LLM-as-judge | Strong | LangSmith+Langfuse 56% of eval mentions; only methodology with hiring traction | Bengaluru metro postings |
| Guardrails / prompt-injection defense | Strong | Top-5 AI-Sec JD skill; OWASP LLM Top 10 | EY GDS Bengaluru tracks |
| vLLM / inference optimization | Strong | NVIDIA/AMD dedicated ladders $124–356K; TorchServe archived | Tanla, GCC MLOps |
| AI coding tools as JD line | Rising fast | 0→named requirements in 12 months; GCC productivity benchmarks | GCC pilots |
| GraphRAG | Medium | Standalone titles; Accenture L2 interview topic | Early |
| Context engineering | Medium | Explicit Accenture JD phrase | Accenture/Infosys rounds |
| Voice agents (Pipecat/LiveKit) | Medium | Mandatory production exp in startup JDs | Hyderabad/TN startups |
| Ollama/local small models | Weak-JD/strong-ecosystem | Community surge, few JD lines | Negligible |

## 24. DECLINING SKILLS

| Skill | Evidence | Replacement |
|---|---|---|
| Prompt-engineer-only roles | −35% postings since Mar'25; media consensus | Agentic workflow architect / context engineer |
| TensorFlow-only DL | PyTorch 73% vs TF 56% share; TF +3% stall; Keras −63% since 2022 | PyTorch + serving stack |
| Classic AutoML | Absent from 5K-posting benchmark | Fine-tuning + eval pipelines |
| Legacy RPA dev | $3.6B actual vs $22B projected; vendor pivot to agents | LangGraph/CrewAI orchestration + IDP |
| Notebook-only DS / Kaggle portfolios | Explicit red flags in Indian hiring guides; Quess demand shift to production | Deployed RAG/LLMOps ownership |
| AutoGPT-style hype projects | Zero JD footprint | Eval-driven, guarded agent builds |

---

## 25. EXPERIENCE-LEVEL PATTERNS

Validated from JD bands + interview guides (not assumed):

| Level | What employers actually emphasize | India salary anchor (GenAI/AI Eng) |
|---|---|---|
| 0–2 yrs | Python, APIs, basic RAG, prompt eng, notebooks→FastAPI demos, certs help entry | Services ₹4.5–9L; Product ₹10–16L; GCC ₹8–14L [Med] |
| 2–4 yrs | Production RAG ownership, vector DBs, Docker, one cloud, evals exposure | Services ₹7–12L; Product ₹18–35L; GCC ₹14–24L |
| 4–6 yrs | End-to-end GenAI delivery, LangGraph agents, LLMOps tasks, cost awareness; "relevant 2–3 yrs" formula unlocks laterals here | Services ₹10–18L; Product ₹28–55L; GCC ₹20–35L |
| 6–8 yrs | Architecture + trade-offs (guardrails vs UX latency), multi-cloud, governance, mentoring; DSA reappears at GCCs | Services ₹12–22L; Product ₹40–70L; GCC ₹25–40L |
| 8+ yrs | System design >> model skills; stakeholder mgmt, FinOps/cost optimization, compliance (SR 11-7-style challenge in BFSI), team leadership | Services ₹15–25+L; Product ₹55–90+L; GCC ₹30–50+L |

Key validation: senior AI JDs weight **system design, evaluation strategy, security/governance and cost** far more than model training — confirmed across TCS/Accenture/BFSI-GCC interview maps.

## 26. IT SUPPORT → AI TRANSFERABILITY

**Statistical:** Quess — 72% of India's AI-skilled pool are converts who added AI to an existing function. Talenbrium — first-line support→junior-ML is the most-attempted, LEAST-successful pathway; successful transitions monetize existing domain knowledge; viable reskilling = 4–11 months.
**Anecdotal (survivorship-biased, directionally consistent):**
- Helpdesk/IT support → AIOps/observability or infra-side ML titles via scripting + monitoring depth (Reddit r/cscareerquestions).
- DevOps → MLOps/LLMOps: smoothest tech pivot; "productive within weeks"; obstacles = probabilistic thinking, eval metrics, versioning.
- SysAdmin → Cloud AI: 6–12 months typical; failure mode = "cert-rich-project-poor".
- Service desk → ServiceNow+GenAI: natural ITSM-to-agentic-ITSM bridge; comp premium niche.
- Cybersecurity → AI Security/Governance: AppSec/red-team most common route; GRC→AI-governance the overlooked door (nobody has >2 yrs ISO 42001).

### Top Transition Pathways (ranked by evidence)
| From → To | Existing leverage | New skills | Time observed |
|---|---|---|---|
| NOC/IT Support → AIOps/Observability | Incident mgmt, ITIL, monitoring tools | Python, Dynatrace/Splunk/Datadog APIs, event-correlation automation, Now Assist | 4–9 mo |
| Service Desk → ServiceNow+GenAI | ITSM workflows | Now Assist, AI Agent Studio, IntegrationHub/MCP | 3–6 mo |
| DevOps/SRE → MLOps/LLMOps/AI Platform | CI/CD, K8s, IaC | Model serving, vLLM, registries, LLM tracing/evals | 3–9 mo |
| SysAdmin/Cloud → Cloud AI Engineer | Linux, network, cloud basics | Azure OpenAI/Bedrock, RAG, Terraform, AI-102/AIF-C01 | 6–12 mo |
| QA/Test Automation → AI Test Automation | Frameworks, CI/CD | Agent-based test gen, LLM-output eval harnesses | 4–6 mo |

Recurring advice themes: (1) ship deployed projects, not cert stacks; (2) pivot adjacent not alien; (3) go inference/platform side, not model-building; (4) move internally first to preserve level/salary; (5) master evals + observability + governance as the scarce differentiator.

## 27. SKILL GAP ANALYSIS (for this candidate: IT ops/support background)

Already leveraged (keep visible on resume): incident management, ITIL, monitoring/observability tooling, scripting, cloud familiarity, vendor management, on-call reliability instincts, regulated-environment hygiene.

Gap to close, priority order:
1. **Production Python** (APIs, async, packaging) — foundation of every target role.
2. **LLM application engineering**: OpenAI/Azure OpenAI/Bedrock APIs, structured outputs, function/tool calling.
3. **RAG end-to-end**: ingestion→chunking→embeddings→pgvector/AI Search→rerank→evals.
4. **Agents on LangGraph + MCP servers** (one real workflow, guarded, HITL).
5. **Evals & observability**: RAGAS/LangSmith/Langfuse, LLM-as-judge, tracing in CI — the differentiator layer.
6. **Cloud AI services depth**: Azure OpenAI + AI Search primary; Bedrock secondary; IaC + CI/CD for AI apps.
7. **Containers/K8s working level** (deploy, not administer).
8. **Security/governance vocabulary**: OWASP LLM Top 10, guardrails, NIST AI RMF, DPDP basics.
9. **AIOps bridge skills**: connect existing Splunk/Dynatrace/ServiceNow knowledge to AI features (Now Assist, Davis AI, event correlation scripts).
10. **Interview craft**: DSA-lite (arrays/strings/hashmaps) for GCC screens; system-design narratives for LLM apps; STAR stories converting ops war-rooms into reliability achievements.

## 28. INDIA TRANSITION OPPORTUNITY RANKING (/100)

Weights: Demand 25 · Transferability 20 · Salary 15 · Growth 15 · Learning ease 10 · Low competition 10 · Remote 5.

| Rank | Role | Score | One-line rationale |
|---|---|---|---|
| 1 | **Cloud AI Engineer** | **78** | Highest demand × direct reuse of infra experience × Azure-first services volume |
| 2 | **AI Platform / LLMOps Engineer** | **77** | DevOps-adjacent, premium pay, GCC platform hiring wave |
| 3 | **AIOps / Intelligent Ops Engineer** | **76** | Tenure-as-qualification; lowest friction; ServiceNow+GenAI premium niche |
| 4 | GenAI Engineer | 71 | Biggest absolute demand but junior-flooded entry tier; portfolio-gated |
| 5 | AI Security Engineer | 70 | Small market, high premiums, low competition if security-adjacent |
| 6 | LLM Engineer | 68 | Same cluster as GenAI; fine-tuning/serving flavor favors infra minds |
| 7 | Agentic AI Engineer (as title) | 67 | Real growth; enter after establishing #1–4 base |
| 8 | AI Solutions Architect | 66 | Excellent second step at 10+ yrs; needs architecture narrative first |
| 9 | Intelligent Automation Engineer | 64 | Hybrid RPA+agents niche; moderate ceilings |
| 10 | Forward Deployed / AI Deployment Eng | 64 | Tiny base; startup pace; watchlist |
| 11 | Generative AI Product Engineer | 59 | Product ownership expected; weakest fit for ops profile |

Global ranking shifts only slightly: application-layer AI Engineer ranks #1 globally (volume), Cloud/AI-Platform #2, AIOps #5 (US titles scarcer than India's services ecosystem), AI Security #4 (higher US premiums $184–215K).

## 29. GLOBAL TRANSITION OPPORTUNITY RANKING

1. AI Engineer (application cluster) — unmatched volume, remote-rich
2. Cloud AI Engineer — every enterprise deployment
3. AI Platform/LLMOps — premium + DevOps adjacency
4. AI Security Engineer — $184–215K medians, acute shortage (64% of orgs)
5. AIOps/Observability-AI — smaller US title market than India
6. GenAI Solutions Architect — senior-friendly pre-sales track
7. FDE — extreme growth, tiny base
8. Agentic specialist — fold into #1–3 as specialization

## 30. TOP SKILLS BY CAREER ROI (India-weighted)

Tier S (learn now): Python production · RAG engineering · Azure OpenAI+AI Search · Evals/LLM-as-judge · LangGraph · MCP/tool-calling.
Tier A (within 3 months): AWS Bedrock · FastAPI · PostgreSQL/pgvector · Docker/K8s deploy-level · Guardrails · Terraform+CI/CD-for-AI · Observability/tracing.
Tier B (differentiators): vLLM serving · GraphRAG · voice agents · NIST AI RMF/ISO 42001 vocabulary · ServiceNow Now Assist (ops veterans) · FinOps-for-AI cost engineering.
Negative ROI: Kaggle portfolios, AutoML tools, TensorFlow-only study, prompt-only courses.

## 31. BEST THREE ROLES (INDIA)

Exactly three, ranked:
1. **Cloud AI Engineer (Azure-first, GenAI/RAG workload focus)** — largest lateral-accessible demand pool across services+GCC; monetizes existing infrastructure experience; clear certification path (AI-102 → AIF-C01).
2. **GenAI Engineer (application layer)** — biggest raw volume (+60% YoY skill growth); reachable within 6–9 months via deployed portfolio; consulting/services label fits Indian hiring culture.
3. **AIOps / Intelligent Operations Engineer** — the zero-reset emergency door: current tenure converts to seniority immediately; ServiceNow Now Assist/Dynatrace Davis wave creates a premium under-supplied niche while the bigger transition matures.

## 32. SINGLE BEST GLOBAL ROLE

**AI Engineer (application-layer cluster)** — ~80% of all AI postings collapse into it; remote density highest; every other target (GenAI, LLM, agentic, product) is a keyword variant of it. Enter via its platform sub-track if coming from infra.

## 33. SINGLE BEST INDIA ROLE

**Cloud AI Engineer with a GenAI/RAG specialization**, positioned inside GCC or IT-services AI practice.
Why: (a) matches India's actual JD formula ("total IT experience + relevant GenAI"); (b) rides both dominant stacks (Azure OpenAI services-side, Bedrock GCC-side); (c) sits in the 56% of GCC demand that is exactly the 4–12-yr cohort; (d) platform/data engineers are hired 5–6× more than core-AI staff; (e) salary path ₹12–22L services → ₹25–40L GCC mid-career → ₹40–60L senior without needing research credentials.

Primary: Cloud AI Engineer (GenAI/RAG) | Secondary: GenAI Engineer (app layer) | Backup transition: AIOps / Intelligent Operations Engineer.

## 34. INDIA JOB-READY TECHNOLOGY STACK (evidence-derived)

```
Python (production-grade)
  ↓
FastAPI (async APIs)
  ↓
LLM APIs — Azure OpenAI (primary) + OpenAI/Anthropic (portability) + Bedrock (GCC/BFSI)
  ↓
RAG pipeline: ingestion → chunking → embeddings → pgvector / Azure AI Search → hybrid search + reranker
  ↓
Agents: LangGraph + tool calling + MCP server + guardrails + human-in-loop
  ↓
Data: SQL + PostgreSQL (+ Databricks/Snowflake literacy)
  ↓
Cloud: Azure (AI Search, Functions, Container Apps) + AWS equivalents (Lambda, OpenSearch)
  ↓
Docker → Kubernetes (deploy-level)
  ↓
CI/CD with automated EVALS (RAGAS/LLM-as-judge gates)
  ↓
LLMOps: LangSmith/Langfuse tracing, registries, drift + token-cost dashboards
  ↓
Security & Governance: OWASP LLM Top 10, NeMo/Bedrock guardrails, NIST AI RMF + DPDP awareness
  ↓
(For ops veterans: ServiceNow Now Assist / AIOps integration layer as wedge project)
```

## 35. TEN TECHNOLOGIES TO LEARN (priority order)

1. Python + FastAPI 2. Azure OpenAI + AI Search 3. RAG with pgvector/hybrid retrieval 4. LangGraph agents 5. MCP (build one server) 6. Evals (RAGAS + LangSmith/Langfuse) 7. AWS Bedrock (working knowledge) 8. Docker + K8s deployment 9. Terraform + GitHub Actions for AI workloads 10. Guardrails + OWASP LLM Top 10 practices.

## 36. FIVE PORTFOLIO PROJECTS (all must be DEPLOYED with README metrics)

1. **Enterprise Doc-Q&A RAG** — hybrid BM25+dense + reranker over messy PDFs; recall@K + RAGAS scores published; pgvector + Azure AI Search comparison; token-cost table.
2. **AIOps Incident Summarizer** (leverage story) — ingest alerts from a monitored sandbox (Prometheus/Splunk-free tier), auto-triage + RCA draft + runbook suggestion via LLM; measure MTTA reduction on simulated incidents; optional Now Assist-style ServiceNow integration demo.
3. **Guarded Multi-Tool Agent** — LangGraph agent with MCP server exposing 3 tools (SQL query, ticket create, doc search); injection-attack test suite; HITL approval gate; full LangSmith trace published.
4. **Eval & Cost Dashboard** — golden dataset, LLM-as-judge vs human labels agreement score, per-version regression tracking in CI, latency/cost per answer — demonstrates THE scarce skill.
5. **Fine-tuned small-model service** — LoRA on a task (ticket classification), served via vLLM on cheap GPU, benchmarked vs GPT-4o-mini on accuracy AND cost; documents inference-optimization literacy.

## 37. INTERVIEW INTELLIGENCE

| Company type | Rounds | Focus |
|---|---|---|
| TCS/Wipro/Infosys | 4 (HR→Tech×2→Mgr→HR) | Sampling params/top-K, RAG pipeline design, function calling, Recall@K/RAGAS, live Python; GenAI round now STANDARD for all lateral DS/SDE hires |
| Accenture/consulting | 5–6 + Super Day | Agent architecture, guardrail-vs-prompt-injection design, cost/latency benchmarking, client case, multi-provider fallback |
| Infosys | 4 rounds/3–5 wks | Live coding; chunking internals (HNSW), agent error-recovery, MCP questions |
| BFSI GCC (JPMC/Citi) | 5–7 | System design, model-validation/compliance challenge, SQL+Python, STAR behavioral, take-home 3–5 hrs |
| Product GCC (Google/Walmart) | 4–6 | No-AI coding screen, LLM system design, production debugging, ownership stories |
| Startups (Sei/Tanla type) | 3–4 + take-home | Agentic build (Pipecat/LiveKit/vLLM), evals fluency, 0→1 portfolio, AI-tool mastery |

Macro shift: plan→build→review formats with AI allowed (Sierra); 2-hour onsite agent builds (Applied Intuition, 86% interviewer preference); Anthropic grades prompt-quality/verification/decomposition; **Indian consulting now mandates AI-tool use inside rounds — practice coding WITH Copilot/Cursor on camera.**

## 38. SIX-MONTH ROADMAP

- **Month 1:** Python refresh (async, FastAPI build) + Azure AI Fundamentals→start AI-102; ship Project 1 skeleton (RAG over own docs).
- **Month 2:** Finish AI-102; deep RAG (hybrid+rerank+pgvector); deploy Project 1 publicly with eval metrics; begin LinkedIn rewrite using Cluster-A title keywords.
- **Month 3:** LangGraph agents + MCP server (Project 3); add Bedrock variant of Project 1; internal outreach: volunteer for any GenAI/automation initiative at current employer (lateral-first strategy).
- **Month 4:** Evals month (Project 4 dashboard; wire eval gates into CI); publish 2 technical posts (RAG cost tuning; alert-summarization results); start applying — services tier first (TCS/Infosys/LTIMindtree/Persistent) for interview calibration.
- **Month 5:** AIOps wedge (Project 2) + ServiceNow Now Assist trial instance; apply to GCC roles (JPMC/Walmart/Optum/Lowe's/Hyderabad+Bengaluru clusters) with 75–80% ATS keyword mirroring; DSA-lite practice 3×/week for GCC screens.
- **Month 6:** Interview loops; negotiate using cluster-title salary data; fallback: convert current role toward AI-adjacent duties (champion Now Assist/Copilot rollout) if offers lag — internal redeployment costs employers 62% less, so keep that channel hot.

Weekly rhythm: 12–15 hrs learning, 5 hrs building, 2 hrs publishing/networking, 1 hr applications (from Month 4).

## 39. 50 INDIA JOB-SEARCH KEYWORDS

Core titles: 1 AI Engineer 2 GenAI Engineer 3 Generative AI Engineer 4 LLM Engineer 5 Applied AI Engineer 6 AI Software Engineer 7 AI Product Engineer 8 Full Stack AI Engineer 9 RAG Engineer 10 Agentic AI Engineer 11 AI Agent Developer 12 LLMOps Engineer 13 AI Platform Engineer 14 MLOps Engineer 15 AI Infrastructure Engineer 16 AIOps Engineer 17 AI Operations Engineer 18 Intelligent Automation Engineer 19 Cloud AI Engineer 20 AI Solutions Engineer 21 Forward Deployed Engineer 22 AI Deployment Engineer 23 AI Security Engineer 24 GenAI Security Engineer 25 AI Governance Lead 26 Responsible AI Consultant 27 AI Solutions Architect 28 GenAI Consultant 29 Context Engineer 30 Conversational AI Engineer.
Skill/description keywords: 31 Azure OpenAI 32 Azure AI Search 33 AWS Bedrock 34 Vertex AI 35 RAG 36 Retrieval Augmented Generation 37 LangChain 38 LangGraph 39 CrewAI 40 Semantic Kernel 41 Model Context Protocol (MCP) 42 Function Calling / Tool Calling 43 Vector Database 44 pgvector 45 FastAPI LLM 46 LLMOps 47 Prompt Engineering 48 AI Agents (description search) 49 ServiceNow Now Assist 50 GenAI Copilot Development.
Platform tips: run Cluster-A titles as OR searches on LinkedIn/Naukri; on Naukri also search descriptions ("agentic", "RAG", "GenAI") since exact titles undercount ~70×; set alerts for GCC employer names directly.

## 40. 15 HIDDEN INSIGHTS (what a normal job seeker would miss)

1. **Title words move salaries more than skills do** — identical JDs pay up to $86K apart depending on whether they say "AI Engineer" or "AI Software Engineer." Apply sideways-up: search the whole cluster, anchor negotiations to the highest-paying adjacent title.
2. **Boards lie about categories.** "Agentic AI Engineer" shows ~10K fuzzy hits but ~142 real ones (~1 exact per 70). The genuine agentic market hides inside ordinary AI-engineer/architect JDs — search descriptions, not titles.
3. **Hype inversely predicts some hiring.** LangGraph has the fewest GitHub stars yet ranks #2 in actual job demand; AutoGen is sunset yet still staffed. Hiring data leads social consensus by 2–3 quarters — mine JD counts, not star counts.
4. **Enterprises buy platforms, influencers sell frameworks.** Social debates LangChain vs CrewAI; enterprise JDs default to Bedrock/Azure OpenAI/Vertex services with frameworks as glue. Cloud-service fluency out-earns framework loyalty.
5. **India's experience reset is optional.** The dominant formula is "total IT years + 2–3 relevant GenAI years" (Cognizant literally prints it). Self-rejecting veterans who assume they must start junior are the largest untapped supply pool — which is why TeamLease can fill only 30% of reqs.
6. **The eval gap is the cheapest arbitrage left.** Almost everyone can wire a RAG demo; almost nobody ships recall@K/RAGAS/LLM-as-judge evidence. Eval artifacts convert ops profiles into "production AI engineer" narratives in interviews.
7. **GCCs are a parallel hidden market.** They hire the 4–12-yr cohort deliberately (56%), add 5–6 platform engineers per core-AI hire, pay 15–40% premiums, and run formal conversion tracks — yet most candidates only spray services-company applications.
8. **Your ops tenure flips sign depending on the room.** In app-layer startups it's a liability ("chatbot-demo fatigue"); in AIOps/platform/architect rooms it IS the qualification (Accenture hires 8+yr NOC veterans into AI advisory at senior grades). Aim the same resume at different rooms.
9. **Internal moves beat external switches economically.** Redeployment costs employers 62% less than exit-and-rehire — the budget case for your lateral transfer exists; you usually have to write it for your manager.
10. **Age bias is real externally, muted internally.** 90% vs 32% willingness gap for under-35 vs 60+ external AI hires makes the internal-first route not just cheaper but structurally fairer.
11. **Cert language is "preferred," never required — except as ATS keys.** AI-102/AIF-C01 appear as tie-breakers and keyword gates (GCC ATS bars ~75–80% match), not as skill proof. Certify fast, then let projects argue.
12. **Silent AI screening already started.** McKinsey/Kearney India mandate AI-tool use inside interview rounds; GCCs pilot Claude-Code productivity benchmarks. Not practicing AI-assisted coding on camera is the new "can't reverse a binary tree."
13. **Governance is the quiet gold rush.** AI-governance hiring grows 3× faster than AI overall in BFSI/pharma; nobody has >2 yrs ISO 42001 experience, so early movers get instant seniority — especially GRC/security-adjacent profiles.
14. **Geography arbitrage beats skill marginalia.** Hyderabad's +51% momentum and tier-2 GCC headcount growing +35% YoY mean the same skill set clears easier loops and cheaper living outside Bengaluru's 44% crowd.
15. **JDs lag layoffs of old stacks.** TensorFlow stalls, Keras −63%, AutoML vanished, prompt-only −35% — yet thousands still study them from outdated curricula. Check posting deltas before spending a single study hour.

## 41. FINAL CAREER ACTION PLAN

**Decision chain (evidence-locked):**
WHICH ROLE → Cloud AI Engineer (primary), GenAI Engineer (secondary), AIOps/Intelligent Ops (backup wedge).
WHICH SKILLS → Section 34 stack; Tier-S first (Python/RAG/Azure OpenAI/Evals/LangGraph/MCP).
WHICH CLOUD → Azure-first (services volume) + Bedrock working knowledge (GCC/BFSI) + Vertex literacy.
WHICH PROJECTS → Five deployed builds in §36, each with public metrics; lead with the AIOps summarizer to weaponize existing experience.
WHICH CITIES → Bengaluru + Hyderabad (volume/momentum), Pune (security angle), Kochi/Coimbatore (low-competition stable pivots); remote as supplement.
WHICH COMPANIES → GCCs first (JPMC, Walmart GT, Optum, Lowe's, Wells Fargo, Standard Chartered, Bosch, Siemens), then services AI practices (TCS/Infosys/LTIMindtree/Persistent), then product/SaaS after 12 months of GenAI delivery.
WHICH TITLES TO SEARCH → All of Cluster A + C + B keywords (§39); description-keyword searches for agentic.
RESUME → Mirror JD vocabulary ≥75%; lead with "total X yrs IT + Y yrs GenAI delivery"; quantify reliability wins; link deployed repos.
INTERVIEWS → Prepare RAG internals, agent error-recovery, guardrail design, cost/latency trade-offs, eval strategy; practice AI-assisted live building; STAR stories reframing ops crises as reliability engineering.
TIMELINE → Months 1–2 foundations+cert, 3 agents+internal pitch, 4 evals+applications, 5 GCC loops+AIOps wedge, 6 negotiate/close; fallback = internal conversion championing Now Assist/Copilot adoption.

**The single sentence to remember:** In a market where 380K Indian AI jobs will chase too few proven builders, the fastest route is not to become a new person but to make your existing decade count — total-experience-plus-GenAI positioning, platform-flavored role, deployed-and-evaluated proof, aimed at the GCC city of your choice.

---
*Report generated August 2026. Confidence tags throughout; anecdotal transition claims separated from statistical findings. Re-run recommended quarterly — agentic/MCP signals move monthly.*
