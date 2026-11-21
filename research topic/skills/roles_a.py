"""Roles 1-2: AIOps Engineer, Cloud AI Engineer — full Module A-F data."""

ROLE_AIOPS = {
"num": 1, "title": "AIOps Engineer",
"tagline": "AI for IT Operations — turning telemetry firehoses into self-healing systems",
"mission": ("Own the telemetry-to-remediation loop: ingest logs/metrics/traces/events at scale, "
"detect anomalies before customers notice, correlate noise into incidents, and ship safe automated remediation. "
"You are the bridge between SRE/DevOps reality and ML-driven foresight."),
"tele_intro": ("Recon harvested 30+ live postings (Selector, AIOps School, PeopleInAI, Robert Half, Futurense, "
"TechGig Lead AIOps Bangalore 8-12 yrs, EduCativ Senior AIOps 9+ yrs, GE HealthCare Sr Staff AIOps). Demand is strongest "
"in platform/infra teams at hyperscalers, banks, healthcare, and India GCCs modernizing ITSM estates."),
"openings_rows": [
["United States", "~4,500-6,000 active (LinkedIn/Indeed); hubs: Bay Area, Seattle, NYC, Austin, remote-first SaaS"],
["EMEA", "~1,800-2,500 active; hubs: London, Dublin, Amsterdam, Berlin, Warsaw delivery centers"],
["India / APAC", "~3,000-4,500 active; hubs: Bengaluru, Hyderabad, Chennai, Pune, NCR; heavy GCC hiring"],
["Global Remote", "~900-1,400 active; async-first observability vendors + MSPs"],
["TOTAL (directional, Sep 2026)", "~10,000-14,000 worldwide; ~20% YoY growth on AI-assisted ops postings"]],
"comp_rows": [
["L3 / Mid (3-5 yrs)", "$125K", "$148K", "$178K", "$215K"],
["L4 / Senior (5-9 yrs)", "$155K", "$185K", "$225K", "$275K"],
["L5 / Staff / Lead (9+ yrs)", "$195K", "$238K", "$295K", "$360K+"]],
"comp_note": ("Sources: Levels.fyi AI-engineer premium data (Senior AI +14.2%, Staff +18.7% over non-AI peers, Q3 2025); "
"Robert Half 2025 Demand for Skilled Talent (44% report AI/ML skills gap); Futurense India bands. "
"India mapping (GCC/product): Mid 3-5 yrs INR 15-28 LPA; Senior 5-9 yrs INR 28-45 LPA; Staff/Architect INR 30-50 LPA+ "
"at product firms. USD TTC includes base + bonus + annualized equity; GCC India figures are fixed + variable. "
"1 USD approx 84 INR for conversions in this manual."),
"top15_rows": [
["Hyperscalers", "AWS (CloudWatch AIOps), Microsoft Azure (Monitor/Automanage), Google Cloud (Ops Suite)"],
["Observability vendors", "Datadog, Dynatrace, Splunk/Cisco, Elastic, New Relic, ServiceNow ITOM"],
["Enterprise / GCC", "GE HealthCare (Sr Staff AIOps), Bosch, JPMorgan-scale banks, large healthcare + retail GCCs (Bengaluru/Hyderabad)"],
["AI-native / scale-ups", "Moogsoft-type event-correlation startups, BigPanda-type incident platforms, MSP/MSSP automation practices"]],
"exp_bullets": [
("Minimum tenure: ", "3 years in IT operations / SRE / DevOps / NOC with on-call ownership; scripting in production."),
("Preferred tenure: ", "5-9 years with IaC (Terraform), Kubernetes, and one cloud; 2+ years tuning ML-based detection or AIOps platforms (Splunk ITSI, Moogsoft, BigPanda, Datadog Watchdog, Dynatrace Davis)."),
("Feeder backgrounds: ", "IT Service Desk L2/L3 -> NOC -> SRE -> AIOps (strongest vector: you already triage alerts); Infra/Network admin -> Observability; DevOps -> AIOps platform engineering."),
("Education signal: ", "CS/IT degree helps; heavier weight on CKA, AWS/Azure Architect, ITIL + demonstrable on-call post-mortems and automation PRs.")],
"bound_rows": [
["Data Engineering", "Telemetry pipelines (Kafka/OTel/Fluent Bit), schema + retention + cardinality control", "Warehouse modeling, BI marts, batch ETL SLAs", "Shared contract on event schemas; AIOps consumes, DE guarantees delivery"],
["ML Research", "Applied anomaly/time-series models, threshold tuning, eval on incident recall", "Novel architectures, papers, foundation training", "Research consults on model choice; AIOps owns production precision/recall"],
["Platform / DevOps", "Detection-to-remediation wiring, runbook automation, canary gates", "Cluster lifecycle, service scaffolding, release trains", "Joint ownership of rollback gates; AIOps supplies signals, platform actuates"],
["Solutions Architecture", "Internal reliability narratives, cost-of-noise dashboards for leadership", "Pre-sales discovery, customer-facing demos", "AIOps provides MTTR/noise-reduction evidence for SA decks"]],
"artifacts": [
("PR: dedupe PagerDuty storms from flapping K8s readiness probes",
"Problem: 41 pages/week from 3 services flapping on rolling deploys. Change: added OTel-derived flap detector (5-min rolling entropy on probe failures) + deploy-event join so alerts during 10-min post-deploy windows auto-severity-drop to P4 with runbook link. Files: detectors/flap.py, rules/pagerduty.yml, dashboards/flap.json. Validation: replayed 6 weeks of Alertmanager history; pages -73%, missed true-positive 0. Rollback: feature flag DETECT_FLAP."),
("Incident post-mortem: missed disk-pressure cascade on statefulset",
"Summary: anomaly model trained only on CPU/mem missed inode exhaustion on ES data nodes; 2-hr degraded search. Root cause: feature gap + stale runbook threshold (85% from 2019). Fix: added inode + FS-latency features, retrained IsolationForest, added self-heal clear_tmp action behind dry-run for 2 weeks. Action items with owners/dates; eval gate added to CI (replay last 3 incidents must page)."),
("Architecture review: unifying 4 telemetry stacks into one OTel pipeline",
"Decision: collapse Datadog-agent + Fluentd + StatsD into OTel Collector (gateway + agent daemonset), export to Prometheus-remote-write + Loki + Tempo. Trade-offs: short-term dashboard churn vs single cardinality-control point and vendor-neutral retention. Risks: high-cardinality label explosion; mitigation: allowlist processor + drop rules reviewed monthly. Cost: -22% ingest bill projected."),
("PR: self-healing restart for OOMKilled workers behind approval gate",
"Change: anomaly score >0.8 on oom_kill counter triggers open_incident (never auto-restart in prod); score 0.35-0.8 in staging auto-restarts deployment and posts evidence bundle (logs slice, diff of last deploy, detector score). Safety: allowlist-only actions, dry-run flag, audit log to SIEM. Test: chaos-injected OOM in staging; MTTR 14 min -> 3 min."),
("Weekly ops review artifact: alert quality scorecard",
"Table per service: alert volume, % actionable, median acknowledge time, detector precision/recall vs labeled incidents, top-5 noisiest rules with recommended tuning. Outcome: killed 11 rules, retuned 9, noise -38% MoM. This artifact is the AIOps engineer's promotion packet: it proves business impact in MTTR and on-call load.")],
"toolchain": [
("IDEs/editors: ", "VS Code + Remote-SSH into jump hosts; PyCharm for detector work; vim for incident-time triage."),
("CLI daily drivers: ", "kubectl, helm, stern/k9s, jq/yq, rg, gh, terraform, ansible-playbook, promtool, otelcol validate."),
("Inference/runtime: ", "Python 3.11+ services on K8s; models via scikit-learn/ONNX; LLM triage assistants via Bedrock/OpenAI with PII scrubbing sidecar."),
("Telemetry dashboards: ", "Grafana (SLO burn), Kibana/OpenSearch (log forensics), Jaeger/Tempo (trace tail), PagerDuty + ServiceNow (incident lifecycle).")],
"skills_rows": [
["Core systems & programming", "Python (Critical); Go for operators/collectors (High); Bash/PowerShell (Critical); SQL for incident analytics (High)", "Rust eBPF agents (Emerging); CUDA (rare/absent)"],
["Inference & serving", "ONNX Runtime for detector serving (High); Triton for scale-out scoring (High)", "vLLM/TensorRT-LLM only where LLM triage copilots exist (Emerging)"],
["Agentic & orchestration", "Temporal/Airflow for remediation DAGs (High); LangGraph for triage agents (Emerging-High)", "CrewAI/AutoGen (Emerging; rarely production)"],
["Vector storage & retrieval", "OpenSearch/Elastic (Critical for logs); pgvector for runbook search (High)", "Qdrant/Milvus/Pinecone/Weaviate (Emerging; runbook-RAG only)"],
["Cloud AI platforms", "CloudWatch/Azure Monitor/GCP Ops (Critical); Bedrock/OpenAI for summarization (High)", "SageMaker/Vertex custom training (Medium; usually overkill)"],
["LLMOps / telemetry / eval", "Prometheus + OpenTelemetry (Critical); MLflow (High); Ragas-style detector eval (Emerging-High)", "LangSmith/Phoenix/TruLens (Emerging; for triage copilots)"],
["Security & guardrails", "PII scrubbing before model ingest (Critical); RBAC on remediation (Critical)", "NeMo Guardrails/Llama Guard/Garak/Promptfoo (Emerging-High for copilot surfaces)"]],
"theory": [
{"h": "T1. Telemetry geometry: metrics vs logs vs traces vs events",
"body": ("Metrics are sampled numbers with labels (high-cardinality danger: each label-value multiplies series count). "
"Logs are unstructured/semi-structured narratives (cheap to emit, expensive to query). Traces bind the two across service hops "
"with exemplars. Events/changes (deploys, config pushes, autoscale actions) are the highest-leverage join key in AIOps: "
"most 'mystery anomalies' resolve to a change nobody correlated. Canonical pipeline: instrument (OTel SDK) -> collect "
"(agent/gateway) -> process (batch, tail-sample, redact, enrich with kube/cloud metadata) -> route (hot 7-15d, warm 30-90d, cold archive). "
"Cardinality control is the core economic skill: drop/allowlist labels at the collector, aggregate histograms (exponential buckets), "
"and tail-sample traces (head-sample errors + slow traces, drop healthy bulk). A 10x ingest bill almost always traces to one unbounded label "
"(pod id, user id, request id) smuggled into a metric."),
"diagram": "+--------+  OTel SDK   +-----------+  processors  +---------+\\n|  app   | ----------> | collector | -----------> | backends|\\n|  pod   |  m/l/t/events | agent+gw  | batch/sample | Prom/Loki|\\n+--------+             +-----------+ redact/enrich +---------+\\n        \\u2500\\u2500 change feed (deploys) joins here: anomaly x deploy = diagnosis"},
{"h": "T2. Detection mathematics: thresholds vs statistical vs learned detectors",
"body": ("Static thresholds (CPU > 85% for 5m) are interpretable but brittle under seasonality and deploys. Statistical detectors "
"(z-score, EWMA, Holt-Winters/Prophet residuals) model expected bands; alert when residual exceeds k-sigma for N consecutive points. "
"Learned detectors (IsolationForest, autoencoders, LSTM forecasters) catch multivariate drift (inode + latency + error-rate jointly) but need "
"labeled incident history and retraining discipline. Production rule of thumb: thresholds for SLO-burn paging (multiwindow, e.g. 1h/5m burn), "
"statistical for early-warning tickets, learned for correlation/dedup and noise suppression. Always measure detector quality as "
"precision@page (of pages, how many needed humans) and recall@incident (of real incidents, how many paged in time); a detector with 99% accuracy "
"and 10% precision is a pager-spam machine because anomalies are rare-class events."),
"diagram": "signal ──> expected-band model ──> residual ──> persistence(N/m) ──> page/ticket/drop\\n                  ^                         |\\n          deploy/change feed ────────────┘  (suppress or annotate)"},
{"h": "T3. Correlation: from 10,000 events to 1 incident",
"body": ("Naive per-rule alerting scales pages linearly with fleet size. Correlation compresses via: (i) temporal grouping (same 5-15 min window), "
"(ii) topological grouping (same blast radius: cluster/namespace/dependency subgraph from service mesh or CMDB), (iii) causal hints (deploy/change "
"markers, health-check state transitions), (iv) semantic similarity (log-template clustering with Drain/Spell, embedding dedup). "
"DBSCAN over (time, topology-distance, text-similarity) is the workhorse; hierarchy: raw events -> alerts -> correlated incident -> problem record. "
"LLM summarizers sit at the top (incident title + timeline draft), never at the paging decision — the pager path stays deterministic and auditable. "
"Anti-pattern: correlating on free-text message only; hostnames and UUIDs guarantee every event looks unique."),
"diagram": "10k raw events ──temporal+topo cluster──> ~40 alerts ──causal join──> 3 incidents ──LLM──> 1 summary + actions"},
{"h": "T4. Safe remediation: the ladder of autonomy",
"body": ("L0 observe (dashboards only) -> L1 recommend (suggest + link runbook) -> L2 supervised (propose action, human approves) -> "
"L3 scoped-auto (allowlisted actions in non-prod or low-blast-radius) -> L4 conditional-auto (prod actions gated on anomaly bands + change-freeze calendar + error-budget state). "
"Each rung demands stronger guardrails: idempotency keys, dry-run defaults, blast-radius caps (one AZ/10% fleet first), automatic halt on error-budget burn, "
"and full audit to SIEM. The AIOps promotion story is climbing this ladder per action with evidence: dry-run logs -> shadow-mode precision -> supervised approvals -> "
"scoped autonomy with rollback drills. Skip rungs and you ship an outage cannon, not a self-healing system.")}],
"syllabus_concepts": [
"OpenTelemetry (signals, SDKs, Collector pipelines, sampling), PromQL, LogQL, trace tail-sampling",
"Time-series: stationarity, seasonality decomposition, ARIMA/ETS/Prophet, EWMA control charts",
"Anomaly detection: z-score, IsolationForest, autoencoders, DBSCAN/HDBSCAN clustering, log-template mining (Drain)",
"SLO engineering: SLIs, multiwindow burn-rate alerting (Google SRE workbook ch. 5-6)",
"Kubernetes failure modes: OOMKill, CrashLoopBackOff, throttling, noisy neighbors, PDB/disruption budgets",
"Incident command: ICS roles, blameless post-mortems, error budgets, change-freeze policy"],
"syllabus_papers": [
"Google SRE Book + SRE Workbook (burn-rate alerting) — canonical ops theory",
"OpenTelemetry specification (opentelemetry.io/docs/specs) — the telemetry contract",
"Drain: An Online Log Parsing Approach (He et al., 2017) — log-template clustering basis",
"Isolation Forest (Liu et al., 2008) — anomaly baseline every JD implicitly expects",
"Prophet (Taylor & Letham, 2018) — seasonal forecasting for capacity/incident prediction"],
"syllabus_docs": [
"Prometheus alerting + recording rules; Grafana SLO plugin; Alertmanager inhibition/routing trees",
"OTel Collector (receivers/processors/exporters), Prometheus remote-write, Loki, Tempo/Jaeger",
"Splunk ITSI / Moogsoft / BigPanda / Dynatrace Davis / Datadog Watchdog — one enterprise suite deeply",
"Terraform + Ansible + ArgoCD/Flux runbook automation; PagerDuty/ServiceNow ITOM integration guides",
"Python: pandas, scikit-learn, statsmodels, onnxruntime; nbconvert replay harnesses for detector CI"],
"failures": [
("Static-threshold pager storms after deploys",
"Deploy changes the metric baseline (new version is 15% slower for 10 min during warmup); static rules page on the transient. Fix: deploy-event join with auto severity-drop windows + burn-rate paging on user-facing SLIs instead of infra raw metrics."),
("Cardinality explosion bankrupts the telemetry budget",
"One high-cardinality label (container id, request id) turns 50k series into 50M; remote-write stalls, queries time out during the incident you most need them. Fix: collector-side allowlist/drop processors, histogram buckets, cardinality dashboards with CI gate on series growth."),
("Silent truncation: dropped spans hide the failing hop",
"Tail-sampling misconfigured to keep only errors drops the slow-but-successful upstream span that explains queueing. Fix: keep slow-trace tail rules + exemplar links from metrics to traces; verify sampling on game-day."),
("Model drift: detector trained on last quarter's architecture",
"Service split invalidates learned correlations; precision decays silently. Fix: version features with code, monitor detector precision/recall weekly, auto-open retrain ticket on decay, replay-gate in CI over labeled incident corpus."),
("Automation cannon: self-heal amplifies the outage",
"Restart loop on CrashLoopBackOff hammers the image registry and snowballs. Fix: allowlist + per-action rate limits + circuit breaker (halt after 2 failures) + blast-radius staging + mandatory dry-run soak."),
("Log PII leaks into the model vendor",
"Raw logs with emails/tokens shipped to an external LLM summarizer. Fix: collector-side redaction processors (regex + NER), field-level allowlists, VPC endpoints, DPA review; fail-closed on redactor errors.")],
"ats_keywords": ("OpenTelemetry, Prometheus, PromQL, Grafana, ELK/OpenSearch, Jaeger/Tempo, Kubernetes, Terraform, Ansible, "
"Python, anomaly detection, time-series forecasting, alert correlation, noise reduction, root cause analysis, runbook automation, "
"self-healing, SLO/SLI, ITIL, ServiceNow, Splunk ITSI, Moogsoft, BigPanda, Datadog, Dynatrace, AWS/Azure/GCP, Kafka, MLflow"),
"ats_antipatterns": [
"Listing 'AI/ML' with zero on-call, incident, or telemetry evidence — instant reject for senior loops.",
"Only dashboard screenshots, no detector code, replay evals, or MTTR/noise-reduction numbers.",
"'Built a chatbot' as the AIOps headline — signals misunderstanding of the role's ops core."],
"loop_rows": [
["Recruiter screen (30 min)", "Tenure, on-call scope, cloud + K8s depth, salary band", "Concrete paging stories with your action and outcome"],
["Hiring-manager deep dive (45-60 min)", "Biggest outage owned; noisiest alert estate tamed; stakeholder conflict", "MTTR/volume numbers, blameless framing, prioritization logic"],
["Live systems coding (60-90 min)", "Python: parse 10k log lines -> top templates + anomaly flags; PromQL writing", "Streaming discipline, regex/parse correctness, complexity awareness"],
["AI systems design (60 min)", "Design anomaly detection + correlation for 5k-service fleet; cost it", "Cardinality control, eval gates, autonomy ladder, cost math"],
["Behavioral + on-call judgment (45 min)", "Missed page, bad automation, disagreeing with dev on severity", "Ownership, safety instinct, communication under pressure"]],
"interview_qa": [
("Q1. Our Prometheus has 40M active series and queries time out during incidents. Diagnose and fix.",
"A. Model answer: (1) find top cardinality via topk(count by (__name__)({__name__=~\".+\"})) and label cardinality drill-downs; (2) identify offending labels (IDs in labels); (3) move them to exemplars/logs, drop at collector with allowlist processors; (4) convert summaries to histograms, federate or remote-write tier (hot/warm/cold); (5) add CI gate on series growth per PR; (6) short-term: raise retention sharding, add recording rules for hot dashboards. Cite a past series-count reduction with bill impact."),
("Q2. Design alert correlation that turns 10k deploy-time events into one incident.",
"A. Model answer: ingest deploy/change feed as first-class events; group by (15-min window, topology blast radius from mesh/CMDB, log-template cluster); DBSCAN over time+topo+text features; join deploy markers to annotate cause; page once with evidence bundle; LLM only summarizes post-grouping. Eval: replay labeled incident history, report precision@page and recall@incident; rollback via rule versioning + shadow mode first."),
("Q3. Code: from Alertmanager JSON history, compute the 5 noisiest rules and propose tuning.",
"A. Model answer: stream JSONL, key by (alertname, namespace), count firings vs incidents-resolved linkage, compute precision proxy (firing led to ticket/page-with-action), sort by volume x (1-precision); propose per rule: raise for-duration, add inhibition (deploy window), convert to ticket not page, or delete. Discuss O(n) single pass, bounded memory with Counter + heapq.nlargest."),
("Q4. When would you let automation restart production pods unsupervised?",
"A. Model answer: almost never on day one. Ladder: dry-run 2 weeks -> shadow precision measured -> supervised approvals -> scoped autonomy only for allowlisted, idempotent, low-blast-radius actions with rate limits, error-budget halt, change-freeze awareness, and audit. Prod OOM with high anomaly still pages human first. Shows safety maturity hirers screen for."),
("Q5. Your IsolationForest pages perfectly in staging, fires garbage in prod. Why?",
"A. Model answer: train/serve skew (different label sets, scaling, sampling), stale features (architecture changed), contamination mis-set for prod base rate, unlabeled seasonal effects, feedback loop (remediation actions change the distribution). Fix: feature parity checks, versioned features, weekly precision/recall monitoring, retrain tickets on decay, replay-gate in CI.")],
"capstones": [
{"name": "Capstone 1 — K8s Incident Copilot with Scoped Self-Healing (staging autonomy, prod supervised)",
"arch": ("Simulated 20-service K8s fleet (kind/k3d) emitting OTel metrics/logs/traces -> OTel Collector (redact+enrich) -> "
"Prometheus + Loki + Tempo -> detector service (IsolationForest ONNX + burn-rate rules) -> correlation engine (DBSCAN over time/topo/template) -> "
"incident API + Slack/Teams evidence cards -> remediation DAGs (Temporal) with approval gate -> audit to local SIEM file. LLM summarizer optional, post-grouping only."),
"stack_rows": [
["Compute", "k3d cluster + Python 3.11 detector/correlation services on Docker"],
["Telemetry", "OTel Collector, Prometheus, Loki, Tempo, Grafana (SLO burn board)"],
["ML/Retrieval", "scikit-learn -> ONNX Runtime; OpenSearch for log-template + runbook RAG"],
["Orchestration", "Temporal (remediation DAGs), Alertmanager + webhook receiver"],
["Observability of the system", "Detector precision/recall dashboard; replay harness in CI (pytest)"]],
"steps": [
"1. Stand up k3d + OTel Collector with redact processor (drop emails/tokens) and add a chaos script (CPU hog, OOM, deploy flap).",
"2. Train IsolationForest on 2 weeks (simulated 2 days accelerated) of labeled normal data; export ONNX; serve behind FastAPI /score.",
"3. Implement burn-rate paging rules (1h/5m) for two SLIs; wire Alertmanager inhibition on deploy events.",
"4. Build correlation: Drain-style template clustering + DBSCAN grouping; emit one incident per group with evidence bundle.",
"5. Add remediation DAG with dry-run default; promote one action to staging-auto after 50 shadow approvals logged.",
"6. Harden: allowlist, rate limits, audit log; replay-gate in CI over 3 scripted incidents (must page, must not storm).",
"7. Ship scorecard dashboard + post-mortem template; record demo video of chaos -> page -> evidence -> heal."],
"tests": [
"Replay test: 3 labeled incidents -> recall 3/3, pages <= 5 total (no storm).",
"Cardinality test: add pod-id label experimentally -> CI gate fails the PR.",
"Safety test: kill-switch + dry-run flag verified; prod-context action always opens incident, never auto-executes.",
"Drift test: retrain job triggers ticket when weekly precision drops >10 pts."]},
{"name": "Capstone 2 — Telemetry Cost & Quality Platform (the GCC promotion-maker)",
"arch": ("Nightly job scans Prometheus TSDB + Loki index: series cardinality by metric/label, log volume by template, dashboard query cost -> "
"quality report (top-20 waste offenders, suggested drop/aggregate rules, projected savings) -> PR bot proposing Collector processor edits -> "
"human approves -> canary rollout with before/after bill + query-latency comparison."),
"stack_rows": [
["Compute", "Python batch jobs (CronJob on K8s) + Streamlit/Grafana report board"],
["Telemetry", "Prometheus API, Loki API, OTel Collector config-as-code (Git)"],
["Data", "Postgres for nightly snapshots + trend charts"],
["Automation", "GitHub Actions PR bot; ArgoCD rollout of Collector config"],
["Governance", "PII-redaction conformance check per pipeline (fail-closed)"]],
"steps": [
"1. Snapshot cardinality + volume baselines; build top-offender report with dollar attribution.",
"2. Implement rule recommender (drop high-card labels, histogram conversion, retention tiering).",
"3. PR bot opens Collector config change with projected savings + blast-radius note.",
"4. Canary one namespace; compare ingest bytes, query p95, detector precision before/after.",
"5. Add redaction conformance gate (no raw email/API-key patterns in sampled logs).",
"6. Publish monthly savings + noise-reduction scorecard (the artifact hiring managers screenshot)."],
"tests": [
"Savings test: >=20% ingest reduction on canary namespace with zero detector recall loss.",
"Query test: p95 dashboard latency improves or holds flat post-aggregation.",
"Compliance test: 1,000 sampled log lines contain zero unredacted PII patterns."]}],
};

