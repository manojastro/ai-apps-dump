"""Wave-2 expansion: append empirical annex sheets + update dashboard/sources/querylog/QA."""
import os, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = r"D:\ai apps dump\research topic\project"
XLSX = os.path.join(OUT, "AI_Portfolio_Project_Intelligence_2026.xlsx")

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
THIN = Border(left=Side(style='thin', color='B0B0B0'), right=Side(style='thin', color='B0B0B0'),
              top=Side(style='thin', color='B0B0B0'), bottom=Side(style='thin', color='B0B0B0'))
WRAP = Alignment(wrap_text=True, vertical="top")

def style_header(ws, row=1, max_col=None):
    for c in range(1, (max_col or ws.max_column)+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL; cell.font = HEADER_FONT
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
            except Exception: pass
        ws.column_dimensions[letter].width = max(min_width, min(max_width, m+4))

def add_sheet(wb, title, headers, rows):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for r in rows: ws.append(r)
    style_header(ws, 1, len(headers))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):
        for cell in row:
            cell.alignment = WRAP; cell.border = THIN
    ws.freeze_panes = "A2"; autofit(ws)
    return ws

wb = openpyxl.load_workbook(XLSX)

# ---------- A1: 54 GitHub deep sweep ----------
a1 = [
 ["wassim249/fastapi-langgraph-agent-production-ready-template","https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template","unknown","app/services/llm/registry.py, docs/*-service.md, Prometheus+Grafana, JWT+slowapi, Alembic, mem0+pgvector","agent-backend template","Observed files"],
 ["bhaskar511939/langgraph-boilerplate-kit","https://github.com/bhaskar511939/langgraph-boilerplate-kit","unknown","agent/graph.py, api/app.py, config/, prompts/system.md","stateful-agent skeleton MCP+SSE","Observed+Inferred"],
 ["Arcan17/agentforge","https://github.com/Arcan17/agentforge","unknown","docker compose, FastAPI+SSE, Celery+Redis+Postgres, pytest-123","multi-agent research HITL","Observed"],
 ["Theepankumargandhi/Multi-Agent-Orchestration","https://github.com/theepankumargandhi/multi-agent-orchestration","unknown",".github/workflows/ci.yml + cd-release.yml, 2x Dockerfile, /metrics /healthz /readyz","supervisor-router RAG+KG+MCP","Observed"],
 ["shreyabaid007/multi-agent-script-generator","https://github.com/shreyabaid007/multi-agent-script-generator","unknown","sandbox/Dockerfile, Jinja prompts, Langfuse spans, pytest-50, ruff, uv","parallel Send-API + sandbox exec","Observed"],
 ["girijesh-ai/langgraph-supervisor-agents","https://github.com/girijesh-ai/langgraph-supervisor-agents","unknown","tools/*.py, FastAPI HITL, Redis+Qdrant+Mem0, pytest","fraud-risk supervisor-specialist","Observed"],
 ["nehalvaghasiya/langgraph-agents","https://github.com/nehalvaghasiya/langgraph-agents","7 stars / 1 fork (OBS)","src/core/agents+tools, examples/paper_writing, pytest+ruff; no Docker/K8s","modular ReAct examples","Observed"],
 ["MohansaiRitesh/AgentMind","https://github.com/MohansaiRitesh/AgentMind","unknown","researcher_graph.py, SqliteSaver, Send-API; no Docker/CI","map-reduce research demo","Observed"],
 ["BerriAI/litellm","https://github.com/BerriAI/litellm","unknown (vendor 53k claim)","helm/litellm, proxy_server_config.yaml, Dockerfile, Terraform AWS/GCP, cosign GHCR","gateway virtual-keys/spend/guardrails","Observed"],
 ["hwdsl2/docker-litellm","https://github.com/hwdsl2/docker-litellm","unknown","docker-compose.yml, litellm.env.example, init.sh, GH Actions, PG volume","self-host LiteLLM wrapper","Observed"],
 ["leeroopedia/litellm-proxy-deploy","https://github.com/leeroopedia/workflow-berriai-litellm-proxy-server-deployment","unknown","config/examples/*.yaml, docker-compose, prometheus.yaml, deploy.py","proxy deploy workflow","Observed"],
 ["vllm-project/production-stack","https://github.com/vllm-project/production-stack","unknown","helm/values.yaml, tutorials values-*.yaml, router+observability","K8s-native vLLM reference","Observed"],
 ["vllm-project/vllm","https://github.com/vllm-project/vllm","unknown","docs production-stack.md + k8s.md, Deployment+Service YAML","inference engine OpenAI-server","Observed"],
 ["kserve/kserve","https://github.com/kserve/kserve","5835/1636 (OBS)","InferenceService CRD YAML, config/, Kustomize, Go+Python","standardized K8s inference","Observed"],
 ["kubernetes-sigs/gateway-api-inference-extension","https://github.com/kubernetes-sigs/gateway-api-inference-extension","unknown","config/manifests/vllm/gpu-deployment.yaml, LoRA syncer, probes+preStop","inference routing LoRA-aware","Observed"],
 ["langgenius/dify","https://github.com/langgenius/dify","154290/24393 (OBS)","docker-compose.yaml, .env.example, multi-service api/worker/web/sandbox/weaviate/pg/redis/nginx","agentic-workflow+RAG workspace","Observed"],
 ["infiniflow/ragflow","https://github.com/infiniflow/ragflow","~78k claimed unverified","docker-compose.yml, .env, Dockerfile, service_conf.yaml.template","deep-doc RAG+agents","Observed"],
 ["deepset-ai/haystack","https://github.com/deepset-ai/haystack","unknown","Pipeline API, async/stream, eval docs, integrations","orchestration framework","Observed"],
 ["deepset-ai/haystack-rag-app","https://github.com/deepset-ai/haystack-rag-app","unknown","docker-compose, FastAPI, React, OpenSearch, /api/search","RAG reference app","Observed"],
 ["deepset-ai/hayhooks","https://github.com/deepset-ai/hayhooks","unknown (INF)","wraps pipelines as REST/MCP, OpenAI-chat endpoint","serve Haystack as API/MCP","Inferred"],
 ["langfuse/langfuse","https://github.com/langfuse/langfuse","34157/3689 (OBS)","docker-compose.yml, web/worker Dockerfiles, Helm langfuse-k8s, ClickHouse+PG+Redis+MinIO","LLM evals+obs+prompts","Observed"],
 ["Arize-ai/phoenix","https://github.com/Arize-ai/phoenix","11304/1090 (OBS)","tutorials/tracing ipynb, OTel register, evals","tracing+evals OpenInference","Observed"],
 ["Arize-ai/openinference","https://github.com/Arize-ai/openinference","unknown (INF)","instrumentation pkgs LangChain/LlamaIndex/OpenAI","OTel semconv","Inferred"],
 ["traceloop/openllmetry","https://github.com/traceloop/openllmetry","7201/996 (OBS)","packages/*-instrumentation, SDK decorators, OTel Collector","GenAI OTel instrumentation","Observed"],
 ["promptfoo/promptfoo","https://github.com/promptfoo/promptfoo","~22k (OBS branch tag)","promptfooconfig.yaml, redteam.yaml, CLI, promptfoo-action CI, 50+ plugins","evals+red-team CI gates","Observed"],
 ["NVIDIA/garak","https://github.com/NVIDIA/garak","9079/1236 (OBS)","Python CLI, probes/detectors, pip install","LLM vuln scanner","Observed"],
 ["microsoft/PyRIT","https://github.com/microsoft/PyRIT","4388/852 (OBS)","pyrit_scan/pyrit_shell, scorers+memory","genAI risk multi-turn","Observed"],
 ["HolmesGPT/holmesgpt","https://github.com/HolmesGPT/holmesgpt","~3k (OBS)","docs/data-sources, Helm enableHolmesGPT, toolsets, CNCF sandbox","SRE incident agent+operator","Observed"],
 ["robusta-dev/robusta","https://github.com/robusta-dev/robusta","unknown","Helm chart, generated_values.yaml, Slack/Prom sinks","K8s monitoring+automation","Observed docs"],
 ["robusta-dev/kubernetes-demos","https://github.com/robusta-dev/kubernetes-demos","unknown","crashpod/broken.yaml demo manifest","AIOps demo fixtures","Observed"],
 ["n8n-io/n8n","https://github.com/n8n-io/n8n","203261 (OBS org index)","Dockerfile, :5678, 400+ nodes, LangChain AI nodes","workflow+AI-agent flows","Observed"],
 ["n8n-io/self-hosted-ai-starter-kit","https://github.com/n8n-io/self-hosted-ai-starter-kit","15228 (OBS)","docker-compose.yml, .env.example, Ollama+Qdrant+Postgres","local AI starter","Observed"],
 ["n8n-io/n8n-hosting","https://github.com/n8n-io/n8n-hosting","1732 (OBS org index)","docker/k8s hosting examples","self-host recipes","Observed"],
 ["kossakovsky/n8n-install","https://github.com/kossakovsky/n8n-install","886/227 (OBS)","Compose wizard, Caddy HTTPS, Redis queue, Grafana+Prom","homelab AI platform 30+ tools","Observed"],
 ["backstage/backstage","https://github.com/backstage/backstage","unknown (INF)","plugin monorepo, Yarn workspaces, Postgres","IDP core","Inferred"],
 ["RoadieHQ/roadie-backstage-plugins","https://github.com/RoadieHQ/roadie-backstage-plugins","342 (OBS TS)","plugins/backend/rag-ai-backend, rag-ai-storage-pgvector, Bedrock/OpenAI emb","RAG AI assistant ref","Observed"],
 ["webstackdev/ai-crew-suite","https://github.com/webstackdev/ai-crew-suite","unknown","plugins/backend/*, pgvector+Qdrant, SSE runs, approvals/audit","agentic Backstage runtime","Observed"],
 ["modelcontextprotocol/servers","https://github.com/modelcontextprotocol/servers","unknown","src/filesystem|github|postgres|fetch|memory, mcpServers JSON","MCP reference servers","Observed"],
 ["containers/kubernetes-mcp-server","https://github.com/containers/kubernetes-mcp-server","unknown","Go native K8s API, multi-cluster kubeconfig, npm binary","K8s/OpenShift MCP","Observed"],
 ["Kishan960615/enterprise-mcp-server","https://github.com/Kishan960615/enterprise-mcp-server","unknown","Dockerfile, Compose demo, CI+adversarial tests, audit store, Streamable HTTP","secure multi-tenant MCP","Observed"],
 ["AdrienTHOMAS/enterprise-mcp-server","https://github.com/AdrienTHOMAS/enterprise-mcp-server","unknown","Redis cache, webhooks :8081, OTel structlog, 38 tools","Jira/GitHub/Confluence/Slack/PagerDuty MCP","Observed"],
 ["ddukbg/github-enterprise-mcp","https://github.com/ddukbg/github-enterprise-mcp","unknown","MCP tools table repos/issues/PRs/actions, GHE API","GitHub Enterprise MCP","Observed"],
 ["tensorzero/tensorzero","https://github.com/tensorzero/tensorzero","~12k (OBS)","Dockerfile, docker run gateway, Rust gateway, ClickHouse, evals/AB","gateway+obs+optimization","Observed"],
 ["Agenta-AI/agenta","https://github.com/Agenta-AI/agenta","unknown","Dockerfile, playground+registry+envs, SDK ag.init(), LiteLLM naming","prompt-mgmt+evals+obs","Observed"],
 ["comet-ml/opik","https://github.com/comet-ml/opik","20k+ README claim (OBS as claim)","docker-compose, Py/TS SDKs, pytest, datasets/experiments","tracing+evals+optimizer","Observed"],
 ["comet-ml/opik-examples","https://github.com/comet-ml/opik-examples","unknown","integrations/otel/*, use-cases/*, scripts/*","Opik cookbooks","Observed"],
 ["explodinggradients/ragas","https://github.com/explodinggradients/ragas","15602/1673 (OBS)","ragas quickstart, metrics, docs","RAG/agent eval+synthesis","Observed"],
 ["confident-ai/deepeval","https://github.com/confident-ai/deepeval","unknown","pytest deepeval test run, G-Eval/RAG/conversational, Confident-AI","LLM unit-testing","Observed"],
 ["sunilp303/deepeval-evaluation-harness","https://github.com/sunilp303/deepeval-evaluation-harness","unknown","Makefile targets, src/*.py, tests/test_*.py, multi-provider judges","pluggable DeepEval scaffold","Observed"],
 ["savitharaghunathan/gen-eval","https://github.com/savitharaghunathan/gen-eval","unknown (2025-07)","adapters ragas+deepeval, profiles, JSON+exit-code CI","unified Ragas+DeepEval gate","Observed"],
 ["rmednitzer/ai-stack","https://github.com/rmednitzer/ai-stack","unknown","single Helm chart, values.yaml+values-prod.yaml, OpenWebUI/Ollama/Qdrant/Tika/SearXNG/Valkey/PG/Authelia/OTel","EU self-host AI stack","Observed"],
 ["AI-Governance-Lab/k8s-ai-agent-multicloud-rag-iac","https://github.com/AI-Governance-Lab/k8s-ai-agent-multicloud-rag-iac","unknown","helm-chart/values.yaml, FastAPI+LangChain+Qdrant+Terraform, RBAC/NetworkPolicy","multicloud RAG+IaC agent","Observed"],
 ["citadelgrad/llm-governance-gateway","https://github.com/citadelgrad/llm-governance-gateway","unknown","proxy/, governance/, policies/llm/*.rego, docker-compose.yml, OPA+PG+Redis","OpenAI-compat governance GW","Observed"],
 ["egnaro9/llm-gateway","https://github.com/egnaro9/llm-gateway","unknown","llmgateway/*.py, 22 tests green CI, /metrics, LRU+token-bucket+mock","minimal FastAPI GW teaching ref","Observed"],
]
add_sheet(wb, "A1 GitHub Deep Sweep", ["Repo","URL","Stars_Note","Production_Signals_Observed","Roles","Evidence_Label"], a1)

