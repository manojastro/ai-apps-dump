-- M2 full domain schema (v2). Deterministic: safe to re-run (IF NOT EXISTS).
-- Aliased IDs only (USER_001/DEVICE_001). No PII hostnames.
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'employee',
    department TEXT NOT NULL DEFAULT '',
    entitlements TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    os TEXT NOT NULL DEFAULT '',
    department TEXT NOT NULL DEFAULT '',
    device_group TEXT NOT NULL DEFAULT '',
    compliance_state TEXT NOT NULL DEFAULT 'unknown',
    risk_attributes TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET DEFAULT
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    device_id TEXT NOT NULL DEFAULT '',
    request_text TEXT NOT NULL DEFAULT '',
    request_type TEXT NOT NULL DEFAULT 'technical',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL DEFAULT '',
    servicenow_sys_id TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'New',
    priority TEXT NOT NULL DEFAULT '3',
    short_description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    resolved_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    source_system TEXT NOT NULL DEFAULT '',
    tool TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    entity TEXT NOT NULL DEFAULT '',
    measurement TEXT NOT NULL DEFAULT '',
    value TEXT NOT NULL DEFAULT '',
    unit TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 1.0,
    raw_reference TEXT NOT NULL DEFAULT '',
    sanitized_summary TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id);

CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    rank INTEGER NOT NULL DEFAULT 0,
    title TEXT NOT NULL DEFAULT '',
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    confidence REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'INSUFFICIENT',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_hypotheses_case ON hypotheses(case_id);

