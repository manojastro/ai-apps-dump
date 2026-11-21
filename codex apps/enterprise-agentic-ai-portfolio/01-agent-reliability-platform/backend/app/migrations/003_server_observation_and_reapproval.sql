ALTER TABLE agent_runs ADD COLUMN observed_started_at TEXT;
ALTER TABLE agent_runs ADD COLUMN verification_deadline TEXT;

UPDATE approvals
SET decision = 'REAPPROVAL_REQUIRED'
WHERE decision = 'APPROVED' AND payload_hash = '';

UPDATE actions
SET status = 'REAPPROVAL_REQUIRED'
WHERE action_id IN (
    SELECT action_id FROM approvals WHERE decision = 'REAPPROVAL_REQUIRED'
);
