from app import models, sync_catalog
from sqlalchemy.orm import sessionmaker


def inventory_item(sku, name):
    return {
        "sku": sku,
        "name": name,
        "brand": "marca",
        "category": "categoria",
        "part_number": "PN",
        "short_description": "Importada",
        "description": "Importada",
        "specs": {},
        "highlights": [],
        "is_used": False,
        "source_sheet": "test",
        "balances": [{"warehouse": "principal", "quantity": 3}],
    }


def test_sync_skips_existing_and_creates_new_inactive(db, monkeypatch):
    brand = models.Brand(name="Marca", slug="marca")
    category = models.Category(name="Categoría", slug="categoria")
    warehouse = models.Warehouse(name="Principal", slug="principal")
    db.add_all([brand, category, warehouse])
    db.flush()
    existing = models.Product(
        sku="EXISTING",
        name="Nombre del dashboard",
        slug="existing",
        brand_id=brand.id,
        category_id=category.id,
        available_stock=7,
        status="inactive",
    )
    db.add(existing)
    db.commit()

    monkeypatch.setattr(sync_catalog, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(
        sync_catalog,
        "INVENTORY_PRODUCTS",
        [inventory_item("EXISTING", "Sobrescrito"), inventory_item("NEW", "Nuevo")],
    )
    monkeypatch.setattr(sync_catalog, "PRODUCT_CONTENT", {})
    sync_catalog.run()

    db.expire_all()
    assert db.query(models.Product).filter_by(sku="EXISTING").one().name == "Nombre del dashboard"
    assert db.query(models.Product).filter_by(sku="EXISTING").one().available_stock == 7
    new_product = db.query(models.Product).filter_by(sku="NEW").one()
    assert new_product.status == "inactive"
    assert new_product.available_stock == 3
