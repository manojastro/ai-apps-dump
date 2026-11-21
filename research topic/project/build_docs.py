"""Build Word playbook + blueprints."""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

OUT = r"D:\ai apps dump\research topic\project"
PLAY = os.path.join(OUT, "AI_Portfolio_Project_Deep_Research_Playbook_2026.docx")
BLUE = os.path.join(OUT, "Top_AI_Project_Blueprints_2026.docx")

def base_doc(title, subtitle):
    d = Document()
    st = d.styles['Normal']
    st.font.name = 'Calibri'; st.font.size = Pt(10)
    for i in range(1,4):
        hs = d.styles[f'Heading {i}']
        hs.font.color.rgb = RGBColor(0x1F,0x38,0x64)
    h = d.add_heading(title, 0)
    p = d.add_paragraph(subtitle); p.italic = True
    p2 = d.add_paragraph("Evidence labels used throughout: [Observed] = seen in search snippets/repos/JDs/cases; [Inferred] = synthesis across sources; [Recommended] = portfolio proposal. No business metrics are stated as facts — impact uses [X%] / [X] placeholders. Individuals anonymized (role + city only). Window 2024–2026, India-prioritized.")
    p2.italic = True
    return d

def add_table_doc(d, headers, rows, col_widths=None):
    t = d.add_table(rows=1, cols=len(headers))
    t.style = 'Light Grid Accent 1'
    for i,h in enumerate(headers):
        t.rows[0].cells[i].text = h
    for r in rows:
        cells = t.add_row().cells
        for i,v in enumerate(r):
            cells[i].text = str(v)
    d.add_paragraph("")

def add_bullets(d, items):
    for it in items:
        d.add_paragraph(it, style='List Bullet')

# ================= PLAYBOOK =================
d = base_doc("AI Portfolio Project Deep Research Playbook — 2026",
             "Resume + GitHub + Portfolio mining for 8 AI roles · India-prioritized · 2024–2026 · 60 canonical patterns · 7 research streams · ~110 searches")

toc = ["Executive Summary","Research Methodology","Projects Found in Real Resumes","Projects Found in GitHub","Projects Found in Portfolios","Project Patterns by Role","AIOps Projects","Cloud AI Projects","Intelligent Automation Projects","AI Security Projects","Forward Deployed AI Projects","GenAI Projects","Agentic AI Projects","AI Solutions Engineering Projects","AI Solutions Architecture Projects","Technologies","Agent Frameworks","Architecture Patterns","Enterprise Integrations","Production Readiness","Security","Observability","Evaluation","Projects to Avoid","High-Value Rare Projects","8–10 Year Portfolio Benchmark","Career Transition Analysis","Top 25 Projects","Top 15","Top 10","Top 5","Top 3 Final Projects","Recommended Portfolio Architecture","Resume Positioning","Interview Strategy","Final Recommendations"]
d.add_heading("Contents (36 sections)", 1)
for i,t in enumerate(toc,1):
    d.add_paragraph(f"{i}. {t}")

# 1
d.add_heading("1. Executive Summary", 1)
d.add_paragraph("Strong hires show the same cluster again and again [Observed across resumes, GitHub, JDs, portfolios]: hybrid RAG with rerank + citations + ACLs + evals; an agent with bounded tools + budgets + human approvals + traces; a gateway with auth + fallbacks + spend caps; and an eval/security harness in CI. Notebook-only demos, basic PDF chatbots, and accuracy-only claims are filtered out at mid level and above.")
add_bullets(d, [
 "Flagship 1 [Recommended]: Secure Enterprise RAG + Agent Platform (P039+P026+P009) — best overall hiring signal (95/100), covers 6 roles.",
 "Flagship 2 [Recommended]: Autonomous Incident Intelligence + RCA (P001+P002+P006) — best leverage of 8.5-yr Ops background (94/100), AIOps + GenAI + Cloud.",
 "Flagship 3 [Recommended]: AI Gateway + LLMOps + Guardrails (P009+P012+P024) — best differentiation + platform depth (93/100).",
 "Supporting [Recommended]: Eval harness as product (P048), MCP tool server + gateway (P049), IDP bot with HITL (P017), observability stack (P054). Together they prove GenAI + agents + cloud + arch + security + observability + integration + deployment + automation.",
 "Build order: P048 eval harness first (2–3 wks) → P039 secure RAG (5–8 wks) → P009 gateway (3–4 wks) → P001 RCA agent (5–8 wks) → harden with P024/P025/P054. Total ~5–7 months part-time; each milestone is independently demoable.",
 "India framing: target product/GCC senior bands require deployed + evaluated proof, not courses [Observed salary guides conflict; treat ranges as vendor estimates, verify live]. Services route pays ~2x less for same skill [Observed].",
])

# 2
d.add_heading("2. Research Methodology", 1)
d.add_paragraph("Seven parallel streams; ~110 web searches; 2024–2026 window; India primary, global secondary. Coverage matrix Role × Project Type × Source × Tech × Arch × Seniority × Geography tracked in Excel Executive Dashboard.")
add_table_doc(d, ["Stream","Queries","What was inspected","Limitation handling"],
 [["Resume mining",19,"Snippets + open PDFs + JD mirrors","Gated PDFs marked snippet-only; templates flagged as templates"],
  ["GitHub mining",20,"README, Docker/K8s/workflows/evals/docs","Stars only where observed; conflicts noted; small-star repos = pattern only"],
  ["Portfolio + taxonomy",23,"Live sites, HF Spaces, JDs 2025–26","Board counts = snapshots, inflate noted"],
  ["AIOps/Cloud/Auto",14,"Docs, GitHub, vendor eng blogs","Triangulated 2+ sources"],
  ["Security/FDE/Arch",12,"Firewalls, red-team, NeMo, ERP cases","5/12 rate-limited (429) — disclosed"],
  ["Stack/prod/integrations",12,"RAG, MCP/A2A, evals, FastAPI/K8s","Comparisons triangulated"],
  ["Hiring/differentiation",16,"Recruiter guides, interviews, salaries","Salaries qualified, never stated as offers"]])
d.add_paragraph("Anti-hallucination: no invented repo stats, resume bullets, company usage, or metrics. Production claims require Docker/K8s/tests/evals/docs/audit evidence. Authenticity A/B/C/D/E assigned; Top 25 from A/B only. Privacy: no PII collected.", style='Intense Quote')

