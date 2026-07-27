import pytest

from app import models
from app.services import media_service
from app.storage import StorageUnavailableError


JPEG = b"\xff\xd8\xff\xe0" + b"image-data"
PNG = b"\x89PNG\r\n\x1a\n" + b"image-data"
PDF = b"%PDF-1.4\n" + b"document-data"


@pytest.fixture
def product(db):
    brand = models.Brand(name="Marca medios", slug="marca-medios")
    category = models.Category(name="Categoría medios", slug="categoria-medios")
    db.add_all([brand, category])
    db.flush()
    product = models.Product(
        sku="MEDIA-001",
        name="Producto con medios",
        slug="producto-con-medios",
        brand_id=brand.id,
        category_id=category.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def fake_storage(monkeypatch):
    state = {"stored": [], "removed": []}

    def put_object(object_name, data, length, content_type, metadata=None):
        assert len(data.read()) == length
        uri = f"minio://test-bucket/{object_name}"
        state["stored"].append((uri, content_type, metadata))
        return uri

    def remove_object(value):
        state["removed"].append(value)
        return value.startswith("minio://")

    monkeypatch.setattr(media_service, "put_object", put_object)
    monkeypatch.setattr(media_service, "remove_object_strict", remove_object)
    monkeypatch.setattr(
        media_service,
        "resolve_media_url",
        lambda value, download_name=None: f"https://media.test/{value.split('/')[-1]}",
    )
    monkeypatch.setattr(
        models,
        "resolve_media_url",
        lambda value, download_name=None: (
            f"https://media.test/{value.split('/')[-1]}" if value else ""
        ),
    )
    return state


def test_image_crud_order_primary_and_validation(
    client, db, admin_headers, product, fake_storage
):
    first = client.post(
        f"/api/admin/products/{product.id}/images",
        files={"file": ("front.jpg", JPEG, "image/jpeg")},
        data={"alt": "Vista frontal"},
        headers=admin_headers,
    )
    assert first.status_code == 201
    assert first.json()["is_primary"] is True
    assert first.json()["sort_order"] == 0

    second = client.post(
        f"/api/admin/products/{product.id}/images",
        files={"file": ("back.png", PNG, "image/png")},
        data={"alt": "Vista posterior"},
        headers=admin_headers,
    )
    assert second.status_code == 201
    assert second.json()["is_primary"] is False

    without_csrf = client.patch(
        f"/api/admin/products/{product.id}/images/{second.json()['id']}",
        json={"is_primary": True},
    )
    assert without_csrf.status_code == 403

    primary = client.patch(
        f"/api/admin/products/{product.id}/images/{second.json()['id']}",
        json={"is_primary": True, "alt": "Nueva vista posterior"},
        headers=admin_headers,
    )
    assert primary.status_code == 200
    assert primary.json()["is_primary"] is True

    listed = client.get(f"/api/admin/products/{product.id}/images")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [
        second.json()["id"],
        first.json()["id"],
    ]
    assert [item["sort_order"] for item in listed.json()] == [0, 1]

    reordered = client.put(
        f"/api/admin/products/{product.id}/images/order",
        json={"ordered_ids": [first.json()["id"], second.json()["id"]]},
        headers=admin_headers,
    )
    assert reordered.status_code == 200
    assert reordered.json()[0]["id"] == first.json()["id"]
    assert reordered.json()[0]["is_primary"] is True

    old_uri = db.get(models.ProductImage, first.json()["id"]).url
    replaced = client.put(
        f"/api/admin/products/{product.id}/images/{first.json()['id']}/file",
        files={"file": ("replacement.webp", b"RIFF1234WEBPdata", "image/webp")},
        headers=admin_headers,
    )
    assert replaced.status_code == 200
    assert old_uri in fake_storage["removed"]

    invalid = client.post(
        f"/api/admin/products/{product.id}/images",
        files={"file": ("fake.jpg", b"not-an-image", "image/jpeg")},
        headers=admin_headers,
    )
    assert invalid.status_code == 415

    mismatched_order = client.put(
        f"/api/admin/products/{product.id}/images/order",
        json={"ordered_ids": [first.json()["id"]]},
        headers=admin_headers,
    )
    assert mismatched_order.status_code == 422

    second_uri = db.get(models.ProductImage, second.json()["id"]).url
    deleted = client.delete(
        f"/api/admin/products/{product.id}/images/{second.json()['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 204
    assert second_uri in fake_storage["removed"]
    remaining = client.get(f"/api/admin/products/{product.id}/images").json()
    assert len(remaining) == 1
    assert remaining[0]["sort_order"] == 0
    assert remaining[0]["is_primary"] is True


def test_document_upload_replace_delete_and_formats(
    client, db, admin_headers, product, fake_storage
):
    created = client.post(
        f"/api/admin/products/{product.id}/documents",
        files={"file": ("datasheet.pdf", PDF, "application/pdf")},
        data={
            "title": "Ficha técnica oficial",
            "document_type": "datasheet",
            "is_official": "true",
        },
        headers=admin_headers,
    )
    assert created.status_code == 201
    assert created.json()["title"] == "Ficha técnica oficial"
    assert created.json()["is_official"] is True
    assert created.json()["size_bytes"] == len(PDF)

    listed = client.get(f"/api/admin/products/{product.id}/documents")
    assert listed.status_code == 200
    assert listed.json()[0]["download_url"].startswith("https://media.test/")

    old_uri = db.get(models.ProductDocument, created.json()["id"]).storage_uri
    replacement = b"%PDF-1.7\nreplacement"
    replaced = client.put(
        f"/api/admin/products/{product.id}/documents/{created.json()['id']}/file",
        files={"file": ("manual.pdf", replacement, "application/pdf")},
        headers=admin_headers,
    )
    assert replaced.status_code == 200
    assert replaced.json()["original_filename"] == "manual.pdf"
    assert replaced.json()["size_bytes"] == len(replacement)
    assert old_uri in fake_storage["removed"]

    invalid = client.post(
        f"/api/admin/products/{product.id}/documents",
        files={"file": ("manual.pdf", b"plain text", "application/pdf")},
        headers=admin_headers,
    )
    assert invalid.status_code == 415

    current_uri = db.get(models.ProductDocument, created.json()["id"]).storage_uri
    deleted = client.delete(
        f"/api/admin/products/{product.id}/documents/{created.json()['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 204
    assert current_uri in fake_storage["removed"]
    assert client.get(f"/api/admin/products/{product.id}/documents").json() == []


def test_failed_storage_delete_restores_database_record(
    client, db, admin_headers, product, fake_storage, monkeypatch
):
    created = client.post(
        f"/api/admin/products/{product.id}/images",
        files={"file": ("front.jpg", JPEG, "image/jpeg")},
        headers=admin_headers,
    )
    image_id = created.json()["id"]

    def fail_remove(_):
        raise StorageUnavailableError("MinIO no disponible")

    monkeypatch.setattr(media_service, "remove_object_strict", fail_remove)
    response = client.delete(
        f"/api/admin/products/{product.id}/images/{image_id}",
        headers=admin_headers,
    )
    assert response.status_code == 503
    db.expire_all()
    assert db.get(models.ProductImage, image_id) is not None


def test_category_image_and_brand_logo_crud(
    client, db, admin_headers, fake_storage
):
    brand = models.Brand(name="Marca visual", slug="marca-visual")
    category = models.Category(name="Categoría visual", slug="categoria-visual")
    db.add_all([brand, category])
    db.commit()

    without_csrf = client.put(
        f"/api/admin/categories/{category.id}/image",
        files={"file": ("category.jpg", JPEG, "image/jpeg")},
    )
    assert without_csrf.status_code == 403

    category_upload = client.put(
        f"/api/admin/categories/{category.id}/image",
        files={"file": ("category.jpg", JPEG, "image/jpeg")},
        headers=admin_headers,
    )
    assert category_upload.status_code == 200
    assert category_upload.json()["image_url"].startswith("https://media.test/")
    db.refresh(category)
    first_category_uri = category.image_url
    assert first_category_uri.startswith(
        f"minio://test-bucket/categories/{category.id}/"
    )

    category_replace = client.put(
        f"/api/admin/categories/{category.id}/image",
        files={"file": ("category.png", PNG, "image/png")},
        headers=admin_headers,
    )
    assert category_replace.status_code == 200
    assert first_category_uri in fake_storage["removed"]

    logo_upload = client.put(
        f"/api/admin/brands/{brand.id}/logo",
        files={"file": ("logo.png", PNG, "image/png")},
        headers=admin_headers,
    )
    assert logo_upload.status_code == 200
    assert logo_upload.json()["logo_url"].startswith("https://media.test/")
    db.refresh(brand)
    logo_uri = brand.logo_url
    assert logo_uri.startswith(f"minio://test-bucket/brands/{brand.id}/")
    assert client.get(f"/api/categories/{category.slug}").json()["image_url"].startswith(
        "https://media.test/"
    )
    assert client.get(f"/api/brands/{brand.slug}").json()["logo_url"].startswith(
        "https://media.test/"
    )

    invalid = client.put(
        f"/api/admin/brands/{brand.id}/logo",
        files={"file": ("logo.png", b"not-an-image", "image/png")},
        headers=admin_headers,
    )
    assert invalid.status_code == 415

    category_delete = client.delete(
        f"/api/admin/categories/{category.id}/image",
        headers=admin_headers,
    )
    assert category_delete.status_code == 204
    db.refresh(category)
    assert category.image_url == ""

    logo_delete = client.delete(
        f"/api/admin/brands/{brand.id}/logo",
        headers=admin_headers,
    )
    assert logo_delete.status_code == 204
    assert logo_uri in fake_storage["removed"]
    db.refresh(brand)
    assert brand.logo_url == ""


def test_failed_taxonomy_asset_delete_restores_uri(
    client, db, admin_headers, fake_storage, monkeypatch
):
    category = models.Category(name="Categoría restaurable", slug="categoria-restaurable")
    db.add(category)
    db.commit()
    uploaded = client.put(
        f"/api/admin/categories/{category.id}/image",
        files={"file": ("category.jpg", JPEG, "image/jpeg")},
        headers=admin_headers,
    )
    assert uploaded.status_code == 200
    db.refresh(category)
    stored_uri = category.image_url

    def fail_remove(_):
        raise StorageUnavailableError("MinIO no disponible")

    monkeypatch.setattr(media_service, "remove_object_strict", fail_remove)
    deleted = client.delete(
        f"/api/admin/categories/{category.id}/image",
        headers=admin_headers,
    )
    assert deleted.status_code == 503
    db.expire_all()
    assert db.get(models.Category, category.id).image_url == stored_uri


def test_media_limits_are_the_existing_limits():
    assert media_service.IMAGE_MAX_BYTES == 10 * 1024 * 1024
    assert media_service.PDF_MAX_BYTES == 25 * 1024 * 1024
