# A7 — Skills, Certs, Portfolio — August 2026

**Subject:** Manoj Kumar, 8.5 YOE Service Desk Lead / IT Ops, Cognizant, ~₹11 LPA, Coimbatore.  
**Target:** Practical GenAI / Agentic / LLM / AIOps / AI automation roles. **Not** Java-first, **not** SQL-analytics-first, **not** research-ML.  
**Constraint:** Skills and projects must leverage troubleshooting, enterprise support, ITSM, operations.  
**Recency of this snapshot:** 23 August 2026.

---

## Method

### What was counted

Three layers were used. They are **not** interchangeable.

| Layer | Source | What it measures | How to read it |
|---|---|---|---|
| **A. Absolute Naukri keyword volume** | naukri.com skill-tag pages, titles dated **August 2026** unless noted | How many live postings contain a token | Inflated by homonyms, recruiter keyword stuffing, and generic IT jobs. Use as *relative* volume, not as “this many GenAI jobs.” |
| **B. Conditional frequency inside AI Engineer JDs** | letsinterview.me scrape of **313 unique LinkedIn India AI Engineer listings**, published 25 Feb 2026 | % of *AI Engineer* postings that mention a skill | Best available India-specific mix for applied AI titles. Older than this report by ~6 months. |
| **C. Individual JDs and hiring-manager posts** | Naukri, LinkedIn, Foundit, hirist, Glassdoor, employer career pages, 2026 | Must-have vs preferred language, cert mentions, “real project only” filters | Highest signal for *what blocks a first shortlist*. |

### Recency tags used throughout

- **VERIFIED FACT** — observed on a live JD page, official vendor page, or a dated scrape with a public method.
- **COMMUNITY EXPERIENCE** — candidate reports, recruiter blogs, hiring-manager posts. Treat as directional, not census.
- **INFERENCE** — synthesis across sources; labelled as such.
- **RECOMMENDATION** — action for this profile only, after evidence.

### Keyword-inflation warning (Naukri)

These Naukri totals **cannot** be used as GenAI job counts:

- `python-jobs-in-india-remote` returned **175,556** — the token “python” leaks into unrelated listings.
- `datadog-jobs` **20,611–21,575** and `grafana-jobs` **33,091** are not “observability-for-AI” counts; they are platform-wide.
- `open-ai-jobs` **32,215** vs `openai-jobs` **3,566–3,801** — hyphenation and the words “open” + “ai” inflate the first.
- `mcp-jobs` is contaminated by **Microsoft Certified Professional** and unrelated MCP acronyms. Do not treat raw MCP counts as Model Context Protocol demand.
- `bedrock-jobs` **1,507** includes non-AWS noise (e.g. “Bedrock Tyres” collisions on some crawls).

**Rule used here:** Naukri counts are cited with the exact URL and date. Skill *priority* for Manoj is driven by Layer B (% inside AI Engineer JDs) plus Layer C (must-have language in 6–10 YOE JDs).

### Primary datasets

1. letsinterview.me, “I Analyzed 313 AI Engineer Job Listings…”, 25 Feb 2026 — https://www.letsinterview.me/blog/ai-engineer-jobs-india-2026  
2. Naukri skill pages, August 2026 snapshots (URLs in Source appendix).  
3. Live / recently closed JDs: Infosys GenAI/Agentic (LinkedIn/Glassdoor, Aug 2026); Cognizant AI Engineer LangGraph (Jun 2026); Optum LangChain/LangGraph/MCP (Mar 2026); UnitedHealth Group AI/ML Engineer Bengaluru (Aug 2026); Atos ServiceNow forward-deployed AI (Jun 2026); PepsiCo Now Assist (Jul 2026); NTT Data AI/GenAI Lead infra automation (May 2026); Kezan Consulting Agentic AI FastAPI; Anlage Infotech Senior GenAI 6–10 YOE; Staffnix Senior Python Backend GenAI; KDK Software GenAI Engineer.  
4. Official vendor cert pages: Microsoft Learn AI-103 / AI-102 retirement; AWS MLS-C01 retirement; Google Cloud Generative AI Leader; Databricks GenAI Engineer Associate; ServiceNow University exam fees; Linux Foundation CKA.  
5. Hiring-side verification blogs: SuperSourcing “Hiring GenAI & LLM Engineers from India: 2026 Guide” (2 Jun 2026); OwnYourCareer AI certs India (15 Aug 2026); Masai School Agentic AI skills (27 Jun 2026).

### What this report will **not** do

- Rank Scaler / Great Learning / Simplilearn as primary evidence.
- Invent salary premiums “because of a cert.”
- Treat a Hugging Face or DeepLearning.AI *course certificate* as equivalent to a proctored vendor exam.
- Recommend Java Spring, warehouse SQL, or “become a data scientist in 6 months.”

---

## Blocking vs optional skills (JD-backed frequency)

### How to read the table

- **Blocking** = appears as *must-have / mandatory / primary* on enough 6–10 YOE applied-GenAI or AIOps+GenAI JDs that a recruiter can reject without a screening call if it is missing from resume + GitHub.
- **Shortlist accelerator** = frequently listed; raises rank in ATS and recruiter Boolean, but one gap is survivable if the rest of the stack is proven.
- **Optional / niche** = named on a minority of JDs or only in specific clouds/vendors.
- **Naukri N** = absolute keyword volume, August 2026 unless dated. **% in AI Eng JDs** = letsinterview.me N=313 (Feb 2026).

### Master frequency table (applied GenAI + adjacent ops)