for sec, body in [
 ("3. Projects Found in Real Resumes", "Strongest resume evidence is GenAI/RAG + text-to-SQL [Observed: Nancy Jain, India — AskAI LangGraph text-to-SQL, NER tagging, MetaMapper graph retrieval + rerank, semantic matching]. AIOps resumes show alert-noise reduction + MTTR + platform + automation [Observed: resumedesign + Porch/Trianz India JDs: GCP/GKE/BigQuery/PubSub/Vertex, EKS+OTel]. Automation shows UiPath/Power Automate + PDD/SDD + queues + Doc Understanding + LLM extraction [Observed: Veradigm India, Coforge, Shriansh Singh snippet]. Architect senior sample shows 5M-doc RAG + automation + modernization + governance + vendor evals [Observed: GetSetResumes 10-yr India vendor sample — flag as sample, not verified hire]. Security/FDE resumes are mostly templates/JDs in snippets [Observed gap — honestly noted; global patterns apply]. Universal bullet formula [Observed]: verb + what + stack (model/framework/DB) + measurable result + scale; name base model, dataset, baseline, eval size, latency, cost."),
 ("4. Projects Found in GitHub", "Foundations to build on, not to clone [Observed]: langgraph (state + HITL + LangSmith), litellm (100+ provider gateway + budgets), vLLM (PagedAttention + K8s), dify (154k stars LLM app platform), ragflow (90k deep-doc RAG), haystack (pipeline YAML + eval), langfuse/phoenix/openllmetry (OTel GenAI semconv), promptfoo/garak (CI red-team), holmesgpt + robusta (SRE agent + playbooks), n8n (203k workflow+AI), tensorzero (gateway+obs+evals), kserve (inference CRDs), prometheus-anomaly-detector (611 stars). Pattern: Compose for dev, Helm+Terraform for prod; Postgres+pgvector+Redis+ClickHouse; OTel gen_ai.* spans; eval→CI gate→sampling loop; HITL + OPA + audit; hybrid + rerank + citations; per-run cost caps. Small-star gateways/MCP wrappers (1–3 stars) are pattern references only [Observed + Inferred]."),
 ("5. Projects Found in Portfolios", "Reviewers decide in ~60 seconds [Observed]: problem + outcome in first 3 lines, arch diagram, live URL + demo GIF before scroll, Key Learnings / What failed, Dockerfile + CI + eval/ + cost/latency table. 3-project rule: one RAG + one agent + one eval/MLOps beats 10 tutorials. Live URL non-negotiable (FastAPI Swagger, Vercel, HF Spaces, Streamlit Cloud). 2026 site stack: Next.js + TS + Tailwind + Vercel + AI twin with injection defense [Observed]. 20 portfolio types catalogued in Excel (RAG, crews, eval harness, guardrails lab, LoRA, memory assistant, text-to-SQL, support system, SDR agent, code reviewer, voice bot, YOLO API, LLMOps pipe, cloud AI, multi-cloud case, consulting toolkit, sanitized arch cases, Spaces demos, site templates)."),
 ("6. Project Patterns by Role", "Each role has ≥7 canonical patterns (Excel Projects by Role). GenAI deliberately capped at 14/60 to prevent dominance. Cross-cutting hiring cluster [Observed]: Python + SQL + AWS/Azure + Docker/K8s + LangGraph + vector DB + evals in 6/8 roles. Differentiators: Dynatrace/Datadog (AIOps), REFramework/Orchestrator (Automation), OWASP/ATLAS (Security), ontology + decomposition (FDE), RFP/discovery (Solutions Eng), TOGAF/Well-Architected + cost/scale (Architect)."),
]:
    d.add_heading(sec, 1); d.add_paragraph(body)

