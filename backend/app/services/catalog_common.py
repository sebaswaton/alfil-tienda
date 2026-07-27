import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError


def slugify(value: str, max_length: int) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    slug = slug[:max_length].rstrip("-")
    if not slug:
        raise HTTPException(status_code=422, detail="No se pudo generar un slug válido")
    return slug


def ensure_unique(db, model, field_name: str, value: str, label: str, exclude_id=None) -> None:
    field = getattr(model, field_name)
    query = db.query(model.id).filter(func.lower(field) == value.lower())
    if exclude_id is not None:
        query = query.filter(model.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=409, detail=f"Ya existe {label} con ese {field_name}")


def commit_or_conflict(db, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def require_changes(values: dict) -> None:
    if not values:
        raise HTTPException(status_code=422, detail="Debes enviar al menos un campo para actualizar")
