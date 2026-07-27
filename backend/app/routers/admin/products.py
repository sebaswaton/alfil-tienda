from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import admin_schemas
from app.auth.dependencies import CurrentAdmin
from app.database import get_db
from app.services import product_service


router = APIRouter(prefix="/api/admin/products", tags=["admin-products"])


@router.get("", response_model=admin_schemas.AdminProductListResponse)
def list_products(
    _: CurrentAdmin,
    q: str | None = Query(default=None, max_length=200),
    product_status: Literal["active", "inactive"] | None = Query(default=None, alias="status"),
    availability: Literal["in_stock", "out_of_stock"] | None = None,
    brand_id: int | None = Query(default=None, gt=0),
    category_id: int | None = Query(default=None, gt=0),
    is_used: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Literal["name", "sku", "stock", "created_at", "updated_at"] = "name",
    direction: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    return product_service.list_products(
        db,
        q=q,
        status=product_status,
        availability=availability,
        brand_id=brand_id,
        category_id=category_id,
        is_used=is_used,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.get("/{product_id}", response_model=admin_schemas.AdminProductOut)
def get_product(product_id: int, _: CurrentAdmin, db: Session = Depends(get_db)):
    return product_service.to_product_out(product_service.get_product(db, product_id))


@router.post("", response_model=admin_schemas.AdminProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: admin_schemas.AdminProductCreate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return product_service.create_product(db, payload)


@router.patch("/{product_id}", response_model=admin_schemas.AdminProductOut)
def update_product(
    product_id: int,
    payload: admin_schemas.AdminProductUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return product_service.update_product(db, product_id, payload)


@router.patch("/{product_id}/status", response_model=admin_schemas.AdminProductOut)
def update_product_status(
    product_id: int,
    payload: admin_schemas.AdminProductStatusUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return product_service.update_product_status(db, product_id, payload.status)