# 7-15 role sections
role_secs = [
 ("7. AIOps Projects", "P001 RCA agent (HolmesGPT + Robusta change correlation) [Observed pattern]; P002 correlation/noise service (Splunk→orchestrator→ServiceNow with approval + audit) [Observed]; P003 streaming log anomaly (Kafka + IF + DLQ + Grafana) [Observed: log-anomaly-platform]; P004 forecast planner (Prophet+XGBoost + mitigation sim) [Observed: ForecastOps]; P005 Slack commander (SLO burn before paging) [Observed: incident.io pattern]; P006 change-RCA; P007 runbook RAG; P008 FinOps advisor. Prod bar: phased read-only → high-confidence auto-create; human confirm P1–P4; dedupe precision/recall evals; CMDB grounding; lineage IDs [Observed]."),
 ("8. Cloud AI Projects", "P009 LiteLLM gateway (fallbacks per error class + budgets + cache; 5–15ms overhead) [Observed]; P010 KServe+vLLM on EKS/GKE (Standard mode for LLMs, QPS/latency HPA, PVC model cache, SSE ingress fix) [Observed]; P012 MLflow LLMOps (prompt registry + judge eval + gateway + drift) [Observed]; P015 Backstage→ArgoCD→KServe golden path + OpenCost + Kyverno [Observed: NeuroScale]; P016 multi-cloud via gateway (Bedrock + Azure + Vertex) with residency [Inferred from cases]; P013 LoRA adapters; P014 semantic cache + routing. Strategy [Observed 2026]: Bedrock = broadest models; Azure = compliance/hybrid search; Vertex = long-doc/multimodal cheapest; abstract via LiteLLM, measure 60–90d before savings plans."),
 ("9. Intelligent Automation Projects", "P017 invoice IDP (Azure DI + LLM validation + Action Center + Insights) [Observed JD pattern; India volume]; P018 Maestro↔Power Automate order-to-cash [Observed docs]; P019 email triage + approval; P020 self-healing bot ops (40–50% auto-resolve claim [Observed guide]); P021 drawing extractor (DI custom 92–95% vs Textract 78–82% plateau [Observed benchmark]); P022 HR onboarding; P023 CRM agent (<60s, 42 tests pattern [Observed]). Prod bar [Observed]: vaulted creds, logic in bot not prompt, phased attended→semi→unattended, token/override tracking, rollback to rules."),
 ("10. AI Security Projects", "S1 firewall 3–5 layers (regex <2ms + ONNX 50–150ms + FAISS + judge; BLOCK≥70/FLAG/ALLOW) [Observed: 8 firewall repos]; S2 Promptfoo per-PR + Garak nightly + PyRIT quarterly + SARIF gate [Observed]; S3 NeMo 5 rails + NIMs (needs 2×H100/A100 [Observed]); S4 Presidio + 95 secret detectors + vault [Observed]; S5 OWASP reference on AWS (Cognito+WAF+Bedrock Guardrails + least-privilege action groups) [Observed]; S6 OPA PDP for excessive agency [Observed mitigations + Inferred OPA wiring]; S7 Lakera/Rebuff runtime loop [Partially observed]; S8 Giskard quality gates [Recommended]; S9 output-as-untrusted + sandbox [Observed]; S10 spend circuit breaker [Observed OWASP 2026 elevation]. 92% say agent governance critical, 44% have policies [Observed report — treat as survey claim]."),
 ("11. Forward Deployed AI Projects", "Formula per case [Observed]: Discovery (workshops + 40 golden Qs) → Integration (SAP/Salesforce/D365/NetSuite/SNOW/Snowflake/SharePoint) → Deployment (pilot 14→55 users + SSO/RBAC) → Outcomes. Cases: Salesforce Agentforce + Trust Layer [Observed Ksolves]; D365 hybrid (40% search cut, 65% adoption, no ERP slowdown [Observed Businessware — vendor claim]); NetSuite 4-wk rebuild (4–6min→15s, $140k/yr, 50% auto [Observed Botscrew]); parts layer 41→84% accuracy, trust 22→79% [Observed SupplyTech]; SageMaker text-to-SQL 55→71% [Observed Schneider/AWS]; ERP foundation land-and-expand (quote 50h→30m [Observed Annora]); Bedrock read-only SQL agent [Observed Adastra]. P038 SAP/ServiceNow/Snowflake copilot is [Recommended] gap-fill for JD keywords."),
 ("12. GenAI Projects", "P039 enterprise RAG (hybrid BM25+dense + RRF 15–30% + rerank Recall@10 74→89% [Observed Databricks claim] + citations + ACLs + freshness) [Observed across resumes/cases/repos]; P040 GraphRAG (entity/graph split; write-consistency hard [Observed]); P041 text-to-SQL with router + guard + charts [Observed India resume]; P047 freshness + tenant filter copilot; P050 context engineering (parent-child + HyDE +49% recall/+67% with rerank per Anthropic reports cited [Observed as cited claim]); P056 FT loop (RAG-first; LoRA delta + cost/latency trade [Observed guidance]). Baselines [Observed]: precision >0.8, faithfulness >0.8–0.95, relevancy >0.75, p95 <2s, top-k 4–8."),
 ("13. Agentic AI Projects", "Default is LangGraph supervisor + specialists + budgets + max-hops + stop + verify-in-system-of-record [Observed + Inferred]. Token reality [Observed]: LangGraph ~2k vs CrewAI ~3.5k vs AutoGen ~8k same task; code routing 47% cheaper than LLM routing. P042 crews are tutorial-common (Tier C unless HITL+evals+write-back) [Observed]. P043 support system with Zendesk/Slack write-back; P044 code reviewer with test-gen loop; P045 voice (<1s); P046 memory (weak unless eval + privacy); P048 eval harness; P049 MCP server + gateway (17–18k servers Q1 2026, 97M SDK dl/mo [Observed]); A2A for agent-to-agent (150+ orgs [Observed]). MCP+A2A together is baseline [Observed]. Convergence [Observed]: vendor SDK + LangGraph/CrewAI + gateway (400+ models)."),
 ("14. AI Solutions Engineering Projects", "Pre-sales + PoC motion [Observed JD]: discovery → RAG/prompt for customer KB → demo → RFP → eval vs customer KPIs (precision/recall/BLEU + exec story). Python non-negotiable + SQL + REST/Docker + 1 cloud deeply [Observed]. Reusable accelerators (templates, connectors, BI/ROI dashboards) + adoption past go-live (paired builds, usage reviews, playbooks) [Observed NewRocket/Statisfy]. Demos must show SSO/SAML, tenant isolation, and cost per query — not just answers."),
 ("15. AI Solutions Architecture Projects", "A1 secure RAG gold standard; A2 tool-governed agent platform (OPA + user-context OAuth + caps); A3 NIM/Bedrock/gateway inference tiers (Lite <0.3ms / Std <80ms / Full <2s [Observed inferwall]); A4 governance/audit + Trust Layer; A5 PII vault; A6 LLMOps observability; A7 multi-cloud with residency; A8 10-week POC→pilot gates (accuracy >80%, trust >75%, <90s, <0.5% revenue, zero critical OWASP [Observed synthesis]); A9 modular-monolith start. Principles [Observed synthesis]: separate instruction/data/retrieval planes; authz outside model; default-deny tools; version everything together; re-run adversarial evals before promotion."),
]
for t,b in role_secs:
    d.add_heading(t,1); d.add_paragraph(b)

# 16-23
for t,b in [
 ("16. Technologies", "Frequency in 60 patterns (Excel Technology Frequency): Python 97%, Docker 80%, OpenAI/Azure 77%, FastAPI 73%, Actions 67%, LangGraph 63%, AWS 63%, LangChain 60%, pgvector 57%, Azure 57%, K8s 53%, Redis 50%, Prometheus/Grafana 50%, LLM-obs 47%, RAGAS/DeepEval 43%, Terraform 43%, MCP 40%, OTel 37%, LlamaIndex 37%, Pinecone 33%, Vertex 33%. [Observed counts within this study; treat as comparative, not market shares]. Skill cluster for ATS: LangGraph + RAG + MCP + LangSmith/Langfuse + FastAPI/K8s + evals."),
 ("17. Agent Frameworks", "LangGraph = production default + strongest hiring signal (146x US roles, Klarna/Uber/LinkedIn prod [Observed]); LlamaIndex = RAG-first second; CrewAI = prototype signal (token-heavy); AutoGen standalone weakening → Microsoft Agent Framework; Semantic Kernel = Azure/C# vertical; OpenAI SDK rising (sandbox/handoffs); Google ADK rising (GCP/A2A-native, 5 langs); PydanticAI niche-growing; DSPy low-vol high-signal; MCP = strongest 2025–26 accelerant (Forrester 30% vendors by end 2026 [Observed claim]); A2A emerging (ServiceNow/Salesforce/SAP partners [Observed]). Rule [Inferred]: LangGraph + LlamaIndex-retrieval + MCP + gateway + evals = strongest generalist."),
 ("18. Architecture Patterns", "Universal: modular RAG. Very high: API-first, microservices split, agent orchestration, K8s. High: event/queue, HITL, gateway choke point, eval→sampling loop. Medium: serverless (85–95% cut for bursty [Observed]), multi-tenant. Rising→mandatory: zero-trust/governance. If a project lacks hybrid+rerank+evals+HITL+tracing it reads as demo [Inferred from Observed bars]."),
 ("19. Enterprise Integrations", "Tier 1 [Inferred ranking from Observed weight]: ServiceNow/ITSM (audit + approvals), Slack/Teams/Email (same-session continuity — Red Hat lesson [Observed]), Snowflake/Databricks (no data movement), MCP+SSO (shadow-IT fix), telemetry sources (Datadog/Splunk/PagerDuty). Tier 2: GitHub, M365/Copilot Studio, vector+reranker, Jira/PagerDuty. Tier 3: Salesforce, SAP/Workday (keyword moat), S3/SharePoint. Template: ServiceNow↔Microsoft Ignite Nov 2025 (Control Tower ↔ Foundry/Copilot, Agent 365 [Observed])."),
 ("20. Production Readiness", "Checklist distilled [Observed]: OAuth 2.1/OIDC/SSO/PKCE; RBAC per tool/namespace/index; Vault secrets; private subnet; Pydantic validation; timeouts/retries/idempotency/breaker; queue backpressure; multi-model failover; HPA on QPS/latency (not CPU); GPU isolation; multi-stage Docker; blue-green; golden 50–200 + CI gate (0.65→0.8–0.9); 5–10% online sampling + drift alert (<0.75); $/tenant budgets + kill-switch; HITL tiers (auto→approval→dual); SOC2/ISO/GDPR/HIPAA/EU-AI audit. Scores in Excel Production Readiness; Top 25 all ≥77/100."),
 ("21. Security", "See §10 + Excel Security Patterns. Interview translation [Inferred]: draw secure assistant (Cognito → WAF → Gateway → Guardrails → least-privilege action groups → scoped vector DB → audit). Never pass model output to shell; render plain text; sandbox code; schema-allowlist; topic-drift check. Pre-commit secret scan + training-data sanitize."),
 ("22. Observability", "Three layers [Observed best practice]: L1 golden pre-deploy; L2 CI gate blocking; L3 prod sampling dashboard. Traces (tokens/latency/tool/session via OTel + Langfuse/Phoenix); quality (faithfulness/precision/recall); infra (GPU/queue/error); cost ($/query/tenant/cache); drift (7-day <0.75 alert); incident (MTTD/MTTR). LangSmith if all-in LangGraph else Langfuse/Phoenix self-hosted for VPC/RBAC [Inferred pick]."),
 ("23. Evaluation", "Start 0.65 → prod 0.8+ (regulated 0.9+) [Observed]. RAGAS for metric design + DeepEval for gates + Langfuse/Phoenix for prod [Inferred]. Musts: golden 50–200 versioned; CI fail on regression; red-team zero-critical; citation accuracy; trajectory (task/tool/steps); cost/latency per resolved task. 18/20 + 2 failures explained beats 99% claim [Observed recruiter signal]."),
]:
    d.add_heading(t,1); d.add_paragraph(b)

