"""Idempotent additive upgrades for the existing cPanel database."""

from sqlalchemy import inspect, text

from app.database import engine


ADDITIVE_COLUMNS = {
    "brands": {
        "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "categories": {
        "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "products": {
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
}


def apply_additive_schema_upgrades() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table, columns in ADDITIVE_COLUMNS.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(
                        text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}')
                    )
