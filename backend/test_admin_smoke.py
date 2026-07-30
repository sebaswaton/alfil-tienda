"""Minimal end-to-end smoke test for the internal catalog panel."""

from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app


def prepare_catalog():
    db = SessionLocal()
    try:
        if not db.query(models.Brand).first():
            db.add(models.Brand(name="Marca Test", slug="marca-test"))
        if not db.query(models.Category).first():
            db.add(models.Category(name="Categoría Test", slug="categoria-test"))
        db.commit()
    finally:
        db.close()


def run():
    prepare_catalog()
    client = TestClient(app)

    login = client.post(
        "/api/admin/login",
        json={"username": "admin.test", "password": "TestPassword.2026"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    brands = client.get("/api/brands").json()
    categories = client.get("/api/categories").json()
    payload = {
        "sku": "TEST-ADMIN-001",
        "name": "Producto de prueba administrativa",
        "brand_id": brands[0]["id"],
        "category_id": categories[0]["id"],
        "available_stock": 3,
        "status": "active",
        "short_description": "Registro creado por la prueba del panel.",
        "specs": {"Prueba": "Correcta"},
        "highlights": ["Carga administrativa"],
    }
    created = client.post("/api/admin/products", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    product = created.json()
    assert product["status"] == "active"

    payload["available_stock"] = 5
    updated = client.put(
        f"/api/admin/products/{product['id']}", json=payload, headers=headers
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["available_stock"] == 5

    public = client.get(f"/api/products/{product['slug']}")
    assert public.status_code == 200, public.text
    print("ADMIN_SMOKE_OK")


if __name__ == "__main__":
    run()