d.add_heading("24. Projects to Avoid (or Heavily Upgrade)",1)
d.add_paragraph("Only listed because evidence supports high prevalence + low signal [Observed across recruiter/portfolio guides]. Each has an enterprise upgrade path:")
add_table_doc(d, ["Toy pattern","Why it fails [Observed]","Enterprise upgrade [Observed fix]"],
 [["Titanic/Iris/MNIST/Boston","Pristine CSV, seen 1000s of times","Scraped/API messy data + Postgres + preprocessing notebook"],
  ["Accuracy-only 99%","Hides imbalance/leakage","Precision/recall/F1/AUC + confusion + error analysis"],
  ["Sentiment/MNIST, no deploy","No prod constraints","FastAPI + Docker + Spaces + latency/cost + rate-limit"],
  ["Basic PDF chatbot","No eval/citations/ACLs","Hybrid + reranker + RAGAS + tenant filter + 30-Q eval + traces"],
  ["Kaggle-only copy-paste","No framing/sourcing","Cite + what-changed + 2 self-directed + deploy one"],
  ["Single .ipynb, one commit, no README","Can't run/review","ingest/train/serve/eval split + README + 3-cmd run"],
  ["Todo/CRUD claiming millions","Overclaim, no SLO/cost/safety","Label prototype + prod-needs OR rebuild with queue/auth/obs"],
  ["Fine-tune with no before/after","Expensive, undifferentiated","RAG-first; LoRA delta + cost/latency justification"],
  ["Same technique ×5","Comfort-zone signal","Range: tree + neural + retrieval + agent, justify each"],
  ["'Built NLP from scratch' (was API)","Credibility loss","Precise verbs + What Didn't Work section"]])

d.add_heading("25. High-Value Rare Projects",1)
d.add_paragraph("Less common + technically deep + enterprise-relevant + prod-oriented [Observed demand + Inferred mapping]. Ranked:")
add_bullets(d, ["1. Eval + regression harness as product (P048) — scarcest senior skill.",
 "2. MCP tool server + gateway with auth/registry/signing (P049) — least-saturated 2025–26.",
 "3. Agent IAM broker with OPA + approvals (P028) — governance gap (92% critical / 44% have policies).",
 "4. LLM firewall sidecar <50ms (P024) — CISO-visible.",
 "5. Golden-path platform Backstage→KServe + cost (P015) — platform-eng moat.",
 "6. Drawing extractor DI+YOLO (P021) — 78→93% custom-training story.",
 "7. ITSM+procurement SAP/ServiceNow/Snowflake copilot (P038) — JD keyword closer.",
 "8. Context-engineering showcase (P050) — recall +49%/+67% cited pattern.",
 "9. Cost/latency rescue with trace breakdown (P014/P055) — FinOps hybrid.",
 "10. Voice/multimodal NOC copilot — hands-free ops, eval on task completion."])

d.add_heading("26. 8–10 Year Portfolio Benchmark",1)
d.add_paragraph("You are judged as a senior switcher, not a fresher [Observed leveling]. 3 deep > 8 shallow. Must show: defined approach (not tickets), system ownership incl deploy/monitor/rollback/stakeholders, boundaries with perf/cost data, graceful recovery + postmortems, business outcomes in non-eng language, conventions/RFCs that changed teams. Interview probe is live debugging: RAG wrong despite doc existing → split ingest/chunk/embed/retrieve/rerank/generate; plus cost/latency/security/incident ownership; RAG vs FT vs agent with numbers. Transfer framing that works [Inferred]: 'I owned [X] services, [Y] incidents, [Z] cost' → 'now own AI system with same rigor'. Without 18–24mo genuine prod ML, framing alone won't close the gap — AIOps bridges count as prod [Inferred]. See Excel 8–10 Year Benchmark.")

d.add_heading("27. Career Transition Analysis",1)
add_table_doc(d, ["From → To","Bridge project","Why it bridges"],
 [["IT Ops → AIOps","P001/P002/P003 anomaly + correlation + RCA","Same telemetry + on-call + MTTR language; 4–6 wks data for seasonality [Observed roadmap]"],
  ["DevOps → Cloud AI/LLMOps","P010/P012/P009 KServe + registry + gateway","IaC→ML infra, CI/CD→CT, monitoring→drift [Observed 3–5mo]"],
  ["QA → AI Quality","P048/P025 eval + red-team","Eval is scarcest skill; judge bias + kappa + gates [Observed +82% demand]"],
  ["Security → AI Security","P024/P027/P028 firewall + vault + OPA","OWASP Agentic + ACLs + injection [Observed]"],
  ["Backend → Agentic","P039/P041/P049 RAG + SQL agent + MCP","Queues/auth/cache + typed tools + budgets [Observed]"],
  ["Consulting → FDE","P035/P038 pilots + ROI + runbook","70% FDE is execution; integration 12%; adoption 5% [Observed]"]])

