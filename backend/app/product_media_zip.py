import logging
import os
import re
import stat
import warnings
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy.orm import Session, joinedload

from app import models
from app.product_creation import normalize_sku
from app.product_media import (
    build_product_document,
    build_product_image,
    safe_filename,
    save_product_media_object,
)
from app.storage import StorageUnavailableError, remove_object_strict


logger = logging.getLogger(__name__)


def _env_limit(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


MEDIA_ZIP_MAX_BYTES = _env_limit("MEDIA_ZIP_MAX_BYTES", 100 * 1024 * 1024)
MEDIA_ZIP_MAX_FILES = _env_limit("MEDIA_ZIP_MAX_FILES", 500)
MEDIA_ZIP_MAX_EXPANDED_BYTES = _env_limit(
    "MEDIA_ZIP_MAX_EXPANDED_BYTES", 300 * 1024 * 1024
)
MEDIA_ZIP_MAX_IMAGES_PER_PRODUCT = _env_limit(
    "MEDIA_ZIP_MAX_IMAGES_PER_PRODUCT", 5
)
MEDIA_ZIP_IMAGE_MAX_BYTES = _env_limit(
    "MEDIA_ZIP_IMAGE_MAX_BYTES", 5 * 1024 * 1024
)
MEDIA_ZIP_PDF_MAX_BYTES = _env_limit(
    "MEDIA_ZIP_PDF_MAX_BYTES", 15 * 1024 * 1024
)
MEDIA_ZIP_MAX_COMPRESSION_RATIO = _env_limit(
    "MEDIA_ZIP_MAX_COMPRESSION_RATIO", 1000
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", {".jpg", ".jpeg"}),
    "PNG": ("image/png", {".png"}),
    "WEBP": ("image/webp", {".webp"}),
}
ALLOWED_DIRECTORIES = {"imagenes", "fichas"}
SAFE_SKU_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class ProductMediaZipError(ValueError):
    pass


class ProductMediaZipConflictError(RuntimeError):
    pass


def safe_zip_filename(filename: str | None) -> str:
    name = re.split(r"[\\/]", filename or "archivos.zip")[-1]
    cleaned = "".join(character for character in name if character.isprintable()).strip()
    return cleaned[:255] or "archivos.zip"


def _is_symlink(info: ZipInfo) -> bool:
    mode = info.external_attr >> 16
    return stat.S_IFMT(mode) == stat.S_IFLNK


def _path_errors(info: ZipInfo) -> list[str]:
    path = info.filename
    errors: list[str] = []
    if not path or "\\" in path:
        errors.append("La ruta usa un nombre vacío o separadores no permitidos.")
        return errors
    if any(ord(character) < 32 for character in path):
        errors.append("La ruta contiene caracteres de control no permitidos.")
    pure_path = PurePosixPath(path)
    parts = pure_path.parts
    if pure_path.is_absolute() or path.startswith("/") or ":" in parts[0]:
        errors.append("No se permiten rutas absolutas.")
    if ".." in parts:
        errors.append("La ruta contiene segmentos '..' no permitidos.")
    if any(part.startswith(".") for part in parts):
        errors.append("No se permiten archivos o carpetas ocultos.")
    if _is_symlink(info):
        errors.append("No se permiten enlaces simbólicos.")
    if len(parts) != 2 or parts[0] not in ALLOWED_DIRECTORIES:
        errors.append("El archivo debe estar directamente en 'imagenes/' o 'fichas/'.")
    if len(path) > 255 or (parts and len(parts[-1]) > 180):
        errors.append("La ruta o el nombre del archivo es demasiado largo.")
    if info.flag_bits & 0x1:
        errors.append("No se permiten entradas cifradas dentro del ZIP.")
    if info.file_size and (
        info.compress_size == 0
        or info.file_size / max(1, info.compress_size) > MEDIA_ZIP_MAX_COMPRESSION_RATIO
    ):
        errors.append("La relación de compresión de la entrada es sospechosa.")
    return errors


def _parse_image_name(filename: str, errors: list[str]) -> tuple[str, int | None, str]:
    stem, extension = os.path.splitext(filename)
    extension = extension.lower()
    if extension not in IMAGE_EXTENSIONS:
        errors.append("La imagen debe usar extensión JPG, JPEG, PNG o WebP.")
    if "_" not in stem:
        errors.append("La imagen debe nombrarse como SKU_ORDEN.extensión.")
        return "", None, extension
    sku_text, order_text = stem.rsplit("_", 1)
    if not sku_text or not SAFE_SKU_PATTERN.fullmatch(sku_text):
        errors.append("El SKU del nombre contiene caracteres no permitidos.")
    if not order_text.isdigit() or int(order_text or 0) <= 0:
        errors.append("El orden de imagen debe ser un entero positivo.")
        order = None
    else:
        order = int(order_text)
    return normalize_sku(sku_text), order, extension


def _parse_document_name(filename: str, errors: list[str]) -> tuple[str, str]:
    stem, extension = os.path.splitext(filename)
    extension = extension.lower()
    if extension != ".pdf":
        errors.append("La ficha técnica debe usar extensión PDF.")
    if not stem or not SAFE_SKU_PATTERN.fullmatch(stem):
        errors.append("El SKU del nombre contiene caracteres no permitidos.")
    return normalize_sku(stem), extension


def _validate_image(contents: bytes, extension: str, errors: list[str]) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(contents)) as image:
                detected_format = image.format
                image.verify()
            with Image.open(BytesIO(contents)) as image:
                image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning):
        errors.append("El contenido no es una imagen válida o está corrupto.")
        return "unknown"
    detected = IMAGE_FORMATS.get(detected_format or "")
    if not detected:
        errors.append("El formato real de la imagen no está permitido.")
        return "unknown"
    content_type, valid_extensions = detected
    if extension not in valid_extensions:
        errors.append("La extensión no coincide con el formato real de la imagen.")
    return content_type


