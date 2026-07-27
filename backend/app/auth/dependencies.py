import os
import secrets
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app import models
from app.auth.security import hash_token, utc_now
from app.database import get_db


SESSION_COOKIE_NAME = os.getenv("ADMIN_SESSION_COOKIE_NAME", "alfil_admin_session")
CSRF_COOKIE_NAME = os.getenv("ADMIN_CSRF_COOKIE_NAME", "alfil_admin_csrf")
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión administrativa inválida o expirada",
    )


def require_admin_session(
    request: Request,
    db: Session = Depends(get_db),
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_COOKIE_NAME)] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> models.AdminUser:
    if not session_token:
        raise _unauthorized()

    session = (
        db.query(models.AdminSession)
        .options(joinedload(models.AdminSession.user))
        .filter(models.AdminSession.token_hash == hash_token(session_token))
        .first()
    )
    now = utc_now()
    if not session or session.expires_at.replace(tzinfo=session.expires_at.tzinfo or now.tzinfo) <= now:
        if session:
            db.delete(session)
            db.commit()
        raise _unauthorized()
    if not session.user.is_active:
        raise HTTPException(status_code=403, detail="El usuario administrador está desactivado")

    if request.method not in SAFE_METHODS:
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(status_code=403, detail="Token CSRF inválido")
        if not secrets.compare_digest(hash_token(csrf_header), session.csrf_token_hash):
            raise HTTPException(status_code=403, detail="Token CSRF inválido")

    return session.user


CurrentAdmin = Annotated[models.AdminUser, Depends(require_admin_session)]