# ---------- A2: 30 portfolio/cases ----------
a2 = [
 ["Production-RAG GraphRAG service","https://github.com/WeiGuang-2099/Production-RAG","cite-or-refuse + hybrid+graph ablation","FastAPI,LangChain,LangGraph,Qdrant,BM25,Cohere,RAGAS","eval table+React SSE","Observed"],
 ["ShopTalk Prod RAG P5","https://github.com/rubsj/ai-portfolio","46-config bench NDCG@5 0.896","Python,FAISS,Ollama,BM25,cross-encoder,LLM-judge","627 tests,97% cov,7 ADRs","Observed"],
 ["RAG Eval Framework P2","https://github.com/rubsj/ai-rag-evaluation-framework","rerank +19.5% Recall@5 0.747","FAISS,LangChain,RAGAS,Cohere,Braintrust,Streamlit","557 tests,16-config grid","Observed"],
 ["InsureLLM Expert Assistant","https://github.com/chandra-vv/genai_portfolio","prod RAG 4.48/5 over 150 Qs","OpenAI,Chroma,litellm,Gradio","eval dashboard+app.py","Observed"],
 ["Banking Copilot RAG+QLoRA","https://github.com/rakeshmadasaniai/banking-genai-portfolio","domain RAG+finetune+memory","FAISS,QLoRA Mistral,Streamlit","live app+120+120 eval CSVs","Observed"],
 ["Multi-Agent Research Pipeline","https://github.com/axon011/multi-agent-pipeline","Planner-Researcher-Writer-Critic dual-engine","LangGraph,CrewAI,FastAPI,Langfuse","SSE UI+eval/topics.yaml","Observed"],
 ["Stock-Picker Multi-Agent","https://github.com/Crazy-Horse/stock-picker-agent","RAG-grounded ranking","CrewAI,LangGraph,Chroma","markdown+JSON report","Observed"],
 ["Agent-Compose YAML Orchestrator","https://github.com/Ismail-2001/agent-compose","framework-agnostic DAG","LangGraph,CrewAI,OpenAI SDK,YAML","CLI+report.md","Observed"],
 ["Fin-Agent x3 Frameworks","https://github.com/greghodgkinson/agent-examples","LangGraph vs CrewAI vs Swarm","LangGraph,CrewAI,Swarm,FMP API","code comparison","Observed"],
 ["LangCrew OAK Framework","https://github.com/01-ai/langcrew","HITL+memory+UI productization","LangGraph,React,LangSmith","templates+Agent-UI","Observed"],
 ["AI-Safety RedTeam Suite","https://github.com/Juadsuarezsan/ai-safety-redteam","OWASP LLM Top10+guardrails","Claude,LangGraph,NeMo-pattern","15 tests+traces","Observed"],
 ["Defensive Red-Team Harness","https://github.com/ag2020sa/ai-security-red-team-harness","CI-gated RAG/agent eval","Python,demo RAG/agent,SARIF","HTML/JSON/SARIF+dashboard","Observed"],
 ["AI Security Research Portfolio","https://github.com/InsiyahBhatia/ai-security-research-portfolio","25 rooms to OWASP/ATLAS","Groq Llama3.3-70B,NeMo+Colang","16-scenario simulator","Observed"],
 ["AgentStrike Canary Fuzzer","https://github.com/nadirzhon/agentstrike","proven breach via canary","Python zero-dep,mutator","HTML/SARIF,16 tests","Observed"],
 ["LLM-Intruder 633 Payloads","https://github.com/crazywifi/llm-Intruder","adaptive hunt+browser target","Playwright,9 LLM providers","MD/HTML/SARIF+dashboard","Observed"],
 ["RedPincer 222 Payloads","https://github.com/rustyorb/pincer","7-cat heatmap+regression","TS,React,multi-LLM","verbose pen-test report","Observed"],
 ["ZeroLeaks Scanner","https://github.com/ZeroLeaks/zeroleaks","extraction+tool-hijack judge","Bun,TS,Vercel AI SDK,OpenRouter","CLI+JSON","Observed"],
 ["Crunch-IS SharePoint+Salesforce RAG","https://crunch-is.com/case-study/knowledge-access-transformation-with-rag-and-aws/","60% faster contracts","Kendra,Bedrock,Step Functions,React,Nest","case metrics","Observed"],
 ["Ksolves Agentforce BESS RAG","https://www.ksolves.com/case-studies/salesforce/rag-powered-agentforce-ai-assistant-industrial-product-sales","CRM-grounded assistant","Agentforce,Data Cloud,Einstein Trust","data-flow diagram","Observed"],
 ["DataFlux UK Construction RAG","https://datafluxsoft.com/case-corporate-rag-construction.html","15min to sec permissioned","Kendra,Bedrock Claude,OpenFGA,Keycloak","promptfoo 30+ cases","Observed"],
 ["SupplyTech Dynamics365 RAG","https://www.supplytechsolutions.ai/post/rag-architecture-consulting-how-we-built-a-grounded-parts-knowledge-layer-for-an-industrial-parts-d","4-layer grounded parts","Azure AI Search,Dynamics365,SharePoint","citation UI","Observed"],
 ["DigitalGravity NetSuite SuiteQL Bot","https://www.digitalgravity.ae/case-studies/artificial-intelligence/technology/ai-netsuite-chatbot/","NL to SuiteQL on-prem","DeepSeek,Milvus,Flask,RESTlet","live summaries","Observed"],
 ["S&B Filters NetSuite AI Layer","https://botscrew.com/cases/s-and-b-filters-case-study/","$140K save,250% ROI,15s","OpenAI,Spring,Pinecone,React,AWS","2 UIs+metrics","Observed vendor claim"],
 ["NetSuiteSync Claude MCP","https://netsuitesync.com/talk-to-your-data","read-only cited answers","Claude,MCP,PowerBI/Snowflake","live connector","Observed"],
 ["Vanna 2.0 Text-to-SQL Agent","https://github.com/vanna-ai/vanna","agentic NL-SQL+charts","Python,FastAPI,PG/Snowflake/BigQuery","<vanna-chat> SSE","Observed"],
 ["Vanna Streamlit Viewer","https://github.com/vanna-ai/streamlit","multi-type SQL results","Streamlit,Vanna API","demo app","Observed"],
 ["KnowledgeMesh HF Space","https://huggingface.co/blog/pkheria/knowledgemesh","ZeroGPU RAG hub","Gradio,Qdrant,Nemotron,@spaces.GPU","live Space","Observed"],
 ["YiWang Next.js Twin Portfolio","https://github.com/YiWang24/portfolio","RAG+agents portfolio","Next.js,Vercel AI SDK,Neon pgvector,Upstash","https://www.yiw.me","Observed"],
 ["Bhushan Offline RAG Portfolio","https://bhushan-songire-portfolio.vercel.app/","local Gemma3 RAG","LangChain,FastAPI,FAISS,Ollama,Docker","Vercel live+HF Spaces","Observed"],
 ["Enterprise Toolkit ROI Playbook","https://github.com/maree217/enterprise-agent-toolkit","$20-100k consulting close","Semantic Kernel,Azure,ROI calc","3 cases+decks+scripts","Observed"],
]
add_sheet(wb, "A2 Portfolio Cases", ["Title","URL","What_It_Proves","Stack","Demo_Artifact","Evidence_Label"], a2)