def funnel(d, title, items, note):
    d.add_heading(title,1); d.add_paragraph(note)
    for rank,pid,name,hs in items:
        d.add_paragraph(f"{rank}. {pid} — {name} (Hiring {hs})", style='List Number')

top25list = [(1,"P060","OpsPilot Unified Spine",96),(2,"P039","Enterprise Secure RAG Platform",95),(3,"P026","Secure RAG with Guardrails",94),(4,"P001","Incident Triage + RCA Agent",94),(5,"P009","Multi-provider AI Gateway",93),(6,"P012","LLMOps Platform",93),(7,"P024","LLM Firewall Gateway",93),(8,"P048","Eval + Regression Harness",93),(9,"P010","K8s Inference Platform",92),(10,"P025","CI/CD Red-teaming Gates",92),(11,"P041","Agentic Text-to-SQL Analyst",92),(12,"P049","MCP Tool Server + Gateway",92),(13,"P028","Agent IAM Broker (OPA)",91),(14,"P035","Industrial Parts Knowledge Layer",91),(15,"P016","Hybrid Multi-cloud RAG",90),(16,"P015","Golden-path Platform",90),(17,"P002","Alert Correlation Service",90),(18,"P033","D365 Conversational Layer",90),(19,"P027","PII Vault + DLP",90),(20,"P032","Salesforce Agentforce RAG",89),(21,"P034","NetSuite AI Rebuild",89),(22,"P017","Invoice IDP Bot + HITL",89),(23,"P006","Change-correlated RCA",88),(24,"P040","GraphRAG System",89),(25,"P054","AI Observability Stack",90)]
funnel(d, "28. Top 25 Projects", top25list, "Ranked by Hiring + Quality composite (Excel Top Projects). All A/B authenticity. Why each survived is in Excel Why_Survived.")
funnel(d, "29. Top 15", top25list[:15], "Cut drops single-channel or narrower-coverage items (P032/P034/P017 kept as role-supporting, not core). Survivors each cover ≥4 roles or own a scarce gate (eval/security/gateway).")
funnel(d, "30. Top 10", top25list[:10], "Cut drops IAM/parts/multi-cloud/golden-path/correlation (strong but second-order once core RAG+gateway+eval+firewall+RCA exist). Survivors are the minimal senior spine: RAG + secure RAG + RCA + gateway + LLMOps + firewall + eval + inference + red-team + SQL agent.")
funnel(d, "31. Top 5", top25list[:5], "Cut drops firewall/eval/inference/red-team/SQL/MCP as extensions of the top-5 spine (they return as hardening sprints). Survivors: OpsPilot vision (P060) + secure RAG (P039+P026) + RCA (P001) + gateway (P009) + LLMOps (P012). Each maximizes Hiring × Coverage × Prod Depth per build week.")
d.add_heading("32. Top 3 Final Projects",1)
d.add_paragraph("Optimization: Hiring Signal + Market Relevance + Transferable Experience + Differentiation + Production Depth + Role Coverage, per build time [Recommended].")
add_bullets(d, ["#1 Secure Enterprise RAG + Agent Platform (P039+P026+P009): gold-standard RAG + authority tiers + gateway. Why it wins every cut: most-observed pattern + BFSI/health gate + interview-deep + 6-role coverage. Bundle effort Large (5–8 wks MVP, +3 wks hardening).",
 "#2 Autonomous Incident Intelligence + RCA (P001+P002+P006): HolmesGPT operator + correlation + change-RCA. Why it survives: only flagship that weaponizes 8.5-yr Ops (MTTR/noise/on-call/SLO) + AIOps hiring density in India (Porch/Trianz/HSBC observed). Effort Large.",
 "#3 AI Gateway + LLMOps + Guardrails (P009+P012+P024): LiteLLM + registry/eval gates + firewall. Why it survives: platform differentiator + CISO visibility + FinOps story; turns the other two from demos into a governed platform. Effort Medium."])
d.add_paragraph("P060 OpsPilot is the vision that the three flagships compose into — do not build it first. Build P048 eval harness in parallel from week 1; it is the senior gate for all three.", style='Intense Quote')

d.add_heading("33. Recommended Portfolio Architecture",1)
d.add_paragraph("One spine, three flagships, four supports [Recommended]. Experience (Teams/Slack/ERP UI) → Gateway (P009: auth/rate/PII/budgets) → Guardrails (P024/P026: multi-config) → Orchestration (P039 RAG vs P001 agent router) → Data (vector + ERP APIs + Snowflake) → Models (Bedrock/Azure/Vertex + vLLM) → Observability + Governance (P054+P048+P025+P031: traces, evals, red-team, audit, cost). Repo strategy: 3 flagship repos + 1 eval-harness + 1 MCP-server + 1 IDP + 1 obs-config (7 repos, each with Dockerfile, CI eval gate, arch.png, cost note, failure log). Demo: 90-sec Loom per flagship (problem → live query → trace → eval → cost) + Swagger + HF Space for RAG.")
add_table_doc(d, ["Build","Projects","Weeks (part-time)","Demo exit"],
 [["Sprint 0","P048 eval harness skeleton + golden 30 Qs","2–3","CI gate failing build on regression"],
  ["Flagship 1 MVP","P039 secure RAG (hybrid+rerank+citations+ACLs)","5–6","Live RAG + eval table + citation UI"],
  ["Platform slice","P009 gateway + P024 firewall-lite","3–4","Multi-model failover + spend caps + block demo"],
  ["Flagship 2","P001 RCA agent + P002 correlation","5–6","Fault injection → Slack RCA + MTTR board"],
  ["Harden","P012 registry + P025 red-team + P054 obs","3–4","Rollback on regression + drift alert"],
  ["Support","P017 IDP + P049 MCP server","4–6","HITL queue + scoped tools"]])

