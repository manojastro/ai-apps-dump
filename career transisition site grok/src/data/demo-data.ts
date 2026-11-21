import { createEmptyState } from "@/lib/empty-state";
import { nowIso } from "@/lib/ids";
import type { CareerOSState } from "@/types/career";

const T = "2026-06-15T09:00:00.000Z";
const T2 = "2026-08-01T09:00:00.000Z";
const T3 = "2026-08-20T09:00:00.000Z";

function stamp<TExtra extends object>(id: string, extra: TExtra) {
  return { id, createdAt: T, updatedAt: T2, tags: ["demo"] as string[], ...extra };
}

export function createDemoState(): CareerOSState {
  const base = createEmptyState();
  const now = nowIso();

  const skills = [
    stamp("demo_sk_python", { category: "core_python", name: "Python", sourceLearned: "Production services + focused 2026 rebuild", sourceUrl: "https://docs.python.org", summary: "Typed Python for services, agents, and evaluation harnesses.", whatNext: "Property-based tests around tool-calling adapters.", mappedRoles: ["Agentic AI Engineer", "GenAI Engineer"], status: "mastered" }),
    stamp("demo_sk_async", { category: "core_python", name: "asyncio", sourceLearned: "FastAPI + agent runtimes", sourceUrl: "", summary: "Concurrent tool execution and backpressure in agent loops.", whatNext: "Document cancellation and timeout policy.", mappedRoles: ["Agentic AI Engineer"], status: "mastered" }),
    stamp("demo_sk_pydantic", { category: "intermediate_python", name: "Pydantic", sourceLearned: "Structured output pipelines", sourceUrl: "https://docs.pydantic.dev", summary: "Schema-first tool arguments and structured generation.", whatNext: "Version schemas with compatibility tests.", mappedRoles: ["LLM Engineer"], status: "mastered" }),
    stamp("demo_sk_fastapi", { category: "intermediate_python", name: "FastAPI", sourceLearned: "Service layer for RCA platform", sourceUrl: "https://fastapi.tiangolo.com", summary: "AuthN, tracing headers, and eval webhooks.", whatNext: "Idempotent action endpoints.", mappedRoles: ["AI Solutions Engineer"], status: "in_progress" }),
    stamp("demo_sk_tools", { category: "llm_orchestration", name: "Tool calling", sourceLearned: "OpenAI-compatible tool loop", sourceUrl: "", summary: "Validated tool calls with retries and side-effect gates.", whatNext: "Human approval for mutating tools.", mappedRoles: ["Agentic AI Engineer"], status: "mastered" }),
    stamp("demo_sk_prompts", { category: "llm_orchestration", name: "Prompt architecture", sourceLearned: "Context engineering notes", sourceUrl: "", summary: "System/developer/user layers, memory, and tool docs as context.", whatNext: "Prompt diffs in CI.", mappedRoles: ["GenAI Engineer"], status: "in_progress" }),
    stamp("demo_sk_langgraph", { category: "agents", name: "LangGraph", sourceLearned: "RCA graph runtime", sourceUrl: "https://github.com/langchain-ai/langgraph", summary: "Stateful graphs with interrupt, resume, and checkpointing.", whatNext: "Multi-tenant checkpoint store.", mappedRoles: ["Agentic AI Engineer"], status: "mastered" }),
    stamp("demo_sk_multi", { category: "agents", name: "Multi-agent architecture", sourceLearned: "Investigator / SRE / critic pattern", sourceUrl: "", summary: "Specialist agents with a supervisor and shared incident memory.", whatNext: "Cost-aware routing.", mappedRoles: ["Agentic AI Engineer"], status: "in_progress" }),
    stamp("demo_sk_rag", { category: "rag", name: "Vector retrieval", sourceLearned: "Enterprise knowledge platform", sourceUrl: "", summary: "Hybrid search over runbooks, ADRs, and postmortems.", whatNext: "Per-tenant embedding isolation.", mappedRoles: ["GenAI Engineer"], status: "in_progress" }),
    stamp("demo_sk_rerank", { category: "rag", name: "Reranking", sourceLearned: "Knowledge platform v1", sourceUrl: "", summary: "Cross-encoder rerank with citation constraints.", whatNext: "Latency budget vs nDCG curve.", mappedRoles: ["GenAI Engineer"], status: "to_learn" }),
    stamp("demo_sk_rageval", { category: "rag", name: "RAG evaluation", sourceLearned: "Golden set of 80 enterprise queries", sourceUrl: "", summary: "Faithfulness and context recall on internal corpus.", whatNext: "Weekly eval gate in CI.", mappedRoles: ["GenAI Engineer"], status: "in_progress" }),
    stamp("demo_sk_docker", { category: "serving_llmops", name: "Docker", sourceLearned: "All portfolio services", sourceUrl: "", summary: "Reproducible eval and serving images.", whatNext: "Distroless runtime image.", mappedRoles: ["Cloud AI Engineer"], status: "mastered" }),
    stamp("demo_sk_obs", { category: "serving_llmops", name: "Observability", sourceLearned: "OpenTelemetry on RCA platform", sourceUrl: "", summary: "Traces for tool calls, tokens, and incident timelines.", whatNext: "SLO burn alerts on eval drift.", mappedRoles: ["AIOps Engineer"], status: "in_progress" }),
    stamp("demo_sk_cicd", { category: "serving_llmops", name: "CI/CD", sourceLearned: "Agent evaluation CI", sourceUrl: "", summary: "Prompt/model/graph diffs fail the build on eval regression.", whatNext: "Canary eval environment.", mappedRoles: ["LLM Engineer"], status: "in_progress" }),
  ];

  const competencies = base.competencies.map((c) => {
    const map: Record<string, string[]> = {
      comp_python_core: ["demo_sk_python", "demo_sk_async", "demo_sk_pydantic"],
      comp_backend: ["demo_sk_fastapi"],
      comp_tool_calling: ["demo_sk_tools"],
      comp_prompt_arch: ["demo_sk_prompts"],
      comp_agent_orch: ["demo_sk_langgraph"],
      comp_multi_agent: ["demo_sk_multi"],
      comp_rag_retrieval: ["demo_sk_rag", "demo_sk_rerank"],
      comp_rag_eval: ["demo_sk_rageval"],
      comp_observability: ["demo_sk_obs"],
      comp_llmops: ["demo_sk_docker", "demo_sk_cicd"],
    };
    return { ...c, skillIds: map[c.id] ?? c.skillIds };
  });

  const projects = [
    {
      ...stamp("demo_pr_rca", {}),
      title: "Agent-Native Production Intelligence & Autonomous RCA Platform",
      category: "AIOps" as const,
      targetRole: "AIOps Engineer",
      techStack: ["Python", "LangGraph", "OpenTelemetry", "FastAPI", "Postgres", "Redis"],
      useCase: "Enterprise production incidents: ingest telemetry, hypothesize causes, gather evidence, and propose RCA with human approval before any mutating action.",
      architectureSummary: "Supervisor graph with investigator, metric, log, and critic agents. Checkpoints after each tool batch. HITL gate before runbook execution. Traces exported to OTel.",
      githubUrl: "https://github.com/demo/rca-platform",
      liveUrl: "https://rca-demo.example.com",
      starPitch: "Cut mean-time-to-hypothesis on recurring production incidents by encoding SRE reasoning as an evaluated agent graph — not a ticket bot.",
      status: "in_progress" as const,
      maturity: "Portfolio Ready" as const,
      evaluationNotes: "40 historical incidents replayed. Trajectory success 71%. False-action rate 4% with HITL on.",
      testingNotes: "Contract tests for tools. Replay fixtures for 12 incident classes.",
      safetyNotes: "No production mutation without dual-control. Prompt-injection tests on log text. Secret redaction in prompts.",
      observabilityNotes: "Per-node latency, token cost, tool error rate, human override rate.",
      failureHandlingNotes: "Tool timeout → retry with backoff → degrade to read-only summary. Checkpoint resume after crash.",
      documentationNotes: "Architecture README, threat model, eval protocol.",
      interviewDefense30s: "I built an agent graph that investigates production incidents with evidence and a human gate — evaluated on historical RCA, not a chatbot.",
      interviewDefense2m: "The system is a stateful LangGraph: ingest, hypothesize, retrieve evidence, critique, then stop for human approval. Evaluation is replay-based. Safety is non-negotiable because tools can touch production.",
      interviewDefenseDeep: "Why agents vs rules: long-tail incidents. Why not a single LLM: tool routing and critique. Failure: log-injection, cost blowups, overconfident actions. Redesign: cheaper classifier router + specialist graphs.",
    },
    {
      ...stamp("demo_pr_db", {}),
      title: "Autonomous Database Performance Tuning Agent",
      category: "Agents" as const,
      targetRole: "Agentic AI Engineer",
      techStack: ["Python", "LangGraph", "Postgres", "pg_stat_statements"],
      useCase: "Explain query regressions and propose index/config changes with measured before/after and rollback.",
      architectureSummary: "Read-only diagnosis graph plus a gated change planner. Never applies DDL without approval.",
      githubUrl: "https://github.com/demo/db-tuner-agent",
      liveUrl: "",
      starPitch: "Turn slow-query archaeology into a repeatable, evaluated agent workflow with rollback.",
      status: "in_progress" as const,
      maturity: "Prototype" as const,
      evaluationNotes: "12 slow-query cases labeled by a DBA.",
      testingNotes: "SQL sandbox only.",
      safetyNotes: "Read-only by default. DDL requires approval token.",
      observabilityNotes: "Query plan capture.",
      failureHandlingNotes: "Abort if EXPLAIN cost missing.",
      documentationNotes: "Design notes.",
      interviewDefense30s: "A diagnosis agent for query regressions with a hard human gate on schema changes.",
      interviewDefense2m: "",
      interviewDefenseDeep: "",
    },
    {
      ...stamp("demo_pr_eval", {}),
      title: "Enterprise Agent Evaluation & CI Platform",
      category: "Agents" as const,
      targetRole: "Agentic AI Engineer",
      techStack: ["Python", "pytest", "GitHub Actions", "Docker"],
      useCase: "Treat agent graphs like software: golden tasks, trajectory scores, cost budgets, and regression gates on every PR.",
      architectureSummary: "Eval runner as CI job. Stores traces, scores, and diffs. Blocks merge on quality or cost SLO breach.",
      githubUrl: "https://github.com/demo/agent-eval-ci",
      liveUrl: "https://eval-ci.example.com",
      starPitch: "If it is not evaluated in CI, it is not an engineering system.",
      status: "deployed" as const,
      maturity: "Production Grade" as const,
      evaluationNotes: "Self-hosting: the platform evaluates the RCA agent. 80 tasks, nightly + PR.",
      testingNotes: "Runner unit tests, flake quarantine.",
      safetyNotes: "Eval tenants isolated. No prod credentials in CI.",
      observabilityNotes: "Eval dashboards: pass rate, cost, latency, flake.",
      failureHandlingNotes: "Quarantine flaky tasks rather than hiding regressions.",
      documentationNotes: "Protocol + contribution guide.",
      interviewDefense30s: "I built CI that fails the build when an agent regresses on quality or cost.",
      interviewDefense2m: "Golden tasks, trajectory eval, cost budgets, and PR gates. This is how I talk about LLMOps in interviews.",
      interviewDefenseDeep: "Judge-model caveats, human labels, version pinning, and why eval is the real product.",
    },
    {
      ...stamp("demo_pr_rag", {}),
      title: "Enterprise Knowledge Intelligence RAG Platform",
      category: "RAG" as const,
      targetRole: "GenAI Engineer",
      techStack: ["Python", "FastAPI", "pgvector", "rerankers"],
      useCase: "Grounded answers over architecture docs, postmortems, and runbooks with citations and refusal when unsupported.",
      architectureSummary: "Hybrid retrieval, rerank, citation assembler, and faithfulness eval. No answer without span-level support.",
      githubUrl: "https://github.com/demo/enterprise-rag",
      liveUrl: "",
      starPitch: "A knowledge system that refuses to hallucinate operational guidance.",
      status: "in_progress" as const,
      maturity: "Prototype" as const,
      evaluationNotes: "80 query golden set. Faithfulness 0.78.",
      testingNotes: "Chunking fixtures.",
      safetyNotes: "ACL filters on retrieval. PII scrubber.",
      observabilityNotes: "Retrieval hit rate, refusal rate.",
      failureHandlingNotes: "Refuse on low support score.",
      documentationNotes: "Indexing guide.",
      interviewDefense30s: "Hybrid RAG with citation-or-refuse, evaluated on an internal golden set.",
      interviewDefense2m: "",
      interviewDefenseDeep: "",
    },
    {
      ...stamp("demo_pr_sec", {}),
      title: "AI Security Investigation Agent",
      category: "Security_LLMOps" as const,
      targetRole: "AI Security Engineer",
      techStack: ["Python", "LangGraph", "OpenTelemetry"],
      useCase: "Investigate prompt-injection, tool-abuse, and data-exfil attempts against internal LLM apps.",
      architectureSummary: "Detector + investigator + reporter. Never auto-blocks in v1; produces a case file.",
      githubUrl: "https://github.com/demo/ai-sec-agent",
      liveUrl: "",
      starPitch: "Security cases with evidence trails, not a regex dashboard.",
      status: "planned" as const,
      maturity: "Prototype" as const,
      evaluationNotes: "",
      testingNotes: "",
      safetyNotes: "Read-only investigation.",
      observabilityNotes: "",
      failureHandlingNotes: "",
      documentationNotes: "",
      interviewDefense30s: "",
      interviewDefense2m: "",
      interviewDefenseDeep: "",
    },
  ];

  const evidence = [
    stamp("demo_ev_rca_arch", { title: "RCA platform architecture diagram", type: "Architecture Diagram", url: "https://rca-demo.example.com/arch", description: "Graph, HITL, and telemetry planes.", projectId: "demo_pr_rca", skillIds: ["demo_sk_langgraph", "demo_sk_obs"], competencyIds: ["comp_agent_orch", "comp_observability"], mappedRoleIds: ["role_aiops", "role_agentic"], strength: "Strong", lastVerifiedAt: T3 }),
    stamp("demo_ev_eval", { title: "Agent eval CI report", type: "Evaluation Report", url: "https://eval-ci.example.com/report", description: "Nightly scores for RCA graph.", projectId: "demo_pr_eval", skillIds: ["demo_sk_cicd"], competencyIds: ["comp_agent_eval", "comp_llm_eval"], mappedRoleIds: ["role_agentic"], strength: "Strong", lastVerifiedAt: T3 }),
    stamp("demo_ev_bench", { title: "Incident replay benchmark", type: "Benchmark", url: "https://rca-demo.example.com/bench", description: "40 incident replay suite.", projectId: "demo_pr_rca", skillIds: ["demo_sk_langgraph"], competencyIds: ["comp_agent_eval"], mappedRoleIds: ["role_aiops"], strength: "Usable" }),
    stamp("demo_ev_git_eval", { title: "Eval platform GitHub", type: "GitHub Repository", url: "https://github.com/demo/agent-eval-ci", description: "Public eval runner.", projectId: "demo_pr_eval", skillIds: ["demo_sk_cicd"], competencyIds: ["comp_llmops"], mappedRoleIds: ["role_agentic"], strength: "Strong" }),
    stamp("demo_ev_live", { title: "Eval CI live demo", type: "Live Demo", url: "https://eval-ci.example.com", description: "Deployed eval dashboard.", projectId: "demo_pr_eval", skillIds: [], competencyIds: ["comp_llmops"], mappedRoleIds: ["role_agentic"], strength: "Strong" }),
  ];

  const applications = [
    stamp("demo_job_1", { company: "DEMO · Contoso GCC", tier: "GCC", role: "Agentic AI Engineer", platform: "Referral", jobUrl: "https://careers.example.com/agentic", referralContact: "A. Mentor", referralContactId: "demo_ct_1", resumeVariantId: "demo_cv_agentic", dateApplied: "2026-08-12", nextFollowUpDate: "2026-08-19", status: "Technical", notes: "DEMO record. Strong graph + eval conversation.", location: "Bengaluru", interest: 5, jdCaptured: true, evidenceReviewed: true, referralAttempted: true, companyId: "demo_co_1", campaignId: "demo_camp_1" }),
    stamp("demo_job_2", { company: "DEMO · Nimbus AI", tier: "AI Startup", role: "GenAI Engineer", platform: "LinkedIn", dateApplied: "2026-08-18", nextFollowUpDate: "2026-08-25", status: "Applied", notes: "DEMO record.", location: "Hyderabad", interest: 4, jdCaptured: true, evidenceReviewed: true, referralAttempted: false, resumeVariantId: "demo_cv_genai", companyId: "demo_co_2" }),
    stamp("demo_job_3", { company: "DEMO · Himalaya Systems", tier: "Enterprise IT", role: "AIOps Engineer", platform: "Naukri", dateApplied: "2026-07-30", nextFollowUpDate: "2026-08-06", status: "Rejected", notes: "DEMO record.", outcomeReason: "No Response", location: "Chennai", interest: 3, jdCaptured: false, evidenceReviewed: false, referralAttempted: false }),
  ];

  const state = {
    ...base,
    ui: { onboardingComplete: true, demoMode: true, privacyMode: false, sidebarCollapsed: false },
    meta: { updatedAt: now, lastSavedAt: now },
    competencies,
    skills,
    projects,
    evidenceArtifacts: evidence,
    applications,
    contacts: [
      stamp("demo_ct_1", { name: "A. Mentor", designation: "Staff AI Engineer", company: "Contoso GCC", medium: "LinkedIn", contactDate: "2026-08-01", outreachFormulaUsed: true, status: "Mentorship Active", helpfulRating: "High", keyTakeaway: "Lead with eval and deployment, not course lists.", nextTouchpointDate: "2026-09-10", linkedinUrl: "https://linkedin.com/in/demo" }),
      stamp("demo_ct_2", { name: "B. Recruiter", designation: "Technical Recruiter", company: "Nimbus AI", medium: "Email", contactDate: "2026-08-16", outreachFormulaUsed: true, status: "Connected", helpfulRating: "Medium", keyTakeaway: "Wants architecture one-pager.", nextTouchpointDate: "2026-08-28" }),
    ],
    certifications: [
      stamp("demo_cert_1", { name: "Azure AI Engineer Associate", provider: "Microsoft", code: "AI-102", status: "Studying", examDate: "2026-10-12", whatNext: "Finish agent evaluation case study first.", mappedTrack: "Option A: Azure Enterprise" }),
    ],
    starStories: [
      stamp("demo_star_1", { category: "Outage/RCA", title: "Major payment latency incident", situation: "Checkout p95 latency tripled during a regional event.", task: "Lead technical RCA across app, data, and edge.", action: "Built a timeline from traces, isolated a cache stampede, and introduced load-shed + jittered refresh.", result: "Restored SLO in 70 minutes. Recurrence dropped to zero over the next quarter.", techNotes: "Observability, capacity, human coordination — now encoded in the RCA agent graph." }),
      stamp("demo_star_2", { category: "LLM Trade-Offs", title: "Why the RCA graph is not a single prompt", situation: "A stakeholder asked for one mega-prompt to 'do RCA'.", task: "Defend a graph architecture.", action: "Compared single-call vs graph on 12 incidents: tool routing, critique, and HITL.", result: "Graph reduced unsafe action proposals from 22% to 4%.", techNotes: "Evaluation decided the architecture." }),
    ],
    researchTopics: [
      stamp("demo_rs_1", { title: "KV cache and long context", coreConcept: "Attention over growing prefixes is dominated by KV memory and bandwidth.", mathOrFormula: "KV size ≈ layers × 2 × seq × d_head × precision", tradeOffs: "Windowing vs quality; quantization vs recall.", interviewTalkingPoints: "I explain cost of long RCA traces and why retrieval beats stuffing logs.", isMastered: true, category: "inference" }),
      stamp("demo_rs_2", { title: "Agent evaluation vs LLM-as-judge", coreConcept: "Judges are noisy; golden tasks and trajectory checks are the backbone.", mathOrFormula: "Cohen's κ between judge and human", tradeOffs: "Cheap judges vs expensive humans.", interviewTalkingPoints: "CI gates use mixed signals, not a single judge score.", isMastered: true, category: "agent evaluation" }),
    ],
    weeklySprints: [
      stamp("demo_sp_1", { weekStart: "2026-09-01", title: "Week 6 — Deploy eval gates", objectives: ["Ship eval CI dashboard", "RCA replay 40/40", "6 quality applications"], completedObjectives: ["Ship eval CI dashboard"], learningHours: 6, applicationsSubmitted: 2, networkingActions: 2, interviewSessions: 1, buildingHours: 11, jobSearchHours: 4, availableHours: 20, retrospective: "", nextWeekPriority: "Deploy RCA v1 with HITL on" }),
    ],
    tasks: [
      stamp("demo_tk_1", { title: "Deploy RCA v1 with HITL gate", category: "Project", priority: "Critical", dueDate: "2026-09-08", completed: false, linkedEntityId: "demo_pr_rca", estimatedMinutes: 240 }),
      stamp("demo_tk_2", { title: "Finish benchmark write-up for incident replay", category: "Project", priority: "High", dueDate: "2026-09-06", completed: false, linkedEntityId: "demo_pr_rca", estimatedMinutes: 120 }),
      stamp("demo_tk_3", { title: "Practice multi-agent evaluation questions", category: "Interview", priority: "High", dueDate: "2026-09-05", completed: false, estimatedMinutes: 60 }),
    ],
    interviewQuestions: [
      stamp("demo_iq_1", { category: "Agents", question: "When would you not use an agent?", answer: "When the control flow is a short deterministic DAG with stable tools and no branching uncertainty. Agents add failure modes.", confidence: 4, lastPracticed: "2026-08-28", nextReviewDate: "2026-09-07", mastered: false }),
      stamp("demo_iq_2", { category: "RAG", question: "How do you evaluate RAG beyond 'it looks good'?", answer: "Golden set, faithfulness, context precision/recall, refusal rate, and latency/cost. Citations required.", confidence: 3, mastered: false }),
      stamp("demo_iq_3", { category: "System Design", question: "Design an evaluated agent platform.", answer: "Graph runtime, tool sandbox, HITL, tracing, eval CI, cost gates, rollback.", confidence: 4, mastered: false }),
      stamp("demo_iq_4", { category: "Behavioral", question: "Why senior AI engineering rather than an entry-level LLM bootcamp role?", answer: "8.5 years of production operations: incident reasoning, reliability, stakeholders. I now encode that as evaluated AI systems.", confidence: 5, mastered: true }),
    ],
    learningSessions: [
      stamp("demo_ls_1", { skillId: "demo_sk_langgraph", date: "2026-08-21", durationMinutes: 180, activity: "Coding", notes: "HITL interrupt + resume on RCA graph." }),
      stamp("demo_ls_2", { skillId: "demo_sk_rageval", date: "2026-08-22", durationMinutes: 90, activity: "Lab", notes: "Faithfulness scoring." }),
      stamp("demo_ls_3", { date: "2026-08-23", durationMinutes: 60, activity: "Interview Practice", notes: "Agent vs DAG." }),
      stamp("demo_ls_4", { date: "2026-08-24", durationMinutes: 120, activity: "Course", notes: "Azure AI-102 module — paused to ship eval CI." }),
    ],
    projectMilestones: [
      stamp("demo_ms_1", { projectId: "demo_pr_rca", title: "Graph + HITL", category: "Architecture", status: "Complete", notes: "Done" }),
      stamp("demo_ms_2", { projectId: "demo_pr_rca", title: "Replay eval 40 incidents", category: "Evaluation", status: "In Progress", notes: "32/40" }),
      stamp("demo_ms_3", { projectId: "demo_pr_rca", title: "Public demo", category: "Deployment", status: "In Progress", notes: "" }),
      stamp("demo_ms_4", { projectId: "demo_pr_eval", title: "Nightly + PR gates", category: "Deployment", status: "Complete", notes: "Live" }),
    ],
    architectureDecisions: [
      stamp("demo_adr_1", { projectId: "demo_pr_rca", title: "Graph over single prompt", context: "Incidents are multi-step with tools.", decision: "LangGraph supervisor with specialist nodes.", alternativesConsidered: "Single ReAct loop; rules engine.", tradeOffs: "More moving parts, better critique and HITL.", consequences: "Need eval CI and checkpoints." }),
    ],
    projectMetrics: [
      stamp("demo_pm_1", { projectId: "demo_pr_rca", name: "Trajectory success", baseline: "42%", achieved: "71%", unit: "%", methodology: "40 labeled historical incidents.", notes: "" }),
      stamp("demo_pm_2", { projectId: "demo_pr_eval", name: "PR gate catch rate", baseline: "n/a", achieved: "3 regressions blocked in August", unit: "count", methodology: "Intentional prompt drift fixtures.", notes: "" }),
    ],
    resumeVariants: [
      stamp("demo_cv_agentic", { name: "Agentic AI Engineer", targetRoleIds: ["role_agentic"], versionLabel: "v3", summary: "Production agents, eval CI, HITL.", selectedProjectIds: ["demo_pr_eval", "demo_pr_rca"], selectedEvidenceIds: ["demo_ev_eval", "demo_ev_rca_arch"], notes: "Lead with eval platform.", isActive: true }),
      stamp("demo_cv_genai", { name: "GenAI Engineer", targetRoleIds: ["role_genai"], versionLabel: "v1", summary: "RAG + evaluation.", selectedProjectIds: ["demo_pr_rag"], selectedEvidenceIds: [], notes: "Needs stronger RAG evidence.", isActive: true }),
    ],
    jobDescriptions: [
      stamp("demo_jd_1", { applicationId: "demo_job_1", sourceUrl: "https://careers.example.com/agentic", capturedAt: T3, rawText: "We need an Agentic AI Engineer to design multi-agent systems, tool calling, evaluation, and production deployment on Azure. Python, LangGraph, observability, security.", requiredSkills: ["Python", "LangGraph", "Agents", "Evaluation", "Azure"], preferredSkills: ["OpenTelemetry", "RAG"], responsibilities: ["Own agent runtime", "Eval gates", "Production rollout"], locationText: "Bengaluru / Hybrid India", compensationText: "₹24–32 LPA", notes: "DEMO JD" }),
    ],
    interviewRounds: [
      stamp("demo_ir_1", { applicationId: "demo_job_1", roundNumber: 1, type: "Recruiter", scheduledAt: "2026-08-14T10:00:00.000Z", completedAt: "2026-08-14T10:30:00.000Z", interviewerName: "R. Patel", outcome: "Passed", questionsAsked: ["Why AI now?"], strongAreas: ["Narrative"], weakAreas: [], notes: "DEMO", wentWell: "Clear 90-second story." }),
      stamp("demo_ir_2", { applicationId: "demo_job_1", roundNumber: 2, type: "Technical", scheduledAt: "2026-09-06T11:00:00.000Z", outcome: "Upcoming", questionsAsked: [], strongAreas: [], weakAreas: [], notes: "Likely graph + eval." }),
    ],
    networkingInteractions: [
      stamp("demo_ni_1", { contactId: "demo_ct_1", date: "2026-08-01", type: "Message", summary: "Asked for a critique of the RCA architecture one-pager." }),
      stamp("demo_ni_2", { contactId: "demo_ct_1", date: "2026-08-08", type: "Call", summary: "60m. Push eval CI to the top of the resume.", nextAction: "Send eval dashboard link", nextActionDate: "2026-09-10" }),
      stamp("demo_ni_3", { contactId: "demo_ct_1", date: "2026-08-10", type: "Referral", summary: "Intro to Contoso hiring manager." }),
    ],
    targetCompanies: [
      stamp("demo_co_1", { name: "Contoso GCC", tier: "GCC", priority: "Dream", targetRoleIds: ["role_agentic", "role_aiops"], careerUrl: "https://careers.example.com", locations: ["Bengaluru", "Hyderabad"], whyTarget: "Serious agent platform work with production constraints.", notes: "DEMO" }),
      stamp("demo_co_2", { name: "Nimbus AI", tier: "AI Startup", priority: "High", targetRoleIds: ["role_genai"], locations: ["Hyderabad", "Remote India"], whyTarget: "Applied GenAI with eval culture.", notes: "DEMO" }),
    ],
    campaigns: [
      stamp("demo_camp_1", { name: "September Agentic AI + AI Solutions GCC Campaign", startDate: "2026-09-01", targetRoleIds: ["role_agentic", "role_solutions"], targetCompanyIds: ["demo_co_1"], weeklyApplicationTarget: 6, weeklyNetworkingTarget: 4, resumeVariantIds: ["demo_cv_agentic"], hypothesis: "Eval-led evidence + referrals outperform spray applications.", retrospective: "", status: "Active" }),
    ],
    achievements: [
      stamp("demo_ach_1", { title: "Stabilized a multi-region latency incident practice", context: "Enterprise production operations, 8.5 years.", action: "Facilitated cross-team RCA, introduced better telemetry hygiene, and documented failure modes.", result: "Repeat incidents of the same class stopped the following quarter.", technologies: ["Observability", "Incident command"], transferableCompetencies: ["comp_observability", "comp_sysdesign", "comp_comms"], mappedRoleIds: ["role_aiops"], quantified: true }),
    ],
    offers: [],
    researchSources: [
      stamp("demo_src_1", { researchTopicId: "demo_rs_2", title: "Agent evaluation primer (internal notes)", sourceType: "Article", credibility: "Strong Secondary", takeaway: "Mix golden tasks with human spot checks.", reviewedAt: T3 }),
    ],
    activityEvents: [
      stamp("demo_ae_1", { occurredAt: "2026-08-12T08:00:00.000Z", category: "Application", action: "Applied to Contoso GCC Agentic AI", entityId: "demo_job_1" }),
      stamp("demo_ae_2", { occurredAt: "2026-08-20T08:00:00.000Z", category: "Project", action: "Deployed Agent Evaluation CI", entityId: "demo_pr_eval" }),
      stamp("demo_ae_3", { occurredAt: "2026-08-22T08:00:00.000Z", category: "Evidence", action: "Added eval report", entityId: "demo_ev_eval" }),
    ],
    scoreSnapshots: [
      { id: "demo_snap_1", capturedAt: "2026-07-01T00:00:00.000Z", globalReadiness: 28, capability: 32, evidence: 22, interview: 18, positioning: 30, marketExecution: 12, roleScores: { role_agentic: 24, role_aiops: 30 } },
      { id: "demo_snap_2", capturedAt: "2026-08-01T00:00:00.000Z", globalReadiness: 41, capability: 44, evidence: 38, interview: 28, positioning: 40, marketExecution: 22, roleScores: { role_agentic: 40, role_aiops: 48 } },
    ],
    careerAssets: [
      stamp("demo_as_1", { kind: "GitHub", title: "GitHub", targetRoleIds: ["role_agentic"], url: "https://github.com/demo", status: "Ready", completeness: 70, notes: "Pin eval CI + RCA." }),
      stamp("demo_as_2", { kind: "LinkedIn", title: "LinkedIn", targetRoleIds: ["role_agentic"], url: "https://linkedin.com/in/demo", status: "Review", completeness: 55, notes: "Rewrite headline to Agentic / AIOps." }),
    ],
    resumeBullets: [
      stamp("demo_rb_1", { text: "Built an evaluated LangGraph RCA system that raised trajectory success from 42% to 71% on 40 historical incidents, with HITL blocking unsafe actions.", projectId: "demo_pr_rca", mappedRoleIds: ["role_aiops", "role_agentic"], competencyIds: ["comp_agent_orch", "comp_agent_eval"], quantified: true }),
    ],
    negotiationLogs: [],
    transitionNarratives: [
      stamp("demo_tn_1", {
        intro30s: "I'm an AI engineer focused on agentic systems, evaluation, and production reliability — translating 8.5 years of enterprise operations into senior AI engineering.",
        story90s: "I spent 8.5 years in enterprise technology operations. In 2026 I'm not pivoting into support chatbots; I'm building evaluated agent systems, RAG with refusal, and LLMOps gates, targeting ₹20–35 LPA AI engineering roles.",
        whyAI: "The work I already did — incidents, systems, trade-offs — is the work production AI needs, if encoded with eval and deployment discipline.",
        whyNow: "Tool-calling, graphs, and eval practice finally make this identity defensible.",
        whySenior: "I am not entry-level. I have production scars, stakeholder communication, and system thinking. The gap is AI-native evidence, which this OS is built to create.",
        howOpsStrengthens: "RCA, reliability, change control, and enterprise constraints are the difference between a demo agent and a deployed one.",
        evidenceIds: ["demo_ev_eval", "demo_ev_rca_arch"],
      }),
    ],
    attachments: [],
  };

  return state as unknown as CareerOSState;
}
