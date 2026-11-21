export type Incident = {
  id: string;
  title: string;
  service: string;
  scenario: string;
  severity: string;
  status: "open" | "investigating" | "complete" | "failed";
  created_at: string;
};

export type Evidence = {
  id: string;
  source: string;
  source_ref: string;
  observed_at: string;
  service: string;
  summary: string;
  redacted: boolean;
  attributes: Record<string, unknown>;
};

export type Hypothesis = {
  id: string;
  rank: number;
  category: string;
  component: string;
  statement: string;
  confidence: number;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  rationale: string;
  rejected: boolean;
};

export type Investigation = {
  incident: Incident;
  plan: string[];
  worker_runs: Array<{
    worker: string;
    tool: string;
    status: string;
    latency_ms: number;
    evidence_count: number;
    error?: string;
  }>;
  evidence: Evidence[];
  timeline: Array<{
    timestamp: string;
    title: string;
    detail: string;
    evidence_ids: string[];
  }>;
  hypotheses: Hypothesis[];
  critic: {
    challenged_hypothesis_id: string;
    challenge: string;
    evidence_ids: string[];
    overturned: boolean;
    replacement_hypothesis_id?: string;
  };
  rca: {
    incident_id: string;
    sections: unknown[];
    confidence: number;
    unresolved_questions: string[];
    generated_at: string;
    markdown: string;
  };
  duration_ms: number;
  token_usage: number;
  estimated_cost_usd: number;
};

