from app import models


def create_taxonomies(db, *, brand_active=True, category_active=True):
    brand = models.Brand(name="Marca base", slug="marca-base", is_active=brand_active)
    category = models.Category(
        name="Categoría base",
        slug="categoria-base",
        is_active=category_active,
    )
    db.add_all([brand, category])
    db.commit()
    return brand, category


def product_payload(brand_id, category_id, **overrides):
    payload = {
        "sku": "SKU-ADMIN-1",
        "name": "Producto Administrativo",
        "brand_id": brand_id,
        "category_id": category_id,
        "available_stock": 3,
    }
    payload.update(overrides)
    return payload


def test_product_crud_search_filters_and_public_visibility(client, db, admin_headers):
    brand, category = create_taxonomies(db)
    created = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id),
        headers=admin_headers,
    )
    assert created.status_code == 201
    product = created.json()
    assert product["slug"] == "producto-administrativo"
    assert product["status"] == "inactive"
    assert product["is_publicly_visible"] is False

    product_id = product["id"]
    update = client.patch(
        f"/api/admin/products/{product_id}",
        json={
            "name": "Producto editado",
            "part_number": "PN-22",
            "short_description": "Descripción pública",
            "specs": {"Memoria": "16 GB"},
            "highlights": ["Entrega rápida"],
            "available_stock": 5,
            "is_used": True,
        },
        headers=admin_headers,
    )
    assert update.status_code == 200
    assert update.json()["slug"] == "producto-administrativo"
    assert update.json()["available_stock"] == 5

    activation = client.patch(
        f"/api/admin/products/{product_id}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
    assert activation.status_code == 200
    assert activation.json()["is_publicly_visible"] is True

    listing = client.get(
        "/api/admin/products",
        params={
            "q": "PN-22",
            "status": "active",
            "availability": "in_stock",
            "brand_id": brand.id,
            "category_id": category.id,
            "is_used": True,
            "sort": "stock",
            "direction": "desc",
        },
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == product_id

    public = client.get("/api/products")
    assert public.status_code == 200
    assert public.json()["total"] == 1


def test_product_validations(client, db, admin_headers):
    brand, category = create_taxonomies(db)
    first = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id, slug="producto-unico"),
        headers=admin_headers,
    )
    assert first.status_code == 201

    duplicate_sku = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id, sku="sku-admin-1", slug="otro"),
        headers=admin_headers,
    )
    assert duplicate_sku.status_code == 409

    duplicate_slug = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id, sku="SKU-2", slug="PRODUCTO-UNICO"),
        headers=admin_headers,
    )
    assert duplicate_slug.status_code == 409

    negative_stock = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id, sku="SKU-3", available_stock=-1),
        headers=admin_headers,
    )
    assert negative_stock.status_code == 422

    missing_brand = client.post(
        "/api/admin/products",
        json=product_payload(99999, category.id, sku="SKU-4"),
        headers=admin_headers,
    )
    assert missing_brand.status_code == 422

    immutable_sku = client.patch(
        f"/api/admin/products/{first.json()['id']}",
        json={"sku": "CHANGED"},
        headers=admin_headers,
    )
    assert immutable_sku.status_code == 422

    legacy_stock_fields = client.patch(
        f"/api/admin/products/{first.json()['id']}",
        json={"stock_note": "Texto manual", "stock_type": "bulk"},
        headers=admin_headers,
    )
    assert legacy_stock_fields.status_code == 422


def test_product_cannot_be_activated_with_inactive_taxonomy(client, db, admin_headers):
    brand, category = create_taxonomies(db, brand_active=False)
    created = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id),
        headers=admin_headers,
    )
    assert created.status_code == 201
    activation = client.patch(
        f"/api/admin/products/{created.json()['id']}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
    assert activation.status_code == 409

    active_on_create = client.post(
        "/api/admin/products",
        json=product_payload(brand.id, category.id, sku="SKU-ACTIVE", status="active"),
        headers=admin_headers,
    )
    assert active_on_create.status_code == 409


def test_brand_crud_status_and_protected_delete(client, db, admin_headers):
    created = client.post(
        "/api/admin/brands",
        json={"name": "Nueva Marca", "accent_color": "#123ABC"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    brand = created.json()
    assert brand["slug"] == "nueva-marca"
    assert brand["product_count"] == 0

    duplicate = client.post(
        "/api/admin/brands",
        json={"name": "nueva marca", "slug": "otra"},
        headers=admin_headers,
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/admin/brands/{brand['id']}",
        json={"description": "Actualizada"},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Actualizada"

    disabled = client.patch(
        f"/api/admin/brands/{brand['id']}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
    assert client.get("/api/admin/brands", params={"is_active": False}).json()["total"] == 1

    category = models.Category(name="Categoría", slug="categoria")
    db.add(category)
    db.flush()
    db.add(
        models.Product(
            sku="BRAND-PRODUCT",
            name="Producto",
            slug="brand-product",
            brand_id=brand["id"],
            category_id=category.id,
        )
    )
    db.commit()
    blocked = client.delete(f"/api/admin/brands/{brand['id']}", headers=admin_headers)
    assert blocked.status_code == 409

    orphan = client.post(
        "/api/admin/brands",
        json={"name": "Sin productos"},
        headers=admin_headers,
    ).json()
    assert client.delete(f"/api/admin/brands/{orphan['id']}", headers=admin_headers).status_code == 204


def test_category_crud_status_and_protected_delete(client, db, admin_headers):
    created = client.post(
        "/api/admin/categories",
        json={"name": "Redes Especiales"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    category = created.json()
    assert category["slug"] == "redes-especiales"

    updated = client.patch(
        f"/api/admin/categories/{category['id']}",
        json={"description": "Categoría actualizada"},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Categoría actualizada"

    disabled = client.patch(
        f"/api/admin/categories/{category['id']}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False

    brand = models.Brand(name="Marca", slug="marca")
    db.add(brand)
    db.flush()
    db.add(
        models.Product(
            sku="CATEGORY-PRODUCT",
            name="Producto",
            slug="category-product",
            brand_id=brand.id,
            category_id=category["id"],
        )
    )
    db.commit()
    blocked = client.delete(
        f"/api/admin/categories/{category['id']}",
        headers=admin_headers,
    )
    assert blocked.status_code == 409

    orphan = client.post(
        "/api/admin/categories",
        json={"name": "Sin productos"},
        headers=admin_headers,
    ).json()
    assert (
        client.delete(f"/api/admin/categories/{orphan['id']}", headers=admin_headers).status_code
        == 204
    )


def test_future_module_placeholders_remain(client, db, admin_headers):
    brand, category = create_taxonomies(db)
    product = models.Product(
        sku="PLACEHOLDER",
        name="Producto",
        slug="placeholder",
        brand_id=brand.id,
        category_id=category.id,
    )
    db.add(product)
    db.commit()
    assert client.get(f"/api/admin/products/{product.id}/faqs").status_code == 501
    assert client.get(f"/api/admin/products/{product.id}/sources").status_code == 501
    assert client.get("/api/admin/inquiries").status_code == 501