CREATE TABLE IF NOT EXISTS scripts (
    script_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '1.0',
    hash TEXT NOT NULL DEFAULT '',
    owner TEXT NOT NULL DEFAULT '',
    platform TEXT NOT NULL DEFAULT '',
    supported_device_groups TEXT NOT NULL DEFAULT '[]',
    risk TEXT NOT NULL DEFAULT 'LOW',
    approved INTEGER NOT NULL DEFAULT 0,
    approval_timestamp TEXT NOT NULL DEFAULT '',
    approved_by TEXT NOT NULL DEFAULT '',
    rollback_available INTEGER NOT NULL DEFAULT 0,
    autonomy_level TEXT NOT NULL DEFAULT 'L2',
    execution_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    rollback_count INTEGER NOT NULL DEFAULT 0,
    reopen_count INTEGER NOT NULL DEFAULT 0,
    success_rate REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS script_versions (
    version_id TEXT PRIMARY KEY,
    script_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    hash TEXT NOT NULL DEFAULT '',
    content_ref TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    approved_by TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (script_id) REFERENCES scripts(script_id) ON DELETE CASCADE
);

-- M14: AI-generated script intake (never executes before approval+register).
CREATE TABLE IF NOT EXISTS script_proposals (
    proposal_id TEXT PRIMARY KEY,
    script_id TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    platform TEXT NOT NULL DEFAULT 'windows',
    primitives TEXT NOT NULL DEFAULT '[]',
    risk_claimed TEXT NOT NULL DEFAULT 'LOW',
    risk_computed TEXT NOT NULL DEFAULT '',
    autonomy_claimed TEXT NOT NULL DEFAULT 'L3',
    autonomy_granted TEXT NOT NULL DEFAULT '',
    rollback_available INTEGER NOT NULL DEFAULT 0,
    supported_device_groups TEXT NOT NULL DEFAULT '["corporate-laptop"]',
    owner TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'proposed',
    findings TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    decided_at TEXT NOT NULL DEFAULT '',
    decided_by TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON script_proposals(status);

CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    rules TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS policy_decisions (
    decision_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL DEFAULT '',
    script_id TEXT NOT NULL DEFAULT '',
    device_id TEXT NOT NULL DEFAULT '',
    user_id TEXT NOT NULL DEFAULT '',
    checks TEXT NOT NULL DEFAULT '{}',
    decision TEXT NOT NULL DEFAULT 'DENY',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_case ON policy_decisions(case_id);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL DEFAULT '',
    script_id TEXT NOT NULL DEFAULT '',
    requested_by TEXT NOT NULL DEFAULT '',
    approver TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'PENDING',
    requested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    decided_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_approvals_case ON approvals(case_id);

CREATE TABLE IF NOT EXISTS remediation_runs (
    run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL DEFAULT '',
    script_id TEXT NOT NULL DEFAULT '',
    device_id TEXT NOT NULL DEFAULT '',
    before_state TEXT NOT NULL DEFAULT '{}',
    after_state TEXT NOT NULL DEFAULT '{}',
    verification_result TEXT NOT NULL DEFAULT '',
    rollback_run_id TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    finished_at TEXT NOT NULL DEFAULT '',
    success INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_remediation_case ON remediation_runs(case_id);

CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '1.0',
    failure_signature TEXT NOT NULL DEFAULT '',
    required_evidence TEXT NOT NULL DEFAULT '[]',
    root_cause_signature TEXT NOT NULL DEFAULT '',
    action_id TEXT NOT NULL DEFAULT '',
    policy_requirements TEXT NOT NULL DEFAULT '{}',
    autonomy_level TEXT NOT NULL DEFAULT 'L1',
    approval_state TEXT NOT NULL DEFAULT 'candidate',
    owner TEXT NOT NULL DEFAULT '',
    execution_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    rollback_count INTEGER NOT NULL DEFAULT 0,
    reopen_count INTEGER NOT NULL DEFAULT 0,
    success_rate REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    last_updated TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS workflow_versions (
    version_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    definition TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workflow_runs (
    run_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL DEFAULT '',
    case_id TEXT NOT NULL DEFAULT '',
    policy_decision TEXT NOT NULL DEFAULT '',
    approval_state TEXT NOT NULL DEFAULT '',
    success INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    finished_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fleet_matches (
    match_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL DEFAULT '',
    workflow_id TEXT NOT NULL DEFAULT '',
    device_id TEXT NOT NULL DEFAULT '',
    match_state TEXT NOT NULL DEFAULT 'AT_RISK',
    policy_decision TEXT NOT NULL DEFAULT 'DENY',
    remediation_run_id TEXT NOT NULL DEFAULT '',
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_fleet_case ON fleet_matches(case_id);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    doc_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL DEFAULT '',
    content_ref TEXT NOT NULL DEFAULT '',
    allowed_roles TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS knowledge_permissions (
    perm_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY (doc_id) REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    case_id TEXT NOT NULL DEFAULT '',
    agent TEXT NOT NULL DEFAULT '',
    event_type TEXT NOT NULL DEFAULT '',
    tool TEXT NOT NULL DEFAULT '',
    sanitized_input TEXT NOT NULL DEFAULT '',
    sanitized_output TEXT NOT NULL DEFAULT '',
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    decision TEXT NOT NULL DEFAULT '',
    policy_result TEXT NOT NULL DEFAULT '',
    risk TEXT NOT NULL DEFAULT '',
    approval TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL DEFAULT '',
    duration_ms INTEGER NOT NULL DEFAULT 0,
    success INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_audit_case_time ON audit_events(case_id, timestamp);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    value REAL NOT NULL DEFAULT 0.0,
    case_id TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- M20: resolution snapshots (learning input — never chat history).
CREATE TABLE IF NOT EXISTS resolution_patterns (
    pattern_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL DEFAULT '',
    failure_signature TEXT NOT NULL DEFAULT '',
    evidence_pattern TEXT NOT NULL DEFAULT '[]',
    root_cause TEXT NOT NULL DEFAULT '',
    action_id TEXT NOT NULL DEFAULT '',
    script_id TEXT NOT NULL DEFAULT '',
    policy_result TEXT NOT NULL DEFAULT '',
    approval_state TEXT NOT NULL DEFAULT '',
    verification TEXT NOT NULL DEFAULT '{}',
    success INTEGER NOT NULL DEFAULT 0,
    reopen INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_patterns_signature ON resolution_patterns(failure_signature);
