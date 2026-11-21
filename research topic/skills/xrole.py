"""Cross-role comparison, transition strategy, differentiator playbook, appendix data."""

HEATMAP_HEADERS = ["Capability", "AIOps", "Cloud AI", "Intel Auto", "AI Security", "FDE", "GenAI/Agentic", "AI Solutions"]
# Ratings: ● Critical / ◐ High / ○ Medium-Emerging / – Low
HEATMAP_ROWS = [
["Python + async engineering", "\u25cf", "\u25cf", "\u25cf", "\u25cf", "\u25cf", "\u25cf", "\u25d0"],
["Go / systems languages", "\u25d0", "\u25d0", "\u2013", "\u2013", "\u25cb", "\u25cb", "\u2013"],
["Inference serving (vLLM/Triton/TGI)", "\u25cb", "\u25d0", "\u25cb", "\u25cb", "\u25d0", "\u25cf", "\u25cb"],
["Agent orchestration (LangGraph/Temporal)", "\u25cb", "\u25d0", "\u25d0", "\u25d0", "\u25cf", "\u25cf", "\u25d0"],
["Hybrid RAG + rerank", "\u25cb", "\u25d0", "\u25d0", "\u25d0", "\u25cf", "\u25cf", "\u25d0"],
["Vector stores", "\u25cb", "\u25d0", "\u25d0", "\u25d0", "\u25cf", "\u25cf", "\u25d0"],
["Cloud AI platforms (1 deep)", "\u25d0", "\u25cf", "\u25d0", "\u25d0", "\u25d0", "\u25d0", "\u25d0"],
["Kubernetes + IaC", "\u25cf", "\u25cf", "\u25cb", "\u25cb", "\u25d0", "\u25d0", "\u25cb"],
["LLMOps / eval ownership", "\u25cb", "\u25d0", "\u25d0", "\u25d0", "\u25cf", "\u25cf", "\u25d0"],
["Telemetry (Prom/OTel/Grafana)", "\u25cf", "\u25cf", "\u25d0", "\u25d0", "\u25d0", "\u25d0", "\u25cb"],
["Security + guardrails", "\u25d0", "\u25d0", "\u25d0", "\u25cf", "\u25d0", "\u25d0", "\u25d0"],
["RPA / IDP platforms", "\u2013", "\u2013", "\u25cf", "\u2013", "\u25cb", "\u25cb", "\u25cb"],
["Red-team / OWASP-LLM", "\u25cb", "\u25cb", "\u25cb", "\u25cf", "\u25d0", "\u25d0", "\u25cb"],
["Customer discovery + demos", "\u25cb", "\u25cb", "\u25d0", "\u25cb", "\u25cf", "\u25cb", "\u25cf"],
["FinOps / unit economics", "\u25d0", "\u25cf", "\u25d0", "\u25cb", "\u25d0", "\u25d0", "\u25d0"],
]

TRANSITION_ROWS = [
["AIOps", "NOC triage + alert storytelling is the core asset", "OTel + PromQL + Python detectors + 1 correlation capstone",
"3-6 mo: on-call scorecard at current job; 6-12 mo: Incident-Copilot capstone + CKA", "MTTR/noise-reduction numbers, detector replay evals"],
["Cloud AI", "Ticketing + AD/IAM + virtualization map to cloud ops", "Terraform + 1 hyperscaler cert + endpoint canary capstone",
"3-6 mo: cert + landing-zone module; 6-12 mo: private RAG platform capstone + FinOps one-pager", "Cost model, quota plan, private-networking diagram"],
["Intel Auto", "Process knowledge + ticket/ERP fluency is gold", "UiPath/Power cert + Python IDP + golden-set eval habits",
"2-5 mo: first production bot with ROI math; 6-10 mo: IDP capstone + P&L one-pager", "STP/exception-rate/ROI per process, kill decisions"],
["AI Security", "SOC/IR + access-control instincts transfer directly", "OWASP-LLM + guardrail code + 1 red-team report",
"4-8 mo: guardrail sidecar + probe pack; 8-14 mo: red-team gate capstone + disclosure story", "Severity-rated findings, blocked launch, MTTR-to-mitigate"],
["FDE", "Stakeholder range + troubleshooting under pressure", "Full-stack + RAG/MCP + eval-acceptance + discovery reps",
"4-8 mo: steel-thread deliveries; 8-14 mo: bootcamp-in-a-box + handoff drill proof", "Handoff metric, eval suite, scope-cut log"],
["GenAI/Agentic", "Support/incident pattern-matching + ops discipline", "Hybrid RAG + agents + serving SLOs + eval gates",
"4-8 mo: RAG service capstone; 8-14 mo: supervisor-agent capstone + cost board", "Eval board, latency report, $/grounded-answer curve"],
["AI Solutions", "Trust + troubleshooting + demo-adjacent explaining", "Pilot app + discovery briefs + questionnaire pack",
"2-6 mo: 2 recorded demos + brief; 6-12 mo: pilot-to-close kit + conversion story", "Conversion rate, time-to-security-approval, readout samples"],
]

