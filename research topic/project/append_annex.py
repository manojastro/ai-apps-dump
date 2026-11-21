"""Append Wave-2 empirical annex to playbook + grounding appendix to blueprints."""
import os
from docx import Document
from docx.shared import Pt

OUT = r"D:\ai apps dump\research topic\project"
PLAY = os.path.join(OUT, "AI_Portfolio_Project_Deep_Research_Playbook_2026.docx")
BLUE = os.path.join(OUT, "Top_AI_Project_Blueprints_2026.docx")

def add_table(d, headers, rows):
    t = d.add_table(rows=1, cols=len(headers)); t.style = 'Light Grid Accent 1'
    for i,h in enumerate(headers): t.rows[0].cells[i].text = h
    for r in rows:
        cells = t.add_row().cells
        for i,v in enumerate(r): cells[i].text = str(v)
    d.add_paragraph("")

d = Document(PLAY)
d.add_page_break()
d.add_heading("Wave-2 Empirical Annex (2026-09-06) — full retrieval without truncation", 0)
d.add_paragraph("Eight parallel deep streams, ~140 searches. Provider 429s disclosed per stream; retries + webfetch fallback; one stream (Resume/JD wave-2) reported an honest 0-source fail rather than inventing — wave-1 resume evidence stands. Labels Observed / Inferred / Unknown kept strictly. Full row-level data lives in Excel annex sheets A1–A8; key tables mirrored here.")
d.add_paragraph("Method note: rows are compact one-liners so nothing truncates. Stars/benchmarks appear ONLY where observed; otherwise 'unknown'. Vendor case numbers are flagged vendor-claim, not facts.")

d.add_heading("Annex A1 — GitHub deep sweep (54 repos): file-presence + frequency", 1)
d.add_paragraph("Sample: fastapi-langgraph templates (registry.py, docs/*-service.md, Prometheus+Grafana, JWT+slowapi); agentforge (compose + Celery+Redis+Postgres + pytest-123); multi-agent-orchestration (CI+CD workflows + 2 Dockerfiles + /metrics); litellm (helm + proxy_server_config.yaml + Terraform + cosign); production-stack (helm values + router+obs); kserve 5835★ (InferenceService CRD + Kustomize); dify 154290★ (compose multi-service); langfuse 34157★ (compose + Helm + ClickHouse); phoenix 11304★; openllmetry 7201★; promptfoo ~22k (redteam.yaml + CI action); garak 9079★; PyRIT 4388★; holmesgpt ~3k (Helm + toolsets + CNCF); n8n 203261 + starter 15228; roadie RAG backend (pgvector); enterprise MCP servers (Dockerfile + audit + OTel + 38 tools); tensorzero ~12k (Rust gateway + ClickHouse); opik 20k claim (compose + SDKs); ragas 15602★; ai-stack (single Helm + OTel); llm-governance-gateway (OPA rego + compose). Full 54 one-line rows: Excel A1.")
add_table(d, ["Signal","Observed frequency (54-sample, OBS only)"],
 [["Dockerfile",14/54],["docker-compose",18/54],["Helm/values",9/54],["K8s manifests/CRD",11/54],["CI workflows/Actions",10/54],["Evals (pytest/red-team/judge/synth)",19/54],["Docs+tutorials/notebooks",31/54],["2024–2026 recency",38/54]])
d.add_paragraph("Toy patterns to avoid (10): chat-with-pdf-streamlit (InMemory, no auth/CI); quickstart notebook (hardcoded keys); passthrough /chat (no rate/cache/audit); .env-committed; no-checkpointer agent (loses HITL); single-prompt eval; shell-out kubectl MCP (no allowlist); FROM:latest unpinned; no-observability RAG; static creds in config. Each maps to a P009/P012/P024/P028/P048/P054 fix. Full list: Excel A1 + playbook §24.")

