"""Parts V–VIII: agents, production, cloud, FDE/enterprise."""


def part5(b):
    b.page_break()
    b.h1("Part V — Agentic AI")
    b.h2("29. Foundations: workflow vs agent")
    b.table(
        ["Thing", "Who chooses the next step", "When to use"],
        [
            ["Deterministic workflow", "Your code", "Known DAG, compliance, payments"],
            ["Agentic workflow", "Code with LLM-chosen branches at named points", "Most enterprise ‘agents’"],
            ["Autonomous agent", "The model, looping until a stop condition", "Open-ended research with tight tool sandbox"],
            ["Multi-agent", "A supervisor or protocol", "Heterogeneous skills, not for show"],
        ],
        col_widths=[2340, 3510, 3510],
    )
    b.p(
        "Agents are inappropriate when the action is high-risk, the state machine is already known, latency is tight, or you cannot evaluate success. A router plus three tools is often better than a ‘crew.’"
    )
    b.h2("30. The agent loop and failure points")
    b.p(
        "Input → understand → plan → choose tool → execute → observe → update state → validate → continue or stop."
    )
    b.table(
        ["Step", "Typical failure", "Control"],
        [
            ["Understand", "Wrong user goal", "Clarify; structured intake"],
            ["Plan", "Infinite plan, too many steps", "Max steps, critic, plan schema"],
            ["Choose tool", "Wrong tool / hallucinated tool", "Strict enum of tools"],
            ["Execute", "Side effects, timeouts", "Sandbox, idempotency, HITL"],
            ["Observe", "Huge tool dump blows context", "Summarize, schema, truncate"],
            ["Validate", "‘Looks good’ from the same model", "Independent checks, tests, policy engine"],
            ["Stop", "Never stops", "Hard caps, budget, watchdog"],
        ],
        col_widths=[1800, 3780, 3780],
    )
    b.h2("31. Agent patterns")
    b.table(
        ["Pattern", "Idea", "Production note"],
        [
            ["ReAct", "Interleave thought, act, observe", "Good default; log thoughts privately"],
            ["Router", "Classify then dispatch", "Cheap, evaluable, underrated"],
            ["Plan-and-Execute", "Plan once, execute steps", "Needs replan on failure"],
            ["Orchestrator-worker", "Supervisor delegates", "Clear traces; watch ping-pong"],
            ["Sequential / parallel", "Fixed or fan-out graph", "Prefer for known work"],
            ["Hierarchical", "Managers of managers", "Complexity tax"],
            ["Evaluator-optimizer", "Generate then critic", "Cost 2×; use on final answers"],
            ["HITL / approval-gated", "Human signs high-risk tools", "Default for write actions"],
        ],
        col_widths=[2340, 3510, 3510],
    )
    b.code(
        """# Pseudocode: approval-gated tool node (LangGraph-style)
def tool_node(state):
    call = state["pending_call"]
    if call.name in WRITE_TOOLS and not state.get("approved"):
        return {"interrupt": {"type": "approval", "call": call}}
    result = run_tool(call)  # idempotent
    return {"observations": state["observations"] + [result]}""",
        caption="Figure 31-1. Deterministic gate around a probabilistic chooser.",
    )
    b.h2("32. State, memory, tools")
    b.p(
        "Prefer an explicit state schema (TypedDict/Pydantic) checkpointed to Postgres. Short-term memory is the state + recent messages. Long-term semantic memory is retrieval with TTL and user scope. Episodic memory is traces. Procedural memory is your code and prompts, not a vector of ‘how we do refunds.’ Forgetting is a feature: stale memories cause policy violations."
    )
    b.p(
        "Tool calling: JSON schema, server-side validation, allowlists, parallel vs sequential, timeouts, argument canonicalization, audit logs, and user confirmation for writes. Never let the model invent an endpoint URL."
    )
    b.h2("33. Agent frameworks (learn two deeply)")
    b.table(
        ["Framework", "Strength", "Weakness", "Production fit", "Learn?"],
        [
            ["LangGraph", "Durable graphs, HITL, mix deterministic+LLM", "API surface to learn", "High", "Deep (pick this)"],
            ["OpenAI Agents SDK / Agents API", "Native tools, MCP, sandboxes, sessions", "Vendor lock-in", "High if you are all-in OpenAI", "Deep if targeting OpenAI/FDE"],
            ["Google ADK", "Multi-language, context mgmt, Vertex deploy, graphs in 2.0", "Google-centric ops", "High on GCP", "Deep if targeting Google"],
            ["LlamaIndex", "Data/RAG superpower", "Less general orchestration", "High for knowledge apps", "P1 for RAG"],
            ["PydanticAI", "Pythonic, typed", "Younger ecosystem", "Good for API-centric apps", "P2"],
            ["Semantic Kernel / MSFT Agent Framework", ".NET/enterprise Microsoft shops", "Split mindshare", "High on Azure", "Literacy + deep if Azure FDE"],
            ["CrewAI", "Fast multi-agent demos", "Easy to overfit to hype", "Cautious", "Literacy only"],
            ["AutoGen", "Multi-agent research pedigree", "Moving platform", "Selective", "Literacy"],
            ["LangChain (classic chains)", "Integrations", "Too much magic for control", "Use as I/O library", "Don’t build identity on LCEL chains"],
        ],
        col_widths=[2000, 2200, 1800, 1680, 1680],
    )
    b.must(
        [
            "Recommendation: LangGraph deeply + one vendor SDK (OpenAI Agents or Google ADK) based on your target employers.",
            "If interviewing at Microsoft-heavy India GCCs, add Semantic Kernel / Azure AI Foundry literacy.",
            "Do not list five frameworks on a resume with no production traces.",
        ]
    )
    b.h2("34. MCP — Model Context Protocol")
    b.p(
        "MCP is an open protocol to connect LLM applications to tools, resources, and prompts. Latest specification version as of this research: 2026-07-28 (current). Official docs: modelcontextprotocol.io. SDKs: TypeScript, Python, C#, Go, Rust are Tier 1."
    )
    b.p(
        "Architecture: Host (the LLM app) creates Clients; Servers expose capabilities. JSON-RPC 2.0. Server features: resources, prompts, tools. Client features (older mental model): sampling, roots, elicitation. The 2026-07-28 revision is the largest since launch: the core is now stateless. Handshake initialize/initialized and Mcp-Session-Id were removed. Each request carries protocol version and client capabilities in _meta. Servers MUST implement server/discover. List results are cacheable. Multi Round-Trip Requests (MRTR) replace always-on bidirectional streams for elicitation. Tasks moved to an official extension. Authorization is closer to OAuth/OIDC. Gateways can route on Mcp-Method and Mcp-Name headers."
    )
    b.table(
        ["Build", "What to implement", "Security bar"],
        [
            ["Simple MCP server", "One tool, stdio or Streamable HTTP, discover", "No secrets in resources"],
            ["Database MCP", "Read-only SQL with bind params, row limits", "Identity of caller; never interpolate SQL"],
            ["Enterprise API MCP", "Wrap a real business API", "OAuth, allowlist, audit, rate limit"],
            ["Authenticated MCP", "Token passthrough or on-behalf-of", "Confused deputy, audience checks, no token in logs"],
        ],
        col_widths=[2200, 3580, 3580],
    )
    b.warn(
        [
            "MCP tool descriptions are untrusted unless the server is trusted. Tool poisoning and prompt injection via resources are first-class threats (OWASP Agentic supply chain; LLM01).",
            "Do not run arbitrary community MCP servers with production credentials.",
        ]
    )
    b.h2("35. A2A and interoperability")
    b.p(
        "Agent2Agent (A2A) is an open standard, initiated by Google and donated to the Linux Foundation, for communication between independent agents. Current released version in official materials: 1.0.0. Normative source: specification protobuf. Bindings: JSON-RPC 2.0, gRPC, HTTP/REST. Discovery via Agent Cards at /.well-known/agent-card.json. Unit of work: Task, with messages and artifacts."
    )
    b.table(
        ["Layer", "Protocol", "Status"],
        [
            ["Model ↔ tools/context", "MCP", "Standardized and widely implemented (2026-07-28 current)"],
            ["Agent ↔ agent", "A2A v1.0", "Standardized spec; enterprise adoption emerging"],
            ["Payments between agents", "Related efforts (e.g. AP2) mentioned in secondary write-ups", "Experimental / adjacent — verify before designing around them"],
        ],
        col_widths=[2800, 3280, 3280],
    )
    b.p(
        "MCP vs A2A is complementary, not a replacement fight: tools vs peer agents. Authentication, capability advertisement, and not sharing raw internal state are the enterprise requirements. Treat A2A as P2 implement / P1 explain unless the JD names it."
    )
    b.h2("36. Human-in-the-loop")
    b.p(
        "Approval for payments, emails, deletions, production change tickets, and anything irreversible. Confirmation for medium-risk. Escalation when confidence is low or policy is silent. Store the human decision in the audit log with the exact tool args shown to them — not a summary the model wrote."
    )
    b.h2("37. Agent evaluation")
    b.bullets(
        [
            "Task success / completion rate on a frozen scenario pack.",
            "Tool-selection accuracy and argument correctness.",
            "Step count, retry rate, latency, cost.",
            "Policy adherence and human-intervention rate.",
            "Offline replay from traces; online sampling; regression suite in CI.",
        ]
    )


