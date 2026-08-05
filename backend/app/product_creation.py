import re
import unicodedata

from sqlalchemy.orm import Session

from app import models, schemas


class ProductCatalogError(ValueError):
    pass


def normalize_sku(value: str) -> str:
    return value.strip().upper()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


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


def apply_product(
    product: models.Product,
    payload: schemas.AdminProductInput,
    db: Session,
) -> None:
    if not db.query(models.Brand).filter(models.Brand.id == payload.brand_id).first():
        raise ProductCatalogError("Selecciona una marca válida")
    if not db.query(models.Category).filter(
        models.Category.id == payload.category_id
    ).first():
        raise ProductCatalogError("Selecciona una categoría válida")

    product.sku = normalize_sku(payload.sku)
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


def create_product_record(
    db: Session,
    payload: schemas.AdminProductInput,
) -> models.Product:
    """Create and flush one product without committing the surrounding transaction."""
    product = models.Product(slug=unique_slug(db, payload.name))
    apply_product(product, payload, db)
    db.add(product)
    db.flush()
    return product


def audit_product_creation(
    db: Session,
    user: models.AdminUser,
    product: models.Product,
    *,
    source: str | None = None,
) -> None:
    detail = {"sku": product.sku}
    if source:
        detail["source"] = source
    db.add(
        models.AdminAuditLog(
            user_id=user.id,
            action="product.create",
            entity_type="product",
            entity_id=product.id,
            detail=detail,
        )
    )
