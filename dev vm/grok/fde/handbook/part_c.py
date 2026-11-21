"""Parts IX–XII: architecture, hands-on, interviews, career execution."""


def part9(b):
    b.page_break()
    b.h1("Part IX — Architecture")
    b.h2("61. System design method")
    b.numbered(
        [
            "Clarify the job-to-be-done and the cost of being wrong.",
            "Users, volumes, languages, online vs batch.",
            "Functional requirements (must / later).",
            "Non-functionals: latency, availability, residency, RPO/RTO.",
            "Data: sources, ACL, freshness, deletion.",
            "APIs and integration contracts.",
            "Synchronous path vs async jobs.",
            "Models: default, cheap, fallback; who hosts.",
            "Retrieval: hybrid, rerank, citations.",
            "Agents: tools, state, HITL, max steps.",
            "Storage, cache, queues.",
            "Identity and tenancy.",
            "Eval plan (offline golden + online).",
            "Observability and cost.",
            "Deployment and rollback.",
            "Trade-offs said out loud.",
        ]
    )
    b.interview(
        [
            "Talk for 30–40 minutes. Draw. State assumptions. Do not jump to LangGraph before you have a success metric.",
            "Always mention ACL-before-retrieval, evals, and a kill switch. Interviewers listen for those three.",
        ]
    )

    designs = [
        (
            "62. Enterprise RAG assistant",
            [
                "Users: employees. Success: grounded answers with citations, <5s p95, zero cross-tenant leaks.",
                "Ingest: connectors → parse → ACL snapshot → chunk parent/child → BM25+pgvector.",
                "Query: rewrite → hybrid retrieve 50 → rerank 8 → generate with refusal if weak evidence.",
                "Identity: SSO; groups expanded server-side; filter in SQL.",
                "Eval: 150 golden Qs; faithfulness + recall@10 in CI.",
                "Trade-off: managed KB (Bedrock/Azure AI Search) vs own pipeline. Own pipeline if ACL is subtle.",
            ],
        ),
        (
            "63. Permission-aware knowledge platform",
            [
                "Same as RAG plus document-level ACL from SharePoint/Drive/Git, impersonation-free queries, audit of every retrieval, legal hold, and delete fan-out to index.",
                "Hardest part is mapping IdP groups to document ACLs without downloading the world as the service account.",
            ],
        ),
        (
            "64. AI coding agent",
            [
                "Sandbox (OpenAI-hosted or self-hosted), apply_patch/shell tools, repo indexing, tests as the eval, human approval to push.",
                "Never give prod credentials. OWASP LLM03/LLM10.",
            ],
        ),
        (
            "65. Research agent",
            [
                "Plan-and-execute, web+internal RAG, source list, critic on citations, budget on steps and dollars.",
                "Output: memo with links, not a vibe.",
            ],
        ),
        (
            "66. Customer-service agent",
            [
                "Router: FAQ RAG vs account tool vs human.",
                "Tools: CRM read, order status; refunds HITL.",
                "Voice optional (GPT-Live / provider realtime). PII redaction in traces.",
            ],
        ),
        (
            "67. Enterprise data analyst / SQL agent",
            [
                "Warehouse semantic layer; allowlisted views; dry-run EXPLAIN; row limits; never raw INSERT.",
                "Show SQL to the user. Golden questions from analysts.",
            ],
        ),
        (
            "68. Multi-agent operations platform",
            [
                "Supervisor routes to specialist workers (retriever, coder, ticket writer).",
                "Shared state in Postgres; A2A only if workers are separate vendors.",
                "Kill the swarm if a router + tools meets the SLA.",
            ],
        ),
        (
            "69. Document intelligence",
            [
                "OCR + layout + extraction schemas (Pydantic); human review queue; write-back to DMS.",
                "Eval on field-level F1, not BLEU.",
            ],
        ),
        (
            "70. Voice agent",
            [
                "Telephony SIP, VAD, barge-in, endpointing, tool latency budget <800ms for acknowledgements.",
                "Recordings: consent, retention, encryption.",
            ],
        ),
        (
            "71. Secure enterprise action agent",
            [
                "Read path autonomous; write path dual-control.",
                "MCP servers per system with OAuth on-behalf-of.",
                "Policy engine (OPA or Bedrock Guardrails/AgentCore policy) independent of the model.",
            ],
        ),
        (
            "72. Multi-tenant AI SaaS",
            [
                "Tenant in every key: DB, cache, vector namespace, logs, model budget.",
                "Noisy-neighbor isolation; per-tenant keys to providers or a gateway.",
                "Config as data; prompt versions per tenant optional, dangerous.",
            ],
        ),
    ]
    for title, bullets in designs:
        b.h2(title)
        b.bullets(bullets)

    b.h2("73. Other systems (brief)")
    b.p(
        "Multimodal assistant (images as first-class chunks). Autonomous RCA (logs → hypotheses → runbooks, never auto-remediate prod without HITL). "
        "Enterprise AI search (hybrid + ACL, no generation). Workflow automation agent (BPM + tools). Agent platform (gateway, eval, registry of MCP servers). "
        "Knowledge graph + RAG (only if entity resolution is funded). Browser/computer-use agent (sandboxed VM, allowlisted domains, video audit). "
        "AI deployment platform (the FDE’s internal factory: templates, identity, promotion)."
    )


