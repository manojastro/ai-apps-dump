-- Approved attestations and invalidated legacy attestations are append-only.
-- A new decision must be represented by a new approval row.
CREATE TRIGGER IF NOT EXISTS bound_approval_no_update
BEFORE UPDATE ON approvals
WHEN OLD.decision IN ('APPROVED', 'REAPPROVAL_REQUIRED')
BEGIN SELECT RAISE(ABORT, 'bound approval attestation is immutable'); END;

CREATE TRIGGER IF NOT EXISTS bound_approval_no_delete
BEFORE DELETE ON approvals
WHEN OLD.decision IN ('APPROVED', 'REAPPROVAL_REQUIRED')
BEGIN SELECT RAISE(ABORT, 'bound approval attestation is immutable'); END;

-- SQLite foreign keys already prevent deleting an action referenced by an
-- approval. Keep an explicit invariant for clearer failure semantics.
CREATE TRIGGER IF NOT EXISTS approved_action_no_delete
BEFORE DELETE ON actions
WHEN EXISTS (
    SELECT 1 FROM approvals
    WHERE approvals.action_id = OLD.action_id AND approvals.decision = 'APPROVED'
)
BEGIN SELECT RAISE(ABORT, 'approved action binding is immutable'); END;
