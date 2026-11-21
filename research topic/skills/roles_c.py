"""Roles 5-7: Forward Deployed / AI Deployment, GenAI/Agentic AI, AI Solutions Engineer."""

ROLE_FDE = {
"num": 5, "title": "Forward Deployed / AI Deployment Engineer (FDE)",
"tagline": "The engineer-diplomat — embed, ship day one, own the outcome in the customer's world",
"mission": ("Embed with one customer at a time (8-16 week arcs): discover the real workflow on site, model their domain into an "
"ontology, ship LLM/agentic systems (RAG, tool-use, MCP servers, sub-agents) against their data inside their constraints, "
"harden to production with evals-as-acceptance, hand over operable systems, and route field learning back to the platform roadmap. "
"Success = the customer's workflow changed, not that code merged."),
"tele_intro": ("Recon: Palantir FDSE JD (Lever, $135-200K base band, startup-CTO framing), OpenAI FDE SF ($162-280K + equity, 50% travel, "
"full-arc ownership), Anthropic Applied AI (40% build / 30% customer / 30% product feedback), Pragmatic Engineer deep dive, "
"aiarch.dev + Vibe Engines 2026 trackers (Palantir ~51 openings, OpenAI ~31; FDE postings +729-800% YoY to ~5.3k; frontier-lab mid "
"$350-550K TTC, senior $560-785K, staff $600K-1M+). Variant titles: FDSE, Deployment Strategist (Palantir Echo), Applied AI Engineer, Agent Engineer."),
"openings_rows": [
["United States", "~2,500-3,500 active; hubs: SF, NYC, DC (gov), Seattle; travel-heavy by definition"],
["EMEA", "~900-1,400 active; hubs: London, Paris, Berlin, Zurich (banking/pharma embeds)"],
["India / APAC", "~700-1,100 active; hubs: Bengaluru, Singapore, Tokyo (delivery + GCC embeds)"],
["Global Remote", "~600-1,000 active; startup FDEs (compressed 1-4 week cycles)"],
["TOTAL (directional, Sep 2026)", "~4,500-6,500 worldwide; venture's 'hottest job in tech' (a16z, 2026)"]],
"comp_rows": [
["Entry / New-grad (frontier-adjacent)", "$180K", "$215K", "$250K", "$300K"],
["Mid (3-6 yrs, Palantir band)", "$171K", "$211K", "$260K", "$295K"],
["Senior (frontier labs)", "$350K", "$450K", "$560K", "$785K"],
["Staff / Principal (frontier)", "$486K", "$630K", "$800K", "$1,000K+"]],
"comp_note": ("Sources: Levels.fyi Palantir FDSE ($171-295K, median ~$211K); OpenAI FDE posting ($162-280K base + equity); 2026 FDE "
"compensation trackers (broad median ~$183-190K; frontier mid $350-550K; Palantir average ~$238K, range to $486K, staff $630K+). "
"Equity dominates frontier bands; travel + clearance premiums stack. India mapping: GCC-embedded INR 25-45 LPA; frontier-remote INR 50-90 LPA+. 1 USD approx 84 INR."),
"top15_rows": [
["Frontier labs", "OpenAI (FDE org, 10+ and scaling), Anthropic (Applied AI), Google DeepMind/Google Cloud FDE practice"],
["Palantir + data platforms", "Palantir (FDSE Delta + Strategist Echo), Databricks, Cohere, Mistral, Glean/Sierra-class"],
["Enterprise AI delivery", "Scale AI, Salesforce, ServiceNow, Microsoft Frontier org (6,000-expert plan), AWS FDE practice"],
["Vertical AI startups", "Runway/Greptile-class (compressed-cycle FDEs), defense/health/finserve AI startups, a16z services-led-growth bets"]],
"exp_bullets": [
("Minimum tenure: ", "2-3 years shipping production full-stack/data systems with real users; must show ambiguous-problem ownership."),
("Preferred tenure: ", "5+ years (Ramp-class bar) incl. customer-facing delivery: scoping, security reviews, on-site hardening, handoff that stuck."),
("Feeder backgrounds: ", "Fullstack/backend -> FDE (most common); data engineering (ontology strength); SRE/DevOps (hardening strength); founders/ex-founders (ambiguity tolerance); IT infra veterans with stakeholder range (underrated vector)."),
("Education signal: ", "Engineering depth over pedigree; Palantir hires from ~1 yr experience with brutal decomposition interviews; clearance/government familiarity helps DC-track roles.")],
"bound_rows": [
["Data Engineering", "Customer-specific ontology + pipelines for THIS deployment", "Canonical platform pipelines for all customers", "FDE extends platform models; feeds reusable transforms back"],
["ML Research", "Applied evals, grounding, tool-use behavior in the wild", "Model training, alignment, benchmarks", "FDE field feedback shapes research; research briefs FDE on model limits"],
["Platform / DevOps", "Harden in customer env (their cloud/VPC/air-gap), deployment scripts", "Core platform lifecycle", "FDE is platform's field sensor + hardest integration tester"],
["Solutions Architecture", "Write production code + own post-launch outcomes", "Demos, POCs, pre-sales config (hands off pre-prod)", "FDE replaces SA-plus-services with engineer-owned delivery"]],
"artifacts": [
("Bootcamp delivery log: AIP-style 5-day LLM-grounded claims app (days 0-4)",
"Day 0-1: ontology (Claim/Customer/Policy entities + links) modeled with adjusters. Day 2: ontology exposed as MCP tools. Day 3: working decision-workflow app on live (masked) data. Day 4+: iteration against adjuster feedback + eval acceptance suite. Artifact includes scope-cut log (what was NOT built) — interviewers prize the cuts."),
("PR: MCP server + sub-agents handed to customer platform team",
"Change: typed tool surface (lookup/verify/escalate) with approval flags, audit log, versioned skills docs; customer engineers merged 2 follow-on tools unassisted within a week (handoff success metric). Security review packet attached (data-flow + residency + SSO)."),
("Post-mortem: eval regression discovered on customer PII-laden edge cases",
"Summary: acceptance evals passed on clean data, failed on real claims language (abbreviations, code-switching). Fix: expanded eval set from shadowing sessions, grounding-abstain behavior, weekly field-eval review with customer SMEs. Lesson logged to platform team: eval-set sourcing guide updated."),
("Architecture review: air-gapped deployment variant for regulated agency",
"Decision: VPC-isolated stack with model weights mirrored, no external calls, hash-pinned artifacts, offline eval runner. Trade-offs: 3-week hardening cost vs deal requirement; documented residual risks + waiver owners."),
("Handoff memo + expansion proposal (the FDE promotion artifact)",
"Runbook, eval dashboard ownership transfer, on-call rotation design, cost/usage forecast, and 3 expansion workflows ranked by measured impact of v1. Closes with platform feedback: 2 roadmap items filed with field evidence.")],
"toolchain": [
("IDEs/editors: ", "Cursor/VS Code full-stack (Python + TypeScript); notebooks for eval exploration; customer-constrained editors on classified sites."),
("CLI daily drivers: ", "git/gh, docker, kubectl, cloud CLIs inside customer tenancy, mcp inspector CLIs, eval runners, SSO/device-auth flows."),
("Inference runtimes: ", "Frontier APIs (Claude/GPT) + customer-approved models; RAG (pgvector/Pinecone/Weaviate), MCP servers, sub-agent harnesses."),
("Telemetry dashboards: ", "Eval acceptance boards (correctness/grounding/latency/token-cost), usage-adoption funnels proving workflow change, platform feedback logs.")],
"skills_rows": [
["Core systems & programming", "Python + TypeScript full-stack (Critical); SQL beyond basics (Critical); Go/Java as needed (Medium)", "CUDA (Low)"],
["Inference & serving", "API + self-hosted serving inside customer VPC (High); Triton/TGI where air-gapped (Medium)", "TensorRT/ONNX tuning (Low-Medium)"],
["Agentic & orchestration", "Tool-use/MCP/sub-agents + LangGraph-style orchestration (Critical); eval-driven iteration (Critical)", "CrewAI/AutoGen (Medium)"],
["Vector storage & retrieval", "pgvector/Pinecone/Weaviate + reranking on customer docs (Critical)", "Milvus/Qdrant/OpenSearch per residency (High)"],
["Cloud AI platforms", "One hyperscaler deep + frontier APIs (Critical); private/on-prem deployment (High)", "Multi-cloud (Medium)"],
["LLMOps / telemetry / eval", "Eval suites as acceptance tests (Critical); LangSmith/Phoenix/Ragas (High); OTel/Prometheus (High)", "TruLens/MLflow (Medium)"],
["Security & guardrails", "Customer trust: SSO, residency, audit, PII handling (Critical); OWASP-LLM + Llama Guard/Promptfoo (High)", "NeMo/Garak depth (Medium-High)"]],
"theory": [
{"h": "T1. The ontology-first doctrine (Palantir pattern, generalized)",
"body": ("Before any model call, model the customer's world: entities (Claim, Policy, Adjuster), properties, and link types — the ontology becomes "
"the permanent data contract the LLM reasons over via tools. Why it wins: it converts vague 'AI for claims' into typed operations (lookup_claim, "
"verify_coverage, escalate_with_evidence), bounds hallucination to real entities, and survives model swaps. Method: 5-10 deep conversations/week with "
"operators (not just sponsors), shadow real cases, draft ontology v0 in days, validate by wiring one decision workflow end to end. The ontology review "
"with domain skeptics is the highest-leverage meeting of the embed — get the nouns wrong and every agent step inherits the error."),
"diagram": "shadow operators ──> entities+links (ontology) ──> typed MCP tools ──> agent workflow ──> eval acceptance ──> handoff"},
{"h": "T2. Ship-on-day-one mechanics: scoping under ambiguity",
"body": ("FDE scoping inverts normal engineering: fixed time (days), variable scope, non-negotiable working software on real data. Technique: "
"problem-slicing (one decision workflow, one user, one data source), steel-thread delivery (ugly end-to-end beats polished slice), explicit non-goals "
"list (cuts documented daily), and risk-ordered sequencing (security review + data access on day 1 — the long poles). Estimation: no story points; "
"commit to demo-able increments every 48 hours. Communication is the control plane: thinking aloud in front of skeptics, written decision logs, "
"demo-or-it-didn't-happen Fridays. Half the interview loop tests exactly this (decomposition rounds, defend-your-take-home)."),
"diagram": "day1 access+risk ──> steel thread (ugly E2E) ──> 48h demos ──> harden (evals+security) ──> handoff (customer builds solo)"},
{"h": "T3. Evals as the acceptance contract",
"body": ("In FDE work the eval suite IS the requirements doc and the signature page. Structure: golden cases sourced from shadowing (real phrasing, "
"real edge cases incl. PII-laden/abbreviated inputs), dimensions (correctness, grounding/citation, policy compliance, latency, cost), thresholds "
"negotiated with the customer (e.g. 95% to ship), and regression runs on every change. Failure discipline: eval failures block demos, not just deploys — "
"nothing erodes customer trust faster than a live demo hallucinating on their data. Carry eval deltas back to the platform team; the highest-leverage "
"FDE output is often the eval set + failure taxonomy, reused across ten future embeds."),
"diagram": "shadow ──> golden cases ──> thresholds (signed) ──> gate every change ──> acceptance sign ──> platform feedback"},
{"h": "T4. Hardening in hostile environments: security, residency, handoff",
"body": ("Customer environments are adversarial by constraint: their network, their IdP, their data classification, their change board. Hardening checklist: "
"SSO/service accounts with least privilege, secret storage in their vault, data-flow + residency diagram signed by their security, PII minimization with "
"redaction proofs, audit exports to their SIEM, runbooks their on-call can execute without you, and a filmed rollback. Handoff success metric: customer "
"engineers ship a follow-on change unassisted within 2 weeks. Refuse staff-augmentation traps (Palantir doctrine): customer-owned applications with "
"your leverage decreasing over time — expansion comes from proven impact, not headcount.")}],
"syllabus_concepts": [
"Full-stack delivery: Python + TypeScript APIs/UIs, auth flows (OAuth2/OIDC/SAML), webhooks, idempotency, schema evolution",
"Data fluency: advanced SQL, pipeline basics, ontology/domain modeling, data contracts",
"Applied AI: RAG (chunking/embeddings/rerank), tool-use/MCP, sub-agents, structured outputs, eval design",
"Deployment under constraint: VPC/private clouds, air-gap patterns, SSO, secrets, audit, compliance narratives",
"Discovery craft: customer interviewing, scoping, demo storytelling, written decision logs, stakeholder mapping"],
"syllabus_papers": [
"Palantir S-1 + Foundry ontology docs — the original FDE/ontology doctrine",
"RAG (Lewis et al., 2020); ReAct (Yao et al., 2023) — agent reasoning foundations",
"Ragas / LLM-as-judge literature — eval-acceptance mechanics",
"Instruction hierarchy research (Wallace et al., 2024) — securing deployed agents",
"Anthropic/OpenAI applied-AI engineering blogs — current frontier deployment patterns"],
"syllabus_docs": [
"Anthropic Applied AI + OpenAI FDE career pages (role language mirrors interview rubrics)",
"Palantir Foundry/AIP bootcamp + ontology modeling guides",
"MCP specification + inspector; LangGraph + eval (LangSmith) docs",
"One hyperscaler security-review packet template (data-flow, residency, SSO, audit) — write one yourself"],
"failures": [
("Demo hallucination on customer data kills trust",
"Unvetted demo invents policy clauses in front of skeptics. Fix: eval-gated demos, abstain behavior, pre-demo dry run on their sample cases."),
("Scope sprawl: embed becomes staff-augmentation",
"Months pass, no acceptance, headcount dependency. Fix: 8-16 week arcs, steel threads, non-goals log, handoff metric from week 1."),
("Security review ambush in week 10",
"Data-flow questions surface at sign-off. Fix: security packet day 1, residency/SSO/audit designed in, not bolted on."),
("Eval-passing, user-rejecting system",
"Golden cases written by engineers, not operators; real phrasing fails. Fix: shadow-sourced cases, SME sign-off on thresholds, field-eval reviews."),
("Handoff collapse after exit",
"Only the FDE can operate it. Fix: customer-built follow-on change before exit, runbooks tested by their on-call, eval ownership transferred."),
("Feedback black hole: field learning dies in Slack",
"Platform repeats the same failure next embed. Fix: written field notes -> roadmap items with evidence; 30% time budgeted for feedback synthesis.")],
"ats_keywords": ("forward deployed, FDSE, deployment strategist, applied AI, Python, TypeScript, full-stack, RAG, LangGraph, "
"MCP, sub-agents, evals, LLM, customer-facing, discovery, scoping, solution delivery, AWS/GCP/Azure, Docker, Kubernetes, "
"SQL, data pipelines, SSO, security review, stakeholder management, travel"),
"ats_antipatterns": [
"Pure platform resume with zero customer-facing delivery, discovery, or on-site hardening evidence.",
"'Solutions engineer' duties (demos/POCs) framed as FDE without production ownership after launch.",
"No evals, no ontology/domain-modeling, no handoff story — the three FDE keywords."],
"loop_rows": [
["Recruiter screen (30 min)", "Engineering depth + customer range + travel reality", "One ambiguous delivery owned end to end"],
["Decomposition round (60 min)", "Messy CSV + vague goal -> scope aloud to a Friday ship", "Problem-slicing, cuts, risk ordering, narration"],
["Take-home + defense (multi-hour + 60 min)", "Build working prototype on sample data, defend decisions live", "Working software, trade-off honesty, eval thinking"],
["Customer simulation (45-60 min)", "Skeptical stakeholder + shifting requirements mid-session", "Calm, scoping, saying no with alternatives"],
["Values + platform feedback (45 min)", "Anthropic-style values; what field learning changed the roadmap", "Judgment, ownership, product-feedback instinct"]],
"interview_qa": [
("Q1. Given this messy claims CSV, what ships by Friday? (Decomposition round.)",
"A. Model answer: narrate aloud — profile the data (5 min), pick one adjuster + one decision (coverage check), define steel thread (upload -> entity view -> grounded recommendation with citations), name explicit non-goals (no auth overhaul, no bulk backfill), flag long poles (data access, security review) for day 1, define Friday acceptance (3 golden cases demoed live + eval sheet). They score slicing and narration, not the CSV."),
("Q2. Defend your take-home: why this architecture, what breaks at 10x?",
"A. Model answer: walk decisions with rejected alternatives, cite eval numbers, name the first bottleneck (retrieval latency? tool fan-out? cost?), propose the 10x change (index sharding, caching, async agents) with cost math, and admit the weakest part unprompted — candor under pressure is the signal."),
("Q3. Design the eval acceptance suite for a coverage-decision agent.",
"A. Model answer: shadow-sourced golden cases (clean + adversarial + PII-laden), dimensions (correctness, grounding, policy, latency, cost), negotiated thresholds, regression-on-every-change, demo-gating, SME sign-off ritual, and the feedback artifact back to platform. Quote the 95%-to-ship norm and abstain behavior."),
("Q4. The customer CISO blocks your architecture in week 6. What do you do?",
"A. Model answer: no surprise doctrine (security packet should exist from week 1); diagnose the objection class (residency/IdP/audit); propose constrained variants with trade-off table; escalate with options + recommendation, never with panic; log the miss as a process fix (security-first scoping checklist for next embed)."),
("Q5. How do you hand off so the system survives your departure?",
"A. Model answer: customer-engineer pairing from week 2, runbooks executed by their on-call in a drill, eval ownership transferred with SME review cadence, follow-on change shipped unassisted as exit criteria, expansion proposal tied to measured v1 impact. Success = leverage decreasing over time.")],
"capstones": [
{"name": "Capstone 1 — Bootcamp in a Box: ontology-to-agent delivery on a messy public dataset",
"arch": ("Pick a domain (insurance claims / hospital ops / procurement): model ontology (entities/links) -> ingest messy CSVs/PDFs -> MCP tool server "
"(Module D FDE pattern) with approvals -> agent workflow -> eval acceptance suite (shadow-style golden cases incl. adversarial) -> handoff packet "
"(runbook + security one-pager + expansion proposal). Timed 5-day build log included."),
"stack_rows": [
["Compute", "Python API + minimal UI (Streamlit/Next.js) (Docker Compose)"],
["AI", "Frontier or local LLM + hybrid RAG (Module D) + MCP server (Module D)"],
["Quality", "Eval suite with signed thresholds; regression on every change"],
["Ops", "Audit log + usage funnel proving a workflow changed (simulated users)"],
["Handoff", "Runbook + security packet + roadmap feedback memo"]],
"steps": [
"1. Shadow-simulate: sample 30 real cases; write operator-style notes; draft ontology v0.",
"2. Ship steel thread by day 2 (ugly E2E on real rows) with non-goals log.",
"3. Harden: approvals, PII redaction, audit; security one-pager.",
"4. Build golden eval set (incl. 5 adversarial); gate demos on it.",
"5. Handoff drill: a peer extends one tool unassisted using only your docs.",
"6. Write platform-feedback memo (2 roadmap items with field evidence)."],
"tests": [
"Acceptance test: golden suite >=95% with abstain on ungrounded cases.",
"Handoff test: peer ships follow-on change with zero synchronous help.",
"Security test: red-team probes blocked; audit export complete.",
"Honesty test: build log shows cuts + one failed demo with lesson."]},
{"name": "Capstone 2 — Regulated-Variant Deployment (air-gap/VPC-constrained re-target)",
"arch": ("Re-target Capstone 1 into a constrained topology: private networking, mirrored artifacts (hash-pinned), local/small-model fallback, "
"offline eval runner, SSO-mocked auth, SIEM-format audit export. Decision doc compares open vs constrained variants (cost, latency, residual risk)."),
"stack_rows": [
["Topology", "Compose profiles simulating isolated network + artifact mirror"],
["Models", "Primary API + local fallback with eval-delta report"],
["Security", "Least-privilege service accounts, vaulted secrets, audit export"],
["Quality", "Offline eval runner with identical golden set"],
["Governance", "Waiver/acceptance register with named owners"]],
"steps": [
"1. Map every external call; mirror/pin each artifact with hashes.",
"2. Implement local-model fallback; measure eval + latency deltas honestly.",
"3. Run offline evals; prove parity-or-documented-gap.",
"4. Produce security packet a real CISO could review.",
"5. Demo the go/no-go decision ritual with residual risks named."],
"tests": [
"Isolation test: zero external calls during constrained run (logged).",
"Parity test: eval delta within signed tolerance or explicitly waived.",
"Audit test: SIEM-format export accepted by schema validator."]}],
};