| Skill | Naukri N (Aug 2026 unless noted) | % of 313 AI Eng JDs (Feb 2026) | Blocking for first shortlist at 8.5 YOE ops? | Notes | Evidence |
|---|---|---|---|---|---|
| **Python** | Python Developer 4,689; “Python” token is far larger and inflated | **83%** (260/313) | **BLOCKING** for GenAI Engineer titles | Infosys lists “Python – Core: OOP, typing, modules, pytest/unittest, fixtures, basic async” as must-have. Cognizant AI Engineer 7–13 YOE: “Design… using Python.” | https://www.letsinterview.me/blog/ai-engineer-jobs-india-2026 ; https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669 ; https://in.linkedin.com/jobs/view/ai-engineer-python-langchain-langgraph-agentic-ai-api-llms-at-cognizant-4415497554 |
| **REST APIs / FastAPI** | FastAPI **3,238** | FastAPI **22%** (68/313) | **BLOCKING as a concept** (APIs). FastAPI itself is accelerator not the only framework | Almost every GenAI JD requires integrating LLMs with APIs. FastAPI is the most named Python web framework. Flask still appears. Django named on some backend-GenAI JDs (Staffnix). | https://www.naukri.com/fastapi-jobs ; Kezan Consulting Agentic AI Engineer FastAPI https://www.naukri.com/job-listings-sr-developer-python-fast-api-ai-ml-immediate-joiner-kezan-consulting-gurugram-bengaluru-delhi-ncr-3-to-7-years-081225008903 |
| **RAG** | RAG **6,876**; “Retrieval Augmented Generation” **3,241** | **48%** (149/313) | **BLOCKING** for GenAI Engineer / LLM Engineer | letsinterview: “If you only have time to learn two things, make it RAG and Agentic AI.” Anlage Infotech 6–10 YOE: “Only candidates with real project experience in LLM/RAG will be considered.” | https://www.naukri.com/rag-jobs ; https://www.naukri.com/retrieval-augmented-generation-jobs ; https://www.naukri.com/job-listings-senior-genai-engineer-python-rag-llm-agentic-ai-anlage-infotech-bengaluru-mumbai-all-areas-6-to-10-years-190626021342 |
| **Agentic AI / agents / tool calling** | Agentic AI **9,938** | **43%** (134/313) | **BLOCKING for 2026 “GenAI / Agentic” titles**; accelerator for generic “AI Engineer” | Infosys: “simple agent flows and routing” + LangChain/LangGraph. Cognizant: “autonomous AI agents capable of planning, reasoning, and tool usage.” | https://www.naukri.com/agentic-ai-jobs |
| **LangChain** | **4,122** | **42%** (131/313) | **Shortlist accelerator → near-blocking on services/product GenAI JDs** | Dominant orchestration keyword. Often paired with RAG (100 of 313 JDs list both). | https://www.naukri.com/langchain-jobs |
| **LangGraph** | Naukri Feb 2026 snapshot **1,152**; Glassdoor India Aug 2026 **1,675**; hirist **440** | Not separately %’d in Feb scrape (absorbed into LangChain/agentic) | **Accelerator, rising to near-must on 2026 agentic JDs** | Cognizant, Infosys, Optum, Sandisk, UnitedHealth all name LangGraph in 2026. | https://www.glassdoor.co.in/Job/india-langgraph-jobs-SRCH_IL.0,5_IN115_KO6,15.htm ; https://www.hirist.tech/k/langgraph-jobs |
| **OpenAI API** | openai-jobs **3,566–3,801** (do not use “open ai” 32k) | OpenAI/GPT **34%** (106/313) | **Blocking as “call an LLM API”**; provider can be Azure OpenAI / Bedrock / Gemini | Combine OpenAI + Azure OpenAI and the cluster is the default. | https://www.naukri.com/openai-jobs |
| **Azure OpenAI / Azure AI Foundry** | Azure overall **43,557–48,111** (all Azure, not GenAI) | Azure **49%** of AI Eng JDs; Azure OpenAI **12%** named | **Accelerator; blocking on Microsoft-account JDs** | Highest cloud share in the 313-JD set. Cognizant/Infosys/Accenture Microsoft accounts. | letsinterview.me §10 |
| **AWS Bedrock** | bedrock-jobs **1,507** (some noise) | AWS **45%** of AI Eng JDs (cloud, not Bedrock-specific) | **Blocking on Infosys/AWS-account GenAI JDs**; optional otherwise | Infosys GenAI/Agentic Engineer (Aug 2026): AWS Bedrock is a **must-have** alongside Python. | https://www.naukri.com/bedrock-jobs ; https://www.glassdoor.co.in/job-listing/genai-agentic-ai-engineer-infosys-JV_KO0,25_KE26,33.htm?jl=1010157961831 |
| **Vertex AI / Gemini** | Gemini **2,084**; “google cloud ai” inflated | GCP **37%**; Gemini/PaLM **13%** | Optional unless targeting TCS/Google Cloud / ADK JDs | TCS “Senior AI Engineer – Agentic AI & Multi-Agent Systems (Google Cloud)” names Vertex AI Agent Builder, ADK, MCP. | https://www.naukri.com/gemini-jobs |
| **Embeddings / vector DBs** | (no clean Naukri token) | Embeddings **31%**; Pinecone **19%**, Weaviate **13%**, FAISS **13%**, Chroma **12%** | **Blocking as a concept** (you must have used *one* store). Brand is interchangeable | JDs list FAISS, Pinecone, Chroma, Weaviate, Milvus, Qdrant, pgvector, Azure AI Search, OpenSearch as OR-lists. Pick one, know hybrid search. | Kezan 6–9 YOE: FAISS/Pinecone/Chroma/Weaviate/Milvus/Qdrant https://www.naukri.com/job-listings-ai-ml-engineer-immediate-joiner-kezan-consulting-gurugram-bengaluru-delhi-ncr-6-to-9-years-081225007236 |
| **LlamaIndex** | **841** (Feb 2026 Naukri snapshot — stale) | **15%** (47/313) | Optional | Alternate RAG framework. LangChain wins volume. | https://www.naukri.com/llamaindex-jobs |
| **CrewAI** | No clean Aug 2026 Naukri total captured | **11%** (33/313) | Optional | Named as “or similar” with AutoGen. Kezan Agentic AI Engineer: LangGraph **and** CrewAI. | letsinterview.me §8 |
| **AutoGen** | No clean total | Bundled with CrewAI | Optional | Infosys Agentic AI Engineer: “LangChain, AutoGen, or CrewAI.” | https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-infosys-4441390349 |
| **Semantic Kernel** | No clean total | Not in top table | Optional / Azure-.NET shops | Appears on Microsoft-stack JDs, often with C#. Skip unless targeting those. | Naukri snippets (Capgemini Agentic AI PM; Sr AI Engineer Semantic Kernel) |
| **MCP (Model Context Protocol)** | Raw “MCP” counts are **contaminated** | Not in Feb 2026 top table (protocol too new) | **Optional today; named on 2026 enterprise agentic JDs** | Optum India: “Lang Chain, Lang Graph and MCP” as hands-on expertise. Atos ServiceNow AI: “A2A and MCP-based AI integration approaches is an advantage.” Emerson GenAI Developer: LangChain, AutoGen, Copilot, **MCP**. | https://in.linkedin.com/jobs/view/ai-ml-engineer-lang-chain-lang-graph-and-mcp-at-optum-india-4388550311 ; https://jobs.atos.net/job/Bangalore-ServiceNow-forward-deployed-AI-engineer/1409487633/ |
| **Evals / guardrails / LangSmith** | No clean Naukri total | Fine-tuning **37%**; prompt **33%** — evals not separately %’d | **Accelerator for senior; differentiator vs tutorial clones** | Infosys: “basic evaluation awareness” + Bedrock “guardrails & access controls.” SuperSourcing hiring guide: look for RAGAS / custom eval scripts on GitHub. | SuperSourcing 2 Jun 2026 https://supersourcing.com/blog/hiring-genai-llm-engineers-india/ |
| **Git** | (all-IT, not useful as N) | **27%** (84/313) | **Blocking as hygiene** | Assumed. No Git = no shortlist for engineering titles. | letsinterview.me §13 |
| **Docker** | **47,986** (all IT) | **31%** (98/313) | **Accelerator → near-blocking for “deployed” claims** | Infosys: “Docker basics.” UnitedHealth: Docker + Kubernetes. | https://www.naukri.com/docker-jobs |
| **CI/CD** | (all IT) | **34%** (105/313) | Accelerator | GitHub Actions / Azure DevOps / GitLab. Infosys: “tested, maintainable Python… CI/CD pipelines.” | letsinterview.me §13 |
| **Kubernetes** | **25,624–26,059** (all IT) | **23%** (72/313) | **Optional for first GenAI shortlist**; blocking for MLOps/platform | Do not spend 90 days on CKA unless targeting platform/MLOps. | https://www.naukri.com/kubernetes-jobs |
| **Terraform** | **20,289** (all IT) | Not in top 313 table | Optional | Named on some Sr AI Engineer / cloud-AI infra JDs. | https://www.naukri.com/terraform-jobs |
| **Linux** | Python+Linux **8,682** | Not %’d | Accelerator (ops background already covers) | Shell + process + logs is assumed for AIOps. | https://www.naukri.com/python-and-linux-jobs |
| **ITIL** | ITIL+ServiceNow **5,706** (Jul 2026 snapshot) | Not an AI Eng keyword | **Blocking for ITSM/AIOps/Service Desk Lead+AI**; irrelevant for pure GenAI IC | Cognizant Service Management CoE (Aug 2026) still lists ITIL Foundation on multiple roles. | https://www.naukri.com/itil-servicenow-jobs ; https://www.glassdoor.co.in/job-listing/service-management-experts-cognizant-technology-solutions-JV_IC2865319_KO0,26_KE27,57.htm?jl=1009951210332 |
| **ServiceNow** | SN Developer **5,983** | Not in 313 AI Eng mix | **Blocking for SN+GenAI / Now Assist path**; optional for Python GenAI IC | Atos, PepsiCo, Birlasoft, Cognizant Agentic AI SN Expert, TCS AI Operations Engineer. | https://www.naukri.com/servicenow-developer-jobs |
| **Splunk** | **8,531** (page may be location-skewed) | Not in 313 mix | Accelerator for AIOps | UnitedHealth AI/ML Engineer Bengaluru: Splunk, Dynatrace, CloudWatch, Azure Monitor, Log Analytics. | https://www.naukri.com/splunk-jobs ; https://careers.unitedhealthgroup.com/job/bengaluru/ai-or-ml-engineer-llms-rag-langchain-langgraph/34088/99093468144 |
| **Datadog / Prometheus / PagerDuty** | Datadog raw N inflated; Prometheus **3,892** (Apr 2026) | Not in 313 mix | Optional except SRE/AIOps JDs | Use as “observability” story, not as a cert path. | https://www.naukri.com/prometheus-jobs-32 |
| **PowerShell / Bash** | (ops-wide) | Not in 313 mix | **Accelerator for runbook/automation path**; not a GenAI IC must | NTT Data AI/GenAI Lead: Ansible + Python + ServiceNow. Windows estates still want PowerShell. | https://careers.services.global.ntt/global/en/job/P-100236/AI-GenAI-Lead-Infrastructure-Automation-Ansible-Python-ServiceNow |
| **n8n / Zapier / Power Automate** | n8n **203** (Jan 2026 snapshot — stale/small) | n8n not in 313 top table | **Optional / niche automation-agent roles** | Named on Agentic AI + n8n JDs (Welkin Soft, Cibronix, Unicorn Lab architect). Power Automate appears on Copilot/D365/ServiceNow hybrid JDs. | https://www.naukri.com/n8n-jobs ; https://in.linkedin.com/jobs/view/agentic-ai-and-genai-engineer-with-n8n-expertise-at-welkin-soft-tech-pvt-ltd-4405751777 |
| **PyTorch / TensorFlow** | HuggingFace **333** | PyTorch **30%**, TF **28%**, HF **23%** | **Not blocking for applied GenAI**; often copy-paste on services JDs | Infosys Bedrock JD does **not** require TF/PT. Fine-tuning listed 37% but many applied JDs accept “API + RAG.” | letsinterview.me §8, §11 |
| **Java** | — | **12%** (36/313) | **Do not pursue for this profile** | Present, but a minority of AI Engineer listings. Violates profile constraint. | letsinterview.me §7 |
| **SQL** | — | **20%** (64/313) | **Working knowledge, not a career bet** | Enough to query incident tables / pgvector. Not a data-analyst path. | letsinterview.me §7 |
| **Fine-tuning (LoRA/QLoRA)** | — | **37%** (115/313) | Optional for first ops→GenAI shortlist | Over-indexed in generic AI/ML JDs. Applied GenAI JDs more often want RAG first (see Azure/GCP interview Qs: “business wants to fine-tune on 300 PDFs” → push back, propose RAG). | https://cloudsoftsol.com/blog/azure-ai-interview-questions-answers/ |

### Blocking vs optional — first shortlist at 8.5 YOE ops (plain language)

**VERIFIED FACT (Layer C):** Recruiters for 6–10 YOE GenAI roles are filtering on *hands-on LLM/RAG project language*, not on Service Desk tenure. Anlage Infotech (6–10 YOE, Jun 2026): “Only candidates with real project experience in LLM/RAG will be considered.” SuperSourcing (Jun 2026) tells *employers* to refuse a senior GenAI screen if there is no GitHub/portfolio evidence of production RAG.

**INFERENCE for Manoj — two doors, different blocking sets:**

| Door | Typical titles | Blocking for *first* shortlist | Can stay optional | Why this door exists for an ops lead |
|---|---|---|---|---|
| **Door 1 — Applied GenAI IC** | GenAI Engineer, LLM Engineer, Agentic AI Engineer, Python + RAG | Python (OOP + pytest + APIs), one LLM API, a RAG pipeline you can demo, Git, ability to talk chunking/embeddings/eval | LangGraph depth, MCP, K8s, Terraform, LoRA, CrewAI/AutoGen, CKA | Highest volume (Naukri GenAI **7,887**; Agentic **9,938**) but you compete with backend Python people. |
| **Door 2 — ITSM/AIOps + GenAI** | ServiceNow + Now Assist / Agentic, AIOps Engineer, AI Operations Engineer, GenAI Lead – infra automation | ITSM process fluency (already have), ServiceNow *or* equivalent tool proof, incident/problem/change language, one automation/LLM overlay, stakeholder comms | CSA/CIS if going SN-developer-deep, Dynatrace/Moogsoft, Ansible, Databricks | Naukri AIOps **558–680** is smaller, but JDs explicitly want ops + AI (Atos, PepsiCo, NTT, TCS, AT&T IAM AIOps, Cognizant SN Expert Agentic AI). Less Python-from-scratch competition. |
| **Door 3 — Automation/agentic ops** | Agentic AI + n8n, Power Platform + Azure OpenAI, runbook agents | Workflow automation + LLM API + REST integrations | Visual builders as *primary* skill | Lower ceiling than Door 1; useful as a **90-day proof** while Python matures. |

**RECOMMENDATION:** Do not pick Door 1 *or* Door 2. Use Door 2 domain (ITSM/incidents/on-call) as the **portfolio content**, and Door 1 skills (Python, RAG, agents, FastAPI, Docker) as the **implementation**. That combination is rare in the 313-JD set (almost none of those listings asked for ServiceNow + LangChain together). That rarity is the conversion thesis.

### What is *not* blocking (even if JDs name it)

- PhD / Master’s — Bachelor’s is baseline (62% of 313); Master’s 28%; PhD 3%. **VERIFIED FACT.**
- TensorFlow-from-scratch, custom transformer training, CUDA.
- Java, Spring Boot, heavy SQL warehouses.
- “Prompt Engineer” as a title — see Time-wasters.
- A stack of MOOC certificates without a repo.

---

## Python/engineering bar for ops-to-AI

### What JDs actually test (not “learn all of Python”)

**VERIFIED FACT — Infosys GenAI / Agentic AI Engineer must-haves (LinkedIn, posted ~19 Aug 2026, 200+ applicants):**

> Python – Core concepts: OOP, typing, modules, pytest/unittest, fixtures, basic async  
> AWS Bedrock – Model invocation (Claude/Titan), Knowledge bases or retrieval, basic guardrails & access controls  
> Generative AI – Prompting (system, few-shot), RAG types, basic evaluation awareness, LangChain / LangGraph, simple agent flows  
> DevOps basics – Git, PRs, CI pipelines, Docker basics, artifacts  
> Also: monitor latency, token usage, cost.

Source: https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669 and Glassdoor mirror https://www.glassdoor.co.in/job-listing/genai-agentic-ai-engineer-infosys-JV_KO0,25_KE26,33.htm?jl=1010157961831

