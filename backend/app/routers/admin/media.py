from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app import admin_schemas
from app.auth.dependencies import CurrentAdmin
from app.database import get_db
from app.services import media_service


router = APIRouter(prefix="/api/admin/products", tags=["admin-product-media"])


@router.get(
    "/{product_id}/images",
    response_model=list[admin_schemas.AdminProductImageOut],
)
def list_product_images(
    product_id: int,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return media_service.list_images(db, product_id)


@router.post(
    "/{product_id}/images",
    response_model=admin_schemas.AdminProductImageOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: int,
    file: Annotated[UploadFile, File()],
    _: CurrentAdmin,
    alt: Annotated[str, Form(max_length=200)] = "",
    is_primary: Annotated[bool, Form()] = False,
    db: Session = Depends(get_db),
):
    return await media_service.upload_image(
        db,
        product_id,
        file,
        alt=alt,
        is_primary=is_primary,
    )


@router.patch(
    "/{product_id}/images/{image_id}",
    response_model=admin_schemas.AdminProductImageOut,
)
def update_product_image(
    product_id: int,
    image_id: int,
    payload: admin_schemas.AdminProductImageUpdate,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return media_service.update_image(db, product_id, image_id, payload)


@router.put(
    "/{product_id}/images/{image_id}/file",
    response_model=admin_schemas.AdminProductImageOut,
)
async def replace_product_image(
    product_id: int,
    image_id: int,
    file: Annotated[UploadFile, File()],
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return await media_service.replace_image(db, product_id, image_id, file)


@router.put(
    "/{product_id}/images/order",
    response_model=list[admin_schemas.AdminProductImageOut],
)
def order_product_images(
    product_id: int,
    payload: admin_schemas.AdminMediaOrder,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return media_service.reorder_images(db, product_id, payload.ordered_ids)


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product_image(
    product_id: int,
    image_id: int,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    media_service.delete_image(db, product_id, image_id)


@router.get(
    "/{product_id}/documents",
    response_model=list[admin_schemas.AdminProductDocumentOut],
)
def list_product_documents(
    product_id: int,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return media_service.list_documents(db, product_id)


@router.post(
    "/{product_id}/documents",
    response_model=admin_schemas.AdminProductDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_document(
    product_id: int,
    file: Annotated[UploadFile, File()],
    _: CurrentAdmin,
    title: Annotated[str, Form(max_length=200)] = "",
    document_type: Annotated[
        Literal["datasheet", "manual", "warranty", "brochure", "other"],
        Form(),
    ] = "datasheet",
    is_official: Annotated[bool, Form()] = False,
    db: Session = Depends(get_db),
):
    return await media_service.upload_document(
        db,
        product_id,
        file,
        title=title,
        document_type=document_type,
        is_official=is_official,
    )


@router.put(
    "/{product_id}/documents/{document_id}/file",
    response_model=admin_schemas.AdminProductDocumentOut,
)
async def replace_product_document(
    product_id: int,
    document_id: int,
    file: Annotated[UploadFile, File()],
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    return await media_service.replace_document(
        db, product_id, document_id, file
    )


@router.delete(
    "/{product_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product_document(
    product_id: int,
    document_id: int,
    _: CurrentAdmin,
    db: Session = Depends(get_db),
):
    media_service.delete_document(db, product_id, document_id)
