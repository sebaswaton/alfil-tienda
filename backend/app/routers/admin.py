import re
import unicodedata
import os
from datetime import datetime
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.auth import create_session, require_admin, token_digest, verify_password
from app.database import get_db
from app.routers.products import (
    IMAGE_MAX_BYTES,
    IMAGE_TYPES,
    PDF_MAX_BYTES,
    matches_file_signature,
    safe_filename,
    safe_path_segment,
)
from app.storage import (
    StorageUnavailableError,
    put_object,
    remove_object_strict,
    resolve_media_url,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def taxonomy_out(db: Session, item, kind: str) -> dict:
    count_field = models.Product.brand_id if kind == "brand" else models.Product.category_id
    asset = item.resolved_logo_url if kind == "brand" else item.resolved_image_url
    result = {
        "id": item.id,
        "name": item.name,
        "slug": item.slug,
        "description": item.description,
        "is_active": item.is_active,
        "updated_at": item.updated_at,
        "product_count": db.query(models.Product).filter(count_field == item.id).count(),
    }
    if kind == "brand":
        result.update(accent_color=item.accent_color, logo_url=asset)
    else:
        result.update(icon=item.icon, image_url=asset)
    return result


def unique_slug(db: Session, name: str, product_id: int | None = None) -> str:
    base = slugify(name) or "producto"
    candidate = base
    suffix = 2
    while True:
        query = db.query(models.Product).filter(models.Product.slug == candidate)
        if product_id:
            query = query.filter(models.Product.id != product_id)
        if not query.first():
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def audit(
    db: Session,
    user: models.AdminUser,
    action: str,
    entity_id: int | None,
    detail: dict | None = None,
):
    db.add(
        models.AdminAuditLog(
            user_id=user.id,
            action=action,
            entity_type="product",
            entity_id=entity_id,
            detail=detail or {},
        )
    )


@router.post("/login", response_model=schemas.AdminSessionOut)
def login(payload: schemas.AdminLogin, db: Session = Depends(get_db)):
    user = (
        db.query(models.AdminUser)
        .filter(models.AdminUser.username == payload.username.strip().lower())
        .first()
    )
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token, expires_at = create_session(db, user)
    return {"token": token, "expires_at": expires_at, "user": user}


@router.get("/me", response_model=schemas.AdminUserOut)
def me(user: models.AdminUser = Depends(require_admin)):
    return user


@router.post("/logout", status_code=204)
def logout(
    user: models.AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.query(models.AdminSession).filter(models.AdminSession.user_id == user.id).delete()
    db.commit()


@router.get("/products", response_model=schemas.AdminProductListResponse)
def list_admin_products(
    q: str | None = None,
    status: str | None = None,
    availability: str | None = None,
    brand_id: int | None = None,
    category_id: int | None = None,
    is_used: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("name", pattern="^(name|sku|stock|created_at|updated_at)$"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    query = db.query(models.Product).options(
        joinedload(models.Product.brand),
        joinedload(models.Product.category),
        joinedload(models.Product.images),
    )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.Product.name.ilike(like),
                models.Product.sku.ilike(like),
                models.Product.part_number.ilike(like),
            )
        )
    if status:
        query = query.filter(models.Product.status == status)
    if availability == "in_stock":
        query = query.filter(models.Product.available_stock > 0)
    elif availability == "out_of_stock":
        query = query.filter(models.Product.available_stock == 0)
    if brand_id:
        query = query.filter(models.Product.brand_id == brand_id)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if is_used is not None:
        query = query.filter(models.Product.is_used.is_(is_used))
    total = query.count()
    sort_fields = {
        "name": models.Product.name,
        "sku": models.Product.sku,
        "stock": models.Product.available_stock,
        "created_at": models.Product.created_at,
        "updated_at": models.Product.updated_at,
    }
    ordering = desc(sort_fields[sort]) if direction == "desc" else asc(sort_fields[sort])
    items = (
        query.order_by(ordering, models.Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/products/{product_id}", response_model=schemas.AdminProductOut)
def get_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
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
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def apply_product(product: models.Product, payload: schemas.AdminProductInput, db: Session):
    if not db.query(models.Brand).filter(models.Brand.id == payload.brand_id).first():
        raise HTTPException(status_code=400, detail="Selecciona una marca válida")
    if not db.query(models.Category).filter(models.Category.id == payload.category_id).first():
        raise HTTPException(status_code=400, detail="Selecciona una categoría válida")

    product.sku = payload.sku.strip().upper()
    product.name = payload.name.strip()
    product.brand_id = payload.brand_id
    product.category_id = payload.category_id
    product.part_number = payload.part_number.strip()
    product.short_description = payload.short_description.strip()
    product.description = payload.description.strip()
    product.specs = payload.specs
    product.highlights = payload.highlights
    product.stock_note = payload.stock_note.strip()
    product.price = payload.price
    product.currency = payload.currency.upper()
    product.available_stock = payload.available_stock
    product.stock_type = payload.stock_type
    product.is_used = payload.is_used
    product.status = payload.status


@router.post("/products", response_model=schemas.AdminProductOut, status_code=201)
def create_product(
    payload: schemas.AdminProductInput,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    if db.query(models.Product).filter(models.Product.sku == payload.sku.strip().upper()).first():
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese SKU")
    product = models.Product(slug=unique_slug(db, payload.name))
    apply_product(product, payload, db)
    db.add(product)
    db.flush()
    audit(db, user, "product.create", product.id, {"sku": product.sku})
    db.commit()
    return get_admin_product(product.id, db, user)


@router.put("/products/{product_id}", response_model=schemas.AdminProductOut)
def update_product(
    product_id: int,
    payload: schemas.AdminProductInput,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    duplicate = (
        db.query(models.Product)
        .filter(
            models.Product.sku == payload.sku.strip().upper(),
            models.Product.id != product_id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe otro producto con ese SKU")
    if product.name != payload.name.strip():
        product.slug = unique_slug(db, payload.name, product.id)
    apply_product(product, payload, db)
    audit(db, user, "product.update", product.id, {"sku": product.sku})
    db.commit()
    return get_admin_product(product.id, db, user)


@router.patch("/products/{product_id}", response_model=schemas.AdminProductOut)
def patch_product(
    product_id: int,
    payload: schemas.AdminProductPatch,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    values = payload.model_dump(exclude_unset=True)
    if "brand_id" in values and not db.get(models.Brand, values["brand_id"]):
        raise HTTPException(status_code=400, detail="Selecciona una marca válida")
    if "category_id" in values and not db.get(models.Category, values["category_id"]):
        raise HTTPException(status_code=400, detail="Selecciona una categoría válida")
    if "sku" in values:
        values["sku"] = values["sku"].strip().upper()
        duplicate = db.query(models.Product).filter(
            models.Product.sku == values["sku"], models.Product.id != product_id
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe otro producto con ese SKU")
    if "slug" in values:
        values["slug"] = slugify(values["slug"])
        duplicate = db.query(models.Product).filter(
            models.Product.slug == values["slug"], models.Product.id != product_id
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe otro producto con ese slug")
    elif "name" in values and values["name"].strip() != product.name:
        values["slug"] = unique_slug(db, values["name"], product.id)
    for key in ("name", "part_number", "short_description", "description", "stock_note"):
        if key in values and isinstance(values[key], str):
            values[key] = values[key].strip()
    if "currency" in values:
        values["currency"] = values["currency"].upper()
    for key, value in values.items():
        setattr(product, key, value)
    audit(db, user, "product.update", product.id, {"fields": sorted(values)})
    commit_or_conflict(db, "No se pudo actualizar el producto")
    return get_admin_product(product.id, db, user)


@router.delete("/products/{product_id}", status_code=204)
def archive_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.status = "inactive"
    audit(db, user, "product.archive", product.id, {"sku": product.sku})
    db.commit()


@router.patch("/products/{product_id}/status", response_model=schemas.AdminProductOut)
def set_product_status(
    product_id: int,
    payload: schemas.AdminStatusUpdate,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = get_admin_product(product_id, db, user)
    if payload.status == "active":
        if not product.brand.is_active or not product.category.is_active:
            raise HTTPException(
                status_code=409,
                detail="Activa primero la marca y la categoría del producto",
            )
    product.status = payload.status
    audit(db, user, "product.status", product.id, {"status": payload.status})
    db.commit()
    return get_admin_product(product.id, db, user)


def _list_taxonomy(db, model, q, is_active, page, page_size, sort, direction, kind):
    query = db.query(model)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(model.name.ilike(like), model.slug.ilike(like)))
    if is_active is not None:
        query = query.filter(model.is_active.is_(is_active))
    total = query.count()
    column = {"name": model.name, "slug": model.slug, "updated_at": model.updated_at}[sort]
    order = desc(column) if direction == "desc" else asc(column)
    items = query.order_by(order, model.id).offset((page - 1) * page_size).limit(page_size)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [taxonomy_out(db, item, kind) for item in items],
    }


@router.get("/brands", response_model=schemas.AdminBrandListResponse)
def list_admin_brands(
    q: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("name", pattern="^(name|slug|updated_at)$"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    return _list_taxonomy(
        db, models.Brand, q, is_active, page, page_size, sort, direction, "brand"
    )


@router.get("/brands/{brand_id}", response_model=schemas.AdminBrandOut)
def get_admin_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Brand, brand_id)
    if not item:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return taxonomy_out(db, item, "brand")


@router.post("/brands", response_model=schemas.AdminBrandOut, status_code=201)
def create_admin_brand(
    payload: schemas.AdminBrandInput,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = models.Brand(
        name=payload.name.strip(),
        slug=slugify(payload.slug or payload.name),
        description=payload.description.strip(),
        accent_color=payload.accent_color,
        is_active=payload.is_active,
    )
    db.add(item)
    commit_or_conflict(db, "Ya existe una marca con ese nombre o slug")
    db.refresh(item)
    return taxonomy_out(db, item, "brand")


@router.patch("/brands/{brand_id}", response_model=schemas.AdminBrandOut)
def update_admin_brand(
    brand_id: int,
    payload: schemas.AdminBrandUpdate,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Brand, brand_id)
    if not item:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    values = payload.model_dump(exclude_unset=True)
    if "slug" in values:
        values["slug"] = slugify(values["slug"])
    for key, value in values.items():
        setattr(item, key, value.strip() if isinstance(value, str) else value)
    commit_or_conflict(db, "Ya existe una marca con ese nombre o slug")
    return taxonomy_out(db, item, "brand")


@router.patch("/brands/{brand_id}/status", response_model=schemas.AdminBrandOut)
def status_admin_brand(
    brand_id: int,
    payload: schemas.AdminActiveUpdate,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Brand, brand_id)
    if not item:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    item.is_active = payload.is_active
    db.commit()
    return taxonomy_out(db, item, "brand")


@router.delete("/brands/{brand_id}", status_code=204)
def delete_admin_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Brand, brand_id)
    if not item:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    if db.query(models.Product).filter(models.Product.brand_id == brand_id).first():
        raise HTTPException(status_code=409, detail="La marca tiene productos asociados")
    db.delete(item)
    db.commit()


@router.get("/categories", response_model=schemas.AdminCategoryListResponse)
def list_admin_categories(
    q: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("name", pattern="^(name|slug|updated_at)$"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    return _list_taxonomy(
        db, models.Category, q, is_active, page, page_size, sort, direction, "category"
    )


@router.get("/categories/{category_id}", response_model=schemas.AdminCategoryOut)
def get_admin_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Category, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return taxonomy_out(db, item, "category")


@router.post("/categories", response_model=schemas.AdminCategoryOut, status_code=201)
def create_admin_category(
    payload: schemas.AdminCategoryInput,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = models.Category(
        name=payload.name.strip(),
        slug=slugify(payload.slug or payload.name),
        description=payload.description.strip(),
        icon=payload.icon,
        is_active=payload.is_active,
    )
    db.add(item)
    commit_or_conflict(db, "Ya existe una categoría con ese nombre o slug")
    db.refresh(item)
    return taxonomy_out(db, item, "category")


@router.patch("/categories/{category_id}", response_model=schemas.AdminCategoryOut)
def update_admin_category(
    category_id: int,
    payload: schemas.AdminCategoryUpdate,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Category, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    values = payload.model_dump(exclude_unset=True)
    if "slug" in values:
        values["slug"] = slugify(values["slug"])
    for key, value in values.items():
        setattr(item, key, value.strip() if isinstance(value, str) else value)
    commit_or_conflict(db, "Ya existe una categoría con ese nombre o slug")
    return taxonomy_out(db, item, "category")


@router.patch("/categories/{category_id}/status", response_model=schemas.AdminCategoryOut)
def status_admin_category(
    category_id: int,
    payload: schemas.AdminActiveUpdate,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Category, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    item.is_active = payload.is_active
    db.commit()
    return taxonomy_out(db, item, "category")


@router.delete("/categories/{category_id}", status_code=204)
def delete_admin_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Category, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if db.query(models.Product).filter(models.Product.category_id == category_id).first():
        raise HTTPException(status_code=409, detail="La categoría tiene productos asociados")
    db.delete(item)
    db.commit()


async def replace_taxonomy_asset(
    db: Session,
    item,
    kind: str,
    file: UploadFile,
) -> str:
    contents, original_name, extension = await read_media_upload(file, "image")
    prefix = "brands" if kind == "brand" else "categories"
    new_uri = save_media_object(
        f"{prefix}/{safe_path_segment(item.slug)}",
        contents,
        extension,
        (file.content_type or "").lower(),
        {"original-filename": original_name, f"{kind}-slug": item.slug},
    )
    field = "logo_url" if kind == "brand" else "image_url"
    old_uri = getattr(item, field)
    setattr(item, field, new_uri)
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_object_strict(new_uri)
        raise
    remove_object_strict(old_uri)
    return new_uri


@router.put("/brands/{brand_id}/logo", response_model=schemas.AdminBrandOut)
async def replace_brand_logo(
    brand_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Brand, brand_id)
    if not item:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    await replace_taxonomy_asset(db, item, "brand", file)
    return taxonomy_out(db, item, "brand")


@router.delete("/brands/{brand_id}/logo", status_code=204)
def delete_brand_logo(
    brand_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Brand, brand_id)
    if not item:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    old_uri = item.logo_url
    item.logo_url = ""
    db.commit()
    remove_object_strict(old_uri)


@router.put("/categories/{category_id}/image", response_model=schemas.AdminCategoryOut)
async def replace_category_image(
    category_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Category, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    await replace_taxonomy_asset(db, item, "category", file)
    return taxonomy_out(db, item, "category")


@router.delete("/categories/{category_id}/image", status_code=204)
def delete_category_image(
    category_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    item = db.get(models.Category, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    old_uri = item.image_url
    item.image_url = ""
    db.commit()
    remove_object_strict(old_uri)


async def read_media_upload(file: UploadFile, media_type: str) -> tuple[bytes, str, str]:
    original_name = safe_filename(file.filename or "archivo", "archivo")
    content_type = (file.content_type or "").lower()
    extension = os.path.splitext(original_name)[1].lower()
    if media_type == "image":
        expected_extension = IMAGE_TYPES.get(content_type)
        if not expected_extension or extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(status_code=415, detail="La imagen debe ser JPG, PNG o WebP")
        max_bytes = IMAGE_MAX_BYTES
        final_extension = expected_extension
    else:
        if content_type != "application/pdf" or extension != ".pdf":
            raise HTTPException(status_code=415, detail="El documento debe ser PDF")
        max_bytes = PDF_MAX_BYTES
        final_extension = ".pdf"
    contents = await file.read(max_bytes + 1)
    await file.close()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {max_bytes // (1024 * 1024)} MB",
        )
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if not matches_file_signature(media_type, content_type, contents):
        raise HTTPException(status_code=415, detail="El contenido no coincide con el formato")
    return contents, original_name, final_extension


def save_media_object(
    prefix: str, contents: bytes, extension: str, content_type: str, metadata: dict
) -> str:
    object_name = f"{prefix}/{uuid4().hex}{extension}"
    try:
        return put_object(
            object_name,
            BytesIO(contents),
            len(contents),
            content_type,
            metadata=metadata,
        )
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def image_out(image: models.ProductImage, images: list[models.ProductImage]) -> dict:
    ordered = sorted(images, key=lambda item: (item.sort_order, item.id))
    return {
        "id": image.id,
        "product_id": image.product_id,
        "url": image.resolved_url,
        "alt": image.alt,
        "sort_order": image.sort_order,
        "is_primary": bool(ordered and ordered[0].id == image.id),
    }


def document_out(document: models.ProductDocument) -> dict:
    return {
        "id": document.id,
        "product_id": document.product_id,
        "title": document.title,
        "document_type": document.document_type,
        "original_filename": document.original_filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "is_official": document.is_official,
        "sort_order": document.sort_order,
        "download_url": document.download_url,
    }


def require_product(db: Session, product_id: int) -> models.Product:
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.get("/products/{product_id}/images", response_model=list[schemas.AdminImageOut])
def list_product_images(
    product_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    images = sorted(product.images, key=lambda item: (item.sort_order, item.id))
    return [image_out(image, images) for image in images]


@router.post(
    "/products/{product_id}/images",
    response_model=schemas.AdminImageOut,
    status_code=201,
)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    alt: str = Form(""),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    contents, original_name, extension = await read_media_upload(file, "image")
    storage_uri = save_media_object(
        f"products/{safe_path_segment(product.sku)}/images",
        contents,
        extension,
        (file.content_type or "").lower(),
        {"original-filename": original_name, "product-sku": product.sku},
    )
    next_order = max((item.sort_order for item in product.images), default=-1) + 1
    if is_primary:
        for item in product.images:
            item.sort_order += 1
        next_order = 0
    image = models.ProductImage(
        product_id=product.id,
        url=storage_uri,
        alt=(alt.strip() or product.name)[:200],
        sort_order=next_order,
    )
    try:
        db.add(image)
        db.flush()
        audit(db, user, "product.image.create", product.id, {"image_id": image.id})
        db.commit()
        db.refresh(image)
    except Exception:
        db.rollback()
        remove_object_strict(storage_uri)
        raise
    db.refresh(product)
    return image_out(image, product.images)


@router.patch(
    "/products/{product_id}/images/{image_id}",
    response_model=schemas.AdminImageOut,
)
def update_product_image(
    product_id: int,
    image_id: int,
    payload: schemas.AdminImageUpdate,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    image = db.query(models.ProductImage).filter(
        models.ProductImage.id == image_id,
        models.ProductImage.product_id == product_id,
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    if payload.alt is not None:
        image.alt = payload.alt.strip()[:200]
    if payload.is_primary:
        ordered = sorted(product.images, key=lambda item: (item.sort_order, item.id))
        for index, item in enumerate([image] + [item for item in ordered if item.id != image.id]):
            item.sort_order = index
    audit(db, user, "product.image.update", product.id, {"image_id": image.id})
    db.commit()
    db.refresh(product)
    return image_out(image, product.images)


@router.put(
    "/products/{product_id}/images/{image_id}/file",
    response_model=schemas.AdminImageOut,
)
async def replace_product_image(
    product_id: int,
    image_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    image = db.query(models.ProductImage).filter(
        models.ProductImage.id == image_id,
        models.ProductImage.product_id == product_id,
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    contents, original_name, extension = await read_media_upload(file, "image")
    new_uri = save_media_object(
        f"products/{safe_path_segment(product.sku)}/images",
        contents,
        extension,
        (file.content_type or "").lower(),
        {"original-filename": original_name, "product-sku": product.sku},
    )
    old_uri = image.url
    image.url = new_uri
    audit(db, user, "product.image.replace", product.id, {"image_id": image.id})
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_object_strict(new_uri)
        raise
    remove_object_strict(old_uri)
    db.refresh(product)
    return image_out(image, product.images)


@router.put("/products/{product_id}/images/order", status_code=204)
def reorder_product_images(
    product_id: int,
    payload: schemas.AdminMediaOrder,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    current_ids = {item.id for item in product.images}
    if set(payload.ordered_ids) != current_ids:
        raise HTTPException(status_code=400, detail="La lista debe incluir todas las imágenes")
    for index, image_id in enumerate(payload.ordered_ids):
        next(item for item in product.images if item.id == image_id).sort_order = index
    audit(db, user, "product.image.order", product.id, {"ids": payload.ordered_ids})
    db.commit()


@router.delete("/products/{product_id}/images/{image_id}", status_code=204)
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    image = db.query(models.ProductImage).filter(
        models.ProductImage.id == image_id,
        models.ProductImage.product_id == product_id,
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    old_uri = image.url
    db.delete(image)
    audit(db, user, "product.image.delete", product.id, {"image_id": image.id})
    db.commit()
    remove_object_strict(old_uri)


@router.get(
    "/products/{product_id}/documents",
    response_model=list[schemas.AdminDocumentOut],
)
def list_product_documents(
    product_id: int,
    db: Session = Depends(get_db),
    _: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    return [document_out(item) for item in product.documents]


@router.post(
    "/products/{product_id}/documents",
    response_model=schemas.AdminDocumentOut,
    status_code=201,
)
async def upload_product_document(
    product_id: int,
    file: UploadFile = File(...),
    title: str = Form("Ficha técnica"),
    document_type: str = Form("datasheet"),
    is_official: bool = Form(False),
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    contents, original_name, extension = await read_media_upload(file, "document")
    storage_uri = save_media_object(
        f"products/{safe_path_segment(product.sku)}/documents",
        contents,
        extension,
        "application/pdf",
        {"original-filename": original_name, "product-sku": product.sku},
    )
    document = models.ProductDocument(
        product_id=product.id,
        title=(title.strip() or "Ficha técnica")[:200],
        document_type=document_type[:40],
        storage_uri=storage_uri,
        original_filename=original_name,
        mime_type="application/pdf",
        size_bytes=len(contents),
        is_official=is_official,
        sort_order=max((item.sort_order for item in product.documents), default=-1) + 1,
    )
    try:
        db.add(document)
        db.flush()
        audit(db, user, "product.document.create", product.id, {"document_id": document.id})
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        remove_object_strict(storage_uri)
        raise
    return document_out(document)


@router.put(
    "/products/{product_id}/documents/{document_id}/file",
    response_model=schemas.AdminDocumentOut,
)
async def replace_product_document(
    product_id: int,
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    document = db.query(models.ProductDocument).filter(
        models.ProductDocument.id == document_id,
        models.ProductDocument.product_id == product_id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    contents, original_name, extension = await read_media_upload(file, "document")
    new_uri = save_media_object(
        f"products/{safe_path_segment(product.sku)}/documents",
        contents,
        extension,
        "application/pdf",
        {"original-filename": original_name, "product-sku": product.sku},
    )
    old_uri = document.storage_uri
    document.storage_uri = new_uri
    document.original_filename = original_name
    document.size_bytes = len(contents)
    audit(db, user, "product.document.replace", product.id, {"document_id": document.id})
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_object_strict(new_uri)
        raise
    remove_object_strict(old_uri)
    return document_out(document)


@router.delete("/products/{product_id}/documents/{document_id}", status_code=204)
def delete_product_document(
    product_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user: models.AdminUser = Depends(require_admin),
):
    product = require_product(db, product_id)
    document = db.query(models.ProductDocument).filter(
        models.ProductDocument.id == document_id,
        models.ProductDocument.product_id == product_id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    old_uri = document.storage_uri
    db.delete(document)
    audit(db, user, "product.document.delete", product.id, {"document_id": document.id})
    db.commit()
    remove_object_strict(old_uri)