**VERIFIED FACT — Staffnix Senior Python Backend + GenAI (LinkedIn, May 2026):** mandatory Python backend (Django/Flask/FastAPI) + REST; LLM integration in production; RAG with Pinecone or PGVector; PostgreSQL; Git. 3+ years application development + at least 6 months hands-on GenAI.

Source: https://in.linkedin.com/jobs/view/senior-python-backend-engineer-genai-llm-langchain-langgraph-rag-fastapi-postgresql-agentic-ai-at-staffnix-4433490913

**VERIFIED FACT — Kezan Consulting Agentic AI Engineer (Python FastAPI), 3–6 YOE, ₹20–22.5 LPA:** “Advanced proficiency in Python”; FastAPI microservices; LangGraph and CrewAI; MongoDB and VectorDB; Hugging Face / LangChain; prompt engineering.

Source: https://www.naukri.com/job-listings-sr-developer-python-fast-api-ai-ml-immediate-joiner-kezan-consulting-gurugram-bengaluru-delhi-ncr-3-to-7-years-081225008903

### Practical bar for an 8.5 YOE ops lead (INFERENCE, mapped to those JDs)

You do **not** need to be a 5-year Python backend engineer. You **do** need to clear a 45-minute screen that looks like this:

| Competency | Bar that matches Infosys/Kezan/Staffnix language | Typical fail for ops switchers |
|---|---|---|
| Language | Write a FastAPI endpoint, parse JSON, use `httpx`/`requests`, type hints, a pytest for the happy path and one failure | Notebook-only Python; cannot structure a package |
| LLM I/O | Call Azure OpenAI or Bedrock; set system prompt; parse tool-call JSON; log tokens | ChatGPT UI screenshots as “experience” |
| RAG | Chunk → embed → retrieve top-k → cite sources → refuse when retrieval is empty | Copy of LangChain quickstart with no eval |
| Agents | One graph: retrieve → decide → call a tool (create ticket / run script) → write result; handle tool failure | Multi-agent “crew” demo with no error path |
| Eng hygiene | Git history that is not one “final commit”; Dockerfile; `.env` not committed; README with how to run | Private Drive zip of a course project |
| Ops overlay | Latency, cost per query, hallucination on a golden set of 50 tickets | No numbers |

**Python time budget (RECOMMENDATION):** 4–6 weeks of deliberate practice at ~10 hours/week is enough to *start* portfolio work if you already script in PowerShell/Bash. The Infosys list is the syllabus. Do not detour into NumPy-from-scratch or DSA leetcode beyond arrays/hashes unless a GCC OA appears.

**DSA:** OwnYourCareer and product-company tracks still require coding OAs for GCC/product. Services GenAI interviews (Infosys/Cognizant/LTI) more often whiteboard RAG/agent design. **Insufficient reliable evidence (N small)** that Coimbatore services-to-services GenAI loops will give a hard DSA round. Budget 2 weeks of easy/medium Python problems *after* the first repo exists, not before.

---

## Platform skills (Azure/AWS/GCP) evidence

### Cloud share inside AI Engineer JDs (VERIFIED FACT)

letsinterview.me N=313, India, Feb 2026:

| Cloud | Jobs | % | Implication for Manoj |
|---|---|---|---|
| Azure | 154 | **49%** | Default if you pick one cloud. Microsoft + Infosys/TCS/Accenture accounts. |
| AWS | 141 | **45%** | Infosys Bedrock JD is explicit. |
| GCP | 116 | **37%** | Real, but third. TCS Vertex/ADK roles exist. |

Source: https://www.letsinterview.me/blog/ai-engineer-jobs-india-2026 §10

Co-occurrence: Python+Azure **140**, Python+AWS **134**, Python+RAG **138**, Python+LangChain **125**. Azure is not “legacy”; it is the most co-listed cloud with Python for AI Engineer titles in that scrape.

### Platform AI services — what JDs name

| Service | Where it is mandatory vs preferred | Example JD |
|---|---|---|
| **Azure OpenAI / AI Foundry / AI Search** | Mandatory on Microsoft-stack GenAI; preferred elsewhere | QBID Infotech Azure AI Architect 8–9 YOE, LangChain/LangGraph, Azure OpenAI, AKS — https://in.indeed.com/viewjob?jk=1297521d00b8e3bf ; ZK Technologies AI Engineer Python & Azure AI, 4–5 YOE, **Azure AI Engineer Associate required** — https://in.linkedin.com/jobs/view/ai-engineer-python-azure-ai-at-zk-technologies-4432952119 |
| **AWS Bedrock + Knowledge Bases + Guardrails** | Mandatory on Infosys GenAI/Agentic (Aug 2026) | Infosys JD cited above |
| **Vertex AI / Gemini / Google ADK** | Mandatory on TCS/Google Cloud agentic JDs | TCS Senior AI Engineer Agentic + Vertex AI Agent Builder + MCP + ADK — https://www.naukri.com/google-cloud-jobs |
| **Azure AI Search / OpenSearch / pgvector** | Listed as vector-store options | McLaren Strategic (8–12 YOE, Bangalore): Pinecone, Chroma, Weaviate, FAISS, Azure AI Search — https://www.hirist.tech/j/mclaren-strategic-solutions-generative-ai-developer-rag-pipelines-1625811 |

### Which cloud should Manoj pick?

**RECOMMENDATION (INFERENCE):**

1. **Primary: Azure** — highest share in AI Engineer JDs; Cognizant Microsoft accounts; ITSM/M365/ServiceNow adjacency; AI-103 exists specifically for apps+agents.  
2. **Secondary literacy: Bedrock concepts** — so Infosys-style JDs are not auto-rejects (Knowledge Bases ≈ RAG, Guardrails ≈ content filters). One weekend of Skill Builder + a Bedrock Knowledge Base lab is enough to speak the dialect.  
3. **Do not collect all three clouds.** OwnYourCareer (15 Aug 2026): “Three associate logos look like panic.” https://www.ownyourcareer.in/blog/ai-certifications-india-2026-worth-it

Cognizant is multi-cloud. Your **current account’s cloud** still wins if you can name it on the resume. If the account is Microsoft-heavy, Azure is not a detour.

---

## AIOps / ITSM overlap skills

This is the part of the market that **does not require you to pretend you are a 5-year Python backend engineer**.

### Volume

| Token | Naukri N | Recency | Caveat |
|---|---|---|---|
| AIOps | **558–680** | Aug 2026 | Small vs GenAI 7,887. Higher fit. |
| ServiceNow Developer | **5,983** | Aug 2026 | Includes classic SN, not only AI. |
| ITIL + ServiceNow | **5,706** | Jul 2026 | Process + platform. |
| ServiceNow CSA (LinkedIn India) | **9,000+** “CSA jobs” | Aug 2026 | LinkedIn string is noisy (CSA ≠ only SN). |

https://www.naukri.com/aiops-jobs  
https://www.naukri.com/servicenow-developer-jobs

### JDs that map onto Service Desk Lead + GenAI (Door 2)

**1. Atos — ServiceNow forward deployed AI engineer, Bangalore (29 Jun 2026)**  
Now Assist, GenAI Skills, AI Agents, AI Search, Predictive Intelligence, Virtual Agent. Advantage: **A2A and MCP**. JavaScript/Glide (SN-native — a real gap for a non-SN-developer).  
https://jobs.atos.net/job/Bangalore-ServiceNow-forward-deployed-AI-engineer/1409487633/

**2. PepsiCo — Developer DEEx AI Search / NowAssist (ServiceNow GenAI), India (Jul 2026)**  
Now Assist, AI Search, Virtual Agent, semantic search, embeddings, REST APIs, **9+ YOE**. Qual: ServiceNow CIS – AI & Virtual Agent.  
https://www.bayt.com/en/india/jobs/developer-deex-ai-search-nowassist-servicenow-genai-74303169/

**3. Cognizant — ServiceNow Expert – Agentic AI, Chennai (28 Apr 2026)**  
6+ YOE SN development; integrate **Claude / OpenAI / Azure OpenAI** via REST & IntegrationHub; Virtual Agent, Now Assist, Flow Designer. Nice to have: SN certs, **AIOps**, Azure/AWS.  
https://careers.cognizant.com/us-en/jobs/00068415441/servicenow-expert-agentic-ai/

**4. TCS — AI Operations Engineer ITSM & Agentic Automation (closed, described Mar 2026)**  
Now Assist, Aisera, agentic triage of password/access incidents, RPA + GenAI, CMDB. 3+ YOE ITSM.  
https://www.foundit.in/job/itsm-cmdb-spm-irm-tprm-gen-ai-rpa-agentic-ai-tata-consultancy-services-bengaluru-bangalore-44223355

**5. NTT Data — AI / GenAI Lead – Infrastructure Automation (Ansible + Python \| ServiceNow), Mumbai, 10–14 YOE (May 2026)**  
Ansible + Python ownership; ServiceNow incident/change/request automation; ELK event-based automation; “Define Agentic AI and GenAI roadmap for operations.”  
https://careers.services.global.ntt/global/en/job/P-100236/AI-GenAI-Lead-Infrastructure-Automation-Ansible-Python-ServiceNow

**6. AT&T Bengaluru — Sr Specialist Cybersecurity IAM Operations AIOps (Jun 2026)**  
ServiceNow + AIOps: noise reduction, MTTR, Predictive Intelligence, incident clustering. (Asks 10+ years AI/AIOps on SN — treat as a stretch/adjacent signal, not a literal 10-year AI requirement.)  
https://www.att.jobs/job/bengaluru/sr-specialist-cybersecurity-iam-operations-aiops/117/91583646528

**7. UnitedHealth Group Bengaluru — AI or ML Engineer LLMs, RAG, LangChain, LangGraph (11 Aug 2026)**  
Spring AI / LangChain / LangGraph; **Splunk, Dynatrace, CloudWatch, Azure Monitor, Log Analytics**; Docker/K8s; Azure OpenAI / Bedrock / AI Foundry / Azure AI Search. This is the hybrid “ops observability + LLM” JD.  
https://careers.unitedhealthgroup.com/job/bengaluru/ai-or-ml-engineer-llms-rag-langchain-langgraph/34088/99093468144

**8. AIOps Engineer, 3–5 YOE, Hybrid Pune/Coimbatore/Bengaluru, ₹8–15 LPA**  
ServiceNow, Azure, GCP, Dynatrace, Moogsoft, Bash. **Coimbatore is on the location list.**  
https://www.naukri.com/aiops-jobs

### Mapping Manoj’s existing skills → JD language

| You already do | JD phrase to steal | Proof artifact |
|---|---|---|
| Major incident comms, bridge, timeline | “incident summarization, RCA narrative, stakeholder updates” | Anonymized timeline → LLM summarizer eval |
| Ticket routing / assignment / SLA | “classification, assignment prediction, misroute reduction” | Classifier or LLM router vs historical labels |
| Runbooks, KEDB, knowledge articles | “RAG over runbooks with citations; refuse when not in KB” | RAG + citation + “I don’t know” tests |
| On-call, escalation, PagerDuty-like | “on-call assistant, next-best-action, human-in-the-loop” | LangGraph with approval node |
| Tool sprawl (ITSM + monitoring + AD) | “tool calling / MCP to ticketing and observability APIs” | MCP server wrapping a mock ServiceNow |
| Shift lead / coaching | “runbook quality, deflection, MTTR” — lead-level bullets | Metrics if you can get them (even team-level) |