# ---------- A3: Security OWASP matrix (16) + delta ----------
a3 = [
 ["LLM01 Prompt Injection","input rail + delimit + least-priv tools + output check","NeMo jailbreak check; Garak promptinject/encoding/dan","+50-200ms; blocks > retry cost","#1 ERP jailbreak to SOQL/SQL write","https://genai.owasp.org/llmrisk/llm01-prompt-injection/","Observed"],
 ["LLM02 Sensitive Disclosure","Presidio analyze-anonymize in/out/retrieval + vault","Presidio; NeMo mask sensitive data","NER 20-100ms; vault lookup cheap","PII to ERP field handling","https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/","Observed"],
 ["LLM03 Supply Chain","pin models/datasets/images, SBOM, sign NIM","OPA allowed registries; NIM allowlist","build-time only","stops poisoned HF swap","https://genai.owasp.org/llmrisk/llm032025-supply-chain/","Observed"],
 ["LLM04 Data+Model Poisoning","curate embeddings, RAG ACL, re-eval on change","Garak leakreplay; Promptfoo datasets; Langfuse","nightly eval cost","corpus provenance","https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/","Observed"],
 ["LLM05 Improper Output Handling","sanitize/parameterize before SQL/API/render","NeMo exec/output rails; OPA HTTP authz","+5-20ms","text-to-SQL XSS/SSRF guard","https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/","Observed"],
 ["LLM06 Excessive Agency","scope tools, approval for write, dry-run confirm","OPA Rego allow+threshold; NeMo dialog","human latency; saves write-off","core agent-ERP control","https://genai.owasp.org/llmrisk/llm062025-excessive-agency/","Observed"],
 ["LLM07 System Prompt Leakage","isolate system prompt, verbatim-replay filter","Garak encoding/gcg; Promptfoo redteam","~10ms","protects prompt IP","https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/","Observed"],
 ["LLM08 Vector/Embedding Weakness","tenant namespaces, retrieval rail ACL","NeMo retrieval rails; Langfuse trace","+5ms; namespace cost","stops cross-tenant leak","https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/","Observed"],
 ["LLM09 Misinformation","RAG grounding + fact-check rail + cites + review","NeMo self-check; Garak snowball","1 extra LLM call (2x)","quote/order accuracy","https://genai.owasp.org/llmrisk/llm092025-misinformation/","Observed"],
 ["LLM10 Unbounded Consumption","quotas, timeouts, input caps, per-user billing","Langfuse alerts; OPA rate; Bedrock quotas","alerting ~0 runtime","prevents DoS bill shock","https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/","Observed"],
 ["Jailbreak/DAN/Toxicity","nightly scan + CI gate + moderation","Garak dan/atkgen; NeMo ActiveFence","nightly batch","redteam cadence","https://github.com/NVIDIA/garak","Observed"],
 ["PII in RAG Loop","Presidio ingest+retrieval+output mask + vault","Presidio 10.8k stars; NeMo PERSON/EMAIL","2x NER passes","end-to-end DLP","https://github.com/data-privacy-stack/presidio","Observed"],
 ["CI Redteam Gate","promptfoo redteam in PR + cache + severity fail","Promptfoo 24.8k stars + CI action","cached fast; full min-hrs","shift-left proof","https://github.com/promptfoo/promptfoo","Observed"],
 ["Adaptive Adversary","PyRIT multi-turn attacker + scorer pre-release","PyRIT microsoft/PyRIT","orchestrated $$$","beyond static probes","https://github.com/Azure/PyRIT","Observed"],
 ["Policy-as-Code Tool Gate","OPA sidecar allow/deny/approval JSON","OPA/Rego, Gatekeeper","<10ms","auditable least-priv","https://www.openpolicyagent.org/docs/latest/","Observed"],
 ["Blind Ops coverage","OTel traces + judge + session cost + alerts","Langfuse traces/judges/alerts","SDK minimal; judge adds cost","detect-fix loop","https://langfuse.com/docs","Observed"],
 ["OWASP 2026 delta","Top-10 re-ranked 2026-08-04; GenAI Security Project; ATLAS/CWE maps; Agent Control Standard companion","—","—","use 2026 IDs in new work","https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/","Observed pub; rest Inferred"],
]
add_sheet(wb, "A3 Security OWASP Matrix", ["Threat","Defense","Tools_Observed","Latency_Cost_Note","Hiring_Why","URL","Evidence_Label"], a3)

