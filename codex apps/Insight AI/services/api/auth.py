import hashlib
import secrets
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy import select

from services.api.db import LoginSession, Session, User

passwords = PasswordHash.recommended()
attempts = defaultdict(deque)


def digest(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request):
    token = request.cookies.get("pl_session", "")
    if not token:
        raise HTTPException(401, "AUTH_REQUIRED")
    with Session() as db:
        session = db.scalar(
            select(LoginSession).where(
                LoginSession.token_hash == digest(token), LoginSession.expires_at > time.time()
            )
        )
        if not session:
            raise HTTPException(401, "AUTH_REQUIRED")
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
                raise HTTPException(403, "CSRF_INVALID")
        user = db.get(User, session.user_id)
        if not user:
            raise HTTPException(401, "AUTH_REQUIRED")
        request.state.csrf = session.csrf
        return user


def require(*roles):
    def check(user: User = Depends(current_user)):
        if user.role not in roles and user.role != "administrator":
            raise HTTPException(403, "ROLE_FORBIDDEN")
        return user

    return check


def throttle_login(key):
    now = time.time()
    bucket = attempts[key]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= 8:
        raise HTTPException(429, "LOGIN_RATE_LIMITED")
    bucket.append(now)
