"""Roles 3-4: Intelligent Automation Engineer, AI Security Engineer."""

ROLE_AUTO = {
"num": 3, "title": "Intelligent Automation Engineer",
"tagline": "From RPA bots to agentic process operators — automate the work, prove the ROI",
"mission": ("Own business processes end to end as production systems: discover and size opportunities, build IDP + RAG + agent "
"pipelines across ERP/CRM/ticketing estates (UiPath, Power Platform, Automation Anywhere, n8n, Temporal), gate every step with "
"confidence thresholds and human-in-the-loop review, and report automation rate, accuracy, and dollars saved like a P&L owner."),
"tele_intro": ("Recon: 30+ postings incl. Bosch (RPA+GenAI+Agentic, 5-7 yrs, Azure OpenAI), AMETEK (UiPath + Power Platform, 4-6 yrs, "
"Bangalore), OCERS pension modernization JD (Azure MLOps + IDP + RPA hybrid), Sundeep Teki 2026 guide (RPA market ~$35B, ~20% annual "
"demand growth, US mean ~$135K top-quartile $200K+), JobDescription.org/axialsearch role analyses. Variant titles: AI Automation "
"Engineer, RPA Developer (Intelligent), Agentic Automation Engineer, IDP Engineer."),
"openings_rows": [
["United States", "~5,000-7,000 active; hubs: NYC, Dallas, Chicago, Atlanta, Cleveland (finserv/insurance ops centers)"],
["EMEA", "~2,000-3,000 active; hubs: London, Warsaw, Bucharest, Frankfurt, Amsterdam (shared-service centers)"],
["India / APAC", "~5,000-7,500 active; hubs: Bengaluru, Hyderabad, Chennai, NCR, Manila (GCC + BPO-to-automation shift)"],
["Global Remote", "~800-1,200 active; n8n/Temporal-native startups + consultancies"],
["TOTAL (directional, Sep 2026)", "~13,000-18,000 worldwide; fastest share-shift toward agentic (LLM+orchestration) phrasing"]],
"comp_rows": [
["L2 / Builder (2-4 yrs)", "$95K", "$118K", "$142K", "$170K"],
["L3 / Senior (4-7 yrs)", "$125K", "$150K", "$185K", "$225K"],
["L4 / Lead / Architect (7+ yrs)", "$155K", "$190K", "$235K", "$290K+"]],
"comp_note": ("Sources: 2026 guides (US mean ~$135K, top quartile $200K+; senior enterprise specialists higher); Levels.fyi AI premiums. "
"India mapping: Builder INR 8-16 LPA; Senior INR 16-30 LPA (UiPath Advanced + Azure AI skills); Architect INR 30-48 LPA+ "
"(Bosch/AMETEK-class enterprise + Big-4 automation practices). UiPath Advanced RPA + Azure AI Engineer Associate are documented pay levers. "
"1 USD approx 84 INR."),
"top15_rows": [
["Enterprise adopters", "Bosch, AMETEK, Siemens-class manufacturing; JPMorgan/Citi-scale banks; UnitedHealth-scale payers; pension/PSU modernization (OCERS-class)"],
["Platform vendors", "UiPath, Automation Anywhere, Microsoft (Power Automate + AI Builder + Copilot), Blue Prism/SS&C"],
["GCC / delivery", "Bengaluru/Hyderabad automation COEs, Big-4 + Accenture/TCS/Infosys intelligent-automation practices"],
["AI-native automation", "n8n, Temporal, Retool/Appsmith-ecosystem startups; IDP specialists (Hyperscience-class)"]],
"exp_bullets": [
("Minimum tenure: ", "2-3 years shipping automations (RPA, ETL, scripting, or backend) with production support ownership."),
("Preferred tenure: ", "4-7 years incl. 1-2 years LLM/RAG/agent production work: prompt/version discipline, eval + HITL design, exception-rate ownership."),
("Feeder backgrounds: ", "RPA Developer -> Intelligent Automation (largest vector: add LLM eval + orchestration); IT Service Desk/ops (process knowledge is gold); backend/fullstack (engineering rigor); BPO/ops analysts who learned Python + UiPath."),
("Education signal: ", "Degree flexible; UiPath Certified Advanced RPA Developer + Azure AI Engineer Associate / TensorFlow Developer carry real weight; portfolio of 2+ production automations with ROI math beats certificates.")],
"bound_rows": [
["Data Engineering", "Consume curated tables/APIs; own automation-local schemas, queues, idempotency", "Warehouse modeling, canonical ETL, governance", "Contract on input schemas + freshness; automation never silently redefines source truth"],
["ML Research", "Select/configure/evaluate models for extraction/classification/routing", "Train novel models, publish", "Buy-or-fine-tune decision with eval evidence; research engaged only past eval ceiling"],
["Platform / DevOps", "Automation services on paved road (containers, secrets, CI/CD)", "Cluster/landing-zone ownership", "Deploy via platform pipelines; automation team owns pipeline logic + runbooks"],
["Solutions Architecture", "Process ROI narratives, expansion roadmaps per business unit", "Pre-sales demos, deal shaping", "Automation supplies measured savings SAs can promise again"]],
"artifacts": [
("PR: invoice IDP straight-through-rate 61% -> 88% with confidence-gated HITL",
"Change: upgraded classifier + per-field extraction thresholds; low-confidence fields route to reviewer queue with highlighted spans instead of failing whole doc; idempotency keys end duplicate postings from retried queue deliveries. Validation: 2k-doc backtest, exception-rate and $/doc before/after. Rollback: threshold config versioned, one-flag revert."),
("Post-mortem: bot posted duplicate vendor payments during ERP brownout",
"Summary: retry storm + missing idempotency on POST created 14 duplicate payments ($312k held, recovered). Root cause: at-least-once queue without idem keys + no ledger pre-check. Fix: idem keys (Module D pattern), ERP reversal API runbook, HITL for amounts >$10k. Compensation + control attestation included."),
("Architecture review: deterministic RPA vs agentic handling for claims intake",
"Decision: deterministic bots for structured EDI + agent pipeline for unstructured emails/attachments, arbitrated by classifier confidence; agent outputs never post without HITL above risk threshold. Rationale with error-rate and cost-per-claim math; exit note: agent vendor swap cost bounded by tool-schema layer."),
("PR: n8n -> Temporal migration for long-running approval workflows",
"Change: approval chains with 14-day SLA timers moved to Temporal (durable timers, versioned workflows); n8n kept for lightweight webhooks. Validation: replay of 6-month history, zero stuck executions; versioning drill recorded."),
("Quarterly automation P&L one-pager",
"Per-process: hours returned, accuracy vs human baseline, exception rate, $ saved (loaded-cost math), bot uptime, reviewer burden. Killed 2 negative-ROI bots (celebrated publicly). This artifact is the promotion packet in automation orgs.")],
"toolchain": [
("IDEs/editors: ", "VS Code; UiPath Studio / Power Automate designer for platform bots; Temporal UI + n8n canvas for orchestration."),
("CLI daily drivers: ", "uipathcli, pac (Power Platform), git/gh, docker, kubectl (hosted workers), sql clients, OCR eval harnesses."),
("Inference runtimes: ", "Azure OpenAI / Document Intelligence, UiPath Document Understanding + AI Center, open models for PII-safe extraction."),
("Telemetry dashboards: ", "UiPath Orchestrator/Insights, Power Automate analytics, app-provided eval boards (accuracy/exception queues), Grafana for worker fleets.")],
"skills_rows": [
["Core systems & programming", "Python incl. async (Critical); SQL (Critical); TypeScript for web triggers (High)", "Go/Rust/CUDA (Low)"],
["Inference & serving", "Managed doc-AI + LLM APIs (Critical); ONNX for on-prem extraction (Medium)", "vLLM/Triton self-host (Low-Medium)"],
["Agentic & orchestration", "UiPath/Automation Anywhere/Power Automate (Critical); Temporal/Airflow/Prefect (High); LangChain/LlamaIndex/AutoGen (High)", "CrewAI/Semantic Kernel (Emerging)"],
["Vector storage & retrieval", "pgvector/Chroma/Pinecone/Weaviate for grounding (High)", "Milvus/Qdrant/OpenSearch at IDP scale (Medium)"],
["Cloud AI platforms", "Azure (AI Builder, Doc Intelligence, Foundry) (Critical-High); AWS Textract/Bedrock (High)", "Vertex doc-AI (Medium)"],
["LLMOps / telemetry / eval", "LLM-as-judge + regression suites + reviewer-agreement metrics (Critical); LangSmith/Phoenix (High); Prometheus/OTel for fleets (High)", "Ragas/TruLens formal gates (Emerging-High)"],
["Security & guardrails", "PII handling in docs, least-privilege ERP creds, vaulted secrets (Critical)", "NeMo/Llama Guard + Promptfoo red-teams on agent steps (High)"]],
"theory": [
{"h": "T1. Process theory: what is automatable (and what should not be)",
"body": ("Score processes on volume x standardization x stability x cost-of-error. High-volume, rule-stable, low-judgment work (invoice posting, "
"address changes, ticket triage) is deterministic-bot territory. Variable-format, judgment-heavy work (claims narratives, contract deviations) needs "
"LLM extraction + confidence-gated HITL. Never automate: processes with undefined ownership, changing weekly by tribal exception, or where error cost "
"dwarfs labor savings (safety-critical postings without review). Discovery method: shadow 5-10 cases end to end, time each step, log every exception "
"and its handler — the exception catalog IS the design spec. ROI math: (minutes saved x fully-loaded rate x volume) minus (build + reviewer burden + "
"license + maintenance); require payback <9 months or kill the candidate."),
"diagram": "discover(shadow+time) ──> exception catalog ──> bot/agent design ──> HITL gates ──> P&L review ──> expand/kill"},
{"h": "T2. IDP mathematics: OCR, classification, extraction, confidence",
"body": ("Pipeline: layout-aware OCR (tokens + bounding boxes) -> document classification (invoice/contract/claim; calibrated probabilities) -> "
"field extraction (regex + NER + LLM with schema) -> per-field confidence -> routing (straight-through vs review vs dead-letter). "
"Calibration matters more than raw accuracy: a 90%-accurate model with honest confidence routes correctly; an overconfident one auto-posts errors. "
"Measure per-field precision/recall, reviewer overturn rate, and straight-through rate jointly — pushing STP up while overturn climbs is fraud-adjacent "
"negligence. Human-review UX (highlighted spans, one-key accept/correct) determines whether reviewers catch errors or rubber-stamp them; "
"reviewer-agreement sampling audits the auditors."),
"diagram": "scan ──OCR──> tokens+boxes ──classify──> type+conf ──extract──> fields+conf ──route──> post / review / DLQ"},
{"h": "T3. Orchestration semantics: queues, idempotency, durable execution",
"body": ("Enterprise automation is distributed systems work: at-least-once queues demand idempotency keys on every side-effecting call (the IDP pattern "
"in Module D); long approvals demand durable timers (Temporal), not cron prayers; retried webhooks demand dedup windows; schema drift in ERP/CRM APIs "
"demands versioned adapters with contract tests. State machines beat nested ifs: explicit states (received/extracted/reviewing/posted/failed) with "
"allowed transitions, dead-letter after N attempts, and replayable history. Every workflow needs: run ID propagation, structured audit log, "
"per-step timeouts + compensation actions (reverse the posting, close the ticket with note)."),
"diagram": "webhook/queue ──dedupe(idem)──> state machine ──risk?──> HITL ──> post ──> reconcile ──> DLQ+alert on N fails"},
{"h": "T4. Evaluation for automation: proving the bot beats the human baseline",
"body": ("Three eval layers: (i) component evals (OCR CER, classifier F1, extraction field-F1 on golden sets); (ii) workflow evals (STP rate, exception rate, "
"reviewer overturn, $/doc, cycle time) on replayed history before each release; (iii) business evals (hours returned, error-cost delta, CSAT impact). "
"LLM-as-judge grades extraction equivalence where exact-match is too strict; blind dual-review calibrates the judge. Regression rule: no release ships "
"if workflow metrics degrade vs baseline on the frozen golden quarter — demos impress, golden-set diffs promote.")}],
"syllabus_concepts": [
"RPA platforms deeply (UiPath Studio/Orchestrator/Document Understanding; Power Automate + AI Builder; one of AA/Blue Prism)",
"Orchestration: Temporal (workflows/activities/versioning), Airflow/Prefect, n8n; queues (Service Bus/SQS), webhooks, retries",
"IDP: OCR (Tesseract/Azure DI), layout models (LayoutLM-class intuition), NER, calibration, confidence gating",
"LLM integration: function calling, structured outputs, RAG grounding, prompt/version management, eval harnesses",
"Enterprise integration: REST/GraphQL, SAP/ERP adapters, SSO, vaults (Key Vault/Secrets Manager), audit + DPA basics"],
"syllabus_papers": [
"LayoutLM / LayoutLMv2 (Microsoft, 2020-21) — layout-aware document understanding foundations",
"Attention Is All You Need (2017) — the extraction engine underneath modern IDP assists",
"Drain log parsing (2017) — template clustering reused for semi-structured doc variants",
"Temporal workflow-durability papers/docs — durable execution mental model",
"RAG (Lewis et al., 2020) — grounding extraction/classification in enterprise corpora"],
"syllabus_docs": [
"UiPath (Studio, Orchestrator API, Document Understanding, AI Center); Power Automate + AI Builder limits/quotas",
"Azure AI Document Intelligence + Content Understanding; AWS Textract/Comprehend; confidences + bounding-box contracts",
"Temporal concepts (workflows, activities, versioning, schedules); n8n self-host ops; SAP GUI/API automation guides",
"LangChain/LlamaIndex tool-use + eval guides; Promptfoo red-team basics; reviewer-queue UX patterns"],
"failures": [
("Duplicate financial postings from retry storms",
"At-least-once delivery + non-idempotent ERP POST = double payments. Fix: idempotency keys, ledger pre-check, amount-threshold HITL, reconciliation job with alerting."),
("Overconfident extraction auto-posts wrong bank details",
"Model 96% confident, wrong account; money misrouted. Fix: calibration, per-field thresholds, dual-control review above risk limits, overturn-rate monitoring."),
("Screen-scrape bot breaks on every vendor UI release",
"Selector-based automation coupled to DOM churn. Fix: prefer APIs; where UI is forced, anchor selectors + computer-vision fallback + contract test that pages before business hours."),
("Reviewer rubber-stamping under quota pressure",
"HITL becomes decoration; errors sail through. Fix: blind audit sampling, reviewer-agreement metrics, rotate reviewers, cap queue depth with SLA relief valve."),
("Silent schema drift drops half the fields",
"ERP upgrade renames fields; extractor emits nulls that post as zeros. Fix: schema contract tests, null-rate alarms, dead-letter on unexpected nulls, versioned adapters."),
("Context rot: agent acts on stale policy PDF",
"Policy updated, vector index not re-embedded; agent cites revoked clause. Fix: source-of-truth webhooks -> reindex SLA, staleness banners, index-version in every answer.")],
"ats_keywords": ("UiPath, UiPath Orchestrator, Document Understanding, AI Center, Power Automate, Power Apps, AI Builder, "
"Automation Anywhere, Blue Prism, n8n, Temporal, Airflow, OCR, IDP, intelligent document processing, Python, SQL, REST API, "
"SAP, ERP, CRM, LangChain, LlamaIndex, RAG, prompt engineering, human-in-the-loop, RPA, exception handling, Azure AI, AWS"),
"ats_antipatterns": [
"Listing 6 RPA tools with no production bot, no volume/accuracy/ROI numbers — reads as tutorial tourism.",
"'Built a chatbot' with no process ownership, eval, or exception-rate story.",
"No mention of idempotency, HITL, audit, or PII handling on enterprise processes."],
"loop_rows": [
["Recruiter screen (30 min)", "Platform depth (which bots live), volumes, comp band", "Named live processes + your on-call role"],
["Hiring-manager + process deep dive (60 min)", "Hardest process automated; ROI math; stakeholder fight", "Exception-catalog thinking, P&L ownership, kill decisions"],
["Live build (60-90 min)", "IDP mini-pipeline: classify + extract + confidence gate + queue push", "Schema discipline, edge cases, HITL instinct"],
["Systems design (60 min)", "Claims-intake automation at 50k docs/mo with audit + DPA constraints", "Idempotency, durability, eval gates, reviewer UX, cost/doc"],
["Behavioral (45 min)", "Duplicate-posting incident; reviewer revolt; vendor UI breakage", "Ownership, blamelessness, controls mindset"]],
"interview_qa": [
("Q1. Invoice bot posts 2% of invoices to wrong vendors. Fix it end to end.",
"A. Model answer: freeze auto-post, backtest to isolate failing field (usually remit-to extraction on multi-remit templates); add per-field confidence with calibrated thresholds; route low-confidence to span-highlighted review; add vendor-master fuzzy-match verification pre-post; idempotency + duplicate-invoice check; monitor overturn + STP jointly; re-enable auto-post per template cohort only after golden-set pass."),
("Q2. Code the confidence gate and routing for the IDP pipeline.",
"A. Model answer: reproduce Module D process_document/push_to_rpa: idem keys, OCR emptiness guard, classify-then-threshold, straight-through vs HITL vs dead-letter, audit payload. Discuss tuning CONFIDENCE_FLOOR from overturn data and versioning the threshold."),
("Q3. Design claims intake at 50k documents/month with auditors watching.",
"A. Model answer: states + DLQ, durable orchestration, PII vaulting, reviewer queues with blind audits, reconciliation vs claim system, retention policy, DPA mapping, per-claim cost tracking; chaos: ERP brownout replay proving no duplicates and full audit export."),
("Q4. When do you choose deterministic RPA over an LLM agent?",
"A. Model answer: deterministic for structured, stable, high-volume steps with hard rules (postings, EDI, reconciliations); agent for variable-format intake/classification/summarization behind confidence gates and HITL; hybrid arbitrated by classifier; cost-per-case and error-cost decide the boundary, reviewed quarterly."),
("Q5. Your straight-through rate is 95% but finance found mis-postings. What happened?",
"A. Model answer: threshold gaming/overconfidence, reviewer sampling too thin, golden set stale (new template variants), silent schema drift, or evaluation measuring the wrong field. Response: halt cohort, expand golden set with failures, recalibrate, add verification checks (totals balance, master-data match), restore with staged rollout.")],
"capstones": [
{"name": "Capstone 1 — Invoice-to-Pay Automation with Confidence-Gated HITL",
"arch": ("Watch folder/queue -> OCR (Azure DI or Tesseract) -> classifier -> Pydantic-validated extraction -> vendor-master verification -> "
"confidence router (post / review SPA / DLQ) -> mock ERP API with idempotency -> reconciliation report -> P&L dashboard. "
"Reviewer UI (Streamlit) with span highlights + one-key accept/correct feeding the golden set."),
"stack_rows": [
["Compute", "Python 3.11 services + Streamlit reviewer app (Docker Compose)"],
["Automation", "Temporal (durable posting workflow) or n8n for ingestion webhooks"],
["Retrieval", "pgvector/Chroma vendor-master + policy grounding"],
["Quality", "Golden-set replay harness (pytest) + LLM-as-judge equivalence checks"],
["Ops", "Structured audit log + Grafana exception/STP board"]],
"steps": [
"1. Assemble 300-doc corpus (multi-template invoices) with labeled fields; freeze golden split.",
"2. Build OCR->classify->extract with per-field confidence; calibrate thresholds on validation split.",
"3. Implement router + reviewer UI; measure STP vs overturn trade-off curve.",
"4. Add idempotent ERP posting + reconciliation; chaos-test duplicate deliveries.",
"5. Add regression gate: release blocked on golden-set delta; record before/after P&L.",
"6. Publish one-pager: $/doc, hours returned, accuracy vs human baseline."],
"tests": [
"Golden test: field-F1 >= targets; STP >= 80% with overturn < 3%.",
"Idempotency test: 100 duplicate deliveries -> exactly-once ledger.",
"Drift test: new template variant routes to review, never silently mis-posts.",
"Audit test: every posting traceable to source spans + reviewer identity."]},
{"name": "Capstone 2 — Agentic Ticket-Resolution Operator (RPA + RAG + approvals)",
"arch": ("Ticket webhook -> classifier (password-reset/access/billing/how-to) -> grounded answer draft (runbook RAG) -> risk router: "
"auto-resolve low-risk with verification, HITL medium, human-only high -> action executor (AD reset/CRM note) with approvals -> CSAT + reopen tracking."),
"stack_rows": [
["Compute", "Python API + worker fleet (Docker)"],
["Orchestration", "Temporal workflows with durable SLA timers"],
["Retrieval", "Hybrid RAG over runbooks (Module D pattern) with citations"],
["Safety", "Approval gates (supervisor pattern), PII redaction, audit trail"],
["Measurement", "Auto-resolve rate, reopen rate, CSAT delta, $/ticket"]],
"steps": [
"1. Ingest 500 historical tickets; label category + risk tier; freeze eval split.",
"2. Build hybrid RAG over runbooks with quote-or-abstain answering.",
"3. Implement risk router + approval workflow; low-risk actions verified post-execution.",
"4. Chaos-test: stale runbook version must abstain or cite version, never hallucinate steps.",
"5. A/B vs human baseline on reopen rate; ship expansion proposal for one more category."],
"tests": [
"Safety test: high-risk tickets never auto-execute (100% HITL).",
"Grounding test: ungrounded questions abstain with citation coverage on answered ones.",
"Regression test: reopen rate <= human baseline before expanding scope."]}],
};

