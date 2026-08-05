import unittest
import stat
from io import BytesIO
from unittest.mock import patch
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import require_admin
from app.database import Base, get_db
from app.product_media_zip import (
    ProductMediaZipConflictError,
    ProductMediaZipError,
    inspect_product_media_zip,
    upload_product_media_operations,
)
from app.routers import admin, products


def image_bytes(format_name="PNG", color="navy") -> bytes:
    output = BytesIO()
    Image.new("RGB", (12, 12), color=color).save(output, format=format_name)
    return output.getvalue()


def pdf_bytes() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


def encrypted_pdf_bytes() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    writer.write(output)
    return output.getvalue()


def zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for path, contents in entries:
            archive.writestr(path, contents)
    return output.getvalue()


def storage_uri(object_name, *_args, **_kwargs):
    return f"minio://alfil-catalog/{object_name}"


class ProductMediaZipTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            brand = models.Brand(name="HP", slug="hp")
            category = models.Category(name="Laptops", slug="laptops")
            user = models.AdminUser(
                username="media.admin",
                password_hash="not-used",
                role="admin",
            )
            db.add_all([brand, category, user])
            db.flush()
            db.add_all(
                [
                    models.Product(
                        sku="SKU-001",
                        name="Producto Uno",
                        slug="producto-uno",
                        brand_id=brand.id,
                        category_id=category.id,
                        available_stock=1,
                        status="active",
                    ),
                    models.Product(
                        sku="SKU-002",
                        name="Producto Dos",
                        slug="producto-dos",
                        brand_id=brand.id,
                        category_id=category.id,
                        available_stock=1,
                        status="active",
                    ),
                ]
            )
            db.commit()
            self.admin_id = user.id

        self.app = FastAPI()
        self.app.include_router(products.router)
        self.app.include_router(admin.router)

        def override_db():
            with self.Session() as db:
                yield db

        self.app.dependency_overrides[get_db] = override_db
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def authenticate(self):
        self.app.dependency_overrides[require_admin] = lambda: models.AdminUser(
            id=self.admin_id,
            username="media.admin",
            password_hash="not-used",
            role="admin",
        )

    def inspect(self, entries):
        with self.Session() as db:
            return inspect_product_media_zip(
                db,
                zip_bytes(entries),
                filename="media.zip",
            )

    def post_zip(self, endpoint, entries, filename="media.zip"):
        return self.client.post(
            endpoint,
            files={"file": (filename, zip_bytes(entries), "application/zip")},
        )

    def test_valid_zip_with_images(self):
        preview, _ = self.inspect(
            [
                ("imagenes/sku-001_1.png", image_bytes()),
                ("imagenes/SKU-001_2.jpg", image_bytes("JPEG")),
            ]
        )
        self.assertTrue(preview["can_upload"])
        self.assertEqual(preview["image_count"], 2)
        self.assertEqual([item["order"] for item in preview["files"]], [1, 2])
        self.assertEqual({item["sku"] for item in preview["files"]}, {"SKU-001"})

    def test_valid_zip_with_pdf(self):
        preview, _ = self.inspect([("fichas/SKU-001.pdf", pdf_bytes())])
        self.assertTrue(preview["can_upload"])
        self.assertEqual(preview["document_count"], 1)
        self.assertEqual(preview["files"][0]["content_type"], "application/pdf")

    def test_valid_combined_zip_for_two_products(self):
        preview, _ = self.inspect(
            [
                ("imagenes/SKU-001_1.png", image_bytes()),
                ("fichas/SKU-001.pdf", pdf_bytes()),
                ("imagenes/SKU-002_1.jpg", image_bytes("JPEG")),
                ("fichas/SKU-002.pdf", pdf_bytes()),
            ]
        )
        self.assertTrue(preview["can_upload"])
        self.assertEqual(preview["related_products"], 2)
        self.assertEqual(preview["image_count"], 2)
        self.assertEqual(preview["document_count"], 2)

    def test_unknown_sku_is_rejected(self):
        preview, _ = self.inspect([("imagenes/NO-EXISTE_1.png", image_bytes())])
        self.assertFalse(preview["can_upload"])
        self.assertIn("No existe", " ".join(preview["files"][0]["errors"]))

    def test_corrupt_image_and_pdf_are_rejected(self):
        for path, contents, expected in [
            ("imagenes/SKU-001_1.png", b"not-an-image", "imagen válida"),
            ("fichas/SKU-001.pdf", b"%PDF-1.7\nnot-a-pdf", "corrupto"),
        ]:
            with self.subTest(path=path):
                preview, _ = self.inspect([(path, contents)])
                self.assertFalse(preview["can_upload"])
                self.assertIn(expected, " ".join(preview["files"][0]["errors"]))

    def test_encrypted_pdf_is_rejected(self):
        preview, _ = self.inspect(
            [("fichas/SKU-001.pdf", encrypted_pdf_bytes())]
        )
        self.assertFalse(preview["can_upload"])
        self.assertIn("protegidos", " ".join(preview["files"][0]["errors"]))

    def test_fake_image_extension_is_rejected(self):
        preview, _ = self.inspect(
            [("imagenes/SKU-001_1.jpg", image_bytes("PNG"))]
        )
        self.assertFalse(preview["can_upload"])
        self.assertIn("no coincide", " ".join(preview["files"][0]["errors"]))

    def test_unsafe_or_disallowed_paths_are_rejected(self):
        for path in [
            "../SKU-001_1.png",
            "otros/SKU-001_1.png",
            "SKU-001_1.png",
            "imagenes/sub/SKU-001_1.png",
            "imagenes/.oculta.png",
            "imagenes\\SKU-001_1.png",
            "imagenes/SKU-001.exe_1.jpg",
        ]:
            with self.subTest(path=path):
                preview, _ = self.inspect([(path, image_bytes())])
                self.assertFalse(preview["can_upload"])

    def test_symbolic_link_entry_is_rejected(self):
        output = BytesIO()
        info = ZipInfo("imagenes/SKU-001_1.png")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with ZipFile(output, "w") as archive:
            archive.writestr(info, "target")
        with self.Session() as db:
            preview, _ = inspect_product_media_zip(
                db,
                output.getvalue(),
                filename="media.zip",
            )
        self.assertFalse(preview["can_upload"])
        self.assertIn("simbólicos", " ".join(preview["files"][0]["errors"]))

    def test_empty_corrupt_and_disallowed_empty_directory_archives_are_rejected(self):
        with self.Session() as db:
            with self.assertRaisesRegex(ProductMediaZipError, "vacío"):
                inspect_product_media_zip(db, b"", filename="media.zip")
            with self.assertRaisesRegex(ProductMediaZipError, "ZIP válido"):
                inspect_product_media_zip(db, b"PK-not-a-zip", filename="media.zip")
            with self.assertRaisesRegex(ProductMediaZipError, "carpeta no permitida"):
                inspect_product_media_zip(
                    db,
                    zip_bytes([("otra/", b"")]),
                    filename="media.zip",
                )

    def test_per_file_size_limits_are_enforced(self):
        with self.Session() as db, patch(
            "app.product_media_zip.MEDIA_ZIP_IMAGE_MAX_BYTES", 10
        ):
            preview, _ = inspect_product_media_zip(
                db,
                zip_bytes([("imagenes/SKU-001_1.png", image_bytes())]),
                filename="media.zip",
            )
            self.assertFalse(preview["can_upload"])
            self.assertIn("límite", " ".join(preview["files"][0]["errors"]))
        with self.Session() as db, patch(
            "app.product_media_zip.MEDIA_ZIP_PDF_MAX_BYTES", 10
        ):
            preview, _ = inspect_product_media_zip(
                db,
                zip_bytes([("fichas/SKU-001.pdf", pdf_bytes())]),
                filename="media.zip",
            )
            self.assertFalse(preview["can_upload"])

    def test_duplicate_or_nonconsecutive_image_orders_are_rejected(self):
        repeated, _ = self.inspect(
            [
                ("imagenes/SKU-001_1.png", image_bytes()),
                ("imagenes/SKU-001_1.jpg", image_bytes("JPEG")),
            ]
        )
        missing, _ = self.inspect(
            [
                ("imagenes/SKU-002_1.png", image_bytes()),
                ("imagenes/SKU-002_3.png", image_bytes(color="red")),
            ]
        )
        self.assertFalse(repeated["can_upload"])
        self.assertFalse(missing["can_upload"])
        self.assertIn("repetidos", " ".join(repeated["products"][0]["errors"]))
        self.assertIn("consecutivos", " ".join(missing["products"][0]["errors"]))

    def test_more_than_five_images_is_rejected(self):
        entries = [
            (f"imagenes/SKU-001_{index}.png", image_bytes(color=(index, 0, 0)))
            for index in range(1, 7)
        ]
        preview, _ = self.inspect(entries)
        self.assertFalse(preview["can_upload"])
        self.assertIn("Solo se permiten 5", " ".join(preview["products"][0]["errors"]))

    def test_more_than_one_datasheet_is_rejected_case_insensitively(self):
        preview, _ = self.inspect(
            [
                ("fichas/SKU-001.pdf", pdf_bytes()),
                ("fichas/sku-001.pdf", pdf_bytes()),
            ]
        )
        self.assertFalse(preview["can_upload"])
        self.assertIn("Solo se permite una", " ".join(preview["products"][0]["errors"]))

    def test_existing_images_or_datasheet_are_conflicts(self):
        with self.Session() as db:
            first = db.query(models.Product).filter_by(sku="SKU-001").one()
            second = db.query(models.Product).filter_by(sku="SKU-002").one()
            db.add(models.ProductImage(product_id=first.id, url="https://old/image.jpg"))
            db.add(
                models.ProductDocument(
                    product_id=second.id,
                    title="Ficha",
                    document_type="datasheet",
                    storage_uri="https://old/file.pdf",
                    original_filename="file.pdf",
                )
            )
            db.commit()
        image_preview, _ = self.inspect(
            [("imagenes/SKU-001_1.png", image_bytes())]
        )
        pdf_preview, _ = self.inspect([("fichas/SKU-002.pdf", pdf_bytes())])
        self.assertFalse(image_preview["can_upload"])
        self.assertFalse(pdf_preview["can_upload"])
        self.assertIn("ya tiene imágenes", " ".join(image_preview["files"][0]["errors"]))
        self.assertIn("ya tiene una ficha", " ".join(pdf_preview["files"][0]["errors"]))

    def test_archive_file_count_and_expanded_size_limits(self):
        entries = [
            ("imagenes/SKU-001_1.png", image_bytes()),
            ("fichas/SKU-002.pdf", pdf_bytes()),
        ]
        with self.Session() as db, patch(
            "app.product_media_zip.MEDIA_ZIP_MAX_FILES", 1
        ):
            with self.assertRaisesRegex(ProductMediaZipError, "máximo"):
                inspect_product_media_zip(db, zip_bytes(entries), filename="media.zip")
        with self.Session() as db, patch(
            "app.product_media_zip.MEDIA_ZIP_MAX_EXPANDED_BYTES", 10
        ):
            with self.assertRaisesRegex(ProductMediaZipError, "descomprimido"):
                inspect_product_media_zip(db, zip_bytes(entries), filename="media.zip")

    def test_validation_endpoint_requires_auth_and_never_uploads(self):
        entries = [("imagenes/SKU-001_1.png", image_bytes())]
        unauthenticated = self.post_zip(
            "/api/admin/products/media-import/validate", entries
        )
        self.assertEqual(unauthenticated.status_code, 401)
        self.authenticate()
        with patch("app.product_media.put_object") as put_mock:
            authenticated = self.post_zip(
                "/api/admin/products/media-import/validate", entries
            )
        self.assertEqual(authenticated.status_code, 200, authenticated.text)
        self.assertTrue(authenticated.json()["can_upload"])
        put_mock.assert_not_called()
        with self.Session() as db:
            self.assertEqual(db.query(models.ProductImage).count(), 0)

    def test_definitive_endpoint_requires_authentication(self):
        response = self.post_zip(
            "/api/admin/products/media-import",
            [("imagenes/SKU-001_1.png", image_bytes())],
        )
        self.assertEqual(response.status_code, 401)

    def test_zip_size_limit_is_enforced_by_endpoint(self):
        self.authenticate()
        with patch("app.routers.admin.MEDIA_ZIP_MAX_BYTES", 10):
            response = self.post_zip(
                "/api/admin/products/media-import/validate",
                [("imagenes/SKU-001_1.png", image_bytes())],
            )
        self.assertEqual(response.status_code, 413)

    def test_definitive_upload_creates_ordered_primary_images_and_documents(self):
        self.authenticate()
        entries = [
            ("imagenes/SKU-001_1.png", image_bytes()),
            ("imagenes/SKU-001_2.jpg", image_bytes("JPEG")),
            ("fichas/SKU-001.pdf", pdf_bytes()),
            ("imagenes/SKU-002_1.png", image_bytes(color="green")),
        ]
        with patch("app.product_media.put_object", side_effect=storage_uri):
            response = self.post_zip("/api/admin/products/media-import", entries)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["uploaded_images"], 3)
        self.assertEqual(response.json()["uploaded_documents"], 1)
        with self.Session() as db:
            first = db.query(models.Product).filter_by(sku="SKU-001").one()
            images = db.query(models.ProductImage).filter_by(product_id=first.id).order_by(
                models.ProductImage.sort_order
            ).all()
            self.assertEqual([image.sort_order for image in images], [0, 1])
            self.assertEqual(db.query(models.ProductDocument).count(), 1)
            self.assertEqual(db.query(models.AdminAuditLog).count(), 4)
            self.assertTrue(
                all(
                    log.detail["source"] == "zip_media_import"
                    for log in db.query(models.AdminAuditLog).all()
                )
            )
        images_response = self.client.get(f"/api/admin/products/{first.id}/images")
        self.assertTrue(images_response.json()[0]["is_primary"])
        self.assertFalse(images_response.json()[1]["is_primary"])

    def test_second_upload_is_rejected_without_new_objects(self):
        self.authenticate()
        entries = [("imagenes/SKU-001_1.png", image_bytes())]
        with patch("app.product_media.put_object", side_effect=storage_uri):
            first = self.post_zip("/api/admin/products/media-import", entries)
            second = self.post_zip("/api/admin/products/media-import", entries)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        with self.Session() as db:
            self.assertEqual(db.query(models.ProductImage).count(), 1)

    def test_storage_failure_cleans_uploaded_objects_and_rolls_back(self):
        with self.Session() as db:
            user = db.get(models.AdminUser, self.admin_id)
            preview, operations = inspect_product_media_zip(
                db,
                zip_bytes(
                    [
                        ("imagenes/SKU-001_1.png", image_bytes()),
                        ("imagenes/SKU-001_2.png", image_bytes(color="red")),
                    ]
                ),
                filename="media.zip",
            )
            self.assertTrue(preview["can_upload"])
            with patch(
                "app.product_media_zip.save_product_media_object",
                side_effect=[
                    "minio://alfil-catalog/first",
                    RuntimeError("storage failed"),
                ],
            ), patch("app.product_media_zip.remove_object_strict") as remove_mock:
                with self.assertRaisesRegex(RuntimeError, "storage failed"):
                    upload_product_media_operations(db, user, operations)
                remove_mock.assert_called_once_with("minio://alfil-catalog/first")
        with self.Session() as db:
            self.assertEqual(db.query(models.ProductImage).count(), 0)

    def test_database_failure_rolls_back_and_cleans_all_objects(self):
        with self.Session() as db:
            user = db.get(models.AdminUser, self.admin_id)
            _, operations = inspect_product_media_zip(
                db,
                zip_bytes([("imagenes/SKU-001_1.png", image_bytes())]),
                filename="media.zip",
            )
            with patch(
                "app.product_media_zip.save_product_media_object",
                return_value="minio://alfil-catalog/object",
            ), patch("app.product_media_zip.remove_object_strict") as remove_mock, patch.object(
                db,
                "commit",
                side_effect=IntegrityError("INSERT", {}, Exception("failure")),
            ):
                with self.assertRaises(IntegrityError):
                    upload_product_media_operations(db, user, operations)
                remove_mock.assert_called_once()
        with self.Session() as db:
            self.assertEqual(db.query(models.ProductImage).count(), 0)
            self.assertEqual(db.query(models.AdminAuditLog).count(), 0)

    def test_concurrent_conflict_after_upload_triggers_compensation(self):
        with self.Session() as db:
            user = db.get(models.AdminUser, self.admin_id)
            _, operations = inspect_product_media_zip(
                db,
                zip_bytes([("imagenes/SKU-001_1.png", image_bytes())]),
                filename="media.zip",
            )
            with patch(
                "app.product_media_zip._current_conflicts",
                side_effect=[[], ["conflicto concurrente"]],
            ), patch(
                "app.product_media_zip.save_product_media_object",
                return_value="minio://alfil-catalog/object",
            ), patch("app.product_media_zip.remove_object_strict") as remove_mock:
                with self.assertRaises(ProductMediaZipConflictError):
                    upload_product_media_operations(db, user, operations)
                remove_mock.assert_called_once()
        with self.Session() as db:
            self.assertEqual(db.query(models.ProductImage).count(), 0)

    def test_manual_upload_and_deletion_still_work_for_zip_media(self):
        self.authenticate()
        with patch("app.product_media.put_object", side_effect=storage_uri):
            manual = self.client.post(
                "/api/admin/products/1/images",
                files={"file": ("manual.png", image_bytes(), "image/png")},
                data={"alt": "Manual", "is_primary": "true"},
            )
        self.assertEqual(manual.status_code, 201, manual.text)
        self.assertEqual(manual.json()["alt"], "Manual")
        image_id = manual.json()["id"]
        with patch("app.routers.admin.remove_object_strict", return_value=True) as remove_mock:
            deleted = self.client.delete(f"/api/admin/products/1/images/{image_id}")
        self.assertEqual(deleted.status_code, 204)
        remove_mock.assert_called_once()

    def test_manual_admin_upload_preserves_blank_alt_fallback(self):
        self.authenticate()
        with patch("app.product_media.put_object", side_effect=storage_uri):
            response = self.client.post(
                "/api/admin/products/1/images",
                files={"file": ("manual.png", image_bytes(), "image/png")},
                data={"alt": "   ", "is_primary": "false"},
            )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["alt"], "Producto Uno")

    def test_zip_media_uses_existing_public_and_admin_views_and_manual_delete(self):
        self.authenticate()
        entries = [
            ("imagenes/SKU-001_1.png", image_bytes()),
            ("fichas/SKU-001.pdf", pdf_bytes()),
        ]
        with patch("app.product_media.put_object", side_effect=storage_uri):
            uploaded = self.post_zip("/api/admin/products/media-import", entries)
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        public = self.client.get("/api/products/producto-uno")
        self.assertEqual(public.status_code, 200, public.text)
        self.assertEqual(len(public.json()["images"]), 1)
        self.assertEqual(len(public.json()["documents"]), 1)
        self.assertTrue(public.json()["documents"][0]["download_url"])
        with self.Session() as db:
            document = db.query(models.ProductDocument).one()
            image = db.query(models.ProductImage).one()
        with patch(
            "app.routers.admin.remove_object_strict", return_value=True
        ) as remove_mock:
            deleted_document = self.client.delete(
                f"/api/admin/products/1/documents/{document.id}"
            )
            deleted_image = self.client.delete(
                f"/api/admin/products/1/images/{image.id}"
            )
        self.assertEqual(deleted_document.status_code, 204)
        self.assertEqual(deleted_image.status_code, 204)
        self.assertEqual(remove_mock.call_count, 2)

    def test_legacy_media_urls_remain_accessible(self):
        self.authenticate()
        with self.Session() as db:
            product = db.query(models.Product).filter_by(sku="SKU-001").one()
            db.add(
                models.ProductImage(
                    product_id=product.id,
                    url="https://legacy.example/image.jpg",
                )
            )
            db.add(
                models.ProductDocument(
                    product_id=product.id,
                    title="Ficha anterior",
                    storage_uri="https://legacy.example/file.pdf",
                    original_filename="file.pdf",
                )
            )
            db.commit()
        public = self.client.get("/api/products/producto-uno")
        self.assertEqual(public.json()["images"][0]["url"], "https://legacy.example/image.jpg")
        self.assertEqual(
            public.json()["documents"][0]["download_url"],
            "https://legacy.example/file.pdf",
        )


if __name__ == "__main__":
    unittest.main()