ROLE_GENAI = {
"num": 6, "title": "GenAI / Agentic AI Engineer",
"tagline": "The model-adjacent builder — RAG, agents, inference, and evals at production quality",
"mission": ("Own generative systems from prompt to production: retrieval architectures (hybrid + rerank), agent orchestration "
"(LangGraph/CrewAI/AutoGen/Semantic Kernel/Temporal), inference serving (vLLM/TensorRT-LLM/TGI/Triton/ONNX), structured tool-calling, "
"LLMOps telemetry (LangSmith/Phoenix/TruLens), and eval suites (Ragas + LLM-judge) that decide what ships. You make probabilistic systems behave deterministically enough to bill for."),
"tele_intro": ("Recon: dominant JD vocabulary across 30+ postings — LangChain/LangGraph/LlamaIndex, vector DBs (Pinecone/Qdrant/Milvus/pgvector), "
"vLLM/Triton serving, Bedrock/OpenAI/Vertex, eval + observability. Levels.fyi: AI-engineer median $155K broad / $307K Santa Clara; "
"Senior +14.2%, Staff +18.7% premiums; ML/AI SWE mean ~$246K. Variant titles: LLM Engineer, Applied AI Engineer, Agent Engineer, RAG Engineer, LLMOps Engineer."),
"openings_rows": [
["United States", "~8,000-11,000 active; hubs: SF Bay, Seattle, NYC, Boston, Austin"],
["EMEA", "~3,000-4,500 active; hubs: London, Berlin, Paris, Amsterdam, Zurich"],
["India / APAC", "~6,000-9,000 active; hubs: Bengaluru, Hyderabad, NCR, Pune, Singapore"],
["Global Remote", "~2,000-3,000 active; highest remote share of the 7 (async AI-native startups)"],
["TOTAL (directional, Sep 2026)", "~19,000-27,000 worldwide; largest volume + deepest vendor-keyword churn"]],
"comp_rows": [
["L3 / Mid (2-5 yrs)", "$150K", "$178K", "$215K", "$265K"],
["L4 / Senior (5-8 yrs)", "$185K", "$228K", "$285K", "$360K"],
["L5 / Staff+ (8+ yrs)", "$240K", "$307K", "$400K", "$550K+"]],
"comp_note": ("Sources: Levels.fyi AI-engineer title ($155K median broad; $307K Santa Clara; p90 $300K/$544K); ML/AI SWE mean $246K; "
"Q3-2025 premium curve (Staff +18.7%). Frontier-lab senior/staff skew far above via equity. India mapping: Mid INR 20-38 LPA; "
"Senior INR 38-65 LPA; Staff INR 65 LPA-1.1 Cr+ (AI-native startups pay top-decile cash + equity). Evals + serving depth are the documented pay levers. 1 USD approx 84 INR."),
"top15_rows": [
["Frontier labs", "OpenAI, Anthropic, Cohere, Mistral, xAI (model-adjacent product + eval roles)"],
["Hyperscalers", "AWS (Bedrock), Microsoft (Foundry + AOAI), Google (Vertex + DeepMind applied)"],
["AI-native startups", "Glean, Sierra, Perplexity-class, Harvey/Legora-class vertical, agent-infra (LangChain-class)"],
["Enterprise / GCC", "Banks/retail/health GCC GenAI pods (Bengaluru/Hyderabad), Big-4 AI engineering, data-platform vendors"]],
"exp_bullets": [
("Minimum tenure: ", "2-3 years software engineering with 1+ shipped LLM/RAG/agent system (production users, not notebooks)."),
("Preferred tenure: ", "4-7 years incl. inference-serving ownership (latency/cost SLOs) + eval-suite ownership (release decisions made on your metrics)."),
("Feeder backgrounds: ", "Backend/fullstack -> GenAI (dominant); data/ML -> retrieval + eval lane; DevOps/SRE -> serving + LLMOps lane; IT infra veterans via RAG-capstone + support-copilot proof (viable with evidence)."),
("Education signal: ", "Papers help less than artifacts: eval dashboards, latency reports, red-team finds, cost-per-answer curves. OSS agent/RAG contributions prized.")],
"bound_rows": [
["Data Engineering", "Consume indexed corpora via contracts; own chunking/embedding/index-config for serving quality", "Canonical pipelines, warehouse truth", "Index-version + reindex-SLA contract; never silently fork source truth"],
["ML Research", "Apply/evaluate/serve models; fine-tune with eval-gated discipline", "Pretraining, novel architectures", "Fine-tune only past prompt/RAG ceiling with eval proof"],
["Platform / DevOps", "Serve on paved road; own SLOs, budgets, eval gates for AI services", "Generic platform lifecycle", "AI service ships via platform pipelines with AI-specific gates added"],
["Solutions Architecture", "Build the systems SAs demo; supply eval/cost evidence", "Discovery, deal shaping", "GenAI engineer arms SA with numbers that survive procurement"]],
"artifacts": [
("PR: hybrid retrieval upgrade (BM25 + dense + RRF + cross-encoder rerank) with eval proof",
"Change: replaced pure-dense retriever with Module D hybrid pipeline; context-precision +11 pts, faithfulness +8 pts on frozen golden set; p95 +60ms acknowledged with cache mitigation. Files: retrieval/hybrid.py, evals/golden_v7.json, report. Rollback: index-version flag."),
("Incident post-mortem: token-budget runaway ($18k weekend from a retry loop)",
"Summary: agent retried a failing tool with full-context re-prompts; no budget cap. Fix: per-run token budgets + rate-limiter pattern + context truncation with staleness banners; cost alarms at 70/90%. Eval re-run proving answer parity at capped budgets."),
("Architecture review: agent framework selection (LangGraph vs Temporal-hybrid)",
"Decision: LangGraph for agent reasoning graphs + Temporal for durable business workflows (approvals/timers), bridged by explicit handoff events. Rejected single-framework purity with failure-mode table (recursion loops, timer durability, versioning)."),
("PR: structured-output migration (free-text parsing -> Pydantic tool schemas)",
"Change: all tool args validated via Module D tool-calling pattern; production parse-failure rate 4.1% -> 0.2%; bounded repair pass logged. Validation: 10k-call replay + red-team malformed-arg battery."),
("Eval review artifact: weekly quality board",
"Faithfulness/precision/relevance trends, judge-agreement, cost-per-grounded-answer, top failure clusters with owner + fix. Two blocked releases documented. This board is the GenAI promotion packet.")],
"toolchain": [
("IDEs/editors: ", "Cursor/VS Code + prompt/playground harnesses; LangSmith/Phoenix trace viewers as second IDE."),
("CLI daily drivers: ", "python/uv, docker, kubectl, vllm/tei/triton CLIs, vector-DB CLIs, eval runners (ragas/pytest), promptfoo."),
("Inference runtimes: ", "vLLM, TensorRT-LLM, TGI, Triton, ONNX Runtime; managed fallbacks (Bedrock/AOAI/Vertex)."),
("Telemetry dashboards: ", "LangSmith/Phoenix/TruLens (trace + eval), Prometheus/Grafana (serve SLOs: TTFT/TPOT/GPU), MLflow (experiment + registry).")],
"skills_rows": [
["Core systems & programming", "Python incl. async/typing (Critical); SQL (High); Go/TS as needed (Medium)", "Rust/C++/CUDA (Medium; Triton/TensorRT teams higher)"],
["Inference & serving", "vLLM/TensorRT-LLM/TGI/Triton/ONNX (Critical); KV-cache/quantization basics (High)", "Custom kernels (Emerging; specialized teams)"],
["Agentic & orchestration", "LangGraph/CrewAI/AutoGen/Semantic Kernel/LlamaIndex/Temporal (Critical — 2+ deeply)", "MCP/A2A protocols (Emerging-High)"],
["Vector storage & retrieval", "Qdrant/Milvus/Pinecone/pgvector/Weaviate/OpenSearch (Critical); rerankers (High)", "GraphRAG stores (Emerging)"],
["Cloud AI platforms", "Bedrock+SageMaker / Foundry+AOAI / Vertex (High — one deep)", "Multi-cloud serving (Medium)"],
["LLMOps / telemetry / eval", "LangSmith/Phoenix/TruLens/Ragas/MLflow/Prometheus/OTel (Critical)", "Custom judge calibration (High)"],
["Security & guardrails", "NeMo/Llama Guard/Garak/Promptfoo/OWASP-LLM (High-Critical for user-facing)", "Formal red-team ops (High)"]],
"theory": [
{"h": "T1. Retrieval science: why hybrid + rerank beats pure dense",
"body": ("Dense embeddings capture semantics but miss exact terms (part numbers, names, codes); BM25 captures exact terms but misses paraphrase. "
"Hybrid fuses both via Reciprocal Rank Fusion — rank-based, hence robust to incomparable raw scores — then a cross-encoder reranker scores (query, passage) "
"pairs jointly for precision the bi-encoder cannot afford at scale. Chunking is load-bearing: 300-800 tokens with 10-20% overlap for prose, smaller with "
"structure-aware splits for code/tables; oversized chunks dilute embeddings (lost-in-the-middle starts at retrieval, not just generation). "
"Measure context precision@k and recall separately from answer faithfulness — conflating them hides whether the retriever or the generator failed. "
"Index hygiene: version embeddings with model + chunker, reindex SLA on source change, staleness banners downstream."),
"diagram": "query ──┬──> dense top-25 ──┐\\n       └──> BM25 top-25 ───┴──> RRF fuse ──> top-25 ──> cross-encoder ──> top-k ──> budget-cap ──> prompt"},
{"h": "T2. Attention economics: context windows, KV-cache, and lost-in-the-middle",
"body": ("Transformer attention is quadratic in sequence length; serving systems survive via KV-caching (store key/value states, decode incrementally), "
"paged attention (non-contiguous cache blocks, the vLLM breakthrough), continuous batching (pack many requests per GPU step), and quantization "
"(FP16/BF16 -> INT8/FP8 with eval-verified quality). Lost-in-the-middle (Liu et al., 2023): models overweight prompt edges and underuse the middle — "
"mitigate by ordering passages best-first/best-last, compressing (map-reduce/summarize-then-read), and capping context with explicit budgets instead of "
"stuffing windows. TTFT (time-to-first-token) measures prefill pain; TPOT (time-per-output-token) measures decode health — optimize and SLO them separately. "
"Every context decision is a cost decision: 10x context ~= 10x prefill compute; prove the quality delta justifies it on evals."),
"diagram": "prompt(tokens) ──prefill──> KV-cache ──decode loop──> tokens (TPOT)   │ TTFT = queue + prefill │\\n              └─ paged blocks + continuous batch + quant ─┘"},
{"h": "T3. Agent control theory: plans, tools, memory, and recursion guards",
"body": ("An agent is a loop: perceive (state + tools) -> reason (plan/step) -> act (validated tool call) -> observe -> repeat, with memory (short: scratchpad, "
"long: vector/episodic) and halting rules. Frameworks differ in control placement: LangGraph (explicit state graphs, best debuggability), "
"ReAct-style (flexible, hardest to bound), supervisor/worker (Module D: decomposition + HITL gates), Temporal-backed (durable timers/approvals). "
"Production pathologies: recursion loops (no progress detector), tool-calling drift (malformed args under long contexts — answer: Pydantic schemas + bounded repair), "
"memory poisoning (untrusted content in long memory — answer: provenance + summarization with citations), token runaways (no per-run budget). "
"Design rule: every loop needs max-steps, progress metric, budget cap, and an escalation state a human can resolve."),
"diagram": "goal ──> plan ──> act(validated tool) ──> observe ──checks(budget? progress? risk?)──> done / escalate / next step\\n                                            │ high-risk ──> HITL approval ──> resume"},
{"h": "T4. Evaluation metrology: making probabilistic systems shippable",
"body": ("Evals turn vibes into release decisions. Dimensions: faithfulness (claims supported by context), context precision/recall (retriever quality), "
"answer relevance (question fit), plus safety (policy), latency, and cost per grounded answer. Methods: golden sets (frozen, versioned, shadow-sourced), "
"LLM-as-judge (calibrated against human labels with agreement metrics — uncalibrated judges are random-number generators with confidence), "
"pairwise/regression diffs on every change, and production sampling (async judge on live traffic with human spot audits). Governance: thresholds signed by "
"owners, BLOCK/REVIEW/SHIP verdicts enforced in CI, failure-cluster reviews weekly. The eval suite is the product spec — teams that version it like code ship; teams that don't, demo.")}],
"syllabus_concepts": [
"Transformer + attention mechanics, tokenization/BPE, KV-cache, quantization (GPTQ/AWQ/FP8) trade-offs",
"Embeddings + ANN (HNSW/IVF), BM25, RRF, cross-encoders (MS-MARCO-style), chunking strategies",
"Agent patterns: ReAct, supervisor/worker, plan-and-execute, reflection, memory systems, MCP/A2A tool protocols",
"Serving: vLLM (paged attention, continuous batching), TGI, Triton, TensorRT-LLM, ONNX; TTFT/TPOT SLOs",
"Eval + LLMOps: Ragas dimensions, judge calibration, LangSmith/Phoenix/TruLens, prompt/version management, cost accounting"],
"syllabus_papers": [
"Attention Is All You Need (2017); BERT (2019) — representations lineage",
"RAG (Lewis et al., 2020); REALM/RETRO-class follow-ups — grounding lineage",
"ReAct (Yao et al., 2023); Reflexion (Shinn et al., 2023) — agent loop lineage",
"Lost in the Middle (Liu et al., 2023); PagedAttention/vLLM (Kwon et al., 2023) — context + serving canon",
"Ragas (Es et al., 2023); Judging LLM-as-a-Judge (Zheng et al., 2023) — eval canon; read with calibration skepticism"],
"syllabus_docs": [
"LangGraph + LangSmith, LlamaIndex, CrewAI, AutoGen, Semantic Kernel, Temporal — build one real workflow in two of them",
"vLLM + TGI + Triton + ONNX Runtime serving guides; HuggingFace transformers/generation parameters",
"Qdrant/Milvus/Pinecone/pgvector/Weaviate/OpenSearch vector guides; reranker (Cohere-class/CrossEncoder) docs",
"Bedrock / Azure OpenAI + Foundry / Vertex GenAI docs; Ragas + Promptfoo + Phoenix operation guides"],
"failures": [
("Lost-in-the-middle on stuffed 100k context",
"Answer ignores the key clause buried mid-context. Fix: retrieve-then-rerank tighter, order passages by score at edges, compress, budget-cap; prove on evals."),
("Token-budget runaway from agent retry loop",
"Failing tool retried with full history each time; $18k weekend. Fix: per-run budgets, truncated retries with fresh (not appended) context, cost alarms."),
("Agent recursion loop burns 200 steps doing nothing",
"No progress detection. Fix: max-steps + progress metric (new evidence per N steps?) + escalation state + supervisor pattern."),
("Silent truncation ships ungrounded answers confidently",
"Context cut mid-sentence; model fills gaps fluently. Fix: budget guard with truncation markers, abstain-on-truncation policy for high-stakes answers."),
("Vector index staleness cites revoked policy",
"Source updated, index not. Fix: reindex SLA webhooks, index-version in answers, staleness banners, nightly drift probe."),
("Judge-hacked release: green evals, red users",
"Judge overfit to golden phrasing. Fix: rotating held-out sets, human agreement audits, production sampling with spot review.")],
"ats_keywords": ("LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, LlamaIndex, Temporal, RAG, embeddings, vector database, "
"Pinecone, Qdrant, Milvus, pgvector, Weaviate, OpenSearch, vLLM, TensorRT-LLM, TGI, Triton, ONNX, HuggingFace, PyTorch, "
"Bedrock, SageMaker, Azure OpenAI, Vertex AI, LangSmith, Phoenix, Arize, TruLens, Ragas, MLflow, Prometheus, Pydantic, FastAPI, Python"),
"ats_antipatterns": [
"Notebook-only 'RAG projects' with no eval numbers, no latency/cost data, no production users.",
"Framework alphabet soup (7 orchestrators listed) with zero depth artifact in any one.",
"No mention of evals, budgets, truncation, or failure modes — reads as demo-tier."],
"loop_rows": [
["Recruiter screen (30 min)", "Shipped LLM systems, scale, comp band", "Production users + your release-decision story"],
["Hiring-manager (45-60 min)", "Hardest quality/latency/cost trade-off; blocked release", "Eval-driven judgment, cost ownership"],
["Live coding (60-90 min)", "Hybrid RAG + rerank + budget guard; Pydantic tool schemas", "Retrieval correctness, typing, edge cases"],
["AI system design (60 min)", "Support agent at 1M queries/mo: retrieval, agents, serving, evals, cost", "SLO math, failure modes, unit economics"],
["Behavioral + quality (45 min)", "Judge said ship, users said broken; runaway cost incident", "Intellectual honesty, safety instinct"]],
"interview_qa": [
("Q1. Pure-dense RAG fails on part numbers and SKUs. Redesign retrieval.",
"A. Model answer: add BM25 path, RRF fusion, cross-encoder rerank (Module D hybrid), structure-aware chunking preserving codes, exact-match boost rules, eval split heavy on SKU queries proving precision@k delta; discuss index versioning and reindex SLA so the fix persists."),
("Q2. Code the tool-calling layer so malformed args never execute.",
"A. Model answer: reproduce Module D dispatch: registry of Pydantic schemas, validate-then-execute, bounded single repair (drop nulls, clamp ints), audit log, unknown-tool rejection; test battery: malformed JSON, wrong types, injection-ish strings, oversized payloads."),
("Q3. Your agent loops 200 steps on hard tickets. Fix the control plane.",
"A. Model answer: max-steps + progress metric + per-run token budget + escalation state (supervisor pattern), tool allowlists with risk tiers, HITL on high-impact actions, failure-cluster review feeding golden-set growth; show before/after step histograms."),
("Q4. Size inference for 1M support queries/month within p95 2s and $X budget.",
"A. Model answer: traffic model (peak vs avg) -> vLLM replica math with continuous batching, TTFT/TPOT budgets, cache strategy (prompt + retrieval), quantization with eval-verified parity, managed fallback for spillover, autoscale signals, unit-economics table ($/1k grounded answers) with break-even vs managed APIs."),
("Q5. Evals are green but support agents hallucinate order statuses. Diagnose.",
"A. Model answer: separate retriever vs generator failure (citation coverage first), check truncation/staleness/tool-data freshness, audit judge calibration (agreement vs humans on fresh samples), add production sampling; likely culprits: stale order index, over-truncation, or judge overfit — fix with reindex SLA, budget guards, held-out rotation.")],
"capstones": [
{"name": "Capstone 1 — Production RAG Service with Serving SLOs + Eval Gates",
"arch": ("Corpus (10k+ docs, multi-format) -> versioned indexing (hybrid + rerank) -> vLLM-or-managed serving with TTFT/TPOT tracking -> "
"eval suite (faithfulness/precision/relevance + judge) gating every index/prompt change -> cost board ($/1k grounded answers) -> red-team pack. "
"Load-tested, budget-capped, abstain-capable."),
"stack_rows": [
["Compute", "Python 3.11 API (FastAPI) + worker (Docker); vLLM or managed-LLM switchable backend"],
["Retrieval", "pgvector/Qdrant + BM25 + RRF + cross-encoder (Module D hybrid)"],
["Serving", "Batch scheduler (Module D) + TTFT/TPOT SLO board"],
["Quality", "Eval suite (Module D) enforced in CI; golden set versioned"],
["Safety", "Guardrail middleware (Module D) + red-team battery"]],
"steps": [
"1. Ingest corpus with source hashes; freeze golden Q/A set (150+ incl. adversarial).",
"2. Implement hybrid retrieval; beat pure-dense baseline on precision with proof.",
"3. Serve behind budgeted API (rate-limiter + token budgets); load-test to SLOs.",
"4. Enforce eval gates in CI; demonstrate one blocked bad change.",
"5. Run red-team + cost-optimization passes; publish quality/latency/cost report.",
"6. Demo abstain behavior + staleness banner + audit export."],
"tests": [
"Quality test: faithfulness/precision/relevance >= signed thresholds; regressions block.",
"SLO test: TTFT/TPOT within budget at 3x average load in drill.",
"Safety test: injection/PII battery blocked; ungrounded questions abstain.",
"Cost test: $/1k grounded answers tracked with optimization delta documented."]},
{"name": "Capstone 2 — Supervisor Agent with HITL Approvals on Real Tools",
"arch": ("Supervisor graph (Module D) orchestrating researcher/drafter/verifier workers over real tools (search, ticket, mock payments with approvals) -> "
"audit trail + eval-per-run -> failure-cluster board. Includes runaway-budget + recursion-loop chaos drills with proof of containment."),
"stack_rows": [
["Orchestration", "LangGraph supervisor + Temporal-style durable approvals (or native)"],
["Tools", "Pydantic-validated tool registry (Module D) with risk tiers"],
["Safety", "HITL breakpoints, budgets, escalation states, audit"],
["Quality", "Per-run eval scoring + judge panel on sampled runs"],
["Ops", "Replay harness for incident reproduction"]],
"steps": [
"1. Define 3 workflows (research, ticket-triage, purchase-assist) with risk tiers.",
"2. Implement supervisor + workers with typed state and checkpointing.",
"3. Add HITL + budgets + escalation; chaos-test loop/runaway containment.",
"4. Score 100 runs on quality + cost; publish failure clusters + fixes.",
"5. Record approval-UX demo (reviewer accepts/rejects with rationale)."],
"tests": [
"Containment test: injected loop/runaway always escalates within budget.",
"Safety test: high-risk tools 100% approval-gated in 200 sampled runs.",
"Quality test: task success + grounding >= thresholds with cost per task tracked."]}],
};

