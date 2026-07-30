import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal, get_db

PBKDF2_ITERATIONS = 310_000
SESSION_HOURS = 12


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: models.AdminUser) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_HOURS)
    db.add(
        models.AdminSession(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=expires_at,
        )
    )
    user.last_login_at = datetime.utcnow()
    db.commit()
    return token, expires_at


def extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar")
    return authorization.split(" ", 1)[1].strip()


def require_admin(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> models.AdminUser:
    token = extract_bearer(authorization)
    session = (
        db.query(models.AdminSession)
        .filter(
            models.AdminSession.token_hash == token_digest(token),
            models.AdminSession.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not session or not session.user.active:
        raise HTTPException(status_code=401, detail="La sesión venció. Vuelve a ingresar")
    return session.user


def ensure_initial_admin() -> None:
    """Create the first account only from explicit environment variables."""
    username = os.getenv("ADMIN_INITIAL_USERNAME", "").strip().lower()
    password = os.getenv("ADMIN_INITIAL_PASSWORD", "")
    if not username or not password:
        return
    if len(password) < 8:
        raise RuntimeError("ADMIN_INITIAL_PASSWORD debe tener al menos 8 caracteres")

    db = SessionLocal()
    try:
        if db.query(models.AdminUser).count() == 0:
            db.add(
                models.AdminUser(
                    username=username,
                    full_name=os.getenv("ADMIN_INITIAL_FULL_NAME", "Administrador"),
                    password_hash=hash_password(password),
                    role="admin",
                )
            )
            db.commit()
    finally:
        db.close()
