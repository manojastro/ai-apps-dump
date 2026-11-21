CREATE TABLE IF NOT EXISTS incidents (
  id TEXT PRIMARY KEY, scenario TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL,
  risk_tier TEXT, namespace TEXT NOT NULL, resource TEXT NOT NULL, force_verification_failure INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, detected_at TEXT NOT NULL, resolved_at TEXT, snapshot_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS signals (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, kind TEXT NOT NULL, value TEXT NOT NULL, observed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, kind TEXT NOT NULL, summary TEXT NOT NULL, source_ref TEXT NOT NULL, collected_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runbooks (id TEXT PRIMARY KEY, title TEXT NOT NULL, incident_type TEXT NOT NULL, approved INTEGER NOT NULL, content TEXT NOT NULL, action TEXT NOT NULL, version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS hypotheses (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, statement TEXT NOT NULL, confidence REAL NOT NULL, evidence_refs TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS remediation_plans (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, action TEXT NOT NULL, parameters_json TEXT NOT NULL, rollback_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS policy_decisions (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, allowed INTEGER NOT NULL, risk_tier TEXT NOT NULL, reasons_json TEXT NOT NULL, approval_required INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, decision TEXT NOT NULL, actor TEXT NOT NULL, comment TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS executions (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE, action TEXT NOT NULL, resource TEXT NOT NULL, status TEXT NOT NULL, original_state_json TEXT NOT NULL, result_json TEXT NOT NULL, duration_ms REAL NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS verification_results (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, healthy INTEGER NOT NULL, checks_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rollback_records (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, execution_id TEXT NOT NULL, original_state_json TEXT NOT NULL, status TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, incident_id TEXT, event_type TEXT NOT NULL, actor TEXT NOT NULL, details_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS model_usage (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL, cost_usd REAL NOT NULL, latency_ms REAL NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_audit_incident ON audit_events(incident_id, created_at);
CREATE INDEX IF NOT EXISTS idx_exec_incident ON executions(incident_id, created_at);
