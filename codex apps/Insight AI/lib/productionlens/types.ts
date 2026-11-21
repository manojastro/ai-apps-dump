export type Incident = {
  id: string;
  title: string;
  description: string;
  service: string;
  severity: string;
  mode: string;
  status: string;
  created_at: number;
};
export type Evidence = {
  id: string;
  run_id: string;
  source_type: string;
  source_record_id: string;
  summary: string;
  observed_at: number;
  collected_at: number;
  payload: Record<string, unknown>;
  content_hash: string;
  stale: boolean;
  truncated: boolean;
};
export type ToolCall = {
  tool: string;
  inputs: Record<string, unknown>;
  status: string;
  duration_ms: number;
  error?: string;
  evidence_ids: string[];
  output: unknown;
};
export type Diagnosis = {
  category: string;
  confidence: string;
  explanation: string;
  evidence_ids: string[];
  missing: string[];
  alternatives: string[];
};
export type Recovery = {
  verified: boolean;
  reason: string;
  mode: string;
  measurement: string;
  before: { error_rate: number; p95_ms: number };
  after: { error_rate: number; p95_ms: number; samples: number };
};
export type Proposal = {
  id: string;
  digest: string;
  expires_at: number;
  status: string;
  proposal: {
    operation: string;
    target: string;
    parameters: Record<string, unknown>;
    expected_effect: string;
    risk: string;
    preconditions: string[];
    rollback: string;
    evidence_ids: string[];
  };
  result: Partial<Recovery> & { error?: string };
};
export type Run = {
  id: string;
  incident_id: string;
  mode: string;
  status: string;
  created_at: number;
  state: {
    diagnosis?: Diagnosis;
    tools?: ToolCall[];
    budget?: {
      tool_calls: number;
      tool_limit: number;
      model_calls: number;
      tokens: number;
    };
    error?: string;
    recovery?: Recovery;
  };
  version: Record<string, unknown>;
  incident?: Incident;
  events?: { id: string; kind: string; message: string; created_at: number }[];
  evidence?: Evidence[];
  action?: Proposal;
};
export type Metrics = {
  accuracy: number;
  baseline_accuracy: number;
  correct: number;
  diagnosis_count: number;
  total: number;
  executed: number;
  passed: number;
  regressions: number;
  max_latency_ms: number;
  tokens: number;
  cost: number | null;
};
export type Trial = {
  passed: boolean;
  status: string;
  note?: string;
  latency_ms: number;
  assertions: { name: string; passed: boolean }[];
  output?: { diagnosis: Diagnosis; tools: ToolCall[] };
};
export type CaseResult = {
  key: string;
  case_id: string;
  name: string;
  category: string;
  expected: string;
  regression: boolean;
  baseline: Trial;
  candidate: Trial;
  review_status: string;
};
export type Evaluation = {
  id: string;
  mode: string;
  status: string;
  created_at: number;
  config: { candidate: string; trials: number; case_id?: string };
  report?: {
    error?: string;
    metrics?: Metrics;
    release?: { decision: string; failures: string[]; missing: string[] };
    limitations?: string[];
  };
  results?: CaseResult[];
};
export type Integrations = {
  mode: string;
  worker: string;
  provider_configured: boolean;
  model: string;
  sources: {
    name: string;
    status: string;
    freshness: string;
    timeout_seconds: number;
    retries: number;
    max_bytes: number;
    authentication: string;
  }[];
};
export type User = { id: string; username: string; role: string; csrf: string };
export type Demo = {
  mode: string;
  fault: string | null;
  traffic: boolean;
  samples: number;
  revision: number;
  expires_at?: number;
};
