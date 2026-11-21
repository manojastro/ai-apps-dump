"""Seed demo users, workspaces and the taxonomy table. Local demo credentials only.

    uv run python -m spreadlens.seed            # users + workspaces + taxonomy
    uv run python -m spreadlens.seed --demo     # also upload the bundled synthetic documents

Demo password comes from SPREADLENS_SEED_PASSWORD (default in .env.example). Never use in production.
"""

from __future__ import annotations

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.config import TAXONOMY_VERSION, get_settings
from spreadlens.db import session_scope
from spreadlens.models import CanonicalLineItem, Company, Membership, Organization, User, Workspace
from spreadlens.security.passwords import hash_password
from spreadlens.taxonomy.loader import load_taxonomy

USERS = [
    ("analyst@demo.local", "Asha Analyst", [("Demo Credit Team", "analyst")]),
    ("reviewer@demo.local", "Ravi Reviewer", [("Demo Credit Team", "reviewer")]),
    ("admin@demo.local", "Anil Admin", [("Demo Credit Team", "admin")]),
    ("other@demo.local", "Olga Other-Tenant", [("Other Tenant Workspace", "admin")]),
]


def seed(db: Session) -> dict[str, str]:
    pw = get_settings().seed_password
    org = db.scalar(select(Organization).where(Organization.name == "Demo organization"))
    if org is None:
        org = Organization(name="Demo organization")
        db.add(org)
        db.flush()
    ws_ids: dict[str, str] = {}
    for name in ("Demo Credit Team", "Other Tenant Workspace"):
        ws = db.scalar(select(Workspace).where(Workspace.name == name))
        if ws is None:
            ws = Workspace(organization_id=org.id, name=name)
            db.add(ws)
            db.flush()
        ws_ids[name] = ws.id
    for email, display, memberships in USERS:
        u = db.scalar(select(User).where(User.email == email))
        if u is None:
            u = User(email=email, display_name=display, password_hash=hash_password(pw))
            db.add(u)
            db.flush()
        for ws_name, role in memberships:
            if not db.scalar(select(Membership).where(Membership.user_id == u.id, Membership.workspace_id == ws_ids[ws_name])):
                db.add(Membership(user_id=u.id, workspace_id=ws_ids[ws_name], role=role))
    for item in load_taxonomy().items:
        if not db.scalar(select(CanonicalLineItem).where(CanonicalLineItem.code == item.code, CanonicalLineItem.taxonomy_version == TAXONOMY_VERSION)):
            db.add(CanonicalLineItem(taxonomy_version=TAXONOMY_VERSION, code=item.code, label=item.label, statement_type=item.statement,
                                     unit_type=item.unit, period_type=item.period, sign=item.sign, is_total=item.total,
                                     display_order=item.order, definition=", ".join(item.synonyms[:6])))
    if not db.scalar(select(Company).where(Company.workspace_id == ws_ids["Demo Credit Team"])):
        db.add(Company(workspace_id=ws_ids["Demo Credit Team"], name="Aravalli Polymers Limited", industry="Specialty chemicals (synthetic)"))
    return ws_ids


def upload_demo_documents() -> None:
    """Upload bundled synthetic fixtures through the API code path (TestClient), so the demo exercises the real flow."""
    from pathlib import Path

    from fastapi.testclient import TestClient

    from spreadlens.main import app
    from spreadlens.workflow.worker import Worker

    get_settings().run_worker_in_api = False  # process synchronously below; no background threads in this CLI
    root = Path(__file__).resolve().parents[1] / "fixtures" / "documents"
    with TestClient(app) as c:
        tok = c.post("/api/auth/login", json={"email": "analyst@demo.local", "password": get_settings().seed_password}).json()["token"]
        h = {"authorization": f"Bearer {tok}"}
        me = c.get("/api/me", headers=h).json()
        ws = next(w for w in me["workspaces"] if w["name"] == "Demo Credit Team")
        dash = c.get(f"/api/workspaces/{ws['id']}/dashboard", headers=h).json()
        company = next(x for x in dash["companies"] if x["name"] == "Aravalli Polymers Limited")
        for name in ("01_aravalli_fy25_standalone.pdf", "07_aravalli_fy26_restated_comparative.pdf"):
            with open(root / name, "rb") as f:
                r = c.post(f"/api/companies/{company['id']}/documents", headers=h, files={"file": (name, f, "application/pdf")})
                print(name, r.status_code)
        processed = Worker(get_settings()).drain()
        print(f"processed {processed} workflow tasks")


if __name__ == "__main__":
    with session_scope() as db:
        ids = seed(db)
    print("seeded workspaces:", ids)
    if "--demo" in sys.argv:
        upload_demo_documents()
