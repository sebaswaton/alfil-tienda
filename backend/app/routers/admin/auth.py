import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app import admin_schemas, models
from app.auth.dependencies import CSRF_COOKIE_NAME, SESSION_COOKIE_NAME, CurrentAdmin
from app.auth.security import hash_password, hash_token, new_token, session_expiry, verify_password
from app.database import get_db


router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])
SESSION_TTL_HOURS = int(os.getenv("ADMIN_SESSION_TTL_HOURS", "12"))
COOKIE_SECURE = os.getenv("ADMIN_COOKIE_SECURE", "false").lower() == "true"
DUMMY_PASSWORD_HASH = hash_password("not-a-real-administrator-password")


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    max_age = SESSION_TTL_HOURS * 60 * 60
    common = {
        "secure": COOKIE_SECURE,
        "samesite": "lax",
        "max_age": max_age,
    }
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        httponly=True,
        path="/api/admin",
        **common,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        path="/",
        **common,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/api/admin")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


@router.post("/login", response_model=admin_schemas.AdminAuthOut)
def login(
    payload: admin_schemas.AdminLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    user = db.query(models.AdminUser).filter(models.AdminUser.email == email).first()
    password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    if not verify_password(payload.password, password_hash) or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="El usuario administrador está desactivado")

    session_token = new_token()
    csrf_token = new_token()
    session = models.AdminSession(
        id=str(uuid4()),
        user_id=user.id,
        token_hash=hash_token(session_token),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=session_expiry(SESSION_TTL_HOURS),
    )
    user.last_login_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    _set_auth_cookies(response, session_token, csrf_token)
    return admin_schemas.AdminAuthOut(user=user, csrf_token=csrf_token)


@router.get("/me", response_model=admin_schemas.AdminMeOut)
def me(admin: CurrentAdmin):
    return admin_schemas.AdminMeOut(user=admin)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        session = (
            db.query(models.AdminSession)
            .filter(models.AdminSession.token_hash == hash_token(session_token))
            .first()
        )
        if session:
            db.delete(session)
            db.commit()
    _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None
