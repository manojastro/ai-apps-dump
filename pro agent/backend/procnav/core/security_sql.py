"""Database-enforced invariants: tenant RLS, the order-ledger state machine, immutability of
quotes and audit events, and runtime-role grants. Applied by migration 0001."""

from __future__ import annotations

from .models import TENANT_SCOPED_TABLES

# Valid order-intent transitions. Terminal: reconciled, failed, canceled.
ORDER_TRANSITIONS: dict[str, set[str]] = {
    "created": {"approved", "canceled", "failed"},
    "approved": {"submitting", "canceled", "failed"},
    "submitting": {"submitted", "unknown", "failed", "cancellation_requested"},
    "cancellation_requested": {"submitted", "unknown", "canceled", "failed"},
    "submitted": {"reconciled", "unknown"},
    # unknown -> submitting is only allowed once absence of an external order is established.
    "unknown": {"reconciled", "submitted", "submitting", "failed", "canceled"},
    "reconciled": set(),
    "failed": set(),
    "canceled": set(),
}


def _transition_case() -> str:
    pairs = []
    for old, news in ORDER_TRANSITIONS.items():
        for new in sorted(news):
            pairs.append(f"('{old}','{new}')")
    return ", ".join(pairs)


def upgrade_statements() -> list[str]:
    stmts: list[str] = []
    for table in TENANT_SCOPED_TABLES:
        stmts += [
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
            f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
            f"""CREATE POLICY tenant_isolation ON {table}
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)""",
        ]
    stmts.append(
        f"""CREATE OR REPLACE FUNCTION enforce_order_intent_transition() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'INSERT' THEN
            IF NEW.status NOT IN ('created', 'approved') THEN
              RAISE EXCEPTION 'order intent must start as created or approved, got %', NEW.status
                USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
          END IF;
          IF NEW.status = OLD.status THEN
            RETURN NEW;
          END IF;
          IF (OLD.status, NEW.status) NOT IN (VALUES {_transition_case()}) THEN
            RAISE EXCEPTION 'invalid order intent transition % -> %', OLD.status, NEW.status
              USING ERRCODE = 'check_violation';
          END IF;
          IF NEW.intent_key <> OLD.intent_key OR NEW.approved_fingerprint <> OLD.approved_fingerprint
             OR NEW.max_amount <> OLD.max_amount OR NEW.approval_request_id <> OLD.approval_request_id THEN
            RAISE EXCEPTION 'order intent binding is immutable' USING ERRCODE = 'check_violation';
          END IF;
          NEW.updated_at := now();
          RETURN NEW;
        END $$ LANGUAGE plpgsql"""
    )
    stmts.append(
        """CREATE TRIGGER order_intent_transition BEFORE INSERT OR UPDATE ON order_intents
           FOR EACH ROW EXECUTE FUNCTION enforce_order_intent_transition()"""
    )
    stmts.append(
        """CREATE OR REPLACE FUNCTION reject_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
        END $$ LANGUAGE plpgsql"""
    )
    for table in ("audit_events", "quotes", "quote_lines", "policy_decisions", "approvals"):
        stmts.append(
            f"""CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION reject_mutation()"""
        )
    # Approval decisions: one decision per request; only these status moves are legal.
    stmts.append(
        """CREATE OR REPLACE FUNCTION enforce_approval_request_transition() RETURNS trigger AS $$
        BEGIN
          IF NEW.status = OLD.status THEN RETURN NEW; END IF;
          IF (OLD.status, NEW.status) NOT IN (VALUES ('pending','approved'), ('pending','rejected'),
              ('pending','expired'), ('pending','invalidated'), ('approved','consumed'),
              ('approved','invalidated'), ('approved','expired')) THEN
            RAISE EXCEPTION 'invalid approval request transition % -> %', OLD.status, NEW.status
              USING ERRCODE = 'check_violation';
          END IF;
          IF NEW.fingerprint <> OLD.fingerprint THEN
            RAISE EXCEPTION 'approval fingerprint is immutable' USING ERRCODE = 'check_violation';
          END IF;
          RETURN NEW;
        END $$ LANGUAGE plpgsql"""
    )
    stmts.append(
        """CREATE TRIGGER approval_request_transition BEFORE UPDATE ON approval_requests
           FOR EACH ROW EXECUTE FUNCTION enforce_approval_request_transition()"""
    )
    # At most one in-flight intent per run: the run lock for purchasing side effects.
    stmts.append(
        """CREATE UNIQUE INDEX uq_order_intent_active_per_run ON order_intents (run_id)
           WHERE status IN ('created','approved','submitting','submitted','unknown','cancellation_requested')"""
    )
    stmts.append(
        """CREATE UNIQUE INDEX uq_one_active_run_per_request ON procurement_runs (request_id)
           WHERE status IN ('queued','running','awaiting_approval','submitting','reconciling',
                            'cancellation_requested')"""
    )
    # Runtime role: DML only, no DDL; audit/quotes are insert+select only.
    stmts += [
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO procnav_app",
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO procnav_app",
        "REVOKE UPDATE, DELETE ON audit_events, quotes, quote_lines, policy_decisions, approvals FROM procnav_app",
        "REVOKE ALL ON alembic_version FROM procnav_app",
    ]
    return stmts


def downgrade_statements() -> list[str]:
    stmts = [
        "DROP TRIGGER IF EXISTS order_intent_transition ON order_intents",
        "DROP TRIGGER IF EXISTS approval_request_transition ON approval_requests",
        "DROP FUNCTION IF EXISTS enforce_order_intent_transition()",
        "DROP FUNCTION IF EXISTS enforce_approval_request_transition()",
    ]
    for table in ("audit_events", "quotes", "quote_lines", "policy_decisions", "approvals"):
        stmts.append(f"DROP TRIGGER IF EXISTS {table}_append_only ON {table}")
    stmts.append("DROP FUNCTION IF EXISTS reject_mutation()")
    for table in TENANT_SCOPED_TABLES:
        stmts.append(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    return stmts
