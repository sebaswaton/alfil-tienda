import argparse
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app import models
from app.auth.security import hash_password
from app.database import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea el administrador inicial de Alfil")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="Omite esta opción para solicitarla de forma segura")
    args = parser.parse_args()

    email = args.email.strip().lower()
    password = args.password or getpass("Contraseña (mínimo 8 caracteres): ")
    if len(password) < 8 or len(password) > 128:
        raise SystemExit("La contraseña debe tener entre 8 y 128 caracteres")

    with SessionLocal() as db:
        db.add(models.AdminUser(email=email, password_hash=hash_password(password)))
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise SystemExit("Ya existe un administrador con ese correo") from exc
    print(f"Administrador creado: {email}")


if __name__ == "__main__":
    main()
