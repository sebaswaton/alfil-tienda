import os
import secrets
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.auth import require_admin
from app.database import get_db
from app import models, schemas
from app.product_media import (
    IMAGE_MAX_BYTES,
    IMAGE_TYPES,
    PDF_MAX_BYTES,
    build_product_document,
    build_product_image,
    matches_file_signature,
    safe_filename,
    save_product_media_object,
)
from app.storage import StorageUnavailableError, remove_object

router = APIRouter(prefix="/api/products", tags=["products"])

def require_media_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
):
    expected = os.getenv("MEDIA_ADMIN_API_KEY", "")
    if expected and x_admin_key and secrets.compare_digest(x_admin_key, expected):
        return
    if authorization:
        require_admin(authorization, db)
        return
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="La carga de archivos no está habilitada",
        )
    raise HTTPException(status_code=401, detail="Inicia sesión para cargar archivos")


@router.get("", response_model=schemas.ProductListResponse)
def list_products(
    brand: str | None = None,
    category: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    db: Session = Depends(get_db),
):
    query = db.query(models.Product).options(
        joinedload(models.Product.brand),
        joinedload(models.Product.category),
        joinedload(models.Product.images),
    ).filter(
        models.Product.status == "active",
        models.Product.available_stock > 0,
        models.Product.brand.has(models.Brand.is_active.is_(True)),
        models.Product.category.has(models.Category.is_active.is_(True)),
    )

    if brand:
        query = query.join(models.Brand).filter(models.Brand.slug == brand)
    if category:
        query = query.join(models.Category).filter(models.Category.slug == category)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(models.Product.name.ilike(like), models.Product.short_description.ilike(like))
        )

    total = query.count()
    items = (
        query.order_by(models.Product.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return schemas.ProductListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{slug}", response_model=schemas.ProductDetail)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.brand),
            joinedload(models.Product.category),
            joinedload(models.Product.images),
            joinedload(models.Product.documents),
            joinedload(models.Product.sources),
            joinedload(models.Product.faqs),
        )
        .filter(
            models.Product.slug == slug,
            models.Product.status == "active",
            models.Product.available_stock > 0,
            models.Product.brand.has(models.Brand.is_active.is_(True)),
            models.Product.category.has(models.Category.is_active.is_(True)),
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/{slug}/media", status_code=201)
async def upload_product_media(
    slug: str,
    media_type: Annotated[Literal["image", "document"], Form()],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    alt: Annotated[str | None, Form()] = None,
    document_type: Annotated[
        Literal["datasheet", "manual", "warranty", "brochure", "other"], Form()
    ] = "datasheet",
    is_official: Annotated[bool, Form()] = False,
    sort_order: Annotated[int, Form(ge=0, le=1000)] = 0,
    db: Session = Depends(get_db),
    _: None = Depends(require_media_admin),
):
    """Upload a product image or PDF to the private MinIO bucket."""
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    original_name = safe_filename(file.filename or "archivo", "archivo")
    extension = os.path.splitext(original_name)[1]
    content_type = (file.content_type or "").lower()

    if media_type == "image":
        expected_extension = IMAGE_TYPES.get(content_type)
        if not expected_extension or extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(
                status_code=415,
                detail="La imagen debe ser JPG, PNG o WebP",
            )
        max_bytes = IMAGE_MAX_BYTES
        folder = "images"
        final_extension = expected_extension
    else:
        if content_type != "application/pdf" or extension != ".pdf":
            raise HTTPException(status_code=415, detail="El documento debe ser un archivo PDF")
        max_bytes = PDF_MAX_BYTES
        folder = "documents"
        final_extension = ".pdf"

    contents = await file.read(max_bytes + 1)
    await file.close()
    if len(contents) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"El archivo supera el límite de {limit_mb} MB")
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if not matches_file_signature(media_type, content_type, contents):
        raise HTTPException(
            status_code=415,
            detail="El contenido del archivo no coincide con su formato declarado",
        )

    try:
        storage_uri = save_product_media_object(
            product,
            folder,
            contents,
            final_extension,
            content_type,
            original_name,
        )
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if media_type == "image":
        media = build_product_image(
            product,
            storage_uri,
            sort_order=sort_order,
            alt=alt,
        )
    else:
        document_title = (title or "").strip() or "Ficha técnica"
        media = build_product_document(
            product,
            storage_uri,
            original_filename=original_name,
            size_bytes=len(contents),
            title=document_title,
            document_type=document_type,
            is_official=is_official,
            sort_order=sort_order,
        )

    try:
        db.add(media)
        db.commit()
        db.refresh(media)
    except Exception:
        db.rollback()
        remove_object(storage_uri)
        raise

    if media_type == "image":
        return {
            "id": media.id,
            "media_type": "image",
            "url": media.resolved_url,
            "alt": media.alt,
        }
    return {
        "id": media.id,
        "media_type": "document",
        "title": media.title,
        "download_url": media.download_url,
    }


@router.get("/{slug}/related", response_model=list[schemas.ProductListItem])
def get_related_products(slug: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    related = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.brand),
            joinedload(models.Product.category),
            joinedload(models.Product.images),
        )
        .filter(
            models.Product.category_id == product.category_id,
            models.Product.id != product.id,
            models.Product.status == "active",
            models.Product.available_stock > 0,
            models.Product.brand.has(models.Brand.is_active.is_(True)),
            models.Product.category.has(models.Category.is_active.is_(True)),
        )
        .limit(4)
        .all()
    )
    return related