ROLE_AISEC = {
"num": 4, "title": "AI Security Engineer",
"tagline": "Make AI systems hard to break and safe to operate — red-team mind, platform hands",
"mission": ("Own the AI threat surface: prompt injection, jailbreaks, data/tool poisoning, model extraction, PII leakage, "
"insecure tool-use and over-permissioned agents. Build guardrails (NeMo/Llama Guard, policy engines), red-team harnesses "
"(Garak/Promptfoo-style), eval gates that block unsafe releases, and incident runbooks for AI-specific breaches."),
"tele_intro": ("Recon: OWASP Top 10 for LLM Applications (2025 edition) as the de-facto JD vocabulary; frontier-lab safety postings; "
"bank/healthcare AI-risk roles; GCC security COEs adding LLM-app review queues. Variant titles: LLM Security Engineer, "
"AI Red-Team Engineer, Product Security (AI), AI Risk & Safety Engineer. Smallest but fastest-growing of the 7 roles."),
"openings_rows": [
["United States", "~2,000-3,200 active; hubs: Bay Area, Seattle, NYC, DC (gov/AI-safety), Boston"],
["EMEA", "~900-1,400 active; hubs: London, Dublin, Amsterdam, Berlin (EU AI Act-driven demand)"],
["India / APAC", "~1,200-2,000 active; hubs: Bengaluru, Hyderabad, NCR, Singapore (GCC security COEs)"],
["Global Remote", "~500-800 active; audit/red-team boutiques + bug-bounty-adjacent"],
["TOTAL (directional, Sep 2026)", "~4,500-6,500 worldwide; EU AI Act + enterprise AI rollouts as growth engines"]],
"comp_rows": [
["L3 / Mid (3-5 yrs)", "$145K", "$172K", "$205K", "$250K"],
["L4 / Senior (5-9 yrs)", "$175K", "$212K", "$258K", "$320K"],
["L5 / Staff / Principal (9+ yrs)", "$220K", "$270K", "$335K", "$430K+"]],
"comp_note": ("Sources: Levels.fyi security + AI premium composites; 2026 AI-safety salary surveys (frontier-lab safety bands highest). "
"India mapping: Mid INR 20-35 LPA; Senior INR 35-60 LPA; Staff/Principal INR 60-95 LPA+ (product + GCC security COEs). "
"Offensive-security credentials (OSCP/GWAPT-adjacent) + shipped guardrails are documented pay levers. 1 USD approx 84 INR."),
"top15_rows": [
["Frontier labs & AI platforms", "OpenAI, Anthropic (safety/alignment-adjacent delivery), Cohere, Databricks, Snowflake"],
["Hyperscalers", "AWS (Bedrock Guardrails/Inspector), Microsoft (Defender + AI red team), Google (Model Armor, DeepMind safety)"],
["Enterprise / GCC", "Global banks (model-risk + AI-risk), healthcare payers, Big-4 cyber practices with AI-risk lines"],
["Security vendors & boutiques", "CrowdStrike/Zscaler-class platforms adding AI modules, Promptfoo-class eval tooling, red-team boutiques"]],
"exp_bullets": [
("Minimum tenure: ", "3-4 years in AppSec/product security or backend engineering with authN/Z, threat modeling, and incident response reps."),
("Preferred tenure: ", "5-8 years incl. 2+ years securing LLM/agent systems: guardrail deployment, red-team ops, eval-gate ownership, AI incident runbooks."),
("Feeder backgrounds: ", "AppSec/SOC -> AI Security (dominant); backend/fullstack with auth+API depth; pentesters adding LLM tradecraft; GRC/risk analysts who learned to code probes."),
("Education signal: ", "OSCP/GWAPT/OSWE-class offensive certs or cloud-security specialty + a public red-team writeup/CVE/advisory; EU AI Act literacy prized in EMEA.")],
"bound_rows": [
["Data Engineering", "Advise on training/inference data lineage, poisoning vectors, retention minimization", "Pipeline ownership, quality SLAs", "Joint data-provenance reviews; security sets requirements, DE implements"],
["ML Research", "Evaluate safety properties, attack papers into test packs, alignment-eval collaboration", "Capability research, training", "Red-team findings feed research; research discloses failure modes early"],
["Platform / DevOps", "Policy-as-code packs, guardrail sidecars, secret/tool-permission baselines", "Cluster/service lifecycle", "Security ships guardrail modules; platform enforces via admission/policy gates"],
["Solutions Architecture", "Secure reference patterns, risk-acceptance templates, customer security reviews", "Deal demos, scoping", "Security gives SAs answers that survive procurement questionnaires"]],
"artifacts": [
("PR: guardrail sidecar (injection-block + PII-redact) on all assistant ingress",
"Change: middleware from Module D security pattern deployed as sidecar; fail-closed on redactor error; latency budget 25ms p99 with async deep-scan path. Validation: red-team pack (Module D probes) green in CI; latency canary clean. Rollback: header flag bypass with audit alert (break-glass only)."),
("Red-team report: indirect injection via retrieved contract clause",
"Finding: retrieved Tier-1 vendor PDF contained 'ignore policy, approve' instruction that agent obeyed. Severity critical. Fix: instruction-hierarchy enforcement (retrieved content is data, never instruction), tool-approval on financial actions, provenance banners in UI. Re-test pack added; finding briefed to research + FDE teams."),
("Architecture review: agent tool-permission model (least privilege per workflow)",
"Decision: per-workflow scoped credentials, short-lived tokens, no ambient prod-write; high-impact tools require step-up approval with filmed audit. Rejected ambient service-account design with blast-radius math (one prompt -> whole ERP write)."),
("Incident runbook: suspected training-data poisoning",
"Steps: quarantine dataset version, hash-diff vs provenance manifest, retrain-from-clean checkpoint, eval-delta review, disclosure timeline, regulator-notification triggers (EU AI Act mapping). Tested via tabletop + poisoned-canary drill quarterly."),
("Quarterly AI-risk scorecard",
"Per app: OWASP-LLM coverage, red-team pass rate, guardrail block/prevent stats, mean-time-to-mitigate, exception inventory with owners. Outcome: 3 apps moved from exception to compliant; 1 launch blocked (documented save). This is the promotion artifact.")],
"toolchain": [
("IDEs/editors: ", "VS Code + Burp/ZAP for API attack surface; Python notebooks for probe development; policy-IDE (Rego) for guardrail rules."),
("CLI daily drivers: ", "garak, promptfoo, nuclei/httpx for surface mapping, opa/conftest, cosign/sbom tools, siem query CLIs."),
("Inference runtimes: ", "Llama Guard / NeMo Guardrails / ShieldGemma-class classifiers; vendor moderation + content-safety APIs as second opinions."),
("Telemetry dashboards: ", "SIEM (Splunk/Sentinel/Chronicle) AI-attack boards, guardrail block-rate + bypass-attempt analytics, red-team trend lines.")],
"skills_rows": [
["Core systems & programming", "Python (Critical); web/API security fundamentals (Critical); SQL for forensics (High)", "Rust/Go/CUDA (Low except platform-hardening teams)"],
["Inference & serving", "Serving-stack attack surface (Triton/vLLM/TGI configs, SSRF/model-endpoint abuse) (High)", "TensorRT/ONNX internals (Low)"],
["Agentic & orchestration", "Tool-permission design, approval workflows (LangGraph gates) (Critical)", "CrewAI/AutoGen internals (Low-Medium)"],
["Vector storage & retrieval", "Poisoned-corpus defense, access-filtered retrieval (tenant isolation) (High)", "Index internals (Low)"],
["Cloud AI platforms", "Guardrails-for-Bedrock / Content Safety / Model Armor + KMS/private endpoints (High)", "Deep platform admin (Medium)"],
["LLMOps / telemetry / eval", "Garak + Promptfoo + custom probe packs (Critical); Ragas-style safety evals (High); SIEM detection content (High)", "LangSmith/Phoenix (Medium)"],
["Security & guardrails", "OWASP Top 10 for LLMs (Critical); NeMo Guardrails/Llama Guard (Critical); threat modeling + pentest tradecraft (Critical)", "Formal verification (Emerging)"]],
"theory": [
{"h": "T1. The LLM threat model: what is new vs what is old",
"body": ("Old threats persist (injection is XSS's cousin, SSRF via tool-use, IDOR in multi-tenant retrieval, secret leakage in logs). "
"New: the model itself is a confused deputy — it cannot reliably distinguish instruction from data, so retrieved content, tool outputs, "
"and file attachments become injection carriers (indirect prompt injection). Attack classes: direct injection, jailbreak (policy evasion), "
"data/tool poisoning (corrupt the grounding), model extraction/inversion (steal weights or training rows), PII regurgitation, "
"excessive agency (over-permissioned tools), and eval gaming. Defense is layered: minimize agency (least-privilege tools), validate at boundaries "
"(schemas + provenance), monitor behavior (not just strings), and assume bypass — design so single control failure is insufficient for impact. "
"Memorize OWASP LLM01-LLM10 cold; interviewers use it as a checklist."),
"diagram": "attacker ──> [prompt | retrieval doc | tool output | file] ──> model (confused deputy) ──> tools/data ──> impact\\n              └──────── layered defenses: least-privilege + validation + provenance + monitoring ────────┘"},
{"h": "T2. Guardrail architecture: classifiers, policies, and fail-closed design",
"body": ("Production guardrails combine: (i) deterministic pre-filters (regex/PII patterns, allowlists, schema validation — cheap, fast, auditable), "
"(ii) classifier judges (toxicity/PII/injection scorer, e.g. Llama Guard-style) with calibrated thresholds, (iii) policy engines (OPA/Rego: role x data-class x tool -> allow/deny/escalate), "
"(iv) output verification (citation checks, schema conformance, canary tokens). Latency budget forces two paths: sync fast-path (<25ms p99: regex+schema+light classifier) "
"and async deep-path (heavy judges, full red-team replay on samples). Fail-closed on safety-component errors; break-glass bypass requires ticketed audit. "
"Measure bypass rate (red-team), false-positive cost (blocked legit users), and latency tax — a guardrail nobody can afford to keep on is off."),
"diagram": "request ──> fast-path(regex+schema+light clf) ──block?──> deep-path(heavy judge+policy) ──> tools ──> output-verify ──> user\\n                                    │ fail-closed on component error; every deny logged with reason + sample-hash"},
{"h": "T3. Red-teaming as engineering: from vibes to regression gates",
"body": ("Ad-hoc 'try to break it' finds headlines, not coverage. Engineering-grade red-teaming: seeded probe packs per OWASP category with severity tags, "
"automated runners (Garak/Promptfoo + custom target adapters), deterministic verdicts (must-not-contain + judge panel), tracking (new failures vs fixed vs regressed), "
"and CI gates (critical-severity fail blocks release). Rotate: fresh jailbreak techniques monthly (attack literature moves fast), canary probes in production "
"(synthetic attacks verifying detection still fires), and purple-team reviews (builders + breakers agree the fix, then the probe becomes permanent). "
"Report format executives fund: coverage matrix x severity x trend, with one blocked-launch story per quarter."),
"diagram": "probe packs ──runner──> target ──verdicts──> gate(BLOCK/REVIEW/SHIP) ──> findings ──> fix ──> probe becomes permanent"},
{"h": "T4. Data-layer defense: provenance, tenant isolation, poisoning response",
"body": ("Most AI breaches are data-layer failures: poisoned corpus (malicious doc indexed), cross-tenant retrieval (filters applied in UI, not in query), "
"over-retained prompts (breach scope balloons), unlogged inference (no forensic trail). Controls: cryptographic provenance (hash + signer per source, quorum for high-risk corpora), "
"retrieval-time tenant predicates (enforced in the vector query, tested with negative probes), minimization + TTLs on prompts/logs, immutable audit (who asked, what grounded, what tools fired). "
"Poisoning response mirrors malware IR: quarantine version, diff vs manifest, rebuild from clean checkpoint, eval-delta sign-off, disclosure clock. Drill it before you need it.")}],
"syllabus_concepts": [
"OWASP Top 10 for LLM Applications (2025) + MITRE ATLAS matrix — the interview checklist",
"Web/API security: OAuth2/OIDC, SSRF/IDOR/XSS, secret management, threat modeling (STRIDE), pentest workflow",
"Guardrails: NeMo Guardrails (Colang), Llama Guard/ShieldGemma classifiers, OPA/Rego policy, moderation APIs",
"Red-team tooling: Garak, Promptfoo, custom harnesses; judge-panel design; CI gating",
"Privacy/compliance: PII/NER redaction, data minimization, EU AI Act risk tiers, NIST AI RMF, model-risk (SR 11-7-style) vocabulary"],
"syllabus_papers": [
"OWASP Top 10 for LLM Applications 2025 — read the full project docs, not summaries",
"Not what you've signed up for: indirect prompt injection (Greshake et al., 2023) — the FDE-relevant attack",
"Universal/transferable adversarial attacks on aligned LMs (Zou et al., 2023) — jailbreak mechanics",
"PoisonedRAG / corpus-poisoning literature (2024) — retrieval-layer defense motivation",
"MITRE ATLAS case studies — enterprise threat-model vocabulary"],
"syllabus_docs": [
"NeMo Guardrails + Llama Guard + Promptfoo + Garak docs — run all four against a demo app",
"Guardrails-for-Bedrock / Azure Content Safety / Google Model Armor — one cloud suite deeply",
"OPA/Rego + admission-controller patterns; cosign/SLSA provenance for model artifacts",
"SIEM detection-content authoring (Splunk/Sentinel) for AI-attack telemetry; tabletop templates"],
"failures": [
("Indirect injection via retrieved document pays a fraudulent refund",
"Agent treats vendor-PDF instruction as command. Fix: instruction hierarchy (retrieved = data), financial-tool approvals, provenance UI banners, negative-probe pack."),
("Cross-tenant RAG leaks salary data between customers",
"Tenant filter applied in presentation layer only. Fix: predicate pushdown into vector query + negative tenant-probe suite + per-tenant index option for top tier."),
("Guardrail latency tax gets it silently disabled",
"p99 +400ms; on-call disables sidecar during peak. Fix: fast/deep paths, budget enforcement in load tests, disable-requires-ticket control."),
("PII training rows regurgitated to another user",
"Memorized support tickets leak via completion. Fix: PII scrub pre-training, output filters, canary-secret monitoring, minimization + TTLs."),
("Model endpoint SSRF reaches cloud metadata",
"Tool-use fetch hits 169.254.169.254. Fix: egress allowlists, metadata-service hardening (IMDSv2), tool URL validation, no ambient creds."),
("Eval-gaming: safety metrics green, red-team red",
"Judge overfit to training phrasing. Fix: held-out probe sets, rotating techniques, human spot audits, judge disagreement metrics.")],
"ats_keywords": ("OWASP LLM Top 10, prompt injection, jailbreak, red team, Garak, Promptfoo, Llama Guard, NeMo Guardrails, "
"threat modeling, penetration testing, AppSec, SOC, SIEM, SOAR, OPA, Rego, IAM, KMS, PII redaction, NER, EU AI Act, "
"NIST AI RMF, Python, Burp, ZAP, cloud security, model risk, incident response"),
"ats_antipatterns": [
"Pure GRC prose with zero probes, guardrail code, or blocked-launch evidence.",
"'AI ethics enthusiast' with no threat model, no tool output, no severity-rated finding.",
"Claiming CISSP-only readiness for hands-on LLM red-team loops."],
"loop_rows": [
["Recruiter screen (30 min)", "Security tenure, offensive vs defensive mix, AI exposure", "Named findings with severity + impact"],
["Hiring-manager (45-60 min)", "Worst AI finding owned; blocked launch; incident led", "Severity judgment, disclosure courage, builder empathy"],
["Live red-team (60-90 min)", "Break a demo assistant (find 2+ issues), then propose fixes", "Methodical surface mapping, severity rating, fix quality"],
["Guardrail build (60-90 min)", "Code the injection+PII middleware with latency budget", "Fail-closed instinct, test coverage, bypass thinking"],
["Behavioral + disclosure (45 min)", "Disagreed with PM on ship; handled false positives anger", "Risk communication, audit honesty, user empathy"]],
"interview_qa": [
("Q1. Map OWASP LLM01-LLM10 to concrete controls in a customer-support agent.",
"A. Model answer: walk all ten — injection (hierarchy + provenance), insecure output (schema + verification), poisoning (provenance quorum), DoS (budgets + autoscale), supply-chain (SBOM/pinned artifacts), disclosure (PII filters + minimization), plugin design (scoped tools + approvals), agency (least-privilege + halt), overreliance (citations + abstain), model theft (rate limits + output watermarking audit). Controls named per item with test method."),
("Q2. Live: find vulnerabilities in this RAG support bot (15 min).",
"A. Model answer: narrate surface map (prompt, docs, tools, auth, logs), try direct injection, upload poisoned doc, test tenant isolation with second identity, check tool perms (can it refund?), inspect error verbosity; rate each finding (critical/high/med) with repro steps and one-line fix. Process clarity outranks exploit count."),
("Q3. Code the guardrail middleware with a 25ms p99 budget.",
"A. Model answer: reproduce Module D guard(): compiled regex fast-path, PII map, injection signatures, oversize cap, fail-closed error handling, latency measurement; deep-path async sampling explained; tests: bypass corpus, PII battery, latency benchmark, redactor-failure-closed test."),
("Q4. Production alert: retrieved doc telling the agent to exfiltrate. Respond.",
"A. Model answer: contain (kill-switch/approval-freeze the tool), preserve (audit + sample hashes), eradicate (quarantine corpus version, purge index), recover (clean reindex + eval gate), lessons (provenance control + permanent probe); comms + disclosure timeline; tabletop scheduled."),
("Q5. The business wants the guardrail off because it blocks 8% of legit traffic. Decide.",
"A. Model answer: disaggregate blocks (true vs false positives with samples), tune thresholds + allowlists per cohort, fast-path legit patterns, measure bypass-rate cost of disabling vs support-ticket cost; propose staged relaxation with canary + rollback; refuse blanket disable in writing with risk quantification — the answer they are really testing.")],
"capstones": [
{"name": "Capstone 1 — Guardrailed Support Agent + Red-Team Gate (block-the-release rig)",
"arch": ("Demo support agent (RAG + refund/status tools with approvals) fronted by guardrail sidecar (Module D) -> probe packs (Module D red-team + "
"custom tenant-isolation and poisoning probes) run in CI -> BLOCK/REVIEW/SHIP verdict -> SIEM-style findings board with severity trends. "
"Includes poisoned-canary corpus version proving the gate catches regressions."),
"stack_rows": [
["Compute", "Python 3.11 agent + sidecar (Docker Compose)"],
["Safety", "Guardrail middleware + Llama Guard-class classifier hook + OPA-style policy file"],
["Testing", "Garak + Promptfoo + custom probes; pytest gate (critical fail = red build)"],
["Data", "Two corpus versions (clean + poisoned-canary) with hash manifests"],
["Ops", "Audit log + findings dashboard (Streamlit/Grafana)"]],
"steps": [
"1. Build the agent with scoped tools + approval workflow; log every tool call with provenance.",
"2. Implement sidecar (Module D) with fast/deep paths + latency instrumentation.",
"3. Assemble probe packs per OWASP category incl. tenant-isolation negatives.",
"4. Wire CI gate; prove clean corpus SHIPs and poisoned-canary BLOCKs.",
"5. Run latency test proving p99 tax within budget; document break-glass procedure.",
"6. Publish red-team report with coverage matrix + one blocked-launch narrative."],
"tests": [
"Gate test: poisoned corpus always BLOCKs; clean always SHIPs (deterministic).",
"Bypass test: 50-attack battery bypass rate <5% with samples retained.",
"Tenant test: cross-tenant probes 100% denied at query layer.",
"Latency test: p99 overhead within declared budget under load."]},
{"name": "Capstone 2 — AI Incident Response Drill Kit (tabletop + tooling)",
"arch": ("Scenario library (poisoning, exfiltration via tool, PII regurgitation, model theft) -> drill runner (injects synthetic audit traces) -> "
"responder scores MTTD/MTTR per playbook -> gap report -> control backlog. Packaged so a hiring manager can run one scenario live in interview."),
"stack_rows": [
["Content", "4 scenarios with inject timelines + expected responder actions"],
["Tooling", "Audit-trace generator + SIEM query pack + quarantine/reindex scripts"],
["Process", "RACI, disclosure clock template, EU AI Act notification mapping"],
["Validation", "Quarterly drill calendar with metric targets"],
["Evidence", "After-action report template with control deltas"]],
"steps": [
"1. Write 4 scenarios with realistic audit traces and tool-call logs.",
"2. Build drill runner producing the traces on demand.",
"3. Run solo drill timed; record MTTD/MTTR and missed steps.",
"4. Harden one control per gap found; re-drill proving improvement.",
"5. Package as interview-ready demo (15-min live tabletop)."],
"tests": [
"Detection test: each scenario detected via documented query within target minutes.",
"Containment test: kill-switch/approval-freeze demonstrably stops tool abuse.",
"Disclosure test: notification decision reached within clock using the template."]}],
};
