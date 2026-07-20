"""Sincroniza el catálogo normalizado sin reiniciar PostgreSQL.

El comando actualiza productos y saldos existentes, crea las referencias nuevas
y registra ajustes de inventario. Es seguro ejecutarlo más de una vez.
"""

from sqlalchemy import func, select

from app import models
from app.database import Base, SessionLocal, engine
from app.inventory_data import INVENTORY_PRODUCTS
from app.product_content import PRODUCT_CONTENT


def required_map(db, model, label):
    values = {row.slug: row for row in db.scalars(select(model)).all()}
    if not values:
        raise RuntimeError(f"No existen {label}; ejecuta primero el seed inicial.")
    return values


def sync_faqs(db, product, curated):
    db.query(models.ProductFAQ).filter(
        models.ProductFAQ.product_id == product.id
    ).delete(synchronize_session=False)
    for sort_order, faq_data in enumerate(curated.get("faqs", [])):
        db.add(models.ProductFAQ(
            product_id=product.id,
            question=faq_data["question"],
            answer=faq_data["answer"],
            sort_order=sort_order,
        ))


def run():
    Base.metadata.create_all(bind=engine)
    created = 0
    updated = 0
    adjusted = 0

    with SessionLocal() as db:
        brands = required_map(db, models.Brand, "marcas")
        categories = required_map(db, models.Category, "categorías")
        warehouses = required_map(db, models.Warehouse, "almacenes")
        suppliers = {row.slug: row for row in db.scalars(select(models.Supplier)).all()}

        for data in INVENTORY_PRODUCTS:
            expected_quantity = sum(balance["quantity"] for balance in data["balances"])
            if expected_quantity <= 0:
                continue

            curated = PRODUCT_CONTENT.get(data["sku"], {})
            product = db.scalar(select(models.Product).where(models.Product.sku == data["sku"]))
            is_new = product is None
            if is_new:
                product = models.Product(sku=data["sku"], slug=data["sku"].lower())
                db.add(product)
                created += 1
            else:
                updated += 1

            product.name = data["name"]
            product.brand_id = brands[data["brand"]].id
            product.category_id = categories[data["category"]].id
            product.part_number = data["part_number"]
            product.short_description = data["short_description"]
            product.description = curated.get("description", data["description"])
            product.specs = {**data["specs"], **curated.get("specs", {})}
            product.highlights = curated.get("highlights", data["highlights"])
            product.stock_type = data["stock_type"]
            product.is_used = data["is_used"]
            product.status = "active"
            db.flush()
            sync_faqs(db, product, curated)

            for balance_data in data["balances"]:
                warehouse = warehouses[balance_data["warehouse"]]
                balance = db.scalar(select(models.InventoryBalance).where(
                    models.InventoryBalance.product_id == product.id,
                    models.InventoryBalance.warehouse_id == warehouse.id,
                ))
                old_quantity = balance.quantity if balance else 0
                new_quantity = balance_data["quantity"]
                supplier_slug = balance_data.get("supplier")
                supplier = suppliers.get(supplier_slug) if supplier_slug else None

                if balance is None:
                    balance = models.InventoryBalance(
                        product_id=product.id,
                        warehouse_id=warehouse.id,
                    )
                    db.add(balance)

                balance.supplier_id = supplier.id if supplier else None
                balance.quantity = new_quantity
                balance.condition = "used" if data["is_used"] else "new"
                balance.source_sheet = data["source_sheet"]
                balance.source_reference = balance_data.get("reference", "")

                delta = new_quantity - old_quantity
                if delta:
                    db.add(models.StockMovement(
                        product_id=product.id,
                        from_warehouse_id=warehouse.id if delta < 0 else None,
                        to_warehouse_id=warehouse.id if delta > 0 else None,
                        movement_type="catalog_sync",
                        quantity=abs(delta),
                        reference=balance_data.get("reference", data["source_sheet"]),
                        notes=f"Ajuste de catálogo: {old_quantity} -> {new_quantity}",
                    ))
                    adjusted += 1

            db.flush()
            total = db.scalar(select(func.coalesce(func.sum(models.InventoryBalance.quantity), 0)).where(
                models.InventoryBalance.product_id == product.id
            ))
            product.available_stock = int(total or 0)
            product.stock_note = (
                f"{product.available_stock} unidad"
                f"{'es' if product.available_stock != 1 else ''} disponible"
                f"{'s' if product.available_stock != 1 else ''}"
            )

        db.commit()

    print(
        f"Catálogo sincronizado: {created} productos creados, "
        f"{updated} actualizados y {adjusted} saldos ajustados."
    )


if __name__ == "__main__":
    run()