ROLE_SOL = {
"num": 7, "title": "AI Solutions Engineer",
"tagline": "The technical closer — discovery to working pilot to production handoff",
"mission": ("Own the technical sale and the pilot that earns production: discovery that finds the valuable problem, scoped demos on the "
"customer's data (never slideware), trial instrumentation proving ROI, security/procurement navigation (questionnaires, DPA, reviews), "
"and handoff to delivery teams with evals, runbooks, and expansion paths. You carry quota-adjacent responsibility with engineering credibility."),
"tele_intro": ("Recon: 30+ postings pattern — pre-sales + post-sales hybrid, RAG/pilot delivery, cloud AI breadth, eval-flavored POCs. "
"Variant titles: Solutions Architect (AI), Sales Engineer (AI), Customer Engineer (AI), Value Engineer (AI). Heavy hiring at AI-native "
"startups (every funding round buys SEs), hyperscalers, data platforms, and GCC solution-centers supporting global sales."),
"openings_rows": [
["United States", "~5,000-7,000 active; hubs: SF, NYC, Chicago, Dallas, Atlanta"],
["EMEA", "~2,200-3,200 active; hubs: London, Dublin, Amsterdam, Frankfurt, Paris"],
["India / APAC", "~3,500-5,000 active; hubs: Bengaluru, NCR, Hyderabad, Singapore, Sydney (follow-the-sun presales)"],
["Global Remote", "~1,000-1,500 active; startup SEs covering global books"],
["TOTAL (directional, Sep 2026)", "~11,500-16,500 worldwide; tracks enterprise AI-spend cycles closely"]],
"comp_rows": [
["SE Mid (2-5 yrs)", "$130K base", "$165K TTC", "$195K TTC", "$230K TTC"],
["SE Senior (5-9 yrs)", "$155K base", "$205K TTC", "$250K TTC", "$310K TTC"],
["SE Staff / Principal (9+ yrs)", "$190K base", "$260K TTC", "$330K TTC", "$420K+ TTC"]],
"comp_note": ("SE comp mixes base + variable (OTE: typically 70/30 or 80/20 base/variable tied to influenced revenue). Table shows base at p25 and "
"TTC (base + variable + equity) at p50+. Sources: 2026 SE salary surveys + Levels.fyi customer-engineering composites. Top-decile startup SEs exceed "
"bands via accelerators. India mapping: Mid INR 18-30 LPA; Senior INR 30-52 LPA; Staff INR 52-85 LPA+. 1 USD approx 84 INR."),
"top15_rows": [
["AI-native sellers", "OpenAI, Anthropic, Cohere, Glean, Harvey/Legora-class verticals (SE = demo-to-pilot engine)"],
["Hyperscalers", "AWS, Microsoft, Google Cloud (customer engineering for Bedrock/Foundry/Vertex)"],
["Data platforms", "Databricks, Snowflake, Pinecone/Elastic, MongoDB (RAG-stack SEs)"],
["Enterprise / GCC / SI", "Global banks/retail/health solution centers; Accenture/Deloitte AI studios; delivery-adjacent SE roles"]],
"exp_bullets": [
("Minimum tenure: ", "2-3 years building software or solutions (support/sales-adjacent welcome) with demo-able artifacts and customer contact."),
("Preferred tenure: ", "4-8 years incl. owned pilots end to end: discovery notes -> working trial -> eval-backed business case -> closed expansion."),
("Feeder backgrounds: ", "Fullstack/backend with demo flair; IT Service Desk/infra veterans with deep troubleshooting + stakeholder trust (strong underrated vector); support/CS engineers going technical; consultants adding code depth."),
("Education signal: ", "Demo portfolio > pedigree: 2 recorded technical demos on real data + one trial-to-close narrative with numbers; cloud certs help procurement credibility.")],
"bound_rows": [
["Data Engineering", "Pilot-scope ingestion (sample connectors, trial schemas)", "Production pipelines, warehouse SLAs", "Pilot proves value on samples; DE scopes production hardening with SE's lineage notes"],
["ML Research", "Translate capabilities into customer language; surface field failure modes", "Model R&D", "SE never promises research futures; carries field evals back honestly"],
["Platform / DevOps", "Trial deploys on paved road; production handoff to delivery/FDE teams", "Platform ownership", "SE hands over evals + runbooks + security packet, not just slides"],
["Solutions Architecture", "Overlaps heavily; SE = quota-adjacent closer, SA = design authority (varies by firm)", "Varies", "Clarify RACI per org in interviews; show both discovery and close evidence"]],
"artifacts": [
("Discovery brief: from vague 'AI for support' to scoped pilot (2-pager)",
"Stakeholders, current workflow timings, data inventory + access path, success metric with baseline (e.g. AHT 6.2 min), non-goals, 3-week trial plan with exit criteria. Shows scoping discipline AEs trust."),
("PR: pilot RAG on customer sample (200 docs) with eval-backed readout",
"Change: trial app (Module D solutions pattern) + golden set from customer phrasing + before/after metrics (deflection, AHT, citation coverage). Readout: ship/iterate/kill recommendation with numbers — including kills (credibility)."),
("Security questionnaire response pack (reused 10+ times)",
"Data-flow diagram, residency/retention answers, subprocessors, pen-test summary, DPA redlines log, SSO/audit evidence. Turnaround <48h. This pack is the SE force-multiplier."),
("Trial instrumentation dashboard + business-case one-pager",
"Usage, task success, AHT/CSAT deltas, $/resolution, projected ARR expansion with sensitivity table. Finance-readable; the artifact that converts pilots to POs."),
("Handoff memo to FDE/delivery (production conversion)",
"Evals, eval-owner, runbooks, security packet, open risks, expansion candidates ranked. No 'throw over wall'; joint first-30-days plan. Measures SE quality by conversion rate.")],
"toolchain": [
("IDEs/editors: ", "VS Code/Cursor for pilot apps; notebook + playground for live discovery demos; Loom/recording for async demos."),
("CLI daily drivers: ", "git/gh, docker, cloud CLIs for trial tenancies, vector-DB CLIs, eval runners, questionnaire-text expanders (your secret weapon)."),
("Inference runtimes: ", "Managed APIs (fastest to pilot) + one self-hosted fallback story for regulated prospects."),
("Telemetry dashboards: ", "Pilot usage + quality boards (LangSmith/Phoenix), trial-guard quota views, business-case calculators.")],
"skills_rows": [
["Core systems & programming", "Python + JS/TS demos (Critical); SQL for discovery data-profiling (High)", "Go/Rust/CUDA (Low)"],
["Inference & serving", "Managed APIs fluency (Critical); basic self-host literacy for objection handling (Medium)", "Deep perf-tuning (Low)"],
["Agentic & orchestration", "LangChain/LlamaIndex + one agent framework demo-ready (High); MCP story (Emerging-High)", "Deep orchestration internals (Low-Medium)"],
["Vector storage & retrieval", "One vector DB demo-deep + RAG eval story (High-Critical)", "Multi-engine depth (Low)"],
["Cloud AI platforms", "Breadth across two hyperscalers + depth in one (High)", "Landing-zone build depth (Low-Medium)"],
["LLMOps / telemetry / eval", "Pilot evals + instrumentation (Critical); LangSmith/Phoenix basics (High)", "Full Ragas ops (Medium)"],
["Security & guardrails", "Questionnaire/DPA fluency + PII story + OWASP-LLM literacy (Critical for close)", "Red-team depth (Medium)"]],
"theory": [
{"h": "T1. Discovery as engineering: MEDDIC-flavored technical qualification",
"body": ("Great SEs disqualify fast. Framework: pain (quantified cost of today), champion (who bleeds), data (access path + quality in week 1?), "
"success metric (one number with baseline), non-goals, competition (status quo + build-in-house + rival), paper process (security/procurement path mapped day 1). "
"Data-profiling in discovery (row counts, PII scan, language mix, staleness) prevents the classic pilot death: week-3 discovery that the corpus is "
"unusable. Write the 2-page brief before writing code — AEs promote SEs whose briefs predict trial outcomes."),
"diagram": "pain($) ──> champion ──> data(access+profile) ──> metric+baseline ──> paper path ──> trial plan (or DISQUALIFY)"},
{"h": "T2. Demo theory: working software on their data, narrated risk-first",
"body": ("Demo hierarchy: live on customer data (best) > live on analog data > recorded > slides (never). Risk-first narration: open with the hard part "
"(their messiest doc, their hardest question) — surviving it earns the right to show the easy parts. Rule of three: three workflows, three minutes each, "
"one metric per workflow. Every claim lands with a verifiable artifact (citation shown, audit row queried live, eval number on screen). Never fake latency "
"(no pre-baked responses without disclosure), never promise roadmap as committed, always end with the trial offer framed as an experiment with exit criteria — "
"pilots framed as purchases stall; pilots framed as experiments with kill clauses sign."),
"diagram": "hardest case first ──> 3 workflows x 3 min ──> artifact per claim ──> experiment-framed trial ask"},
{"h": "T3. Trial economics: instrumentation that converts",
"body": ("Trials fail from unmeasured success. Instrument from day 1: usage (who/which workflows), task success (eval-scored + human spot checks), "
"baseline deltas (AHT, deflection, cycle time with pre-trial baseline captured in writing), cost ($/resolution, projected at scale), and kill triggers "
"(if X not met by week N, we recommend stop). Weekly readout ritual with the champion using the same one-pager format that becomes the business case. "
"Trial guard (Module D): expiry + quota + data-use boundaries enforced in code, not email — expired trials that keep running become security findings. "
"Conversion math: expansion ARR ranked by measured impact, sensitivity-tabled for finance."),
"diagram": "baseline(in writing) ──> instrumented trial ──> weekly readout ──> business case ──> PO or documented kill"},
{"h": "T4. Navigating trust: security reviews, procurement, and production promises",
"body": ("Enterprise deals die in security/procurement, not in demos. Arsenal: pre-built questionnaire pack (data-flow, residency, retention, subprocessors, "
"pen-test, SSO/audit), DPA redline log, reference architecture with private-networking variant, and the honest production speech (what the pilot is NOT: "
"no HA, no full PII review, no scale test — with the priced path to each). Never let the pilot imply production properties it lacks; the handoff memo + "
"joint 30-day plan convert trust into expansion. Track SE quality by pilot conversion rate and time-to-security-approval, not demo count.")}],
"syllabus_concepts": [
"Discovery: MEDDIC/MEDDPICC-lite, stakeholder mapping, data profiling, baseline capture, disqualification discipline",
"Demo engineering: RAG/agent pilots on customer-like data, live-narration craft, objection handling, experiment-framed closes",
"Cloud breadth: two hyperscalers' AI portfolios at demo depth; private-networking + SSO story for regulated buyers",
"Eval literacy: golden sets from customer phrasing, before/after readouts, business-case math (AHT/deflection/ROI)",
"Trust navigation: security questionnaires, DPA basics, residency/retention design, handoff engineering"],
"syllabus_papers": [
"RAG (2020) + ReAct (2023) — enough depth to whiteboard credibly, not to publish",
"Lost in the Middle (2023) — answers 'why did the demo miss that clause?'",
"LLM-as-judge (Zheng et al., 2023) — trial-eval credibility with calibration caveats",
"Technology acceptance / diffusion classics (Davis 1989; Rogers) — pilot-adoption intuition",
"Your top-3 vendors' TCO/ROI whitepapers — steal their calculator formats, verify their assumptions"],
"syllabus_docs": [
"Top-2 hyperscaler AI portfolios (Bedrock/Foundry/Vertex) + one vector DB at demo depth",
"LangChain/LlamaIndex + LangSmith/Phoenix pilot stack; Streamlit/Next.js for trial UIs",
"Sample SIG/CAIQ questionnaire + your filled response pack (build this artifact early)",
"MEDDIC-lite + command-plan templates; Loom/demo-recording craft guides"],
"failures": [
("Slideware pilot that never touches customer data",
"Generic demo impresses, trial on real docs collapses. Fix: data access in week 1 or disqualify; no-data-no-trial rule."),
("Unmeasured trial decays into free consulting",
"No baseline, no kill triggers, 4 months of effort. Fix: written baselines + weekly readouts + trial guard expiry."),
("Roadmap promised as committed, deal dies at delivery",
"SE oversells futures. Fix: committed/roadmap/never trichotomy in writing; AE co-signs."),
("Security ambush kills week-8 close",
"Questionnaire first seen at procurement. Fix: trust packet in week 1, paper-process mapping in discovery."),
("Pilot implies production properties",
"Trial praised, production quote shocks (HA/scale/security costs). Fix: production-pricing preview + handoff memo early."),
("Champion-only selling, economic buyer blindsided",
"Enthusiast loves it, budget owner never met. Fix: multi-thread from discovery; business case in finance language.")],
"ats_keywords": ("solutions engineer, sales engineer, customer engineer, presales, discovery, demo, POC, pilot, RAG, LLM, "
"Python, TypeScript, REST API, AWS, Azure, GCP, vector database, LangChain, stakeholder management, security questionnaire, "
"SOC 2, DPA, SSO, trial, onboarding, enablement, value engineering, MEDDIC, Salesforce, quota, expansion"),
"ats_antipatterns": [
"Pure sales prose with zero built artifacts (no pilot code, no demo recordings, no eval readouts).",
"Pure backend resume with zero customer-facing evidence (no discovery, demos, questionnaires, closes).",
"Claiming 'closed $XM' with no technical mechanism described (what did YOU build/prove?)."],
"loop_rows": [
["Recruiter screen (30 min)", "Technical + customer mix, travel, OTE expectations", "One pilot owned end to end with outcome"],
["Hiring-manager + AE panel (60 min)", "Discovery-to-close narrative; lost deal autopsy", "Disqualification discipline, forecast honesty"],
["Live demo (45-60 min)", "Teach us our product on sample data in 20 min + handle objections", "Narration, risk-first ordering, artifact-per-claim"],
["Technical + security (60 min)", "Whiteboard RAG for a bank; answer mock questionnaire items", "Breadth with honesty boundaries, trust-packet fluency"],
["Behavioral + close (45 min)", "Champion went dark; promised roadmap slipped; trial failing at week 3", "Multi-threading, kill-clause courage, recovery plans"]],
"interview_qa": [
("Q1. Demo our platform on this sample dataset in 20 minutes. Go.",
"A. Model answer: 2-min discovery (who are we solving for, what metric matters), risk-first opening (hardest doc/question live), 3 workflows x 3 min with one metric each, every claim anchored (citation/audit row/eval number shown), close with experiment-framed trial (scope, baselines, exit criteria, dates). Narrate trade-offs; never fake latency or roadmap."),
("Q2. A bank's questionnaire asks about training-data use, residency, and retention. Answer.",
"A. Model answer: no training on customer data (contractual + technical: inference-only paths, logging exclusions), residency matrix (region-pinned processing/storage with private networking option), retention schedule (prompts/logs TTLs, deletion API + attestation), subprocessor list, pen-test cadence, SSO/audit evidence links — then offer the reference architecture call with their security."),
("Q3. Your 3-week trial shows flat AHT at midpoint. What do you do?",
"A. Model answer: diagnose before defending — segment by workflow/user/tenure, check instrumentation (are we measuring the assisted path?), shadow 5 sessions, present findings + one pivot (different workflow slice or UX fix) with revised exit criteria; if structurally flat, recommend kill with learnings — the kill memo that saves the account relationship and your credibility."),
("Q4. Whiteboard a pilot RAG for 200k insurance documents with a path to production.",
"A. Model answer: trial slice (one product line, sampled corpus with PII scan), hybrid retrieval + eval readout plan, trial guard (quota/expiry), security packet week 1, production path priced (HA, reindex SLA, audit SIEM, SSO, DPA) with sensitivity table; handoff memo owners named; expansion candidates ranked by measured trial impact."),
("Q5. Tell us about a deal you lost. What was YOUR failure?",
"A. Model answer: pick a real loss, own the technical contribution (late data profiling, weak champion multi-threading, roadmap overpromise), show the process fix now in your discovery checklist, and the later win the fix enabled. EP-level signal: disqualification stories told proudly.")],
"capstones": [
{"name": "Capstone 1 — Pilot-to-Close Kit: trial app + eval readout + trust packet",
"arch": ("Trial RAG app (Module D solutions pattern) on a public vertical corpus (support docs / policy docs) -> golden set in customer-like phrasing -> "
"instrumented 14-day simulated trial (usage/quality/cost boards) -> business-case one-pager -> filled security questionnaire + DPA checklist -> "
"recorded 20-min risk-first demo + handoff memo. The kit IS the interview portfolio."),
"stack_rows": [
["Compute", "Python trial app + UI (Streamlit/Next.js) (Docker Compose)"],
["AI", "Managed LLM + hybrid RAG (Module D) with citations + abstain"],
["Quality", "Golden evals + weekly-readout generator (same template as business case)"],
["Trust", "Questionnaire pack + data-flow/residency one-pager + trial guard"],
["Evidence", "Recorded demo + discovery brief + kill-memo sample"]],
"steps": [
"1. Write discovery brief for a fictional-but-specific buyer (metric + baseline + paper path).",
"2. Build trial app with guard (quota/expiry) + instrumentation from day 1.",
"3. Freeze golden set; capture baseline; run simulated trial with weekly readouts.",
"4. Produce business case + sensitivity table + kill-memo variant.",
"5. Fill mock security questionnaire with evidence links; record risk-first demo.",
"6. Write handoff memo a real FDE could execute."],
"tests": [
"Realism test: peer plays skeptical buyer in mock discovery + demo; scores you.",
"Conversion test: business case survives finance-style sensitivity grilling.",
"Trust test: questionnaire pack answers 90%+ of a SIG-lite without new writing.",
"Kill test: kill-memo variant is genuinely well-argued, not a strawman."]},
{"name": "Capstone 2 — Objection-Handling Lab (regulated-buyer variant + bake-off win)",
"arch": ("Re-target Capstone 1 for a regulated buyer (bank/health): private-networking variant design, residency matrix, PII-handling proof (redaction "
"battery results), bake-off scorecard (you vs build-in-house vs rival on eval/cost/time-to-value), and exec-summary narrative. Includes recorded 10-min exec readout."),
"stack_rows": [
["Design", "Regulated-variant architecture one-pager + residency matrix"],
["Proof", "PII redaction battery + eval parity report (open vs constrained)"],
["Commercial", "Bake-off scorecard + TCO comparison with cited assumptions"],
["Narrative", "Exec readout (10 min) + AE-ready one-pager"],
["Process", "Multi-threading map (champion/economic/technical/security owners)"]],
"steps": [
"1. Threat-model the trial for a regulated buyer; produce variant design.",
"2. Run redaction + eval batteries; publish parity-or-gap honestly.",
"3. Build bake-off scorecard with winnable, provable differentiators.",
"4. Record exec readout; peer-review with a hostile-finance lens.",
"5. Package AE one-pager + follow-up experiment proposal."],
"tests": [
"Parity test: constrained variant eval within tolerance or gap priced.",
"Scorecard test: every claimed win links to a reproducible artifact.",
"Exec test: 10-min readout holds attention and ends with a dated next step."]}],
};
