from app import models
from app.main import app
from fastapi.testclient import TestClient


def catalog_data(db):
    brand = models.Brand(name="Marca", slug="marca")
    category = models.Category(name="Categoría", slug="categoria")
    db.add_all([brand, category])
    db.flush()
    product = models.Product(
        sku="SKU-1",
        name="Producto",
        slug="producto",
        brand_id=brand.id,
        category_id=category.id,
        short_description="Descripción",
        available_stock=2,
        status="active",
    )
    db.add(product)
    db.commit()
    return brand, category, product


def test_existing_public_product_contract_is_unchanged(client, db):
    catalog_data(db)
    response = client.get("/api/products")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"total", "page", "page_size", "items"}
    assert body["total"] == 1
    assert set(body["items"][0]) == {
        "id",
        "sku",
        "name",
        "slug",
        "short_description",
        "stock_note",
        "available_stock",
        "stock_type",
        "is_used",
        "brand",
        "category",
        "images",
    }


def test_inactive_taxonomy_hides_product_without_changing_response_shape(client, db):
    brand, _, _ = catalog_data(db)
    brand.is_active = False
    db.commit()
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_public_inquiry_contract_is_unchanged(client, db):
    response = client.post(
        "/api/inquiries",
        json={"name": "Cliente", "email": "cliente@example.com", "message": "Consulta"},
    )
    assert response.status_code == 201
    assert set(response.json()) == {"id", "created_at"}


def test_application_starts_and_health_endpoint_responds():
    with TestClient(app) as live_client:
        response = live_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
