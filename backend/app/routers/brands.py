from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("", response_model=list[schemas.BrandOut])
def list_brands(db: Session = Depends(get_db)):
    return db.query(models.Brand).order_by(models.Brand.id).all()


@router.get("/{slug}", response_model=schemas.BrandOut)
def get_brand(slug: str, db: Session = Depends(get_db)):
    brand = db.query(models.Brand).filter(models.Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return brand
