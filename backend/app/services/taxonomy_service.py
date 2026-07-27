from fastapi import HTTPException
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app import admin_schemas, models
from app.services.catalog_common import commit_or_conflict, ensure_unique, require_changes, slugify


BRAND_SORT_FIELDS = {
    "name": models.Brand.name,
    "slug": models.Brand.slug,
    "updated_at": models.Brand.updated_at,
}
CATEGORY_SORT_FIELDS = {
    "name": models.Category.name,
    "slug": models.Category.slug,
    "updated_at": models.Category.updated_at,
}


def _product_count(db: Session, foreign_key, item_id: int) -> int:
    return db.query(models.Product.id).filter(foreign_key == item_id).count()


def brand_out(db: Session, brand: models.Brand) -> admin_schemas.AdminBrandOut:
    return admin_schemas.AdminBrandOut(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        description=brand.description,
        accent_color=brand.accent_color,
        logo_url=brand.resolved_logo_url,
        is_active=brand.is_active,
        updated_at=brand.updated_at,
        product_count=_product_count(db, models.Product.brand_id, brand.id),
    )


def category_out(db: Session, category: models.Category) -> admin_schemas.AdminCategoryOut:
    return admin_schemas.AdminCategoryOut(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        image_url=category.resolved_image_url,
        is_active=category.is_active,
        updated_at=category.updated_at,
        product_count=_product_count(db, models.Product.category_id, category.id),
    )


def get_brand(db: Session, brand_id: int) -> models.Brand:
    brand = db.get(models.Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return brand


def list_brands(
    db: Session,
    *,
    q: str | None,
    is_active: bool | None,
    page: int,
    page_size: int,
    sort: str,
    direction: str,
) -> admin_schemas.AdminBrandListResponse:
    query = db.query(models.Brand)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(models.Brand.name.ilike(like), models.Brand.slug.ilike(like)))
    if is_active is not None:
        query = query.filter(models.Brand.is_active.is_(is_active))
    total = query.count()
    sort_column = BRAND_SORT_FIELDS[sort]
    order = desc(sort_column) if direction == "desc" else asc(sort_column)
    items = (
        query.order_by(order, models.Brand.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return admin_schemas.AdminBrandListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[brand_out(db, brand) for brand in items],
    )


def create_brand(db: Session, payload: admin_schemas.AdminBrandCreate):
    values = payload.model_dump()
    values["slug"] = slugify(values["slug"] or values["name"], 80)
    ensure_unique(db, models.Brand, "name", values["name"], "una marca")
    ensure_unique(db, models.Brand, "slug", values["slug"], "una marca")
    brand = models.Brand(**values)
    db.add(brand)
    commit_or_conflict(db, "No se pudo crear la marca porque el nombre o slug ya existe")
    return brand_out(db, get_brand(db, brand.id))


def update_brand(db: Session, brand_id: int, payload: admin_schemas.AdminBrandUpdate):
    brand = get_brand(db, brand_id)
    values = payload.model_dump(exclude_unset=True)
    require_changes(values)
    if any(value is None for value in values.values()):
        raise HTTPException(status_code=422, detail="Los campos enviados no pueden ser null")
    if "name" in values:
        ensure_unique(db, models.Brand, "name", values["name"], "una marca", brand.id)
    if "slug" in values:
        values["slug"] = slugify(values["slug"], 80)
        ensure_unique(db, models.Brand, "slug", values["slug"], "una marca", brand.id)
    for field, value in values.items():
        setattr(brand, field, value)
    commit_or_conflict(db, "No se pudo actualizar la marca porque el nombre o slug ya existe")
    return brand_out(db, get_brand(db, brand.id))


def update_brand_status(db: Session, brand_id: int, is_active: bool):
    brand = get_brand(db, brand_id)
    brand.is_active = is_active
    db.commit()
    return brand_out(db, get_brand(db, brand.id))


def delete_brand(db: Session, brand_id: int) -> None:
    brand = get_brand(db, brand_id)
    if _product_count(db, models.Product.brand_id, brand.id):
        raise HTTPException(
            status_code=409,
            detail="No puedes eliminar una marca que tiene productos asociados",
        )
    db.delete(brand)
    commit_or_conflict(db, "No puedes eliminar una marca que tiene productos asociados")


def get_category(db: Session, category_id: int) -> models.Category:
    category = db.get(models.Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


def list_categories(
    db: Session,
    *,
    q: str | None,
    is_active: bool | None,
    page: int,
    page_size: int,
    sort: str,
    direction: str,
) -> admin_schemas.AdminCategoryListResponse:
    query = db.query(models.Category)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(models.Category.name.ilike(like), models.Category.slug.ilike(like))
        )
    if is_active is not None:
        query = query.filter(models.Category.is_active.is_(is_active))
    total = query.count()
    sort_column = CATEGORY_SORT_FIELDS[sort]
    order = desc(sort_column) if direction == "desc" else asc(sort_column)
    items = (
        query.order_by(order, models.Category.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return admin_schemas.AdminCategoryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[category_out(db, category) for category in items],
    )


def create_category(db: Session, payload: admin_schemas.AdminCategoryCreate):
    values = payload.model_dump()
    values["slug"] = slugify(values["slug"] or values["name"], 120)
    ensure_unique(db, models.Category, "name", values["name"], "una categoría")
    ensure_unique(db, models.Category, "slug", values["slug"], "una categoría")
    category = models.Category(**values)
    db.add(category)
    commit_or_conflict(db, "No se pudo crear la categoría porque el nombre o slug ya existe")
    return category_out(db, get_category(db, category.id))


def update_category(
    db: Session,
    category_id: int,
    payload: admin_schemas.AdminCategoryUpdate,
):
    category = get_category(db, category_id)
    values = payload.model_dump(exclude_unset=True)
    require_changes(values)
    if any(value is None for value in values.values()):
        raise HTTPException(status_code=422, detail="Los campos enviados no pueden ser null")
    if "name" in values:
        ensure_unique(
            db, models.Category, "name", values["name"], "una categoría", category.id
        )
    if "slug" in values:
        values["slug"] = slugify(values["slug"], 120)
        ensure_unique(
            db, models.Category, "slug", values["slug"], "una categoría", category.id
        )
    for field, value in values.items():
        setattr(category, field, value)
    commit_or_conflict(db, "No se pudo actualizar la categoría porque el nombre o slug ya existe")
    return category_out(db, get_category(db, category.id))


def update_category_status(db: Session, category_id: int, is_active: bool):
    category = get_category(db, category_id)
    category.is_active = is_active
    db.commit()
    return category_out(db, get_category(db, category.id))


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    if _product_count(db, models.Product.category_id, category.id):
        raise HTTPException(
            status_code=409,
            detail="No puedes eliminar una categoría que tiene productos asociados",
        )
    db.delete(category)
    commit_or_conflict(db, "No puedes eliminar una categoría que tiene productos asociados")