PLAYBOOK_MOVES = [
("Move 1 — Sell stability as revenue protection",
"Translate every ops win into money and risk: 'cut P1 MTTR 38 min -> 9 min across 14 Sev-1s/quarter' beats 'knows Kubernetes'. Build one number per story: downtime cost avoided, SLA credits saved, churn-risk tickets defused. Academic profiles cannot produce these numbers; you can."),
("Move 2 — Weaponize the post-mortem",
"Maintain 3 written post-mortems (missed page, bad automation, vendor outage) in blameless format with your action items. In interviews, volunteer one unprompted: it signals production adulthood faster than any certificate and answers 'tell me about a failure' before it is asked."),
("Move 3 — Demo the boring excellence",
"Show the runbook, the audit log, the eval gate, the kill-switch drill — the artifacts pure-builders skip. Hiring managers for FDE/Solutions/AIOps roles hire the candidate who proves the system survives contact with customers, auditors, and 2 a.m."),
("Move 4 — Convert tickets into evals",
"Your service-desk history is a golden-set goldmine: 500 real user phrasings beat 50 synthetic ones. Frame it explicitly: 'I source evals from production, not imagination.' This single sentence differentiates you from every tutorial-portfolio candidate."),
("Move 5 — Price everything",
"Attach unit economics to every project ($/ticket, $/1k answers, $/doc, GPU util). Ops veterans who speak FinOps outrank researchers who cannot cost their inference. The FinOps one-pager belongs in every loop, regardless of role."),
("Move 6 — Time-box the transition publicly",
"Publish a 90-day plan in the cover note: days 1-30 (ship scoped artifact + learn stack), 31-60 (own eval/metric), 61-90 (lead incident/pilot/review). Managers hire trajectories; a dated plan with exit criteria de-risks the non-traditional background."),
]

APPENDIX_PAPERS = [
["Attention Is All You Need (2017)", "Transformer foundation; cost object behind every serving decision"],
["BERT (2019)", "Representation lineage for embeddings/classifiers"],
["RAG (Lewis et al., 2020)", "Grounding lineage; the enterprise AI workhorse"],
["ReAct (Yao et al., 2023); Reflexion (2023)", "Agent loop lineage"],
["Lost in the Middle (Liu et al., 2023)", "Context-ordering discipline"],
["PagedAttention / vLLM (Kwon et al., 2023)", "Serving-economics canon"],
["Ragas (Es et al., 2023); LLM-as-judge (Zheng et al., 2023)", "Eval canon (calibrate judges!)"],
["OWASP Top 10 for LLM Apps (2025)", "Security interview checklist"],
["Indirect prompt injection (Greshake et al., 2023)", "Deployed-agent threat model"],
["SRE Book + Workbook (Google)", "Burn-rate alerting, error budgets, post-mortems"],
["Isolation Forest (Liu et al., 2008); Prophet (2018)", "AIOps detection baselines"],
["LayoutLM (2020-21)", "Document-understanding foundations"],
]

ATS_BANK_ROWS = [
["AIOps", "OpenTelemetry, Prometheus, PromQL, Grafana, Kubernetes, Terraform, anomaly detection, alert correlation, SLO/SLI, runbook automation, ServiceNow, Splunk ITSI"],
["Cloud AI", "Bedrock, SageMaker, Azure AI Foundry, Vertex AI, EKS/AKS/GKE, Terraform, IAM, VPC, PrivateLink, KMS, GPU, FinOps, autoscaling, canary"],
["Intel Auto", "UiPath, Orchestrator, Document Understanding, Power Automate, AI Builder, Temporal, n8n, OCR, IDP, SAP, ERP, human-in-the-loop, RAG"],
["AI Security", "OWASP LLM Top 10, red team, Garak, Promptfoo, Llama Guard, NeMo Guardrails, threat modeling, SIEM, OPA, EU AI Act, NIST AI RMF"],
["FDE", "Forward deployed, FDSE, applied AI, Python, TypeScript, RAG, LangGraph, MCP, evals, discovery, scoping, SSO, stakeholder management"],
["GenAI", "LangGraph, LlamaIndex, vLLM, Triton, Pinecone, Qdrant, pgvector, Ragas, LangSmith, Pydantic, FastAPI, Bedrock, Vertex AI"],
["AI Solutions", "Presales, discovery, demo, POC, pilot, MEDDIC, security questionnaire, SOC 2, DPA, SSO, trial, onboarding, value engineering"],
]

GLOSSARY_ROWS = [
["TTFT / TPOT", "Time-to-first-token / time-per-output-token; the two serving SLOs, optimized separately"],
["RRF", "Reciprocal Rank Fusion: rank-based hybrid-retrieval fusion, robust across heterogeneous scorers"],
["HITL", "Human-in-the-loop: approval breakpoints before high-risk or low-confidence actions"],
["Ontology", "Typed domain model (entities + links) grounding agent reasoning; the FDE doctrine"],
["Burn rate", "Error-budget consumption speed; multiwindow burn-rate alerting pages on user impact, not infra noise"],
["STP", "Straight-through processing rate: share of automation cases needing zero human touch"],
["Eval gate", "CI/CD quality check blocking promotion on faithfulness/precision/safety thresholds"],
["Canary", "Staged traffic shift (5% -> 25% -> 100%) with health gates and auto-rollback"],
["Provenance", "Cryptographic + logged origin of data/models; basis of poisoning defense and audit"],
["Unit economics", "$/1k grounded answers (or /ticket, /doc): the cost metric that makes AI spend discussable"],
]
