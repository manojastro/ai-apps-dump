import type {
  Competency,
  CompetencyDomain,
  RoleCompetencyRequirement,
  Seniority,
  TargetRoleProfile,
} from "@/types/career";

const STAMP = "2026-01-01T00:00:00.000Z";

function competency(
  id: string,
  name: string,
  domain: CompetencyDomain,
  description: string,
): Competency {
  return {
    id,
    name,
    domain,
    description,
    skillIds: [],
    researchTopicIds: [],
    createdAt: STAMP,
    updatedAt: STAMP,
    tags: ["catalog"],
  };
}

export const CATALOG_COMPETENCIES: Competency[] = [
  competency("comp_python_core", "Python Engineering", "Python", "Production Python: typing, packaging, testing, OOP, and async."),
  competency("comp_backend", "Backend APIs", "Backend", "FastAPI/service design, structured output, auth, and integration."),
  competency("comp_llm_fundamentals", "LLM Fundamentals", "LLM", "Tokenization, context windows, sampling, cost/latency, failure modes."),
  competency("comp_prompt_arch", "Prompt & Context Architecture", "LLM", "Prompt architecture, structured output, tool schemas, context engineering."),
  competency("comp_tool_calling", "Tool Calling", "Agents", "Reliable tool use, schema validation, retries, and side-effect control."),
  competency("comp_agent_orch", "Agent Orchestration", "Agents", "Agent loops, state machines, LangGraph-style graphs, human-in-the-loop."),
  competency("comp_multi_agent", "Multi-Agent Systems", "Agents", "Role-specialized agents, routing, shared memory, and coordination."),
  competency("comp_agent_eval", "Agent Evaluation", "Evaluation", "Task success, trajectory eval, regression suites, and CI for agents."),
  competency("comp_rag_retrieval", "RAG Retrieval", "RAG", "Chunking, embeddings, hybrid search, reranking, and grounding."),
  competency("comp_rag_eval", "RAG Evaluation", "Evaluation", "Faithfulness, context precision/recall, and retrieval diagnostics."),
  competency("comp_llm_eval", "LLM Evaluation", "Evaluation", "Offline eval, LLM-as-judge caveats, golden sets, and quality gates."),
  competency("comp_llmops", "Serving & LLMOps", "LLMOps", "Gateways, routing, versioning, CI/CD, canaries, and rollback."),
  competency("comp_observability", "AI Observability", "Observability", "Traces, token/cost metrics, eval dashboards, and incident RCA."),
  competency("comp_cloud_azure", "Azure / Cloud AI", "Cloud", "Azure OpenAI, identity, networking, and enterprise cloud patterns."),
  competency("comp_cloud_aws", "AWS Cloud AI", "Cloud", "Bedrock/SageMaker-style serving, IAM, and cloud-agnostic design."),
  competency("comp_sysdesign", "AI System Design", "System Design", "Reliability, queues, caching, backpressure, and failure domains."),
  competency("comp_security", "AI Security", "Security", "Prompt injection, data leakage, tool-abuse, and guardrails."),
  competency("comp_cost", "Cost & Latency", "LLMOps", "Caching, quantization, routing, batching, and SLO trade-offs."),
  competency("comp_data", "Enterprise Data", "Data", " unstructured enterprise data, governance, and retrieval corpora."),
  competency("comp_comms", "Technical Communication", "Communication", "Architecture narratives, STAR stories, and stakeholder translation."),
];

function req(competencyId: string, importance: 1 | 2 | 3 | 4 | 5, targetLevel: 1 | 2 | 3 | 4 | 5, evidenceRequired = true): RoleCompetencyRequirement {
  return { competencyId, importance, targetLevel, evidenceRequired };
}

function role(
  id: string,
  name: string,
  priority: TargetRoleProfile["priority"],
  seniority: Seniority,
  requirements: RoleCompetencyRequirement[],
  notes: string,
): TargetRoleProfile {
  return {
    id,
    name,
    priority,
    active: priority === "Primary" || priority === "Secondary",
    targetSeniority: seniority,
    competencyRequirements: requirements,
    notes,
    createdAt: STAMP,
    updatedAt: STAMP,
    tags: ["catalog"],
  };
}

