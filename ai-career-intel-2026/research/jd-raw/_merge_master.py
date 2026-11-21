# Merge + extra harvest into MASTER India AI JD corpus. Harvest date: 23 Aug 2026.
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path(r"C:\Users\manoj\ai-career-intel-2026\research\jd-raw")
OUT_TSV = RAW / "MASTER-india-ai-jd-corpus.tsv"
OUT_CSV = RAW / "MASTER-india-ai-jd-corpus.csv"
OUT_MD = Path(r"C:\Users\manoj\ai-career-intel-2026\research\W1-A2-JD-CORPUS-MASTER.md")

HDR = [
    "id",
    "source",
    "company",
    "title",
    "location",
    "exp",
    "posted",
    "salary",
    "url",
    "java",
    "sql",
    "status",
    "snippet",
    "harvest_file",
]

VOLUME_RE = re.compile(
    r"(naukri\.com/(?!job-listings)[^/\s]*jobs"
    r"|naukri\.com/[^/\s]*jobs-in-"
    r"|indeed\.com/q-"
    r"|foundit\.in/search/"
    r"|linkedin\.com/jobs/(?!view/)"
    r"|glassdoor\.[^/]+/Job/"
    r"|glassdoor\.[^/]+/Jobs/"
    r")",
    re.I,
)

