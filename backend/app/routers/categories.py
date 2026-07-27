from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return (
        db.query(models.Category)
        .filter(models.Category.is_active.is_(True))
        .order_by(models.Category.id)
        .all()
    )


@router.get("/{slug}", response_model=schemas.CategoryOut)
def get_category(slug: str, db: Session = Depends(get_db)):
    category = (
        db.query(models.Category)
        .filter(models.Category.slug == slug, models.Category.is_active.is_(True))
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category