def part10(b):
    b.page_break()
    b.h1("Part X — Hands-on")
    b.h2("74. Labs (progressive)")
    labs = [
        ["L01", "LLM API + retries + cost log", "Typed client, tests"],
        ["L02", "Streaming SSE from FastAPI", "Client can cancel"],
        ["L03", "Structured output / JSON schema", "Invalid JSON never reaches DB"],
        ["L04", "Embeddings + cosine search in memory", "Eval 20 queries"],
        ["L05", "pgvector hybrid search + ACL column", "Unauthorized doc never returns"],
        ["L06", "Chunker bake-off on one PDF corpus", "Recall table"],
        ["L07", "Reranker vs no reranker", "Latency/quality trade"],
        ["L08", "Citations in the answer UI", "Click-through to chunk"],
        ["L09", "RAGAS or DeepEval in CI", "Fails the PR if faithfulness drops"],
        ["L10", "Tool calling with Pydantic tools", "Unknown tool rejected"],
        ["L11", "LangGraph: two nodes + checkpoint", "Resume after kill"],
        ["L12", "HITL interrupt on a write tool", "Cannot skip in API"],
        ["L13", "Agent memory with TTL", "Forgotten on purpose"],
        ["L14", "MCP server (stdio) one tool", "Inspector works"],
        ["L15", "MCP Streamable HTTP + OAuth sketch", "Token not logged"],
        ["L16", "Prompt injection suite on your RAG", "Indirect injection via a doc"],
        ["L17", "Output sanitization (markdown/HTML)", "XSS attempt fails"],
        ["L18", "OpenTelemetry traces of a tool loop", "One request id"],
        ["L19", "Docker Compose: api+db+ui", "One command demo"],
        ["L20", "GitHub Actions: test+eval+image", "Main protected"],
        ["L21", "Deploy to one cloud (ECS/Cloud Run/ACA)", "HTTPS + identity"],
        ["L22", "Budgets and 429 handling", "Tenant cannot blow the bill"],
        ["L23", "Model router (luna→terra→astra)", "Quality vs cost table"],
        ["L24", "Eval golden set from prod traces", "Privacy redaction"],
        ["L25", "Multi-user SSO (Cognito/Entra/Auth0)", "Groups in ACL"],
        ["L26", "Delete a document end-to-end", "Vector gone, audit remains"],
        ["L27", "Queue for ingest", "Poison message DLQ"],
        ["L28", "SQL agent on allowlisted views", "No raw DDL"],
        ["L29", "Voice hello-world (optional)", "Latency notes"],
        ["L30", "Red-team day: OWASP LLM01–10 against your app", "Written findings"],
    ]
    b.table(["ID", "Lab", "Exit criteria"], labs, col_widths=[1000, 4680, 3680])

    b.h2("75. Portfolio bar")
    b.table(
        ["Bar", "Looks like"],
        [
            ["Toy (will not get a callback at a serious FDE/GenAI bar)", "ChatGPT wrapper, no evals, no auth, README = ‘I built RAG’"],
            ["Recruiter-worthy", "A named user and metric; messy data; ACL story; retrieval+tools; golden set; two OWASP mitigations actually coded; traces; 3-minute demo"],
            ["Senior / enterprise", "An incident you diagnosed; cost/latency numbers; a feature you killed; a design doc; evidence a workflow changed"],
        ],
        col_widths=[2800, 6560],
    )

    b.h2("76. Fifteen project ideas (ranked)")
    projects = [
        ["1", "Permission-aware company knowledge assistant", "FDE+GenAI flagship"],
        ["2", "Customer-support agent with HITL refunds", "Agentic + enterprise"],
        ["3", "Eval-and-observability platform for RAG", "Platform signal"],
        ["4", "MCP gateway with allowlisted servers and audit", "2026 differentiator"],
        ["5", "Databricks/Snowflake SQL analyst agent on views", "FDE data gravity"],
        ["6", "Document intake + extraction + human review", "Boring, hired"],
        ["7", "Multi-tenant SaaS FAQ agent with budgets", "Tenancy/cost"],
        ["8", "Incident RCA copilot over logs (read-only)", "Ops"],
        ["9", "Salesforce/ServiceNow write-back agent (sandbox)", "Integration"],
        ["10", "Hybrid search over code + tickets for internal eng", "DevEx"],
        ["11", "Voice IVR with handoff", "Multimodal optional"],
        ["12", "Computer-use agent in a locked VM for one workflow", "High risk, cap scope"],
        ["13", "Model router + gateway with OpenTelemetry", "LLMOps"],
        ["14", "Graph-augmented RAG for a real entity set", "Only if you have entities"],
        ["15", "Fine-tune LoRA for a tool-calling dialect", "P2; compare vs prompt"],
    ]
    b.table(["Rank", "Project", "Signal"], projects, col_widths=[800, 5560, 3000])

    b.h2("77. Top five — build plans")
    b.h3("Project A — Permission-aware knowledge assistant")
    b.bullets(
        [
            "Stack: FastAPI, Postgres+pgvector, Redis, SSO, LangGraph for optional multi-step, OpenTelemetry, one cloud.",
            "Folders: /api /ingest /eval /web /infra /docs. Prompts versioned in /prompts.",
            "Schema: tenants, users, documents(acl[], tsv, embedding), chunks(parent_id), traces, eval_cases.",
            "APIs: POST /query (SSE), POST /ingest, DELETE /documents/{id}, GET /admin/eval.",
            "Milestones: (1) hybrid search (2) ACL (3) citations UI (4) eval CI (5) deploy (6) injection tests.",
            "Interview talk: show a denied retrieval and a faithfulness fail that blocked a prompt change.",
        ]
    )
    b.h3("Project B — HITL support agent")
    b.bullets(
        [
            "Router + RAG + CRM mock + refund tool gated by human.",
            "State machine with checkpoints. Replay a bad trajectory in the demo.",
        ]
    )
    b.h3("Project C — MCP gateway")
    b.bullets(
        [
            "Catalog of servers, OAuth, policy on Mcp-Name, audit, prompt-injection tests on tool descriptions.",
            "This is a 2026 conversation starter; keep the implementation small and correct.",
        ]
    )
    b.h3("Project D — SQL analyst agent")
    b.bullets(
        [
            "Semantic layer YAML, allowlisted views, EXPLAIN, row cap, show SQL, golden questions from a public dataset (e.g. TPC-H style) plus one messy real CSV.",
        ]
    )
    b.h3("Project E — Eval platform")
    b.bullets(
        [
            "Ingest traces, score faithfulness/recall, dashboards, gate GitHub PRs. Eat your own cooking by using it on Project A.",
        ]
    )


