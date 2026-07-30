"""One-time cPanel bootstrap. Delete this file immediately after running it."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import models
from app.auth import hash_password
from app.database import Base, SessionLocal, engine

def main():
    username = os.getenv("ADMIN_INITIAL_USERNAME", "").strip().lower()
    password = os.getenv("ADMIN_INITIAL_PASSWORD", "")
    full_name = os.getenv("ADMIN_INITIAL_FULL_NAME", "Administrador").strip()

    if not username:
        raise RuntimeError("Falta la variable ADMIN_INITIAL_USERNAME")
    if len(password) < 8:
        raise RuntimeError(
            "ADMIN_INITIAL_PASSWORD debe contener al menos 8 caracteres"
        )

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = (
            db.query(models.AdminUser)
            .filter(models.AdminUser.username == username)
            .first()
        )
        if user is None:
            user = models.AdminUser(username=username)
            db.add(user)
            action = "creado"
        else:
            action = "restablecido"

        user.full_name = full_name or "Administrador"
        user.password_hash = hash_password(password)
        user.role = "admin"
        user.active = True
        db.flush()
        db.query(models.AdminSession).filter(
            models.AdminSession.user_id == user.id
        ).delete()
        db.commit()
        print(f"ADMIN_OK: usuario '{username}' {action} correctamente")
    finally:
        db.close()


if __name__ == "__main__":
    main()