d.add_heading("Annex A2 — Portfolio + cases (30 rows): benches + demos", 1)
add_table(d, ["Evidence","Observed value / artifact"],
 [["ShopTalk prod RAG (rubsj)","46-config bench NDCG@5 0.896; 627 tests, 97% cov, 7 ADRs"],
  ["RAG eval framework (rubsj)","rerank +19.5% Recall@5 0.747; 557 tests, 16-config grid"],
  ["InsureLLM","4.48/5 over 150 Qs; eval dashboard + app.py"],
  ["Banking copilot","domain RAG + QLoRA Mistral + 120+120 eval CSVs"],
  ["Multi-agent pipeline (axon011)","Planner-Researcher-Writer-Critic dual-engine; SSE UI + topics.yaml"],
  ["Red-team suites","AI-safety 15 tests; defensive harness SARIF; 25-room simulator; AgentStrike canary; 633-payload Intruder; 222-payload RedPincer; ZeroLeaks judge"],
  ["ERP cases","Crunch-IS 60% faster contracts (Kendra+Bedrock); Ksolves Agentforce+Trust Layer; DataFlux 15min→sec + promptfoo 30+; SupplyTech citation UI; DigitalGravity SuiteQL bot; S&B $140K/250% ROI/15s (vendor claim); NetSuiteSync Claude MCP read-only"],
  ["Text-to-SQL","Vanna 2.0 agent + Streamlit viewer + SSE"],
  ["Demos","KnowledgeMesh ZeroGPU Space; YiWang Next.js twin (yiw.me); Bhushan offline Gemma3 RAG (Vercel + Spaces); enterprise toolkit $20–100k closes"]])
d.add_paragraph("README/demo checklist (12, Observed): live URL + 60s video; arch diagram; eval table (N/faithfulness/recall/p95/cost); ablation (base→BM25→rerank→graph); refusal bucket + citations; tests+coverage+CI+compose; ACL handling explicit; guardrails+SARIF; cost/query; limits/failures; pinned repro; roadmap+ADRs+traces. HF Spaces patterns (6): Gradio ZeroGPU (@spaces.GPU, cuda scope); CPU basic (FAISS+MiniLM + Inference API); Docker (USER 1000:7860, no ZeroGPU); /data bucket mount; secrets (not env) + py3.12 pin; static+MCP. Full 30 rows: Excel A2.")

d.add_heading("Annex A3 — Security OWASP matrix (LLM01–10 + gates)", 1)
d.add_paragraph("All 16 rows observed via OWASP + repo/doc fetch: LLM01 injection (input rail + least-priv tools, +50–200ms); LLM02 disclosure (Presidio in/out/retrieval + vault, 20–100ms NER); LLM03 supply chain (pin+SBOM+sign, build-time); LLM04 poisoning (ACL + re-eval nightly); LLM05 output handling (sanitize/parameterize, +5–20ms); LLM06 excessive agency (scope + approval + dry-run; core ERP control); LLM07 prompt leakage (isolate + replay filter, ~10ms); LLM08 vector weakness (namespaces + retrieval rail, +5ms); LLM09 misinformation (grounding + fact-check = 1 extra call, 2x); LLM10 consumption (quotas + billing, ~0 runtime); jailbreak nightly (Garak dan/atkgen); PII loop (2x NER + vault); CI redteam gate (Promptfoo 24.8k★, cached fast); adaptive adversary (PyRIT $$$); policy sidecar (OPA <10ms); blind-ops cover (Langfuse loop). OWASP 2026: published 2026-08-04, GenAI Security Project, ATLAS/CWE maps, Agent Control Standard companion (Observed pub/governance; re-rank details Inferred). Full matrix + URLs: Excel A3.")

d.add_heading("Annex A4 — AIOps + Cloud patterns (30, honestly labeled)", 1)
d.add_paragraph("Observed via fetch: HolmesGPT investigate + Operator 24/7 (RBAC read-only first, external-secrets, no auto-apply prod); AIOpsLab harness + task registry (Kind HotelRes/SockShop, fault inject + wrk2, cli.py start, W&B tables, judge versioned); KServe InferenceService + LLMIsvc + InferenceGraph (canary + scale-to-zero, TTFT/TPOT, e2e budget); LiteLLM proxy + budgets/guards (virtual-key auth, 80/100% alerts, kill-primary test). Inferred (search throttled, needs re-verify before claiming): Splunk/SN sync, Now Assist, PD Event Intel + bi-dir sync, Watchdog + Bits AI, Robusta+Holmes remediation, Prom ML detector, MLflow forecasting/registry/evaluate, Kafka streaming + vector RAG, RCAgent, GKE ref arch, vLLM/TGI/Triton matrix, Backstage+ArgoCD IDP, golden-path template. Prod-vs-toy checklist (10): dedup measured; read-only first; grounding citations; fault-suite eval; token caps + p95 <5min; change-awareness (CMDB/deploys/freeze); bi-dir ITSM sync; PII scrub; fallbacks (offline runbook); postmortem→KB + prompt bump. Cloud matrix (8): Bedrock breadth; Azure OpenAI private/Entra; Vertex data/GKE/Gemini; RAG grounding per suite; guardrails per cloud; cost via LiteLLM + native PTU/committed; K8s path GKE smoothest / EKS hybrid; ITSM fit by cloud. Full 30 rows: Excel A4.")