def _validate_pdf(contents: bytes, errors: list[str]) -> str:
    if not contents.startswith(b"%PDF-"):
        errors.append("El contenido no corresponde a un archivo PDF.")
        return "unknown"
    try:
        reader = PdfReader(BytesIO(contents), strict=False)
        if reader.is_encrypted:
            errors.append("No se permiten PDF cifrados o protegidos con contraseña.")
        elif len(reader.pages) == 0:
            errors.append("El PDF no contiene páginas.")
    except (PdfReadError, OSError, ValueError, TypeError):
        errors.append("El PDF está corrupto o no puede leerse.")
    return "application/pdf"


def _read_entry(
    archive: ZipFile,
    info: ZipInfo,
    limit: int,
    errors: list[str],
) -> bytes:
    if info.file_size > limit:
        errors.append(f"El archivo supera el límite de {limit // (1024 * 1024)} MB.")
        return b""
    try:
        with archive.open(info, "r") as stream:
            contents = stream.read(limit + 1)
    except (BadZipFile, RuntimeError, OSError, ValueError):
        errors.append("La entrada está corrupta o no puede leerse.")
        return b""
    if len(contents) > limit:
        errors.append(f"El archivo supera el límite de {limit // (1024 * 1024)} MB.")
        return b""
    if not contents:
        errors.append("El archivo está vacío.")
    return contents


def _product_index(db: Session) -> dict[str, list[models.Product]]:
    products = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.images),
            joinedload(models.Product.documents),
        )
        .all()
    )
    index: dict[str, list[models.Product]] = defaultdict(list)
    for product in products:
        index[normalize_sku(product.sku)].append(product)
    return index


