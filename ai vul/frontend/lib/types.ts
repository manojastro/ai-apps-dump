/** Types mirroring the backend serializers (app/api/serializers.py). */

export type RiskLevel = "critical" | "high" | "medium" | "low";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "analyst" | "approver" | "viewer";
  permissions: string[];
}

export interface IntelProvenance {
  status: string;
  origin: string;
  reference: string;
  fetched_at: string | null;
  notes: string[];
}

export interface Vulnerability {
  id: string;
  cve_id: string;
  title: string | null;
  description: string | null;
  severity: string;
  cvss_score: number | null;
  cvss_vector: string | null;
  cvss_version: string | null;
  cwes: string[];
  published_at: string | null;
  epss_score: number | null;
  epss_percentile: number | null;
  epss_date: string | null;
  kev: boolean | null;
  kev_date_added: string | null;
  kev_due_date: string | null;
  kev_ransomware_use: string | null;
  kev_required_action: string | null;
  affected_vendor: string | null;
  affected_product: string | null;
  references: string[];
  source: string;
  evidence_status: string;
  intel_sources: Record<string, IntelProvenance>;
  first_detected_at: string | null;
  last_detected_at: string | null;
}

export interface VulnerabilityRow {
  id: string;
  cve_id: string;
  title: string | null;
  severity: string;
  cvss_score: number | null;
  max_risk_score: number | null;
  risk_level: RiskLevel | null;
  epss_score: number | null;
  epss_percentile: number | null;
  kev: boolean | null;
  affected_assets: number;
  open_findings: number;
  business_services: string[];
  business_impact: string | null;
  remediation_status: string;
  last_detected_at: string | null;
  affected_product: string | null;
  evidence_status: string;
}

export interface BusinessService {
  id: string;
  name: string;
  division: string;
  criticality: string;
  owner_team: string | null;
  description: string | null;
  cmdb_sys_id: string | null;
  assets?: number;
  open_findings?: number;
  critical_findings?: number;
}

export interface Asset {
  id: string;
  hostname: string;
  fqdn: string | null;
  ip_address: string | null;
  asset_type: string;
  operating_system: string | null;
  os_version: string | null;
  environment: string | null;
  business_criticality: string | null;
  business_service: BusinessService | null;
  owner: string | null;
  support_group: string | null;
  internet_exposed: boolean | null;
  cloud_provider: string | null;
  location: string | null;
  operational_status: string | null;
  cmdb_sys_id: string | null;
  defender_device_id: string | null;
  last_sync_at: string | null;
  open_findings?: number;
  max_risk_score?: number | null;
}

export interface FindingRow {
  id: string;
  cve_id: string;
  severity: string;
  cvss_score: number | null;
  epss_score: number | null;
  kev: boolean | null;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  priority: string | null;
  asset_id: string | null;
  hostname: string;
  environment: string | null;
  business_service: string | null;
  software: string | null;
  software_version: string | null;
  scanner: string;
  status: string;
  verification_state: string;
  correlation_status: string;
  sla_due_at: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
}

export interface RiskFactor {
  name: string;
  label: string;
  max_points: number;
  points: number;
  available: boolean;
  input_value: unknown;
  explanation: string;
  source: string | null;
}

export interface RiskAssessment {
  id: string;
  score: number;
  score_lower: number;
  score_upper: number;
  risk_level: RiskLevel;
  priority: string;
  business_impact: string;
  coverage: number;
  policy_version: string;
  factors: Record<string, RiskFactor>;
  missing_factors: string[];
  requires_immediate_review: boolean;
  rationale: string[];
  calculated_at: string;
  workflow_run_id: string | null;
}

export interface EvidenceRef {
  id: string;
  type: string;
  title: string;
  content?: unknown;
  source?: string;
  reference?: string | null;
  cited?: boolean;
  invalid?: boolean;
}

export interface ValidationIssue {
  code: string;
  severity: string;
  message: string;
  blocking: boolean;
  acknowledged_by?: string;
}

export interface PlanSummary {
  id: string;
  finding_id: string;
  workflow_run_id: string | null;
  revision: number;
  status: string;
  remediation_state: string;
  lifecycle_stage: string;
  title: string;
  summary: string;
  target_version: string | null;
  requires_expert_validation: boolean;
  generated_by: string;
  created_at: string;
  updated_at: string;
  cve_id: string | null;
  hostname: string | null;
  business_service: string | null;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  priority: string | null;
  approval_state: string | null;
  approval_request_id: string | null;
  servicenow_number: string | null;
  sync_state: string | null;
}

export interface ChangeImpact {
  plan_id: string;
  risk_category: string;
  business_impact: string;
  affected_services: { name: string; criticality: string; relation: string }[];
  impacted_assets: { asset_id: string; hostname: string; depth: number; environment: string | null; service: string | null }[];
  known_dependencies: number;
  unknown_dependencies: string[];
  maintenance_window_required: boolean;
  downtime_estimate: string;
  historical_changes: { available: boolean; total?: number; closed?: number; open?: number };
  summary: string;
  recommended_review_steps: string[];
  confidence: string;
  evidence: string[];
}

export interface Plan extends PlanSummary {
  recommended_action: string;
  prerequisites: string[];
  implementation_steps: { step: string; evidence_refs: string[] }[];
  verification_steps: string[];
  rollback_steps: string[];
  testing_requirements: string[];
  expected_impact: string;
  maintenance_window: string;
  required_approvers: string[];
  evidence_refs: EvidenceRef[];
  assumptions: string[];
  change_impact: ChangeImpact | Record<string, never>;
  validation: { status?: string; route?: string; issues?: ValidationIssue[]; citation_validity?: number; checks?: Record<string, boolean> };
  content_hash: string;
  created_by: string | null;
  edited_by: string | null;
}

