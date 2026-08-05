import unittest
from io import BytesIO
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import require_admin
from app.database import Base, get_db
from app.product_excel_import import (
    ProductImportFileError,
    create_products_from_preview,
    validate_product_workbook,
    validate_product_workbook_for_db,
)
from app.product_excel_template import PRODUCT_HEADERS
from app.routers import admin


BRANDS = [(1, "HP")]
CATEGORIES = [(2, "Laptops")]
VALID_ROW = [
    "Laptop Pro",
    "sku-001",
    "PN-001",
    "hp",
    "LAPTOPS",
    4,
    "Nuevo",
    1499.90,
    "USD",
    "Publicado",
    "Equipo empresarial",
    "Descripción completa",
    "Liviana; Rápida",
    "RAM=16 GB; Disco=512 GB",
]


def workbook_bytes(rows=None, *, headers=None, sheet_name="Productos") -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(headers or PRODUCT_HEADERS)
    for row in rows or []:
        worksheet.append(row)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def validate(rows, *, existing_skus=()):
    return validate_product_workbook(
        workbook_bytes(rows),
        filename="productos.xlsx",
        brands=BRANDS,
        categories=CATEGORIES,
        existing_skus=existing_skus,
    )


class ProductExcelImportServiceTests(unittest.TestCase):
    def test_valid_file_returns_normalized_preview_and_defaults(self):
        result = validate([VALID_ROW])

        self.assertTrue(result["can_import"])
        self.assertEqual(result["total_rows"], 1)
        self.assertEqual(result["valid_rows"], 1)
        normalized = result["rows"][0]["normalized"]
        self.assertEqual(normalized["sku"], "SKU-001")
        self.assertEqual(normalized["brand_id"], 1)
        self.assertEqual(normalized["category_id"], 2)
        self.assertFalse(normalized["is_used"])
        self.assertEqual(normalized["currency"], "USD")
        self.assertEqual(normalized["status"], "active")
        self.assertEqual(normalized["highlights"], ["Liviana", "Rápida"])
        self.assertEqual(normalized["specs"], {"RAM": "16 GB", "Disco": "512 GB"})
        self.assertEqual(normalized["stock_note"], "Disponible bajo cotización")
        self.assertEqual(normalized["stock_type"], "serialized")

    def test_missing_products_sheet_is_rejected(self):
        with self.assertRaisesRegex(ProductImportFileError, "Productos"):
            validate_product_workbook(
                workbook_bytes([VALID_ROW], sheet_name="Otra"),
                filename="productos.xlsx",
                brands=BRANDS,
                categories=CATEGORIES,
                existing_skus=(),
            )

    def test_wrong_headers_are_rejected(self):
        headers = PRODUCT_HEADERS.copy()
        headers[0] = "producto"
        with self.assertRaisesRegex(ProductImportFileError, "encabezados"):
            validate_product_workbook(
                workbook_bytes([VALID_ROW], headers=headers),
                filename="productos.xlsx",
                brands=BRANDS,
                categories=CATEGORIES,
                existing_skus=(),
            )

    def test_empty_products_sheet_is_rejected(self):
        with self.assertRaisesRegex(ProductImportFileError, "no contiene filas"):
            validate([])

    def test_duplicate_skus_in_file_are_reported_on_both_rows(self):
        other = VALID_ROW.copy()
        other[0] = "Laptop Dos"
        other[1] = " SKU-001 "
        result = validate([VALID_ROW, other])

        self.assertEqual(result["invalid_rows"], 2)
        for row in result["rows"]:
            self.assertIn("SKU repetido dentro del archivo.", row["errors"])

    def test_existing_sku_is_rejected_case_insensitively(self):
        result = validate([VALID_ROW], existing_skus=["sku-001"])
        self.assertIn("SKU ya existe en el catálogo.", result["rows"][0]["errors"])

    def test_missing_brand_and_category_are_rejected(self):
        row = VALID_ROW.copy()
        row[3] = "Marca inexistente"
        row[4] = "Categoría inexistente"
        errors = validate([row])["rows"][0]["errors"]
        self.assertTrue(any("Marca no existe" in error for error in errors))
        self.assertTrue(any("Categoría no existe" in error for error in errors))

    def test_negative_and_decimal_stock_are_rejected(self):
        for value, expected in [(-1, "negativo"), (1.5, "decimales")]:
            with self.subTest(value=value):
                row = VALID_ROW.copy()
                row[5] = value
                errors = validate([row])["rows"][0]["errors"]
                self.assertTrue(any(expected in error for error in errors))

    def test_invalid_price_is_rejected(self):
        for value in ["S/ 1,200", -1, 10.999]:
            with self.subTest(value=value):
                row = VALID_ROW.copy()
                row[7] = value
                self.assertTrue(validate([row])["rows"][0]["errors"])

    def test_invalid_condition_currency_and_status_are_rejected(self):
        for column, value, label in [
            (6, "Seminuevo", "Condición"),
            (8, "EUR", "Moneda"),
            (9, "Archivado", "Estado"),
        ]:
            with self.subTest(label=label):
                row = VALID_ROW.copy()
                row[column] = value
                errors = validate([row])["rows"][0]["errors"]
                self.assertTrue(any(label in error for error in errors))

    def test_malformed_specs_are_rejected(self):
        row = VALID_ROW.copy()
        row[13] = "Sin igual; =vacía; RAM=8; RAM=16"
        errors = validate([row])["rows"][0]["errors"]
        self.assertTrue(any("no contiene" in error for error in errors))
        self.assertTrue(any("clave vacía" in error for error in errors))
        self.assertTrue(any("repetida" in error for error in errors))

    def test_data_after_row_300_is_rejected(self):
        rows = []
        for index in range(300):
            row = VALID_ROW.copy()
            row[0] = f"Producto {index + 1}"
            row[1] = f"SKU-{index + 1:03d}"
            rows.append(row)
        with self.assertRaisesRegex(ProductImportFileError, "fila 300"):
            validate(rows)


class ProductExcelImportEndpointTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add(models.Brand(name="HP", slug="hp"))
            db.add(models.Category(name="Laptops", slug="laptops"))
            admin_user = models.AdminUser(
                username="import.admin",
                password_hash="not-used-in-tests",
                role="admin",
            )
            db.add(admin_user)
            db.commit()
            self.admin_id = admin_user.id

        self.app = FastAPI()
        self.app.include_router(admin.router)

        def override_db():
            with self.Session() as db:
                yield db

        self.app.dependency_overrides[get_db] = override_db
        self.client = TestClient(self.app)

    def authenticate(self):
        self.app.dependency_overrides[require_admin] = lambda: models.AdminUser(
            id=self.admin_id,
            username="import.admin",
            password_hash="not-used-in-tests",
            role="admin",
        )

    def import_rows(self, rows, filename="productos.xlsx"):
        return self.client.post(
            "/api/admin/products/import",
            files={"file": (filename, workbook_bytes(rows))},
        )

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_endpoint_requires_admin_authentication(self):
        response = self.client.post(
            "/api/admin/products/import/validate",
            files={"file": ("productos.xlsx", workbook_bytes([VALID_ROW]))},
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_endpoint_request_does_not_create_products(self):
        self.authenticate()
        with self.Session() as db:
            before = db.query(models.Product).count()

        response = self.client.post(
            "/api/admin/products/import/validate",
            files={"file": ("productos.xlsx", workbook_bytes([VALID_ROW]))},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["can_import"])
        with self.Session() as db:
            after = db.query(models.Product).count()
        self.assertEqual(before, after)

    def test_import_endpoint_requires_admin_authentication(self):
        response = self.import_rows([VALID_ROW])
        self.assertEqual(response.status_code, 401)

    def test_authenticated_import_creates_one_product_and_audit(self):
        self.authenticate()
        response = self.import_rows([VALID_ROW])

        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["imported_count"], 1)
        self.assertEqual(body["products"][0]["sku"], "SKU-001")
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 1)
            audit_log = db.query(models.AdminAuditLog).one()
            self.assertEqual(audit_log.action, "product.create")
            self.assertEqual(audit_log.detail["source"], "excel_import")

    def test_import_creates_multiple_products_with_repeated_names_and_unique_slugs(self):
        self.authenticate()
        rows = []
        for index in range(3):
            row = VALID_ROW.copy()
            row[1] = f"SKU-{index + 1:03d}"
            rows.append(row)

        response = self.import_rows(rows)

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["imported_count"], 3)
        self.assertEqual(
            [product["slug"] for product in response.json()["products"]],
            ["laptop-pro", "laptop-pro-2", "laptop-pro-3"],
        )
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 3)
        list_response = self.client.get(
            "/api/admin/products",
            params={"page_size": 100},
        )
        self.assertEqual(list_response.status_code, 200, list_response.text)
        self.assertEqual(list_response.json()["total"], 3)
        self.assertEqual(
            {product["sku"] for product in list_response.json()["items"]},
            {"SKU-001", "SKU-002", "SKU-003"},
        )

    def test_import_slug_avoids_collision_with_existing_product(self):
        self.authenticate()
        with self.Session() as db:
            brand = db.query(models.Brand).one()
            category = db.query(models.Category).one()
            db.add(
                models.Product(
                    sku="EXISTING-SLUG",
                    name="Laptop Pro",
                    slug="laptop-pro",
                    brand_id=brand.id,
                    category_id=category.id,
                )
            )
            db.commit()

        response = self.import_rows([VALID_ROW])
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["products"][0]["slug"], "laptop-pro-2")

    def test_file_modified_after_preview_is_revalidated_and_rejected(self):
        self.authenticate()
        preview_response = self.client.post(
            "/api/admin/products/import/validate",
            files={"file": ("productos.xlsx", workbook_bytes([VALID_ROW]))},
        )
        self.assertTrue(preview_response.json()["can_import"])
        modified = VALID_ROW.copy()
        modified[7] = "S/ 100"

        response = self.import_rows([modified])

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["detail"]["preview"]["can_import"])
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 0)

    def test_sku_created_after_preview_cancels_import(self):
        self.authenticate()
        preview_response = self.client.post(
            "/api/admin/products/import/validate",
            files={"file": ("productos.xlsx", workbook_bytes([VALID_ROW]))},
        )
        self.assertTrue(preview_response.json()["can_import"])
        with self.Session() as db:
            brand = db.query(models.Brand).one()
            category = db.query(models.Category).one()
            db.add(
                models.Product(
                    sku="SKU-001",
                    name="Creado por otro administrador",
                    slug="creado-por-otro-administrador",
                    brand_id=brand.id,
                    category_id=category.id,
                )
            )
            db.commit()

        response = self.import_rows([VALID_ROW])

        self.assertEqual(response.status_code, 409)
        self.assertIn("ya no es válido", response.json()["detail"]["message"])
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 1)

    def test_missing_brand_or_category_cancels_import(self):
        self.authenticate()
        for column, value in [(3, "No existe"), (4, "No existe")]:
            with self.subTest(column=column):
                row = VALID_ROW.copy()
                row[column] = value
                response = self.import_rows([row])
                self.assertEqual(response.status_code, 409)
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 0)

    def test_empty_or_invalid_file_does_not_import(self):
        self.authenticate()
        empty_response = self.import_rows([])
        invalid = VALID_ROW.copy()
        invalid[5] = -1
        invalid_response = self.import_rows([invalid])

        self.assertEqual(empty_response.status_code, 400)
        self.assertEqual(invalid_response.status_code, 409)
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 0)

    def test_reimporting_same_file_is_rejected_by_existing_skus(self):
        self.authenticate()
        first = self.import_rows([VALID_ROW])
        second = self.import_rows([VALID_ROW])

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 1)

    def test_service_rolls_back_every_row_when_second_creation_fails(self):
        with self.Session() as db:
            user = db.get(models.AdminUser, self.admin_id)
            rows = [VALID_ROW.copy(), VALID_ROW.copy()]
            rows[1][0] = "Producto Dos"
            rows[1][1] = "SKU-002"
            preview = validate_product_workbook_for_db(
                db,
                workbook_bytes(rows),
                filename="productos.xlsx",
            )
            from app.product_excel_import import create_product_record as real_create

            calls = 0

            def fail_on_second(session, payload):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("simulated persistence failure")
                return real_create(session, payload)

            with patch(
                "app.product_excel_import.create_product_record",
                side_effect=fail_on_second,
            ):
                with self.assertRaisesRegex(RuntimeError, "simulated"):
                    create_products_from_preview(db, user, preview)

        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 0)
            self.assertEqual(db.query(models.AdminAuditLog).count(), 0)

    def test_service_rolls_back_on_integrity_error_at_commit(self):
        with self.Session() as db:
            user = db.get(models.AdminUser, self.admin_id)
            preview = validate_product_workbook_for_db(
                db,
                workbook_bytes([VALID_ROW]),
                filename="productos.xlsx",
            )
            with patch.object(
                db,
                "commit",
                side_effect=IntegrityError("INSERT", {}, Exception("duplicate SKU")),
            ):
                with self.assertRaises(IntegrityError):
                    create_products_from_preview(db, user, preview)

        with self.Session() as db:
            self.assertEqual(db.query(models.Product).count(), 0)
            self.assertEqual(db.query(models.AdminAuditLog).count(), 0)

    def test_endpoint_hides_integrity_error_details(self):
        self.authenticate()
        with patch(
            "app.routers.admin.create_products_from_preview",
            side_effect=IntegrityError("INSERT", {}, Exception("private sql detail")),
        ):
            response = self.import_rows([VALID_ROW])

        self.assertEqual(response.status_code, 409)
        self.assertNotIn("private sql detail", response.text)
        self.assertIn("SKU", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