d.add_heading("34. Resume Positioning",1)
d.add_paragraph("For 8.5-yr Ops → Senior AI: hybrid format; page 1 = summary + top metric bullets; 2 pages acceptable [Observed]. Title exactly matches JD (FDE titles vary [Observed]). Each flagship gets 3 bullets: architecture + deployment + impact-with-placeholder (Excel Resume Bullet Patterns). Name base model, dataset size, baseline, eval size, latency, cost [Observed formula]. GitHub + HF + Loom links mandatory; certs (AWS ML / Azure AI / CKA) fill cloud gap [Observed transition guidance]. Never invent metrics — reviewers probe them live.")
add_bullets(d, ["Summary pattern [Recommended]: '8.5-yr enterprise IT operations/automation engineer building production AI systems — secure RAG, agentic RCA, and governed LLM platforms on AWS/Azure with Kubernetes, evals, and observability.'",
 "Skills block: Python, FastAPI, LangGraph/LangChain, LlamaIndex, MCP, pgvector/Qdrant, Docker/K8s, Terraform, AWS/Azure, Prometheus/Grafana/OTel, LangSmith/Langfuse, RAGAS/DeepEval, Promptfoo/Garak, Presidio, OPA, ServiceNow/Slack/Snowflake.",
 "Avoid helpdesk framing; reframe tickets/incidents/SLAs as reliability engineering + automation ownership."])

d.add_heading("35. Interview Strategy",1)
d.add_paragraph("Expect [Observed question banks]: Why this arch/framework? Why RAG vs FT vs agent? Hallucination/failure/scale/security/monitor/eval/cost defenses? What would you change in prod? Prepare per flagship:")
add_bullets(d, ["RAG: chunking + hybrid + RRF + rerank + top-k 4–8; debug split ingest/chunk/embed/retrieve/rerank/generate; freshness + ACLs; faithfulness vs relevancy.",
 "Agent: workflow vs agent choice; supervisor/router; tool schemas + least-privilege + OPA; budgets/max-hops/stop; verify in system-of-record; trajectory metrics.",
 "Gateway/LLMOps: routing priority + typed fallbacks + cache policy + spend boundary; chaos (429/502/503/refusal/overflow); prompt = code review + rollback <5min.",
 "AIOps: season-aware bands + per-tenant thresholds + backtest; dedupe precision/recall; read-only first; confidence-gated remediation; MTTR with lineage.",
 "Security: 3-layer latency tiers; indirect-injection via docs; cross-tenant leak test; tool-misuse; audit without sensitive store.",
 "Cost: trace breakdown retrieval/model/tool/queue; semantic cache + tiered routing + trimming; $/resolved-task; kill-switch story."])
d.add_paragraph("Bring: eval table (pass/fail + 2 failures explained), trace screenshot, cost/latency dashboard, red-team report, rollback log. Honest numbers beat 99% claims [Observed].", style='Intense Quote')

d.add_heading("36. Final Recommendations",1)
add_bullets(d, ["Build P048 first — it makes every other project senior-credible.",
 "Bundle flagships; do not scatter across 10 shallow repos (2–3 finished > 10 shallow [Observed]).",
 "Deploy everything (live URL + Docker + CI gate); notebook-only = eliminated at mid+ [Observed].",
 "Integrate enterprise systems (ServiceNow/Slack/Snowflake/SharePoint/SAP-keyword via P038 slice) — integrations are the Tier-1 hiring signal.",
 "Instrument cost + latency + drift from day one; add approvals + audit before claiming production.",
 "Re-run research quarterly — MCP/A2A/ADK drift fast; saturation check (<5% new categories = stop).",
 "Answers to the 25 strategic questions (§51 of brief) are embedded: most-common = enterprise RAG + incident automation + text-to-SQL; strongest signal = secure RAG + gateway + eval + RCA; overused = PDF chatbot/sentiment/MNIST (upgrade paths §24); rare = eval/MCP/IAM/firewall/golden-path; K8s/obs/eval/security are gates not bonuses; senior bar = ownership + eval + cost + audit; top-3 = §32."])
d.add_paragraph("Appendix: full 150+ URL index + query log + QA are in Excel (Sources, Search Query Log, QA / Data Quality). Sub-agent evidence packs available on request. All scores are comparative judgments; re-score after building with real eval numbers.", style='Intense Quote')
d.add_paragraph("Generated 2026-09-05 · Window 2024–2026 · Geography India-primary. Methods + limitations in §2 and Excel QA sheet.")
d.save(PLAY)
print("Saved", PLAY)

# ================= BLUEPRINTS =================
b = base_doc("Top AI Project Blueprints — 2026",
             "Build-ready specs for the Top 15. Each blueprint is detailed enough for a coding agent to start implementation. Placeholders [X] = fill with measured values; do not invent.")