def part6(b):
    b.page_break()
    b.h1("Part VI — Production AI")
    b.h2("38. OWASP GenAI LLM Top 10 2026")
    b.p(
        "Source: OWASP GenAI Security Project, OWASP GenAI LLM Top 10 2026, published 3–4 August 2026. "
        "This edition re-ranked risks using votes plus incident evidence. Excessive Agency climbed to third. "
        "Unbounded Consumption rose. Improper Output Handling fell to tenth. Prompt Injection stayed first. "
        "There is a separate OWASP Top 10 for Agentic Applications 2026."
    )
    b.table(
        ["ID", "Risk", "Engineer control (deterministic)"],
        [
            ["LLM01:2026", "Prompt Injection (direct, indirect, multimodal, memory)", "Assume injection; constrain tools; isolate untrusted content; never concatenate untrusted text into system policy"],
            ["LLM02:2026", "Sensitive Information Disclosure", "Minimize secrets in context; tenant isolation; output filters; no training on customer logs by default"],
            ["LLM03:2026", "Excessive Agency", "Least-privilege tools; HITL; no self-granting permissions"],
            ["LLM04:2026", "Supply Chain", "Pin models/SDKs; verify MCP servers; SBOMs; signed images"],
            ["LLM05:2026", "Data and Model Poisoning", "Ingest allowlists; provenance; eval canaries"],
            ["LLM06:2026", "Unbounded Consumption", "Hard budgets, timeouts, max steps, per-tenant quotas"],
            ["LLM07:2026", "Misinformation", "Grounding, citations, refusal, human review on high stakes"],
            ["LLM08:2026", "Hidden Context Exposure", "Redact traces; careful debug dumps; session isolation"],
            ["LLM09:2026", "Vector and Embedding Weaknesses", "ACL on index; inversion/poisoning tests; namespace per tenant"],
            ["LLM10:2026", "Improper Output Handling", "Treat model output as untrusted user input to HTML/SQL/shell"],
        ],
        col_widths=[1600, 3200, 4560],
    )
    b.h3("Agentic Top 10 (names from OWASP 2025-12/2026 materials)")
    b.p(
        "Public OWASP write-ups of the Agentic list include: Agent Goal Hijack, Tool Misuse, Identity & Privilege Abuse, Agentic Supply Chain, Unexpected Code Execution, among others. Use the official PDF for the locked 2026 wording when you study. The engineering moral is identical: identity, tool scope, and supply chain of MCP/A2A components."
    )
    b.h2("39. Deterministic security boundaries")
    b.p(
        "Models propose. Software disposes. Authentication, authorization, spend limits, deletion, schema validation, network egress, and data-class handling are code. If a requirement is ‘the agent should only see its tenant,’ that is a query filter and a warehouse policy, not a system prompt."
    )
    b.h2("40. Identity")
    b.table(
        ["Concept", "Apply to agents"],
        [
            ["OAuth 2.0 / 2.1 + OIDC", "User-delegated tools; PKCE; no implicit grant"],
            ["Workload identity", "Agent runtime in cloud; no long-lived keys in env if federation exists"],
            ["JWT", "Validate iss/aud/exp/nbf; never trust a model-issued token"],
            ["RBAC / ABAC", "Tool allowlists per role; attribute on resource"],
            ["Secrets", "Manager/Key Vault; rotate; never in prompts or traces"],
            ["On-behalf-of", "Pass user identity into MCP/API; prevent confused deputy"],
        ],
        col_widths=[3120, 6240],
    )
    b.h2("41. Guardrails and AI gateways")
    b.p(
        "A gateway gives you provider abstraction, routing, keys, budgets, caching, logging, and policy in one place. Cloud options include Amazon Bedrock Guardrails (including AgentCore policy support announced 17 June 2026), Azure AI Foundry / Azure OpenAI safety systems, and Vertex safety filters. Product gateways (Portkey, Helicone, vendor-native) exist. Build vs buy: buy if you have many models and many teams; still understand the failure mode."
    )
    b.h2("42. Observability")
    b.p(
        "Logs, metrics, traces (OpenTelemetry) plus LLM-specific fields: model, prompt version, response, tokens, cost, latency, retrieval IDs, tool names/args/results (redacted), trajectory, eval scores, tenant, request id. LangSmith, Langfuse, Arize Phoenix, and cloud APM all work. Correlation IDs must survive the agent loop."
    )
    b.h2("43. LLMOps / AgentOps")
    b.bullets(
        [
            "Version prompts, tools, retrievers, and models together.",
            "Canary traffic with eval gates.",
            "Replay failed traces.",
            "On-call runbooks (Part VIII).",
            "Cost anomaly alerts (LLM06).",
        ]
    )
    b.h2("44. Performance, cost, inference")
    b.table(
        ["Idea", "Must understand", "Must implement"],
        [
            ["TTFT vs ITL vs throughput", "Yes", "Measure in your app"],
            ["Prefill vs decode, KV cache", "Yes", "Only if you self-host"],
            ["Prompt caching", "Yes", "Yes — structure prompts for it"],
            ["Continuous batching, vLLM, SGLang, TensorRT-LLM, TGI, Triton", "Conceptual P1", "Only platform/inference JDs"],
            ["Quantization, speculative decoding, TP/PP", "Literacy", "P3 unless inference engineer"],
            ["Model routing", "Yes", "Yes — cheap model first, escalate"],
            ["Semantic cache", "Yes", "When corpus is FAQ-like"],
        ],
        col_widths=[3600, 2880, 2880],
    )
    b.h2("45. Reliability")
    b.p(
        "Fallbacks: smaller model, cached answer, keyword search, human. Timeouts at every hop. Idempotent writers. Chaos: kill the model provider in staging. SLOs on availability and on grounded-answer rate, not just HTTP 200."
    )