**RECOMMENDATION:** If ServiceNow is the account tool, **CSA is Door 2 hygiene** (see cert table). If the account is Remedy/Cherwell/Jira Service Management, do **not** spend 8 weeks becoming a SN developer; spend that time on REST + LLM against a mock ITSM.

JavaScript/Glide is a **real gap** for SN *developer* titles (Atos, Cognizant SN Expert). For “AI overlay on ITSM” you can stay Python-side and integrate via REST — which several JDs allow (Cognizant: “REST & IntegrationHub”; PepsiCo: “secure REST APIs”).

---

## Certification ROI table (cost, time, JD mentions, community opinion)

**Method:** Recommend a cert only if (a) a 2026 JD or hiring-manager post named it, or (b) the official vendor career/cert page exists and JDs name the *platform* the cert maps to. Marketing pages of Scaler / Great Learning / Simplilearn are not used as primary ROI evidence.

Prices: exam fee as published. INR = exam + 18% GST where USD-priced, using ~₹90–96/USD mid-2026 bands. **Confirm on Pearson VUE / vendor on booking day.**

### Cloud / AI vendor exams

| Cert | Official status (Aug 2026) | Exam fee | Typical prep | Named on JDs? | Recruiter / hiring-side comments | ROI for this profile |
|---|---|---|---|---|---|---|
| **Microsoft AI-900** | **Retired Jun 2026.** Successor **AI-901** Azure AI Fundamentals. Official: Microsoft Credentials roundup 25 Jun 2026. | AI-900 was ~₹3,696 in India (Microsoft geo-pricing). AI-901 expected same fundamentals tier (~$99 / ~₹3,700–4,200). | 1–2 weeks | Rarely *required*. Fundamentals are resume noise unless HR keyword-matches “Azure AI.” | OwnYourCareer: keyword unlock only. | **Skip unless free voucher.** Does not prove you can ship RAG. |
| **Microsoft AI-102** Azure AI Engineer Associate | **Retired 30 Jun 2026.** Cannot be earned or renewed. Existing holders keep transcript line. Official AWS-style retirement analog on Microsoft Hub. | Was $165 / India associate band ~₹4,800–13,800 depending on source year. | n/a | **Yes, still appears on JDs written before/during transition** (ZK Technologies “Azure AI Engineer Associate required”; CLaaS2SaaS lists AI-102; Cyclotron “nice not mandatory”; Blend “good to have”). | SuperSourcing: no cert verifies production GenAI. | **Do not sit AI-102.** Sit **AI-103** if sitting any Azure AI associate. |
| **Microsoft AI-103** Azure AI Apps and Agents Developer Associate | **Live.** Official Learn page. Python assumed. Foundry + agents. 120 min, pass 700/1000. | **$165 USD** regional; India associate historically ~₹4,800–5,000 (confirm VUE). | 4–8 weeks if already building RAG/agents on Azure | Too new for a large JD corpus. AI-102 language still in the wild. Microsoft Hub: this is the replacement role cert. | Aligns with “apps and agents” hiring, not classic Cognitive Services. | **Highest-ROI Azure exam IF target JDs are Azure.** Pair with a Foundry/Azure OpenAI repo. Official: https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-apps-and-agents-developer-associate/ and study guide https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103 |
| **Microsoft AZ-104** Azure Administrator | Live. Associate. | $165 / India ~₹4,800–4,865 (Microsoft Q&A Jul 2025; 2026 blogs still cite ~₹4,800). | 6–10 weeks | Named on infra/admin JDs, not GenAI IC. | Strong for cloud-ops, weak as a GenAI differentiator. | **Optional.** Take only if Door 2 + Azure ops, or employer voucher. Do not spend 90 days here instead of a RAG repo. |
| **Microsoft AZ-400** DevOps Engineer Expert | Live. $165 / ~₹4,800. | 8–12 weeks | Appears on Azure DevOps / CI-CD JDs; CLaaS2SaaS listed it among Microsoft certs for Azure AI Engineer. | Overkill for first GenAI shortlist. | **Defer.** GitHub Actions + Docker on the repo is cheaper proof. |
| **AWS Certified AI Practitioner (AIF-C01)** | Live. Foundational. Official $100. 65 Q, 90 min, 3-year validity. | **$100** + GST ≈ **₹10,000–11,300** in India (ExamCert / Find My Guru 2026). | 30–40 hours | **Insufficient reliable evidence (N=JDs naming AIF-C01 specifically is low).** AWS as a *cloud* is in 45% of AI Eng JDs; the *exam code* is not what Infosys wrote. | AWS positioning: non-engineer AI literacy. SuperSourcing: GitHub > cert. OwnYourCareer: sit only if JDs name the family. | **Low-to-medium.** Cheap keyword for Bedrock/AI literacy. **Do not** treat as a GenAI engineer credential. Useful if Infosys/AWS account screening is HR-driven. |
| **AWS ML Engineer Associate (MLA-C01)** | Live. Associate. $150. | $150 + GST ≈ ₹15,000–17,000 | 6–10 weeks | Newer than MLS; JDs still say “AWS / SageMaker / Bedrock” more than exam codes. | Intended successor path for builders. | **Medium, only after a Bedrock/SageMaker project.** Not week-1. |
| **AWS Machine Learning – Specialty (MLS-C01)** | **Retired. Last day 31 Mar 2026.** Official AWS: https://aws.amazon.com/certification/certified-machine-learning-specialty/ Holders keep badge 3 years. | Was $300 | n/a | Historical. | Do not start. | **Do not sit. Closed.** |
| **AWS Certified Generative AI Developer – Professional (AIP-C01)** | Live (2026). $300. Scenario-heavy. | $300 + GST ≈ ₹30,000–34,000 | 8–16 weeks + real Bedrock delivery | Too new for a large India JD sample. | Aimed at people who already ship GenAI on AWS. | **Defer.** Costly. Prove Bedrock on GitHub first. |
| **AWS Cloud Practitioner (CLF-C02)** | Live. $100. | $100 + GST | 2 weeks | Rarely on GenAI JDs. | Entry cloud literacy. | **Skip** if you can already talk IAM/S3/VPC. Overlap with AIF-C01 if you need one foundational AWS badge — pick **AIF-C01** over CLF for this target. |
| **Google Cloud Generative AI Leader** | Official. $99. 90 min, 50–60 MCQ, **no coding required**, 3-year validity. https://cloud.google.com/learn/certification/generative-ai-leader | $99 + tax | 20–40 hours | Foundit listed **128** “Google Cloud Generative Ai Leader” jobs in India (directional; many will be “nice to have”). | Vendor page: business/strategy audience. | **Low for IC builder roles.** Optional for consulting/pre-sales flavour. Not a substitute for Vertex hands-on. |
| **Google Professional ML Engineer** | Official. $200. Does **not** directly assess coding (vendor note). https://cloud.google.com/learn/certification/machine-learning-engineer | $200 + GST ≈ ₹16,500–18,500 | 8–12 weeks | Named more on GCP ML/Vertex JDs than on LangChain RAG JDs. | OwnYourCareer: GCC/GCP lane. | **Skip unless 2+ target JDs are Vertex/GCP.** |
| **Databricks Certified Generative AI Engineer Associate** | Official. $200. 45 scored Q, 90 min, 2-year validity. RAG + Mosaic/AI Search + Model Serving + MLflow + Unity Catalog. https://www.databricks.com/learn/certification/genai-engineer-associate | **$200** + tax ≈ ₹18,000–20,000 | 4–8 weeks if you use Databricks | OwnYourCareer: data-platform badges appear on analytics/AI GCC JDs. **Insufficient reliable evidence (N=public GenAI-IC JDs requiring this exam code)** for Door 1. | Useful if target is bank GCC / lakehouse AI, not Service Desk→LangChain. | **Defer.** Wrong stack unless you land a Databricks account. |
| **Snowflake** (SnowPro / Cortex-adjacent) | Vendor certs exist | SnowPro Core ~$175 (confirm) | — | Luxoft India AI Engineer JD mentioned “Snowflake Cortex” among multi-cloud AI infra. | Data-engineering lane. | **Skip** for this profile (SQL-warehouse adjacent; profile constraint). |

Microsoft Hub (25 Jun 2026) also launched **AB-620 AI Agent Builder Associate** and **GH-600 GitHub Certified Agentic AI Developer** (beta; GH-600 beta noted as not available in India in one Hub post). **Insufficient reliable evidence (N=India GenAI JDs citing AB-620 or GH-600)** — do not pay for these in the next 90 days unless a named JD requires them.  
https://techcommunity.microsoft.com/blog/skills-hub-blog/microsoft-credentials-roundup-june-2026/4528350

### ITSM / ops certs

| Cert | Official cost | Time | JD mentions | Community | ROI for Manoj |
|---|---|---|---|---|---|
| **ITIL 4 Foundation** | Exam-only India **₹8,500–₹12,000** (CertScope 2026). Bundled ATO training often **₹30,000–₹35,000**. PeopleCert, 3-year validity. | 1–2 weeks if you already run incident/problem/change | **Heavy on ITSM/AIOps JDs.** Cognizant Service Management CoE (Aug 2026): ITIL Foundation on Availability, reporting, service request roles. Ericsson/others “preferred.” | Table stakes for ops leads; not a GenAI differentiator. | **Keep current / renew if lapsed.** Cheap credibility for Door 2. Do not redo if you already hold v3/v4. |
| **ServiceNow CSA** | **Official ServiceNow University (2026): CSA/CAD/CAS-PA = $300 USD** exam; on-demand training **$0**; ILT includes an attempt. CIS = **$450**. Retake CSA **$150**. Partner orgs often $0 first attempt. https://learning.servicenow.com/lxp/en/pages/now-learning-knowledge-search?id=kb_article_view&sys_kb_id=fc603dbd47153a9019dfe23c326d43a2 and community thread Jan 2026 https://www.servicenow.com/community/training-and-certifications/2026-exam-vouchers-courses-exams-amp-retakes-major-changes/ba-p/3464930 | 3–6 weeks with PDI practice | **Often mandatory** for SN developer/admin: “CSA Mandatory” appears on multiple Naukri SN JDs. Birlasoft Now Assist Architect: CSA, CAD, CIS preferred. Cognizant SN BA: CSA. | India student thread quoted ~$354 / ₹32,200 all-in (Feb 2026) — **use official $300 + tax**. | **High ROI if Door 2 = ServiceNow.** If you cannot get a PDI and will not script Glide, **do not** force CSA — go Python+REST overlay instead. |
| **ServiceNow CIS (ITSM / ITOM / AI & Virtual Agent)** | Official **$450**. Several CIS now require **CIS-DF (Data Foundation)** first (2026 change). | 4–8 weeks per CIS after CSA | PepsiCo Now Assist JD: **CIS – AI & Virtual Agent**. ITOM SME JDs: CIS-ITOM mandatory. | High for SN specialists; irrelevant for Python GenAI IC. | **Only after CSA**, and only if targeting SN AI roles. |