d.add_heading("Annex A5 — Automation + integration (14 flows + ranking + IDP numbers)", 1)
d.add_paragraph("Observed via fetch: UiPath Trust Layer gateway (TLS1.2/AES-256, zero-training, audit) + BYO routing (allowlist, Relay private, JS hooks); Maestro→Power Automate (manual trigger only, 3–5min lag); Textract+Bedrock+LangChain IDP (A2I low-conf, few-shot + RAG grounding); Bedrock Pipeline (standard vs custom, bbox+score); Azure DI prebuilt-layout (2000pp/500MB, pages param) + pipeline ref (Functions 3–10 conc, 12–15 labels, KeyVault, DLQ); YOLOplan MEP (400DPI, conf 0.25–0.3, 20–50 imgs/100ep) + P&ID prod bar (mAP50>0.90/P>0.92/R>0.88); SN MCP Console + servicenow-mcp SSO (80+ tools, ~8h re-auth, Hermes authoritative) + MCP-ITSM router (safety annotations, /mcp-monitor 10s); Slack-SNOW bot (🎫 trigger, RBAC+PII gate, signing-secret) + VA self-bot (4-step plugin+app+channel). Gaps (search 429, marked): SAP BAPI, Snowflake Cortex, Databricks Mosaic, Agentforce capability — do not cite until re-fetched. Ranking: SN ITSM/MCP 1st, Slack+SN 2nd, UiPath IS/Maestro 3rd, Textract+Bedrock 4th, Azure DI 5th, YOLO 6th, VA+Slack 7th, SAP 8th (inf), Cortex 9th (inf), Mosaic 10th (inf), Agentforce 11th (catalog-obs/capability-inf), PA flows 12th. IDP observed-as-claims: Ricoh 98–99%/4–6wk→2–3d/10k→70k/mo/1900h/yr; Myriad −77% cost 94→98%; Associa 95% + per-model $/doc table; Competiscan 85% 35–45k/d 8wk live; Textract pricing ($1.50/$50/+$15/$8–10 per 1k); Mistral 96.6% vs 84.8% (vendor claim); PeerSpot 2.3% share gaps; YOLO 79%/83% mAP + time table; P&ID >94–96%. Azure/UiPath/AI Builder accuracy: unknown. Full: Excel A5 + A8.")

d.add_heading("Annex A6 — Agent stack + MCP/A2A 2026 (docs-observed)", 1)
d.add_paragraph("Docs verified via fetch (maturity/use/hiring = Inferred): LangGraph (durable HITL), CrewAI (Crews+Flows), AutoGen 0.2→1.x split, LlamaIndex + LlamaCloud/Parse, Haystack v3.1 + Enterprise, OpenAI SDK (Swarm successor + Sandbox/Realtime), ADK GA 5-lang + 2.0 graphs, SK 1.0+ C#/Py/Java, PydanticAI (Harness/Durable/Temporal/DBOS), DSPy (6.6M dl/mo, 38k★, GEPA/MIPRO; 0.41→0.63/62→89% are toy illustrative, NOT retrieval benchmarks), GraphRAG (Leiden+DRIFT), FastAPI+K8s (Uvicorn/Pydantic, SSE/MCP server). MCP/A2A 2026 (all Observed): MCP = USB-C for tools/data/workflows; clients Claude/ChatGPT/VSCode/Cursor; spec docs/2026-07-28 live; A2A = opaque secure agent-to-agent (not dev-kit); LF donation (AWS/Cisco/Google/IBM/MS/Salesforce/SAP/SN TSC); joined Agentic AI Foundation 2026-08-27; SDKs Py/JS/Java/.NET/Go/Rust + Card/Skills/Executor; complement MCP(tool) + A2A(agent), ADK both. Retrieval funnel lifts: unknown — no verified benchmark seen (honest). Full: Excel A6.")