def part11(b):
    b.page_break()
    b.h1("Part XI — Interviews")
    b.h2("78. How much LeetCode is justified")
    b.table(
        ["Track", "DSA intensity", "What actually decides"],
        [
            ["Classic SWE (Google/Meta/Amazon/Microsoft)", "High — still official", "DSA + design + (Amazon) Leadership Principles"],
            ["FDE / FDSE", "Moderate, product-framed medium", "Decomposition, learning/debug, communication, practical coding/SQL/APIs"],
            ["Lab GenAI / Applied (OpenAI/Anthropic)", "Floor, not the job", "Code quality, tests, LLM systems, mission/values, sometimes work sample"],
            ["India product (Flipkart-like)", "Machine coding + DSA mix", "Varies; prepare both machine coding and design"],
            ["India SI GenAI (TCS/Infosys/Accenture-like)", "Often lighter DSA, heavier tools keywords", "Do not confuse with Palantir FDE; still bring a portfolio"],
        ],
        col_widths=[2800, 2800, 3760],
    )
    b.p(
        "Rule: 150–200 well-understood medium problems is enough for FDE if you also practice decomposition and a RAG/agent design. "
        "Hard DP marathons are low ROI for these two career paths unless you are also sitting classic SWE loops."
    )

    b.h2("79. Company patterns (labeled)")
    b.h3("Palantir FDSE")
    b.p(
        "Official / Verified (palantir.com/careers/getting-hired, accessed 15 Sep 2026): process is personalized. Everyone starts with one or two phone interviews; engineering phones include a coding question; a fit leads to an onsite (in-person or virtual). Official guidance: think out loud, ask questions, start simple then expand. Official pages do not publish a fixed 2026 FDSE stage list or the names Decomposition / Learning / Re-engineering."
    )
    b.p(
        "Candidate-reported: recruiter motivation screen; HackerRank or live CodePair/Karat; onsite drawn from decomposition, learning, coding, re-engineering, system design; hiring-manager final. Coding commonly LeetCode-medium as a workflow (graphs/SQL/APIs). Decomposition is the signature. AI tools reported prohibited in the FDE loop — ask the recruiter. Timeline often 3–4 weeks."
    )
    b.h3("Databricks FDE")
    b.p(
        "Official / Verified (Databricks interview-prep site + April 2025 engineering PDF): typically 2–3 months; recruiter; pre-onsite screen; onsite 4–6 interviews; hiring committee for SWE; references. SWE panel types in the PDF include Coding, Algorithms, System Programming, Architecture, Domain Deep Dive, Cross-Functional/HM. Production-quality code, tests, edge cases, Big-O. Language-agnostic but fluent."
    )
    b.p(
        "Candidate-reported FDE variant: SQL + data + light RAG in screen; notebook coding; a decomposition-style business case. Treat round names as unconfirmed."
    )
    b.h3("OpenAI")
    b.p(
        "Official / Verified (openai.com/interview-guide): not credential-driven; application review (~1 week SLA stated), intro calls, skills-based assessment (pair coding, system design, work sample, or presentation), onsite. FDE-specific loop is not separately published. Candidate reports of paid work trials conflict — do not treat as policy."
    )
    b.h3("Anthropic")
    b.p(
        "Official: ‘what you can do, not where you learned it’; ~half of technical staff had no prior ML (careers page claim); engineering background → apply as engineer; Google Meet; Colab and CodeSignal mentioned for technical. Candidate AI guidance page exists (updated 2025-07-10). FDE/Applied AI round list not on the careers page."
    )
    b.h3("Google, Microsoft, Amazon, Meta, NVIDIA")
    b.p(
        "Google official: at most three jobs / 30 days; possible hiring assessment; 3–4 onsite in a day; no brain teasers; GCA, RRK, Leadership, Googliness. Microsoft official: 2–4 conversations; problem solving, design, coding, testing; write runnable code in a language you know. Amazon official: published loop + Leadership Principles in every round. Meta official: ~2–3 months; many interviews include a built-in CoderPad AI assistant you are expected to use; outside AI unauthorized. NVIDIA official: HackerRank-style coding; onsite required before offer. Named FDE loops at Google/Microsoft are not as publicly specified as Palantir’s role pages — prepare the employer’s general engineering loop plus an AI system design."
    )
    b.h3("Salesforce FDE")
    b.p(
        "Official role blog (19 Nov 2025): FDE team launched April 2025; company committed to building toward 1,000 FDEs (company statement in that post); pods of 1 deployment strategist + 2 FDEs; ~3 months / 1–2 use cases. Interview rounds not published."
    )
    b.h3("Scale")
    b.p("Postings exist. No public round-by-round guide found 15 Sep 2026. Candidate reports conflict.")

    b.h2("80. Expanded interview questions (high frequency)")
    qs = [
        {
            "q": "What is an FDE and how is it different from a consultant?",
            "cat": "FDE",
            "why": "Filters title tourists.",
            "s30": "Product engineer embedded with a customer, shipping on our platform, feeding the product. Not billed hours to configure a black box.",
            "s2": "Palantir/Databricks/OpenAI descriptions agree: own discovery through production. Consultants often leave a deck. FDEs leave running software and eval evidence. IT-services ‘FDE’ labels are sometimes diluted — I would ask what I actually merge to production.",
            "deep": "Use the comparison table in Chapter 3. Mention travel, ambiguity, and product feedback loop.",
            "follow": ["When would you refuse a customer request?", "How do you handle a PM who wants a demo that violates ACL?"],
            "miss": "‘I like talking to people.’",
        },
        {
            "q": "Walk me through a RAG system you would put in production tomorrow.",
            "cat": "RAG",
            "why": "Core GenAI loop.",
            "s30": "Hybrid retrieve with ACL in the query, rerank, cite, refuse if weak, eval in CI, traces on every call.",
            "s2": "Ingest with permissions; parent-child chunks; BM25+pgvector; rerank; generate; citations; golden set; injection tests; delete path. Prompt is versioned. Model is routed.",
            "deep": "Chapters 22–27. Draw the sequence diagram.",
            "follow": ["How do you know the retriever failed vs the generator?", "How do you handle a 200-page PDF table?"],
            "miss": "‘We use LangChain.’",
        },
        {
            "q": "Why must authorization happen before retrieval?",
            "cat": "Security",
            "why": "Enterprise bar.",
            "s30": "Once unauthorized text is in the context, the model can leak it. Prompting is not a control.",
            "s2": "Filters in the index query; tenant in every cache key; audit. Defense in depth still re-checks before generate. OWASP LLM02 and LLM09.",
            "deep": "Chapter 26 and 38.",
            "follow": ["What if embeddings invert?", "Shared cache poisoning?"],
            "miss": "System prompt ‘do not reveal other customers.’",
        },
        {
            "q": "Design an agent that can refund a customer.",
            "cat": "Agents",
            "why": "Excessive agency.",
            "s30": "Model proposes; policy engine + human approve; idempotent refund API; audit.",
            "s2": "Read tools autonomous. Refund tool schema with amount caps. Interrupt in the graph. Approver sees raw args. Retry uses the same idempotency key. Eval trajectories for ‘refund without approval’ as a failing case.",
            "deep": "LLM03:2026. Pattern: approval-gated tool node.",
            "follow": ["What if the human never responds?", "How do you prevent prompt injection from the ticket body?"],
            "miss": "Give the model the Stripe key and a prompt.",
        },
        {
            "q": "MCP vs A2A?",
            "cat": "Protocols",
            "why": "2026 literacy.",
            "s30": "MCP connects a host to tools/resources/prompts. A2A connects independent agents via cards and tasks.",
            "s2": "MCP current spec 2026-07-28, now stateless with server/discover. A2A v1.0, Linux Foundation, Agent Cards. Complementary. I would implement MCP first unless the problem is truly cross-vendor agents.",
            "deep": "Chapters 34–35.",
            "follow": ["How would you authenticate an MCP server?", "What is tool poisoning?"],
            "miss": "Treat them as competing standards you must pick one of.",
        },
        {
            "q": "How do you evaluate a RAG change?",
            "cat": "Eval",
            "why": "Separates builders from tuners.",
            "s30": "Freeze a golden set; measure retrieval and generation separately; block merge if faithfulness or recall drops.",
            "s2": "Recall@k on labels; faithfulness of answers; online sampling of traces into the set; LLM-as-judge calibrated on humans. Never ship because a demo looked nicer.",
            "deep": "Chapter 27.",
            "follow": ["How big a golden set?", "How do you handle language mix?"],
            "miss": "‘We eyeball it.’",
        },
        {
            "q": "A customer says the bot is hallucinating. What do you do in the first hour?",
            "cat": "Debug / FDE",
            "why": "Production ownership.",
            "s30": "Get the request id, traces, retrieved chunks, and the user question. Classify retriever miss vs ungrounded generate vs stale index vs injection.",
            "s2": "Check tenant ACL, index freshness, prompt version, model version, cost/latency anomalies. Reproduce offline. If leak suspected, incident process first.",
            "deep": "Table 59-1.",
            "follow": ["What if there are no traces?", "What do you tell the customer VP?"],
            "miss": "Raise temperature discussion first.",
        },
        {
            "q": "Explain attention to a smart software engineer who is not an ML person.",
            "cat": "Transformers",
            "why": "Literacy.",
            "s30": "Each token builds a query and looks up others by key, then mixes their values. Many heads, then a feed-forward. Residuals keep it trainable.",
            "s2": "Tie to cost (quadratic attention), KV cache, and why long context is not free. Decoding = next-token sampling.",
            "deep": "Chapter 15.",
            "follow": ["What is a KV cache?", "Why does JSON burn tokens?"],
            "miss": "Only say ‘it looks at important words.’",
        },
        {
            "q": "Python: implement retries with exponential backoff and jitter for an LLM client.",
            "cat": "Coding",
            "why": "Practical bar.",
            "s30": "Retry 429/5xx/timeouts only; cap attempts; jitter; don’t retry POSTs unless idempotent.",
            "s2": "Show typed response, logging, timeout, tests with a fake clock/transport. See Figure 7-1.",
            "deep": "Idempotency keys for tools.",
            "follow": ["What about streaming failures?", "How do you test it?"],
            "miss": "Bare except and sleep(1) in a loop.",
        },
        {
            "q": "SQL: given documents(tenant_id, acl[], embedding, tsv), write the authorized hybrid retrieve.",
            "cat": "SQL",
            "why": "FDE/data.",
            "s30": "Filter tenant and acl overlap first, then order by blended BM25 and cosine, limit.",
            "s2": "Figure 10-1. Discuss indexes (GIN on tsv, ivfflat/hnsw on embedding, btree tenant).",
            "deep": "Why filter before ANN if the engine supports it.",
            "follow": ["How do you paginate ANN?", "How do you delete?"],
            "miss": "SELECT * and filter in Python.",
        },
    ]
    for i, item in enumerate(qs, 1):
        b.h3(f"Q{i}. {item['q']}")
        b.table(
            ["Field", "Content"],
            [
                ["Category / why", f"{item['cat']} — {item['why']}"],
                ["30-second", item["s30"]],
                ["2-minute", item["s2"]],
                ["Deep pointer", item["deep"]],
                ["Follow-ups", " | ".join(item["follow"])],
                ["Common miss", item["miss"]],
            ],
            col_widths=[2200, 7160],
        )

    b.h2("81. Drill banks (answer out loud; expand the important ones yourself)")
    b.h3("Python (50 prompts)")
    b.p(
        "GIL vs asyncio vs processes; event loop blocking; context managers; decorators; dataclasses vs Pydantic; typing.Protocol; generators; itertools; deepcopy pitfalls; mutable defaults; __slots__; packaging; venv/uv; pytest fixtures; monkeypatch; parametrize; coverage; logging vs print; structlog; secrets in env; pathlib; json vs orjson; httpx vs requests; streaming responses; cancellation; TaskGroup; deadlock; race; queue.Queue vs asyncio.Queue; pickle safety; eval/exec; hash randomization; sort stability; bisect; heapq; LRU cache; functools.partial; match/case; exceptions hierarchy; custom exceptions; traceback; profiling; memory leaks; circular imports; namespace packages; wheels; C extensions literacy; mypy/pyright; ruff; make a CLI; design a plugin interface."
    )
    b.h3("Backend / APIs (40)")
    b.p(
        "REST vs RPC; idempotency; pagination; ETags; CORS; CSRF; cookies vs bearer; OAuth code flow; PKCE; JWT claims; refresh rotation; rate limit algorithms; API gateway vs library; OpenAPI; versioning; webhooks signing; SSE vs WS; backpressure; 201 vs 202; problem+json; tracing headers; retries at client vs server; bulkheads; multi-region; blue-green; feature flags; N+1; connection pools; migrations; zero-downtime schema; outbox pattern; sagas; CQRS lite; file uploads; SSRF; mass assignment; IDOR; least privilege service accounts."
    )
    b.h3("SQL / Postgres (40)")
    b.p(
        "JOIN types; GROUP BY vs window; CTEs; EXPLAIN ANALYZE; btree vs gin vs gist vs hnsw; MVCC; isolation levels; deadlocks; vacuum; bloat; JSONB queries; partial indexes; covering indexes; hot updates; pooling (PgBouncer); RLS; logical replication; failover; pgvector ops; hybrid retrieval SQL; upsert; advisory locks; LISTEN/NOTIFY; partitioning; generated columns; collations; timezone; slow query log; seq scan surprises; cardinality; bind params; SQL injection; views vs matviews; transactions around ingest+index; delete fan-out."
    )
    b.h3("Distributed systems (30)")
    b.p(
        "CAP as a conversation not a slogan; at-least-once; exactly-once illusion; idempotency keys; outbox; inbox; leader election; fencing; clocks; HLC; partitions; rebalancing; poison pills; backpressure; load shedding; hedging requests; tail latency; SLO/SLI/SLA; error budgets; chaos; quorum; cache stampede; thundering herd; split brain; rolling deploys; sticky sessions; why agents must be horizontally stateless at the pod."
    )
    b.h3("LLMs / RAG / agents / MCP / security / eval / cloud / k8s / FDE / behavioral")
    b.p(
        "Use Parts III–VIII as the question generator. Minimum self-test: 60 LLM, 75 RAG, 100 agent, 40 MCP/A2A, 50 security, 40 eval, 40 LLMOps, 60 cloud, 40 Docker/K8s, 50 system-design prompts, 50 FDE scenarios, 40 behavioral STAR stories. If you cannot fill a 2-minute answer from this book plus your project, that topic is not yet P0."
    )

    b.h2("82. Coding interview problems (practice set)")
    b.numbered(
        [
            "HTTP client with retries, jitter, and typed errors (solution pattern: Figure 7-1).",
            "Token-bucket rate limiter (per tenant).",
            "Async gather of N tools with individual timeouts.",
            "SSE generator that heartbeats.",
            "Chunker: recursive split with overlap; unit tests on a fixture.",
            "Cosine similarity + top-k in numpy-free Python.",
            "Merge k ranked lists (RRF).",
            "JSON schema validate tool args; reject additionalProperties.",
            "Idempotent refund ledger.",
            "In-memory vector store with tenant filter.",
            "Simple BM25-ish scorer on a toy corpus.",
            "Agent state reducer that is deterministic.",
            "Detect repeated tool calls (loop). ",
            "Parse a messy CSV to a Pydantic model with errors collected.",
            "SQL: top N documents per tenant by recency with window functions.",
            "Queue worker with exponential backoff and DLQ.",
            "Prefix cache key builder that includes tenant and prompt version.",
        ]
    )

    b.h2("83. Debugging exercises")
    b.p(
        "Take any row in Table 59-1 and run: hypothesis → logs/metrics/traces you would pull → experiment → root cause → fix → prevention. Time-box 15 minutes each. Record a STAR story from your project when you actually hit one."
    )

    b.h2("84. FDE case studies (practice)")
    cases = [
        "Airline: ‘Why are we delaying flights?’ (Palantir-style open question).",
        "Bank: money-laundering typology assistant with SAR workflow and strict ACL.",
        "Hospital: clinical guideline RAG; HIPAA-like controls; no diagnosis claims.",
        "Retail: returns agent across OMS + policy PDFs.",
        "Public sector: caseworker knowledge base; clearance; air-gapped options.",
        "SaaS vendor: deploy your product into a customer VPC with PrivateLink.",
        "Manufacturer: maintenance manuals + IoT alarms; on-prem.",
        "Telco: field-tech voice assistant; offline mode.",
        "Insurer: claims extraction + fraud hints; human final.",
        "University: student-records chatbot; FERPA-like; never cross students.",
    ]
    b.p("For each: business context, ambiguous ask, 10 questions, constraints, architecture, prototype slice, security, risks, success metric.")
    b.numbered(cases)
    b.p("Write ten more from your domain. Quality of questions beats cleverness of architecture.")

    b.h2("85. Behavioral (STAR)")
    b.p(
        "Always: Situation, Task, Action (your actions), Result (numbers), and a sentence of what you would do differently. Palantir and FDE loops embed behavioral inside technical rounds. Amazon maps stories to Leadership Principles. OpenAI/Anthropic probe collaboration, honesty about uncertainty, and mission."
    )
    themes = [
        "Ambiguity with no spec",
        "Customer who wanted a demo that was unsafe",
        "Disagreement with a senior engineer",
        "Production incident you owned",
        "Urgent deadline vs quality",
        "Prioritization when everything is P0",
        "Requirements changed mid-build",
        "Influencing without authority",
        "A time you killed your own idea",
        "Feedback you gave to product from the field",
        "Working with legal/security as partners",
        "Failure that taught you evals",
    ]
    b.bullets(themes)


