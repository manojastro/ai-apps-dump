"""Parts I–IV: career/market, engineering foundations, AI foundations, GenAI."""


def cover(b):
    b.doc.add_paragraph()
    for _ in range(3):
        b.doc.add_paragraph()
    t = b.doc.add_paragraph()
    t.alignment = 1
    r = t.add_run("FORWARD DEPLOYED ENGINEER")
    from handbook.theme import set_run_font, NAVY
    set_run_font(r, size=14, bold=True, color=NAVY)
    t2 = b.doc.add_paragraph()
    t2.alignment = 1
    r2 = t2.add_run("& AGENTIC AI ENGINEER")
    set_run_font(r2, size=14, bold=True, color=NAVY)
    t3 = b.doc.add_paragraph()
    t3.alignment = 1
    r3 = t3.add_run("Career, Production, and Interview Handbook")
    set_run_font(r3, size=22, bold=True, color=NAVY)
    sub = b.doc.add_paragraph()
    sub.alignment = 1
    rs = sub.add_run(
        "A practical textbook for becoming job-ready in Forward Deployed / AI Deployment\n"
        "Engineering and Generative / Agentic AI Engineering"
    )
    set_run_font(rs, size=12, italic=True, color="1F6F8B")
    meta = [
        ("Version", "1.0"),
        ("Research date", "15 September 2026"),
        ("Access / compilation date", "15 September 2026"),
        ("Primary geographies", "India (Bengaluru, Hyderabad, Chennai, Pune, Gurugram, Noida, Mumbai, Kochi, Coimbatore, India-remote) with global comparison"),
        ("Document type", "Technical career handbook — study copy"),
    ]
    b.doc.add_paragraph()
    rows = [[k, v] for k, v in meta]
    b.table(["Field", "Value"], rows, col_widths=[3120, 6240])
    b.warn(
        [
            "This handbook is evidence-based where sources exist and explicitly labeled where they do not.",
            "Job-market counts come from a public FDE-title census (Plank, observed 12 Sep 2026, N=1,333) plus inspected official postings. They are not a complete universe of AI jobs.",
            "India compensation figures in the press conflict with each other. They are cited as secondary reports, not as a salary guarantee.",
            "Interview loops described as Official are from company career pages. Loops described as Candidate-reported are from public candidate write-ups and may vary by team.",
            "Product names and model IDs are those published on vendor docs as of 15 Sep 2026 and will change.",
        ]
    )


def front_matter(b):
    b.page_break()
    b.h1("How to use this handbook")
    b.p(
        "This book is written for an engineer who wants to become employable, not merely well-read. "
        "Each major topic is taught at four depths: understand it, explain it in an interview, implement it, "
        "and operate it in a customer or production environment. Cross-references replace repeated lectures."
    )
    b.h2("Who this is for")
    b.bullets(
        [
            "Software engineers moving into AI deployment or applied GenAI.",
            "ML engineers who can train or prompt models but have not shipped an enterprise system.",
            "Consultants and customer engineers who need production AI depth.",
            "Hiring managers who need a shared language for FDE vs GenAI vs Agentic roles.",
        ]
    )
    b.h2("How the book is organized")
    b.p(
        "Parts I–II establish the career map and the software foundation employers actually test. "
        "Parts III–V are the AI core: models, RAG, agents, MCP, interoperability. "
        "Parts VI–VIII are production and customer work: security, cloud, FDE lifecycle. "
        "Parts IX–XII are practice: system design, labs, projects, interviews, and a 12-week / 90-day plan."
    )
    b.h2("Priority labels used throughout")
    b.table(
        ["Label", "Meaning", "What to do"],
        [
            ["P0", "Mandatory before applying seriously", "Build and explain without notes"],
            ["P1", "High priority before onsite loops", "Independent builder depth"],
            ["P2", "Differentiator", "Have one strong story or lab"],
            ["P3", "Specialist / later", "Learn when the role demands it"],
            ["L0–L4", "Awareness → working → builder → production → expert", "Match depth to the role column in the skill matrix"],
        ],
        col_widths=[1560, 3900, 3900],
    )
    b.h2("What this version does not pretend to be")
    b.bullets(
        [
            "It is not a dump of 1,000 fully scripted interview answers. High-frequency questions are expanded; the rest is a drill bank you should answer out loud.",
            "It does not invent adoption rates, headcount, or unpublished salary medians.",
            "It does not recommend learning every agent framework. Two are recommended for deep skill; the rest for literacy.",
            "It is not legal, immigration, or compensation advice.",
        ]
    )
    b.page_break()
    b.h1("Table of contents")
    b.p(
        "In Microsoft Word: click the field below, then press F9 (or right-click → Update Field → Update entire table)."
    )
    b.toc()