d.add_heading("Annex A7 — Hiring + eval deep (40 items, URLs each)", 1)
d.add_paragraph("Hiring 12 (Observed): evals-first golden+gate; retrieval-vs-generation split; e2e ownership + runbook; deployed hybrid+rerank+cites+abstention; supervisor budgets/HITL (8 iters/depth 3/30s); proof-of-work (merged PRs/HF/papers); depth>breadth (3 > 20 notebooks); live demo+README; provenance; tracing+cost/tenant; responsible AI (cards/bias/defense/audit); discount list-only/certs/forks/API-no-eval. Toy→enterprise 10 with URLs (titanicAI, sink-or-swim, cv-joseph, supervisor-arch, Langfuse faithfulness, upskillist, RAG-eval interview, obs-stack comparison, devops-to-mlops). Eval 7: IR (recall/MRR/NDCG, ~0.8 bars rough); faithfulness (claim-extract JSON; Ragas stricter than DeepEval; DeepEval reason + pytest/cache); triad; citation+abstention (launch-block confident-wrong); judge calibration (~50 human, agreement first); golden regression (50–100 frozen, CI assert); online/shadow (canary + weekly + add failures). Obs 6: trace tree (missing context = fail); cost (10x hard-stop, 2x breaker); latency (supervisor 620ms–1.8s, 30s timeout, 1s/4s×2 retries); retrieval obs (replay gold isolate); safety (deny w/o approval); health (PSI/KL drift, thumbs, escalation). Senior 6: bounds → platform; 1-team → multi-team; mentor juniors → mentor seniors; clarify → define; de-risk features → themes; promotion = 6–12mo staff-scope + sponsor + adoption. Bridges 6: DevOps→MLOps (CI/CD→CT, artifacts=models); IaC/K8s→ML (vLLM/Triton/KServe, GPU binpack/spot); monitoring→drift/quality/token-cost; gates (baseline/bias/lineage/rollback) + 90-day runbook; Ops→AIOps 5-phase; noise→correlation + seasonal + self-heal (MTTD/MTTR/coverage). Full: Excel A7.")

d.add_heading("Annex A8 — IDP + RAG benchmarks (observed-as-claims + unknowns)", 1)
d.add_paragraph("See Excel A8 for the 16-row numbers table with URLs and claim flags. Headlines: Associa per-model accuracy/cost table (Nova Pro $0.0055 → Sonnet4 $0.0121); Textract feature pricing; YOLO time collapse (1.34h manual → 0.54min); RAG benches (NDCG 0.896; +19.5% rerank; 4.48/5/150Qs). Azure DI / UiPath DU / AI Builder accuracy: unknown — explicitly not cited. Vendor case numbers are treated as vendor claims pending independent rerun on your own docs.")

d.add_heading("Wave-2 QA + saturation update", 1)
d.add_paragraph("429 handling: disclosed per annex; backoffs 15/60/90s; webfetch fallback (docs/standards/repos, not rate-limited); one honest 0-source stream (Resume/JD wave-2) with re-run plan (stagger 1-per-60s, numResults=5, fast). No stars/benchmarks/salaries invented in wave-2. Saturation: A1–A8 add genuinely new categories (MCP enterprise servers, governance gateway with OPA rego, Vanna, AgentStrike/RedPincer/ZeroLeaks, KnowledgeMesh ZeroGPU, AIOpsLab registry, GIE LoRA gateway, ai-stack Helm) — wave-2 was NOT redundant. Remaining gaps for next pass: SAP/Snowflake/Databricks/Agentforce primary docs; senior India JD re-run; rerank/hybrid numeric benchmarks from primary sources.")
d.save(PLAY)
print("Appended annex to", PLAY)