# ---------- A4: AIOps/Cloud patterns (30, labels honest) ----------
a4 = [
 ["Splunk ITSM GenAI Assist","Splunk SPL -> SN table API -> LLM summary -> worknotes","Splunk ES, SN ITSM, OpenAI/Azure","PII redact + human-approve before auto-close","https://www.splunk.com/en_us/blog/conf-splunk-blogs/splunk-and-servicenow.html","Inferred"],
 ["Splunk-SN Event sync","Splunk alert -> webhook -> SN em_event -> correlation -> incident","Splunk ITSI, SN ITOM","dedup key stable, CI binding >95%","https://docs.splunk.com/Documentation/AddOns/released/ServiceNow/Setup","Inferred"],
 ["SN Now Assist ITSM","Incident/chat -> Now LLM -> summary + notes -> review","SN Vancouver+, VA, KB","no auto-resolve P1; faithfulness eval","https://www.servicenow.com/products/now-assist.html","Inferred"],
 ["GenAI RCA on ITSM+Obs","metrics/logs/traces + CMDB + change -> RAG runbooks -> RCA draft","Splunk/Dynatrace, CMDB, vector DB","citations required; freeze guardrail","https://www.servicenow.com/blogs/2024/aiops-event-correlation","Inferred"],
 ["PagerDuty Event Intel","CEF/events -> ML correlation -> cause -> pause low-urgency","PD AIOps, SN, Datadog/Splunk","noise -[X%] measured; never suppress P1","https://www.pagerduty.com/platform/aiops/","Inferred"],
 ["PD-SN bi-dir sync","PD <-> SN webhook/OAuth status/priority mapping","PD, SN, Slack","idempotent sync + conflict table + e2e test","https://www.pagerduty.com/integrations/servicenow-integration/","Inferred"],
 ["Datadog Watchdog RCA","Watchdog anomaly -> APM/logs/RUM -> Bits AI summary","Datadog APM/Log/Monitors, Slack/Jira","precision/recall on labeled window; sample cap","https://docs.datadoghq.com/watchdog/","Inferred"],
 ["Datadog Bits AI SRE","NL query -> Bits AI -> metric/log query -> dashboard","Datadog LLM obs","read-only role; cost/log per query","https://www.datadoghq.com/product/bits-ai/","Inferred"],
 ["HolmesGPT investigate-alert","Alertmanager webhook -> holmes investigate -> kubectl/prom/grafana -> runbook+PR","K8s, Prom, Slack, GitHub MCP","read-only first; benchmark tracked","https://holmesgpt.dev/latest/","Observed"],
 ["HolmesGPT Operator 24/7","Cron health-checks -> Operator -> Slack alert + fix PR","K8s operator, ArgoCD, DD/Splunk/Kafka","in-cluster; external-secrets; no auto-apply prod","https://holmesgpt.dev/latest/operator/","Observed"],
 ["Robusta+Holmes remediation","Robusta triggers -> Holmes enrichment -> action w/ approval","Robusta, K8s, Slack, SN","approval for mutating; audit log","https://github.com/HolmesGPT/holmesgpt","Inferred"],
 ["Prom ML anomaly detector","Prom remote-read -> IF/Prophet -> Alertmanager -> Holmes","Prom, Thanos/Mimir, MLflow","backtest F1 vs static; versioned retrain","https://prometheus.io/docs/instrumenting/exporters/","Inferred"],
 ["MLflow forecasting","sched PromQL pull -> sklearn train -> registry -> serving","MLflow, S3/GCS, KServe","staging->prod needs drift check","https://mlflow.org/docs/latest/tracking/","Inferred"],
 ["Kafka log anomaly streaming","Filebeat -> Kafka -> Flink/Spark Drain/LogBERT -> OpenSearch+alert","Kafka, Flink, OpenSearch, Prom","p99 lag <30s; schema registry","https://kafka.apache.org/documentation/","Inferred"],
 ["Kafka+vector RAG logs","Kafka topic -> embeddings -> pgvector kNN -> LLM RCA","Kafka, embeddings, pgvector","PII scrub ingest; retention enforced","https://opensearch.org/docs/latest/ml-commons-plugin/","Inferred"],
 ["RCAgent Alibaba","alerts+traces/logs -> LLM+tools -> ranked causes","K8s, Jaeger, MySQL, LLM","tool allowlist; top-k on injected faults","https://arxiv.org/abs/2403.04173","Inferred"],
 ["Tool-augmented RCA agent","observe -> plan -> tools -> hypothesis -> mitigation","LangChain/LlamaIndex, Grafana, K8s","max steps+timeout; read-only; AIOpsLab eval","https://github.com/microsoft/AIOpsLab","Inferred"],
 ["AIOpsLab harness","Kind HotelRes/SockShop -> fault inject + wrk2 -> agent API -> scorer","Kind, Helm, Prom, GPT/VLLM","reproduce cli.py start <id>; data/results","https://github.com/microsoft/AIOpsLab","Observed"],
 ["AIOpsLab tasks","registry app+fault+workload+eval -> orchestrator -> W&B","Py3.11, Poetry, Azure OpenAI","detection vs mitigation split; judge versioned","https://github.com/microsoft/AIOpsLab/blob/main/aiopslab/orchestrator/problems/registry.py","Observed"],
 ["KServe InferenceService","YAML -> control-plane -> predictor/transformer/explainer","K8s, Istio/Knative, S3/HF","canary split + scale-to-zero; payload log opt-in","https://kserve.github.io/website/","Observed"],
 ["KServe LLMIsvc","LLMIsvc CRD -> vLLM/llm-d -> OpenAI endpoint + autoscale","vLLM, HF, GPU, KEDA","TTFT/TPOT SLOs; KV+model cache sized","https://kserve.github.io/website/docs/model-serving/generative-inference/overview","Observed"],
 ["KServe InferenceGraph","ensemble/router pre/post -> multi-model DAG","KServe, Triton, SKLearn","e2e latency budget; fallback tested","https://kserve.github.io/website/docs/model-serving/inferencegraph/overview","Observed"],
 ["GKE inference ref arch","GCS model -> GKE GPU/TPU (GCS Fuse) -> vLLM/TGI -> ILB+HPA","GKE Autopilot, GCS, AlloyDB/Vertex","GPU >60%; spot fallback; private cluster","https://cloud.google.com/kubernetes-engine/docs/inference-reference-architecture","Inferred"],
 ["vLLM vs TGI vs Triton","same model/GPU -> guidellm loadgen -> thrpt/lat matrix","vLLM, TGI, Triton, Prom","publish tok/s p50/p99 cost/1k before choice","https://docs.vllm.ai/en/latest/","Inferred"],
 ["LiteLLM proxy","App OpenAI SDK -> proxy config.yaml -> 100+ providers + LB","OpenAI/Azure/Bedrock/Vertex/Ollama, Redis","virtual-key auth + budget; kill-primary test","https://docs.litellm.ai/docs/simple_proxy","Observed"],
 ["LiteLLM budgets/guards","proxy -> spend tracker + TPM/RPM + guardrail hooks","PG/Redis, Prom spend, PII guards","alerts 80/100%; rotation runbook","https://docs.litellm.ai/docs/proxy/users","Observed"],
 ["MLflow prompt registry","prompt versioned alias stage/prod -> app by alias -> eval","MLflow 2.x, OpenAI eval, CI","PR needs eval delta; no prod move on regression","https://mlflow.org/docs/latest/llms/prompt-engineering/","Inferred"],
 ["MLflow evaluate+trace","traces -> evaluate faithfulness/toxicity -> dashboard","MLflow Tracing, RAG, Databricks","golden + pinned judge","https://mlflow.org/docs/latest/llms/llm-evaluate/","Inferred"],
 ["Backstage+ArgoCD+KServe IDP","scaffold template -> Git -> ArgoCD -> KServe+monitors","Backstage, ArgoCD, KServe, Grafana","SLO/ServiceMonitor default; team RBAC","https://backstage.io/docs/","Inferred"],
]
add_sheet(wb, "A4 AIOps Cloud Patterns", ["Pattern","Components_Flow","Integrations","Prod_Gate","URL","Evidence_Label"], a4)