### Learning certificates (not proctored vendor exams)

| Program | Cost | Time | JD mentions | Honest signal | ROI |
|---|---|---|---|---|---|
| **DeepLearning.AI** short courses (LangChain, LangGraph, RAG) | Coursera sub ~₹4–5k/mo or free audit | Hours to days each | Almost never as a *requirement*. SuperSourcing: “widely held. Signal learning investment, **not production delivery**.” | Fine as study. Weak as resume headline. | **Use as labs. Do not list 8 certificates.** https://www.deeplearning.ai/courses |
| **Hugging Face Agents Course** | **Free.** Certificate: Unit 1 + 80% quiz (fundamentals) or full course + GAIA ≥30% (completion). https://huggingface.co/learn/agents-course/unit0/introduction | 2–6 weeks | HuggingFace **as a library** is in 23% of 313 JDs and Naukri **333** HF jobs. The *course certificate* is not what those JDs ask. | Community-respected for agents; still not production proof. | **Do the course. Ship the agent to the Hub. Put the Space URL on the resume, not the PDF.** |
| **LangChain Academy / LangChain Certified Agent Engineer** | Academy free–paid; **Certified Agent Engineer announced ~Jul 2026** (LangChain YouTube 20 Jul 2026) https://www.youtube.com/watch?v=sFfhQLqXVmM | Unknown exam load | LangChain the *framework* is in 42% of AI Eng JDs. **Insufficient reliable evidence (N≈0 public India JDs requiring “LangChain Certified Agent Engineer” as of Aug 2026).** | Too new. | **Do Academy modules that feed the repo. Do not wait on / pay for the cert unless a JD names it.** |
| **Prompt-only certificates** (any vendor) | ₹2k–40k | Days | “Prompt engineering” as a *skill* is in **33%** of 313 JDs. “Prompt Engineer” as a *title* is shrinking (Masai 29 Jul 2026; Dheya May 2026; OwnYourCareer 7 Jul 2026). | Hiring managers treat prompt-only badges as 2023 residue. | **Do not buy.** Practice prompting *inside* RAG/agents. |

### Kubernetes

| Cert | Cost | Time | JD mentions in GenAI | ROI |
|---|---|---|---|---|
| **CKA** | **$445 USD** (Linux Foundation 2026, includes one retake) ≈ **₹36,000–42,000** | 8–12 weeks of labs | K8s in **23%** of 313 AI Eng JDs — as Docker/K8s *skills*, almost never “CKA required.” | **Low for 90-day GenAI pivot.** OwnYourCareer: CKA helps MLOps/platform more than “AI engineer” title inflation. JobRoadmaps 2026: experience > CKA; early-career should ship projects first. |

### Community verdict that is consistent across independent sources

> “The honest answer: no certification verifies production GenAI delivery. GitHub portfolios and interview-based production scenario questions are the only reliable verification methods.”  
> — SuperSourcing, 2 Jun 2026, https://supersourcing.com/blog/hiring-genai-llm-engineers-india/

> “If the posting does not name the cert, it is optional… a 40-hour cert that blocks a shipped eval is a net loss.”  
> — OwnYourCareer, 15 Aug 2026, https://www.ownyourcareer.in/blog/ai-certifications-india-2026-worth-it

**RECOMMENDATION (90-day cert spend cap):** ₹0–₹20,000. Preferred order if employer will not pay: (1) nothing until repo v1; (2) **AI-103** if Azure JDs dominate your saved list; (3) **AIF-C01** only as a cheap Bedrock keyword; (4) **CSA** only if Door 2 is ServiceNow. Everything else is a Q4 decision.

---

## Portfolio project specifications (evidence-backed, detailed enough to build)

### Why these shapes (not “chat with PDF”)

Take-home analysis of 100+ candidate GitHub submissions (Q4 2025 / Q1 2026) in alexeygrigorev/ai-engineering-field-guide: **RAG systems 40%+**, **agentic systems 30%+**. SuperSourcing’s employer checklist: RAG with chunking (not a quickstart), eval framework, FastAPI + streaming + cost tracking, agent workflows with error recovery.

Sources:  
https://github.com/alexeygrigorev/ai-engineering-field-guide/blob/main/interview/03-get-hired.md  
https://raw.githubusercontent.com/alexeygrigorev/ai-engineering-field-guide/main/interview/questions/06-home-assignments.md  
https://supersourcing.com/blog/hiring-genai-llm-engineers-india/

**RECOMMENDATION:** Build **two deep repos** plus **one eval/cost sidecar**, not five tutorial clones. Domain = IT operations. That is the anti-clone.

---

### Project 1 — Incident Copilot (RAG on tickets + runbooks + KB)

**Why interviews:** RAG is in 48% of AI Eng JDs; ITSM is your domain; SuperSourcing explicitly wants chunking + retrieval logic + eval.

| Item | Spec |
|---|---|
| **Problem** | Given a new incident (short description + work notes), retrieve similar historical incidents, matching KB/runbook steps, and draft: (a) customer-safe summary, (b) likely CI/assignment group, (c) next diagnostic steps, (d) citations. Must say “insufficient evidence” when retrieval is weak. |
| **Stack** | Python 3.12, FastAPI, LangChain or raw SDK, embeddings (`text-embedding-3-large` **or** Azure OpenAI embedding **or** `bge-m3` local), **Chroma or FAISS locally** (Pinecone only if you want the keyword; local is cheaper and more honest), hybrid retrieval (BM25 + vector), optional reranker (`bge-reranker`), Streamlit or simple React for demo. |
| **Data** | **Do not use real client tickets.** Synthesize 200–500 incidents from public post-mortems + ITIL-style templates (P1 network, disk, AD lockout, app 5xx, batch job fail). Include messy text, HTML, duplicates, wrong categories. |
| **Complexity (8.5 YOE bar)** | Chunking experiments (200/500/1000 tokens, sentence vs recursive); metadata filters (CI class, assignment group, severity); hybrid search; citation offsets; PII redaction; latency budget p95 < 3s on CPU for retrieval. |
| **Eval (non-negotiable)** | Golden set of 50 questions. Metrics: Recall@5, citation precision, faithfulness (LLM-as-judge **and** a rule: every claim maps to a chunk id), “I don’t know” accuracy. Log to a CSV + one chart in README. |
| **Ops overlay** | Cost per query (tokens). Prompt/version in git. Refusal on empty retrieval. |
| **Complexity vs clone** | Clones: “upload PDF, ask question.” You: ticket-shaped data, routing metadata, explicit don’t-know, eval table. |

**Interview talking points:** Why hybrid search beat dense-only on short incident titles; why 200-token chunks failed on runbooks; how you measured hallucination.

---

### Project 2 — Agentic runbook executor (human-in-the-loop)

**Why interviews:** Agentic 43% of AI Eng JDs; Infosys wants “simple agent flows and routing”; Optum/Cognizant want tool use; NTT wants auto-healing *governed* by ServiceNow change.

| Item | Spec |
|---|---|
| **Problem** | Agent reads an alert (CPU, disk, failed job). Plans checks. Calls **tools** (mock: `get_metrics`, `get_recent_changes`, `search_kb`, `draft_incident`). Stops for human approval before `restart_service` or `open_change`. Writes a timeline. |
| **Stack** | **LangGraph** (state machine, not a hidden chain), tool functions with Pydantic schemas, FastAPI webhook that accepts a mock alert JSON, optional **MCP server** exposing the same tools (Optum/Atos keyword). Docker Compose: api + redis for checkpointing. |
| **Complexity** | Explicit graph: `triage → retrieve → plan → tool_loop → approval → act → summarize`. Timeouts, retries, max-step cap (prevent loops — a common interview trap). Structured logs (JSON) for each node. |
| **Eval** | 20 scripted alerts. Score: correct tool chosen, no unauthorized restart, loop does not exceed N steps, summary contains evidence. |
| **Anti-clone** | Clones: CrewAI “researcher + writer.” You: **approval node**, **idempotent tools**, **failure injection** (tool returns 500), circuit breaker. |

---

### Project 3 — ServiceNow-shaped integration (REST, not a SN plugin unless you have a PDI)

**Why interviews:** Cognizant SN Expert Agentic AI (REST & IntegrationHub); PepsiCo REST; TCS AI Operations Engineer.

| Item | Spec |
|---|---|
| **Problem** | From a natural-language request (“user locked out in Coimbatore site, VIP”), create a **normalized incident payload**, match a catalog item, and **post to a mock ServiceNow Table API**. Round-trip: poll until state changes, summarize for the user. |
| **Stack** | FastAPI, `httpx`, OpenAPI of a **WireMock / Prism mock** of `/api/now/table/incident`. LLM only for NLU → JSON schema (Instructor/Pydantic). Auth: OAuth client-credentials against the mock. |
| **Complexity** | JSON schema strictness (assignment_group, cmdb_ci, impact/urgency). Replay of failed posts. Idempotency key. Never send PII to a public LLM — show a redaction step. |
| **Anti-clone** | No SN instance required. You prove you understand **ITSM data model + API contracts**, which SN-only course-takers often cannot explain. |

If you **do** have a ServiceNow PDI: add Now Assist-style **incident summarization** *inside* the PDI and document upgrade-safe vs custom. That is Door 2 gold.

---

### Project 4 — Log / major-incident summarizer

**Why interviews:** UnitedHealth lists Splunk/Log Analytics next to LangGraph; AIOps JDs want noise reduction and MTTR.

| Item | Spec |
|---|---|
| **Problem** | Ingest 10k lines of mixed logs (app + Windows Event + syslog). Cluster, extract entities (host, error code), produce a bridge-ready timeline and a customer-safe status. |
| **Stack** | Python, sliding-window map-reduce summarization (fit context window), optional Splunk-like mock, eval against a human timeline. |
| **Complexity** | Token budget; hierarchical summary; do not invent root cause (faithfulness). |
| **Anti-clone** | Use **real public incident logs** (e.g. anonymized open-source outage postmortems) and show before/after token cost. |

---

### Project 5 — Eval harness + cost dashboard (the senior signal)

**Why interviews:** SuperSourcing GitHub audit looks for RAGAS/custom eval; Infosys wants latency/token/cost; resumegyani.in (2026 hiring-manager pattern): “eval discipline is the new senior signal.”

| Item | Spec |
|---|---|
| **Problem** | A CLI + small dashboard that runs Project 1’s golden set on every prompt/model change. Tracks faithfulness, latency, USD/INR cost, regression vs last git SHA. |
| **Stack** | `pytest` or a tiny runner, pandas, Streamlit, optional LangSmith/Langfuse **self-hosted** or CSV-only (do not make the project depend on a paid SaaS). |
| **Anti-clone** | Almost no bootcamp repos have **CI that fails the build when faithfulness drops**. Put that in GitHub Actions. |

---

### Project 6 — On-call assistant (PagerDuty-shaped)