b = Document(BLUE)
b.add_page_break()
b.add_heading("Empirical Grounding Appendix — which evidence supports each blueprint", 0)
b.add_paragraph("Wave-1 (7 streams, ~110 searches) + Wave-2 (8 streams, ~140 searches). Use this to cite proof in interviews/README. Numbers below are observed values/claims with URLs in Excel A1–A8; do not present vendor claims as your results.")
rows = [
 ("P039 Secure RAG","ShopTalk NDCG 0.896 + rerank +19.5% (rubsj); InsureLLM 4.48/5/150Qs; Crunch-IS 60% faster; DataFlux 15min→sec + promptfoo 30+; SupplyTech citation UI; dify 154k + ragflow deep-doc + haystack pipelines + hayhooks MCP"),
 ("P026 Secure RAG guards","NeMo rails + NIMs; NemoGuard/Topic/LlamaGuard; Presidio 10.8k + vault; 40-Q golden + authority tiers (SupplyTech pattern); Trust Layer (Agentforce/Salesforce)"),
 ("P001 RCA agent","HolmesGPT (~3k, Helm+toolsets+CNCF) + Robusta playbooks; AIOpsLab harness + registry (Kind + wrk2 + W&B); RCAgent paper; PD Event Intel + SN bi-dir (inferred, re-verify)"),
 ("P009 Gateway","litellm (helm + config.yaml + Terraform + cosign) + docker wrapper + deploy workflow; budgets/guards docs (80/100% alerts, virtual keys); TensorZero Rust GW (~12k) + Opik; chaos kill-primary test"),
 ("P012 LLMOps","MLflow registry/evaluate/tracing (prompt alias stage/prod + judge + CI); Langfuse 34k (compose + Helm + ClickHouse) + Phoenix 11k + OpenLLMetry 7k; drift + rollback loop"),
 ("P024 Firewall","8 firewall repos (regex <2ms + ONNX 50–150ms + FAISS + judge); Garak 9k probes + Promptfoo 24.8k CI + PyRIT 4.4k multi-turn; OPA <10ms sidecar; SARIF + SIEM/SSE"),
 ("P048 Eval harness","Ragas 15.6k + DeepEval pytest + gen-eval unified gate + sunilp303 scaffold; faithfulness (Ragas stricter) + triad + citation/abstention + calibration (~50) + golden 50–100 + shadow; rubsj 557–627 tests model"),
 ("P010 K8s inference","KServe 5.8k (InferenceService + LLMIsvc + InferenceGraph) + vLLM production-stack (helm + router+obs) + GIE LoRA gateway; GKE ref arch (inferred); vLLM/TGI/Triton matrix (publish tok/s + TTFT/TPOT)"),
 ("P025 Red-team CI","Promptfoo per-PR (redteam.yaml + action) + Garak nightly (dan/encoding) + PyRIT quarterly (multi-turn) + SARIF gate; AgentStrike/RedPincer/ZeroLeaks suites as seed corpora"),
 ("P041 Text-to-SQL","Vanna 2.0 agent + Streamlit + SSE; DataWeave AskAI resume pattern (India); read-only role + caps + OPA row-ACL + Bedrock parameterized SQL (inferred, re-verify)"),
 ("P049 MCP gateway","modelcontextprotocol/servers + K8s Go-native + Kishan/Adrien enterprise servers (Dockerfile + audit + OTel + 38 tools) + GHE MCP; MCP spec 2026-07-28 + A2A LF/TSC/foundation; registry + allowlist + container-per-server"),
 ("P028 Agent IAM","OPA/Rego sidecar (<10ms, audit) + llm-governance-gateway (policies/llm/*.rego + compose); min-tools + user-context OAuth + dual approval prod/finance; LLM06 core control"),
 ("P035 Parts layer","SupplyTech 10-wk eval-driven pilot template (40-Q day-1, layout-aware row chunks, reranker + metadata filter, citation page/date, 14→55 users); DataFlux permissioned + promptfoo pattern"),
 ("P016 Multi-cloud","Bedrock + Azure AI Search + Vertex via LiteLLM abstraction; ai-stack Helm + k8s-IaC-agent (RBAC/NetworkPolicy + Terraform); residency + per-tenant namespaces; 60–90d measurement rule"),
 ("P060 OpsPilot","Composes all above; Backstage RAG backend (pgvector) + ai-crew-suite (approvals/audit) + ArgoCD + KServe + OpenCost; n8n 203k + starter 15k + SN MCP 80+ tools + Slack-SNOW bot as execution layer"),
]
t = b.add_table(rows=1, cols=2); t.style = 'Light Grid Accent 1'
t.rows[0].cells[0].text = "Blueprint"; t.rows[0].cells[1].text = "Grounding (repos/cases/benches — see Excel A1–A8 for URLs)"
for pid, g in rows:
    cells = t.add_row().cells; cells[0].text = pid; cells[1].text = g
b.add_paragraph("")
b.add_paragraph("Build order unchanged: P048 → P039/P026 → P009/P024 → P001 → P012/P025/P054 → supports; P060 last. Fill [X] only with measured values from your runs.", style='Intense Quote')
b.save(BLUE)
print("Appended grounding to", BLUE)