def part7(b):
    b.page_break()
    b.h1("Part VII — Cloud and deployment")
    b.h2("46. AWS (primary cloud to master)")
    b.p(
        "Why primary: breadth of FDE/enterprise demand, Bedrock as multi-model API, and a complete surrounding platform. Map services to the AI architecture, do not memorize 200 names."
    )
    b.table(
        ["Job in the architecture", "AWS service"],
        [
            ["Model API, multi-model", "Amazon Bedrock (plus OpenAI via Bedrock where offered)"],
            ["Managed agents / runtime", "Bedrock Agents / AgentCore; Guardrails in policy (Jun 2026+)"],
            ["Managed RAG", "Bedrock Knowledge Bases — still learn to build your own"],
            ["Training / custom", "SageMaker (P2 unless the JD is ML platform)"],
            ["API", "API Gateway + Lambda or ALB + ECS/EKS"],
            ["Containers", "ECS/Fargate first; EKS when you need k8s"],
            ["Object store / corpus", "S3"],
            ["OLTP + pgvector", "Aurora PostgreSQL / RDS"],
            ["Key-value / sessions", "DynamoDB or ElastiCache Redis"],
            ["Search", "OpenSearch"],
            ["Queues / events", "SQS, SNS, EventBridge, Step Functions"],
            ["Identity", "IAM, Cognito, STS / IRSA"],
            ["Secrets", "Secrets Manager / SSM"],
            ["Observability / audit", "CloudWatch, X-Ray, CloudTrail"],
        ],
        col_widths=[3600, 5760],
    )
    b.h2("47. Azure")
    b.p(
        "Microsoft’s current brand is Azure AI Foundry (classic Foundry portal has a published migration path). Azure OpenAI / Foundry hosts OpenAI and other models including Claude (Microsoft Foundry IDs in Anthropic docs). Azure AI Search is the usual managed retrieval. Identity is Entra ID — this is Azure’s enterprise advantage. Functions, Container Apps, AKS, API Management, Service Bus, Event Grid, Cosmos, PostgreSQL, Blob, Key Vault, App Insights are the surrounding cast. If your target employers are Microsoft, Accenture/Deloitte Microsoft practices, or India GCCs on Azure, this is co-primary, not optional."
    )
    b.h2("48. Google Cloud")
    b.p(
        "Vertex AI + Gemini + Vertex AI Search + Agent Development Kit + Agent Runtime / Cloud Run / GKE. ADK deploys with auth and Cloud Trace when you use Google’s agent platform. BigQuery is often the customer’s data gravity. Choose GCP as primary only if your target list is Google-heavy; still keep literacy."
    )
    b.h2("49. Cloud decision")
    b.table(
        ["Question", "Answer"],
        [
            ["Primary to master for a general FDE/GenAI IC in India targeting product + global labs", "AWS"],
            ["Primary if targeting Microsoft ecosystem / many India enterprise SI projects", "Azure"],
            ["Primary if targeting Google Cloud FDE / ADK shops", "GCP"],
            ["Secondary", "Whichever you did not pick; be able to redraw the same architecture"],
            ["What ‘master’ means", "Identity, networking, one container path, one data path, one AI API, logs, IAM least privilege, cost"],
        ],
        col_widths=[5200, 4160],
    )
    b.h2("50. Docker")
    b.p(
        "Images, layers, multi-stage builds, non-root users, healthchecks, Compose for local RAG+API+DB, .dockerignore, scanning. You should debug ‘works on my laptop’ with logs, exec, and diffing env vars. Never bake secrets into layers."
    )
    b.h2("51. Kubernetes (production literacy)")
    b.p(
        "Cluster/node/pod/ReplicaSet/Deployment/Service/Ingress/namespace, ConfigMap/Secret, requests/limits, probes, HPA, PVCs, Helm, kubectl logs/exec/describe. You do not need to write a scheduler. You do need to explain why a pod is CrashLooping, how to roll back, and how to keep GPU nodes from sitting idle. Interview depth: L2. Implement on a personal project with a managed cluster or skip GPU and run CPU for the RAG API."
    )
    b.h2("52. Terraform and CI/CD")
    b.p(
        "Terraform: providers, modules, remote state, workspaces/environments, never commit secrets. CI: GitHub Actions that run tests, eval smoke, docker build, and deploy to a non-prod account. CD: environment promotion, canary, rollback. Treat prompt files as code."
    )
    b.h2("53. Events")
    b.p(
        "SQS/Pub/Sub/Kafka/EventBridge for ingest, eval, and long agent jobs. Know at-least-once, idempotency, ordering (or the lack of it), and DLQ. Agents that ‘listen to the business’ are event consumers with a tool loop, not a 24/7 chat socket."
    )