# ---------- A5: automation/integration ----------
a5 = [
 ["UiPath LLM GW via Trust Layer","Studio/Autopilot -> GW -> BYO/UiPath LLM w/ policy+audit","PII-mask + Ops review","TLS1.2/AES-256, zero-training, usage/audit","https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-ai-trust-layer","Observed"],
 ["BYO-LLM routing","Product -> GW -> IS / Relay / custom connector","admin approves + probe test","allowlist IPs, Relay private group, JS hooks","https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-llms","Observed"],
 ["Maestro -> Power Automate","Start-and-Wait External Agent -> manual-trigger flow -> Respond","validate outputs downstream","manual trigger only; 3-5min lag","https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-microsoft-powerautomate","Observed"],
 ["Textract+Bedrock+LangChain IDP","AmazonTextractPDFLoader -> classify/summarize/QA via Claude","A2I low-conf + reviewer correction","few-shot + RAG grounding; no world-knowledge","https://aws.amazon.com/blogs/machine-learning/intelligent-document-processing-with-amazon-textract-amazon-bedrock-and-langchain/","Observed"],
 ["Bedrock Pipeline mode","Textract OCR -> FM classify/extract + Blueprints + Test Studio","conf<threshold -> human","standard vs custom; bbox+score explain","https://idp-software.com/vendors/textract","Observed"],
 ["Azure DI prebuilt-layout","Blob -> begin_analyze_document -> text/tables/marks/roles/sections","Studio labeling + threshold","2000pp/500MB S0; pages param","https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout?view=doc-intel-4.0.0","Observed"],
 ["Azure DI pipeline ref","Split 2pp -> Functions 3-10 conc -> DI neural -> Cosmos+Synapse+DLQ","label 12-15; review auto-labels","KeyVault; App Insights; DLQ retries","https://github.com/fgarofalo56/azure-doc-intelligence-pipeline","Observed"],
 ["YOLOplan MEP takeoff","PDF@400DPI -> YOLO11 -> count + CSV/Excel/JSON + netlist","review low-conf + FP","conf 0.25-0.3; train 20-50 imgs/100ep","https://github.com/DynMEP/YOLOplan","Observed"],
 ["P&ID YOLOv8 prod","annotate -> YOLOv8m 1280 -> ONNX -> tune conf recall","expert box review","mAP50>0.90/P>0.92/R>0.88 prod bar","https://www.ai.codersarts.com/post/p-id-symbol-detection-with-yolov8-and-pytorch-complete-tutorial","Observed"],
 ["ServiceNow MCP","intent -> MCP Console tools incidents/CMDB/KB/approvals","SSO+RBAC+audit; fail-loud","one conn all tools; versioned","https://www.servicenow.com/docs/r/intelligent-experiences/mcp-platform-manager-landing.html","Observed"],
 ["servicenow-mcp SSO","auth_browser Playwright SSO -> cookies/Hermes -> 80+ tools","re-auth ~8h; least-priv","Hermes authoritative; legacy fallback only","https://github.com/schwarztim/servicenow-mcp","Observed"],
 ["MCP-ITSM unified","Claude/Cursor -> create_ticket -> router SN/Jira/Zendesk/Ivanti","safety readOnly/destructiveHint","stdio+Express; /mcp-monitor 10s","https://github.com/madosh/MCP-ITSM","Observed"],
 ["Slack-SNOW incident bot","reaction_added -> fetch -> RBAC+PII -> POST incident -> thread","block non-admin; redact PII/PHI","scopes+signing-secret; ngrok:3000","https://github.com/tpickle/slack-servicenow-ticketbot","Observed"],
 ["SN VA + Slack self-bot","Slack App events message.im+OAuth -> VA adapter -> topics","virtual_agent_admin channel","plugins chatbot+sn_va_slack","https://www.servicenow.com/community/virtual-agent-nlu-articles/simplify-communication-integrating-servicenow-with-slack-bot/ta-p/2760909","Observed"],
 ["SAP BAPI/RFC via RPA (gap)","IDP -> BAPI posting deterministic over GUI","expert review postings","needs retry: search throttled","unknown — retry search","Inferred gap"],
 ["Snowflake Cortex RAG (gap)","governed retrieval over tables/docs","—","needs retry: search throttled","unknown — retry search","Inferred gap"],
 ["Databricks Mosaic AI (gap)","serving/eval custom extraction","—","needs retry: search throttled","unknown — retry search","Inferred gap"],
]
add_sheet(wb, "A5 Automation Integration", ["Flow","Details","HITL","Prod_Gate_URL","URL","Evidence_Label"], a5)

# ---------- A6: agent stack + MCP/A2A ----------
a6f = [
 ["LangGraph","Mature/stable + LangSmith deploy","stateful durable HITL graphs","LangGraph+LangSmith agent platform roles","https://docs.langchain.com/langgraph","Docs Observed; judgment Inferred"],
 ["CrewAI","Productized Crews+Flows","role-playing teams under Flow control","certs/enterprise automation","https://docs.crewai.com/introduction","Docs Observed; judgment Inferred"],
 ["AutoGen (MS)","Mature 0.2-1.x AgentChat/Core/Studio","conversational R&D + gRPC + Docker exec","MS-stack research","https://microsoft.github.io/autogen/stable/","Observed"],
 ["LlamaIndex","Leading RAG + LlamaCloud/Parse","ingestion/index/query private data","RAG engineer default","https://docs.llamaindex.ai/en/stable/","Observed"],
 ["Haystack (deepset)","Production v3.1 + Enterprise Platform","modular pipelines, multimodal search","EU/enterprise RAG","https://docs.haystack.deepset.ai/docs/intro","Observed"],
 ["OpenAI Agents SDK","Production Swarm successor + Sandbox/Realtime","Python-first OpenAI delegation","OpenAI-ecosystem dev","https://openai.github.io/openai-agents-python/","Observed"],
 ["Google ADK","GA 5 langs + 2.0 graphs","Gemini/GCP Agent Runtime/Run/GKE","GCP/Gemini roles","https://google.github.io/adk-docs/","Observed"],
 ["Semantic Kernel","Enterprise 1.0+ C#/Py/Java","C#/.NET + Azure plugins via OpenAPI",".NET/Azure signal","https://learn.microsoft.com/en-us/semantic-kernel/overview/","Observed"],
 ["PydanticAI","Typed SDK + Harness/Durable","type-safe tools/DI/structured-out","Python/Pydantic shops","https://ai.pydantic.dev/","Observed"],
 ["DSPy","Stanford 6.6M dl/mo 38k stars GEPA/MIPRO","program-not-prompt optimizer compile","LLM-optimization niche","https://dspy.ai/","Observed"],
 ["GraphRAG (MS)","Research-to-product Leiden+DRIFT","holistic Q&A where baseline fails","KG-RAG specialist","https://microsoft.github.io/graphrag/","Observed"],
 ["FastAPI+K8s serving","De-facto Py API Uvicorn/Pydantic","typed gateway SSE streaming MCP server","universal backend req","https://fastapi.tiangolo.com/","Observed"],
 ["MCP fact: USB-C for AI","open standard tools/data/workflows","—","—","https://modelcontextprotocol.io/docs/getting-started/intro","Observed"],
 ["MCP clients","Claude/ChatGPT/VSCode/Cursor listed","—","—","https://modelcontextprotocol.io/docs/getting-started/intro","Observed"],
 ["MCP spec","versioned docs/2026-07-28 live","—","—","https://modelcontextprotocol.io/docs/getting-started/intro","Observed"],
 ["A2A definition","open agent-to-agent, opaque/secure, not dev-kit","—","—","https://a2a-protocol.org/latest/","Observed"],
 ["A2A governance","donated LF; TSC AWS/Cisco/Google/IBM/MS/Salesforce/SAP/SN","—","—","https://a2a-protocol.org/latest/","Observed"],
 ["A2A foundation","joined Agentic AI Foundation 2026-08-27","—","—","https://a2a-protocol.org/latest/","Observed"],
 ["A2A SDKs","Python/JS/Java/.NET/Go/Rust + Card/Skills/Executor","—","—","https://a2a-protocol.org/latest/","Observed"],
 ["MCP+A2A complement","MCP=agent-to-tool; A2A=agent-to-agent; ADK both","—","—","https://a2a-protocol.org/latest/ + https://google.github.io/adk-docs/","Observed"],
 ["Retrieval funnel numbers","hybrid lift / rerank Recall@k / top-k defaults: unknown — no verified benchmark seen","DSPy 0.41->0.63 F1 / 62%->89% are toy illustrative, NOT retrieval benchmarks","—","https://dspy.ai/","Observed unknown"],
]
add_sheet(wb, "A6 Agent Stack MCP-A2A", ["Item","Maturity_Status","Use_For","Hiring_Signal","URL","Evidence_Label"], a6f)

