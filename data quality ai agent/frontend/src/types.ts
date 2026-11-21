export type IncidentStatus = 'CREATED' | 'RUNNING' | 'WAITING_FOR_HUMAN' | 'COMPLETED' | 'FAILED' | 'REJECTED'
export type Scenario = 'schema_drift' | 'null_spike' | 'duplicates' | 'transformation_regression' | 'dependency_failure'
export interface Candidate { summary: string; operations: string[]; evidence_ids: string[]; amount_divisor?: number | null }
export interface Validation { validator: string; status: 'PASS' | 'FAIL'; severity: string; expected: unknown; actual: unknown; evidence: string }
export interface Attempt { number: number; status: 'PASSED' | 'REJECTED'; candidate: Candidate; feedback: string[]; validations: Validation[] }
export interface Evidence { id: string; branch: string; summary: string; source: string; facts: Record<string, unknown> }
export interface Hypothesis { cause: string; summary: string; confidence: number; evidence_ids: string[]; contradicting_evidence: string[] }
export interface Verification { decision: 'APPROVE' | 'REJECT' | 'NEEDS_HUMAN'; confidence: number; reason_summary: string; unsupported_claims: string[]; missing_checks: string[]; risk_findings: string[] }
export interface Timing { node: string; started_at: string; ended_at: string; duration_seconds: number; attempt: number }
export interface Artifact { title: string; filename: string; diff: string; post_validation: string; sha256: string; rollback: string; instructions: string; deployment_executed: boolean }
export interface Metrics { graph_nodes_executed?: number; attempts?: number; time_to_diagnosis_seconds?: number; workflow_duration_seconds?: number; parallel_branch_seconds?: number; validator_pass_count?: number; validator_fail_count?: number; llm_calls?: number; input_tokens?: number; output_tokens?: number; estimated_cost_usd?: number | null }
export interface Incident { id: string; title: string; scenario: Scenario; pipeline_id: string; environment: string; status: IncidentStatus; current_stage: string; attempt_count: number; created_at: string; artifact: Artifact | null; metrics: Metrics; failure_reason: string }
export interface Knowledge { id: string; title: string; content: string; source_type: string; environment: string; version: string; score: number }
export interface WorkflowState { values: { aggregated_evidence?: Evidence[]; selected_hypothesis?: Hypothesis; root_cause_hypotheses?: Hypothesis[]; attempt_history?: Attempt[]; verification_result?: Verification; latency_metrics?: Timing[]; retrieved_context?: Knowledge[]; candidate_remediation?: Candidate; risk_level?: string; approval_status?: string; human_decision?: { actor: string; comment: string; approved: boolean } }; next: string[]; interrupts: { kind: string; reason?: string; scope: string }[] }
export interface WorkflowEvent { id: number; kind: string; node: string; timestamp: string; payload: Record<string, unknown> }
export interface Summary { total_incidents: number; statuses: Record<string, number>; attempts: Record<string, number>; recovery_success_rate: number; validator_rejection_rate: number; evaluation: { metrics: Record<string, number>; created_at: string } | null }

export const scenarios: { value: Scenario; label: string; description: string }[] = [
  { value: 'schema_drift', label: 'Schema drift', description: 'Upstream customer_id renamed to customerId' },
  { value: 'null_spike', label: 'Null spike', description: 'Required customer identifiers missing' },
  { value: 'duplicates', label: 'Duplicate ingestion', description: 'Retry produces duplicate transaction rows' },
  { value: 'transformation_regression', label: 'Transformation regression', description: 'Currency conversion produces incorrect totals' },
  { value: 'dependency_failure', label: 'Dependency failure', description: 'Upstream API returns a transient 503 response' },
]