def part1(b):
    b.page_break()
    b.h1("Part I — Career and market")
    b.h2("1. Executive summary")
    b.p(
        "By September 2026 the scarce skill in enterprise AI is not ‘knowing models.’ It is taking a frontier or open model, "
        "a customer’s messy systems, and a vague business goal, then leaving behind a production path with identity, evaluation, "
        "and an owner. That is the Forward Deployed Engineer (FDE) job. The overlapping GenAI / Agentic AI engineer job is to "
        "build the productized version of the same stack: RAG, tools, agents, evals, and platform controls that many customers can run."
    )
    b.p(
        "The FDE title spread far beyond Palantir. A public census of roles whose titles contain the forward-deployed family "
        "counted 1,333 open roles across 565 companies on 12 September 2026 (Plank FDE census, CC BY 4.0). Databricks (121) and "
        "Palantir (75) were the largest named posters in that snapshot, followed by Salesforce (26), OpenAI (21), and Cohere (20). "
        "The United States still dominates titled FDE demand (728 of 1,333). Only 29 listings in that census were India-located or India-remote. "
        "That does not mean India has no work — it means India more often hires the same work under other titles (Applied AI, GenAI, "
        "AI Solutions, Customer Engineer, ‘embedded engineer’), and some IT-services firms have relabeled consultants as FDEs."
    )
    b.must(
        [
            "FDE is a product-engineering job that happens to sit with the customer, not a rebranded staff-aug consultant.",
            "GenAI/Agentic engineers own the reusable platform; FDEs own a specific customer outcome and feed the platform.",
            "Python + production APIs + RAG + tool-calling agents + identity/authorization-before-retrieval is the shared P0 stack.",
            "MCP (current spec 2026-07-28) is the tool/context protocol. A2A v1.0 is the agent-to-agent protocol. Learn both conceptually; implement MCP first.",
            "Do not let a model decide authorization, payments, deletion, or privilege escalation.",
        ]
    )
    b.h3("Final stack recommendations (evidence-backed)")
    b.table(
        ["Decision", "Primary", "Secondary", "Why"],
        [
            ["Language", "Python", "TypeScript", "Near-universal in inspected JDs; TS for UI/Node integrations"],
            ["API framework", "FastAPI", "Node (Nest/Express) if the customer is JS-native", "Async, OpenAPI, typing"],
            ["Database", "PostgreSQL + pgvector", "Redis", "One system for OLTP, JSONB, vectors"],
            ["Vector store default", "pgvector", "Qdrant or OpenSearch if ops already run them", "Fewer moving parts; hybrid SQL+vector"],
            ["Agent runtime to learn deeply", "LangGraph", "OpenAI Agents SDK or Google ADK", "Durable state + HITL; strong job signal"],
            ["RAG default", "Hybrid (BM25 + dense) + rerank + ACL pre-filter", "Graph RAG only when relations are the product", "Production reliability over novelty"],
            ["Cloud to master", "AWS", "Azure if targeting MSFT/enterprise India GCCs", "Bedrock + AgentCore + broad FDE demand"],
            ["Containers", "Docker → Kubernetes literacy", "Cloud Run / ECS / ACA first for personal projects", "K8s is interview + enterprise; serverless ships faster"],
            ["Observability", "OpenTelemetry + LangSmith or Langfuse", "Phoenix for local eval", "Traces over print-debugging"],
            ["Eval", "Golden sets + RAGAS/DeepEval + online traces", "LLM-as-judge only with human calibration", "Separate retrieval from generation"],
            ["Security baseline", "OWASP GenAI LLM Top 10 2026 + Agentic Top 10", "NIST AI RMF mapping", "Current shared vocabulary"],
            ["Certifications", "One cloud associate/professional if you lack cloud proof", "Skip pile-on AI vendor badges", "Projects beat certs for these roles"],
        ],
        col_widths=[1800, 2520, 2520, 2520],
    )

    b.h2("2. Role definitions")
    b.h3("Forward Deployed Engineer / Forward Deployed Software Engineer / AI Deployment Engineer")
    b.p(
        "Palantir’s public FDSE posting still supplies the canonical definition: work directly with customers to understand "
        "their highest-value problems and design and implement solutions that use data against them. The same posting compares "
        "the job to a startup CTO — small teams, end-to-end ownership, architecture conversations, data wrangling, custom apps, "
        "and executive conversations in the same week. Databricks describes FDEs as engineers who embed with strategic customers "
        "to design and deliver custom full-stack applications on the Data Intelligence Platform, owning architecture from data "
        "ingestion through ML/AI to user-facing apps, then feeding accelerators back into product. OpenAI’s FDE postings (SF/NYC/Seattle "
        "aggregators, September 2026) add a frontier-model twist: own discovery, scoping, system design, build, and production rollout; "
        "measure success by production adoption and eval-driven feedback into research and product; travel up to 50%."
    )
    b.table(
        ["Slice of the job", "What good looks like", "What failure looks like"],
        [
            ["Discovery", "Turns ‘we want an AI assistant’ into data, ACL, latency, and success metrics", "Builds a chatbot on the first meeting’s nouns"],
            ["Architecture", "Draws the smallest system that can go to production", "Copies a 12-box reference diagram into a 3-week pilot"],
            ["Build", "Ships a thin vertical slice in days, instrumented", "Disappears for a sprint and demos a notebook"],
            ["Integration", "Auth, networks, data contracts, idempotent writes", "CSV upload ‘for now’ that becomes the production path"],
            ["Adoption", "Named users, workflow change, training, fallback", "A URL nobody opens after the steering committee"],
            ["Feedback to product", "Reproducible evals and feature requests with evidence", "Anecdotes in a Slack channel"],
        ],
        col_widths=[1800, 3780, 3780],
    )
    b.h3("GenAI Engineer / LLM Engineer / AI Application Engineer")
    b.p(
        "These titles own the application layer around models: prompt and context engineering, structured output, RAG, evaluation, "
        "cost/latency, and product features. They usually sit inside a product org rather than on a customer site. The work is still "
        "software engineering. Employers who say ‘GenAI Engineer’ and then list only notebooks are not hiring for production; treat "
        "those JDs as weaker signals."
    )
    b.h3("Agentic AI Engineer / AI Agent Engineer")
    b.p(
        "Agentic roles assume the system will call tools, maintain state, and sometimes coordinate multiple workers. Cohere’s "
        "Forward Deployed Engineer, Agentic Platform posting (accessed September 2026) is a clean specimen: production Python, "
        "RAG and agents that plan/execute (ReAct or Plan-and-Execute), vector databases, orchestration frameworks, and evaluation "
        "of accuracy, safety, and latency — not trial-and-error prompting. Google ADK (adk.dev) and OpenAI’s Agents API/SDK are "
        "the vendor-native ways to build the same class of system."
    )
    b.h3("Adjacent titles you will see on India boards")
    b.table(
        ["Title you will search", "Usually maps to", "Watch-out"],
        [
            ["Applied AI Engineer", "GenAI app + light FDE", "Sometimes means classical ML"],
            ["AI Solutions Engineer / Architect", "Pre-sales + light build, or true FDE", "Ask for % time coding"],
            ["Customer Engineer — AI", "Google/cloud CE; demos + architecture", "May not own production code"],
            ["Implementation Consultant", "Config of a packaged product", "Weak FDE signal if no engineering bar"],
            ["LLMOps / AgentOps / MLOps", "Platform reliability for models/agents", "P1 for platform teams, P2 for FDE IC"],
            ["AI Platform Engineer", "Internal gateway, eval, routing, tenancy", "High leverage, fewer customer days"],
        ],
        col_widths=[2800, 3280, 3280],
    )

    b.h2("3. Role comparison")
    b.table(
        ["Dimension", "Product SWE", "FDE / FDSE", "Solutions Eng / CE", "Solutions Architect", "GenAI / Agentic Engineer"],
        [
            ["Primary success metric", "Product roadmap shipped", "Customer outcome in production", "Pipeline + technical win", "Reference architecture adopted", "App quality, evals, cost"],
            ["Where you sit", "Internal team", "Customer site / hybrid travel", "Pre-sales", "Pre-sales / advisory", "Product or platform team"],
            ["Code ownership", "Deep in one codebase", "Thin slices across their stack + yours", "POCs, often discarded", "Diagrams, sometimes POCs", "Deep in the AI app/platform"],
            ["Ambiguity", "Ticketed", "Extreme; you invent the ticket", "Scoped to RFP", "Scoped to design", "Medium; product manager exists"],
            ["Customer hours / week", "Low", "High", "High (sales cycle)", "Medium", "Low–medium"],
            ["Feedback into core product", "You are the product", "Required at OpenAI/Databricks-style FDEs", "Win/loss notes", "Requirements docs", "Your own backlog"],
        ],
        col_widths=[1560, 1560, 1560, 1560, 1560, 1560],
    )
    b.interview(
        [
            "If an interviewer asks ‘why FDE not SWE?’, do not say ‘I like people.’ Say: I want ownership of an outcome under constraints I do not control — data, identity, politics, latency — and I want that work to change the product.",
            "If they ask ‘why not consulting?’, say: I ship production software on the company’s platform and return field evidence. I am not billed by the hour to configure someone else’s product.",
        ]
    )

    b.h2("4. 2026 job market")
    b.h3("Global FDE-title census (primary quantitative source)")
    b.p(
        "Source: Plank ‘FDE Job Market’ census, observed 12 September 2026, license CC BY 4.0, count=1,333 jobs. "
        "This is a census of titles in the forward-deployed family, not of all AI engineering jobs. Access date for this handbook: 15 September 2026."
    )
    b.table(
        ["Cut", "N", "Notes"],
        [
            ["All FDE-family titles", "1,333", "565 unique companies"],
            ["Title contains ‘Forward Deployed’", "1,297", "The label has become the brand"],
            ["United States region", "728", "Still the center of titled demand"],
            ["UK & Europe", "198", ""],
            ["Asia-Pacific", "94", "Includes a thin India slice"],
            ["India location / India-remote in census", "29", "Bengaluru is the modal city"],
            ["With a numeric salary band", "388", "Almost none of the India rows include pay"],
            ["US salary-band midpoint (n=324)", "median $196k; p25 $165k; p75 $232.5k", "Midpoint of posted min/max, not total comp; range $80k–$400k in this cut"],
            ["Seniority: mid / unspecified", "935", "Title inflation; read the JD"],
            ["Senior", "195", ""],
            ["Leadership", "85", "Head/Director/Manager of FDE is now a real org"],
            ["Staff / Principal", "57", ""],
            ["Early career", "61", "Palantir new-grad FDSE + Salesforce early-career FDE exist"],
            ["Vertical: enterprise software", "741", ""],
            ["Data & AI platforms", "164", ""],
            ["Defense & data platforms", "108", "Clearance-heavy US"],
            ["Foundation models", "59", "Labs hiring deployers, not only researchers"],
        ],
        col_widths=[3120, 3120, 3120],
    )
    b.h3("Largest named employers in the census")
    b.table(
        ["Company", "FDE-titled rows", "What the titles look like"],
        [
            ["Databricks", "121", "Sr FDE by industry vertical; AI Engineer — FDE; India remote + Bengaluru"],
            ["Palantir", "75", "FDSE commercial & USG; intern/new-grad; infrastructure; enablement"],
            ["Salesforce", "26", "Agentforce / Data360 FDE; early career"],
            ["OpenAI", "21", "Core FDE plus Healthcare and Legal tracks; multi-city"],
            ["Cohere", "20", "FDE, Agentic Platform — explicitly agents + evals"],
            ["ElevenLabs", "18", "Voice AI deployments"],
            ["Scale AI", "10", "GenAI FDE; public sector; India row present"],
            ["Mistral AI", "10", "Applied AI, Forward Deployed ML Engineer"],
            ["Anthropic", "7", "FDE + FDE management"],
            ["Microsoft", "6", "FDE software / industry"],
            ["MongoDB", "6", "Forward Deployed AI Engineer; Staff FDE Gurugram"],
            ["Deloitte", "6", "FDE attached to AWS, Palantir, Google, Microsoft"],
        ],
        col_widths=[2200, 1800, 5360],
    )
    b.h3("India: titled FDE vs the real market")
    b.p(
        "In the Plank snapshot, India-titled FDE employers included Databricks, DevRev, MongoDB, Scale AI, Razorpay, HackerRank, "
        "CommerceIQ, Reltio, Sarvam AI, Nanonets, Arcesium, Cartesia, and others. That is a real but small titled market. "
        "Press and staffing reports describe a much larger ‘FDE-like’ demand inside IT services, GCCs, and product companies, "
        "and they disagree on size and pay. Treat the following as secondary, not as a single official number."
    )
    b.table(
        ["Source (label)", "Claim", "How to use it"],
        [
            ["Plank census 12 Sep 2026 — Verified listing count", "29 India / India-remote FDE-titled jobs in a 1,333 global titled census", "Best count for the literal title"],
            ["Mint, 15 Sep 2026, citing FDE Academy study", "Demand 95% vs supply 45%; indicative medians ₹32L / ₹55L / ₹88L / ₹1.55 Cr by experience band", "One academy report; ₹1.55 Cr is the >15 years band, not a typical offer"],
            ["CIEL HR via Hindu Business Line, 3 Aug 2026", "FDE hiring +130% YoY; ~1,200 ‘fully equipped’; early ₹35–45L, experienced ₹70–90L; select ₹80L–1.4 Cr; 52 IT orgs recruiting as of Jul 2026", "Staffing-firm cut; useful directional"],
            ["India Today, 17 Jul 2026, quoting practitioners", "Bengaluru public data ~₹17 LPA average, ~₹11–36L range; senior integrations ₹50–80 LPA; TCS announced hiring up to 8,900 FDEs", "Average is far below headline maxima; TCS figure is a news report of a company plan"],
            ["Economic Times / Adecco / NLB / Xpheno, May–Jun 2026", "India openings estimates 90 to 800–1,000 depending on the firm; entry ₹18–28 LPA; senior ₹50–80 LPA", "The opening counts cannot all be true; they use different title filters"],
            ["Economic Times, 18 Jun 2026, Everest Group / NelsonHall", "IT services are bundling consultants as ‘FDE’ and diluting the Palantir-style meaning", "Believe this. Ask every services JD what you will actually code"],
        ],
        col_widths=[2800, 3760, 2800],
    )
    b.warn(
        [
            "Insufficient reliable evidence to state a single India FDE median salary. Published bands overlap but the methodologies are not public.",
            "Insufficient evidence to treat TCS’s reported 8,900 FDE hires as equivalent to Palantir-style FDSE roles.",
            "Do not quote US total-comp blog ranges ($350k–$550k) as base salary. OpenAI aggregator postings in Sep 2026 show base bands such as $185k–$300k (SF) and wider Deployment Company ranges; equity is separate and often unpublished.",
        ]
    )
    b.h3("What inspected FDE JDs actually require")
    b.p(
        "A dedicated FDE research pass (15 Sep 2026) read 24 official/ATS FDE JDs in full plus 12 additional India-board descriptions (36 unique qualification sections). "
        "In the 24 full official JDs: customer-facing work was required in 92%; Python in 67%; cloud in 50%; agents in 46%; RAG in 29%; Kubernetes in 13%. "
        "Palantir’s live FDSE posting still does not name RAG — it names coding, data, and collaboration. RAG is P0 for GenAI titles and P1 for classic FDSE unless the JD says otherwise. "
        "Only employer-posted India ATS range verified in that pass: Cartesia Bangalore Forward Deployed Engineer at ₹70–90 L plus equity. "
        "Microsoft Bangalore FDE (job 200029969) exists outside the Plank census — another reminder that titled-census N=29 undercounts India work."
    )
    b.table(
        ["Skill", "FDE JDs", "GenAI/Agentic JDs", "Priority"],
        [
            ["Python production code", "Required (Palantir lists Python/Java/C++/TS)", "Required", "P0"],
            ["Customer-facing communication", "Required (all FDE postings)", "Preferred except SE/CE hybrids", "P0 FDE / P1 GenAI"],
            ["Full-stack delivery (API + light UI)", "Required at Databricks/OpenAI FDE", "Preferred", "P0 FDE / P1 GenAI"],
            ["SQL / data wrangling", "Required", "Required for RAG/analytics agents", "P0"],
            ["LLM APIs (OpenAI, Anthropic, Gemini, Bedrock)", "Databricks JD names OpenAI/Anthropic/Gemini", "Required", "P0"],
            ["RAG + vector search", "Increasingly named; not universal on Palantir FDSE", "Required on Agentic JDs (Cohere)", "P0 GenAI / P1 FDE"],
            ["Agents / tool calling / ReAct / plan-execute", "Named on Cohere FDE; implied on OpenAI FDE", "Required for Agentic titles", "P0 Agentic / P1 others"],
            ["Evaluation frameworks", "OpenAI FDE: eval-driven feedback", "Cohere: explicit evals beyond trial-and-error", "P0"],
            ["Cloud (AWS/Azure/GCP)", "Preferred to required", "Required for platform roles", "P0–P1"],
            ["Kubernetes", "Preferred, not universal", "Preferred for platform", "P1"],
            ["Security / GRC partnership", "OpenAI FDE lists GRC/Security partners", "Required for enterprise RAG", "P0"],
            ["MCP", "Rarely in titles; rising in platform/agent JDs", "Literacy P1, implement P1–P2", "P1"],
            ["Travel 25–50%", "Named (Palantir ~25%, OpenAI up to 50%)", "Rare", "Role-dependent"],
        ],
        col_widths=[2800, 2520, 2520, 1520],
    )

    b.h3("GenAI / Agentic JD skill frequencies (inspected sample)")
    b.p(
        "Source: handbook research pass, 15 September 2026. N=50 job descriptions with extractable skill text "
        "(35 India or India-delivery, 15 global product/lab). Convenience sample of named-employer and live postings — "
        "not a random draw from Naukri headline counts. Naukri listed 10,584 ‘Generative AI Engineer’ jobs in India the same day "
        "(Bengaluru 3,974; Hyderabad 2,373); those aggregator totals are inflated by duplicates and keyword matching and are not a sample size."
    )
    b.table(
        ["Skill", "Mentioned /50", "Required /50", "Read as"],
        [
            ["Python", "49", "44", "Table stakes"],
            ["REST APIs / microservices", "38", "28", "Backend is the job"],
            ["Any hyperscaler", "41", "28", "P0 cloud literacy"],
            ["RAG", "42", "34", "Default architecture"],
            ["LangChain (umbrella)", "31", "22", "Often an OR-list brand"],
            ["LangGraph", "24", "18", "2026 agent-framework signal"],
            ["Vector DB (any)", "27", "18", "Pinecone named most (11); Qdrant 0 in this sample"],
            ["Tool calling", "21", "14", "Agentic in practice"],
            ["Docker / CI/CD", "24", "14", "P1"],
            ["Customer / partner facing", "20", "14", "FDE-adjacent even in GenAI titles"],
            ["Eval / hallucination metrics", "18", "8", "Splits serious JDs from keyword dumps"],
            ["Kubernetes", "14", "8", "Senior/platform filter, not universal"],
            ["MCP", "12", "8", "Differentiator; TCS, PwC AC, SAP, OpenAI among required"],
            ["CrewAI / AutoGen", "14 / 12", "10 / 9", "Almost always OR-list padding"],
            ["FastAPI as a brand", "10", "6", "Teach APIs, not the logo"],
            ["OpenAI Agents SDK", "4", "3", "Vendor-native, rare keyword"],
            ["Google ADK", "3", "1", "Mostly Google FDE orbit"],
            ["A2A", "2", "1", "Not market-wide"],
            ["PydanticAI", "3", "3", "Niche"],
        ],
        col_widths=[2800, 1800, 1800, 2960],
    )
    b.p(
        "Experience in the same 50: 3–6 years (16), 5–9 years (18), 8+ years (12), 1–3 years (4). "
        "India pay in GenAI JDs is usually undisclosed. Secondary: OwnYourCareer Bengaluru AI Engineer (850 records, 15 Sep 2026) median ₹24 L, mid ₹18–30 L, senior ₹35–65 L; "
        "foundit (Sep 2026) senior Bengaluru AI ₹61.7–91.3 LPA. These are AI-engineer datasets, not FDE-only."
    )

    b.h2("5. Skill demand vs hype")
    b.table(
        ["Topic", "Social media", "Job descriptions", "Production teams"],
        [
            ["Autonomous multi-agent swarms", "Constant", "Occasional", "Rare; orchestration + HITL wins"],
            ["MCP", "High in 2026", "Still uneven in JDs", "Real for tool/gateway work"],
            ["A2A", "Rising", "Rare as a hard requirement", "Emerging; know the split vs MCP"],
            ["Fine-tuning foundation models", "High", "Preferred specialist", "Usually last resort after prompt/RAG"],
            ["LangChain as a brand", "Polarized", "Named often", "LangGraph/state machines used; LC chains less so"],
            ["LeetCode hard", "High in prep culture", "Medium at Palantir/labs; lower at many FDE teams", "Decomposition > puzzles"],
            ["K8s from scratch", "High", "Preferred", "Use managed; still must debug a pod"],
            ["Computer-use / browser agents", "Very high", "Niche JDs", "Promising, high-risk, permission-gated"],
            ["Eval / traces / cost", "Under-discussed", "Increasingly explicit", "The actual job after week two"],
        ],
        col_widths=[2340, 2340, 2340, 2340],
    )

    b.h2("6. Master competency matrix")
    b.p(
        "Depth key: L0 awareness, L1 working knowledge, L2 independent builder, L3 production engineer, L4 specialist. "
        "Market: High / Med / Low based on inspected JDs + census, not a computed frequency."
    )
    rows = [
        ["Programming", "Python", "L3", "L3", "L3", "High", "P0"],
        ["Programming", "TypeScript / JS", "L2", "L1", "L1", "Med", "P1 FDE / P2 others"],
        ["SE", "Testing, typing, packaging", "L2", "L3", "L3", "High", "P0"],
        ["Backend", "FastAPI, authn/z, webhooks", "L3", "L3", "L3", "High", "P0"],
        ["Data", "SQL / PostgreSQL", "L3", "L2", "L2", "High", "P0"],
        ["Data", "Redis", "L2", "L2", "L2", "Med", "P1"],
        ["ML literacy", "Metrics, overfitting, embeddings idea", "L1", "L2", "L2", "Med", "P1"],
        ["Transformers", "Intuition + decoding", "L2", "L3", "L3", "High", "P0"],
        ["LLM APIs", "Tools, structured out, streaming, caching", "L3", "L3", "L3", "High", "P0"],
        ["Context eng.", "What enters the window and why", "L2", "L3", "L3", "High", "P0"],
        ["RAG", "Chunk, retrieve, rerank, cite, eval", "L2", "L3", "L3", "High", "P0"],
        ["Enterprise RAG", "ACL before retrieval, tenancy", "L3", "L3", "L3", "High", "P0"],
        ["Agents", "Tool loop, state, HITL", "L2", "L2", "L3", "High", "P0 Agentic"],
        ["MCP", "Server + auth + threat model", "L1", "L2", "L2", "Med-High", "P1"],
        ["A2A", "Cards, tasks, vs MCP", "L1", "L1", "L2", "Low-Med", "P2"],
        ["Security", "Injection, agency, output handling", "L3", "L3", "L3", "High", "P0"],
        ["Eval", "Offline + online", "L2", "L3", "L3", "High", "P0"],
        ["Observability", "Traces, cost, traces of tools", "L2", "L3", "L3", "High", "P0"],
        ["Cloud", "One hyperscaler well", "L3", "L2", "L2", "High", "P0"],
        ["K8s / Docker", "Ship and debug", "L2", "L2", "L2", "Med-High", "P1"],
        ["Customer discovery", "Requirements under ambiguity", "L3", "L1", "L1", "High FDE", "P0 FDE"],
        ["System design", "End-to-end AI systems", "L3", "L3", "L3", "High", "P0"],
    ]
    b.table(
        ["Domain", "Skill", "FDE", "GenAI", "Agentic", "Market", "Priority"],
        rows,
        col_widths=[1400, 2200, 1000, 1000, 1100, 1260, 1400],
    )


