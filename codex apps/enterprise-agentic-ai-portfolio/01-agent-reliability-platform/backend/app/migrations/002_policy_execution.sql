ALTER TABLE actions ADD COLUMN payload_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE actions ADD COLUMN payload_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE approvals ADD COLUMN payload_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE approvals ADD COLUMN payload_hash TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS policy_state (
    policy_key TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policy_executions (
    execution_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL REFERENCES actions(action_id),
    status TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL,
    rollback_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS approved_action_payload_immutable
BEFORE UPDATE OF payload_json, payload_version, payload_hash, action_type, incident_id, risk, required_approval ON actions
WHEN EXISTS (
    SELECT 1 FROM approvals
    WHERE approvals.action_id = OLD.action_id AND approvals.decision = 'APPROVED'
)
BEGIN SELECT RAISE(ABORT, 'approved action payload is immutable'); END;