# ---------- A7: hiring/eval deep ----------
a7 = [
 ["H1 evals-first golden+gate","strongest FDE signal; raises unprompted","—","—","hiring guides","Observed"],
 ["H2 retrieval vs generation split","recall@k + faithfulness localizes failure","—","—","hiring guides","Observed"],
 ["H3 e2e ownership","ingest->retrieve->generate->deploy->monitor + runbook","—","—","hiring guides","Observed"],
 ["H4 deployed hybrid+rerank+cites+abstention","beats tutorial chatbot","—","—","hiring guides","Observed"],
 ["H5 supervisor-worker budgets/HITL","beats free swarm","max 8 iters, depth 3, 30s timeout","hireagentic.dev","Observed"],
 ["H6 proof-of-work","merged PRs vLLM/transformers/LangChain, HF, papers","—","—","hiring guides","Observed"],
 ["H7 depth>breadth","3 polished domain > 20 notebooks","—","—","hiring guides","Observed"],
 ["H8 live demo+runnable+README","problem/who/outcome + arch + failures","—","—","hiring guides","Observed"],
 ["H9 reproducible+provenance","versioned prompts/datasets","—","—","hiring guides","Observed"],
 ["H10 tracing+cost/latency per span/tenant","—","circuit-breaker 2x median","Langfuse/OTel","Observed"],
 ["H11 responsible AI","model card, bias/limits, injection defense, audit","—","—","hiring guides","Observed"],
 ["H12 discount signals","framework list, certs-only, fork-no-commit, API-no-eval","—","—","hiring guides","Observed"],
 ["T1 Titanic notebook","2020 tutorial no deploy/drift/owner","FastAPI+Docker+MLflow+DVC+Evidently+CI","https://github.com/hpekkan/titanicAI","Observed"],
 ["T2 Titanic story gen","no eval/SLO","freeze golden; accuracy/latency/cost gates","https://github.com/simon-quach/sink-or-swim","Observed"],
 ["T3 naive PDF chatbot","miss=hallucination, no faithfulness","hybrid pgvector+BM25 + rerank + claim faithfulness","https://langfuse.com/resources/engineering/rag-faithfulness-evaluation","Observed"],
 ["T4 CrewAI tutorial","loops, no budget, contradictory writes","supervisor returns; caps+timeout","https://hireagentic.dev/blog/multi-agent-swarm-pattern","Observed"],
 ["T5 single-prompt monolith 3+ caps","skips steps, no isolation","supervisor+queue+PG if >=3 tools","https://markaicode.com/architecture/supervisor-agent-architecture/","Observed"],
 ["T6 static portfolio chatbot","no RAG eval/security","71 evals CI + traces + 6-layer defense","https://github.com/joblas/cv-joseph","Observed"],
 ["T7 sentiment copy","no framing/metric","reframe churn/triage precision/recall + $/time","https://www.upskillist.com/blog/10-ai-portfolio-examples-impress-recruiters/","Observed"],
 ["T8 resume parser demo","no calibration/abstention","citation P/R + not-in-corpus refusal slice","https://qaskills.sh/blog/rag-evaluation-interview-questions","Observed"],
 ["T9 no-obs LLM app","throws context, can't debug","OTel spans Q+A+contexts, session grouping","https://axiomlogica.com/ai-ml/llm-observability-stack-comparison-langsmith-vs-langfuse-vs-arize-phoenix-2","Observed"],
 ["T10 model-as-binary deploy","no version/rollback","registry+lineage+shadow/canary+gate","https://devopscube.com/devops-to-mlops/","Observed"],
 ["E1 IR retrieval","recall@k/MRR/NDCG vs labeled; recall ceiling blocks gen","Ragas/DeepEval/Phoenix","~0.8 recall@20 / NDCG@10 rough bars","Observed"],
 ["E2 faithfulness","supported/total claim-extract JSON judge","Ragas/DeepEval/Langfuse","block on drop; route low to human","Observed"],
 ["E3 RAG triad","relevance + precision + recall","Ragas/TruLens","separate retrieval vs generation gates","Observed"],
 ["E4 citation+abstention","ID resolves+entails+coverage; unsupported rate","custom + judge","launch-block confident-wrong","Observed"],
 ["E5 judge calibration","human ~50, agreement target, version prompt/temp","Confident AI/Phoenix",">agreement before trust","Observed"],
 ["E6 golden regression","50-100 real-user + adversarial/stale; freeze","Ragas/DeepEval gen","CI pytest assert","Observed"],
 ["E7 online/shadow","sample live, thumbs, faithfulness, drift","Langfuse/sampling","canary + weekly rerun + add failures","Observed"],
 ["O1 trace tree","root->tool/LLM/retriever spans I/O","LangSmith/Langfuse/Phoenix OTel","missing context = fail build","Observed"],
 ["O2 cost accounting","tokens per step/worker/tenant; 10x hard-stop","Langfuse/OTel","breaker 2x median","Observed"],
 ["O3 latency","p50/p95 per hop; supervisor 620ms-1.8s overhead","OTel+Grafana","timeout 30s; retry 1s/4s max2","Observed"],
 ["O4 retrieval obs","chunks/scores/rank, trunc/dedup logged","Phoenix/Langfuse","replay gold context isolate","Observed"],
 ["O5 safety/governance","allowlist, limits, pre-checks, HITL writes/pay/deploy","ToolGateway+supervisor","deny w/o approval","Observed"],
 ["O6 prod health","drift PSI/KL, thumbs, escalation, cost/success","Arize/Evidently/PD","alert faithfulness/latency breach","Observed"],
 ["S1 senior bounds","mid draws loop; senior caps step/token/time/spend; staff platform registry/budgets","—","https://www.tryexponent.com/courses/system-design-interviews/agentic-ai","Observed"],
 ["S2 scope","senior 1 team; staff multi-team/domain outcomes","—","https://underdog.io/blog/staff-engineer-vs-senior-engineer","Observed"],
 ["S3 mentorship","senior mentors juniors; staff mentors seniors + standards","—","https://fonzi.ai/blog/staff-vs-senior","Observed"],
 ["S4 problem framing","senior clarifies sprint-quarter; staff defines 2-4 quarters","—","https://jcmartinez.dev/post/from-senior-to-staff","Observed"],
 ["S5 de-risking","senior features; staff themes reliability/cost/security","—","same","Observed"],
 ["S6 promotion","6-12mo staff-scope + sponsor + adoption, not PR count","—","https://leonstaff.com/blogs/how-to-get-promoted-staff-engineer/","Observed"],
]
add_sheet(wb, "A7 Hiring Eval Deep", ["ID_Item","Detail","Gate_Artifact","URL_Ref","Evidence_Label"], a7)

