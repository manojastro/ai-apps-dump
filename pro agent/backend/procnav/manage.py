"""Operational commands.

python -m procnav.manage check-env     validate configuration and connectivity
python -m procnav.manage migrate       alembic upgrade + LangGraph checkpoint tables + grants
python -m procnav.manage seed          demo tenants, users, suppliers, policy (idempotent)
python -m procnav.manage reset-demo    DESTRUCTIVE: delete demo runs/requests/orders; refuses in production
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from pathlib import Path

from sqlalchemy import select, text

from .auth.service import hash_password
from .core.config import REPO_ROOT, get_settings
from .core.db import owner_engine
from .core.models import (
    Membership,
    PolicyVersion,
    Supplier,
    SupplierCredentialMetadata,
    Tenant,
    User,
)
from .policies.defaults import DEFAULT_POLICY

DEMO_TENANTS = {
    "acme": "Acme Manufacturing (demo)",
    "globex": "Globex Services (demo)",
}
DEMO_USERS = [
    ("requester", "Riya Requester", ["requester"]),
    ("approver", "Arjun Approver", ["approver"]),
    ("admin", "Asha Admin", ["admin"]),
    ("viewer", "Vik Viewer", ["viewer"]),
]
SUPPLIERS = {
    "alpha": ("Alpha Supply", "ALPHA_URL", "http://127.0.0.1:8301"),
    "beta": ("Beta Devices", "BETA_URL", "http://127.0.0.1:8302"),
    "gamma": ("Gamma Trade", "GAMMA_URL", "http://127.0.0.1:8303"),
}


def cmd_check_env() -> int:
    s = get_settings()
    print(f"APP_ENV={s.app_env} MODEL_MODE={s.model_mode} DRY_RUN={s.dry_run} origins={s.allowed_origins}")
    with owner_engine().connect() as conn:
        print("database:", conn.execute(text("select version()")).scalar().split(",")[0])
    return 0


def cmd_migrate() -> int:
    from alembic.config import Config
    from langgraph.checkpoint.postgres import PostgresSaver

    from alembic import command

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    command.upgrade(cfg, "head")
    url = get_settings().app_migration_database_url.replace("postgresql+psycopg://", "postgresql://")
    with PostgresSaver.from_conn_string(url) as saver:
        saver.setup()
    with owner_engine().begin() as conn:
        conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO procnav_app"))
        conn.execute(text("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO procnav_app"))
        conn.execute(
            text(
                "REVOKE UPDATE, DELETE ON audit_events, quotes, quote_lines, policy_decisions, approvals "
                "FROM procnav_app"
            )
        )
        conn.execute(text("REVOKE ALL ON alembic_version FROM procnav_app"))
    print("migrations applied; checkpoint tables ready")
    return 0


def _demo_password() -> str:
    s = get_settings()
    pw = os.environ.get("DEMO_PASSWORD")
    if pw:
        return pw
    if s.app_env == "production":
        pw = secrets.token_urlsafe(18)
        print(f"Generated demo password (shown once): {pw}")
        return pw
    return "procnav-demo"


def cmd_seed() -> int:
    from sqlalchemy.orm import Session

    password = _demo_password()
    with Session(owner_engine()) as s, s.begin():
        for slug, name in DEMO_TENANTS.items():
            tenant = s.scalar(select(Tenant).where(Tenant.slug == slug))
            if tenant is None:
                tenant = Tenant(slug=slug, name=name)
                s.add(tenant)
                s.flush()
            for local, display, roles in DEMO_USERS:
                email = f"{local}@{slug}.test"
                user = s.scalar(select(User).where(User.email == email))
                if user is None:
                    user = User(email=email, display_name=f"{display} ({slug})", password_hash=hash_password(password))
                    s.add(user)
                    s.flush()
                for role in roles:
                    if not s.scalar(
                        select(Membership.id).where(
                            Membership.user_id == user.id, Membership.tenant_id == tenant.id, Membership.role == role
                        )
                    ):
                        s.add(Membership(tenant_id=tenant.id, user_id=user.id, role=role))
            for key, (sname, env, default) in SUPPLIERS.items():
                sup = s.scalar(select(Supplier).where(Supplier.tenant_id == tenant.id, Supplier.key == key))
                base = os.environ.get(env, default).rstrip("/")
                if sup is None:
                    sup = Supplier(
                        tenant_id=tenant.id,
                        key=key,
                        name=sname,
                        base_url=base,
                        allowed_origins=[base],
                        adapter="semantic_portal_v1",
                        is_simulated=True,
                        enabled=True,
                        eligibility_status="approved",
                        status_api_supported=False,
                        conditional_submit_supported=True,
                        config={"synthetic": True},
                    )
                    s.add(sup)
                    s.flush()
                    s.add(
                        SupplierCredentialMetadata(
                            tenant_id=tenant.id,
                            supplier_id=sup.id,
                            credential_ref=f"supplier/{slug}/{key}",
                            username_hint=f"{slug}-b***",
                        )
                    )
                else:
                    sup.base_url = base
                    sup.allowed_origins = [base]
            if not s.scalar(select(PolicyVersion.id).where(PolicyVersion.tenant_id == tenant.id)):
                s.add(PolicyVersion(tenant_id=tenant.id, version=1, rules=DEFAULT_POLICY, active=True))
    print(f"seeded tenants {list(DEMO_TENANTS)}; users <role>@<tenant>.test")
    return 0


def cmd_reset_demo(force_production: bool) -> int:
    s = get_settings()
    if s.app_env == "production" and not force_production:
        print("refusing to reset demo data in production (pass --i-understand-this-deletes-production-data)")
        return 2
    tables = [
        "run_events",
        "audit_events",
        "supplier_orders",
        "order_attempts",
        "order_intents",
        "approvals",
        "approval_requests",
        "policy_decisions",
        "policy_exceptions",
        "quote_lines",
        "quotes",
        "browser_steps",
        "evidence_artifacts",
        "jobs",
        "procurement_runs",
        "request_items",
        "procurement_requests",
        "idempotency_keys",
        "browser_session_states",
        "eval_runs",
    ]
    with owner_engine().begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(tables) + " CASCADE"))
        for t in ("checkpoints", "checkpoint_blobs", "checkpoint_writes"):
            conn.execute(text(f"TRUNCATE {t}"))
    evidence = Path(s.evidence_dir)
    if evidence.exists() and Path(REPO_ROOT) in evidence.resolve().parents:
        for f in evidence.rglob("*"):
            if f.is_file():
                f.unlink()
    print("demo data reset (users, tenants, suppliers and policies kept)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="procnav.manage")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-env")
    sub.add_parser("migrate")
    sub.add_parser("seed")
    reset = sub.add_parser("reset-demo")
    reset.add_argument("--i-understand-this-deletes-production-data", dest="force", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "check-env":
        return cmd_check_env()
    if args.cmd == "migrate":
        return cmd_migrate()
    if args.cmd == "seed":
        return cmd_seed()
    return cmd_reset_demo(args.force)


if __name__ == "__main__":
    sys.exit(main())