def inspect_product_media_zip(
    db: Session,
    contents: bytes,
    *,
    filename: str,
) -> tuple[dict, list[dict]]:
    if not contents:
        raise ProductMediaZipError("El archivo ZIP está vacío.")
    if not contents.startswith(b"PK"):
        raise ProductMediaZipError("El archivo no es un ZIP válido o está corrupto.")
    try:
        archive = ZipFile(BytesIO(contents), "r")
    except (BadZipFile, OSError, ValueError) as exc:
        raise ProductMediaZipError("El archivo no es un ZIP válido o está corrupto.") from exc

    try:
        infos = archive.infolist()
        if len(infos) > MEDIA_ZIP_MAX_FILES + len(ALLOWED_DIRECTORIES):
            raise ProductMediaZipError(
                f"El ZIP supera el máximo de {MEDIA_ZIP_MAX_FILES} archivos."
            )
        for info in infos:
            if info.is_dir():
                directory = info.filename.rstrip("/")
                if directory not in ALLOWED_DIRECTORIES:
                    raise ProductMediaZipError(
                        f"El ZIP contiene una carpeta no permitida: {info.filename}"
                    )
        file_infos = [info for info in infos if not info.is_dir()]
        if not file_infos:
            raise ProductMediaZipError("El ZIP no contiene imágenes ni fichas técnicas.")
        if len(file_infos) > MEDIA_ZIP_MAX_FILES:
            raise ProductMediaZipError(
                f"El ZIP supera el máximo de {MEDIA_ZIP_MAX_FILES} archivos."
            )
        expanded_size = sum(info.file_size for info in file_infos)
        if expanded_size > MEDIA_ZIP_MAX_EXPANDED_BYTES:
            raise ProductMediaZipError(
                "El contenido descomprimido supera el límite permitido de 300 MB."
            )

        products_by_sku = _product_index(db)
        rows: list[dict] = []
        operations: list[dict] = []
        rows_by_path: dict[str, list[dict]] = defaultdict(list)

        for info in file_infos:
            path = info.filename
            basename = PurePosixPath(path).name
            errors = _path_errors(info)
            warnings_list: list[str] = []
            parts = PurePosixPath(path).parts
            folder = parts[0] if len(parts) == 2 else ""
            media_type = "image" if folder == "imagenes" else (
                "document" if folder == "fichas" else "unknown"
            )
            sku = ""
            order = None
            extension = os.path.splitext(basename)[1].lower()
            if media_type == "image":
                sku, order, extension = _parse_image_name(basename, errors)
                max_bytes = MEDIA_ZIP_IMAGE_MAX_BYTES
            elif media_type == "document":
                sku, extension = _parse_document_name(basename, errors)
                max_bytes = MEDIA_ZIP_PDF_MAX_BYTES
            else:
                max_bytes = max(MEDIA_ZIP_IMAGE_MAX_BYTES, MEDIA_ZIP_PDF_MAX_BYTES)

            matches = products_by_sku.get(sku, []) if sku else []
            product = matches[0] if len(matches) == 1 else None
            if sku and not matches:
                errors.append("No existe un producto con el SKU indicado.")
            elif len(matches) > 1:
                errors.append("El SKU es ambiguo y coincide con más de un producto.")

            entry_contents = _read_entry(archive, info, max_bytes, errors)
            content_type = "unknown"
            if entry_contents and media_type == "image":
                content_type = _validate_image(entry_contents, extension, errors)
            elif entry_contents and media_type == "document":
                content_type = _validate_pdf(entry_contents, errors)

            row = {
                "path": path,
                "filename": basename,
                "type": media_type,
                "sku": product.sku if product else sku,
                "product_id": product.id if product else None,
                "product_name": product.name if product else "",
                "order": order,
                "size": info.file_size,
                "content_type": content_type,
                "valid": False,
                "errors": errors,
                "warnings": warnings_list,
            }
            rows.append(row)
            rows_by_path[path.casefold()].append(row)
            operations.append(
                {
                    "row": row,
                    "product": product,
                    "contents": entry_contents,
                    "extension": extension,
                    "content_type": content_type,
                }
            )

        for duplicated_rows in rows_by_path.values():
            if len(duplicated_rows) > 1:
                for row in duplicated_rows:
                    row["errors"].append("La ruta está duplicada dentro del ZIP.")

        grouped: dict[str, list[dict]] = defaultdict(list)
        for operation in operations:
            row = operation["row"]
            group_key = normalize_sku(row["sku"]) if row["sku"] else row["path"]
            grouped[group_key].append(operation)

        product_previews: list[dict] = []
        for group_operations in grouped.values():
            first = group_operations[0]
            product = first["product"]
            group_errors: list[str] = []
            image_operations = [
                operation
                for operation in group_operations
                if operation["row"]["type"] == "image"
            ]
            document_operations = [
                operation
                for operation in group_operations
                if operation["row"]["type"] == "document"
            ]
            orders = [
                operation["row"]["order"]
                for operation in image_operations
                if operation["row"]["order"] is not None
            ]
            duplicate_orders = {
                order for order, count in Counter(orders).items() if count > 1
            }
            if duplicate_orders:
                message = "Hay órdenes de imagen repetidos: " + ", ".join(
                    str(order) for order in sorted(duplicate_orders)
                ) + "."
                group_errors.append(message)
                for operation in image_operations:
                    if operation["row"]["order"] in duplicate_orders:
                        operation["row"]["errors"].append(message)
            unique_orders = sorted(set(orders))
            if unique_orders and unique_orders != list(range(1, len(unique_orders) + 1)):
                message = "Los órdenes de imagen deben comenzar en 1 y ser consecutivos."
                group_errors.append(message)
                for operation in image_operations:
                    operation["row"]["errors"].append(message)
            if len(image_operations) > MEDIA_ZIP_MAX_IMAGES_PER_PRODUCT:
                message = (
                    f"Solo se permiten {MEDIA_ZIP_MAX_IMAGES_PER_PRODUCT} imágenes "
                    "por producto."
                )
                group_errors.append(message)
                for operation in image_operations:
                    operation["row"]["errors"].append(message)
            if len(document_operations) > 1:
                message = "Solo se permite una ficha técnica por producto."
                group_errors.append(message)
                for operation in document_operations:
                    operation["row"]["errors"].append(message)
            if product and image_operations and product.images:
                message = f"El producto {product.sku} ya tiene imágenes registradas."
                group_errors.append(message)
                for operation in image_operations:
                    operation["row"]["errors"].append(message)
            existing_datasheet = bool(
                product
                and any(
                    document.document_type == "datasheet"
                    for document in product.documents
                )
            )
            if product and document_operations and existing_datasheet:
                message = f"El producto {product.sku} ya tiene una ficha técnica registrada."
                group_errors.append(message)
                for operation in document_operations:
                    operation["row"]["errors"].append(message)

            product_previews.append(
                {
                    "sku": first["row"]["sku"],
                    "product_id": product.id if product else None,
                    "product_name": product.name if product else "",
                    "images": len(image_operations),
                    "has_document": bool(document_operations),
                    "valid": bool(product) and not group_errors,
                    "errors": group_errors,
                }
            )

        for row in rows:
            row["valid"] = not row["errors"] and row["product_id"] is not None
        valid_files = sum(row["valid"] for row in rows)
        invalid_files = len(rows) - valid_files
        product_ids = {row["product_id"] for row in rows if row["product_id"] is not None}
        preview = {
            "filename": safe_zip_filename(filename),
            "total_files": len(rows),
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "related_products": len(product_ids),
            "image_count": sum(row["type"] == "image" for row in rows),
            "document_count": sum(row["type"] == "document" for row in rows),
            "can_upload": bool(rows)
            and invalid_files == 0
            and all(product["valid"] for product in product_previews),
            "files": rows,
            "products": product_previews,
        }
        return preview, operations
    finally:
        archive.close()