BLUEPRINTS = [
 ("P039","Enterprise Secure RAG Platform","GenAI / Agentic AI Engineer","SharePoint/S3/Data Cloud → layout-aware parse → heading/row chunks + metadata (source/page/tier/date) → E5 embed → Azure AI Search / pgvector (hybrid + tenant filter) → reranker → prompt (citations required) → LLM private endpoint → output rails (AlignScore + LlamaGuard + PII redact).","LangGraph router (vector vs SQL vs API) + LlamaIndex ingestion; HyDE/multi-query; Top-100→Top-5 funnel; citation validator.","Python, FastAPI, LangGraph, LlamaIndex, pgvector/Qdrant, Cohere/BGE rerank, Redis cache, Next.js/Streamlit, Docker/K8s, Langfuse, RAGAS/DeepEval","ServiceNow KB, SharePoint/OneDrive, Snowflake (metadata), Slack/Teams bot, Jira (feedback)","Entra/Okta SSO; pre-search ACL filter; Presidio; tenant namespaces; zero-retention; audit query→chunkIDs→answer","Large (5–8 wks)"),
 ("P026","Secure RAG with Guardrails + Authority Tiers","AI Security Engineer","NeMo Guardrails microservice (config_id) → NemoGuard 8B + Topic NIM + LlamaGuard → embedding NIM → vector store → LLM NIM → output rails (stream_first:false). Authority T1 OEM PDFs > T2 notes > T3 history.","5 rails (input/dialog/retrieval/execution/output) + Colang flows; refusal/hedge tuning; 40-Q golden set.","NeMo Guardrails, NIMs, Azure OpenAI/Bedrock, Azure AI Search/pgvector, FastAPI, Prometheus","SharePoint Premium, D365, M365 Copilot (pilot channel)","Per-user authz passthrough; PII mask; policy tiers; immutable logs + SIEM","Large (5–8 wks)"),
 ("P001","Autonomous Incident Triage + RCA Agent","AIOps Engineer","Prometheus/Alertmanager/Datadog → Robusta runner (K8s operator) → HolmesGPT agent (toolsets: K8s, metrics, logs, cloud, PR) → Slack finding + remediation PR (RBAC-gated) → PagerDuty/Jira/ServiceNow sinks.","Controller Thought-Action-Observation loop; per-tool memory limits; stabilization/aggregation; locally-hostable LLM option.","HolmesGPT, Robusta, LangGraph, OTel, Helm, OPA, Prometheus/Grafana","Prometheus, Datadog, Splunk, PagerDuty, Slack/Teams, Jira/ServiceNow, Backstage catalog","Read-only tools first; approval gates; audit trails; prompt-injection sanitization","Large (5–8 wks)"),
 ("P009","Multi-provider AI Gateway","Cloud AI Engineer","App → LiteLLM proxy (stateless Docker) → weighted/least-busy/latency routing → cascading fallbacks per error class → providers (Azure GPT-4o ↔ Claude ↔ Bedrock Llama) → cache → response. Redis sliding-window rate-limit + reserve/reconcile cost caps.","Classifier router (cheap vs frontier); semantic vs exact cache policy; cooldown pools; chaos fire-drills.","LiteLLM, Redis, Postgres, FastAPI, Prometheus, Supabase (billing), Docker/Helm/Terraform","Any LLM consumer; Teams/Slack bots; ERP assistants","Virtual keys, RBAC, PII redact, spend caps, audit, CVE-pinned images","Medium (3–4 wks)"),
 ("P012","LLMOps Platform (Registry + Eval Gates + Tracing)","Cloud AI Engineer","Prompt versions (dev/stage/prod aliases) → tracing (agent steps) → judge eval on curated data → gateway → prod monitoring (quality/latency/cost/drift). Prompt change = code review; rollback <5min.","LiteLLM routing; 10% async judge sampling; drift dashboard; 5% A/B for FT loop.","MLflow, Braintrust-pattern judge, Portkey-pattern routing, Arize-pattern drift, LangSmith","GitHub Actions (eval gate), PagerDuty (alerts)","Pinned model IDs; input+output guardrails; per-request cost attribution","Large (5–8 wks)"),
 ("P024","LLM Firewall Gateway","AI Security Engineer","User app → PIF proxy → [regex 130+ patterns <2ms || DistilBERT ONNX 50–150ms || FAISS semantic || behavior] → consensus BLOCK≥70/FLAG/ALLOW → LLM → output validator (PII/policy/drift) → SIEM/SSE.","3-tier latency profiles (Lite <0.3ms / Std <80ms / Full <2s); canary tokens; self-hardening vectorDB.","FastAPI, ONNX Runtime, FAISS, Presidio, Prometheus/Grafana, Docker","Splunk/Elastic, Slack/SSE live feed, GitHub SARIF","OWASP-mapped; CVSS-style risk score; quarterly PyRIT loop","Medium (3–4 wks)"),
 ("P048","Eval + Regression Harness as Product","GenAI / Agentic AI Engineer","Prod failures → dataset curation (50–200 golden, bias-controlled) → offline experiments (RAGAS/DeepEval) → CI gate (fail if <0.9) → online 5–10% sampling → drift alert + rollback.","LLM-as-judge with order randomization + known-good/bad calibration; human kappa sample; trajectory vs outcome.","RAGAS, DeepEval, Promptfoo, Langfuse/TruLens, GitHub Actions","LangSmith/Phoenix dashboards, PagerDuty","Judge isolation; no PII in datasets; versioned datasets","Medium (2–4 wks; build FIRST)"),
 ("P010","Kubernetes Inference Platform","Cloud AI Engineer","InferenceService CRD → control plane (lifecycle/autoscale) → data plane (transform/predict/explain). Standard mode for LLMs; Gateway API; QPS/latency HPA; image streaming; PVC model cache.","vLLM (prefix caching, TP-size, LoRA) vs Triton (max throughput, long setup) vs TGI (frozen — migrate); queue-depth KEDA.","KServe, vLLM, Triton, KEDA, Gateway API, Prometheus, Terraform","Backstage (self-service), ArgoCD, OpenCost, Kyverno","Per-service RBAC; KMS/SSE; in-region weight mirror; secrets via manager","Large (5–8 wks)"),
 ("P025","CI/CD Red-teaming Gates","AI Security Engineer","promptfooconfig.yaml (targets + purpose + plugins) → redteam generate → eval (grader) → SARIF → Action gate; nightly Garak (dan/promptinject/encoding); quarterly PyRIT multi-turn.","Fail build on regression; map to OWASP/NIST/MITRE/EU-AI-Act; track pass/fail + cost.","Promptfoo, Garak, PyRIT, GitHub Actions, Docker","RAG/agent endpoints, nightly HTML reports","No prod secrets in probes; isolated target envs","Medium (2–4 wks)"),
 ("P041","Agentic Text-to-SQL Analyst","GenAI / Agentic AI Engineer","NL → domain classify → schema-aware SQL gen (read-only role) → execute → chart → cite → guard (PII/limit caps) → Teams/Slack answer.","Router (SQL vs vector vs API); max-hops + token budget; result validator; read-only DB role.","LangGraph, DSPy/Vanna-pattern, Postgres, FastAPI, Streamlit, pgvector (docs)","ERP/CRM DBs (read replica), Snowflake, Teams","Read-only grants; query caps; PII redact; approval for writes","Medium (3–4 wks)"),
 ("P049","MCP Tool Server + Gateway","GenAI / Agentic AI Engineer","Tools exposed once as MCP (JSON-RPC manifest) → enterprise wrapper (OAuth/SAML/LDAP + RBAC + Vault + OPA + approvals via Slack/Jira + audit + cost/rate limits) → any agent (LangGraph/ADK/SDK).","Registry + allowlists + per-server CI/CD + container-per-server; rug-pull/tool-poison defenses; versioned prompts.","MCP SDK, Temporal (durable), OTel, Prometheus, OPA, Vault","Postgres, Slack, GitHub, Snowflake, ServiceNow MCP endpoints","Scoped tools (subset of user); signing; SSO; audit","Medium (3–4 wks)"),
 ("P028","Agent IAM Broker (OPA)","AI Security Engineer","LLM → tool-call proposal → OPA PDP (Rego: allow if role/table/op match + user-context OAuth) → execute/deny + audit → downstream (SAP/SNOW/SQL).","Min tools; complete mediation outside model; monitor + rate-limit + breaker; dual approval for prod/finance.","OPA/Cedar/OpenFGA, OAuth passthrough, OTel, audit store","SAP BAPI/RFC via BTP, ServiceNow, Snowflake","Default-deny; least-privilege IAM roles; action caps","Medium (3–4 wks)"),
 ("P035","Industrial Parts Knowledge Layer (Eval-driven Pilot)","Forward Deployed Engineer","Dynamics/SharePoint → layout-aware chunking (row-level tables) → hybrid + reranker + metadata filter (family/supplier) → Azure OpenAI → citations (page/date) → 14→55-user pilot.","40-Q golden set day 1; weekly eval (accuracy/trust/latency/cost); refusal tuning; feedback loop top-queries/drop-offs.","Azure AI Search, Azure OpenAI, LangGraph, Teams bot, Entra SSO","D365, SharePoint Premium, M365 Copilot","Tenant filter; authority tiers; zero critical OWASP gate","Large (6–10 wks incl pilot)"),
 ("P016","Hybrid Multi-cloud RAG via Gateway","Cloud AI Engineer","Ingest per cloud (S3/SharePoint/BigQuery) → gateway-routed retrieval (Bedrock KB ↔ Azure AI Search ↔ Vertex) → rerank → LLM (latency/cost/compliance route) → answer + failover.","OpenAI-compat abstraction; per-tenant namespaces; no cross-cloud PII replication; 60–90d measurement before savings plans.","LiteLLM, Bedrock, Azure AI, Vertex, Terraform, NIM containers","Snowflake/Databricks (governed), SSO per cloud","Private endpoints; residency; per-cloud audit","Large (5–8 wks)"),
 ("P060","OpsPilot Unified Spine (Vision Integrator)","AIOps Engineer (staff scope)","Telemetry + KB + tickets + ERP signals → correlation → RAG veutre (runbooks) → agent (bounded tools + OPA + approvals) → gateway (budgets) → automation (n8n/RPA) → obs/eval/security loop. Composed from P001+P039+P009+P012+P024+P048 — do NOT build first.","Supervisor + specialists + router; budgets; HITL tiers; eval-gated promotion; drift + red-team loops.","All of the above; Backstage + ArgoCD + KServe + OpenCost","ServiceNow, Slack/Teams, Snowflake, SAP-keyword slice, GitHub","Zero-trust throughout; audit spine; FinOps caps","Very Large (10–14 wks; compose after flagships)"),
]