def part2(b):
    b.page_break()
    b.h1("Part II — Engineering foundations")
    b.h2("7. Python for these roles")
    b.p(
        "You need production Python, not tutorial Python. Palantir lists Python among first-class languages; Cohere requires "
        "clean, testable, observable, scalable Python; Databricks FDE lists Python with SQL and JVM/JS. Interview depth is "
        "‘write a client with retries and tests,’ not ‘explain metaclasses.’"
    )
    b.table(
        ["Topic", "Interview depth", "Production use"],
        [
            ["Data structures, comprehensions, typing", "Write live", "Everywhere"],
            ["dataclasses / Pydantic v2", "Model a tool argument schema", "Request validation, structured LLM output"],
            ["asyncio / httpx", "Explain event loop; write async gather", "Fan-out tool calls, streaming"],
            ["context managers, logging, env vars", "Expected", "Secrets, traces"],
            ["pytest, monkeypatch, respx/httpx mock", "Write a test in-session", "Eval harnesses too"],
            ["packaging, uv or pip-tools", "Literacy", "Reproducible customer deploys"],
            ["generators, iterators", "Medium", "Chunking streams"],
            ["GIL / threads vs process vs async", "When to pick which", "Embedding batches vs I/O"],
        ],
        col_widths=[3120, 3120, 3120],
    )
    b.code(
        """import os, asyncio, logging
from typing import Annotated
import httpx
from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger("llm")

class ChatResult(BaseModel):
    content: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)

async def complete(prompt: str, *, timeout=30.0) -> ChatResult:
    url = os.environ["LLM_URL"]
    key = os.environ["LLM_API_KEY"]
    backoff = 0.5
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(4):
            try:
                r = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": os.environ.get("LLM_MODEL", "gpt-5.6-terra"),
                          "input": prompt},
                )
                if r.status_code in {429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError("retryable", request=r.request, response=r)
                r.raise_for_status()
                data = r.json()
                return ChatResult.model_validate(data)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                log.warning("attempt %s failed: %s", attempt, exc)
                await asyncio.sleep(backoff)
                backoff *= 2
    raise RuntimeError("llm complete failed after retries")""",
        caption="Figure 7-1. The kind of Python interviewers actually want: typed, retried, logged, no secrets in code.",
    )
    b.h2("8. Software engineering")
    b.p(
        "SOLID and clean architecture matter because agent code rots into a god-loop. Keep deterministic policy "
        "(authz, spend limits, allowlists) outside the model. Keep I/O at the edges. Make every tool idempotent. "
        "Prefer explicit state machines over implicit prompt memory."
    )
    b.bullets(
        [
            "Interface: Tool.execute(args, ctx) -> ToolResult. One way to call the world.",
            "Dependency injection: pass clocks, ID generators, and HTTP clients; never hide them in globals except config.",
            "Errors: distinguish retryable vs terminal vs needs-human. Map them in traces.",
            "Reviews: require evals for prompt or retriever changes the way you require tests for code.",
        ]
    )
    b.h2("9. Backend and APIs")
    b.p(
        "An AI feature is an API with a slow, expensive, non-deterministic dependency. Design for that."
    )
    b.table(
        ["Concern", "Default choice", "Notes"],
        [
            ["Sync request/response", "POST /v1/ask with request id", "Timeouts 30–60s; else 202 + job"],
            ["Streaming", "SSE (simpler) or WebSocket", "Token stream + final usage event"],
            ["Authn", "OIDC / company SSO", "Never a long-lived user API key in a browser"],
            ["Authz", "RBAC/ABAC in your code", "Not in the prompt"],
            ["Idempotency", "Idempotency-Key on tool writes", "Agents retry"],
            ["Rate limit", "User + tenant + model budget", "Unbounded consumption is OWASP LLM06:2026"],
            ["Webhooks", "Signed, retried, DLQ", "Async tool completion"],
            ["Versioning", "Model + prompt + retriever IDs in response", "Replay and eval"],
        ],
        col_widths=[2200, 3280, 3880],
    )
    b.h2("10. Databases")
    b.p(
        "PostgreSQL is the default production database for these roles: relational integrity, JSONB, and pgvector in one place. "
        "You must write JOINs, window functions, and EXPLAIN-aware indexes. Mongo/Dynamo/Firestore appear when the customer already standardized on them — do not start there for a greenfield RAG app. "
        "Redis is P1: cache, rate limits, distributed locks, session/scratchpad, semantic cache of embeddings."
    )
    b.code(
        """-- Hybrid retrieval sketch: lexical + vector, ACL applied BEFORE ranking
SELECT d.id, d.title,
       ts_rank(d.tsv, plainto_tsquery('english', :q)) AS lex,
       1 - (d.embedding <=> :qvec) AS dens
FROM documents d
WHERE d.tenant_id = :tenant
  AND d.acl && :user_roles          -- overlap with caller's roles
  AND d.deleted_at IS NULL
ORDER BY (0.4 * ts_rank(d.tsv, plainto_tsquery('english', :q))
        + 0.6 * (1 - (d.embedding <=> :qvec))) DESC
LIMIT 50;""",
        caption="Figure 10-1. Authorization-before-retrieval in SQL. If you cannot write this, you are not enterprise-ready.",
    )
    b.h2("11. Distributed systems for AI")
    b.p(
        "AI systems fail in queues. Treat every model call and tool call as a remote service with tail latency and partial failure."
    )
    b.table(
        ["Pattern", "AI example", "Default"],
        [
            ["Timeouts", "LLM hung on long reasoning", "Hard timeout + user-visible fallback"],
            ["Retries + jitter", "429s, 503s", "Idempotent only; budget remaining tokens"],
            ["Circuit breaker", "Provider outage", "Failover model or cached answer"],
            ["Backpressure", "Ingest embedding storm", "Queue depth metric; shed load"],
            ["Exactly-once illusion", "Agent pays a vendor twice", "Idempotency keys + ledger"],
            ["Poison queue", "Bad tool args loop", "Max steps + DLQ + human"],
            ["Cache", "Prompt cache, embedding cache", "Provider prompt cache + local"],
            ["Stateful vs stateless", "Agent checkpoint vs API replica", "State in Postgres/Redis, not the pod"],
        ],
        col_widths=[2200, 3580, 3580],
    )
    b.h2("12. Data engineering (only the relevant slice)")
    b.p(
        "You will not be hired to rebuild Spark. You will be hired to get documents, tickets, and warehouse tables into a retrieval index without violating ACL or freshness. Know batch vs streaming, schema evolution, dead-lettering, and that Databricks/Snowflake/BigQuery are often the customer’s source of truth — FDE work starts at their lake, not at your laptop."
    )