| Item | Spec |
|---|---|
| **Problem** | Given an alert + last 10 related incidents, draft: page or not, who, runbook link, silence window. Human must confirm page. |
| **Stack** | LangGraph + mock PagerDuty Events API. Quiet-hours policy as config, not prompt. |
| **Anti-clone** | Policy-as-code for paging; show a case where the LLM wanted to page and policy blocked it. |

### What **not** to build

- “ChatGPT clone” UI.
- Fine-tune Llama on Alpaca unless a JD is ML-training.
- Computer vision / Stable Diffusion.
- Kaggle Titanic.
- Multi-agent “startup CEO + intern” CrewAI demo with no tools.

---

## Proof-of-work anti-clone guidance

### What hiring sides say they check

**VERIFIED / COMMUNITY (employer-side, Jun 2026):** SuperSourcing tells India hiring teams to inspect GitHub *before* scheduling: RAG with chunking (not LangChain quickstart), eval scripts, FastAPI with streaming/cost/error handling, agent error recovery. “If they cannot share any evidence of production work, they have not done production work.”  
https://supersourcing.com/blog/hiring-genai-llm-engineers-india/

**COMMUNITY:** “A polished demo of 1 deep project consistently outperforms a portfolio of 5 tutorial-clone projects.” Archer Infotech (Pune, Mar 2026) https://archerinfotech.in/blog/how-to-build-an-ai-portfolio-that-gets-interview-calls

**COMMUNITY:** Agentic portfolios that are “basic conversational bots” get filtered; eval pipeline repo is a senior signal. https://productleadersdayindia.org/blogs/ai-engineering-jobs-skills/agentic-ai-engineer-github-portfolio.html

**VERIFIED FACT (JD):** Anlage Infotech 6–10 YOE: real LLM/RAG project experience only. https://www.naukri.com/job-listings-senior-genai-engineer-python-rag-llm-agentic-ai-anlage-infotech-bengaluru-mumbai-all-areas-6-to-10-years-190626021342

### Anti-clone checklist (put in every README)

1. **Problem is ops-specific** — incident, runbook, on-call, ITSM API — not “chat with any PDF.”  
2. **Data card** — synthetic vs public; no client data; PII policy.  
3. **Architecture diagram** — ingest → retrieve → generate → eval.  
4. **Ablation table** — chunk size / hybrid vs dense / with vs without rerank. **Numbers.**  
5. **Failure gallery** — 3 queries the system gets wrong, and what you did.  
6. **Cost & latency** — p50/p95, $/1k queries, model names + dates.  
7. **How to run** — `docker compose up`, `.env.example`, one curl.  
8. **What is not production** — auth, multi-tenancy, SSO — list gaps honestly.  
9. **Git history** — more than one commit; issues or CHANGELOG for eval regressions.  
10. **60–90 second demo** — unlisted YouTube or Loom; show a miss, not only a hit.

### Fork test

If a recruiter can match your repo to a LangChain blog post in 30 seconds, it is a clone. Change: domain data, eval, HITL, cost, and an integration (mock SN/PagerDuty).

---

## GitHub / LinkedIn / blog / demo norms (India hiring)

### GitHub

| Norm | Evidence | What to do |
|---|---|---|
| URL on **line 2 of resume** | resumegyani.in 2026 hiring-manager notes; SuperSourcing pre-screen | Pin 2–3 repos. Un-pin course dumps. |
| README > stars | Community + SuperSourcing | Stars are weak in India services hiring; **runnable** beats 200 stars of a tutorial. |
| Public > private | SuperSourcing | If IP-blocked, write a public **reimplementation on synthetic data** + a one-pager of “production constraints I cannot show.” |
| Languages | 83% Python JDs | Repo language = Python. |

**COMMUNITY counter-signal:** A 2026 fresher on r/developersIndia with deployed LangGraph RAG still reported 300+ applications and silence. Portfolio is necessary, **not sufficient**, without positioning, YOE match, and outreach. Do not cargo-cult “GitHub is enough.” https://www.reddit.com/r/developersIndia/comments/1ubjoph/built_and_shipped_real_genai_inference_projects/

### LinkedIn / Naukri

| Norm | Evidence |
|---|---|
| Headline with **exact JD tokens**: Python, RAG, LangChain, Azure OpenAI / Bedrock, ITSM | ATS Resume Checker blog (Apr 2026): Naukri ranks higher when GenAI + LangChain + Python are in headline **and** key skills. https://www.atsresumeschecker.com/blog/ai-genai-skills-resume-india-2026 |
| Boolean strings recruiters use | SuperSourcing published them: `"RAG" AND ("LangChain" OR "LlamaIndex") AND ("production" OR "deployed")`; `("LangGraph" OR "AutoGen" OR "CrewAI") AND ("production" OR "enterprise") AND "India"` |
| Naukri **and** LinkedIn | Services hiring still runs on Naukri; GCC/product on LinkedIn. Dual-update. |
| About section = Door 2 thesis | “Service Desk Lead (8.5 YOE) building LLM copilots for incident/KB deflection — Python, RAG, LangGraph, Azure OpenAI.” |

letsinterview.me: **median ~100 applicants** per AI Engineer listing; 3% remote; Bengaluru 26% of the 313. Coimbatore candidates should expect **hybrid metro** or US-shift (Cyclotron JD: 2 PM–11 PM IST). Do not filter yourself out of hybrid Bengaluru/Chennai/Hyderabad if the jump is ₹11 LPA → ₹18–28 LPA.

### Blog vs LinkedIn posts

**INFERENCE:** India services recruiters rarely read a personal blog. They read LinkedIn. One architecture post with your eval table is higher ROI than a 10-post blog. GitHub README is the blog.

### Demo

Field-guide: some companies ask for portfolio up front; best take-homes include a Loom. Have a **running** demo (HF Space / Azure Container Apps / localhost Docker) plus a **video** for when the Space is cold.

---

## English + stakeholder comms as a differentiator for leads

### Evidence that comms are screened

**VERIFIED FACT (JDs):**  
- Relevance Labs “Gen AI – Python Engineer”: **“Excellent Communication skills.”** https://in.indeed.com/viewjob?jk=e56600c037b2516b  
- Cyclotron AI Engineer (6+ YOE, ₹30–45 LPA, 2 PM–11 PM IST): US-shift implies spoken English with US stakeholders. https://www.naukri.com/job-listings-artificial-intelligence-engineer-cyclotron-pune-5-to-10-years-231225026439  
- NTT Data AI/GenAI Lead: strategy + govern automation use cases across domains — a comms job, not a notebook job.  
- Atos SN AI engineer: “working closely with international stakeholders.”

**COMMUNITY / INDUSTRY:** Michael Page 2026 tech-trends piece: with AI doing more routine work, **soft skills become the differentiator** — explain the “why,” influence, translate complexity. https://www.linkedin.com/pulse/6-technology-trends-define-careers-2026-michael-page-wu1oe

Masai School (Jun 2026, training-side — treat as secondary): hiring managers value “measurable impact, reliable safeguards, **work well across teams**.” https://www.masaischool.com/blog/what-is-agentic-ai-and-why-is-it-the-most-in-demand-skill-in-indias-job-market-right-now/

### What this does **not** prove

**Insufficient reliable evidence (N=0 controlled studies)** that “excellent English” *alone* shortlists a Service Desk Lead into GenAI IC roles. Layer B (313 JDs) is skill-token heavy; comms are generic bullets.

**INFERENCE:** Comms are a **gate for lead / FDE / consulting / US-shift** and a **tie-breaker** for IC. They are not a substitute for Python+RAG.

### How to convert Service Desk Lead comms into AI-lead evidence

| Ops behaviour you already have | Phrase on resume / interview |
|---|---|
| Major-incident bridge | “Facilitated cross-tower RCA; can specify eval labels with ops SMEs” |
| VIP / business stakeholder updates | “Drafted customer-safe status — same skill as grounding LLM output to approved language” |
| Shift handovers | “Structured context passing — analogous to agent state / memory” |
| Vendor calls (Microsoft, SN, Splunk) | “Can translate vendor AI features (Now Assist, Azure OpenAI) into deflection/MTTR bets” |

**RECOMMENDATION:** Record the 90-second demo **in English**. One LinkedIn post walking a P1 timeline → copilot output. That is the comms artifact.

---

## Time-wasters with evidence

| Time-waster | Evidence of low ROI for *this* target | What to do instead |
|---|---|---|
| **“Become a data scientist in 6 months” / classical ML bootcamps** | 313 AI Eng JDs: RAG 48%, agents 43%, vs NLP 18%, transformers-as-concept 16%. LogicMojo (affiliate-adjacent — use only as a corroborating *job-posting* claim): they cite 73% of AI postings mentioning LLMs/GenAI vs 22% traditional ML as primary. | Applied RAG + agents. |
| **TensorFlow / training nets from scratch** | Still in **28%** of 313 JDs — **not zero**. But Infosys Bedrock JD and most LangChain JDs do not ask you to implement backprop. KodeKloud 2026: research roles need math; **LLM application roles need conceptual + software skills.** https://kodekloud.com/blog/ai-interview-questions/ | Learn what a transformer *does* (tokens, context window, embeddings). Skip writing TF graphs. |
| **Java Spring as a pivot** | Java in **12%** of 313 AI Eng JDs. Profile constraint: no Java-first. UnitedHealth lists Spring AI as *an* option beside LangChain — not a reason to learn Spring. | Python. |
| **Heavy SQL / warehouse analytics / Snowflake-first** | SQL 20% of 313 — working knowledge. Snowflake Cortex is niche. Profile constraint. | Enough SQL to read incident tables and pgvector. |
| **Kaggle-only portfolio** | SuperSourcing and OwnYourCareer: production scenario + GitHub app, not notebooks. Kaggle can support *eval literacy* but does not show FastAPI, auth, cost, ITSM. | One Kaggle metric in an appendix is fine; do not lead with it. |
| **Prompt-engineer-only certs / “Prompt Engineer” headline** | Dheya (May 2026): standalone prompt role largely gone in India. Masai (Jul 2026): title disappeared; skill remains inside GenAI engineer. OwnYourCareer (Jul 2026): agentic/orchestration mandates +180–260% YoY (staffing-report claim — treat as **COMMUNITY/secondary**, not a census). Recrew.ai: Prompt Engineer posts ~40% down since 2023. | Prompting as a **subsection** of RAG/agents. Headline = GenAI / AIOps automation, not Prompt Engineer. |
| **CKA in the first 90 days** | K8s 23% of AI Eng JDs; CKA almost never required for GenAI IC. $445 + 8–12 weeks steals repo time. | Docker Compose on the project. |
| **AZ-104 / AZ-400 before a repo** | Admin/DevOps exams do not pass Anlage’s “real LLM/RAG project” filter. | AI-103 *after* Azure OpenAI demo, or skip. |
| **Collecting all three clouds** | OwnYourCareer: looks like panic. | One cloud. |
| **MLS-C01** | **Retired 31 Mar 2026.** Official AWS. | MLA-C01 or AIF-C01 only if AWS lane. |
| **AI-102 study guides published before spring 2026** | Exam retired 30 Jun 2026. Successor AI-103 is Foundry + agents. | AI-103 guide only. |
| **Fine-tuning-first** | Interview Qs on Azure/GCP (Cloud Soft Solutions, Aug 2026): if business wants to fine-tune on 300 PDFs, **push back, propose RAG.** | RAG + eval first. LoRA later if a JD is ML-heavy. |
| **n8n/Zapier as the whole career** | n8n Naukri ~203 (Jan 2026). Real but small. Visual automation without Python caps Door 1. | Use n8n as a **week-2 demo**, then reimplement the critical path in Python. |
| **Paid “job guarantee” GenAI courses as the plan** | SuperSourcing + OwnYourCareer: artefact > certificate. Affiliate “90% placed” claims are not used here. | Official docs + one repo. |