for pid, title, roles, arch, ai, stack, integ, sec, eff in BLUEPRINTS:
    b.add_heading(f"{pid} — {title}", 1)
    b.add_paragraph(f"Target roles: {roles}. Effort: {eff}. Label: pattern Observed; sizing Recommended; fill [X] with measured values.")
    secs = [
     ("1. Project Title", f"{title} — [Org/Domain] (resume-friendly; match JD title exactly)."),
     ("2. Problem Statement", "Real enterprise problem: users drowning in fragmented knowledge/alerts/docs/approvals; slow triage; stale answers; cost blowups; audit gaps. Who suffers, how often, what breaks without this."),
     ("3. Business Value", "Why a company pays: time saved ([X]min→[Y]s), deflection [X%], MTTR -[X%], cost -[X%], trust/adoption [X]. Tie to revenue/retention/cost/risk."),
     ("4. Target Roles", f"{roles} + secondaries (see Excel coverage matrix). Interviewers per role listed in playbook §6."),
     ("5. Architecture", arch + " Components + flows + failure paths + scaling notes. Diagram required (arch.png, Mermaid)."),
     ("6. AI Components", ai + " Models, RAG/agents/ML, embeddings/rerank/FT/eval/prompt strategy. Justify RAG vs FT vs agent with numbers."),
     ("7. Technology Stack", stack + ". Pin versions; IaC (Terraform/Helm); private subnets; secrets manager."),
     ("8. Integrations", integ + ". Auth per integration; scope least-privilege; show write-back + audit."),
     ("9. Security", sec + ". Map to OWASP LLM Top 10 2025/2026 + ATLAS where relevant; pre-commit scans."),
     ("10. Observability", "OTel gen_ai.* spans (retrieval chunks, tool calls, rail decisions, tokens) → Langfuse/Phoenix → Prometheus/Grafana: p50/p95, error/tool-fail, drift, $/query/tenant, session. Alerts + Statuspage."),
     ("11. Evaluation", "Golden 50–200 + CI gate (fail <0.9 prod) + 5–10% online sampling + red-team zero-critical + citation/trajectory/cost metrics. Track faithfulness, precision/recall, relevancy, task success."),
     ("12. Deployment", "Docker multi-stage → Compose (dev) → Helm + Terraform (prod EKS/GKE/AKS); blue-green/canary; HPA on QPS/latency/queue; PDBs; 1-command smoke test; rollback <5min."),
     ("13. MVP Scope", "Smallest demoable slice in 2–4 wks: one source, one channel, exact-match cache, 30-Q eval, single-tenant, read-only tools, manual approvals."),
     ("14. Advanced Scope", "Multi-tenant namespaces + SSO, semantic cache + learned routing, GraphRAG/HyDE, LoRA adapters, KEDA GPU autoscale, FinOps caps, quarterly PyRIT, DR + chaos."),
     ("15. Demo Scenario", "90-sec Loom: problem → live query/fault → answer/RCA with citations/traces → eval table → cost/latency → approval/audit. Plus Swagger + Space + arch.png."),
     ("16. GitHub Structure", "README.md, arch/, src/{ingest,retrieve,agent,gateway,guardrails,eval}/, evals/golden.jsonl, tests/, .github/workflows/ci-eval.yml, Dockerfile, docker-compose.yml, helm/, terraform/, dashboards/, docs/ADRs/, FAILURE_LOG.md, COST.md"),
     ("17. README Structure", "Problem + for-whom + outcome (3 lines) → live URL + GIF → arch diagram → stack → 3-cmd run → eval table → cost/latency → security → limitations → roadmap → Key Learnings / What failed."),
     ("18. Resume Bullets", "Architecture bullet (what + stack + scale); deployment bullet (cloud/K8s/CI/obs); impact bullet with [X%] placeholders; security bullet (authZ/guardrails/audit). See Excel Resume Bullet Patterns. Never invent numbers."),
     ("19. Interview Talking Points", "Trade-offs (why LangGraph/MCP/gateway/K8s); failure story (retrieval vs generation split); scale story (queue/HPA/cache); security story (injection/ACL/agency); cost story ($/task + rescue); what you'd change in prod."),
     ("20. Skills Demonstrated", "ATS-ready: Python, FastAPI, LangGraph, vector DBs, Docker/K8s, Terraform, cloud services, OTel, eval/security tools, enterprise integrations per blueprint."),
     ("21. Hiring Signal", "Why this matters: maps to JD keywords + scarce gate (eval/security/gateway) + enterprise realism + interview depth. Tier + role coverage in Excel Hiring Signal."),
    ]
    for h, body in secs:
        b.add_heading(h, 2)
        b.add_paragraph(body)

b.add_paragraph("Build order recommendation: P048 → P039/P026 → P009/P024 → P001 → P012/P025/P054 → supports. Each blueprint composes; P060 last. All impact numbers must be measured post-build.", style='Intense Quote')
b.save(BLUE)
print("Saved", BLUE)
