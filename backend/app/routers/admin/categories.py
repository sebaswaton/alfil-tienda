from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app import admin_schemas
from app.auth.dependencies import CurrentAdmin
from app.database import get_db
from app.services import media_service, taxonomy_service


router = APIRouter(prefix="/api/admin/categories", tags=["admin-categories"])


@router.get("", response_model=admin_schemas.AdminCategoryListResponse)
def list_categories(
    _: CurrentAdmin,
    q: str | None = Query(default=None, max_length=160),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Literal["name", "slug", "updated_at"] = "name",
    direction: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    return taxonomy_service.list_categories(
        db,
        q=q,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.get("/{category_id}", response_model=admin_schemas.AdminCategoryOut)
def get_category(category_id: int, _: CurrentAdmin, db: Session = Depends(get_db)):
    return taxonomy_service.category_out(db, taxonomy_service.get_category(db, category_id))


@router.post(
    "",
    response_model=admin_schemas.AdminCategoryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: admin_schemas.AdminCategoryCreate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return taxonomy_service.create_category(db, payload)


@router.patch("/{category_id}", response_model=admin_schemas.AdminCategoryOut)
def update_category(
    category_id: int,
    payload: admin_schemas.AdminCategoryUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return taxonomy_service.update_category(db, category_id, payload)


@router.put("/{category_id}/image", response_model=admin_schemas.AdminCategoryOut)
async def replace_category_image(
    category_id: int,
    file: Annotated[UploadFile, File()],
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    category = taxonomy_service.get_category(db, category_id)
    await media_service.replace_taxonomy_asset(
        db,
        category,
        attribute="image_url",
        resource="categories",
        file=file,
    )
    return taxonomy_service.category_out(db, category)


@router.delete("/{category_id}/image", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_image(
    category_id: int,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    category = taxonomy_service.get_category(db, category_id)
    media_service.delete_taxonomy_asset(db, category, attribute="image_url")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{category_id}/status", response_model=admin_schemas.AdminCategoryOut)
def update_category_status(
    category_id: int,
    payload: admin_schemas.AdminActiveUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return taxonomy_service.update_category_status(db, category_id, payload.is_active)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, _: CurrentAdmin, db: Session = Depends(get_db)):
    taxonomy_service.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