def part8(b):
    b.page_break()
    b.h1("Part VIII — Enterprise / FDE")
    b.h2("54. Enterprise integrations")
    b.table(
        ["System", "How AI actually connects", "Permission trap"],
        [
            ["Salesforce", "REST/Bulk API, events, Agentforce if they own it", "Object-level FLS; never dump the org"],
            ["ServiceNow", "Table API, now Assist ecosystems", "Ticket PII, HR cases"],
            ["SAP / Workday", "Official APIs / middleware", "Financial/HR data class"],
            ["M365 / SharePoint / Teams", "Graph API, Copilot connectors", "Link sharing ≠ authorization"],
            ["Slack", "Events API, sockets", "Channel ACLs, DLP"],
            ["Snowflake / Databricks / BQ", "Query with roles, not copies", "Secondary indexes that bypass RLS"],
            ["Legacy DB", "Read replica, views, CDC", "Shadow IT extracts"],
        ],
        col_widths=[2200, 3580, 3580],
    )
    b.h2("55. FDE lifecycle")
    b.p(
        "Customer problem → discovery → requirements → data discovery → constraints → architecture → prototype → validation → integration → security review → deployment → adoption → monitoring → iteration → product feedback."
    )
    b.p(
        "Databricks’ FDE blog (2026) states customers moved from ‘help us migrate’ to ‘help us solve the business problem,’ with shared OKRs and weeks-not-quarters. OpenAI FDE postings similarly measure production adoption and eval feedback into research. If your weekly status is ‘we discussed,’ you are not doing the job."
    )
    b.h2("56. Customer discovery checklist")
    b.bullets(
        [
            "Business problem, users, current workflow, frequency, pain, cost of being wrong.",
            "Success metrics the CFO or ops owner already believes.",
            "Data: systems, owners, quality, freshness, volumes, PII.",
            "APIs and the unofficial Excel that actually runs the process.",
            "Identity: SSO, roles, contractors, break-glass.",
            "Latency, languages, offline, mobile.",
            "Compliance: residency, retention, logging, model training opt-out.",
            "Deployment: VPC, private link, on-prem, air-gap.",
            "Budget and who can say no.",
            "Human review: who, SLA, UI.",
            "What must never happen (the negative requirements).",
        ]
    )
    b.h2("57. Translating ‘we want an AI assistant’")
    b.table(
        ["They said", "You write down"],
        [
            ["Assistant for support", "Deflect L1 tickets; cite KB; no refunds without HITL; 5s p95; languages; Salesforce as SoR"],
            ["Internal ChatGPT", "Permission-aware RAG over Confluence+Drive; block other-tenant; DLP; eval on 100 golden Qs"],
            ["Agent that does ops", "Read-only first; change tickets via ServiceNow; dual control; max blast radius"],
            ["Voice bot", "Telephony, barge-in, PII redaction, handoff, recordings retention"],
        ],
        col_widths=[2800, 6560],
    )
    b.h2("58. Prototype vs production")
    b.table(
        ["Stage", "Allowed shortcuts", "Not allowed"],
        [
            ["Prototype (days)", "Hardcoded users, one corpus, one model", "Fake evals, ignoring ACL"],
            ["POC (1–3 weeks)", "Manual ingest, no HA", "Security exceptions that will ‘be fixed later’ without an owner"],
            ["MVP", "Single region, limited tools", "No logging, no rollback"],
            ["Production", "None of the above", "Hope"],
        ],
        col_widths=[2200, 3580, 3580],
    )
    b.h2("59. Production troubleshooting catalog (30 failures)")
    failures = [
        ["Hallucinated policy", "Answer confident, cite missing", "Compare retrieved chunks vs answer; faithfulness eval"],
        ["Wrong tenant snippet", "User saw another customer’s data", "Incident: ACL path, namespaces, cache keys"],
        ["Empty retrieval", "‘I don’t know’ on a known doc", "Recall@k; chunker; query rewrite; filters too tight"],
        ["Stale doc", "Old price/policy", "Indexer lag, delete propagation"],
        ["Duplicate chunks", "Contradictory cites", "Dedup, canonical source"],
        ["PDF parse garbage", "Broken tables", "Parser eval set; keep layout"],
        ["Embedding drift", "Quality drop after model swap", "Pin versions; reindex job"],
        ["Reranker timeout", "p95 exploded", "Fallback to hybrid scores"],
        ["Prompt injection in resume/PDF", "Agent emails secrets", "Untrusted content channel; tool allowlist"],
        ["Tool loop", "30 identical searches", "Max steps, repeat detection"],
        ["Wrong tool args", "API 400 storm", "Schema validation, repair once"],
        ["Double charge", "Two refunds", "Idempotency key from task id"],
        ["SSE disconnect", "UI hangs", "Resume tokens, reconnect"],
        ["Provider 429", "Total outage for tenant", "Backoff, queue, smaller model"],
        ["Cost spike", "Bill 10× overnight", "Budget caps, alert on tokens/user"],
        ["KV/cache leak", "User B got User A prefix", "Cache key includes tenant+user class"],
        ["JWT expired mid-agent", "Tools 401", "Token refresh in runtime, not in prompt"],
        ["SSO group change", "Access lag", "Document TTL of group cache"],
        ["Vector index full disk", "Ingest fail", "Watermarks, SLO on freshness"],
        ["Poisoned wiki page", "Sabotage", "Provenance, owners, canary questions"],
        ["GPU OOM (self-host)", "5xx", "Batch size, quantization — or don’t self-host yet"],
        ["Clock skew", "Token nbf/exp failures", "NTP, leeway"],
        ["Queue poison pill", "Consumer crash loop", "DLQ, schema version"],
        ["Rate limit vs fairness", "One user starves others", "Per-tenant tokens"],
        ["Markdown XSS", "Stored XSS from model", "Sanitize; CSP; LLM10"],
        ["SQL tool concatenation", "Injection", "Bind params only"],
        ["Eval/prod mismatch", "CI green, users scream", "Trace sampling of live questions into golden set"],
        ["Language mix", "Hindi query, English-only index", "Multilingual embedder / translation step"],
        ["Voice barge-in fail", "Talks over user", "VAD tuning"],
        ["Human approval ignored", "Model retried write", "Server-side gate, not prompt"],
    ]
    b.table(["Failure", "Symptom", "First moves"], failures, col_widths=[2200, 3280, 3880],
            caption="Table 59-1. Thirty production failures you should be able to diagnose.")
    b.h2("60. Stakeholders")
    b.p(
        "You will negotiate with security, legal, data owners, a VP who saw a demo, and an engineer who will inherit this. Write decisions down. Do not surprise security in week six. Influence without authority is the FDE behavioral loop: evidence, options, recommendation, ask."
    )