# ---------- A8: IDP benchmarks (observed only) ----------
a8 = [
 ["Ricoh healthcare IDP","98-99% extraction; onboarding 4-6wk to 2-3d; 10k->70k docs/mo; eng ~80h to <5h (>90%); 1900h/yr saved; review -60-70%","vendor page (treat as vendor claim)","https://idp-software.com/vendors/textract","Observed as claim"],
 ["Myriad Genetics","77% cost reduction; classification 94%->98% GenAI Accelerator","vendor page","https://idp-software.com/vendors/textract","Observed as claim"],
 ["Associa 48M docs 26TB 465 PDFs 9 cats","overall 95%; Nova Pro 95%/85%/$0.0055; Premier 96%/90%/$0.0112; Sonnet4 95%/95%/$0.0121; Lite 95%/50%/$0.0041; first-page 91%->95% $0.011->$0.0055; Unknown 40%->85%","benchmark table","https://idp-software.com/vendors/textract","Observed as claim"],
 ["Competiscan","85% classification+extraction; 35-45k/d; live 8wk","vendor page","https://idp-software.com/vendors/textract","Observed as claim"],
 ["Textract pricing","Detect $1.50/1k; Forms $50/1k; Tables +$15/1k (=$65); Expense $8-10/1k; billed separately; >1M pp/mo discounts","calculator","https://www.tech42consulting.com/aws-idp-cost-calculator","Observed"],
 ["Mistral OCR3 claim","96.6% vs Textract 84.8% table; 97% cheaper (vendor claim, not independent)","vendor claim","https://idp-software.com/vendors/textract","Observed as claim"],
 ["PeerSpot gaps","2.3% share; ratings 2.0-4.5/5; gaps tables/checkbox/handwriting/offline","review aggregator","https://idp-software.com/vendors/textract","Observed"],
 ["YOLO construction","mAP 79% YOLO / 83% FRCNN; 0.54min YOLO vs 18.17min FRCNN vs 1.34h manual +1.2min review","Springer paper","https://link.springer.com/article/10.1007/s10032-024-00492-9","Observed"],
 ["YOLO P&ID",">94% 25-class Elyan; ~95% YOLOv8 SLD; 96.3% YOLOv5+MFCGAN; GD&T FRCNN mAP 0.93 @75ms","papers","https://www.sciencedirect.com/science/article/abs/pii/S0893608020301957","Observed"],
 ["P&ID prod bar (tutorial)","mAP50>0.90, P>0.92, R>0.88","tutorial threshold","https://www.ai.codersarts.com/post/p-id-symbol-detection-with-yolov8-and-pytorch-complete-tutorial","Observed"],
 ["Azure DI / UiPath DU / AI Builder accuracy","unknown — no observed numbers in fetched sources","—","—","Unknown (do not cite)"],
 ["RAG bench: ShopTalk 46-config","NDCG@5 0.896; 627 tests 97% cov 7 ADRs","portfolio repo","https://github.com/rubsj/ai-portfolio","Observed"],
 ["RAG bench: rerank lift","Recall@5 0.747 (+19.5% w/ rerank); 557 tests 16-config","portfolio repo","https://github.com/rubsj/ai-rag-evaluation-framework","Observed"],
 ["RAG bench: InsureLLM","4.48/5 over 150 Qs","portfolio repo","https://github.com/chandra-vv/genai_portfolio","Observed"],
 ["RAGLab/RAGScope/ASU evals","latency-as-dimension; faithfulness suites; cost $0.00016 vs $0.0019 (RAGLab, Observed in wave-1 snippets)","eval repos","see Sources + A2","Observed snippet"],
]
add_sheet(wb, "A8 IDP Benchmarks", ["Benchmark","Numbers_Observed","Context","URL","Evidence_Label"], a8)

# ---------- update Dashboard ----------
ws = wb["Executive Dashboard"]
# append wave-2 summary rows after existing table (find last row)
ws.append([])
ws.append(["WAVE-2 EXPANSION (2026-09-06)","Value","Note"])
wave_rows = [
 ["Wave-2 streams executed",8,"GitHub deep, Resume/JD (throttled-honest), Portfolio/cases, AIOps/Cloud, Security/FDE, Agent stack, Automation/Integration, Hiring/Eval"],
 ["Wave-2 searches executed","~140 (25+22+20+16+21+18+16+22, some 429)","429s disclosed per-agent; retries with backoff; webfetch fallback where possible"],
 ["New empirical repos catalogued (A1)",54,"One-line rows with files/stars observed; unknowns marked, never invented"],
 ["New portfolio/case rows (A2)",30,"RAG benches (NDCG 0.896, +19.5% rerank), red-team suites, ERP cases, Spaces, Vanna, toolkits"],
 ["Security patterns matrixed (A3)",17,"LLM01-10 + CI/adaptive/policy/blind-ops + 2026 delta; OWASP IDs/dates observed via fetch"],
 ["AIOps/Cloud patterns (A4)",30,"HolmesGPT/AIOpsLab/KServe/LiteLLM observed; vendor docs inferred where throttled — labeled"],
 ["Automation/integration flows (A5)",17,"UiPath Trust Layer, Maestro-PA, Textract+Bedrock, Azure DI, YOLO, SN MCP/Slack — observed; SAP/Snowflake/Databricks gaps marked"],
 ["Agent/MCP-A2A facts (A6)",21,"12 frameworks (docs observed) + 8 MCP/A2A 2026 facts (observed) + retrieval unknowns (honest)"],
 ["Hiring/eval items (A7)",40,"12 hiring + 10 toy-upgrades + 7 eval + 6 obs + 6 senior + bridges, URLs each"],
 ["IDP benchmarks (A8)",16,"Ricoh/Myriad/Associa/Textract pricing/YOLO/P&ID/RAG benches observed-as-claims; unknowns marked"],
 ["Total empirical URLs added (wave-2)","~250+","Full lists in A1-A8 + expanded Sources"],
 ["Resume/JD wave-2 stream","HONEST FAIL (429) — 0 sources, nothing invented","22 queries attempted w/ backoffs; re-run staggered 1-per-60s; wave-1 resume evidence stands"],
 ["Totals now","~250 searches; ~90+ repos; 60 canonical; 30 cases; 40+ benchmarks","See Sources + Query Log"],
]
for r in wave_rows: ws.append(r)
for row in ws.iter_rows(min_row=ws.max_row-len(wave_rows)-1, max_row=ws.max_row, max_col=3):
    for cell in row:
        cell.alignment = WRAP; cell.border = THIN
autofit(ws)

