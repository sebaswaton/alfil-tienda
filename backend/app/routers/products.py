import os
import re
import secrets
import unicodedata
from io import BytesIO
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.storage import StorageUnavailableError, put_object, remove_object

router = APIRouter(prefix="/api/products", tags=["products"])

IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
IMAGE_MAX_BYTES = 10 * 1024 * 1024
PDF_MAX_BYTES = 25 * 1024 * 1024


def require_media_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
):
    expected = os.getenv("MEDIA_ADMIN_API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="La carga de archivos no está habilitada: configura MEDIA_ADMIN_API_KEY",
        )
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Clave de administración inválida")


def safe_filename(filename: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode()
    stem, extension = os.path.splitext(normalized)
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-._") or fallback
    extension = re.sub(r"[^a-zA-Z0-9.]", "", extension.lower())
    return f"{stem[:100]}{extension[:10]}"


def safe_path_segment(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-") or "producto"


def matches_file_signature(media_type: str, content_type: str, contents: bytes) -> bool:
    if media_type == "document":
        return contents.startswith(b"%PDF-")
    if content_type == "image/jpeg":
        return contents.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return contents.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"
    return False


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

    object_name = (
        f"products/{safe_path_segment(product.sku)}/{folder}/"
        f"{uuid4().hex}{final_extension}"
    )
    try:
        storage_uri = put_object(
            object_name,
            BytesIO(contents),
            len(contents),
            content_type,
            metadata={"original-filename": original_name, "product-sku": product.sku},
        )
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if media_type == "image":
        media = models.ProductImage(
            product_id=product.id,
            url=storage_uri,
            alt=(alt or product.name).strip()[:200],
            sort_order=sort_order,
        )
    else:
        document_title = (title or "").strip() or "Ficha técnica"
        media = models.ProductDocument(
            product_id=product.id,
            title=document_title[:200],
            document_type=document_type,
            storage_uri=storage_uri,
            original_filename=original_name,
            mime_type=content_type,
            size_bytes=len(contents),
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
        )
        .limit(4)
        .all()
    )
    return related