export interface ApprovalDecision {
  id: string;
  actor_id: string;
  actor_name: string | null;
  decision: string;
  outcome: string;
  comment: string | null;
  reason: string | null;
  created_at: string;
}

export interface Approval {
  id: string;
  plan_id: string;
  state: string;
  risk_level: string | null;
  requested_by: string;
  requested_by_name: string | null;
  assigned_approver_id: string | null;
  assigned_approver_name: string | null;
  decided_by: string | null;
  decided_by_name: string | null;
  decided_at: string | null;
  decision_comment: string | null;
  request_comment: string | null;
  payload_hash: string;
  payload_snapshot: { plan: Record<string, unknown>; context: Record<string, unknown>; revision: number };
  policy_version: string;
  separation_of_duties: boolean;
  created_at: string;
  decisions: ApprovalDecision[];
  plan?: PlanSummary | Plan | null;
}

export interface ServiceNowRecord {
  id: string;
  plan_id: string;
  approval_request_id: string;
  mode: string;
  instance: string;
  table_name: string;
  sys_id: string | null;
  number: string | null;
  record_url: string | null;
  sync_state: string;
  external_state: string | null;
  external_state_label: string | null;
  external_close_code: string | null;
  attempts: number;
  last_error: string | null;
  last_sync_at: string | null;
  created_at: string;
  parent_record_id: string | null;
  payload: Record<string, unknown>;
}

export interface ScanEvidence {
  id: string;
  finding_id: string | null;
  asset_identifier: string;
  device_id: string | null;
  cve_id: string;
  scanner: string;
  scan_id: string;
  scanned_at: string;
  vulnerable: boolean;
  software_name: string | null;
  software_version: string | null;
  kind: string;
  raw: Record<string, unknown>;
  submitted_by: string | null;
  created_at: string;
}

export interface WorkflowRun {
  id: string;
  kind: string;
  finding_id: string;
  status: string;
  current_node: string | null;
  waiting_reason: string | null;
  plan_id: string | null;
  provider: string;
  model: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number | null;
  error: string | null;
  resume_count: number;
  summary: Record<string, unknown>;
  started_by: string | null;
  started_at: string;
  updated_at: string;
  completed_at: string | null;
  cve_id: string | null;
  hostname: string | null;
  risk_score: number | null;
  risk_level: RiskLevel | null;
}

export interface AgentExecution {
  id: string;
  agent_name: string;
  node_name: string;
  status: string;
  attempt: number;
  input_summary: Record<string, unknown>;
  output: Record<string, unknown>;
  error: string | null;
  validation_errors: string[];
  model_provider: string | null;
  model_name: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  estimated_cost_usd: number | null;
  latency_ms: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface ToolCall {
  id: string;
  agent_execution_id: string | null;
  caller: string;
  tool_name: string;
  mutating: boolean;
  arguments: Record<string, unknown>;
  result_summary: Record<string, unknown>;
  status: string;
  error: string | null;
  latency_ms: number | null;
  created_at: string;
}

export interface WorkflowEvent {
  id: number;
  event_type: string;
  node: string | null;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface TopologyNode {
  id: string;
  label: string;
  agent: string | null;
  kind: "agent" | "human" | "system" | "gate";
}

export interface Topology {
  nodes: TopologyNode[];
  edges: [string, string, string][];
}

export interface WorkflowDetail {
  run: WorkflowRun;
  finding: FindingRow | null;
  asset: Asset | null;
  correlation_candidates: { asset_id: string; hostname: string; fqdn: string | null; ip_address: string | null; environment: string | null; operational_status: string | null }[];
  executions: AgentExecution[];
  tool_calls: ToolCall[];
  events: WorkflowEvent[];
  node_states: Record<string, { status: string; attempts?: number; latency_ms?: number | null; execution_id?: string }>;
  risk: RiskAssessment | null;
  plan: Plan | null;
  approval: Approval | null;
  pending_interrupt: { node: string; value: Record<string, unknown> } | null;
  topology: Topology;
}

export interface FindingDetail {
  finding: FindingRow & {
    reported_asset_identifier: string;
    reported_ip: string | null;
    reported_device_id: string | null;
    software_vendor: string | null;
    correlation_confidence: number | null;
    correlation_candidates: unknown[];
    source_evidence: Record<string, unknown>;
    scanner_finding_id: string | null;
    duplicate_count: number;
    remediated_at: string | null;
  };
  vulnerability: Vulnerability;
  asset: Asset | null;
  risk: RiskAssessment | null;
  plans: PlanSummary[];
  workflow_runs: WorkflowRun[];
  evidence: ScanEvidence[];
  servicenow_records: ServiceNowRecord[];
  simulated_device: {
    device_id: string;
    computer_dns_name: string;
    software: { vendor: string; product: string; display_name: string; version: string }[];
  } | null;
}

export interface Metric {
  value: number | null;
  unit: string;
  definition: string;
  sample_size: number | null;
}

export interface Integration {
  key: string;
  name: string;
  status: "Mock" | "Connected" | "Not Configured" | "Error" | "Unsupported" | "Unverified" | "Configured";
  mode: string;
  detail: string;
}
