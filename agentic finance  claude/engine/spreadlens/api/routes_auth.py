from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.api.deps import J
from spreadlens.db import get_db
from spreadlens.models import Membership, Organization, Workspace
from spreadlens.security.auth import Principal, get_principal, login, logout
from spreadlens.services.audit import audit

router = APIRouter(prefix="/api", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def do_login(body: LoginIn, db: Session = Depends(get_db)):
    res = login(db, body.email, body.password)
    if res is None:
        db.commit()
        raise HTTPException(401, "Invalid email or password")
    token, user = res
    return J({"token": token, "user": {"id": user.id, "email": user.email, "display_name": user.display_name}})


@router.post("/auth/logout")
def do_logout(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        logout(db, auth[7:])
    return J({"ok": True})


@router.get("/me")
def me(p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    ws = {w.id: w for w in db.scalars(select(Workspace).where(Workspace.id.in_(list(p.memberships))))}
    return J({"user": {"id": p.user.id, "email": p.user.email, "display_name": p.user.display_name},
              "workspaces": [{"id": wid, "name": ws[wid].name, "role": role} for wid, role in p.memberships.items() if wid in ws]})


class WorkspaceIn(BaseModel):
    name: str


@router.post("/workspaces")
def create_workspace(body: WorkspaceIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    org = db.scalar(select(Organization).limit(1)) or Organization(name="Default organization")
    db.add(org)
    db.flush()
    ws = Workspace(organization_id=org.id, name=body.name.strip()[:200])
    db.add(ws)
    db.flush()
    db.add(Membership(workspace_id=ws.id, user_id=p.id, role="admin"))
    audit(db, ws.id, p.id, "workspace.create", "workspace", ws.id)
    return J({"id": ws.id, "name": ws.name, "role": "admin"}, 201)
