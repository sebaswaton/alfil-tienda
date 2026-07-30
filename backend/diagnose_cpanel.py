"""Produce a secret-redacted cPanel deployment diagnostic report."""

from __future__ import annotations

import os
import platform
import traceback
from pathlib import Path


REPORT_PATH = Path(__file__).with_name("cpanel-diagnostic.txt")
SECRET_NAMES = (
    "DATABASE_URL",
    "MEDIA_SIGNING_SECRET",
    "MEDIA_ADMIN_API_KEY",
)


def redact(value: object) -> str:
    text = str(value)
    for name in SECRET_NAMES:
        secret = os.getenv(name)
        if secret:
            text = text.replace(secret, f"<{name}_REDACTED>")

    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        try:
            from sqlalchemy.engine import make_url

            parsed = make_url(database_url)
            if parsed.password:
                text = text.replace(parsed.password, "<DB_PASSWORD_REDACTED>")
        except Exception:
            pass
    return text


def record(lines: list[str], label: str, action) -> None:
    try:
        result = action()
        lines.append(f"[OK] {label}: {redact(result)}")
    except Exception as exc:
        lines.append(f"[ERROR] {label}: {redact(type(exc).__name__)}: {redact(exc)}")
        lines.append(redact(traceback.format_exc()))


def main() -> None:
    lines = [
        "ALFIL CPANEL DIAGNOSTIC",
        f"Python: {platform.python_version()}",
        f"Executable: {platform.python_implementation()}",
    ]

    record(
        lines,
        "Required environment variables",
        lambda: ", ".join(
            name
            for name in (
                "DATABASE_URL",
                "STORAGE_BACKEND",
                "LOCAL_MEDIA_ROOT",
                "MEDIA_SIGNING_SECRET",
                "MEDIA_ADMIN_API_KEY",
                "APPLICATION_BASE_PATH",
            )
            if os.getenv(name)
        ),
    )

    def dependencies() -> str:
        import a2wsgi
        import fastapi
        import psycopg
        import sqlalchemy

        return (
            f"fastapi={fastapi.__version__}, "
            f"sqlalchemy={sqlalchemy.__version__}, "
            f"psycopg={psycopg.__version__}, "
            f"a2wsgi={getattr(a2wsgi, '__version__', 'installed')}"
        )

    record(lines, "Python dependencies", dependencies)

    def database() -> str:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url

        database_url = os.environ["DATABASE_URL"]
        parsed = make_url(database_url)
        safe_target = f"{parsed.username}@{parsed.host}:{parsed.port}/{parsed.database}"
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            version = connection.execute(text("SHOW server_version")).scalar_one()
            products = connection.execute(
                text("SELECT COUNT(*) FROM products")
            ).scalar_one()
        return f"target={safe_target}, PostgreSQL={version}, products={products}"

    record(lines, "PostgreSQL connection and catalog", database)

    def media() -> str:
        root = Path(os.environ["LOCAL_MEDIA_ROOT"])
        if not root.is_dir():
            raise RuntimeError(f"directory does not exist: {root}")
        files = sum(1 for path in root.rglob("*") if path.is_file())
        if not os.access(root, os.R_OK | os.X_OK):
            raise RuntimeError(f"directory is not readable: {root}")
        return f"root={root}, files={files}"

    record(lines, "Local media storage", media)

    def passenger() -> str:
        from passenger_wsgi import application

        return f"callable={callable(application)}"

    record(lines, "Passenger application import", passenger)

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Diagnostic written to {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