def _current_conflicts(db: Session, operations: list[dict]) -> list[str]:
    image_product_ids = {
        operation["product"].id
        for operation in operations
        if operation["product"] and operation["row"]["type"] == "image"
    }
    document_product_ids = {
        operation["product"].id
        for operation in operations
        if operation["product"] and operation["row"]["type"] == "document"
    }
    conflicts: list[str] = []
    if image_product_ids:
        existing_image_products = {
            product_id
            for (product_id,) in db.query(models.ProductImage.product_id)
            .filter(models.ProductImage.product_id.in_(image_product_ids))
            .distinct()
            .all()
        }
        conflicts.extend(
            f"El producto {operation['row']['sku']} ya tiene imágenes registradas."
            for operation in operations
            if operation["product"]
            and operation["product"].id in existing_image_products
            and operation["row"]["type"] == "image"
        )
    if document_product_ids:
        existing_document_products = {
            product_id
            for (product_id,) in db.query(models.ProductDocument.product_id)
            .filter(
                models.ProductDocument.product_id.in_(document_product_ids),
                models.ProductDocument.document_type == "datasheet",
            )
            .distinct()
            .all()
        }
        conflicts.extend(
            f"El producto {operation['row']['sku']} ya tiene una ficha técnica registrada."
            for operation in operations
            if operation["product"]
            and operation["product"].id in existing_document_products
            and operation["row"]["type"] == "document"
        )
    return sorted(set(conflicts))