ROLE_CLOUDAI = {
"num": 2, "title": "Cloud AI Engineer",
"tagline": "Ship AI on hyperscaler metal — landing zones, GPU capacity, and managed AI services",
"mission": ("Own AI workloads on AWS/Azure/GCP end to end: landing-zone and IAM design, GPU provisioning and cost control, "
"managed AI services (Bedrock/SageMaker, Azure AI Foundry/OpenAI Service, Vertex AI), inference endpoints with autoscale and canary gates, "
"and the security/compliance envelope (VPC endpoints, KMS, audit) that lets regulated enterprises say yes."),
"tele_intro": ("30+ postings pattern: hyperscaler professional-services + enterprise platform teams + GCC cloud-centers. "
"Every bank, retailer, and healthcare enterprise standing up a 'GenAI platform team' hires this profile. Variant titles: "
"AI Platform Engineer, ML Platform / Cloud ML Engineer, GenAI Infrastructure Engineer."),
"openings_rows": [
["United States", "~6,000-8,500 active; hubs: Seattle, Bay Area, Northern Virginia, NYC, Chicago"],
["EMEA", "~2,500-3,500 active; hubs: London, Dublin, Frankfurt, Amsterdam, Zurich (sovereign-cloud demand)"],
["India / APAC", "~4,500-6,500 active; hubs: Bengaluru, Hyderabad, NCR, Pune, Singapore; GCC platform teams dominant"],
["Global Remote", "~1,200-1,800 active; platform vendors + consultancies"],
["TOTAL (directional, Sep 2026)", "~14,000-20,000 worldwide; largest of the 7 roles by posting volume"]],
"comp_rows": [
["L3 / Mid (3-5 yrs)", "$140K", "$165K", "$198K", "$240K"],
["L4 / Senior (5-9 yrs)", "$170K", "$205K", "$250K", "$310K"],
["L5 / Staff / Principal (9+ yrs)", "$215K", "$265K", "$330K", "$420K+"]],
"comp_note": ("Sources: Levels.fyi ML/AI SWE mean ~$246K TTC (US, 2026); Santa Clara AI-engineer median ~$307K; Senior AI premium +14.2%. "
"India mapping: Mid INR 18-32 LPA; Senior INR 32-55 LPA; Staff/Principal INR 55-90 LPA+ (hyperscaler India + GCC product). "
"Hyperscaler L5+ bands skew higher via equity. FinOps ownership (GPU utilization, commitment coverage) is a documented comp lever."),
"top15_rows": [
["Hyperscalers", "AWS (Bedrock/SageMaker ProServe), Microsoft (Azure AI Foundry), Google Cloud (Vertex AI)"],
["Frontier labs & data platforms", "OpenAI, Anthropic (delivery-adjacent), Databricks, Snowflake, MongoDB Atlas"],
["Enterprise / GCC", "JPMorgan-scale banks, UnitedHealth-scale payers, global retailers, automotive + manufacturing GCCs"],
["Vendors & SIs", "Accenture/Avanade/Deloitte AI practices, HashiCorp-ecosystem platform shops, GPU-cloud neoclouds (CoreWeave-class)"]],
"exp_bullets": [
("Minimum tenure: ", "3-4 years in cloud engineering/DevOps/SRE with Terraform + containers + one hyperscaler deep (IAM/VPC/KMS)."),
("Preferred tenure: ", "5-8 years incl. 2+ years running ML/AI workloads: endpoints, batch inference, GPU scheduling, model registries, feature stores."),
("Feeder backgrounds: ", "DevOps/SRE -> Cloud AI (most common); backend/fullstack with AWS depth -> platform AI; data engineering -> MLOps-flavored Cloud AI; IT infra virtualization -> cloud networking/security lane."),
("Education signal: ", "AWS Solutions Architect Pro / Azure Expert / GCP Professional Cloud Architect + CKA; security specialty certs prized for regulated-sector roles.")],
"bound_rows": [
["Data Engineering", "Serving + endpoint + capacity + inference cost; feature-store consumption contracts", "Pipeline authoring, warehouse modeling, data-quality SLAs", "Joint latency/cost SLOs; DE owns freshness, Cloud AI owns serving"],
["ML Research", "Managed training clusters, experiment infra, eval harnesses at scale", "Model architecture, training recipes, papers", "Self-serve training platform with quotas; research files tickets, platform ships capacity"],
["Platform / DevOps", "AI-specific platform (registries, endpoints, GPU pools, policy packs)", "Generic CI/CD, cluster lifecycle, service scaffolding", "Cloud AI extends platform with AI modules; shared IaC standards"],
["Solutions Architecture", "Reference architectures, landing zones, cost models leadership trusts", "Deal-stage discovery and demos", "Cloud AI builds the paved road SAs prescribe"]],
"artifacts": [
("PR: Bedrock knowledge-base endpoint behind VPC + PrivateLink with token-budget guard",
"Change: Terraform module for Bedrock agent + OpenSearch Serverless vector store in workload VPC; SCP denies public endpoints; per-tenant token-budget Lambda (see rate-limiter pattern) with CloudWatch alarms at 70/90%. Validation: cfn-nag + Checkov clean,探针 chaos: quota-exhaustion drill pages FinOps. Cost: graviton-backed embeddings cut 31%."),
("Incident post-mortem: GPU node preemption cascade during scale-out",
"Summary: spot-based training pool preempted during AZ rebalance; checkpointing gap lost 6 hrs. Root cause: no checkpoint-on-preempt hook + single-AZ node group. Fix: multi-AZ placement, checkpoint callback every N steps to S3, on-demand base capacity for serving pool. Added GPU-utilization vs commitment-coverage dashboard."),
("Architecture review: SageMaker vs Bedrock vs self-hosted vLLM on EKS",
"Decision matrix scored on latency p99, data-residency, unit economics at 3 load tiers, and ops burden. Outcome: Bedrock for standard RAG tenants, EKS+vLLM for latency-critical tenant, SageMaker training for fine-tunes. Document includes break-even math per 1M tokens and exit plan per option."),
("PR: canary promotion gates for endpoint config change",
"Change: CodePipeline stage shifting 5% -> 25% -> 100% with automatic rollback on 5xx >1% or p99 >900ms (mirrors deploy_canary pattern in Module D). Evidence: 3 prior bad configs would have been caught. Rollback drill recorded."),
("FinOps review artifact: inference unit-economics one-pager",
"Per-tenant $/1k requests, GPU util heatmap, commitment coverage, idle-endpoint reaper savings. Outcome: reaped 17 idle endpoints (-$41k/mo), rightsized 2 GPU pools. This artifact differentiates Cloud AI from generic DevOps hires.")],
"toolchain": [
("IDEs/editors: ", "VS Code + AWS/Azure/GCP toolkits; JetBrains for platform service code; CloudShell for incident triage."),
("CLI daily drivers: ", "aws/cdk, az/bicep, gcloud, terraform/tofu, kubectl, helm, sagemaker-sdk, bedrock-agentcore CLIs, finops exporters (Kubecost)."),
("Inference runtimes: ", "Bedrock, SageMaker endpoints, Azure OpenAI Service + AI Foundry, Vertex AI Prediction/GenAI, EKS+vLLM/Triton for escape-hatch tenants."),
("Telemetry dashboards: ", "CloudWatch/CloudTrail, Azure Monitor/App Insights, GCP Ops Suite, Prometheus+Grafana for EKS pools, Cost Explorer/Budgets + Kubecost.")],
"skills_rows": [
["Core systems & programming", "Python + IaC (Terraform/Bicep/CDK) (Critical); Go for operators (High); SQL (High)", "Rust/C++/CUDA (Low except GPU-kernel-adjacent teams)"],
["Inference & serving", "Triton, TGI, ONNX Runtime on managed endpoints (High); vLLM on EKS/GKE (High)", "TensorRT-LLM perf-tuning (Emerging-High for latency-critical tenants)"],
["Agentic & orchestration", "Step Functions/Durable Functions/Workflows + Temporal (High); Bedrock Agents/Foundry agents (High)", "LangGraph/CrewAI/AutoGen hosted on cloud run (Emerging)"],
["Vector storage & retrieval", "OpenSearch Serverless, pgvector (RDS/AlloyDB), Pinecone-managed (Critical-High)", "Milvus/Weaviate self-hosted (Medium; data-residency cases)"],
["Cloud AI platforms", "Bedrock+SageMaker / AI Foundry+AOAI / Vertex AI (Critical — pick one deep, one working)", "Cross-cloud policy (SCP/Azure Policy/Org Policy) (High)"],
["LLMOps / telemetry / eval", "CloudWatch/Azure Monitor/GCP Ops + OpenTelemetry (Critical); MLflow/SageMaker Experiments (High)", "LangSmith/Phoenix/Ragas gates in pipeline (Emerging-High)"],
["Security & guardrails", "IAM least-privilege, VPC endpoints, KMS, PrivateLink, audit (Critical)", "Guardrails-for-Bedrock / Content Safety / Model Armor + Garak scans (High)"]],
"theory": [
{"h": "T1. Landing zones: the substrate every AI workload inherits",
"body": ("A landing zone is the pre-approved cloud foundation: org hierarchy + SCPs/guardrails, identity (SSO, workload identity federation), "
"networking (hub-spoke/VPC-SC, PrivateLink/Private Endpoint, egress control), logging (CloudTrail/Activity Log/Audit Logs to immutable bucket), "
"KMS strategy (CMEK per data class), and FinOps tagging. AI workloads add: data-residency boundaries (which region may see prompts), "
"model-invocation audit (who called what with which data class), and GPU quota/placement strategy. Get the zone wrong and every later AI "
"decision is either non-compliant or unshippable; get it right and onboarding a new tenant is a module instantiation, not a 6-week review. "
"Know the failure asymmetry: network/KMS mistakes surface at 2 a.m. during the customer demo, not at plan time."),
"diagram": "org-policy(SCP) ──> workload VPC ──PrivateLink──> Bedrock/AOAI/Vertex\\n      │                      │                       │\\n     SSO/OIDC            KMS(CMEK)              audit log ──> SIEM"},
{"h": "T2. Inference economics: managed APIs vs managed endpoints vs self-hosted",
"body": ("Three cost curves cross at different volumes. Managed APIs ($/token) win at spiky/low volume with zero ops burden but fixed margins and "
"data-plane terms to review. Managed endpoints ($/instance-hour + autoscale lag) win at steady mid-volume with compliance-friendly VPC placement. "
"Self-hosted vLLM/Triton on GPU nodes ($/GPU-hour + your on-call) wins at sustained high volume or exotic latency needs, IF utilization stays >60% "
"and you staff the pager. Break-even math per tenant: monthly_tokens x blended $/token vs endpoint_hours x $/hr + autoscale waste + eng hours. "
"Autoscale lag (5-15 min cold) forces overprovisioning for spiky traffic — provisioned-throughput/reserved-capacity purchases hedge this. "
"Always instrument $/1k grounded answers (not raw tokens) so quality regressions cannot hide inside cost wins."),
"diagram": "cost ── API line (steep slope, zero intercept) ──╲\\n                                    ╲── endpoint (flat+steps) ──╲── self-host (high fixed, flat slope)\\n volume ──────────────────────────────>  (crossovers = your migration triggers)"},
{"h": "T3. GPU scheduling and capacity: quotas, placement, preemption",
"body": ("GPUs are the constrained resource: regional quotas, per-family limits, spot-vs-ondemand mix, placement groups for NVLink locality, "
"and nodeSelectors/taints (nvidia.com/gpu) with time-slicing or MIG partitioning for sharing. Training tolerates preemption with checkpointing; "
"serving does not — serving pools stay on-demand/reserved across AZs while training scavenges spot. Know the failure modes: driver/CUDA version skew "
"between image and host, GPU memory fragmentation under long contexts (paged-attention mitigations), NCCL collective hangs across AZs. "
"Capacity planning artifact: P50/P99 token forecast -> GPU-hours at target utilization -> quota request filed 4-8 weeks before launch (quotas are the real lead time)."),
"diagram": "[serve pool: on-demand, multi-AZ, autoscale]   [train pool: spot, checkpoint->S3, preempt-hook]\\n                    \\u2191 autoscaler (custom metric: queue depth / tokens-per-min)"},
{"h": "T4. Private AI networking: keeping prompts off the public internet",
"body": ("Regulated tenants require prompts/embeddings to traverse private paths: VPC endpoints/PrivateLink to Bedrock/AOAI/Vertex, "
"egress firewalls (no 0.0.0.0/0 from inference subnets), Customer-Managed Keys for model I/O logs, and audit of every invocation "
"(identity, data class, token counts, grounding sources). VPC Service Controls / Azure Private DNS zones scope the blast radius; "
"service perimeter violations must alert, not just log. Test the negative: chaos-test DNS exfiltration and endpoint-policy bypass in staging; "
"a perimeter that has never been attacked in drill is a slide, not a control.")}],
"syllabus_concepts": [
"Hyperscaler IAM (roles/instance identity, OIDC federation, ABAC), org policy/SCP design, KMS envelope encryption",
"VPC design (hub-spoke, PrivateLink/endpoints, transit, DNS), WAF/API Gateway throttling + caching",
"Containers + GPUs on cloud: EKS/AKS/GKE GPU node groups, device plugins, MIG/time-slicing, Karpenter/cluster-autoscaler",
"Inference serving: autoscaling signals (concurrency, queue depth, GPU util), canary/shadow deploys, provisioned throughput",
"FinOps: tagging strategy, commitment coverage, rightsizing, idle reaping, showback per tenant"],
"syllabus_papers": [
"Attention Is All You Need (Vaswani et al., 2017) — know the cost object you are serving",
"vLLM / PagedAttention (Kwon et al., 2023) — why GPU memory economics work the way they do",
"Billion-scale similarity search / FAISS (Johnson et al., 2019) — vector-retrieval cost intuition",
"Google SRE Workbook ch. on autoscaling + load balancing — managed-endpoint mental model",
"NIST SP 800-53 / CSA CCM mappings for your sector — compliance vocabulary for design docs"],
"syllabus_docs": [
"AWS: Bedrock + Agents, SageMaker endpoints + Pipelines, EKS GPU guides, Well-Architected ML Lens",
"Azure: AI Foundry + Azure OpenAI Service, AKS GPU, Private Link/DNS, Policy/Defender for Cloud",
"GCP: Vertex AI (Prediction + Vector Search + Agents), GKE autopilot GPUs, VPC-SC, Model Armor",
"Terraform/AWS CDK/Bicep module registries; Checkov/cfn-nag/Conftest policy gates; Kubecost docs"],
"failures": [
("Autoscale-lag outage during launch spike",
"Endpoint scales in 10 minutes, traffic doubles in 60 seconds; cold pool 503s. Fix: provisioned/reserved headroom for launch windows, predictive scaling on queue depth, load-shedding with graceful degradation message, game-day spike test."),
("Quota wall blocks the release train",
"New region, no GPU quota approved; launch slips 6 weeks. Fix: quota requests at design-gate, multi-region fallback matrix, quota-utilization dashboard with 60-day forecast alerts."),
("Cross-AZ NCCL hangs triple training time",
"Collective comms across AZs stall on large all-reduces. Fix: placement groups/single-AZ training, EFA/RDMA fabrics where available, NCCL debug + timeout budgets, checkpoint frequently."),
("Prompt logs with PII land in a public-bucket-adjacent store",
"Invocation logging shipped raw prompts to a broadly-readable bucket. Fix: CMEK + tight bucket policy, field-level redaction before logging, access reviews, DPA-aligned retention."),
("Idle endpoints silently burn $40k/month",
"Experiment endpoints never reaped. Fix: idle-reaper (no traffic 14d -> snapshot + stop), mandatory TTL tags, FinOps showback to owner with auto-nag."),
("Vendor data-plane surprise during incident",
"Managed model behavior changed under you with no diff. Fix: pinned model versions, eval-gate in pipeline, dual-vendor fallback for critical paths, contractual change-notice terms.")],
"ats_keywords": ("AWS Bedrock, SageMaker, Azure AI Foundry, Azure OpenAI, Vertex AI, EKS/AKS/GKE, Terraform, Bicep, CDK, "
"IAM, VPC, PrivateLink, KMS, GPU, vLLM, Triton, autoscaling, canary, FinOps, Kubecost, CloudWatch, Azure Monitor, "
"Prometheus, Grafana, MLflow, model registry, feature store, Docker, Kubernetes, Python, Go"),
"ats_antipatterns": [
"'Multi-cloud expert' with no depth artifact (landing-zone module, quota plan, cost model) in any one cloud.",
"ML buzzwords with zero IaC, networking, or incident evidence — Cloud AI is an ops role first.",
"No cost numbers anywhere: no GPU util, no $/request, no savings story."],
"loop_rows": [
["Recruiter screen (30 min)", "Cloud depth (which services, what scale), certs, comp band", "Named services + scale + incident you owned"],
["Hiring-manager (45-60 min)", "Landing zone you built; hardest quota/cost fight; regulated tenant story", "Trade-off reasoning, compliance fluency, FinOps ownership"],
["Live IaC + coding (60-90 min)", "Terraform module review (find IAM/VPC flaws); Python endpoint health-gate", "Least-privilege instinct, test coverage, rollback thinking"],
["AI systems design (60 min)", "Multi-tenant RAG platform for a bank: regions, keys, endpoints, eval gates", "Data-plane privacy, cost tiers, failure domains, exit plan"],
["Behavioral + FinOps (45 min)", "Cut inference spend 30% without quality loss; missed quota deadline", "Unit economics, stakeholder management, forecasting discipline"]],
"interview_qa": [
("Q1. Design a multi-tenant RAG platform for a regulated bank on AWS.",
"A. Model answer: workload VPC per data class with PrivateLink to Bedrock + OpenSearch Serverless; CMEK everywhere; SCPs denying public resources; per-tenant token budgets (rate-limiter pattern) with 70/90% alarms; Bedrock Guardrails + PII redaction pre-ingest; eval gate (faithfulness>=0.7) blocking index promotion; dual-region pilot with data-residency matrix; FinOps showback per tenant; pinned model versions + fallback tenant pool."),
("Q2. Your SageMaker endpoint p99 triples at 3x traffic. Walk the debug.",
"A. Model answer: check autoscale lag vs traffic slope (CloudWatch invocations vs instance count), GPU util + queue depth custom metrics, model-server worker count/threads, payload size growth (context bloat), downstream vector-DB latency, AZ imbalance; mitigations: provisioned headroom, smaller instance fleet with higher concurrency, response caching, request hedging, context-budget caps; verify with staged load test."),
("Q3. Terraform review: find the security flaws in this Bedrock module.",
"A. Model answer: look for wildcard IAM (* actions/resources), public subnets for endpoints, missing VPC endpoints (traffic leaves VPC), unencrypted stores (no CMEK), missing access logging, overly broad security groups, no deletion protection/backup, hardcoded secrets. State least-privilege rewrite for each finding."),
("Q4. How do you cut inference spend 30% without hurting quality?",
"A. Model answer: measure $/1k grounded answers baseline; levers: prompt compression + context caps, embedding dim/caching, smaller reranker, provisioned-throughput for steady load, idle reaping, graviton/ARM for CPU stages, spot for batch evals, per-tenant budgets to kill abuse; re-run eval suite after each lever — ship only Pareto-safe cuts. Cite prior savings with eval deltas."),
("Q5. Code: implement the canary gate for an endpoint config rollout.",
"A. Model answer: reproduce deploy_canary (Module D): staged weights, soak, error-rate + p99 gates from metrics_fn, auto-rollback on breach, audit record; discuss choosing budgets from SLOs, soak duration from deploy frequency, and why rollback must be a single tested command.")],
"capstones": [
{"name": "Capstone 1 — Private Multi-Tenant RAG Platform (Bedrock/Vertex + IaC + eval gates)",
"arch": ("Terraform landing-zone module (VPC, endpoints, KMS, SCPs, logging) -> per-tenant RAG stack (managed LLM + serverless vector store + "
"token-budget service) -> ingestion pipeline (redact -> chunk -> embed -> index with eval gate) -> canary endpoint promotion -> FinOps + audit dashboards. "
"Second-region design doc (no build) with residency matrix."),
"stack_rows": [
["Compute", "Managed LLM APIs + containers for ingestion/budget services (ECS/Cloud Run/EKS)"],
["Serving", "Bedrock/AOAI/Vertex + serverless vector store (OpenSearch/pgvector)"],
["IaC", "Terraform modules + Checkov/Conftest gates in CI"],
["Observability", "Cloud-native monitor + Prometheus/Grafana for custom $/quality metrics"],
["Quality", "Eval suite gate (faithfulness/precision/relevance) blocking promotion"]],
"steps": [
"1. Scaffold landing-zone module with private endpoints, CMEK, audit logging; pass policy scanners clean.",
"2. Deploy per-tenant RAG with token budgets + PII redaction; load a 5k-doc corpus.",
"3. Implement ingestion eval gate: new index version promotes only on metric thresholds.",
"4. Add canary endpoint promotion with auto-rollback; run a bad-config drill proving rollback.",
"5. Build FinOps board ($/1k answers per tenant) + reap one idle resource class.",
"6. Write residency + exit-plan doc (second region/vendor) with break-even math.",
"7. Demo: red-team probe blocked, quota spike absorbed, audit trail export."],
"tests": [
"Policy test: scanners clean; negative test (public bucket attempt) denied by SCP.",
"Eval test: poisoned corpus version fails the gate and never promotes.",
"Resilience test: traffic spike handled within SLO via headroom + autoscale; rollback drill <10 min.",
"Cost test: idle-reaper + budget alarms demonstrably cut sandbox spend."]},
{"name": "Capstone 2 — GPU Pool Rightsizing + Commitment Strategy (the FinOps portfolio piece)",
"arch": ("Exporters scrape GPU util, queue depth, quota usage across pools -> nightly analyzer recommends instance-type moves, "
"spot/on-demand mix, and commitment purchases -> human-approved Terraform PRs -> before/after unit-economics report."),
"stack_rows": [
["Compute", "EKS/GKE GPU pools (mixed on-demand + spot) + analyzer CronJob"],
["Data", "Prometheus + cost-export tables (Athena/BigQuery) + Postgres recommendations log"],
["Automation", "GitHub Actions PR bot; ArgoCD/Flux rollout"],
["Dashboards", "Grafana GPU-util heatmap + commitment-coverage + forecast"],
["Governance", "Change-freeze calendar + error-budget halt wired into applier"]],
"steps": [
"1. Instrument GPU util + queue depth + quota consumption; baseline 2 weeks.",
"2. Build break-even model (managed vs endpoint vs self-host per tenant tier).",
"3. Recommend mix shifts; simulate savings on history before touching infra.",
"4. Execute one pool move via PR with canary + rollback plan.",
"5. Purchase/adjust one commitment based on P50 forecast; document the bet.",
"6. Publish monthly one-pager leadership actually reads."],
"tests": [
"Forecast test: quota-exhaustion predicted >=14 days ahead on synthetic growth.",
"Savings test: unit cost per 1k answers down >=15% with eval metrics flat-or-better.",
"Safety test: preemption drill loses zero serving traffic; training resumes from checkpoint."]}],
};