---

## 90-day sequence (INFERENCE)

Label: **INFERENCE**, sequenced from JD frequency (Layer B) + Door 2 domain (Layer C) + cert ROI (vendor pages). Assumes ~12–15 hours/week on top of a full-time Service Desk Lead job.

### Design principle

Frequency order in 313 AI Eng JDs: **Python (83) → Azure/AWS (49/45) → RAG (48) → Agents (43) → LangChain (42) → CI/CD/Docker (~30) → embeddings (31) → FastAPI (22) → K8s (23) → LlamaIndex (15) → CrewAI (11).**  
Do the left side of that list first. Put **ITSM content** in every artifact.

### Days 1–21 — Python bar + one LLM API (blocking skills)

- Python: functions, OOP, venv, typing, pytest, FastAPI hello + one POST.  
- GitHub repo skeleton with CI (ruff + pytest).  
- Call **Azure OpenAI** *or* OpenAI *or* Bedrock (pick Azure unless the account is AWS). Log tokens.  
- Write 20 synthetic incidents.  
- **Deliverable:** `GET /health` + `POST /summarize` that summarizes an incident paragraph with a system prompt. README with cost of 20 calls.  
- **Cert:** none. Optional: skim AI-103 skills outline so Azure vocabulary matches.  
https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103

### Days 22–50 — RAG (the 48% skill) on ops data

- Chunking + embeddings + Chroma/FAISS.  
- Hybrid retrieval. Citations. Don’t-know.  
- Golden set n=50. First eval table.  
- **Deliverable:** Project 1 v1 deployed (Docker). LinkedIn post with the eval table (no client data).  
- Update Naukri headline: `IT Ops Lead | Python | RAG | Azure OpenAI | ITSM automation`.

### Days 51–75 — Agent + tool calling + mock ITSM (the 43% skill)

- LangGraph graph with tools and HITL approval.  
- Mock ServiceNow Table API.  
- Optional: thin MCP wrapper (Optum/Atos keyword — 2–3 days, not a rewrite).  
- **Deliverable:** Project 2 + 3 in one repo or two tightly linked repos. Demo video in English.

### Days 76–90 — Eval/cost, applications, one exam *or* CSA decision

- GitHub Action fails on eval regression (Project 5 minimum viable).  
- Save **15 JDs**. Count Azure vs AWS vs SN vs pure Python.  
- **If ≥5 Azure GenAI JDs:** book **AI-103** (or schedule for day 100).  
- **If ≥5 SN AI JDs and you can use a PDI:** start **CSA** on-demand (free training).  
- **If Infosys-like Bedrock JDs dominate:** AIF-C01 in a weekend *after* a Bedrock Knowledge Base lab.  
- Apply 15 roles. Tailor first 10 lines to each JD’s exact tokens (`Retrieval-Augmented Generation` not only `RAG`).  
- **Do not** start CKA, AZ-104, LoRA, or a second cloud.

### What “done” looks like on day 90

| Artifact | Pass criteria |
|---|---|
| GitHub | 2 runnable repos, Docker, eval numbers, failure gallery |
| Resume | Python, RAG, LangGraph, Azure OpenAI/Bedrock, ITSM, Git, FastAPI — all backed by bullets with metrics |
| Naukri/LinkedIn | Headline + skills match Boolean strings |
| Cert | 0 or 1, matching the saved JD cloud |
| Outreach | 15 applications + 10 hiring-manager/recruiter notes pointing at **one** repo URL |

---

## Tools vs theory: how much ML math is actually asked

### Applied GenAI / LLM Engineer interviews

**VERIFIED FACT (interview-guide synthesis, 2026):** CalibreOS GenAI Engineer Interview Guide: do **not** treat this as an ML research interview. Emphasis is RAG architecture, agent design, serving, evaluation, cost — “not deriving attention from first principles.”  
https://www.calibreos.com/blog/genai-engineer-interview-guide-2026

Exponent / Sierra-style questions: “Explain how RAG works”; tokenizer vs cost; embeddings and similarity; context window; temperature; RAG vs fine-tune vs prompt.  
https://www.tryexponent.com/blog/ai-engineer-interview-questions/

KodeKloud (Jun 2026): “For research and core ML roles, yes: linear algebra, probability, and calculus. For many AI application and engineering roles built on LLMs, conceptual understanding plus strong software skills matter more than deriving backprop by hand.”  
https://kodekloud.com/blog/ai-interview-questions/

Azure/GCP interview banks (Cloud Soft Solutions, Aug 2026) used in India prep circles: RAG vs fine-tune stakeholder pushback; hybrid search; citations; identity-trimmed retrieval — **systems and product judgment**, not SVD proofs.  
https://cloudsoftsol.com/blog/azure-ai-interview-questions-answers/

**INFERENCE for Manoj:** You need to **explain** embeddings as vectors and cosine similarity, what “top-k” means, why chunk overlap exists, what temperature does, and why RAG is preferred for changing private data. You do **not** need to derive the transformer.

### ML Engineer / research / “AI/ML Engineer” with PyTorch as primary

letsinterview.me: PyTorch 30%, TF 28%, fine-tuning 37% — these listings are a **mix**. Some are applied GenAI with leftover ML keywords; some are real training jobs.

xAI / lab-style MLE loops still ask transformer math, loss functions, optimization (Dataford xAI guide, Aug 2026). **Out of scope** for this profile.

Happiest Minds “Senior Scientist – ML” style JDs list linear algebra, calculus, statistics alongside Docker/K8s. That is a different job.

### Practical study split (RECOMMENDATION)

| Topic | Applied GenAI JD | ML Engineer JD |
|---|---|---|
| Linear algebra (beyond “dot product = similarity”) | Skip | Required |
| Backprop, vanishing gradients | Skip | Required |
| Tokenization, context window, KV cache (conceptual) | Yes | Yes |
| Chunking, hybrid search, rerank, RAG eval | **Core** | Sometimes |
| Tool calling, graphs, HITL, MCP | **Core in 2026** | Rare |
| LoRA/QLoRA | Optional | Often |
| CUDA, distributed training | Skip | Often |

If a JD’s **first six bullets** are PyTorch, CUDA, research papers — **do not apply** as an ops-to-applied switcher. If they are Python, RAG, LangChain, FastAPI, Azure OpenAI — apply.

---

## Evidence gaps

| Gap | Why it matters | What we did instead |
|---|---|---|
| Naukri keyword inflation | Absolute N for Python, Datadog, MCP, “open ai” are not GenAI job counts | Used 313-JD **percentages** for mix; used Naukri N only as relative volume with URLs |
| letsinterview.me is Feb 2026 | LangGraph, MCP, AI-103, Bedrock-must-have Infosys JDs are stronger by Aug 2026 than Feb mix shows | Layered Aug 2026 individual JDs on top; labelled LangGraph as rising |
| No public Naukri API dump for Aug 2026 skill × experience band (6–10 YOE) | 8.5 YOE filter is inferred from named JDs in that band | Cited 6–10 / 6–11 / 7–13 YOE JDs explicitly |
| Cert → interview conversion | **Insufficient reliable evidence (N=0 longitudinal India studies)** that AI-103 or AIF-C01 caused a shortlist independent of projects | Used JD *mentions* + hiring-manager “GitHub > cert” comments; recommended certs only as ATS unlocks |
| Hugging Face / LangChain / DL.AI certificates | Almost no JDs require the *certificate* | Treated as study paths; proof = Hub Space / repo |
| English as differentiator | No India hiring dataset isolates English scores for GenAI IC | Used JD “excellent communication” + US-shift + lead-role JDs; did not claim it replaces Python |
| Coimbatore-specific GenAI hiring | One AIOps JD listed Coimbatore; most GenAI volume is BLR/HYD/Pune/NCR | Flag metro hybrid / US-shift as likely |
| ServiceNow Now Assist vs Python LangChain overlap | Few JDs want both; they are two labour markets | Dual-door strategy; do not assume SN CSA gets you Infosys Bedrock roles |
| n8n Aug 2026 Naukri N | Last clean snapshot was Jan 2026 (203) | Treated n8n as niche; LinkedIn JDs confirm it exists |
| “Agentic jobs up 220%” staffing headlines | TeamLease/Quess/ET figures circulated via blogs; **not independently re-counted here** | Used as COMMUNITY; relied on Naukri Agentic AI **9,938** as a hard page count instead |
| Salary impact of each cert | Vendor blogs claim +20–30%; those are not causal | **Not used** as ROI. ROI = “would this JD have rejected you without the badge?” |

---

## Source appendix

### Skill-mix and job-board snapshots

- letsinterview.me, 313 LinkedIn India AI Engineer JDs, 25 Feb 2026 — https://www.letsinterview.me/blog/ai-engineer-jobs-india-2026  
- Naukri LangChain — https://www.naukri.com/langchain-jobs (4,122, Aug 2026)  
- Naukri RAG — https://www.naukri.com/rag-jobs (6,876)  
- Naukri Retrieval Augmented Generation — https://www.naukri.com/retrieval-augmented-generation-jobs (3,241)  
- Naukri GenAI — https://www.naukri.com/genai-jobs (7,887)  
- Naukri Agentic AI — https://www.naukri.com/agentic-ai-jobs (9,938)  
- Naukri FastAPI — https://www.naukri.com/fastapi-jobs (3,238)  
- Naukri OpenAI — https://www.naukri.com/openai-jobs (3,566–3,801)  
- Naukri Hugging Face — https://www.naukri.com/huggingface-jobs (333)  
- Naukri AIOps — https://www.naukri.com/aiops-jobs (558–680)  
- Naukri Bedrock — https://www.naukri.com/bedrock-jobs (1,507)  
- Naukri LlamaIndex — https://www.naukri.com/llamaindex-jobs (841, Feb 2026 snapshot)  
- Naukri n8n — https://www.naukri.com/n8n-jobs (203, Jan 2026 snapshot)  
- Naukri Docker — https://www.naukri.com/docker-jobs (47,986, all IT)  
- Naukri Kubernetes — https://www.naukri.com/kubernetes-jobs (25,624–26,059, all IT)  
- Naukri Terraform — https://www.naukri.com/terraform-jobs (20,289, all IT)  
- Naukri Azure — https://www.naukri.com/azure-jobs (43,557–48,111, all Azure)  
- Naukri ServiceNow Developer — https://www.naukri.com/servicenow-developer-jobs (5,983)  
- Naukri Splunk — https://www.naukri.com/splunk-jobs (8,531)  
- Naukri ITIL ServiceNow — https://www.naukri.com/itil-servicenow-jobs (5,706, Jul 2026)  
- Glassdoor India LangGraph — https://www.glassdoor.co.in/Job/india-langgraph-jobs-SRCH_IL.0,5_IN115_KO6,15.htm (1,675, Aug 2026)  
- hirist LangGraph — https://www.hirist.tech/k/langgraph-jobs (440)  
- Foundit LangChain+LangGraph India — https://www.foundit.in/search/langchain-langgraph-jobs (510, 23 Aug 2026)