def part3(b):
    b.page_break()
    b.h1("Part III — AI foundations")
    b.h2("13. ML fundamentals (conceptual)")
    b.p(
        "These roles rarely train foundation models. You still must speak precision/recall/F1, calibration, train/val/test leakage, embeddings as geometry, and why accuracy on a chat vibe-check is not an eval. Classification vs generation is the interview trap: RAG answer quality is not a single accuracy number."
    )
    b.h2("14. Deep learning (interview depth)")
    b.p(
        "A neuron is a weighted sum plus nonlinearity. Layers compose features. Loss measures error; backpropagation assigns blame; optimizers follow gradients. You should be able to say that on a whiteboard in three minutes and then move to transformers. Deriving Adam from scratch is P3."
    )
    b.h2("15. Transformers")
    b.p(
        "A transformer turns tokens into vectors, lets every token attend to others (self-attention), mixes information through feed-forward layers, and uses residuals and normalization so depth trains. Decoder-only LLMs generate the next token from previous tokens (autoregressive). Positional information tells the model order. Multi-head attention lets the model track several relationships at once."
    )
    b.table(
        ["Piece", "Intuition", "Why engineers care"],
        [
            ["Tokenization", "Text → integer IDs; messy at word edges", "Cost, multilingual, ‘token tax’ on JSON"],
            ["Embedding", "ID → vector", "Also the retrieval object"],
            ["Q/K/V attention", "Query asks, keys index, values speak", "Long context cost is attention"],
            ["Softmax / logits", "Scores → distribution over vocab", "Temperature, top-p live here"],
            ["KV cache", "Remember keys/values while decoding", "TTFT vs inter-token latency"],
            ["Context window", "Hard memory limit", "Context engineering is the job"],
        ],
        col_widths=[2200, 3580, 3580],
    )
    b.h2("16. LLM generation and current models")
    b.p(
        "Decoding: greedy is deterministic but dull; temperature flattens the distribution; top-k / top-p truncate the tail; stop sequences end early. Reasoning models spend tokens on internal deliberation (OpenAI reasoning_effort; Anthropic adaptive thinking / effort). Structured output and tool calls beat prompt-only JSON."
    )
    b.h3("OpenAI (docs accessed 15 Sep 2026)")
    b.p(
        "Flagship recommendation on developers.openai.com/api/docs/models: GPT-6 Astra for hardest work; GPT-5.6 Terra for balance; GPT-5.6 Luna for cost-sensitive volume. GPT-5.6 Sol is listed as flagship for complex professional work (alias gpt-5.6). Context windows on these flagships: 1.05M tokens; max output 128K. Responses API is the current primary API surface; Agents API/SDK, MCP connectors, prompt caching, and computer-use tools are first-class. Do not write new production code against the Assistants API."
    )
    b.table(
        ["Model ID", "Role", "Input / output (per 1M tok)", "Notes"],
        [
            ["gpt-6-astra", "Hardest reasoning/coding", "$10 / $50", "Knowledge cutoff 30 Apr 2026"],
            ["gpt-5.6-sol (gpt-5.6)", "Complex professional", "$4 / $20", "Cutoff 16 Feb 2026"],
            ["gpt-5.6-terra", "Balance", "$2 / $12", "Default workhorse candidate"],
            ["gpt-5.6-luna", "High volume / cheap", "$0.20 / $1.20", "Router target"],
        ],
        col_widths=[2340, 2340, 2340, 2340],
    )
    b.h3("Anthropic Claude (docs accessed 15 Sep 2026)")
    b.p(
        "Current lineup on platform.claude.com: start with Claude Opus 5; use Claude Fable 5.1 for demanding long-horizon agentic work; Sonnet 5 for speed/intelligence balance; Haiku 4.5 for fastest near-frontier. IDs: claude-fable-5-1, claude-opus-5, claude-sonnet-5, claude-haiku-4-5-20251001. Context 1M (Haiku 200K). Also on Bedrock, Vertex, and Microsoft Foundry under documented IDs."
    )
    b.h3("Google, Meta, Mistral, Cohere, Qwen")
    b.p(
        "Use Gemini via Vertex AI / AI Studio and Google ADK (Python, TypeScript, Go, Java, Kotlin; ADK TypeScript 2.0 GA with graph workflows). Llama remains the default self-host/open family — always pin a specific current release rather than saying ‘Llama 3’ in 2026. Mistral and Cohere remain enterprise-relevant (Cohere especially where data-residency and agentic enterprise workflows are the pitch). Qwen is a strong open-weight family in multilingual and cost-sensitive self-host. Verify the exact model ID on the provider page the week you implement; this book will rot here first."
    )
    b.h2("17. Prompt engineering")
    b.p(
        "Prompts are specifications, not spells. Put durable rules in the system channel; put user-specific facts in retrieved context; put schemas in tool/structured-output definitions. Few-shot only when the format is unusual. Negative instructions (‘don’t hallucinate’) are weak compared with citations + refusal policy + retrieval. Prompt-only agents will leak authority; see Part VI."
    )
    b.h2("18. Context engineering")
    b.p(
        "Context engineering is the production name for ‘what tokens the model sees, in what order, with what budget.’ Google ADK’s docs describe treating context like source code: sessions, memory, tool outputs, and artifacts assembled so every token earns its place, with summarization and lazy-loading. That is the right mental model even if you do not use ADK."
    )
    b.numbered(
        [
            "System policy (short, versioned).",
            "Non-negotiable tools and output schema.",
            "Retrieved evidence (ACL-filtered), ranked, with source IDs.",
            "Working memory / scratchpad of this task.",
            "Recent conversation, compacted.",
            "User turn.",
        ]
    )
    b.must(
        [
            "Never dump a full CRM into the window ‘just in case.’",
            "Never put secrets in context you would not put in logs.",
            "Cache stable prefixes (policy + tool schemas) for cost; keep user PII out of those prefixes if cache is shared.",
        ]
    )


