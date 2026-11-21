"""Login, logout and the current user."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.api.deps import COOKIE_NAME, CurrentUser, Db
from app.api.schemas import LoginRequest, LoginResponse, UserOut
from app.core.config import get_settings
from app.core.security import create_token, verify_password
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role,
        team_id=user.team_id, team_name=user.team.name if user.team else None,
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Db) -> LoginResponse:
    user = db.scalars(
        select(User).where(func.lower(User.email) == body.email.strip().lower())
    ).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    settings = get_settings()
    token = create_token(user.id, user.role)
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax",
        secure=settings.environment == "prod", max_age=settings.jwt_expire_minutes * 60,
    )
    return LoginResponse(access_token=token, user=user_out(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return user_out(user)
