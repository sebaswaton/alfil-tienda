from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app import admin_schemas
from app.auth.dependencies import CurrentAdmin
from app.database import get_db
from app.services import media_service, taxonomy_service


router = APIRouter(prefix="/api/admin/brands", tags=["admin-brands"])


@router.get("", response_model=admin_schemas.AdminBrandListResponse)
def list_brands(
    _: CurrentAdmin,
    q: str | None = Query(default=None, max_length=160),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Literal["name", "slug", "updated_at"] = "name",
    direction: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    return taxonomy_service.list_brands(
        db,
        q=q,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.get("/{brand_id}", response_model=admin_schemas.AdminBrandOut)
def get_brand(brand_id: int, _: CurrentAdmin, db: Session = Depends(get_db)):
    return taxonomy_service.brand_out(db, taxonomy_service.get_brand(db, brand_id))


@router.post("", response_model=admin_schemas.AdminBrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(
    payload: admin_schemas.AdminBrandCreate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return taxonomy_service.create_brand(db, payload)


@router.patch("/{brand_id}", response_model=admin_schemas.AdminBrandOut)
def update_brand(
    brand_id: int,
    payload: admin_schemas.AdminBrandUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return taxonomy_service.update_brand(db, brand_id, payload)


@router.put("/{brand_id}/logo", response_model=admin_schemas.AdminBrandOut)
async def replace_brand_logo(
    brand_id: int,
    file: Annotated[UploadFile, File()],
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    brand = taxonomy_service.get_brand(db, brand_id)
    await media_service.replace_taxonomy_asset(
        db,
        brand,
        attribute="logo_url",
        resource="brands",
        file=file,
    )
    return taxonomy_service.brand_out(db, brand)


@router.delete("/{brand_id}/logo", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand_logo(
    brand_id: int,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    brand = taxonomy_service.get_brand(db, brand_id)
    media_service.delete_taxonomy_asset(db, brand, attribute="logo_url")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{brand_id}/status", response_model=admin_schemas.AdminBrandOut)
def update_brand_status(
    brand_id: int,
    payload: admin_schemas.AdminActiveUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return taxonomy_service.update_brand_status(db, brand_id, payload.is_active)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, _: CurrentAdmin, db: Session = Depends(get_db)):
    taxonomy_service.delete_brand(db, brand_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