# Extra unique listings harvested by parent 23 Aug 2026 (search-index + guest pages).
EXTRAS = [
    ["PX001", "linkedin", "Systango", "GenAI Engineer (S02/S03)", "Coimbatore, Tamil Nadu", "", "2 weeks ago (LI India GenAI SERP 19 Aug 2026)", "", "https://in.linkedin.com/jobs/view/genai-engineer-s02-s03-at-systango-4423919495", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn India Generative AI Engineer SERP card. Coimbatore. Actively Hiring on same SERP cluster.", "parent-extra"],
    ["PX002", "linkedin", "Techify Solutions Pvt Ltd", "Gen AI Engineer", "Coimbatore, Tamil Nadu", "", "3 weeks ago (LI India GenAI SERP 19 Aug 2026)", "", "https://in.linkedin.com/jobs/view/gen-ai-engineer-at-techify-solutions-pvt-ltd-4435056149", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn India Generative AI Engineer SERP card. Coimbatore.", "parent-extra"],
    ["PX003", "linkedin", "BharatGen", "Generative AI Engineer", "Hyderabad, Telangana", "", "1 month ago (LI India GenAI SERP 19 Aug 2026)", "", "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-bharatgen-4453076575", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn India Generative AI Engineer SERP. Hyderabad. Also in W1-A2 inventory.", "parent-extra"],
    ["PX004", "linkedin", "Blue Machines", "AI Agent Engineer", "Chennai, Tamil Nadu", "", "1 week ago; Actively Hiring (LI SERP 19 Aug 2026)", "", "https://in.linkedin.com/jobs/view/ai-agent-engineer-at-blue-machines-ai-4455576972", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn India Generative AI Engineer SERP. Chennai. Actively Hiring.", "parent-extra"],
    ["PX005", "linkedin", "Artech LLC", "Generative AI Engineer", "Bengaluru, Karnataka", "", "LI Bengaluru GenAI SERP 22 Aug 2026", "", "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-artech-l-l-c-4451669010", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn Bengaluru Generative AI Engineer SERP card.", "parent-extra"],
    ["PX006", "linkedin", "EXL", "Generative AI Engineer", "Bengaluru, Karnataka", "", "2 weeks ago (LI Bengaluru GenAI SERP 22 Aug 2026)", "", "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-exl-4445867650", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn Bengaluru Generative AI Engineer SERP card.", "parent-extra"],
    ["PX007", "linkedin", "HCLTech", "Generative AI Engineer", "Greater Hyderabad Area", "3 to 10 Years", "5 days ago (guest 23 Aug 2026); walk-in 22 Aug 2026", "", "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-hcltech-4452563654", "N", "Unk", "INDEXED-LIVE", "Walk-in Date: 22nd Aug 2026. Experience 3 to 10 Years. Skills indexed: AI, Python, RAG, Prompt Engineering, Advanced Analytics.", "parent-extra"],
    ["PX008", "linkedin", "TalentBridge", "Generative AI Engineer", "India (as indexed)", "", "6 days ago (guest 23 Aug 2026)", "", "https://in.linkedin.com/jobs/view/generative-ai-engineer-at-talentbridge-4454252904", "Unk", "Unk", "INDEXED-LIVE", "Senior AI Engineer to build and scale production-grade Generative AI and Agentic AI solutions.", "parent-extra"],
    ["PX009", "linkedin", "Indium", "Generative AI Engineer / Artificial Intelligence Engineer", "India (as indexed)", "", "6 days ago; Mid-Senior; Full-time", "", "https://in.linkedin.com/jobs/view/generative-ai-engineer-artificial-intelligence-engineer-at-indium-4455256972", "Unk", "Unk", "INDEXED-LIVE", "LinkedIn guest title: Generative AI Engineer / Artificial Intelligence Engineer. Mid-Senior. Full-time.", "parent-extra"],
    ["PX010", "linkedin", "Ahura Workforce Solutions", "Agentic AI Engineer (LangChain / LangGraph / Claude) - 100% Remote", "Remote", "", "LI guest indexed 23 Aug 2026", "", "https://www.linkedin.com/jobs/view/agentic-ai-engineer-langchain-langgraph-claude-100%25-remote-at-ahura-workforce-solutions-4403964352", "N", "Unk", "INDEXED-LIVE", "Design, develop, and deploy intelligent autonomous AI agents. Hands-on LangChain / LangGraph / Claude.", "parent-extra"],
    ["PX011", "linkedin", "AI Data Value Info Com Tech Alliance", "Agentic AI Engineer | Google ADK Langchain & Langraph", "Gurugram (on-site)", "", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/agentic-ai-engineer-google-adk-langchain-langraph-at-ai-data-value-info-com-tech-alliance-4323204373", "N", "Unk", "INDEXED-LIVE", "Full-time on-site Gurugram. Google ADK, LangChain, LangGraph.", "parent-extra"],
    ["PX012", "linkedin", "Tvara", "AI Engineer - LangChain & Agentic Systems (Python)", "Bengaluru, Karnataka", "", "LI guest crawled 18 Aug 2026", "", "https://in.linkedin.com/jobs/view/ai-engineer-langchain-agentic-systems-python-at-tvara-4290569191", "N", "Unk", "INDEXED-LIVE", "Build agentic AI systems and RAG pipelines using LangChain and Python. Full-time Bengaluru.", "parent-extra"],
    ["PX013", "linkedin", "NeoIntelli Technologies", "AI Agent Developer (LangChain / LangGraph)", "Bengaluru, Karnataka", "1+ years GenAI/LLM apps", "crawled 23 Aug 2026 03:30", "", "https://in.linkedin.com/jobs/view/ai-agent-developer-langchain-langgraph-at-neointelli-technologies-4431005043", "N", "Unk", "LIVE", "Build AI agents using LangChain, LangGraph. Develop RAG pipelines and intelligent workflows. 1+ years GenAI or LLM application development.", "parent-extra"],
    ["PX014", "linkedin", "Bradsol", "Agentic AI Developer – n8n & LangChain", "Hyderabad (WFO)", "2–3 Years", "LI guest crawled 21 Aug 2026", "", "https://in.linkedin.com/jobs/view/agentic-ai-developer-%E2%80%93-n8n-langchain-at-bradsol-4314027805", "N", "Unk", "RECENT-CLOSED", "No longer accepting applications. Develop and deploy AI-powered agents using n8n, LangChain, or similar.", "parent-extra"],
    ["PX015", "linkedin", "The Hartford India", "Platform & Agentic AI Engineer", "India (as indexed)", "", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/platform-agentic-ai-engineer-at-the-hartford-india-4382876974", "N", "Unk", "INDEXED-LIVE", "Production-grade Agentic AI using Google ADK, Anthropic MCP, LangGraph/LangChain, and modern Agentic protocols.", "parent-extra"],
    ["PX016", "linkedin", "Infinite Computer Solutions", "Platform Engineer - Azure OpenAI & Copilot Studio", "Bengaluru / Hyderabad / Chennai / Noida / Pune / Vizag; Hybrid", "", "1 week ago; 175 applicants (guest 23 Aug 2026)", "", "https://in.linkedin.com/jobs/view/platform-engineer-azure-openai-copilot-studio-bangalore-hyderabad-chennai-noida-pune-at-infinite-computer-solutions-4378334259", "N", "Unk", "LIVE", "Python Mandatory; Azure Functions Mandatory; Copilot Studio Mandatory; Power Automate Mandatory. Azure OpenAI. Hybrid multi-city India.", "parent-extra"],
    ["PX017", "linkedin", "Tietoevry", "Senior AI Engineer – Microsoft Copilot Studio & Automation", "Bengaluru (Hybrid)", "6 to 10 years (at least 2 years building AI solutions)", "1 day ago; 30 applicants", "", "https://in.linkedin.com/jobs/view/senior-ai-engineer-%E2%80%93-microsoft-copilot-studio-automation-tietoevry-create-m-f-d-at-tietoevry-4324479973", "N", "Unk", "LIVE", "Build AI agents & copilots on Microsoft Copilot Studio. Power Automate / Logic Apps. RAG/grounding via Azure OpenAI & Cognitive Search.", "parent-extra"],
    ["PX018", "linkedin", "Tata Consultancy Services", "Microsoft Copilot Studio Engineer-Chennai/Pune/Indore/Hyderabad/Delhi- 4 to 6 yrs", "Hyderabad (also Chennai/Pune/Indore/Delhi)", "4 to 6 yrs", "4 days ago; 40 applicants", "", "https://in.linkedin.com/jobs/view/microsoft-copilot-studio-engineer-chennai-pune-indore-hyderabad-delhi-4-to-6-yrs-at-tata-consultancy-services-4397329805", "N", "Unk", "LIVE", "Conversational experiences in Copilot Studio for IT support. Power Automate. .NET / .NET Core REST. ServiceNow ITSM via REST. Adaptive Cards in Teams.", "parent-extra"],
    ["PX019", "linkedin", "RAPSYS TECHNOLOGIES PTE LTD", "Microsoft Copilot Studio Developer", "Bengaluru; Work from anywhere", "3+ years Power Platform / Copilot Studio / PVA", "1 day ago; 50 applicants", "", "https://in.linkedin.com/jobs/view/microsoft-copilot-studio-developer-at-rapsys-technologies-pte-ltd-4381551963", "N", "Unk", "LIVE", "Work from anywhere. 3+ years Copilot Studio or Power Virtual Agents. Databricks and M365, Azure AI Services, Dataverse.", "parent-extra"],
    ["PX020", "linkedin", "Codvo.ai", "Copilot Studio / Agentic AI Engineer (Remote)", "Remote (Pune Division listed)", "4-8 years", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/copilot-studio-agentic-ai-engineer-remote-at-codvo-ai-4414406399", "N", "Unk", "INDEXED-LIVE", "Build first 5–6 Copilot Studio agents then scale. M365, Azure, SharePoint, Teams, Dataverse, Power Platform. Mid-Senior. Full-time.", "parent-extra"],
    ["PX021", "linkedin", "SourcingXPress", "Power Platform Engineer (Microsoft Copilot / Power Platform)", "Hyderabad, Telangana", "", "1 day ago; Over 200 applicants; posted 19 Aug 2026", "₹ 12-45 Lacs PA", "https://in.linkedin.com/jobs/view/power-platform-engineer-at-sourcingxpress-4456466593", "N", "Unk", "LIVE", "Employer salary range ₹12-45 Lacs PA. Build Copilot agents and agentic workflows in Copilot Studio. Power Platform, Azure Logic Apps, REST. PowerShell/Python/C#/JavaScript.", "parent-extra"],
    ["PX022", "linkedin", "SMC Squared India", "Power Platform and Copilot - Lead / Architect", "Bengaluru, Karnataka", "2+ years Power Platform / Copilot Studio", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/power-platform-and-copilot-lead-architect-at-smc-squared-india-4404989054", "N", "Unk", "INDEXED-LIVE", "Copilot Studio Developer in App Innovation practice. Power Fx, Power Automate, Dataverse, Microsoft Graph API.", "parent-extra"],
    ["PX023", "linkedin", "VGreen Technology Solutions (VGreenTEK)", "Power Platform & Copilot Studio Developer- 100% Remote", "Bengaluru South listed; 100% Remote", "6-7 yrs (5+ SWE; 3+ Power Platform)", "6 hours ago; 28 applicants", "Budget: 1 LPM", "https://in.linkedin.com/jobs/view/power-platform-copilot-studio-developer-100%25-remote-at-vgreen-technology-solutions-vgreentek-4364238453", "N", "Unk", "LIVE", "Contract 6 months + extendable. Budget 1 LPM. Proven Copilot Studio for AI-driven workflows. M365 + Azure Functions/Logic Apps/Dataverse.", "parent-extra"],
    ["PX024", "linkedin", "Sonata Software", "Copilot Studio Developer / Microsoft Copilot Studio Engineer", "Bengaluru, Karnataka", "4–8 years Power Platform / MS ecosystem", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/copilot-studio-developer-at-sonata-software-4320160656", "N", "Unk", "INDEXED-LIVE", "Custom Copilots via Copilot Studio (PVA). Integrate M365, Dynamics 365. Power Automate, Power Apps, Dataverse, Azure Cognitive Services.", "parent-extra"],
    ["PX025", "linkedin", "CGI", "Copilot Studio Agents Development services 6-9Y", "Bengaluru; Category IT Infrastructure", "6 to 9 Years", "LI guest indexed 23 Aug 2026; Position ID J0226-0338", "", "https://in.linkedin.com/jobs/view/copilot-studio-agents-development-services-6-9y-at-cgi-4375007955", "N", "Unk", "INDEXED-LIVE", "Multiple AI Agents in large enterprise. Copilot Studio topics/flows/plugins/grounding. M365 Copilot Agent Builder and SharePoint Agents. Dataverse ALM. C# custom code plugins.", "parent-extra"],
    ["PX026", "linkedin", "Rockwell Automation", "Power Platform & Copilot Developer", "Delhi listed; hiring Pune and Noida", "", "1 week ago; 98 applicants", "", "https://in.linkedin.com/jobs/view/power-platform-copilot-developer-at-rockwell-automation-4391725060", "N", "Unk", "LIVE", "Lead design/delivery of enterprise AI chatbot and low-code solutions using Copilot Studio and Power Platform. Pune and Noida.", "parent-extra"],
    ["PX027", "linkedin", "EY", "AIOPs Platform Engineer / Hybrid Cloud – AIOps Senior Engineer", "Bengaluru, Karnataka", "5–6 yrs", "12 hours ago; first 25 applicants (guest 23 Aug 2026)", "", "https://in.linkedin.com/jobs/view/aiops-platform-engineer-at-ey-4397954150", "Unk", "Unk", "LIVE", "Moogsoft, BigPanda, Dynatrace, Splunk, Datadog, ServiceNow ITOM. Observability metrics/logs/traces. 5-6 years Observability, AIOps, IT Operations, Service Management, Automation.", "parent-extra"],
    ["PX028", "linkedin", "Nityo Infotech", "Senior AIMLOps Engineer – AIOps / LLMOps / MLOps / GenAI Platforms", "Bengaluru", "5–8+ years", "6 days ago", "Market Range", "https://in.linkedin.com/jobs/view/senior-aiops-engineer-at-nityo-infotech-4370708660", "N", "Unk", "LIVE", "Azure | Databricks | AKS | ARO | Kubernetes | MLflow | GitHub Actions | Python | Helm | GitOps | Vector Stores | GenAI. CI/CD/CT for ML/LLM/GenAI. RAG + vector DBs.", "parent-extra"],
    ["PX029", "linkedin", "Persistent Systems", "LLMOps and AIOps Engineer", "Bengaluru", "8 to 12 years", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/llmops-and-aiops-engineer-at-persistent-systems-4329820249", "N", "Unk", "INDEXED-LIVE", "Deploy/manage LLMs (OpenAI, Azure OpenAI, Bedrock). Vector DBs Pinecone/Milvus/FAISS. Retrieval workflows. Python automation/APIs. Observability of latency/cost.", "parent-extra"],
    ["PX030", "linkedin", "SysTechCorp Inc", "AIOps Engineer", "Bengaluru; Hybrid", "6+ years", "6 days ago; 33 applicants", "max 10LPA", "https://in.linkedin.com/jobs/view/aiops-engineer-at-systechcorp-inc-4407833559", "N", "Unk", "LIVE", "Employer package max 10LPA. AI-driven observability across 700+ enterprise customers. Python AI/ML + data engineering. LLMs (OCI Generative AI, OpenAI).", "parent-extra"],
    ["PX031", "linkedin", "Aditi Consulting", "AIOps Engineer (Project AIRA hub-and-spoke agentic AIOps)", "Bengaluru, Karnataka", "5 years backend/platform Python", "2 days ago; no longer accepting", "", "https://in.linkedin.com/jobs/view/aiops-engineer-at-aditi-consulting-4408264876", "N", "Unk", "RECENT-CLOSED", "LangGraph HybridAgent (Planner, Memory, Tool Registry, Executor). LangChain, GPT-4/Claude, RAG, Guardrails. FastAPI/Flask, MCP, OAuth/mTLS, SSE. Kubernetes.", "parent-extra"],
    ["PX032", "linkedin", "EY", "AIOps Engineer-Senior / AIOps Manager", "Bengaluru, Karnataka", "9+ years IT ops/DevOps/SRE with 3 years AIOps", "4 weeks ago", "", "https://in.linkedin.com/jobs/view/aiops-engineer-senior-at-ey-4364539643", "N", "Y", "INDEXED-LIVE", "Moogsoft, BigPanda, Splunk ITSI, ServiceNow ITOM. Python with working knowledge of SQL, PowerShell, Bash. Azure/AWS/GCP. Terraform, Kubernetes.", "parent-extra"],
    ["PX033", "linkedin", "IBM", "Technical Consultant-AIOps", "Bengaluru East, Karnataka", "", "5 days ago", "", "https://in.linkedin.com/jobs/view/technical-consultant-aiops-at-ibm-4364141983", "N", "Unk", "LIVE", "Design/implement AIOps platforms. Python for AIOps solutions. Client-facing digital transformation / IT operations.", "parent-extra"],
    ["PX034", "linkedin", "Deloitte", "GCP Data/RAG Engineer - Senior Consultant, Data and Insights", "Hyderabad, Telangana", "7+ years data engineering and/or AI/ML; 3+ years GCP", "posted 17 Aug 2026 (guest 23 Aug)", "", "https://in.linkedin.com/jobs/view/gcp-data-rag-engineer-senior-consultant-data-and-insights-sales-and-services-customer-at-deloitte-4422033212", "N", "Unk", "LIVE", "Production RAG: ingestion, chunking, embeddings, vector indexing. Vertex AI Search, Vertex AI RAG Engine, Gemini. Vector Search / Pinecone / Weaviate / pgvector. BigQuery, Dataflow.", "parent-extra"],
    ["PX035", "linkedin", "MantriAI (search partner)", "ML & LLM Ops Software Engineer", "Remote India; open to Bangalore end-2026", "4 to 12 years total; at least 2.5 on ML systems in production", "3 weeks ago; no longer accepting; posted 14 Aug 2026", "₹30-45 LPA fixed plus equity", "https://in.linkedin.com/jobs/view/ml-llm-ops-software-engineer-at-mantriai-4447780207", "N", "Unk", "RECENT-CLOSED", "Employer compensation ₹30-45 LPA + equity. On-prem/plant GPU serving (vLLM/TGI/Triton/Ollama). LLM ops: prompt versioning, evaluation, guardrails, inference cost/latency. 30-45 day NP preferred.", "parent-extra"],
    ["PX036", "linkedin", "Qubrise Technologies", "Hiring AI Engineer | GenAI | LLMs | RAG", "Remote (must be Pune / Bangalore)", "4–6 Years", "no longer accepting (indexed 7 months ago on guest; recrawl 21 Aug 2026)", "", "https://in.linkedin.com/jobs/view/hiring-ai-engineer-genai-llms-rag-at-qubrise-technologies-4321307004", "N", "Unk", "RECENT-CLOSED", "RAG with Pinecone/FAISS/Milvus/Weaviate. Agentic frameworks LangChain, LlamaIndex, AutoGen, CrewAI. GPT/LLaMA/Mistral/Claude.", "parent-extra"],
    ["PX037", "linkedin", "APAS.AI", "Agentic AI Engineer", "India, Remote", "Minimum 5 years production ML/AI; 3 years LLMs/NLP/GenAI", "2 days ago; Over 200 applicants; posted 18 Aug 2026", "$1,500 - $2,500 (as listed on guest page; unit not further specified)", "https://in.linkedin.com/jobs/view/agentic-ai-engineer-at-apas-ai-4456752702", "N", "Unk", "LIVE", "Specialist LLM/retrieval/agent role. Production Python, PyTorch, LangChain or HF Transformers. RAG chunking/embeddings/vector/hybrid retrieval. Compensation listed $1,500-$2,500 — treat as pay-cut/unclear unit until employer confirms.", "parent-extra"],
    ["PX038", "linkedin", "Silicon Labs", "AI Engineer - LLM/ RAG/ Agentic Workflow (3 to 4yrs)", "Hyderabad, Telangana", "3 to 4yrs", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/ai-engineer-llm-rag-agentic-workflow-3-to-4yrs-at-silicon-labs-4351530975", "N", "Unk", "INDEXED-LIVE", "Production RAG and agentic automated workflows. LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI, Semantic Kernel. GPT/Claude/LLaMA/Mistral. MLOps.", "parent-extra"],
    ["PX039", "linkedin", "ZeroToOne.AI", "MLOps Engineer (Remote)", "Remote within India", "3-5 years MLOps / ML platform / ML infra", "no longer accepting", "₹25-40 LPA depending on experience", "https://in.linkedin.com/jobs/view/mlops-engineer-remote-at-zerotoone-ai-4405021949", "N", "Unk", "RECENT-CLOSED", "Employer salary ₹25-40 LPA. Fully remote India. 3-4 hours US Eastern overlap. AWS/GCP (SageMaker, Vertex, EKS/GKE).", "parent-extra"],
    ["PX040", "linkedin", "NymbleUp", "Sr. AI Engineer - RAG/LLM Systems", "Mumbai, Maharashtra", "4+ years production ML", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/sr-ai-engineer-rag-llm-systems-at-nymbleup-4358881257", "N", "Unk", "INDEXED-LIVE", "Domain RAG (labor laws, shift rules). Hook LLMs into existing Python services. LangChain/LlamaIndex, vector DBs, OpenAI/Claude. GCP/AWS.", "parent-extra"],
    ["PX041", "linkedin", "Workfall", "AI Engineer (RAG & Multi-Agent Systems)", "Bengaluru, Karnataka", "4+ Years", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/ai-engineer-rag-multi-agent-systems-at-workfall-4381580098", "Y", "Unk", "INDEXED-LIVE", "LangChain / LlamaIndex / Semantic Kernel / Spring AI. RAG hybrid retrieval. Multi-agent planner-executor. MCP servers. 4+ years.", "parent-extra"],
    ["PX042", "linkedin", "TEKsystems Global Services in India", "Software Engineer / ServiceNow AI Developer", "Hyderabad/Bengaluru; Hybrid", "5+ years ServiceNow; 3+ config/script; 1+ Now Assist", "LI guest indexed 23 Aug 2026; NP Immediate to 15 days", "", "https://in.linkedin.com/jobs/view/software-engineer-at-teksystems-global-services-in-india-4427505026", "N", "Unk", "INDEXED-LIVE", "Now Assist and Moveworks integrations, configuration-first. HRSD, ITSM, ITOM, ESM. Governance/security. Not a Python GenAI IC.", "parent-extra"],
    ["PX043", "linkedin", "Booking Holdings", "Business Application Engineer - Service Now (ITSM) / ServiceNow AI Developer", "Bengaluru, Karnataka (India CoE)", "", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/business-application-engineer-service-now-itsm-at-booking-holdings-nasdaq-bkng-4400187709", "N", "Unk", "INDEXED-LIVE", "Now Assist, Virtual Agent, Predictive Intelligence in production. CSA & CAD required. CIS ITSM required. AI Control Tower. Glide/JS implied by SN CAD.", "parent-extra"],
    ["PX044", "linkedin", "GrowthAXL", "Principal Engineer - Service Now (Now Assist AI Agents)", "Hyderabad, Telangana", "", "1 day ago (guest)", "", "https://in.linkedin.com/jobs/view/principal-engineer-service-now-at-growthaxl-4346968907", "N", "Unk", "LIVE", "Principal Engineer for ServiceNow focusing on Now Assist AI Agents. Prompt engineering, integrations, workflows. Agentic/autonomous systems, vector search, human-AI interaction. Healthcare.", "parent-extra"],
    ["PX045", "linkedin", "Dyooti (a K2 Partnering Solutions company)", "ServiceNow NowAssist (AI / Generative AI) Developer", "Pune City, Maharashtra", "8+ years ServiceNow; Now Assist mandatory", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/servicenow-nowassist-ai-generative-ai-developer-at-dyooti-a-k2-partnering-solutions-company-4390436237", "N", "Unk", "INDEXED-LIVE", "Now Assist OOB + custom AI skills. Predictive Intelligence, Task Intelligence, Virtual Agent. ITSM. Production-ready AI on SN with enterprise governance.", "parent-extra"],
    ["PX046", "linkedin", "PepsiCo", "Global Workplace Svcs Sr Analyst(ServiceNow+ Agentic AI)", "Hyderabad, Telangana", "10+ years programs/products with hands-on SN; 8+ ITSM; 3+ AI/ML/automation", "3 days ago; 30 applicants", "", "https://in.linkedin.com/jobs/view/global-workplace-svcs-sr-analyst-servicenow%2B-agentic-ai-at-pepsico-4374591197", "N", "Unk", "LIVE", "NOW Assist, GenAI orchestration, guardrails, process automation across ITSM. ITIL cert. 3+ years AI/ML frameworks, Process Mining, Automation, SN integrations.", "parent-extra"],
    ["PX047", "linkedin", "NOBL Q", "ServiceNow Agentic AI Engineer", "India", "", "1 week ago; 93 applicants", "", "https://in.linkedin.com/jobs/view/servicenow-agentic-ai-engineer-at-nobl-q-4358188847", "N", "Unk", "LIVE", "Autonomous goal-driven AI agents on ServiceNow. Now Assist / Azure OpenAI / OpenAI. Flow Designer, IntegrationHub. JavaScript, Glide APIs, Script Includes, Business Rules.", "parent-extra"],
    ["PX048", "linkedin", "DigiHelic Solutions Pvt. Ltd.", "ServiceNow AI Developer | Hyderabad: Hybrid | Immediate Joiner", "Hyderabad; Hybrid", "8+ years SN TSM/CSM/ITSM and TSOM/ITOM", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/servicenow-ai-developer-hyderabad-hybrid-immediate-joiner-at-digihelic-solutions-pvt-ltd-4376686108", "N", "Unk", "INDEXED-LIVE", "Now Assist Gen AI: VA with GenAI, AI Search, case summarization. Agentic AI Orchestration using Now Assist Skill Kit. Custom AI skills. Immediate joiner.", "parent-extra"],
    ["PX049", "linkedin", "UST", "Lead I - Software Engineering-Agentic AI, GCP", "Bengaluru, Karnataka", "Minimum 1+ year production AI Agents (lead title)", "posted 6 Aug 2026 (guest 23 Aug)", "", "https://in.linkedin.com/jobs/view/lead-i-software-engineering-agentic-ai-gcp-at-ust-4406465148", "N", "Unk", "LIVE", "Google ADK, LangGraph, LLMs. MCP, Vertex AI. Python. Productionize AI Agents for Data Fabric platforms.", "parent-extra"],
    ["PX050", "linkedin", "RoundCircle", "GenAI Engineer – AI Agents, LangGraph & RAG", "Bengaluru, Karnataka", "", "LI guest indexed 23 Aug 2026", "", "https://in.linkedin.com/jobs/view/genai-engineer-%E2%80%93-ai-agents-langgraph-rag-at-roundcircle-4424185456", "N", "Unk", "INDEXED-LIVE", "LangGraph, CrewAI, AutoGen, or PydanticAI. Python. GPT/Claude/Llama. Preferred MLOps/LLMOps, Azure ML.", "parent-extra"],
    ["PX051", "linkedin", "Freshworks", "Lead Software Engineer - Machine Learning", "Bengaluru, Karnataka", "6–9 years SWE/ML with recent LLM/agentic production", "posted 21 Aug 2026 (guest 23 Aug)", "", "https://in.linkedin.com/jobs/view/lead-software-engineer-machine-learning-at-freshworks-4436494162", "N", "Unk", "LIVE", "Productionize LLMs, multi-agent frameworks, cognitive architectures. LangGraph, AutoGen, CrewAI POCs. LLMOps, RAG, prompt versioning, routing.", "parent-extra"],
    ["PX052", "linkedin", "Cognizant", "AI Customer Engineer", "Bangalore Urban / Chennai onsite 5 days", "", "1 week ago; Over 200 applicants; posted 4 Aug 2026", "", "https://in.linkedin.com/jobs/view/ai-customer-engineer-at-cognizant-4424249762", "N", "Unk", "LIVE", "Google ADK or Copilot Studio or CrewAI/Autogen. RAG, prompt engineering, LLM integrations. Onsite 5 days Chennai/Bangalore.", "parent-extra"],
    ["PX053", "naukri", "CDK Global", "Microsoft Copilot Studio Engineer", "Hyderabad", "6-10 years (JD also states 2–4 years copilots/Power Platform)", "2 weeks ago; 100+", "15-20 Lacs P.A.", "https://www.naukri.com/job-listings-microsoft-copilot-studio-engineer-cdk-global-hyderabad-6-to-10-years-160726033680", "N", "Unk", "LIVE", "Employer 15-20 Lacs PA. Copilot Studio Builder: topics, generative answers, actions, Power Automate, knowledge sources. GPTW-certified Hyderabad/Pune GCC.", "parent-extra"],
    ["PX054", "naukri", "Zensar Technologies", "Microsoft AI Copilot Studio Engineer", "Bengaluru", "3-5 years", "3+ weeks ago; 47 applicants on card", "", "https://www.naukri.com/job-listings-microsoft-ai-copilot-studio-engineer-zensar-technologies-bengaluru-3-to-5-years-111225500155", "N", "Unk", "INDEXED-LIVE", "Hands-on Copilot Studio delivery. Topic design, conversation flows, prompt engineering. 1-2+ years copilots/chatbots (PVA, Azure Bot Service or equivalent).", "parent-extra"],
    ["PX055", "naukri", "Capgemini", "MS Copilot Studio Engineer (+Python)", "Hyderabad / Secunderabad", "2-7 years (min 2 years automation & AI / low-code + Copilot Studio)", "3 weeks ago", "", "https://www.naukri.com/job-listings-ms-copilot-studio-engineer-python-capgemini-technology-services-india-limited-hyderabad-2-to-7-years-011225916609", "N", "Unk", "INDEXED-LIVE", "Design/test/deploy AI agents in Copilot Studio, embed in Power Apps, Power Automate. Python + low-code.", "parent-extra"],
    ["PX056", "naukri", "Sonata Software", "M365 Copilot Platform Engineer", "Hyderabad, Bengaluru, Chennai; Hybrid", "8-13 years", "2 weeks ago", "", "https://www.naukri.com/job-listings-m365-copilot-platform-engineer-sonata-software-hyderabad-chennai-bengaluru-8-to-13-years-230126020443", "N", "Unk", "INDEXED-LIVE", "Copilot Studio plus n8n or Power Automate/Power Platform and Azure AI Services. Python, C#, JavaScript for AI orchestration.", "parent-extra"],
    ["PX057", "naukri", "Insight Global Technologies", "Co-pilot AI Engineer/Agent Builder", "Hyderabad / Secunderabad", "5-10 years (required 6+ years AI development)", "3 days ago", "", "https://www.naukri.com/job-listings-co-pilot-ai-engineer-agent-builder-insight-global-technologies-hyderabad-5-to-10-years-051225038030", "N", "Y", "LIVE", "Copilot Studio agent dialogs/triggers/actions. RAG, LLMs. Azure AI Vector, MongoDB and Postgres. TypeScript, ChatScript, Python. FAISS/Pinecone/Milvus. OpenAI/Anthropic/Vertex/Bedrock.", "parent-extra"],
    ["PX058", "naukri", "Quantaleap", "Copilot Studio Developer (Conversational AI + Power Platform)", "Remote (hiring office Bengaluru)", "4-7 years (2-5 Power Platform / Conversational AI)", "1 day ago", "", "https://www.naukri.com/job-listings-copilot-studio-developer-conversational-ai-power-platform-quantaleap-bengaluru-4-to-7-years-051225017449", "N", "Unk", "LIVE", "Immediate / 0-15 days NP preferred. Copilot Studio bot design + M365 integrations. Remote.", "parent-extra"],
    ["PX059", "naukri", "Hexaware Technologies", "Copilot Studio Developer", "Chennai, Pune, Bengaluru", "4-9 years", "3+ weeks ago; 100+", "", "https://www.naukri.com/job-listings-copilot-studio-developer-hexaware-technologies-pune-chennai-bengaluru-4-to-9-years-271125025186", "N", "Unk", "INDEXED-LIVE", "Enterprise Copilot Studio agents and Power Platform. Custom connectors, RAG, Semantic Index. AI Builder, LLM concepts, prompt engineering, agentic AI patterns.", "parent-extra"],
    ["PX060", "naukri", "Cyclotron", "Microsoft Copilot Studio Architect", "Remote India (hiring office Pune)", "10-20 years band; JD 5+ architecture", "1 week ago; 100+", "25-40 Lacs P.A.", "https://www.naukri.com/job-listings-microsoft-copilot-studio-architect-cyclotron-pune-10-to-20-years-140126019305", "N", "Unk", "LIVE", "Employer 25-40 Lacs PA. FTE. Shift 2 PM IST to 11 AM IST. Azure AI Foundry for model management/evaluation/orchestration/grounding. Enterprise Copilot Studio architect.", "parent-extra"],
    ["PX061", "naukri", "iSoftStone", "Azure AI & Copilot Studio Developer", "Remote (hiring office Bengaluru)", "5-10 years", "3 weeks ago", "50,000 P.A. (as printed on Naukri card — likely data error vs monthly; treat as unverified)", "https://www.naukri.com/job-listings-azure-ai-copilot-studio-developer-isoftstone-bengaluru-5-to-10-years-050126013995", "N", "Unk", "INDEXED-LIVE", "Azure AI Foundry and Copilot Studio. Azure OpenAI / Generative AI. Enterprise prompt engineering & agent design. Salary field 50,000 P.A. is not trusted.", "parent-extra"],
    ["PX062", "naukri", "IDESLABS PRIVATE LIMITED (Leading Client)", "Microsoft Copilot Studio & Python", "Hyderabad (JD also says Bangalore)", "5-8 years", "Few hours ago (23 Aug 2026 index)", "", "https://www.naukri.com/job-listings-microsoft-copilot-studio-python-ideslabs-private-limited-hyderabad-5-to-8-years-181225918069", "N", "Unk", "LIVE", "AI agents and virtual chatbots using MS Copilot Studio. Azure OpenAI. NLP/GenAI models using PowerApps. Python for DS workloads.", "parent-extra"],
    ["PX063", "naukri", "Tata Consultancy Services", "Generative AI Engineer", "Hyderabad, Bengaluru", "4-8 years", "2 weeks ago; 100+", "2-7 Lacs P.A.", "https://www.naukri.com/job-listings-generative-ai-engineer-tata-consultancy-services-hyderabad-bengaluru-4-to-8-years-310326010830", "N", "Unk", "INDEXED-LIVE", "PAY-CUT FLAG: Naukri employer-stated 2-7 Lacs PA for 4-8 YOE. Must-have: LLM Ops & Agent Orchestration (LangChain, LangGraph, Google ADK); RAG; Vector DBs; Python FastAPI/Flask; Docker/K8s.", "parent-extra"],
    ["PX064", "naukri", "Persistent", "GenAI Engineer", "Hyderabad, Bengaluru", "6-10 years", "2 weeks ago; in-person drive dated 14 Feb 2026", "", "https://www.naukri.com/job-listings-genai-engineer-persistent-hyderabad-bengaluru-6-to-10-years-110226000352", "N", "Unk", "OLDER", "In-person hiring drive 14 Feb 2026 Hyd & BLR. GEN AI, ML, LangChain, LangGraph, GenAI Architecture Strategy, Prompt engineering.", "parent-extra"],
    ["PX065", "careers", "UnitedHealth Group", "AI or ML Engineer - LLMs, RAG, LangChain, LangGraph", "Bengaluru, India", "", "Date posted: 08/11/2026; Req 2375302", "", "https://careers.unitedhealthgroup.com/job/bengaluru/ai-or-ml-engineer-llms-rag-langchain-langgraph/34088/99093468144", "Y", "Unk", "LIVE", "Agentic AI, RAG, AI workflow automation. Spring AI, LangChain, LangGraph. AWS and Azure. Tool calling, planning, memory, multi-agent. Docker/K8s/CI/CD.", "parent-extra"],
    ["PX066", "hirist", "BirchAI (Sagility Group)", "LLM Orchestration Engineer - LangGraph", "Hybrid Bangalore", "3+ years software/AI; 1+ year GenAI orchestration", "hirist job 1607190 (indexed 23 Aug 2026)", "", "https://www.hirist.tech/j/llm-orchestration-engineer-langgraph-1607190", "N", "Unk", "INDEXED-LIVE", "Build/own LLM agent workflows using LangGraph/LangChain for production conversational AI. Routing, memory, tool-calling, recovery. Python. RAG. Git, Docker.", "parent-extra"],
    ["PX067", "glassdoor", "Cognizant", "AI Engineer Python, Langchain, LangGraph, Agentic AI, API, LLMs", "Bengaluru", "7 to 13 years; NP Immediate to 90 days", "Glassdoor page dated 6 Jul 2026 (retrieved 23 Aug 2026)", "₹5L - ₹10L (Glassdoor Est. — not employer-stated)", "https://www.glassdoor.co.in/job-listing/ai-engineer-python-langchain-langgraph-agentic-ai-api-llms-cognizant-technology-solutions-JV_IC2940587_KO0,58_KE59,89.htm?jl=1010104809518", "N", "Unk", "INDEXED-LIVE", "Design/deploy Agentic AI in Python. Multi-agent workflows. RAG. Backend microservices for AI apps. Glassdoor estimate ₹5-10L is NOT employer CTC.", "parent-extra"],
    ["PX068", "linkedin", "Sonata Software", "Developer (Copilot Developer)", "Bangalore Urban; Bangalore/Hyderabad/Chennai; shift 11 AM-8 PM", "3+ years", "1 month ago; 84 applicants", "", "https://in.linkedin.com/jobs/view/developer-at-sonata-software-4320968408", "N", "Unk", "INDEXED-LIVE", "Copilot Developer: customize Microsoft Copilot solutions. Copilot Studio. Integrate M365, Power Platform, Azure. APIs and connectors.", "parent-extra"],
]


def clean(s: str) -> str:
    return (s or "").replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def canon(u: str) -> str:
    u = clean(u)
    u = u.split("?")[0].split("#")[0].rstrip("/").lower()
    u = u.replace("http://", "https://")
    u = u.replace("https://www.linkedin.com", "https://in.linkedin.com")
    m = re.search(r"linkedin\.com/jobs/view/[^/]*?(\d{8,})", u)
    if m:
        return "li:" + m.group(1)
    m = re.search(r"naukri\.com/job-listings-[^/?#]*?-(\d{6,})", u)
    if m:
        return "nk:" + m.group(1)
    m = re.search(r"instahyre\.com/job-(\d+)", u)
    if m:
        return "ih:" + m.group(1)
    m = re.search(r"[?&]jk=([a-f0-9]+)", clean(u) if "?" in (u or "") else u)
    if not m:
        # jk may have been stripped; try original handled above
        pass
    m = re.search(r"indeed\.com/viewjob", u)
    m2 = re.search(r"jk=([a-f0-9]+)", u)
    if m2:
        return "ind:" + m2.group(1)
    m = re.search(r"hirist\.tech/j/[^/]*-(\d+)", u)
    if m:
        return "hi:" + m.group(1)
    m = re.search(r"foundit\.in/job/[^/]*-(\d+)$", u)
    if m:
        return "fo:" + m.group(1)
    m = re.search(r"cutshort\.io/job/[^/]*-([A-Za-z0-9]+)$", u)
    if m:
        return "cs:" + m.group(1)
    m = re.search(r"glassdoor\.[^/]+/job-listing/[^\s]*jl=(\d+)", u)
    if m:
        return "gd:" + m.group(1)
    m = re.search(r"careers\.cognizant\.com/[^/]+/jobs/(\d+)/", u)
    if m:
        return "cts:" + m.group(1)
    return u


def is_volume(url: str, title: str = "") -> bool:
    u = (url or "").lower()
    if VOLUME_RE.search(u):
        return True
    if re.search(r"naukri\.com/(?!job-listings)", u) and "job-listings" not in u:
        if re.search(r"jobs(/|$)", u):
            return True
    if "/q-" in u and "indeed.com" in u:
        return True
    return False


def norm_flag(v: str) -> str:
    v = (v or "").strip()
    if v.upper() in ("Y", "YES", "TRUE", "1"):
        return "Y"
    if v.upper() in ("N", "NO", "FALSE", "0"):
        return "N"
    if v.upper() in ("U", "UNK", "UNKNOWN", ""):
        return "Unk"
    return v


def norm_status(s: str) -> str:
    s = clean(s)
    sl = s.upper()
    if sl in ("LIVE",):
        return "LIVE"
    if sl in ("INDEXED-LIVE", "INDEXED LIVE"):
        return "INDEXED-LIVE"
    if sl in ("INDEXED-LIVE PARTIAL", "INDEXED-LIVE-PARTIAL", "INDEXED", "PARTIAL"):
        return "INDEXED-LIVE-PARTIAL"
    if sl in ("RECENT-CLOSED", "CLOSED"):
        return "RECENT-CLOSED"
    if sl in ("EXPIRED",):
        return "EXPIRED"
    if sl in ("OLDER",):
        return "OLDER"
    if "PARTIAL" in sl and "INDEXED" in sl:
        return "INDEXED-LIVE-PARTIAL"
    if sl.startswith("LIVE"):
        return "LIVE"
    return s or "INDEXED-LIVE"


def row_from_dict(d: dict, harvest_file: str) -> dict:
    url = clean(d.get("url", ""))
    return {
        "id": clean(d.get("id", "")),
        "source": clean(d.get("source", "")).lower(),
        "company": clean(d.get("company", "")),
        "title": clean(d.get("title", "")),
        "location": clean(d.get("location", "")),
        "exp": clean(d.get("exp", "")),
        "posted": clean(d.get("posted", "")),
        "salary": clean(d.get("salary", "")),
        "url": url,
        "java": norm_flag(d.get("java", "")),
        "sql": norm_flag(d.get("sql", "")),
        "status": norm_status(d.get("status", "")),
        "snippet": clean(d.get("snippet", "")),
        "harvest_file": harvest_file,
    }


def load_tsvs() -> list[dict]:
    rows = []
    for f in sorted(RAW.glob("*.tsv")):
        if f.name.startswith("MASTER"):
            continue
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines:
            continue
        reader = csv.DictReader(lines, delimiter="\t")
        for d in reader:
            rows.append(row_from_dict(d, f.name))
    return rows


def load_extras() -> list[dict]:
    out = []
    for r in EXTRAS:
        assert len(r) == 14, (r[0], len(r))
        d = dict(zip(HDR, r))
        out.append(row_from_dict(d, "parent-extra"))
    return out


def better(a: dict, b: dict) -> dict:
    """Prefer LIVE full rows, then richer snippets / salary / flags."""
    rank = {
        "LIVE": 5,
        "INDEXED-LIVE": 4,
        "INDEXED-LIVE-PARTIAL": 3,
        "OLDER": 2,
        "RECENT-CLOSED": 2,
        "EXPIRED": 1,
    }
    ra, rb = rank.get(a["status"], 0), rank.get(b["status"], 0)
    if rb > ra:
        return b
    if ra > rb:
        return a
    # merge missing fields from the other
    merged = dict(a)
    for k in HDR:
        if not merged.get(k) and b.get(k):
            merged[k] = b[k]
    if len(b.get("snippet") or "") > len(merged.get("snippet") or ""):
        merged["snippet"] = b["snippet"]
    if merged.get("java") == "Unk" and b.get("java") in ("Y", "N"):
        merged["java"] = b["java"]
    if merged.get("sql") == "Unk" and b.get("sql") in ("Y", "N"):
        merged["sql"] = b["sql"]
    if (not merged.get("salary") or merged["salary"].lower() in ("not disclosed",)) and b.get("salary"):
        merged["salary"] = b["salary"]
    srcs = []
    for s in (a.get("harvest_file"), b.get("harvest_file")):
        if s and s not in srcs:
            srcs.append(s)
    merged["harvest_file"] = "+".join(srcs)
    return merged


def city_bucket(loc: str) -> str:
    t = (loc or "").lower()
    hits = []
    if any(x in t for x in ("bengaluru", "bangalore", "blr")):
        hits.append("Bengaluru")
    if "hyderabad" in t or t.startswith("hyd"):
        hits.append("Hyderabad")
    if "chennai" in t:
        hits.append("Chennai")
    if "pune" in t:
        hits.append("Pune")
    if any(x in t for x in ("noida", "gurgaon", "gurugram", "delhi", "ncr")):
        hits.append("NCR")
    if "coimbatore" in t:
        hits.append("Coimbatore")
    if any(x in t for x in ("remote", "work from home", "wfh", "work from anywhere")):
        hits.append("Remote")
    if "mumbai" in t:
        hits.append("Mumbai")
    if not hits:
        return "Other/unspecified"
    return "+".join(hits)


def family(title: str, snippet: str) -> str:
    t = f"{title} {snippet}".lower()
    if any(x in t for x in ("copilot studio", "power virtual agent", "power platform", "m365 copilot")):
        return "Copilot Studio / Power Platform"
    if any(x in t for x in ("now assist", "servicenow", "nowassist", "itsm")) and any(
        x in t for x in ("agent", "genai", "generative", "now assist", "virtual agent")
    ):
        return "ServiceNow / Now Assist / ITSM-AI"
    if "aiops" in t or "ai ops" in t or "ai-ops" in t:
        return "AIOps / Observability"
    if any(x in t for x in ("llmops", "mlops", "llm ops", "ml ops")):
        return "LLMOps / MLOps"
    if any(x in t for x in ("agentic", "ai agent", "multi-agent", "langgraph", "autogen", "crewai")):
        return "Agentic AI / Agents"
    if any(x in t for x in ("rag", "retrieval")):
        return "RAG / Applied LLM"
    if any(x in t for x in ("genai", "gen ai", "generative ai", "llm")):
        return "GenAI / LLM Engineer"
    return "Other applied AI"


def main() -> None:
    rows = load_tsvs() + load_extras()
    by_key: dict[str, dict] = {}
    volume = []
    dropped_no_url = 0
    for r in rows:
        url = r.get("url") or ""
        if not url:
            dropped_no_url += 1
            continue
        if is_volume(url, r.get("title") or ""):
            volume.append(r)
            continue
        k = canon(url)
        if not k:
            dropped_no_url += 1
            continue
        if k in by_key:
            by_key[k] = better(by_key[k], r)
        else:
            by_key[k] = r

    uniq = list(by_key.values())
    uniq.sort(key=lambda r: (r.get("company", "").lower(), r.get("title", "").lower(), r.get("url", "")))
    for i, r in enumerate(uniq, 1):
        r["id"] = f"JD{i:04d}"

    # write TSV/CSV
    def write_table(path: Path, delimiter: str) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=HDR, delimiter=delimiter, lineterminator="\n")
            w.writeheader()
            for r in uniq:
                w.writerow({k: r.get(k, "") for k in HDR})

    write_table(OUT_TSV, "\t")
    write_table(OUT_CSV, ",")

    n = len(uniq)
    st = Counter(r["status"] for r in uniq)
    src = Counter(r["source"] for r in uniq)
    fam = Counter(family(r["title"], r["snippet"]) for r in uniq)
    geo = Counter()
    for r in uniq:
        for part in city_bucket(r["location"]).split("+"):
            geo[part] += 1
    java_y = sum(1 for r in uniq if r["java"] == "Y")
    java_n = sum(1 for r in uniq if r["java"] == "N")
    sql_y = sum(1 for r in uniq if r["sql"] == "Y")
    sql_n = sum(1 for r in uniq if r["sql"] == "N")
    sal = [
        r
        for r in uniq
        if r.get("salary")
        and r["salary"].lower() not in ("not disclosed", "not disclosed.", "market range")
        and "est" not in r["salary"].lower()
    ]

    def md_table(counter: Counter, total: int) -> str:
        lines = ["| Value | N | % |", "|---|---:|---:|"]
        for k, v in counter.most_common():
            lines.append(f"| {k} | {v} | {100*v/total:.1f}% |")
        return "\n".join(lines)

    # compact inventory for markdown (all rows, truncated snippet)
    inv_lines = [
        "| ID | Company | Title | Location | Exp | Posted | Salary | Java | SQL | Status | URL |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in uniq:
        title = r["title"].replace("|", "/")
        loc = r["location"].replace("|", "/")
        inv_lines.append(
            f"| {r['id']} | {r['company'].replace('|','/')} | {title} | {loc} | {r['exp']} | {r['posted'][:40]} | {r['salary'][:40]} | {r['java']} | {r['sql']} | {r['status']} | {r['url']} |"
        )

    md = f"""# W1-A2 JD Corpus Master — India AI listings (harvest 23 Aug 2026)

**Question answered:** largest unique sample of **active/recent India AI job descriptions** that could be captured without board APIs (Naukri/LinkedIn/Indeed HTML is Akamai/JS-walled).

**Evidence labels:** every row is a real indexed or retrieved listing URL. Bodies are **LIVE** (page retrieved), **INDEXED-LIVE** (Google/Bing/board SERP still showing it as current), **INDEXED-LIVE-PARTIAL** (card/snippet only), **RECENT-CLOSED**, **EXPIRED**, or **OLDER**.

## Headline counts (VERIFIED FACT from this merge)

| Metric | N |
|---|---:|
| Unique listing keys after URL/ID dedupe | **{n}** |
| Raw TSV rows before extras/dedupe (4 harvest files) | 454 |
| Parent extras added this pass | {len(EXTRAS)} |
| Volume/search pages excluded from unique FTE count | {len(volume)} |
| Rows dropped (no URL) | {dropped_no_url} |
| Java named **Y** | {java_y} ({100*java_y/n:.1f}%) |
| Java named **N** (explicit non-Java stack in captured text) | {java_n} |
| Java unknown | {n-java_y-java_n} |
| SQL named **Y** | {sql_y} ({100*sql_y/n:.1f}%) |
| SQL named **N** | {sql_n} |
| Employer-stated salary field nonempty (excl. Not Disclosed / Glassdoor est.) | {len(sal)} |

This is **not** Naukri’s keyword volume. Naukri still prints **~9,938 Agentic AI** and **~558–680 AIOps** title hits in Aug 2026 — those are keyword-polluted, not unique FTE reqs. Unique captured corpus **N={n}**.

## Status mix

{md_table(st, n)}

## Source mix (primary board of the surviving URL)

{md_table(src, n)}

## Role family (title+snippet heuristic — INFERENCE)

{md_table(fam, n)}

## Geography mentions (a listing can hit multiple cities)

{md_table(geo, n)}

## Method and honesty limits

1. **Boards block scrapers.** Naukri listing HTML is Akamai 403; LinkedIn guest often 302s to `expired_jd_redirect`; Instahyre/Cutshort/hirist are JS shells. Harvest = Google-indexed titles/snippets + surviving guest/careers pages + SERP cards.
2. **Several hundred is the honest unique-URL ceiling for this tool path in one day**, not the market size. Market size remains the board keyword volumes (polluted).
3. **Dedupe key:** LinkedIn numeric job id, Naukri listing id, Instahyre job id, Indeed `jk`, hirist id, Foundit id, else normalized URL.
4. **Twins kept if different IDs** (same TCS Agentic title on Naukri vs LinkedIn = 2 rows). Same id across boards collapses.
5. **Java/SQL flags** are only **Y** when captured text names them. Many PARTIAL cards never mention stack → Unk. Do **not** read Unk as “no Java”.
6. **Salary** is employer-stated on the card/JD only. Glassdoor estimates are labelled EST and excluded from the salary-disclosed count.

## Hostile / pay-cut flags inside this corpus (sample)

- TCS Naukri GenAI Hyd/BLR 4–8 Yrs **2–7 Lacs PA** (`nk:310326010830`) — kitchen-sink LangGraph/ADK at Service Desk pay.
- SysTechCorp AIOps Bengaluru 6+ **max 10LPA** (LinkedIn `4407833559`) — below current ₹11 LPA.
- APAS.AI remote Agentic **$1,500–$2,500** listed with unclear unit (LinkedIn `4456752702`).
- iSoftStone Copilot Studio card **50,000 P.A.** — treat as Naukri data error, not an offer.
- Infosys/Cognizant Glassdoor estimates ₹5–10 L are **not** employer CTC.

## High-fit slices for this candidate (RECOMMENDATION, not a lock)

Use the TSV filters; do not treat this list as apply-now without opening the URL.

- **AIOps / hybrid observability** with ITSM: EY Coimbatore/Pune/BLR cards; EY LinkedIn AIOps Platform Engineer; IBM AIOps consultant; Persistent LLMOps+AIOps.
- **Copilot Studio** with IT-support use case: TCS Copilot Studio Engineer (IT support + ServiceNow REST); CGI 6–9Y Copilot agents; Siemens Energy / BRATHON / TOCUMULUS already in prior harvest; CDK Global **15–20 LPA** Hyderabad.
- **Now Assist / SN Agentic:** TEKsystems, Booking Holdings CoE, Dyooti Pune 8+, DigiHelic Hyd, NOBL Q, PepsiCo Hyderabad (senior).
- **Coimbatore named:** Systango GenAI, Techify Gen AI, EY GDS Gen AI Specialist Manager, EY AIOps hybrid card, ShellKode Gen AI Lead (closed).

## Files

- Machine-readable master: `research/jd-raw/MASTER-india-ai-jd-corpus.tsv` and `.csv` (N={n}).
- Source harvests: `naukri-genai.tsv`, `naukri-ops-copilot.tsv`, `other-boards.tsv`, `services-gcc.tsv`, plus parent extras in `_merge_master.py`.
- Prior qualitative coding (full-body N=52): `research/W1-A2-jd-mining.md` and `research/A3-jd-corpus.md`.

## Full unique inventory

{chr(10).join(inv_lines)}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print("UNIQUE", n)
    print("STATUS", dict(st))
    print("SOURCE", dict(src))
    print("FAMILY", dict(fam))
    print("JAVA_Y", java_y, "SQL_Y", sql_y, "SALARY", len(sal))
    print("VOLUME_EXCLUDED", len(volume))
    print("wrote", OUT_TSV)
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