### Individual JDs (must-have language)

- Infosys GenAI / Agentic AI Engineer — https://in.linkedin.com/jobs/view/genai-agentic-ai-engineer-at-infosys-4416389669 ; https://www.glassdoor.co.in/job-listing/genai-agentic-ai-engineer-infosys-JV_KO0,25_KE26,33.htm?jl=1010157961831  
- Cognizant AI Engineer Python LangChain LangGraph 7–13 YOE — https://in.linkedin.com/jobs/view/ai-engineer-python-langchain-langgraph-agentic-ai-api-llms-at-cognizant-4415497554  
- Cognizant ServiceNow Expert Agentic AI, Chennai — https://careers.cognizant.com/us-en/jobs/00068415441/servicenow-expert-agentic-ai/  
- Cognizant Service Management CoE — https://www.glassdoor.co.in/job-listing/service-management-experts-cognizant-technology-solutions-JV_IC2865319_KO0,26_KE27,57.htm?jl=1009951210332  
- Optum India LangChain LangGraph MCP — https://in.linkedin.com/jobs/view/ai-ml-engineer-lang-chain-lang-graph-and-mcp-at-optum-india-4388550311  
- UnitedHealth Group Bengaluru AI/ML Engineer LLM/RAG — https://careers.unitedhealthgroup.com/job/bengaluru/ai-or-ml-engineer-llms-rag-langchain-langgraph/34088/99093468144  
- Atos ServiceNow forward deployed AI engineer — https://jobs.atos.net/job/Bangalore-ServiceNow-forward-deployed-AI-engineer/1409487633/  
- PepsiCo Now Assist / AI Search — https://www.bayt.com/en/india/jobs/developer-deex-ai-search-nowassist-servicenow-genai-74303169/  
- NTT Data AI/GenAI Lead Ansible Python ServiceNow — https://careers.services.global.ntt/global/en/job/P-100236/AI-GenAI-Lead-Infrastructure-Automation-Ansible-Python-ServiceNow  
- Anlage Infotech Senior GenAI 6–10 YOE (real RAG only) — https://www.naukri.com/job-listings-senior-genai-engineer-python-rag-llm-agentic-ai-anlage-infotech-bengaluru-mumbai-all-areas-6-to-10-years-190626021342  
- Kezan Consulting Agentic AI FastAPI — https://www.naukri.com/job-listings-sr-developer-python-fast-api-ai-ml-immediate-joiner-kezan-consulting-gurugram-bengaluru-delhi-ncr-3-to-7-years-081225008903  
- Kezan AI/ML Engineer 6–9 YOE RAG/vector — https://www.naukri.com/job-listings-ai-ml-engineer-immediate-joiner-kezan-consulting-gurugram-bengaluru-delhi-ncr-6-to-9-years-081225007236  
- KDK Software GenAI Engineer — https://www.naukri.com/job-listings-genai-engineer-llm-python-rag-langchain-ai-integration-kdk-software-jaipur-3-to-8-years-180726014409  
- Staffnix Senior Python Backend GenAI — https://in.linkedin.com/jobs/view/senior-python-backend-engineer-genai-llm-langchain-langgraph-rag-fastapi-postgresql-agentic-ai-at-staffnix-4433490913  
- McLaren Strategic GenAI RAG 8–12 YOE Bangalore — https://www.hirist.tech/j/mclaren-strategic-solutions-generative-ai-developer-rag-pipelines-1625811  
- Emerson Generative AI Developer 7–10 YOE — https://www.hirist.tech/j/emerson-generative-ai-developer-artificial-intelligence-machine-learning-1583983  
- HashedIn by Deloitte Python / Generative AI Expert — https://in.linkedin.com/jobs/view/python-generative-ai-expert-at-hashedin-by-deloitte-4393549549  
- ZK Technologies AI Engineer Python Azure AI (AI-102 required) — https://in.linkedin.com/jobs/view/ai-engineer-python-azure-ai-at-zk-technologies-4432952119  
- Cyclotron AI Engineer Azure — https://www.naukri.com/job-listings-artificial-intelligence-engineer-cyclotron-pune-5-to-10-years-231225026439  
- Relevance Labs GenAI Python — https://in.indeed.com/viewjob?jk=e56600c037b2516b  
- Sandisk Senior AI Developer LangGraph 8–11 YOE — https://in.linkedin.com/jobs/view/senior-ai-developer-langgraph-ai-agents-with-8-to-11-years-at-sandisk-4404089765  
- TCS AI Operations Engineer (Foundit, closed) — https://www.foundit.in/job/itsm-cmdb-spm-irm-tprm-gen-ai-rpa-agentic-ai-tata-consultancy-services-bengaluru-bangalore-44223355  
- AT&T IAM Operations AIOps Bengaluru — https://www.att.jobs/job/bengaluru/sr-specialist-cybersecurity-iam-operations-aiops/117/91583646528  
- Welkin Soft Agentic AI + n8n — https://in.linkedin.com/jobs/view/agentic-ai-and-genai-engineer-with-n8n-expertise-at-welkin-soft-tech-pvt-ltd-4405751777  
- Infosys Python Developer GenAI LLM RAG 3–5 YOE — https://www.naukri.com/job-listings-python-developer-genai-llm-rag-infosys-hyderabad-pune-bengaluru-3-to-5-years-110826000068

### Hiring-manager / recruiter commentary

- SuperSourcing, Hiring GenAI & LLM Engineers from India, 2 Jun 2026 — https://supersourcing.com/blog/hiring-genai-llm-engineers-india/  
- OwnYourCareer, AI Certifications India 2026 Worth It?, 15 Aug 2026 — https://www.ownyourcareer.in/blog/ai-certifications-india-2026-worth-it  
- Masai School, Agentic AI demand, 27 Jun 2026 — https://www.masaischool.com/blog/what-is-agentic-ai-and-why-is-it-the-most-in-demand-skill-in-indias-job-market-right-now/  
- Masai School, Prompt engineering jobs India 2026, 29 Jul 2026 — https://www.masaischool.com/blog/prompt-engineering-jobs-and-salary-india-2026/  
- Dheya, Prompt engineering career India 2026, 8 May 2026 — https://www.dheya.com/insights/prompt-engineering-career-india-2026  
- OwnYourCareer, Prompt engineering dead / agentic, 7 Jul 2026 — https://www.ownyourcareer.in/blog/prompt-engineering-dead-india-2026-agentic-ai-orchestration-jobs  
- Michael Page, 6 technology trends 2026 (soft skills) — https://www.linkedin.com/pulse/6-technology-trends-define-careers-2026-michael-page-wu1oe  
- ATS Resume Checker, AI/GenAI skills resume India 2026, 12 Apr 2026 — https://www.atsresumeschecker.com/blog/ai-genai-skills-resume-india-2026  
- Archer Infotech, AI portfolio that gets calls, 28 Mar 2026 — https://archerinfotech.in/blog/how-to-build-an-ai-portfolio-that-gets-interview-calls  
- MyEngineeringPath, GenAI portfolio guide, Mar 2026 — https://myengineeringpath.dev/genai-engineer/portfolio-guide/  
- alexeygrigorev AI engineering field guide (portfolio + take-homes) — https://github.com/alexeygrigorev/ai-engineering-field-guide/blob/main/interview/03-get-hired.md  
- Take-home patterns — https://raw.githubusercontent.com/alexeygrigorev/ai-engineering-field-guide/main/interview/questions/06-home-assignments.md

### Interview content (tools vs math)

- CalibreOS GenAI Engineer Interview Guide 2026 — https://www.calibreos.com/blog/genai-engineer-interview-guide-2026  
- Exponent, 45+ AI Engineer interview questions, 25 Jun 2026 — https://www.tryexponent.com/blog/ai-engineer-interview-questions/  
- KodeKloud, AI interview questions 2026 — https://kodekloud.com/blog/ai-interview-questions/  
- Cloud Soft Solutions, Azure AI interview Qs, 18 Aug 2026 — https://cloudsoftsol.com/blog/azure-ai-interview-questions-answers/

### Official certification pages

- Microsoft AI-103 credential — https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-apps-and-agents-developer-associate/  
- Microsoft AI-103 study guide — https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103  
- Microsoft Credentials roundup Jun 2026 (AI-102/AI-900 retirement; AI-103/AI-901) — https://techcommunity.microsoft.com/blog/skills-hub-blog/microsoft-credentials-roundup-june-2026/4528350  
- AWS MLS-C01 retirement (official) — https://aws.amazon.com/certification/certified-machine-learning-specialty/  
- Google Cloud Generative AI Leader — https://cloud.google.com/learn/certification/generative-ai-leader  
- Google Professional ML Engineer — https://cloud.google.com/learn/certification/machine-learning-engineer  
- Databricks GenAI Engineer Associate — https://www.databricks.com/learn/certification/genai-engineer-associate  
- ServiceNow University exam fees (CSA $300, CIS $450) — https://learning.servicenow.com/lxp/en/pages/now-learning-knowledge-search?id=kb_article_view&sys_kb_id=fc603dbd47153a9019dfe23c326d43a2  
- ServiceNow 2026 exam process — https://www.servicenow.com/community/training-and-certifications/2026-exam-vouchers-courses-exams-amp-retakes-major-changes/ba-p/3464930  
- Hugging Face Agents Course — https://huggingface.co/learn/agents-course/unit0/introduction  
- DeepLearning.AI courses — https://www.deeplearning.ai/courses  
- LangChain Agent Engineer cert announcement — https://www.youtube.com/watch?v=sFfhQLqXVmM  
- CKA cost (Linux Foundation $445, 2026 blogs) — https://ckaexam.com/blog/cka-certification-cost  
- ITIL 4 Foundation country fees 2026 — https://www.certscope.com/blog/itil-4-foundation-cost-exam-fees-by-country  
- AWS exam fees India 2026 — https://www.examcert.app/blog/aws-certification-cost-india-2026/ ; https://www.findmyguru.com/blog/aws-certification-cost-in-india  
- Azure exam fees India — https://learn.microsoft.com/en-sg/answers/questions/2336967/what-is-the-official-fee-for-azure-certification-e ; https://passitexams.com/articles/microsoft-azure-certification-cost/

### Secondary (used cautiously)

- Coursera Micro-Credentials Impact Report 2025 via BW People (employer survey, not JD scrape) — https://www.bwpeople.in/article/indian-firms-value-skills-over-degrees-finds-survey-555388  
- r/developersIndia fresher GenAI portfolio silence — https://www.reddit.com/r/developersIndia/comments/1ubjoph/built_and_shipped_real_genai_inference_projects/

---

*End of A7. Counts are snapshots; re-open the Naukri URLs before making a spend decision. No cert in this file is a job offer. The conversion asset is a runnable ops-domain RAG + agent repo with eval numbers.*