def part12(b):
    b.page_break()
    b.h1("Part XII — Career execution")
    b.h2("86. Learning resources (ranked, official first)")
    b.table(
        ["Priority", "Resource", "Why"],
        [
            ["Essential", "Python docs + FastAPI docs + pytest docs", "The job is software"],
            ["Essential", "PostgreSQL docs (SQL, indexes, JSONB) + pgvector README", "Default data plane"],
            ["Essential", "OpenAI Responses API, tools, structured outputs, prompt caching", "Current, not Chat Completions-first"],
            ["Essential", "Anthropic Messages + tool use + MCP connector docs", "Enterprise + agents"],
            ["Essential", "LangGraph docs (persistence, interrupts)", "Deep framework pick"],
            ["Essential", "MCP spec 2026-07-28 + Python/TS SDK quickstart", "Current protocol"],
            ["Essential", "OWASP GenAI LLM Top 10 2026 + Agentic Top 10 PDFs", "Shared risk language"],
            ["Essential", "One cloud: AWS Bedrock+IAM+ECS or Azure Foundry+Entra or Vertex+ADK", "Pick from target employers"],
            ["Recommended", "LlamaIndex RAG modules; RAGAS/DeepEval; LangSmith or Langfuse", "Eval/observe"],
            ["Recommended", "A2A spec 1.0 conceptual read", "Literacy"],
            ["Recommended", "vLLM docs conceptually", "Inference literacy"],
            ["Recommended", "Palantir Getting Hired + Databricks interview-prep PDF + OpenAI interview guide", "Official loops"],
            ["Optional", "Attention-is-All-You-Need (read once)", "History, not the job"],
            ["Optional", "Kubernetes the Hard Way", "Only if you enjoy pain; managed k8s is enough"],
            ["Skip as primary", "Random ‘50 agent frameworks’ YouTube", "Hype"],
        ],
        col_widths=[1600, 4200, 3560],
    )

    b.h2("87. GitHub study list")
    b.table(
        ["Repo / artifact", "Study", "Reimplement"],
        [
            ["modelcontextprotocol/python-sdk", "Server + auth examples", "Your L14–L15"],
            ["langchain-ai/langgraph examples", "Interrupt + checkpoint", "HITL node"],
            ["openai-agents / Agents SDK samples", "Tools + guardrails + tracing", "One agent without copying structure blindly"],
            ["google/adk-python (ADK)", "Context management, deploy", "A tiny ADK agent if targeting Google"],
            ["a2aproject/A2A", "Agent Card + task lifecycle", "Read spec; implement only if needed"],
            ["OWASP GenAI-LLM-Top10", "Mitigations", "Turn into tests in your app"],
        ],
        col_widths=[2800, 3280, 3280],
    )

    b.h2("88. Papers (engineering takeaway only)")
    b.table(
        ["Paper", "Takeaway", "Depth"],
        [
            ["Attention Is All You Need", "Transformer block", "Skim + diagram"],
            ["Retrieval-Augmented Generation (Lewis et al.)", "Why RAG exists", "Abstract + figure"],
            ["ReAct", "Interleave reason/act", "Pattern"],
            ["Lost in the Middle", "Position in context matters", "Design implication"],
            ["Toolformer / subsequent tool-calling work", "Tools > parametric knowledge for facts", "Idea"],
        ],
        col_widths=[3120, 4000, 2240],
    )

    b.h2("89. Certifications ROI")
    b.p(
        "Principle: at Palantir/OpenAI/Anthropic/Google/Meta a cert almost never substitutes for a shipped system. Certs help ATS at enterprises and SIs and structure your learning. Blog salary-premium claims are not causal."
    )
    b.table(
        ["Cert", "Learning", "Employer signal", "Note"],
        [
            ["AWS SAA", "High", "High in AWS shops/SIs", "Broadest associate keyword"],
            ["AWS ML Engineer associate / current ML path", "High for Bedrock", "Medium-high on AWS GenAI JDs", "Pair with a project"],
            ["Azure AI Engineer (AI-102 or current equivalent)", "High on Azure", "High in MSFT/SI India", "Foundry names change — use current exam"],
            ["Databricks Data Engineer / GenAI associate if current", "High if targeting Databricks FDE", "High there", "Platform-specific"],
            ["CKA", "High for k8s debug", "Medium", "Only if you will operate clusters"],
            ["NVIDIA NCP-GENL or current GenAI", "Medium", "Medium at NVIDIA/partner", "Optional"],
            ["AWS Cloud Practitioner / AI-900 / GCP Digital Leader", "Low", "Low at labs", "Low ROI as a centerpiece"],
            ["Five associate badges, no production", "Low", "Negative", "Looks like exam farming"],
            ["Salesforce Trailhead ranks as a portfolio substitute", "Learning ok", "Not a waiver", "Official FDE blog is about the job, not badges"],
        ],
        col_widths=[2800, 1800, 2200, 2560],
    )
    b.p("FDE rule of thumb: one cloud associate in the customer’s cloud plus Databricks/Salesforce if that is the platform. A second cloud cert is usually worse than one production-ish RAG/agent with evals.")

    b.h2("90. 12-week intensive roadmap")
    weeks = [
        ["1", "Python production + git + tests", "Figure 7-1 client", "L01–L03"],
        ["2", "FastAPI + auth + Postgres SQL", "CRUD + EXPLAIN", "L19 local compose"],
        ["3", "Docker + CI + one cloud account", "Deploy hello API", "L20–L21"],
        ["4", "Embeddings, hybrid search, chunking", "Recall table", "L04–L07"],
        ["5", "Full RAG + citations + ACL", "Unauthorized test", "L05, L08, L16"],
        ["6", "Eval in CI + traces", "Fail a PR on purpose", "L09, L18, L24"],
        ["7", "Tool calling + LangGraph checkpoint", "Resume after kill", "L10–L13"],
        ["8", "HITL + MCP server", "Inspector + audit", "L14–L15"],
        ["9", "OWASP red team + budgets + router", "Written findings", "L16, L22, L23, L30"],
        ["10", "Project A end-to-end polish", "3-minute demo", "README + architecture doc"],
        ["11", "System design drills + FDE cases", "5 designs timed", "Ch 61–73, 84"],
        ["12", "Interview loops + Project B or C slice", "Mocks recorded", "Ch 78–85"],
    ]
    b.table(["Week", "Learn", "Build", "Lab/exit"], weeks, col_widths=[800, 2800, 2880, 2880])
    b.p("Must complete: weeks 1–10. Optional: voice lab, A2A, self-hosted vLLM, second cloud. Daily template: 90 min theory, 120 min code, 30 min debug journal, 30 min interview out-loud, 20 min revision notes.")

    b.h2("91. 90-day job transition")
    b.table(
        ["Days", "Work"],
        [
            ["1–30", "Finish Project A to recruiter-worthy; LinkedIn headline = role you want; 10 conversations not applications; resume with one architecture diagram; apply only to JDs you can map to the skill matrix"],
            ["31–60", "Project B or C; 5 mock interviews (one FDE decomposition, one RAG design, one coding); apply 5–8 tailored roles/week not 50 spray; India: product/GCC/lab first if you want Palantir-like work, SI GenAI with eyes open"],
            ["61–90", "Onsite prep; STAR bank; negotiate with competing evidence not vibes; keep shipping evals so you have a fresh story"],
        ],
        col_widths=[1600, 7760],
    )

    b.h2("92. Interview readiness score (100 points)")
    b.table(
        ["Area", "Points", "4 = ready"],
        [
            ["Python + tests", "8", "Write Figure 7-1 live"],
            ["Backend APIs", "8", "Design + implement FastAPI slice"],
            ["SQL/Postgres", "8", "Write hybrid ACL SQL"],
            ["Software engineering", "6", "State machines vs spaghetti"],
            ["LLMs + APIs", "8", "Current model IDs, Responses API, tools"],
            ["RAG", "10", "Build + eval + cite"],
            ["Agents", "10", "HITL graph, no infinite loop"],
            ["MCP", "6", "Explain 2026-07-28 + implement one server"],
            ["Security", "8", "OWASP 2026 controls in your repo"],
            ["Eval + observability", "8", "CI gate + traces"],
            ["Cloud + Docker", "8", "Deployed, IAM least privilege"],
            ["System design", "6", "40-minute RAG+agent design"],
            ["FDE/customer", "6", "Discovery checklist live"],
        ],
        col_widths=[2800, 1600, 4960],
    )
    b.p("Thresholds: <50 not ready to apply seriously; 50–74 apply to mid SI/product with eyes on gaps; 75–89 competitive for FDE/GenAI IC at product companies; 90+ you are wasting time studying instead of interviewing. Self-score harshly using artifacts, not feelings.")

    b.h2("93. Master checklist (condensed)")
    checks = [
        "I can write production Python with types, tests, and retries.",
        "I can ship a FastAPI service with auth and OpenAPI.",
        "I can write SQL JOINs, windows, and EXPLAIN.",
        "I can explain transformers and decoding without mysticism.",
        "I can call current OpenAI/Anthropic/Gemini APIs (correct names, tools, structured output).",
        "I can build hybrid RAG with citations.",
        "I can evaluate retrieval separately from generation.",
        "I can implement ACL-before-retrieval and prove it with a test.",
        "I can build a tool-calling agent with max steps and HITL on writes.",
        "I can implement a minimal MCP server and describe the 2026-07-28 stateless core.",
        "I can explain MCP vs A2A without mixing them.",
        "I can map OWASP LLM Top 10 2026 onto my app.",
        "I can read a trace and find a failed tool call.",
        "I can estimate cost and add a budget.",
        "I can containerize and deploy to one cloud.",
        "I can debug 10 failures from Table 59-1.",
        "I can run an FDE discovery conversation.",
        "I can design an enterprise RAG system on a whiteboard in 40 minutes.",
        "I have one recruiter-worthy project with a demo and evals.",
        "I have STAR stories for conflict, incident, ambiguity, and a killed feature.",
    ]
    b.numbered(["☐ " + c for c in checks])
    b.p("Expand to 150 items by turning every lab exit criterion and every matrix P0 cell into a checkbox. If any major audit question in the original brief is still NO, that chapter is unfinished for you personally — not for this book’s outline.")

    b.h2("94. Must-know 100 (top of the stack)")
    b.p(
        "Python types; pytest; asyncio; FastAPI; authn vs authz; JWT pitfalls; Postgres indexes; pgvector; Redis uses; Docker; CI; IAM; one cloud AI API; SSE; retries; idempotency; queues; DLQ; embeddings; cosine; BM25; HNSW; hybrid; rerank; chunking; parent-child; citations; golden sets; faithfulness; recall@k; prompt vs context vs tools; structured output; function calling; ReAct; graph state; checkpoints; HITL; max steps; MCP host/client/server; server/discover; OAuth for MCP; tool poisoning; A2A card/task; OWASP LLM01–10 2026; excessive agency; output handling; injection direct/indirect; tenant isolation; cache keys; traces; cost tokens; prompt cache; model routing; TTFT; KV cache idea; vLLM literacy; k8s pod debug; Terraform state; SSO; RBAC; secrets manager; eval in CI; canary; rollback; FDE lifecycle; discovery questions; prototype vs prod; Palantir official vs candidate-reported loops; Databricks FDE JD; OpenAI FDE success metric; LangGraph vs CrewAI in JDs; India title inflation; don’t fine-tune for facts; don’t put ACL in the prompt; don’t run random MCP servers; don’t spray 50 applications without a project."
    )

    b.h2("95. Cheat sheets")
    b.h3("FDE discovery (one page)")
    b.p(
        "Problem, user, workflow, frequency, cost of error, metric, data systems, owners, ACL, PII, APIs, shadow Excel, SSO, latency, language, residency, retention, VPC, budget, human review, never-events, success in 2 weeks vs 2 months."
    )
    b.h3("RAG go-live")
    b.p(
        "Hybrid + ACL + citations + golden 50 + traces + delete path + injection test + budget + fallback search."
    )
    b.h3("Agent go-live")
    b.p(
        "Typed state, tool allowlist, schema validation, max steps, HITL writes, idempotency, audit, eval pack of trajectories, kill switch."
    )
    b.h3("Incident first five")
    b.p("Request id → traces → retrieved chunks → prompt/model versions → classify leak vs quality vs cost vs outage.")

    b.h2("96. Final role blueprints")
    b.h3("Blueprint A — Forward Deployed AI Engineer")
    b.bullets(
        [
            "P0: Python, APIs, SQL, cloud, customer discovery, one full-stack slice, RAG literacy, evals, security boundaries, system design under ambiguity.",
            "P1: LangGraph, MCP, k8s literacy, a vertical (fintech/health/public sector).",
            "Portfolio: Project A + one customer-shaped case write-up.",
            "Interview: decomposition practice, medium coding, SQL, design, STAR.",
            "Cloud: AWS default or the platform of the employer (Databricks/Palantir/Salesforce/Azure).",
        ]
    )
    b.h3("Blueprint B — GenAI / Agentic AI Engineer")
    b.bullets(
        [
            "P0: Python, APIs, RAG as default, tool calling, evals, traces, OWASP 2026, Postgres, one agent graph with HITL.",
            "P1: MCP implementation, routing/cost, k8s, gateway.",
            "P2: A2A, self-host inference, fine-tuning.",
            "Portfolio: Project A + B or C.",
            "Interview: RAG/agent design, practical coding, less LeetCode-hard, more eval thinking.",
        ]
    )
    b.h2("97. Overlap and final priority")
    b.table(
        ["Shared core", "FDE-specific", "GenAI-specific", "Agentic-specific"],
        [
            ["Python, APIs, SQL, cloud, RAG, eval, security, traces", "Discovery, travel, ambiguity, product feedback, stakeholder mgmt", "Retrieval quality, chunking science, eval harness depth", "State machines, HITL, tool platforms, MCP/A2A"],
        ],
        col_widths=[2340, 2340, 2340, 2340],
    )
    b.table(
        ["Band", "Learn"],
        [
            ["P0 now", "Python, FastAPI, Postgres+pgvector, hybrid RAG+ACL, LLM APIs (current names), evals, HITL tools, OWASP 2026, one cloud deploy, discovery checklist"],
            ["P1 before onsites", "LangGraph, MCP server, k8s literacy, system-design reps, decomposition reps"],
            ["P2 while interviewing", "A2A, second cloud, gateway product, voice, computer-use sandbox"],
            ["P3 later", "Train/fine-tune large models, write a scheduler, collect certs, fifth agent framework"],
        ],
        col_widths=[2200, 7160],
    )

    b.h2("98. What not to overlearn")
    b.bullets(
        [
            "Deriving transformer math beyond intuition — low interview ROI for these roles.",
            "Training foundation models from scratch.",
            "Collecting agent frameworks (CrewAI+AutoGen+five more) instead of one graph runtime.",
            "Heavy frontend (Next.js polish) unless the JD is full-stack FDE with UI ownership.",
            "LeetCode Hard as a lifestyle if you are not also sitting classic SWE.",
            "Foundational cloud certs as a personality.",
        ]
    )

    b.h2("99. Knowledge dependency graph")
    b.code(
        """Programming (Python)
  → Backend/API + Git/CI
    → SQL/Postgres + Redis
      → LLM APIs (Responses/Messages) + structured output
        → Embeddings + hybrid search
          → RAG + ACL + citations
            → Eval + traces
              → Tool calling + state graphs (LangGraph)
                → HITL + budgets
                  → MCP (then A2A literacy)
                    → Security (OWASP 2026) wrapped around all of the above
                      → Cloud deploy + identity
                        → System design
                          → FDE discovery / customer delivery""",
        caption="Figure 99-1. Do not skip layers. Agents on top of weak APIs is how demos die in production.",
    )