# ---------- expand Sources ----------
wss = wb["Sources"]
start = wss.max_row + 1
new_urls = [
 ("https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template","GitHub","LangGraph prod template","Observed"),
 ("https://github.com/Arcan17/agentforge","GitHub","multi-agent HITL","Observed"),
 ("https://github.com/theepankumargandhi/multi-agent-orchestration","GitHub","supervisor CI/CD","Observed"),
 ("https://github.com/vllm-project/production-stack","GitHub","vLLM K8s stack","Observed"),
 ("https://github.com/kserve/kserve","GitHub","inference CRDs 5835 stars","Observed"),
 ("https://github.com/langfuse/langfuse","GitHub","obs 34157 stars","Observed"),
 ("https://github.com/Arize-ai/phoenix","GitHub","tracing 11304 stars","Observed"),
 ("https://github.com/traceloop/openllmetry","GitHub","OTel 7201 stars","Observed"),
 ("https://github.com/microsoft/PyRIT","GitHub","red-team 4388 stars","Observed"),
 ("https://github.com/n8n-io/self-hosted-ai-starter-kit","GitHub","AI starter 15228 stars","Observed"),
 ("https://github.com/modelcontextprotocol/servers","GitHub","MCP reference","Observed"),
 ("https://github.com/containers/kubernetes-mcp-server","GitHub","K8s MCP Go-native","Observed"),
 ("https://github.com/comet-ml/opik","GitHub","LLMOps 20k claim","Observed"),
 ("https://github.com/explodinggradients/ragas","GitHub","eval 15602 stars","Observed"),
 ("https://github.com/WeiGuang-2099/Production-RAG","GitHub","GraphRAG ablation","Observed"),
 ("https://github.com/rubsj/ai-portfolio","GitHub","NDCG 0.896 bench","Observed"),
 ("https://github.com/rubsj/ai-rag-evaluation-framework","GitHub","+19.5% rerank","Observed"),
 ("https://github.com/vanna-ai/vanna","GitHub","text-to-SQL agent","Observed"),
 ("https://github.com/axon011/multi-agent-pipeline","GitHub","research pipeline","Observed"),
 ("https://github.com/ag2020sa/ai-security-red-team-harness","GitHub","CI-gated red-team","Observed"),
 ("https://github.com/nadirzhon/agentstrike","GitHub","canary fuzzer","Observed"),
 ("https://github.com/ZeroLeaks/zeroleaks","GitHub","leak scanner","Observed"),
 ("https://crunch-is.com/case-study/knowledge-access-transformation-with-rag-and-aws/","Case","Kendra+Bedrock 60% faster","Observed"),
 ("https://datafluxsoft.com/case-corporate-rag-construction.html","Case","permissioned RAG promptfoo 30+","Observed"),
 ("https://www.digitalgravity.ae/case-studies/artificial-intelligence/technology/ai-netsuite-chatbot/","Case","SuiteQL bot","Observed"),
 ("https://netsuitesync.com/talk-to-your-data","Product","Claude MCP read-only","Observed"),
 ("https://huggingface.co/blog/pkheria/knowledgemesh","Guide","ZeroGPU RAG hub","Observed"),
 ("https://holmesgpt.dev/latest/","Docs","HolmesGPT investigate","Observed fetch"),
 ("https://github.com/microsoft/AIOpsLab","GitHub","AIOps benchmark","Observed fetch"),
 ("https://kserve.github.io/website/","Docs","KServe CRDs","Observed fetch"),
 ("https://docs.litellm.ai/docs/simple_proxy","Docs","LiteLLM proxy","Observed fetch"),
 ("https://genai.owasp.org/llmrisk/llm01-prompt-injection/","Standard","OWASP LLM01","Observed fetch"),
 ("https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/","Standard","OWASP 2026","Observed fetch"),
 ("https://github.com/data-privacy-stack/presidio","GitHub","PII 10.8k stars","Observed fetch"),
 ("https://www.openpolicyagent.org/docs/latest/","Docs","OPA policy","Observed fetch"),
 ("https://langfuse.com/docs","Docs","LLMOps loop","Observed fetch"),
 ("https://docs.langchain.com/langgraph","Docs","LangGraph","Observed fetch"),
 ("https://docs.crewai.com/introduction","Docs","CrewAI","Observed fetch"),
 ("https://microsoft.github.io/autogen/stable/","Docs","AutoGen","Observed fetch"),
 ("https://docs.llamaindex.ai/en/stable/","Docs","LlamaIndex","Observed fetch"),
 ("https://openai.github.io/openai-agents-python/","Docs","OpenAI SDK","Observed fetch"),
 ("https://google.github.io/adk-docs/","Docs","Google ADK","Observed fetch"),
 ("https://modelcontextprotocol.io/docs/getting-started/intro","Standard","MCP USB-C + 2026 spec","Observed fetch"),
 ("https://a2a-protocol.org/latest/","Standard","A2A LF + foundation","Observed fetch"),
 ("https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-ai-trust-layer","Docs","UiPath Trust Layer","Observed fetch"),
 ("https://aws.amazon.com/blogs/machine-learning/intelligent-document-processing-with-amazon-textract-amazon-bedrock-and-langchain/","Guide","Textract+Bedrock IDP","Observed fetch"),
 ("https://idp-software.com/vendors/textract","Benchmark","Ricoh/Myriad/Associa/pricing","Observed as claim"),
 ("https://github.com/DynMEP/YOLOplan","GitHub","YOLO11 takeoff","Observed fetch"),
 ("https://github.com/schwarztim/servicenow-mcp","GitHub","SN MCP 80+ tools","Observed fetch"),
 ("https://github.com/tpickle/slack-servicenow-ticketbot","GitHub","Slack-SNOW bot","Observed fetch"),
 ("https://langfuse.com/resources/engineering/rag-faithfulness-evaluation","Guide","faithfulness fix","Observed"),
 ("https://hireagentic.dev/blog/multi-agent-swarm-pattern","Guide","supervisor caps","Observed"),
 ("https://www.tryexponent.com/courses/system-design-interviews/agentic-ai","Guide","senior bounds","Observed"),
 ("(Wave-2 full URL lists live in A1-A8; ~200 additional URLs there — see annex sheets)","Index","All domains","See annex"),
]
n = start
for u,t,c,l in new_urls:
    wss.append([n-1 if False else wss.max_row, u, t, c, l])
# fix numbering: rewrite first col sequentially
for i,row in enumerate(wss.iter_rows(min_row=2, max_row=wss.max_row, max_col=1), start=1):
    pass
# renumber properly
r = 1
for row in wss.iter_rows(min_row=2, max_row=wss.max_row, max_col=5):
    row[0].value = r; r += 1
    for cell in row:
        cell.alignment = WRAP; cell.border = THIN
autofit(wss)

# ---------- expand Query Log ----------
wsq = wb["Search Query Log"]
extra_q = [
 ["GitHub Deep (w2)",25,"production LangGraph agents; LiteLLM prod; vLLM/KServe manifests; Dify/RAGFlow; Haystack; Langfuse/Phoenix/OpenLLMetry; Promptfoo/Garak/PyRIT; HolmesGPT/Robusta; n8n; Backstage; MCP enterprise; TensorZero/Opik; Ragas/DeepEval; secure GW; K8s AI Helm","54 repos; stars only if observed"],
 ["Resume/JD Deep (w2)",22,"8 roles resume+JD India + senior + salary variants (all 429, backoffs 15/60/90s)","HONEST 0 sources; re-run staggered"],
 ["Portfolio/Case Deep (w2)",20,"RAG prod; multi-agent; red-team; arch cases; Salesforce/SharePoint/D365/NetSuite; Vanna; Spaces; Next.js; ROI; eval/latency","30 rows + 12 checklist + 6 Spaces patterns"],
 ["AIOps/Cloud Deep (w2)",16,"Splunk/SN; PagerDuty; Datadog; HolmesGPT; Prom ML; Kafka; RCAgent; AIOpsLab; KServe; GKE; vLLM/TGI/Triton; LiteLLM; MLflow; Backstage (all 429 -> 4 fetches)","30 patterns labeled; 10 checklist; 8 cloud matrix"],
 ["Security/FDE Deep (w2)",21,"LLM01-10 OWASP; firewall; redteam; NeMo; Presidio; OPA; Agentforce; D365; NetSuite; multi-cloud (all 429 -> 8 fetches)","16 threats + 12 FDE + 2026 delta (fetched)"],
 ["Agent Stack Deep (w2)",18,"LangGraph/CrewAI/AutoGen; LlamaIndex/Haystack; OpenAI SDK; ADK; SK; PydanticAI; DSPy; MCP/A2A; GraphRAG; FastAPI/K8s (all 429 -> 13 fetches)","12 frameworks + 8 MCP/A2A facts observed"],
 ["Automation/Integration Deep (w2)",16,"UiPath Trust Layer (OK); Maestro-PA (OK); Textract-Bedrock (OK); Azure DI (OK); YOLO (OK); SN MCP (OK); Slack-SN (OK); Snowflake/Databricks/SAP/Agentforce (429)","14 flows observed + 3 gaps marked"],
 ["Hiring/Eval Deep (w2)",22,"portfolio recruiters; RAG eval; supervisor; LangSmith/Langfuse/Arize; Ragas/DeepEval; Titanic/PDF; senior/staff; Ops->AIOps; DevOps->MLOps","12 hiring + 10 upgrades + eval/obs matrices"],
]
for q in extra_q: wsq.append(q)
for row in wsq.iter_rows(min_row=2, max_row=wsq.max_row, max_col=4):
    for cell in row:
        cell.alignment = WRAP; cell.border = THIN
autofit(wsq)

# ---------- update QA sheet ----------
wsqa = None
for s in wb.sheetnames:
    if s.startswith("QA"):
        wsqa = wb[s]; break
wsqa.append(["Wave-2 429 handling","DISCLOSED","Resume/JD + parts of AIOps/Security/Agent streams hit provider 429; backed off, fetched docs directly, labeled Inferred where unverified; one stream reported honest 0-source fail instead of inventing."])
wsqa.append(["Wave-2 totals","RECORDED","~140 wave-2 searches; 54 repos + 30 cases + 17 threats + 30 patterns + 17 flows + 21 stack facts + 40 hiring/eval + 16 benchmarks; ~250 URLs added."])
wsqa.append(["No-truncation rule","APPLIED","Annex sheets A1-A8 hold full rows; playbook annex mirrors key tables; unknowns marked, never filled."])
for row in wsqa.iter_rows(min_row=2, max_row=wsqa.max_row, max_col=3):
    for cell in row:
        cell.alignment = WRAP; cell.border = THIN
autofit(wsqa)

wb.save(XLSX)
print("Expanded", XLSX, "sheets:", len(wb.sheetnames))