def part4(b):
    b.page_break()
    b.h1("Part IV — GenAI engineering")
    b.h2("19. Embeddings")
    b.p(
        "An embedding is a vector such that semantic similarity ≈ geometric closeness (usually cosine on L2-normalized vectors). Query and document encoders may differ (asymmetric retrieval). Dimensions are a storage/quality tradeoff. Domain shift kills naive cosine: acronyms, legal terms, tickets. Select embedding models with a retrieval eval on your corpus, not a leaderboard screenshot."
    )
    b.h2("20. Vector search")
    b.p(
        "Exact kNN is brute force. ANN (HNSW, IVF) trades recall for latency. Always keep metadata filters (tenant, ACL, time) in the index path, not as an afterthought. Hybrid retrieval (BM25 + dense) is the 2026 production default for enterprise knowledge. Reciprocal rank fusion is a simple combiner; a cross-encoder reranker is the quality upgrade if latency allows."
    )
    b.h2("21. Vector databases — selection")
    b.table(
        ["Store", "When it is the right default", "Job-market note"],
        [
            ["pgvector", "You already need Postgres; < tens of millions of vectors; want transactional delete/ACL", "Highest ‘just use this’ value"],
            ["OpenSearch / Elasticsearch", "Lexical+vector in a shop that already runs it", "Strong enterprise"],
            ["Qdrant", "Need a dedicated vector engine with good filters", "Common in startups"],
            ["Pinecone", "Managed, team does not want ops", "Named in many JDs; cost watch"],
            ["Weaviate / Milvus", "Scale / hybrid features; existing skill", "More platform-y"],
            ["Chroma", "Local labs", "Not a production resume centerpiece"],
        ],
        col_widths=[2200, 4480, 2680],
    )
    b.h2("22. RAG pipeline")
    b.numbered(
        [
            "Ingest: connectors, permissions preserved, incremental.",
            "Parse: PDF/HTML/Office; OCR if needed; keep layout metadata.",
            "Clean/dedup: hashes, canonical URLs, near-dupes.",
            "Chunk: see next section; store parent pointers.",
            "Embed + index lexical.",
            "Query understand: rewrite, language, filters.",
            "Retrieve hybrid → rerank → parent expand.",
            "Authorize again (defense in depth).",
            "Build context with citations.",
            "Generate with refusal if evidence is weak.",
            "Evaluate offline and in production.",
            "Feedback: thumbs, edit, reindex.",
        ]
    )
    b.h2("23. Chunking")
    b.table(
        ["Strategy", "Use", "Risk"],
        [
            ["Fixed tokens", "Baseline", "Splits meaning"],
            ["Recursive separators", "Default good start", "Still blind to semantics"],
            ["Sentence / paragraph", "Prose", "Uneven sizes"],
            ["Semantic / embedding breaks", "Narrative docs", "Cost, instability"],
            ["Parent-child / hierarchical", "Cite small, generate with parent", "Best default for manuals"],
            ["Proposition", "Factoid Q&A", "Overkill for long procedure"],
            ["Late chunking", "Long-context embedders", "Newer; eval before betting"],
        ],
        col_widths=[2800, 3280, 3280],
    )
    b.h2("24. Retrieval and reranking")
    b.p(
        "Lexical (BM25) wins on identifiers, error codes, names. Dense wins on paraphrase. Hybrid covers both. Query rewriting and multi-query help conversational ellipsis (‘that one’). Routing sends policy questions to a different corpus than HR. Cross-encoder rerankers are accurate and slow; LLM rerank is slower and should be bounded (top 20 → top 5). Always log the candidate set so you can debug ‘the model was wrong’ vs ‘the retriever never saw it.’"
    )
    b.h2("25. Advanced RAG (maturity labels)")
    b.table(
        ["Pattern", "Maturity", "Use when", "Skip when"],
        [
            ["Hybrid RAG", "Proven", "Always, unless corpus is tiny", "Never the first thing to drop"],
            ["Agentic RAG", "Growing", "Multi-step research, tool choice of corpus", "Single-shot FAQ"],
            ["Corrective / Self-RAG", "Useful", "High hallucination cost", "Tight latency budget"],
            ["Graph RAG", "Selective", "Entities/relations are the product", "Unstructured dump"],
            ["Multimodal RAG", "Growing", "Diagrams, scans", "Text-only corpus"],
            ["Permission-aware", "Mandatory in enterprise", "Any multi-user corpus", "Never skip"],
            ["Temporal RAG", "Growing", "Policies that change", "Static manuals"],
        ],
        col_widths=[2200, 1560, 2800, 2800],
    )
    b.h2("26. Enterprise RAG")
    b.must(
        [
            "Authorization happens before unauthorized tokens enter the model. Prompting ‘do not reveal other tenants’ is not a control.",
            "Row/document ACLs, tenant isolation, and audit of who retrieved what are product features.",
            "Deletion and retention must flow to the index. Stale vectors are a compliance incident.",
            "Citations must point at the chunk the model actually saw.",
        ]
    )
    b.h2("27. RAG evaluation")
    b.table(
        ["Metric", "Asks", "Typical tool"],
        [
            ["Recall@k / Hit rate", "Was the needed chunk retrieved?", "Golden questions"],
            ["MRR / nDCG / Precision@k", "Was it ranked well?", "Golden + labels"],
            ["Faithfulness / groundedness", "Did the answer stick to context?", "RAGAS, DeepEval, human"],
            ["Answer relevance", "Did it answer the question?", "Judge + human"],
            ["Citation accuracy", "Do cites support the claim?", "Human / specialized judge"],
            ["Hallucination rate", "Unsupported claims", "Offline suite + prod sampling"],
        ],
        col_widths=[2800, 3760, 2800],
    )
    b.p(
        "Build a golden set of 50–200 real questions before you tune prompts. Synthetic data can expand, not replace, that set. LLM-as-judge is a metric, not ground truth — calibrate against humans. promptfoo, LangSmith, Phoenix, and provider evals are all acceptable; pick one and wire it into CI."
    )
    b.h2("28. Fine-tuning")
    b.p(
        "Fine-tune when you need style, a stable tool-calling dialect, or a domain language the model keeps missing after RAG and examples. Do not fine-tune to ‘teach facts’ that change weekly — that is RAG. SFT, LoRA/QLoRA/PEFT are the practical methods. Distillation is a cost play. For FDE/GenAI IC roles, L1–L2 conceptual depth is enough unless the JD is a customization specialist."
    )
