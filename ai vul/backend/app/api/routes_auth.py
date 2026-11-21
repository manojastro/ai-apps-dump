from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.types import utcnow
from app.models.identity import User
from app.security.auth import COOKIE_NAME, Principal, create_session_token, get_current_user
from app.security.passwords import verify_password
from app.security.ratelimit import SlidingWindowLimiter
from app.services.audit import record_audit

router = APIRouter(tags=["auth"])
login_limiter = SlidingWindowLimiter(get_settings().login_rate_limit_per_minute, 60)


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=256)
    include_token: bool = False  # API clients may request a bearer token; browsers rely on the HttpOnly cookie


@router.post("/api/auth/login")
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    ip = request.client.host if request.client else "unknown"
    if not login_limiter.allow(f"{ip}:{body.email.lower()}"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts; try again in a minute")
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower().strip()))
    ok = verify_password(user.password_hash if user else None, body.password)
    if not ok or user is None or not user.is_active:
        record_audit(
            db,
            actor=None,
            action="login_failed",
            target_type="user",
            target_id=user.id if user else None,
            details={"email": body.email[:255]},
            outcome="denied",
            ip_address=ip,
        )
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = create_session_token(user)
    s = get_settings()
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, secure=s.cookie_secure, samesite="lax", max_age=s.session_ttl_minutes * 60, path="/"
    )
    user.last_login_at = utcnow()
    principal = Principal.from_user(user)
    record_audit(db, actor=principal, action="login", target_type="user", target_id=user.id, ip_address=ip)
    db.commit()
    return {"user": principal.__dict__} | ({"token": token} if body.include_token else {})


@router.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Always clears the session cookie, even when the session already expired."""
    response.delete_cookie(COOKIE_NAME, path="/")
    try:
        principal = get_current_user(request, db)
    except HTTPException:
        return {"ok": True}
    record_audit(db, actor=principal, action="logout", target_type="user", target_id=principal.id)
    db.commit()
    return {"ok": True}


@router.get("/api/auth/me")
def me(principal: Principal = Depends(get_current_user)) -> dict:
    return {"user": principal.__dict__}


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "aegisremediate-backend"}


@router.get("/api/health/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on DB outage
        raise HTTPException(503, f"database unavailable: {type(exc).__name__}") from exc
    s = get_settings()
    return {
        "status": "ready",
        "database": "postgresql" if not s.is_sqlite else "sqlite",
        "ai_provider": s.ai_provider,
        "servicenow_mode": s.servicenow_mode,
        "threat_intel_mode": s.threat_intel_mode,
    }