export const CATALOG_ROLES: TargetRoleProfile[] = [
  role("role_agentic", "Agentic AI Engineer", "Primary", "Senior", [
    req("comp_agent_orch", 5, 5),
    req("comp_multi_agent", 5, 4),
    req("comp_tool_calling", 5, 5),
    req("comp_agent_eval", 5, 4),
    req("comp_python_core", 4, 4),
    req("comp_observability", 4, 4),
    req("comp_security", 4, 4),
    req("comp_sysdesign", 4, 4),
    req("comp_llm_fundamentals", 4, 4),
    req("comp_comms", 3, 4),
  ], "Primary 2026 target. Production agent systems, evaluation, and deployment — not chatbot wrappers."),
  role("role_genai", "GenAI Engineer", "Primary", "Senior", [
    req("comp_llm_fundamentals", 5, 5),
    req("comp_prompt_arch", 5, 4),
    req("comp_rag_retrieval", 5, 4),
    req("comp_llm_eval", 4, 4),
    req("comp_python_core", 4, 4),
    req("comp_backend", 4, 4),
    req("comp_llmops", 4, 3),
    req("comp_security", 3, 3),
  ], "Application-layer generative systems with evaluation and grounding."),
  role("role_aiops", "AIOps Engineer", "Primary", "Senior", [
    req("comp_observability", 5, 5),
    req("comp_sysdesign", 5, 4),
    req("comp_agent_orch", 4, 4),
    req("comp_python_core", 4, 4),
    req("comp_llmops", 4, 4),
    req("comp_cloud_azure", 4, 3),
    req("comp_data", 3, 3),
    req("comp_comms", 4, 4),
  ], "Convert enterprise operations experience into production AIOps and autonomous RCA."),
  role("role_solutions", "AI Solutions Engineer", "Secondary", "Senior", [
    req("comp_comms", 5, 5),
    req("comp_sysdesign", 4, 4),
    req("comp_rag_retrieval", 4, 4),
    req("comp_agent_orch", 4, 3),
    req("comp_llm_fundamentals", 4, 4),
    req("comp_cloud_azure", 4, 3),
    req("comp_backend", 3, 3),
  ], "Customer-facing AI solutioning with credible engineering depth."),
  role("role_architect", "AI Solutions Architect", "Stretch", "Architect", [
    req("comp_sysdesign", 5, 5),
    req("comp_security", 5, 4),
    req("comp_llmops", 5, 4),
    req("comp_cloud_azure", 4, 4),
    req("comp_cloud_aws", 4, 3),
    req("comp_agent_orch", 4, 4),
    req("comp_cost", 4, 4),
    req("comp_comms", 5, 5),
  ], "Longer-horizon architecture track. Evidence bar is high."),
  role("role_cloud", "Cloud AI Engineer", "Secondary", "Senior", [
    req("comp_cloud_azure", 5, 4),
    req("comp_cloud_aws", 4, 4),
    req("comp_llmops", 5, 4),
    req("comp_security", 4, 4),
    req("comp_observability", 4, 3),
    req("comp_python_core", 3, 3),
  ], "Cloud-native model serving, identity, and enterprise integration."),
  role("role_fda", "Forward Deployed / AI Deployment Engineer", "Secondary", "Senior", [
    req("comp_comms", 5, 5),
    req("comp_sysdesign", 4, 4),
    req("comp_agent_orch", 4, 3),
    req("comp_rag_retrieval", 4, 3),
    req("comp_python_core", 4, 3),
    req("comp_observability", 3, 3),
  ], "On-site productionization of AI systems with enterprise constraints."),
  role("role_automation", "Intelligent Automation Engineer", "Parked", "Senior", [
    req("comp_agent_orch", 4, 4),
    req("comp_backend", 4, 4),
    req("comp_python_core", 4, 4),
    req("comp_sysdesign", 3, 3),
    req("comp_observability", 3, 3),
  ], "Keep as adjacent, not the headline identity."),
  role("role_security", "AI Security Engineer", "Stretch", "Senior", [
    req("comp_security", 5, 5),
    req("comp_agent_orch", 4, 3),
    req("comp_llm_fundamentals", 4, 4),
    req("comp_observability", 4, 4),
    req("comp_sysdesign", 4, 3),
  ], "Specialist stretch. Requires dedicated security evidence."),
  role("role_llm", "LLM Engineer", "Secondary", "Senior", [
    req("comp_llm_fundamentals", 5, 5),
    req("comp_cost", 5, 4),
    req("comp_llmops", 5, 4),
    req("comp_llm_eval", 4, 4),
    req("comp_python_core", 4, 4),
    req("comp_observability", 3, 3),
  ], "Model-serving and inference engineering emphasis."),
];

export const ROLE_ID_BY_NAME: Record<string, string> = Object.fromEntries(
  CATALOG_ROLES.map((r) => [r.name, r.id]),
);
