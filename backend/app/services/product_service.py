from fastapi import HTTPException
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session, joinedload

from app import admin_schemas, models
from app.services.catalog_common import commit_or_conflict, ensure_unique, require_changes, slugify


PRODUCT_SORT_FIELDS = {
    "name": models.Product.name,
    "sku": models.Product.sku,
    "stock": models.Product.available_stock,
    "created_at": models.Product.created_at,
    "updated_at": models.Product.updated_at,
}


def is_publicly_visible(product: models.Product) -> bool:
    return bool(
        product.status == "active"
        and product.available_stock > 0
        and product.brand.is_active
        and product.category.is_active
    )


def to_product_out(product: models.Product) -> admin_schemas.AdminProductOut:
    return admin_schemas.AdminProductOut(
        id=product.id,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        brand_id=product.brand_id,
        category_id=product.category_id,
        part_number=product.part_number,
        short_description=product.short_description,
        description=product.description,
        specs=product.specs or {},
        highlights=product.highlights or [],
        stock_note=product.stock_note,
        available_stock=product.available_stock,
        stock_type=product.stock_type,
        is_used=product.is_used,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
        brand=product.brand,
        category=product.category,
        is_publicly_visible=is_publicly_visible(product),
    )


def _base_query(db: Session):
    return db.query(models.Product).options(
        joinedload(models.Product.brand),
        joinedload(models.Product.category),
    )


def get_product(db: Session, product_id: int) -> models.Product:
    product = _base_query(db).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def list_products(
    db: Session,
    *,
    q: str | None,
    status: str | None,
    availability: str | None,
    brand_id: int | None,
    category_id: int | None,
    is_used: bool | None,
    page: int,
    page_size: int,
    sort: str,
    direction: str,
) -> admin_schemas.AdminProductListResponse:
    query = _base_query(db)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.Product.name.ilike(like),
                models.Product.sku.ilike(like),
                models.Product.part_number.ilike(like),
                models.Product.short_description.ilike(like),
            )
        )
    if status:
        query = query.filter(models.Product.status == status)
    if availability == "in_stock":
        query = query.filter(models.Product.available_stock > 0)
    elif availability == "out_of_stock":
        query = query.filter(models.Product.available_stock == 0)
    if brand_id is not None:
        query = query.filter(models.Product.brand_id == brand_id)
    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if is_used is not None:
        query = query.filter(models.Product.is_used.is_(is_used))

    total = query.count()
    sort_column = PRODUCT_SORT_FIELDS[sort]
    order = desc(sort_column) if direction == "desc" else asc(sort_column)
    products = (
        query.order_by(order, models.Product.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return admin_schemas.AdminProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[to_product_out(product) for product in products],
    )


def _get_taxonomies(db: Session, brand_id: int, category_id: int):
    brand = db.get(models.Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=422, detail="La marca seleccionada no existe")
    category = db.get(models.Category, category_id)
    if not category:
        raise HTTPException(status_code=422, detail="La categoría seleccionada no existe")
    return brand, category


def _validate_activation(status: str, brand: models.Brand, category: models.Category) -> None:
    if status != "active":
        return
    if not brand.is_active:
        raise HTTPException(status_code=409, detail="No puedes activar un producto con una marca inactiva")
    if not category.is_active:
        raise HTTPException(
            status_code=409,
            detail="No puedes activar un producto con una categoría inactiva",
        )


def create_product(
    db: Session, payload: admin_schemas.AdminProductCreate
) -> admin_schemas.AdminProductOut:
    values = payload.model_dump()
    values["sku"] = values["sku"].strip()
    values["slug"] = slugify(values["slug"] or values["name"], 220)
    ensure_unique(db, models.Product, "sku", values["sku"], "un producto")
    ensure_unique(db, models.Product, "slug", values["slug"], "un producto")
    brand, category = _get_taxonomies(db, values["brand_id"], values["category_id"])
    _validate_activation(values["status"], brand, category)

    product = models.Product(**values)
    db.add(product)
    commit_or_conflict(db, "No se pudo crear el producto porque el SKU o slug ya existe")
    return to_product_out(get_product(db, product.id))


def update_product(
    db: Session,
    product_id: int,
    payload: admin_schemas.AdminProductUpdate,
) -> admin_schemas.AdminProductOut:
    product = get_product(db, product_id)
    values = payload.model_dump(exclude_unset=True)
    require_changes(values)
    if any(value is None for value in values.values()):
        raise HTTPException(status_code=422, detail="Los campos enviados no pueden ser null")

    if "slug" in values:
        values["slug"] = slugify(values["slug"], 220)
        ensure_unique(
            db,
            models.Product,
            "slug",
            values["slug"],
            "un producto",
            exclude_id=product.id,
        )

    if "brand_id" in values and not db.get(models.Brand, values["brand_id"]):
        raise HTTPException(status_code=422, detail="La marca seleccionada no existe")
    if "category_id" in values and not db.get(models.Category, values["category_id"]):
        raise HTTPException(status_code=422, detail="La categoría seleccionada no existe")

    for field, value in values.items():
        setattr(product, field, value)
    commit_or_conflict(db, "No se pudo actualizar el producto porque el slug ya existe")
    return to_product_out(get_product(db, product.id))


def update_product_status(
    db: Session,
    product_id: int,
    status: str,
) -> admin_schemas.AdminProductOut:
    product = get_product(db, product_id)
    _validate_activation(status, product.brand, product.category)
    product.status = status
    db.commit()
    return to_product_out(get_product(db, product.id))