def references(b):
    b.page_break()
    b.h1("References and source notes")
    b.p("Access date for all URLs unless noted: 15 September 2026. Prefer the live page; products move.")
    refs = [
        ["R1", "Plank FDE job-market census", "Plank", "Observed 12 Sep 2026", "N=1,333 FDE-family titles, CC BY 4.0"],
        ["R2", "Forward Deployed Software Engineer postings", "Palantir / Lever", "Accessed 15 Sep 2026", "Role definition, languages, USG salary example $135–200k"],
        ["R3", "FDE job description + FDE blog + Deployment Strategist JD", "Databricks", "Sep 2026", "Full-stack customer embedding; DS vs FDE split"],
        ["R4", "FDE postings (SF/NYC/Seattle aggregators quoting official)", "OpenAI", "Sep 2026", "End-to-end deploy, evals into research, travel; base bands vary by req"],
        ["R5", "Models, Responses API, tools, caching", "OpenAI", "https://developers.openai.com/api/docs/models", "GPT-6 Astra; GPT-5.6 Sol/Terra/Luna"],
        ["R6", "Models overview", "Anthropic", "https://platform.claude.com/docs/en/models/overview", "Fable 5.1, Opus 5, Sonnet 5, Haiku 4.5"],
        ["R7", "MCP specification 2026-07-28", "MCP project", "https://modelcontextprotocol.io/specification/2026-07-28", "Current; stateless core"],
        ["R8", "A2A protocol", "Linux Foundation / a2a-protocol.org", "v1.0.0", "Agent Cards, tasks; complementary to MCP"],
        ["R9", "OWASP GenAI LLM Top 10 2026", "OWASP GenAI Security Project", "Published 3–4 Aug 2026", "LLM01–10:2026"],
        ["R10", "OWASP Top 10 for Agentic Applications 2026", "OWASP", "2026", "Agentic-specific risks"],
        ["R11", "LangGraph overview", "LangChain Inc.", "https://docs.langchain.com/oss/python/langgraph/overview", "Durable graphs, HITL"],
        ["R12", "Agent Development Kit", "Google", "https://adk.dev/", "ADK 2.0 graphs; multi-language"],
        ["R13", "Getting Hired", "Palantir", "https://www.palantir.com/careers/getting-hired/", "Official personalized loop"],
        ["R14", "Interview prep", "Databricks / OpenAI / Anthropic / Google / Microsoft / Amazon / Meta / NVIDIA", "Official careers pages", "See Ch. 79 labels"],
        ["R15", "Bedrock AgentCore + Guardrails in policy", "AWS", "17 Jun 2026 announcement", "Gateway/policy direction"],
        ["R16", "FDE, Agentic Platform JD", "Cohere", "Sep 2026", "ReAct/plan-execute, evals"],
        ["R17", "Plenty of coders, few deployers… ₹1.55 crore", "Mint citing FDE Academy", "15 Sep 2026", "Secondary India pay bands; not a census"],
        ["R18", "CIEL HR FDE demand +130%", "Hindu Business Line", "3 Aug 2026", "Staffing-firm India cut"],
        ["R19", "India Today FDE explainer", "India Today", "17 Jul 2026", "Bengaluru average vs senior; TCS plan as news"],
        ["R20", "ET on FDE dilution in IT services", "Economic Times / Everest Group", "18 Jun 2026", "Title inflation warning"],
        ["R21", "Salesforce FDE blog", "Salesforce", "19 Nov 2025", "Team launch, pod model, 1,000 FDE commitment (company statement)"],
        ["R22", "GenAI JD convenience sample N=50", "This handbook research", "15 Sep 2026", "Skill frequencies in Ch. 4"],
        ["R23", "Microsoft Foundry naming / Assistants sunset notes", "Microsoft Learn + handbook tech brief", "2026", "Do not use retired API names in interviews"],
    ]
    b.table(["ID", "Work", "Org", "Date / URL", "Used for"], refs, col_widths=[700, 2400, 1800, 2300, 2160])
    b.warn(
        [
            "Where secondary press and a listing census disagree (India opening counts, pay), the handbook shows both and refuses a fake average.",
            "Candidate-reported interview rounds are useful for practice and are never described as official policy.",
            "Model prices and IDs will change; re-read vendor pages before an interview.",
        ]
    )
    b.h2("Document control")
    b.table(
        ["Item", "Value"],
        [
            ["Title", "Forward Deployed Engineer & Agentic AI Engineer Handbook"],
            ["Version", "1.0"],
            ["Research date", "15 September 2026"],
            ["Compiler", "Grok (xAI) study copy for the commissioning reader"],
            ["Next refresh triggers", "New MCP spec; model-family rename; OWASP list change; your target employer’s careers page"],
        ],
        col_widths=[2800, 6560],
    )
    b.p(
        "End of handbook. Update the table of contents in Word (F9). Then do Lab 01 the same day — reading without artifacts will not move the readiness score."
    )