def _cleanup_uploaded_objects(storage_uris: list[str]) -> None:
    for storage_uri in reversed(storage_uris):
        try:
            remove_object_strict(storage_uri)
        except StorageUnavailableError:
            logger.exception("Could not compensate uploaded object %s", storage_uri)


def upload_product_media_operations(
    db: Session,
    user: models.AdminUser,
    operations: list[dict],
) -> dict:
    if not operations:
        raise ValueError("No existen archivos válidos para subir.")
    conflicts = _current_conflicts(db, operations)
    if conflicts:
        raise ProductMediaZipConflictError(" ".join(conflicts))

    uploaded_uris: list[str] = []
    image_count = 0
    document_count = 0
    product_totals: dict[int, dict] = {}
    try:
        for operation in operations:
            row = operation["row"]
            product = db.get(models.Product, row["product_id"])
            if not product or normalize_sku(product.sku) != normalize_sku(row["sku"]):
                raise ProductMediaZipConflictError(
                    "Uno de los productos ya no existe o cambió de SKU."
                )
            folder = "images" if row["type"] == "image" else "documents"
            storage_uri = save_product_media_object(
                product,
                folder,
                operation["contents"],
                operation["extension"],
                operation["content_type"],
                safe_filename(row["filename"], "archivo"),
            )
            uploaded_uris.append(storage_uri)
            operation["storage_uri"] = storage_uri

        db.expire_all()
        conflicts = _current_conflicts(db, operations)
        if conflicts:
            raise ProductMediaZipConflictError(" ".join(conflicts))

        for operation in operations:
            row = operation["row"]
            product = db.get(models.Product, row["product_id"])
            totals = product_totals.setdefault(
                product.id,
                {
                    "id": product.id,
                    "sku": product.sku,
                    "name": product.name,
                    "images_added": 0,
                    "documents_added": 0,
                },
            )
            if row["type"] == "image":
                media = build_product_image(
                    product,
                    operation["storage_uri"],
                    sort_order=row["order"] - 1,
                )
                image_count += 1
                totals["images_added"] += 1
                action = "product.image.create"
            else:
                existing_order = (
                    db.query(models.ProductDocument.sort_order)
                    .filter(models.ProductDocument.product_id == product.id)
                    .order_by(models.ProductDocument.sort_order.desc())
                    .first()
                )
                media = build_product_document(
                    product,
                    operation["storage_uri"],
                    original_filename=safe_filename(row["filename"], "ficha.pdf"),
                    size_bytes=len(operation["contents"]),
                    sort_order=(existing_order[0] + 1) if existing_order else 0,
                )
                document_count += 1
                totals["documents_added"] += 1
                action = "product.document.create"
            db.add(media)
            db.flush()
            db.add(
                models.AdminAuditLog(
                    user_id=user.id,
                    action=action,
                    entity_type="product",
                    entity_id=product.id,
                    detail={
                        (
                            "image_id"
                            if row["type"] == "image"
                            else "document_id"
                        ): media.id,
                        "sku": product.sku,
                        "filename": row["filename"],
                        "source": "zip_media_import",
                    },
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        _cleanup_uploaded_objects(uploaded_uris)
        raise

    return {
        "uploaded_images": image_count,
        "uploaded_documents": document_count,
        "affected_products": len(product_totals),
        "products": list(product_totals.values()),
    }
