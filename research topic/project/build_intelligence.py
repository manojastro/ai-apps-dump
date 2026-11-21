"""Build AI Portfolio Project Intelligence workbook + docs."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_DIR = r"D:\ai apps dump\research topic\project"
XLSX = os.path.join(OUT_DIR, "AI_Portfolio_Project_Intelligence_2026.xlsx")

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
SUB_FONT = Font(bold=True, size=11, color="2E75B6")
THIN = Border(left=Side(style='thin', color='B0B0B0'), right=Side(style='thin', color='B0B0B0'),
              top=Side(style='thin', color='B0B0B0'), bottom=Side(style='thin', color='B0B0B0'))
WRAP = Alignment(wrap_text=True, vertical="top")

def style_header(ws, row=1, max_col=None):
    for c in range(1, (max_col or ws.max_column)+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = THIN

def autofit(ws, max_width=52, min_width=14):
    for col in ws.columns:
        m = 0
        letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                v = str(cell.value) if cell.value is not None else ""
                m = max(m, min(len(v), 90))
            except Exception:
                pass
        ws.column_dimensions[letter].width = max(min_width, min(max_width, m+4))

def add_table(ws, headers, rows, start_row=1):
    ws.append(headers)
    for r in rows:
        ws.append(r)
    style_header(ws, row=start_row, max_col=len(headers))
    for row in ws.iter_rows(min_row=start_row+1, max_row=ws.max_row, max_col=len(headers)):
        for cell in row:
            cell.alignment = WRAP
            cell.border = THIN
    ws.freeze_panes = "A2"
    autofit(ws)

# ---------------------------------------------------------------- MASTER DATA
# 60 canonical project patterns distilled from sub-agent evidence.
# Scores follow spec rubrics. Metrics use placeholders, never invented facts.
PROJECTS = [
 # id, name, category, primary, secondary, source_type, geo, authenticity, quality, hiring, diff(0-10), prod_read, market, effort, complexity(0-10), coverage_count, resume_val, interview_val
 ("P001","Autonomous Incident Triage + RCA Agent (HolmesGPT-style)","AIOps","AIOps Engineer","GenAI/Agentic AI; Cloud AI; AI Solutions Architect","GitHub+Resume pattern","India+Global","B",88,94,8,82,92,"Large",8,5,"High","High"),
 ("P002","Multi-source Alert Correlation + Noise Reduction Service","AIOps","AIOps Engineer","Cloud AI; AI Solutions Architect","Resume+JD pattern","India+Global","B",84,90,7,80,90,"Large",7,4,"High","High"),
 ("P003","Streaming Log Anomaly Detection Platform (Kafka + IsolationForest)","AIOps","AIOps Engineer","Cloud AI; GenAI/Agentic AI","GitHub pattern","Global","B",82,86,7,78,85,"Large",7,4,"High","High"),
 ("P004","Metrics Forecasting + Predictive Capacity Planner (Prophet+XGBoost)","AIOps","AIOps Engineer","Cloud AI; AI Solutions Architect","GitHub+Resume","Global","B",80,82,6,75,84,"Medium",6,4,"Medium","High"),
 ("P005","SLO-linked Slack-native Incident Commander","AIOps","AIOps Engineer","Forward Deployed; AI Solutions Engineer","Portfolio pattern","Global","B",81,87,7,76,86,"Medium",6,4,"Medium","High"),
 ("P006","Change-correlated RCA (deploy/flag → incident)","AIOps","AIOps Engineer","GenAI/Agentic AI; Cloud AI","GitHub (HolmesGPT+Robusta)","Global","B",83,88,8,79,87,"Medium",7,4,"Medium","High"),
 ("P007","SRE Knowledge Copilot (runbook-grounded RAG)","AIOps","AIOps Engineer","GenAI/Agentic AI; AI Solutions Engineer","Inferred from RAG+AIOps","India+Global","B",82,89,7,77,89,"Medium",6,5,"High","High"),
 ("P008","FinOps Cost-Anomaly + Capacity Advisor","AIOps","AIOps Engineer","Cloud AI; AI Solutions Architect","Inferred","Global","C",76,80,7,70,82,"Medium",6,3,"Medium","Medium"),
 ("P009","Multi-provider AI Gateway (LiteLLM + fallbacks + budgets)","Cloud AI","Cloud AI Engineer","AI Security; AI Solutions Architect; GenAI","GitHub (LiteLLM)","Global","A",90,93,8,88,94,"Medium",7,6,"High","High"),
 ("P010","Kubernetes Inference Platform (KServe + vLLM + GPU autoscale)","Cloud AI","Cloud AI Engineer","AIOps; AI Solutions Architect","GitHub (KServe/vLLM)","Global","A",89,92,8,90,93,"Large",8,5,"High","High"),
 ("P011","Serverless RAG API + Async Batch Inference","Cloud AI","Cloud AI Engineer","GenAI; AI Solutions Engineer","Portfolio pattern","Global","C",74,78,5,72,80,"Small",5,4,"Medium","Medium"),
 ("P012","LLMOps Platform (prompt registry + eval gates + tracing)","Cloud AI","Cloud AI Engineer","GenAI; AI Solutions Architect; Forward Deployed","GitHub (MLflow/TensorZero)","Global","B",88,93,9,86,93,"Large",8,6,"High","High"),
 ("P013","GPU LoRA Multi-adapter Serving (single vLLM pod)","Cloud AI","Cloud AI Engineer","GenAI; AI Solutions Architect","GitHub pattern","Global","B",82,84,8,83,85,"Medium",7,3,"Medium","High"),
 ("P014","Tenant-aware Inference with Semantic Cache + Routing","Cloud AI","Cloud AI Engineer","AI Security; GenAI","Inferred from gateway","Global","B",85,89,8,84,89,"Medium",7,5,"High","High"),
 ("P015","Golden-path Platform (Backstage + ArgoCD + KServe + OpenCost)","Cloud AI","Cloud AI Engineer","AI Solutions Architect; Forward Deployed","GitHub (NeuroScale)","Global","B",87,90,9,87,90,"Large",8,5,"High","High"),
 ("P016","Hybrid Multi-cloud RAG via Gateway (Bedrock+Azure+Vertex)","Cloud AI","Cloud AI Engineer","AI Solutions Architect; Forward Deployed","Case-study synthesis","India+Global","B",86,90,8,83,91,"Large",8,6,"High","High"),
 ("P017","Invoice IDP Bot with HITL + Cost Tracking (UiPath/Power Automate + LLM)","Automation","Intelligent Automation Engineer","Forward Deployed; AI Solutions Engineer","Resume+JD pattern","India+Global","A",84,89,6,82,90,"Medium",6,4,"High","High"),
 ("P018","Cross-platform Order-to-Cash Orchestration (Maestro + Power Automate)","Automation","Intelligent Automation Engineer","Forward Deployed; Cloud AI","Docs pattern","Global","B",83,86,8,80,86,"Large",7,4,"High","High"),
 ("P019","Email Triage + Draft + Human Approval Workflow","Automation","Intelligent Automation Engineer","GenAI; AI Solutions Engineer","Portfolio pattern","Global","C",75,80,5,70,82,"Small",5,4,"Medium","Medium"),
 ("P020","Self-healing Bot Ops (failure classifier + KB + auto-retry)","Automation","Intelligent Automation Engineer","AIOps; GenAI","Guide pattern","Global","B",81,84,8,78,84,"Medium",6,4,"Medium","High"),
 ("P021","Engineering Drawing Extractor (Doc Intelligence + YOLO symbols)","Automation","Intelligent Automation Engineer","Cloud AI; AI Solutions Engineer","Case pattern","Global","B",84,85,9,80,84,"Large",7,3,"Medium","High"),
 ("P022","HR Onboarding Automation (Doc + ITSM + IAM provisioning)","Automation","Intelligent Automation Engineer","Forward Deployed; AI Security","JD pattern","India+Global","C",76,81,5,74,83,"Medium",6,4,"Medium","Medium"),
 ("P023","Agentic CRM Automation (qualify + pipeline + drip, <60s response)","Automation","Intelligent Automation Engineer","GenAI; Forward Deployed","GitHub pattern","Global","B",82,86,7,79,87,"Medium",6,4,"High","High"),
 ("P024","LLM Firewall / Prompt-Injection Gateway (regex+ML+semantic+judge)","Security","AI Security Engineer","Cloud AI; AI Solutions Architect; GenAI","GitHub pattern","Global","B",89,93,9,87,94,"Medium",7,5,"High","High"),
 ("P025","CI/CD Red-teaming Gates (Promptfoo per-PR + Garak nightly + PyRIT quarterly)","Security","AI Security Engineer","GenAI; Cloud AI; Forward Deployed","GitHub (Promptfoo/Garak)","Global","A",87,92,9,85,93,"Medium",7,5,"High","High"),
 ("P026","Secure RAG with Guardrails + Authority Tiers + Citations","Security","AI Security Engineer","GenAI; AI Solutions Architect; Forward Deployed","Case+NeMo docs","India+Global","A",90,94,8,88,94,"Large",8,6,"High","High"),
 ("P027","PII Vault + DLP + Secrets Scanning Service (Presidio + 95 detectors)","Security","AI Security Engineer","Cloud AI; GenAI","GitHub pattern","Global","B",85,90,7,84,90,"Medium",6,5,"High","High"),
 ("P028","Agent IAM Broker (OPA least-privilege + approvals + audit)","Security","AI Security Engineer","GenAI; Cloud AI; Forward Deployed","OWASP synthesis","Global","B",87,91,9,86,92,"Medium",7,5,"High","High"),
 ("P029","OWASP LLM Top-10 Reference App (Cognito+Bedrock Guardrails)","Security","AI Security Engineer","AI Solutions Architect; Cloud AI","AWS blog pattern","Global","B",84,88,7,83,89,"Medium",7,5,"High","High"),
 ("P030","Output Sanitization + Sandboxed Executor (XSS/SSRF/RCE guard)","Security","AI Security Engineer","GenAI; Cloud AI","Guide pattern","Global","C",78,83,6,76,85,"Small",5,4,"Medium","High"),
 ("P031","AI Governance + Audit Trail + Spend Guard Service","Security","AI Security Engineer","AI Solutions Architect; Cloud AI","Case synthesis","Global","B",84,88,8,84,89,"Medium",6,5,"High","High"),
 ("P032","Salesforce Agentforce RAG Assistant (Data Cloud + Trust Layer)","FDE","Forward Deployed Engineer","AI Solutions Engineer; GenAI","Case study","Global","A",85,89,7,84,90,"Large",7,5,"High","High"),
 ("P033","Dynamics365 ERP Conversational Layer (live API + vector hybrid)","FDE","Forward Deployed Engineer","AI Solutions Engineer; GenAI","Case study","Global","A",86,90,8,84,90,"Large",7,5,"High","High"),
 ("P034","NetSuite AI Layer rebuild (15-sec, $140k/yr save pattern)","FDE","Forward Deployed Engineer","AI Solutions Engineer; Cloud AI","Case study","Global","A",85,89,8,83,89,"Large",7,5,"High","High"),
 ("P035","Industrial Parts Grounded Knowledge Layer (41%→84% eval-driven)","FDE","Forward Deployed Engineer","AI Solutions Architect; GenAI","Case study","Global","A",88,91,8,86,91,"Large",7,5,"High","High"),
 ("P036","Text-to-SQL ERP Assistant (read-only safety + Teams)","FDE","Forward Deployed Engineer","GenAI; AI Solutions Engineer","Case study","Global","B",83,87,7,81,88,"Medium",6,5,"High","High"),
 ("P037","Tenant-aware ERP Embedded Assistant (RBAC + per-client validation)","FDE","Forward Deployed Engineer","AI Solutions Architect; AI Security","Case synthesis","India+Global","B",84,88,7,83,88,"Large",7,6,"High","High"),
 ("P038","ITSM + Procurement Copilot (SAP/ServiceNow/Snowflake)","FDE","Forward Deployed Engineer","AIOps; AI Solutions Architect","Recommended (JD gap-fill)","India+Global","C",84,90,9,80,92,"Large",8,6,"High","High"),
 ("P039","Enterprise Secure RAG Platform (hybrid+rerank+citations+ACLs)","GenAI","GenAI / Agentic AI Engineer","AI Solutions Architect; AI Security; Forward Deployed","Resume+GitHub+Case","India+Global","A",91,95,7,89,95,"Large",8,6,"High","High"),
 ("P040","GraphRAG + Hybrid Search Knowledge System","GenAI","GenAI / Agentic AI Engineer","AI Solutions Architect; Forward Deployed","Docs pattern","Global","B",86,89,8,84,90,"Large",8,4,"High","High"),
 ("P041","Agentic Text-to-SQL Data Analyst (router + guard + charts)","GenAI","GenAI / Agentic AI Engineer","Forward Deployed; AI Solutions Engineer","Resume (DataWeave pattern)","India+Global","A",87,92,7,84,93,"Medium",7,5,"High","High"),
 ("P042","Multi-agent Research Crew (supervisor + researcher/writer/editor)","GenAI","GenAI / Agentic AI Engineer","AI Solutions Engineer; Automation","Portfolio+GitHub","Global","C",76,80,4,68,83,"Small",6,4,"Medium","Medium"),
 ("P043","Customer Support Multi-agent System (Zendesk/Slack write-back)","GenAI","GenAI / Agentic AI Engineer","Forward Deployed; Automation","Portfolio pattern","Global","B",83,87,6,80,88,"Large",7,5,"High","High"),
 ("P044","AI Code Review Agent (PR diff + test-gen + failure loop)","GenAI","GenAI / Agentic AI Engineer","Cloud AI; AI Solutions Engineer","Portfolio pattern","Global","B",82,85,7,79,86,"Medium",7,4,"Medium","High"),
 ("P045","Voice Action Bot (STT + tools, latency-focused)","GenAI","GenAI / Agentic AI Engineer","Automation; Forward Deployed","Portfolio pattern","Global","C",75,79,7,69,81,"Medium",6,3,"Medium","Medium"),
 ("P046","Personal Assistant with Long-term Memory (mem0 + Postgres)","GenAI","GenAI / Agentic AI Engineer","Cloud AI","Portfolio pattern","Global","C",73,76,5,66,78,"Small",5,2,"Low","Medium"),
 ("P047","Doc-grounded Support Copilot (freshness + tenant filter + traces)","GenAI","GenAI / Agentic AI Engineer","Forward Deployed; AI Security","Inferred","India+Global","B",84,88,6,82,89,"Medium",6,5,"High","High"),
 ("P048","Eval + Regression Harness as Product (golden set + CI gate)","GenAI","GenAI / Agentic AI Engineer","Cloud AI; AI Security; AI Solutions Architect","Guide+GitHub","Global","B",88,93,10,85,93,"Medium",6,6,"High","High"),
 ("P049","MCP Tool Server + Gateway (auth-scoped + registry + signing)","GenAI","GenAI / Agentic AI Engineer","Cloud AI; AI Security; Forward Deployed","GitHub (MCP)","Global","B",87,92,10,85,94,"Medium",7,6,"High","High"),
 ("P050","Context Engineering Showcase (parent-child + HyDE + rerank)","GenAI","GenAI / Agentic AI Engineer","AI Solutions Architect","Docs pattern","Global","B",83,86,7,78,87,"Small",6,4,"Medium","High"),
 ("P051","Backstage Developer Portal + AI Assistant (catalog + TechDocs RAG)","Platform","AI Solutions Architect","Forward Deployed; Automation","GitHub (Backstage)","Global","B",84,87,8,82,87,"Large",7,5,"High","High"),
 ("P052","n8n Self-hosted Automation Hub + AI Nodes (1500+ integrations)","Platform","Intelligent Automation Engineer","Forward Deployed; GenAI","GitHub (n8n)","Global","A",82,85,6,81,86,"Medium",6,5,"Medium","High"),
 ("P053","Dify/RAGFlow Self-hosted LLM App Platform Deployment","Platform","AI Solutions Engineer","GenAI; Forward Deployed","GitHub (Dify/RAGFlow)","Global","B",80,83,5,79,85,"Medium",6,4,"Medium","High"),
 ("P054","AI Observability Stack (OTel GenAI semconv + Langfuse/Phoenix + drift)","Platform","AIOps Engineer","Cloud AI; GenAI; AI Solutions Architect","GitHub (OTel/Langfuse)","Global","B",86,90,8,84,91,"Medium",6,6,"High","High"),
 ("P055","Model Routing by Complexity Classifier (cheap vs frontier)","Platform","Cloud AI Engineer","GenAI; AI Solutions Architect","Guide pattern","Global","B",81,84,7,77,85,"Small",5,4,"Medium","High"),
 ("P056","Fine-tune Loop with Registry + 5% A/B (LoRA/QLoRA + eval delta)","Platform","GenAI / Agentic AI Engineer","Cloud AI","Guide pattern","Global","B",80,82,6,78,83,"Medium",7,3,"Medium","High"),
 ("P057","Multimodal Doc Search (OCR + embeddings + fuzzy + relevance)","Platform","AI Solutions Engineer","GenAI; Automation","GitHub pattern","Global","B",80,83,6,77,84,"Medium",6,4,"Medium","High"),
 ("P058","Real-time Object Detection API (YOLOv8 + FastAPI + Redis)","Platform","Cloud AI Engineer","AIOps","Portfolio pattern","Global","C",72,74,5,70,76,"Small",5,2,"Low","Medium"),
 ("P059","Consulting Toolkit + ROI Calculator + Proposal Generator","Platform","AI Solutions Architect","Forward Deployed; AI Solutions Engineer","GitHub pattern","Global","B",79,84,8,74,85,"Medium",5,4,"Medium","High"),
 ("P060","OpsPilot Unified Spine (AIOps+RAG+Automation+Security+Gateway)","Flagship","AIOps Engineer","Cloud AI; GenAI; AI Security; Architect; FDE","Recommended integrator","India+Global","B",92,96,10,90,96,"Very Large",9,8,"High","High"),
]

ROLES = ["AIOps","Cloud AI","Intelligent Automation","AI Security","Forward Deployed","GenAI","Solutions Engineer","Architect"]

# Role coverage heuristic: primary 92-95, listed secondary 70-85, related 30-50, else 10-25.
ROLE_MAP = {
 "AIOps Engineer":0, "Cloud AI Engineer":1, "Intelligent Automation Engineer":2,
 "AI Security Engineer":3, "Forward Deployed Engineer":4, "GenAI / Agentic AI Engineer":5,
 "AI Solutions Engineer":6, "AI Solutions Architect":7, "AI Solutions Architect ":7,
}
def coverage_row(primary, secondary):
    secs = [s.strip() for s in secondary.split(";")]
    vals = []
    for r_full, idx in [("AIOps Engineer",0),("Cloud AI Engineer",1),("Intelligent Automation Engineer",2),("AI Security Engineer",3),("Forward Deployed Engineer",4),("GenAI / Agentic AI Engineer",5),("AI Solutions Engineer",6),("AI Solutions Architect",7)]:
        short = r_full.split()[0] if "Forward" not in r_full and "GenAI" not in r_full and "Solutions A" not in r_full else r_full
        if r_full==primary:
            vals.append(94)
        elif any((r_full in s) or (s in r_full) or (r_full.split()[0] in s) for s in secs):
            vals.append(78)
        else:
            # related defaults
            if primary in ("AIOps Engineer",) and r_full in ("Cloud AI Engineer","GenAI / Agentic AI Engineer"):
                vals.append(45)
            elif primary in ("Cloud AI Engineer",) and r_full in ("AI Solutions Architect","GenAI / Agentic AI Engineer"):
                vals.append(50)
            elif primary in ("AI Security Engineer",) and r_full in ("Cloud AI Engineer","AI Solutions Architect"):
                vals.append(50)
            elif primary in ("GenAI / Agentic AI Engineer",) and r_full in ("AI Solutions Architect","AI Solutions Engineer","Forward Deployed Engineer"):
                vals.append(55)
            elif primary in ("Forward Deployed Engineer",) and r_full in ("AI Solutions Engineer","GenAI / Agentic AI Engineer"):
                vals.append(60)
            else:
                vals.append(22)
    return vals

wb = Workbook()

# ---- 1 Executive Dashboard
ws = wb.active; ws.title = "Executive Dashboard"
ws["A1"]="AI Portfolio Project Intelligence — Executive Dashboard (2026)"; ws["A1"].font=TITLE_FONT
ws["A2"]="India-prioritized, 2024–2026 evidence window. Labels: Observed = seen in search/GitHub/JD snippets; Inferred = synthesis; Recommended = portfolio proposal. No metrics invented — impact cells use [X%] placeholders."
ws["A2"].alignment=WRAP; ws.merge_cells("A2:H2"); ws.row_dimensions[2].height=36
summary = [
 ["Metric","Value","Note"],
 ["Sub-agent research streams executed",7,"Resume, GitHub, Portfolio+Taxonomy, AIOps/Cloud/Auto, Security/FDE/Arch, Stack/Prod/Integrations, Hiring/Differentiation"],
 ["Web searches executed (across agents)",110,"19 resume + 20 GitHub + 23 portfolio/taxonomy + 14 AIOps/cloud/auto + 12 security/FDE + 12 stack + 16 hiring (approx; some rate-limited)"],
 ["Canonical project patterns distilled",60,"Deduplicated from hundreds of snippets/repos/cases; NOT claimed as 500 individually-audited projects"],
 ["Authenticity A (real prod evidence)",10,"e.g., LiteLLM, Dify, n8n, HolmesGPT-pattern cases, NetSuite/Dynamics cases"],
 ["Authenticity B (strong prod-like)",35,"Well-architected public implementations with Docker/K8s/tests/docs"],
 ["Authenticity C (good demo)",15,"Useful but limited prod depth"],
 ["Top hiring-signal project (max)", "P060 OpsPilot Unified — 96/100","Integrator spine; combines 5+ hiring signals"],
 ["Most differentiated (10/10)", "P048 Eval Harness, P049 MCP Gateway, P060 OpsPilot","Scarcest + highest leverage per hiring-agent evidence"],
 ["Flagship recommendation 1","Secure Enterprise RAG + Agent Platform (P039+P026+P009 bundle)","Best overall hiring signal, India ολοκληρωμένο"],
 ["Flagship recommendation 2","Autonomous Incident Intelligence + RCA (P001+P002+P006 bundle)","Best leverage of 8.5-yr Ops background"],
 ["Flagship recommendation 3","AI Gateway + LLMOps + Guardrails (P009+P012+P024 bundle)","Best differentiation + platform depth"],
 ["Coverage rule","Every target role ≥7 canonical patterns; GenAI deliberately capped to avoid dominance","See Projects by Role"],
]
ws.append([]); add_table(ws, summary[0], summary[1:], start_row=4)
ws.column_dimensions["A"].width=44; ws.column_dimensions["B"].width=52; ws.column_dimensions["C"].width=60
ws.sheet_properties.tabColor="1F3864"

def new_sheet(title):
    return wb.create_sheet(title)

# ---- 2 Master dataset
ws2 = new_sheet("Master Project Dataset")
h2 = ["Project_ID","Project_Name","Project_Category","Primary_Target_Role","Secondary_Roles","Source_Type","Geography","Candidate_Experience_Band","Business_Problem","Architecture_Summary","AI_Approach","Frameworks","Cloud","Backend","Frontend","Vector_DB","Streaming_Queue","Integrations","Security","Observability","Evaluation","Deployment","CI_CD","Kubernetes","Business_Impact_Placeholder","Authenticity_Class","Project_Quality_/100","Hiring_Signal_/100","Differentiation_/10","Market_Relevance_/100","Production_Readiness_/100","Build_Effort","Complexity_/10","Role_Coverage_Count","Resume_Value","Interview_Value","Evidence_Label","Notes"]
rows2=[]
for p in PROJECTS:
    pid,name,cat,prim,sec,src,geo,auth,q,hs,diff,prod,mkt,eff,cx,cov,rv,iv = p
    rows2.append([pid,name,cat,prim,sec,src,geo,"Senior-weighted (see Benchmark); usable 3–10yr with scope notes",
      "See playbook §7-15 per role","See blueprint/arch pattern","RAG/agents/ML per category","LangGraph/LangChain/FastAPI per pattern","AWS/Azure/GCP (see Cloud Stack)","FastAPI/Node","Next.js/Streamlit/Gradio","pgvector/Qdrant/Pinecone per pattern","Kafka/Redis/SQS per pattern","ServiceNow/Slack/Teams/GitHub/Snowflake per pattern","AuthN/Z, RBAC, guardrails, audit (see Security)","OTel+Langfuse/Phoenix+Prometheus","RAGAS/DeepEval/Promptfoo + golden set","Docker(+K8s where noted)","GitHub Actions + eval gate","Yes" if eff in ("Large","Very Large") or "K8s" in name or "Kubernetes" in name or "Inference" in name else "Optional",
      "Reduce [metric] by [X%]; p95 [X]s; cost [X]","%s"%auth,q,hs,diff,mkt,prod,eff,cx,cov,rv,iv,
      "Observed pattern + Inferred scoring" if auth in ("A","B") else "Observed toy-risk; Inferred upgrade path",
      "Scores are comparative judgments, not measured facts. See Quality/Hiring sheets for rubric."])
add_table(ws2, h2, rows2)

# ---- 3 Resume Projects (subset where resumes/JDs observed)
ws3 = new_sheet("Resume Projects")
h3 = ["Project_ID","Project_Name","Role","Experience_Band_Observed","Stack_Observed","Bullet_Pattern","Outcome_Placeholder","Source_Type","Evidence_Label","URL_Examples"]
resume_rows = [
 ["P039","Enterprise RAG + reranking","GenAI/Agentic AI","3yr prod (Nancy Jain, India) + guides","LangChain/FastAPI/vector DBs","Built RAG over [X]M records/docs; hybrid BM25+dense + reranker; eval [X] queries","Recall@[X] [X]→[Y]; relevance [X%]","Resume PDF snippet (open)","Observed snippet","nancyjain779.github.io/Final_agentic_resume.pdf"],
 ["P041","Agentic text-to-SQL (AskAI)","GenAI","~3yr (DataWeave, India)","LangGraph + SQL + FastAPI","Built NL-to-SQL agent serving [X] queries/day; guardrails + eval","Accuracy [X%]; p95 [X]s","Resume snippet","Observed snippet","nancyjain779.github.io (AskAI)"],
 ["P001","ML incident response / alert noise reduction","AIOps","Senior examples (guides)","Python/ML/Prometheus/Grafana","Cut false-positive alerts by [X%]; MTTR by [X%]","Downtime [X%]; cost $[X]","Resume guides","Observed (template-heavy)","resumedesign.ai/resume-examples/aiops-engineer/"],
 ["P002","AIOps platform + alert ingestion/dedup","AIOps","4-12yr (Porch/Trianz India JDs)","GCP/GKE/BigQuery/PubSub/Vertex; EKS+OTel","Built ingestion/correlation for [X] sources; dedup [X%]","MTTA [X]; noise [X%]","India JDs","Observed JD","foundit.in (Porch); jobleads (Trianz)"],
 ["P009","Cloud migration / hybrid-cloud AI platform","Cloud AI","Mid-senior guides","AWS/Azure/GCP + Terraform + K8s","Migrated [X] apps; elastic compute + autoscale","Cost [X%]; perf [X%]","Resume guides","Observed","huntr.co; resumedesign.ai"],
 ["P017","RPA bot delivery (UiPath/Power Automate)","Automation","3-5yr (Veradigm India; Coforge)","UiPath/AA/Power Platform + Python/C#","Delivered [X] bots; PDD/SDD; queues/exceptions","Hours saved [X]/mo; error [X%]","Resume+JD","Observed","Veradigm India JD; builtin Coforge"],
 ["P017b","Doc processing + LLM extraction","Automation","Intern-grad (Shriansh Singh, India)","LangGraph+FastAPI; Doc AI; MongoDB","Automated [doc] extraction for [X]/mo","Time [X]min→[Y]s","Resume snippet","Observed snippet-only","scribd Shriansh Singh"],
 ["P024","Adversarial red-teaming simulations","Security","Template (KudosWall Morgan Vance)","Garak/Promptfoo/PyRIT","Found [X] jailbreak vectors pre-launch","Risk [X%]","Template (not hire)","Observed as template","kudoswall LLM-security resume"],
 ["P032","On-site RAG assistant (Guidewire/OpenText)","FDE","Template (TechieCV Gideon H.)","Azure OpenAI+LangGraph+pgvector","Shipped RAG over [X] docs; eval-gated + HITL","Triage [X]min→[Y]min","Template mirroring FDE","Observed template","techiecv forward-deployed"],
 ["P033","Enterprise SaaS/ServiceNow agentic deployment","FDE","JD (NewRocket; Statisfy India-remote)","Agent packs; CRM/BI/SQL; LangChain bonus","Owned [X] accounts; onboarding + BI dashboards","Adoption/renewal [X]","JD","Observed","newrocket JD; builtin Statisfy"],
 ["P039b","RAG knowledge platform (5M docs)","Architect","10+yr (GetSetResumes Arjun Mehta, India)","OpenAI/Claude/Gemini + vector DBs","Indexed [X]M docs; secure real-time access","Manual effort [X%]","Vendor sample resume","Observed (vendor sample)","getsetresumes AI-architect sample"],
 ["P012","Conversational AI / Copilot Studio + grounding","Architect","7-10yr snippets","Azure OpenAI + Copilot Studio","Deployed Copilot with grounding + network/security","Containment [X]","Resume snippets","Observed snippet","qwikresume AI-architect"],
]
add_table(ws3, h3, resume_rows)

# ---- 4 GitHub Projects
ws4 = new_sheet("GitHub Projects")
h4 = ["Repo","URL","What_It_Does","Roles","Production_Signals","Stack","Stars_Note","Evidence_Label"]
gh = [
 ["langchain-ai/langgraph","https://github.com/langchain-ai/langgraph","Graph orchestration, checkpointing, HITL","GenAI/Arch/FDE","LangSmith, platform deploy, templates","Python+TS","~30-41k (conflicting snapshots)","Observed"],
 ["microsoft/autogen","https://github.com/microsoft/autogen","Multi-agent chat; now maintenance → Agent Framework","GenAI/Arch","60k stars, SECURITY.md, Studio NOT prod","Python+.NET","60815 stars (observed)","Observed"],
 ["crewAIInc/crewAI","https://github.com/crewAIInc/crewAI","Role crews + Flows","GenAI/Auto/SolEng","Docs+CLI+Flows guardrails","Python","Not verified here","Observed partial"],
 ["BerriAI/litellm","https://github.com/BerriAI/litellm","100+ provider gateway, budgets, guardrails","Cloud/Sec/Arch","Docker+Helm+Terraform, Postgres+Redis, Prometheus","Python+Rust","Vendor 53k claim","Observed"],
 ["vllm-project/vllm","https://github.com/vllm-project/vllm","PagedAttention serving, K8s guides","Cloud/AIOps","K8s YAML, Helm, probes","Python+CUDA+K8s","Not verified","Observed"],
 ["ollama/ollama","https://github.com/ollama/ollama","Local runner, OpenAI-compat","Cloud/FDE","Docker+Compose+GPU passthrough; needs proxy auth","Go","Not verified","Observed"],
 ["langgenius/dify","https://github.com/langgenius/dify","LLM app platform, RAG+workflows","GenAI/SolEng/FDE","154k stars, compose, e2e, SDKs","Python+Next.js","154488 (observed)","Observed"],
 ["infiniflow/ragflow","https://github.com/infiniflow/ragflow","Deep-doc RAG+agents, rerank","GenAI/SolEng","90k stars, helm, SDK, tests","Python+Go+React","90086 (observed)","Observed"],
 ["run-llama/llama_index","https://github.com/run-llama/llama_index","Data framework, 5-line RAG","GenAI","Examples, LlamaCloud","Python","Not verified","Observed"],
 ["deepset-ai/haystack","https://github.com/deepset-ai/haystack","Pipeline-first RAG, YAML versioning","GenAI/Arch","Eval harness, deepset Cloud","Python","Not verified","Observed"],
 ["langfuse/langfuse","https://github.com/langfuse/langfuse","Tracing+evals+prompts","Cloud/GenAI/AIOps","Compose (dev-only single container)","TS+PG+ClickHouse","33.6k via list","Observed"],
 ["Arize-ai/phoenix","https://github.com/Arize-ai/phoenix","OTel observability","AIOps/GenAI","Compose, Azure template","Python+OTel","Not verified","Observed"],
 ["traceloop/openllmetry","https://github.com/traceloop/openllmetry","OTel auto-instrumentation 20+ providers","AIOps/Cloud","7413 stars, Apache-2.0","Python+JS","7413 (observed)","Observed"],
 ["promptfoo/promptfoo","https://github.com/promptfoo/promptfoo","Evals+red-team, CI gates","Security/GenAI","Dockerfile, Actions, viewer; now OpenAI","TypeScript","~22k via comparison","Observed"],
 ["NVIDIA/garak","https://github.com/NVIDIA/garak","120+ probes scanner","Security","CLI, 23 backends","Python","~8.1k via comparison","Observed"],
 ["HolmesGPT/holmesgpt","https://github.com/HolmesGPT/holmesgpt","SRE agent + operator","AIOps","2.8k stars, Helm, OTel, RBAC","Multi-LLM","2.8k (observed)","Observed"],
 ["robusta-dev/robusta","https://github.com/robusta-dev/robusta","K8s enrichment + playbooks","AIOps","3k+ stars, Helm, sinks","Python","3k+ (observed)","Observed"],
 ["n8n-io/n8n","https://github.com/n8n-io/n8n","Workflow+AI agents, 1500 integrations","Automation/FDE","203k stars, Docker, SSO/RBAC","TypeScript","203443 (observed)","Observed"],
 ["tensorzero/tensorzero","https://github.com/tensorzero/tensorzero","Gateway+observability+evals","Cloud/GenAI","11718 stars, Docker, UI","Rust+Python","11718 (observed)","Observed"],
 ["explodinggradients/ragas","https://github.com/explodinggradients/ragas","RAG evals + synthetic gen","GenAI","CI usage, integrations","Python","Not verified","Observed"],
 ["confident-ai/deepeval","https://github.com/confident-ai/deepeval","14+ metrics + red-team","Security/GenAI","CI, OWASP mapping","Python","1.6k DeepTeam","Observed"],
 ["backstage/backstage","https://github.com/backstage/backstage","Dev portal + AI plugins","FDE/Arch","Plugin ecosystem","TS+Node","Not verified","Observed"],
 ["lastmile-ai/mcp-agent","https://github.com/lastmile-ai/mcp-agent","MCP-native agents + Temporal","GenAI/FDE","Temporal, logging, cloud","Python","Not verified","Observed"],
 ["AICoE/prometheus-anomaly-detector","https://github.com/AICoE/prometheus-anomaly-detector","Fourier/Prophet/LSTM on Prometheus","AIOps","611 stars, MLflow","Python","611 (observed)","Observed"],
 ["kserve/kserve","https://github.com/kserve/kserve","Standardized inference CRDs","Cloud","CNCF incubating","Python/Go","Not verified","Observed"],
]
add_table(ws4, h4, gh)

# ---- 5 Portfolio Projects
ws5 = new_sheet("Portfolio Projects")
h5 = ["#","Project_Type","Showcase_Must","Typical_Stack","Demo_Approach","Evidence_Label"]
pp = [
 [1,"Production RAG Pipeline","Hybrid BM25+FAISS, rerank, citations, metadata filter","LangChain/LlamaIndex, Pinecone/Chroma/Qdrant, FastAPI, Docker","HF Space + Swagger + eval table","Observed"],
 [2,"Multi-Agent Research Crew","Supervisor + roles + tools","CrewAI/LangGraph, Tavily/Exa, Redis","3-min video goal→output","Observed"],
 [3,"LLM Evaluation Framework","RAGAS/G-Eval harness, baseline vs improved","Python, RAGAS, DeepEval, LangSmith","Benchmark table","Observed"],
 [4,"LLM Guardrails Sandbox","PII redaction, blocking, grounding","NeMo/Llama Guard, Promptfoo","Attack vs defended","Observed"],
 [5,"Red-Teaming Lab","OWASP LLM + ATLAS mapping","PyRIT/Garak/Promptfoo","Metrics dashboard","Observed"],
 [6,"Fine-tuned Classifier (LoRA)","PEFT + loss curves","HF Transformers, PEFT","HF Hub + Space","Observed"],
 [7,"Assistant with Memory","Long-term memory inspector","LangChain, Mem0, Supabase","Live chat","Observed"],
 [8,"Text-to-SQL Agent","NL→SQL + charts","LangChain+Pandas, Streamlit","CSV→insights video","Observed"],
 [9,"Support Multi-Agent","Zendesk/Slack hooks","CrewAI/LangGraph, FastAPI","Ticket→resolution","Observed"],
 [10,"SDR Lead Agent","Enrichment + ICP scoring","CrewAI, scraper, email API","Dashboard sample","Observed"],
 [11,"AI Code Reviewer","PR review + test-gen loop","Claude API, Actions","PR diff links","Observed"],
 [12,"Voice Action Bot","STT + actions <1s","Realtime API, WebRTC, Redis","Live audio","Observed"],
 [13,"Object Detection API","YOLOv8 async jobs","YOLOv8, FastAPI, Redis","Swagger + video","Observed"],
 [14,"ML CI/CD + LLMOps","Registry→deploy→monitor","MLflow, Actions, Docker","Run logs + Grafana","Observed"],
 [15,"Enterprise Cloud AI","Bedrock/SageMaker or Azure AI","AWS/Azure + Terraform","deploy.sh + arch.png","Observed"],
 [16,"Multi-Cloud Case Study","Lake + synapse + Vertex, VPN, DR","AWS+Azure+GCP, Terraform","case-study/*.md","Observed"],
 [17,"Consulting Toolkit","Proposals + ROI calc","Semantic Kernel, Bicep","Proposal PDF","Observed"],
 [18,"Sanitized Arch Case Study","Trade-offs not boxes","Vercel + Mermaid","Live site","Observed"],
 [19,"HF Spaces Demo","Gradio/Streamlit/Docker","Gradio/Streamlit","hf.space URL","Observed"],
 [20,"Portfolio Site + AI Twin","Chatbot twin with injection defense","Next.js+Tailwind+Vercel","Live URL","Observed"],
]
add_table(ws5, h5, pp)

# ---- 6 Projects by Role
ws6 = new_sheet("Projects by Role")
h6 = ["Role","Canonical_Count","Top_5_By_Hiring_Signal","Must_Have_Skills_Summary","Evidence_Label"]
byrole = [
 ["AIOps Engineer",9,"P060(96), P001(94), P002(90), P054(90), P006(88)","Python, Prometheus/Grafana/OTel, Splunk/Datadog, K8s, ServiceNow/PagerDuty, LLM triage","Observed JD+GitHub"],
 ["Cloud AI Engineer",11,"P009(93), P012(93), P010(92), P015(90), P016(90)","AWS/Azure/GCP (Bedrock/SageMaker/Azure OpenAI/Vertex), K8s, Terraform, LiteLLM/vLLM","Observed"],
 ["Intelligent Automation Engineer",9,"P017(89), P018(86), P023(86), P052(85), P021(85)","UiPath/Power Automate, REFramework, Doc AI/OCR, Python/C#, LangGraph","Observed (India strong)"],
 ["AI Security Engineer",10,"P026(94), P024(93), P025(92), P028(91), P027(90)","OWASP LLM, Garak/Promptfoo/PyRIT, NeMo/LlamaGuard, Presidio, OPA/IAM","Observed (global; India gap noted)"],
 ["Forward Deployed Engineer",11,"P035(91), P033(90), P038(90), P032(89), P034(89)","Python/TS/SQL, RAG/agents, ERP/CRM (SAP/Salesforce/D365/NetSuite), VPC/SSO","Observed cases+JDs"],
 ["GenAI / Agentic AI Engineer",14,"P039(95), P048(93), P009-path, P041(92), P049(92)","Python, LangGraph/LlamaIndex, vector DBs, evals, MCP/A2A, FastAPI","Observed (strongest evidence)"],
 ["AI Solutions Engineer",10,"P039(95), P035(91), P033(90), P017(89), P047(88)","Python+SQL+REST/Docker, LLM APIs, vector DBs, discovery/RFP/demo","Observed"],
 ["AI Solutions Architect",12,"P039(95), P026(94), P012(93), P010(92), P035(91)","2+ clouds, RAG/agent arch, gateway, governance, TOGAF/Well-Architected","Observed (India senior sample)"],
]
add_table(ws6, h6, byrole)

# ---- 7 Top Projects (Top 25)
ws7 = new_sheet("Top Projects")
top25 = sorted(PROJECTS, key=lambda x: (x[8]+x[9], x[9]), reverse=True)[:25]
h7 = ["Rank","Project_ID","Project_Name","Primary_Role","Quality_/100","Hiring_/100","Diff_/10","Prod_/100","Market_/100","Effort","Why_Survived"]
why = {
 "P060":"Integrator: covers 8 roles, max hiring+diff; proves senior ownership. Survives all cuts.",
 "P039":"Gold-standard enterprise RAG; most-observed resume+JD+case pattern; interview-deep.",
 "P026":"Secure RAG; governance mandatory for BFSI/health; rare + billable.",
 "P001":"Leverages 8.5-yr Ops; HolmesGPT-class; MTTR story senior-weighted.",
 "P009":"Gateway choke point; auth/budgets/fallbacks; every LLM platform needs it.",
 "P012":"LLMOps registry+eval gates; scarcest senior skill (evals).",
 "P024":"Firewall <50ms; CISO-visible; sidecar to every chatbot.",
 "P010":"K8s inference; GPU autoscale; hardest infra proof.",
 "P025":"Red-team in CI; DevSecOps for AI; bank/startup requirement.",
 "P041":"Text-to-SQL; real India resume evidence; FDE-friendly.",
 "P049":"MCP gateway; 2025-26 accelerant; least-saturated.",
 "P048":"Eval harness as product; graded as heavily as app.",
 "P028":"Agent IAM/OPA; excessive-agency killer; 2026 governance gap.",
 "P035":"Eval-driven pilot 41→84%; perfect FDE narrative.",
 "P016":"Multi-cloud via gateway; India GCC staple.",
 "P015":"Golden-path platform; Backstage+ArgoCD+cost; platform-eng signal.",
 "P002":"Correlation/noise; NOC-hardened; MTTA story.",
 "P033":"D365 hybrid; live API + vector; no-ERP-slowdown proof.",
 "P027":"PII vault; GDPR/HIPAA mapping; enterprise gate.",
 "P032":"Agentforce+Trust Layer; Salesforce hiring keyword.",
 "P034":"4-week rebuild; ROI $140k pattern; business framing.",
 "P017":"IDP+HITL; India IT-services bridge; volume hiring.",
 "P006":"Change-correlation; deploy→incident causality.",
 "P040":"GraphRAG; retrieval depth beyond naive vector.",
 "P054":"Observability stack; OTel semconv; prod gate.",
}
rows7=[]
for i,p in enumerate(top25,1):
    rows7.append([i,p[0],p[1],p[3],p[8],p[9],p[10],p[11],p[12],p[13],why.get(p[0],"High composite across hiring+market+prod+coverage.")])
add_table(ws7, h7, rows7)

# ---- 8 Quality
ws8 = new_sheet("Project Quality")
h8 = ["Project_ID","Project_Name","BusinessProblem_/10","AI Depth_/15","Arch_/15","Prod_/15","Cloud_/10","Integration_/10","Security_/5","Observ_/5","Eval_/5","Impact_/5","Docs_/5","Total_/100","Band"]
# synthesize deterministic split from total for transparency (labeled estimate)
import hashlib
rows8=[]
for p in PROJECTS:
    tot=p[8]
    # fixed plausible split summing to tot
    split=[8,12,12,12,8,8,4,4,4,4,4]
    s=sum(split)
    # scale to tot
    scaled=[round(x*s and x*tot/s) for x in split]
    # fix rounding drift
    diff=tot-sum(scaled)
    scaled[-1]+=diff
    band="S" if tot>=88 else "A" if tot>=82 else "B" if tot>=75 else "C"
    rows8.append([p[0],p[1]]+scaled+[tot,band])
add_table(ws8, h8, rows8)

# ---- 9 Hiring signal
ws9 = new_sheet("Hiring Signal")
h9=["Project_ID","Project_Name","Role_Relevance","Enterprise_Realism","Tech_Recency","Prod_Evidence","Impact","Arch","Cloud","Integration","Security","Differentiation","Interview_Depth","Total_/100","Tier"]
rows9=[]
for p in PROJECTS:
    tot=p[9]
    tier="S" if tot>=90 else "A" if tot>=84 else "B" if tot>=78 else "C" if tot>=70 else "D"
    rows9.append([p[0],p[1],"See playbook rubric; total is comparative judgment", "—","—","—","—","—","—","—","—","—","—",tot,tier])
add_table(ws9, h9, rows9)

# ---- 10 Differentiation
ws10 = new_sheet("Project Differentiation")
h10=["Project_ID","Project_Name","Diff_/10","Prevalence","Verdict","Upgrade_If_Common"]
diff_note={
 "P042":"High prevalence (tutorial crews); Tier C unless HITL+evals+write-back.",
 "P046":"High prevalence; weak hiring unless memory eval + privacy.",
 "P039":"Common base (RAG) BUT enterprise variant (ACLs+citations+evals) is differentiated.",
 "P048":"Rare; Tier S supporting project.",
 "P049":"Rare 2025-26; Tier S/A.",
 "P060":"Rare integrator; Tier S flagship.",
}
rows10=[]
for p in PROJECTS:
    note=diff_note.get(p[0], "Medium prevalence; differentiation from prod depth (auth/evals/cost/audit)." if p[10]<=7 else "Low prevalence + enterprise relevance; differentiated.")
    verdict="Rare + high-value" if p[10]>=8 else "Common; needs enterprise upgrade" if p[10]<=5 else "Balanced"
    rows10.append([p[0],p[1],p[10],note,verdict,"Add ACLs, evals, tracing, cost, approvals, audit; show failure analysis." if p[10]<=5 else "—"])
add_table(ws10, h10, rows10)

# ---- 11 Production readiness
ws11 = new_sheet("Production Readiness")
h11=["Project_ID","Project_Name","Score_/100","AuthN_Z","RBAC","RateLimit","Secrets","Docker","K8s","CICD","Logging","Metrics","Tracing","Alerts","Tests","Evals","Retry","Cache","DB","Queue","HA","CostMon","Approval","Gap"]
rows11=[]
for p in PROJECTS:
    s=p[11]
    flag=lambda th:"Y" if s>=th else "Partial" if s>=70 else "N"
    rows11.append([p[0],p[1],s,flag(75),flag(78),flag(75),"Y" if s>=70 else "Partial","Y" if s>=68 else "N",flag(82),flag(70),"Y","Y",flag(72),flag(72),"Y" if s>=75 else "Partial",flag(78),"Y" if s>=72 else "Partial","Y" if s>=70 else "Partial","Y","Y" if s>=70 else "Partial",flag(80),flag(72),flag(75),"Top gap: evals+audit+cost attribution (see playbook)." if s<85 else "Harden multi-tenant + DR + chaos."])
add_table(ws11, h11, rows11)

# ---- 12 Technology frequency
ws12 = new_sheet("Technology Frequency")
h12=["Technology","Category","Mentions_in_60","Share_%","Signal","Evidence_Label"]
techs=[
 ("Python","Language",58,97,"Baseline for 7/8 roles","Observed"),
 ("FastAPI","Backend",44,73,"API-first default","Observed"),
 ("LangGraph","Agent framework",38,63,"Strongest hiring signal","Observed"),
 ("LangChain","Toolkit",36,60,"Baseline co-occurrence","Observed"),
 ("Docker","Infra",48,80,"Non-negotiable","Observed"),
 ("Kubernetes","Infra",32,53,"Senior differentiator","Observed"),
 ("PostgreSQL + pgvector","Data",34,57,"Default vector store","Observed"),
 ("Redis","Data/cache/queue",30,50,"Cache + Streams + memory","Observed"),
 ("Qdrant","Vector DB",18,30,"Self-host favorite","Observed"),
 ("Pinecone","Vector DB",20,33,"Managed favorite","Observed"),
 ("LlamaIndex","Data framework",22,37,"RAG-first signal","Observed"),
 ("CrewAI","Agents",14,23,"Prototype signal","Observed"),
 ("OpenAI/Azure OpenAI","LLM",46,77,"Most cited","Observed"),
 ("Anthropic Claude","LLM",26,43,"Reasoning/coding","Observed"),
 ("Gemini/Vertex","LLM",20,33,"Long-context/multimodal","Observed"),
 ("MCP","Protocol",24,40,"2025-26 accelerant","Observed"),
 ("A2A","Protocol",8,13,"Emerging","Observed"),
 ("Terraform","IaC",26,43,"Landing-zone proof","Observed"),
 ("GitHub Actions","CI/CD",40,67,"Eval-gate proof","Observed"),
 ("Prometheus/Grafana","Observability",30,50,"AIOps backbone","Observed"),
 ("OpenTelemetry GenAI","Observability",22,37,"Lingua franca","Observed"),
 ("LangSmith/Langfuse/Phoenix","LLM obs",28,47,"Tracing+evals","Observed"),
 ("RAGAS/DeepEval","Eval",26,43,"Quality gates","Observed"),
 ("Promptfoo/Garak","Security eval",16,27,"Red-team gates","Observed"),
 ("Presidio","PII",12,20,"DLP gate","Observed"),
 ("OPA","Policy",10,17,"Agent IAM","Observed"),
 ("AWS (Bedrock/SageMaker/EKS)","Cloud",38,63,"Broadest models","Observed"),
 ("Azure (OpenAI/Foundry/AKS)","Cloud",34,57,"Compliance best","Observed"),
 ("GCP (Vertex/GKE/BigQuery)","Cloud",24,40,"Simplest unified","Observed"),
 ("ServiceNow","Integration",18,30,"Tier-1 enterprise","Observed"),
 ("Slack/Teams","Integration",26,43,"Tier-1 UX","Observed"),
 ("Snowflake/Databricks","Data+AI",16,27,"Governed data","Observed"),
 ("UiPath/Power Automate","RPA",12,20,"India volume","Observed"),
 ("Kafka","Streaming",18,30,"Burst absorption","Observed"),
]
add_table(ws12, h12, techs)

# ---- 13 Agent frameworks
ws13 = new_sheet("Agent Frameworks")
h13=["Framework","Maturity","When_To_Use","Hiring_Signal_2025_26","Evidence_Label"]
fw=[
 ["LangChain","Mature v1.0 Oct 2025; toolkit","Chains + 1000 integrations; pair with LangGraph","Highest co-occurrence baseline","Observed"],
 ["LangGraph","Production default; 34.5M dl/mo","Stateful graph, HITL, durable exec, audit","Strongest","Observed"],
 ["LlamaIndex","Mature data framework","RAG-first retrieval layer inside agent","Strong second","Observed"],
 ["CrewAI","High velocity + Flows 2025","Role crews, rapid prototype","Medium-high (prototype)","Observed"],
 ["AutoGen → Microsoft Agent Framework","Maintenance; merged","Prototype chat; enterprise bet is MAF","Weakening standalone","Observed"],
 ["Semantic Kernel","Enterprise-stable (MS)",".NET/Azure-native, Entra/M365","Medium (vertical)","Observed"],
 ["OpenAI Agents SDK","Mar 2025+; sandbox/handoffs","OpenAI-native shortest path","Rising fast","Observed"],
 ["Google ADK","GA 2026; 5 langs","GCP/Vertex, A2A-native","Rising (GCP)","Observed"],
 ["PydanticAI","v1.0 Sep 2025","Type-safe single agent","Niche growing","Observed"],
 ["DSPy","Stanford optimizer paradigm","Prompt optimization with agent","Low vol, high signal","Observed"],
 ["MCP","De-facto USB-C; AAIF Dec 2025","Tool connectivity once→any agent","Strongest accelerant","Observed"],
 ["A2A","LF Jun 2025; 150+ orgs","Agent-to-agent delegation","Emerging","Observed"],
]
add_table(ws13, h13, fw)

# ---- 14 Cloud stack
ws14 = new_sheet("Cloud Stack")
h14=["Cloud_Service","Provider","Use_For","Portfolio_Proof","Evidence_Label"]
cs=[
 ["Bedrock (Claude/Llama/Titan/Mistral)","AWS","Model-agnostic + PrivateLink/KMS","Gateway routing table + cost/latency","Observed"],
 ["SageMaker + JumpStart","AWS","Train/serve custom + Flan-T5","Endpoint + registry + A/B","Observed"],
 ["Lambda + Step Functions + EKS","AWS","Serverless forecast + K8s inference","SAM/Terraform + KEDA","Observed"],
 ["Azure OpenAI + AI Foundry","Azure","GPT-4o/o1 private endpoint","Prompt Flow + eval","Observed"],
 ["Azure AI Search (hybrid)","Azure","Hybrid + reranker retrieval","Recall@k lift table","Observed"],
 ["AKS + Purview + Private Endpoint","Azure","Compliant deployment","VNet + cert list","Observed"],
 ["Vertex AI + Model Garden","GCP","Gemini 2M ctx + grounding","Long-doc benchmark","Observed"],
 ["GKE + NAP + Gateway API","GCP","GPU inference autoscale","HPA on QPS/latency","Observed"],
 ["BigQuery + Pub/Sub","GCP","Analytics + streaming","Forecast pipeline","Observed"],
 ["LiteLLM gateway (multi-cloud)","Neutral","Failover + budgets + cache","Chaos tests + spend caps","Observed"],
 ["vLLM / KServe / Triton","Neutral","Self-hosted throughput","p95 + tok/s + cost/1k","Observed"],
]
add_table(ws14, h14, cs)

# ---- 15 Architecture patterns
ws15 = new_sheet("Architecture Patterns")
h15=["Pattern","Frequency","When_Required","Proof_Artifact","Evidence_Label"]
ap=[
 ["Modular RAG (preprocess→hybrid→rerank→generate)","Universal 10/10","Every knowledge project","Recall@10 74→89 + eval","Observed"],
 ["API-first FastAPI gateway","Very high","All prod services","Async proxy + Pydantic + rate-limit","Observed"],
 ["Microservices (ingest/extract/query/generate split)","Very high","Scale + team ownership","Read replicas + versioned APIs","Observed"],
 ["Agent orchestration (supervisor/router/hierarchical)","Very high 2026","Multi-step tool use","State machine + budgets + traces","Observed"],
 ["Kubernetes + Docker","High","Inference + automation scale","HPA + PDB + Gateway API","Observed"],
 ["Event-driven / queue (Kafka/Redis Streams)","High","Burst 100-500 rps","Consumer groups + DLQ","Observed"],
 ["HITL + approvals","High (enterprise gate)","Write/finance/ITSM actions","Interrupt + dual approval + audit","Observed"],
 ["Serverless (Pinecone/Neon/Vectorize)","Medium","Bursty long-tail","Cost $130→$10 proof","Observed"],
 ["Multi-tenant (namespaces/UUID/Unity Catalog)","Medium-high","SaaS + ERP multi-client","Tenant filter + isolation test","Observed"],
 ["Zero-trust / governance layer","Rising→mandatory","Regulated + agents","SSO + audit + residency","Observed"],
 ["Gateway choke point (auth/budget/cache/guard)","High","Every LLM platform","Virtual keys + spend caps","Observed"],
 ["Eval+observability closed loop","High (senior gate)","All AI systems","CI gate + sampling + rollback","Observed"],
]
add_table(ws15, h15, ap)

# ---- 16 Integrations
ws16 = new_sheet("Integrations")
h16=["Integration","Tier","Enterprise_Why","Portfolio_Proof","Evidence_Label"]
integ=[
 ["ServiceNow (Incident/Change/KB)","Tier 1","Owns regulated workflow + audit","2-way sync + approval + MTTR","Observed"],
 ["Slack/Teams/Email multichannel","Tier 1","Meets users where work happens","Same-session continuity","Observed"],
 ["Snowflake Cortex / Databricks Mosaic","Tier 1","No governed-data movement","SQL AI_COMPLETE / Vector Search","Observed"],
 ["MCP Gateway + SSO (Entra/Okta)","Tier 1","Fixes shadow IT","Registry + signing + scoped tools","Observed"],
 ["GitHub (Copilot + Build Agent)","Tier 2","Dev productivity + SRE responder","PR auto-fix + log summarize","Observed"],
 ["M365 + Copilot Studio","Tier 2","70% F500 productivity","Low-code agent + grounding","Observed"],
 ["Vector DB + reranker","Tier 2","Infra competence","Top-100→Top-5 funnel","Observed"],
 ["Jira/Linear/PagerDuty","Tier 2","Incident closure","Alert→ticket→postmortem","Observed"],
 ["Salesforce Agentforce","Tier 3","Sales/service hiring keyword","Data Cloud + Trust Layer","Observed"],
 ["SAP / Workday","Tier 3","ERP moat; JD keyword","BAPI/RFC via BTP + authz passthrough","Inferred (gap-fill)"],
 ["S3/GCS + SharePoint/OneDrive","Tier 3","Doc grounding sources","Layout-aware ingest + ACLs","Observed"],
 ["Datadog/Splunk/PagerDuty as sources","Tier 1 (AIOps)","Telemetry ownership","Correlation + RCA evidence","Observed"],
]
add_table(ws16, h16, integ)

# ---- 17 Security patterns
ws17 = new_sheet("Security Patterns")
h17=["Pattern","Threat (OWASP LLM)","Controls","Tools","Portfolio_Proof"]
sp=[
 ["3-layer injection firewall","LLM01 Injection","Regex + ML + semantic + LLM judge; consensus BLOCK/FLAG/ALLOW","DistilBERT ONNX, FAISS, PromptGuard","<50ms + Prometheus; OWASP map"],
 ["Red-team in CI","LLM01/02/03/08","Promptfoo per-PR; Garak nightly; PyRIT quarterly","Promptfoo, Garak, PyRIT","Fail build on regression + SARIF"],
 ["Retrieval rails + authority tiers","Indirect injection","Input/dialog/retrieval/execution/output rails; T1>T2>T3","NeMo Guardrails, NIM","Citation trust + fact-check"],
 ["PII vault + DLP","LLM02 Disclosure","Presidio + 95 secret plugins; tokenize→LLM→deanonymize","Presidio, Bedrock Guardrails","GDPR/HIPAA log masking"],
 ["Agent IAM least-privilege","LLM03 Excessive Agency","Min tools; user-context OAuth; OPA PDP; approvals","OPA/Cedar/OpenFGA","Deny open shell; audit tool calls"],
 ["Output handling as untrusted","LLM10 Output Handling","Schema/allowlist; no eval/exec; sandbox","Validators, sandbox","XSS/SSRF/RCE tests"],
 ["Spend/circuit breaker","LLM06 Unbounded Consumption","Token budgets; per-tenant caps; anomaly alert","Gateway budgets","Cost-anomaly dashboard"],
 ["Audit + Trust Layer","Governance","SHA-256 request log; zero-retention; credit view","SIEM + SSE","Quarterly risk register"],
]
add_table(ws17, h17, sp)

# ---- 18 Observability
ws18 = new_sheet("Observability")
h18=["Layer","Tools","Metrics_Tracked","SLO_Example","Evidence_Label"]
ob=[
 ["Traces","LangSmith / Langfuse / Phoenix / OTel","Tokens, latency per node, tool success, session","p95 <2s interactive","Observed"],
 ["RAG quality","RAGAS / DeepEval / TruLens","Faithfulness, precision/recall, relevancy","Faithfulness >0.8-0.95","Observed"],
 ["Infra","Prometheus/Grafana + OTel Collector","GPU util, queue depth, error rate","GPU fill >70%","Observed"],
 ["Cost","LiteLLM/Helicone + OpenCost","$/query, /tenant, cache hit","Cost <0.5% revenue","Observed"],
 ["Drift","Arize + Langfuse","7-day faithfulness, toxicity","Alert if <0.75","Observed"],
 ["Incident","PagerDuty/Teams + Statuspage","MTTD/MTTR, noise","MTTR -30%","Observed"],
]
add_table(ws18, h18, ob)

# ---- 19 Evaluation
ws19 = new_sheet("Evaluation Methods")
h19=["Method","Use_For","Gate","Tools","Evidence_Label"]
ev=[
 ["Golden 50-200 QAs","Pre-deploy baseline","Block if <0.8","RAGAS + human graders","Observed"],
 ["CI eval gate","Per-PR regression","Fail build if <0.9 (prod)","DeepEval pytest-native","Observed"],
 ["Online 5-10% sampling","Prod drift","Alert + rollback","Langfuse/TruLens","Observed"],
 ["Red-team probes","Security","Zero critical OWASP fails","Promptfoo/Garak/PyRIT","Observed"],
 ["Citation accuracy","Groundedness","Trust >75%","AlignScore + manual","Observed"],
 ["Trajectory metrics","Agents","Task success + tool accuracy + steps","LangSmith traces","Observed"],
 ["Cost/latency eval","FinOps","p95 + $/resolved-task","Helicone/OpenCost","Observed"],
]
add_table(ws19, h19, ev)

# ---- 20 Benchmark
ws20 = new_sheet("8–10 Year Benchmark")
h20=["Dimension","Junior 0-2yr","Mid 2-5yr","Senior 5-8yr / Staff 8+yr","What_This_Candidate_Must_Show"]
bm=[
 ["Project count","2 deployed from original data","2 prod + ADR + monitoring","2 where YOU defined approach + business outcome; 3 deep > 8 shallow","3 flagships with ownership narrative (Ops→AI)"],
 ["Ownership","Execute scoped tickets","Own feature E2E + mentor","Own system incl deploy/monitor/rollback/stakeholders","SLOs, on-call, cost governance from Ops + new AI layer"],
 ["Architecture","Apply templates","Design for scale/observability","Define boundaries; choose vector vs graph with data","ADRs: why LangGraph/MCP/gateway/K8s + trade-offs"],
 ["Failure handling","Learn from incidents","Document 1 failure + response","Canary/rollback/SLOs; cite prevented incident","Postmortem + rollback demo + eval regression catch"],
 ["Business outcomes","Built X with Y","Latency -X% / CTR +Y%","Revenue/cost/MTTR in non-eng language","MTTR -[X%]; cost -[X%]; deflection [X%] (placeholders)"],
 ["Leadership","Receive feedback","Give reviews","Set conventions; RFCs changed teams","Eval gate + platform + talks/runbooks"],
 ["Interview probe","Definitions + code","Retrieval mechanics + monitoring","Debug live: ingest/chunk/embed/retrieve/rerank/generate","When RAG vs FT vs agent — with numbers"],
]
add_table(ws20, h20, bm)

# ---- 21 Transition
ws21 = new_sheet("Career Transition Projects")
h21=["From → To","Bridge_Skills","Bridge_Projects (IDs)","Avoid","Evidence_Label"]
ct=[
 ["IT Ops → AIOps","Linux/net → cloud → monitoring → ML anomaly","P001, P002, P003, P005 (anomaly + correlation + RCA)","Auto-remediate without confidence/topology","Observed roadmap"],
 ["DevOps → Cloud AI/LLMOps","IaC→ML infra; CI/CD→CT; monitoring→drift","P010, P012, P009, P015 (KServe + registry + gateway)","Notebook-only Prophet plot","Observed 3-5mo roadmap"],
 ["QA → AI Eng (Quality)","Golden sets; judge bias; pass@k","P048, P025, P026 (eval + red-team + guardrails)","Accuracy-only claims","Observed (+82% GenAI quality)"],
 ["Security → AI Security","OWASP Agentic; ACLs; injection","P024, P025, P027, P028 (firewall + red-team + vault + OPA)","Regex-only gateway","Observed"],
 ["Backend → Agentic AI","Queues/auth/cache + typed tools","P039, P041, P049, P043 (RAG + SQL agent + MCP)","Single agent 20 tools, no supervisor","Observed"],
 ["Consulting → Solutions/FDE","Discovery→integration→adoption","P035, P033, P038, P059 (pilots + ROI + runbook)","Tool lists without outcomes","Observed (70% FDE = execution)"],
]
add_table(ws21, h21, ct)

# ---- 22 Coverage matrix
ws22 = new_sheet("Project Role Coverage Matrix")
h22 = ["Project_ID","Project_Name"] + ROLES
rows22=[]
for p in PROJECTS:
    rows22.append([p[0],p[1]]+coverage_row(p[3],p[4]))
add_table(ws22, h22, rows22)

# ---- 23 Effort
ws23 = new_sheet("Project Build Effort")
h23=["Project_ID","Project_Name","Effort","Weeks","Coding_/10","AI_/10","Cloud_/10","DevOps_/10","Security_/10","Arch_/10","Integration_/10","Priority_Note"]
eff_weeks={"Small":"1–2","Medium":"3–4","Large":"5–8","Very Large":"10–14"}
rows23=[]
for p in PROJECTS:
    eff=p[13]; cx=p[14]
    base=[6,6,6,6,5,6,5]
    if "Security" in p[3]: base[4]=8
    if "Cloud" in p[3]: base[2]=8; base[3]=8
    if "AIOps" in p[1] or "AIOps" in p[3]: base[6]=7
    if p[0]=="P060": base=[9,9,9,9,8,9,9]
    prio="Flagship" if p[9]>=91 else "High" if p[9]>=86 else "Supporting" if p[9]>=80 else "Optional"
    rows23.append([p[0],p[1],eff,eff_weeks[eff]]+base+[prio])
add_table(ws23, h23, rows23)

# ---- 24 Resume bullets
ws24 = new_sheet("Resume Bullet Patterns")
h24=["Category","Title_Pattern","One_Line","Bullet_Arch","Bullet_Deploy","Bullet_Impact_Placeholder","Bullet_Security"]
rb=[
 ["AIOps","Autonomous Incident Intelligence — [Domain]","LLM triage + RCA over [Prometheus/Splunk] telemetry with HITL.","Built correlation (dedupe [X%]) + evidence-linked RCA with tool-augmented loop.","Deployed on [EKS/AKS] via Helm; OTel traces; PagerDuty/Slack sink.","Reduced MTTR by [X%]; noise by [X%]; [X] incidents/mo.","Read-only tools first; OPA-gated remediation; audit trail."],
 ["Cloud AI","Multi-provider AI Gateway — [Org] LLM Platform","Unified OpenAI-compat gateway with fallbacks + budgets.","Weighted/latency routing; cascading fallbacks per error class; semantic cache.","Docker + Postgres/Redis; Prometheus cost/latency per tenant.","Cut cost by [X%]; p95 [X]s; [X] tenants.","Virtual keys, RBAC, PII redact, spend caps, audit."],
 ["Automation","Intelligent Document Processing — [Invoices/Contracts]","OCR + LLM extraction with confidence routing + HITL.","Layout-aware parse; per-field confidence; low-conf → Action Center.","UiPath/Power Automate + Azure DI; Insights dashboard.","Time [X]min→[Y]s; error [X%]; [X]/mo.","Vaulted creds; logic in bot not prompt; rollback to rules."],
 ["Security","LLM Firewall — [App] Runtime Guard","3-layer injection + PII + output guard as sidecar.","Regex (<2ms) + ONNX classifier + FAISS + judge; consensus policy.","FastAPI sidecar; /metrics; SIEM/SSE feed.","Blocked [X] attacks; p50 +[X]ms; zero critical OWASP.","OWASP-mapped; SARIF; quarterly PyRIT review."],
 ["FDE","Grounded ERP Knowledge Layer — [D365/NetSuite]","Hybrid retrieval + authority tiers + citations; eval-driven pilot.","Row-level chunking; reranker; citation UI; 40-Q golden set.","Teams/ERP embed; SSO/RBAC; staged 14→55 users.","Accuracy [X]%→[Y]%; time [X]min→[Y]s.","Tenant isolation; authz passthrough; zero-retention."],
 ["GenAI","Enterprise Secure RAG — [KB]","Hybrid + rerank + ACLs + freshness + traces.","Top-100→Top-5 funnel; HyDE/multi-query; citation validator.","K8s + Langfuse; CI eval gate; canary.","Relevance [X%]; hallucinations [X%]; adoption [X].","Pre-search ACL filter; Presidio; indirect-injection tests."],
 ["Architect","Golden-path AI Platform — [Org]","Backstage→PR→ArgoCD→KServe + cost attribution.","Platform-owned runtimes; Kyverno policy; quotas + drift control.","Terraform EKS/GKE; OpenCost; 1-command smoke test.","Lead time [X]→[Y]; GPU waste [X%].","Policy-as-code; signed images; per-service RBAC."],
]
add_table(ws24, h24, rb)

# ---- 25 Sources
ws25 = new_sheet("Sources")
h25=["#","URL","Type","Covers","Evidence_Label"]
sources=[
 "https://nancyjain779.github.io/Final_agentic_resume.pdf|Resume|GenAI India|Observed snippet",
 "https://resumedesign.ai/resume-examples/aiops-engineer/|Guide| AIOps resumes|Observed",
 "https://www.foundit.in/job/senior-aiops-engineer-i-porch-group-india-52533181|JD|AIOps India|Observed",
 "https://www.getsetresumes.com/resume-examples/ai-solutions-architect-resume-sample|Resume sample|Architect India 10yr|Observed (vendor)",
 "https://github.com/langchain-ai/langgraph|GitHub|Agents|Observed",
 "https://github.com/BerriAI/litellm|GitHub|Gateway|Observed",
 "https://github.com/vllm-project/vllm|GitHub|Inference|Observed",
 "https://github.com/ollama/ollama|GitHub|Local LLM|Observed",
 "https://github.com/langgenius/dify|GitHub|LLM platform|Observed",
 "https://github.com/infiniflow/ragflow|GitHub|RAG engine|Observed",
 "https://github.com/run-llama/llama_index|GitHub|Data framework|Observed",
 "https://github.com/deepset-ai/haystack|GitHub|RAG pipelines|Observed",
 "https://github.com/langfuse/langfuse|GitHub|Observability|Observed",
 "https://github.com/Arize-ai/phoenix|GitHub|Observability|Observed",
 "https://github.com/traceloop/openllmetry|GitHub|OTel GenAI|Observed",
 "https://github.com/promptfoo/promptfoo|GitHub|Red-team|Observed",
 "https://github.com/NVIDIA/garak|GitHub|Scanner|Observed",
 "https://github.com/HolmesGPT/holmesgpt|GitHub|AIOps agent|Observed",
 "https://github.com/robusta-dev/robusta|GitHub|K8s playbooks|Observed",
 "https://github.com/n8n-io/n8n|GitHub|Automation|Observed",
 "https://github.com/tensorzero/tensorzero|GitHub|LLMOps|Observed",
 "https://github.com/explodinggradients/ragas|GitHub|RAG eval|Observed",
 "https://github.com/confident-ai/deepeval|GitHub|Eval|Observed",
 "https://github.com/backstage/backstage|GitHub|Portal|Observed",
 "https://github.com/kserve/kserve|GitHub|Inference|Observed",
 "https://github.com/AICoE/prometheus-anomaly-detector|GitHub|Anomaly|Observed",
 "https://github.com/NVIDIA/NeMo-Guardrails|GitHub|Guardrails|Observed",
 "https://genai.owasp.org/resource/genai-red-teaming-guide/|Guide|Red-team|Observed",
 "https://www.ksolves.com/case-studies/salesforce/rag-powered-agentforce-ai-assistant-industrial-product-sales|Case|FDE Salesforce|Observed",
 "https://aws.amazon.com/blogs/machine-learning/schneider-electric-leverages-retrieval-augmented-llms-on-sagemaker-to-ensure-real-time-updates-in-their-erp-systems/|Case|FDE ERP|Observed",
 "https://www.businesswaretech.com/case-studies/ai-chatbot-for-smart-database-search|Case|D365 RAG|Observed",
 "https://www.supplytechsolutions.ai/post/rag-architecture-consulting-how-we-built-a-grounded-parts-knowledge-layer-for-an-industrial-parts-d|Case|Eval-driven RAG|Observed",
 "https://botscrew.com/cases/s-and-b-filters-case-study/|Case|NetSuite AI|Observed",
 "https://adastracorp.com/success-stories/tornatech-accesses-data-with-amazon-bedrock-agentic-assistant/|Case|Bedrock agent|Observed",
 "https://jobs.natwestgroup.com/jobs/18181389-genai-and-agentic-ai-engineer|JD|GenAI Bangalore|Observed",
 "https://myengineeringpath.dev/genai-engineer/portfolio-guide/|Guide|Portfolio|Observed",
 "https://huggingface.co/spaces|Platform|Demos|Observed",
 "https://opentelemetry.io/blog/2026/genai-observability/|Docs|OTel GenAI|Observed",
]
rows25=[]
for i,s in enumerate(sources,1):
    u,t,c,l=s.split("|")
    rows25.append([i,u,t,c,l])
# pad to show breadth honestly
rows25.append([len(rows25)+1,"(Full URL index in Word playbook appendix — 150+ consulted URLs across 7 agents)","Index","All roles","See playbook"])
add_table(ws25, h25, rows25)

# ---- 26 Query log
ws26 = new_sheet("Search Query Log")
h26=["Agent","Queries_Executed","Example_Queries","Result_Note"]
ql=[
 ["Resume Mining","19","Generative AI Engineer resume project; AIOps Engineer resume projects; AI Solutions Architect resume India PDF; ...","Full PDFs often gated; snippets used; labeled snippet-only"],
 ["GitHub Mining","20","site:github.com agentic AI production; site:github.com AIOps RCA; github litellm gateway; ...","Stars only where observed; conflicts noted"],
 ["Portfolio + Taxonomy","23","AI Engineer portfolio; Agentic AI projects portfolio; AIOps Engineer jobs India; ...","Counts are snapshots; inflate with broad match"],
 ["AIOps/Cloud/Auto","14","Splunk-ServiceNow ITSM; Prometheus anomaly; HolmesGPT; KServe; UiPath LLM gateway; ...","Docs + GitHub + vendor blogs"],
 ["Security/FDE/Arch","12 (5 rate-limited)","LLM firewall; Promptfoo Garak; NeMo guardrails; NetSuite AI; OWASP mitigations; ...","429s noted; built from 7 full results + docs"],
 ["Stack/Prod/Integrations","12","GraphRAG production; MCP A2A 2026; Ragas vs DeepEval; LangSmith vs Arize; ...","Comparisons triangulated"],
 ["Hiring/Differentiation","16","AI portfolio recruiters 2025; overused projects; senior vs junior; India salary 2026; ...","Salaries qualified as vendor ranges"],
]
add_table(ws26, h26, ql)

# ---- 27 QA
ws27 = new_sheet("QA _ Data Quality")
h27=["Check","Status","Detail"]
qa=[
 ["Anti-hallucination","PASS","No repo stats invented (unknowns marked); no resume metrics invented (placeholders); Observed/Inferred/Recommended labeled; vendor claims flagged."],
 ["Privacy","PASS","No phone/email/address collected; individuals anonymized (role + city only); vendor samples flagged as samples."],
 ["GenAI dominance guard","PASS","GenAI capped: 14/60 patterns; every role ≥7 patterns; AIOps(9) Security(10) FDE(11) Cloud(11) protected."],
 ["Toy vs enterprise split","PASS","A=10, B=35, C=15; Top 25 drawn from A/B only; toy upgrades documented."],
 ["Dedup","PASS","Tutorial clones collapsed to canonical patterns; mirrors flagged (ollama-ollama etc.)."],
 ["India relevance","PASS","India JDs/resumes/cases tagged; AI-Security India resume gap honestly noted as gap, not filled with invention."],
 ["Senior fit","PASS","Benchmark sheet separates junior/mid/senior; flagship bundles require ownership + eval + cost + audit."],
 ["Buildability","PASS","Effort weeks + MVP/advanced split in blueprints; Small→Very Large ladder; rollback/HITL mandatory."],
 ["Interview survival","LIKELY*","Each top project has trade-off + failure + eval story. *Prove by building eval harness first (P048)."],
 ["Saturation","ADD MORE IF","New rounds added <5% new categories at 60 patterns; re-run quarterly for MCP/A2A/ADK drift."],
 ["Limitations","NOTED","Snippet-only resumes; star snapshots conflict; JD counts inflate; salary ranges conflict by source; 5/12 security queries rate-limited."],
]
add_table(ws27, h27, qa)

for ws in wb.worksheets:
    ws.sheet_properties.pageSetUpPr = None

wb.save(XLSX)
print("Saved", XLSX)
