import os
import re
import unicodedata
from io import BytesIO
from uuid import uuid4

from app import models
from app.storage import put_object


IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
IMAGE_MAX_BYTES = 10 * 1024 * 1024
PDF_MAX_BYTES = 25 * 1024 * 1024


def safe_filename(filename: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode()
    stem, extension = os.path.splitext(normalized)
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-._") or fallback
    extension = re.sub(r"[^a-zA-Z0-9.]", "", extension.lower())
    return f"{stem[:100]}{extension[:10]}"


def safe_path_segment(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-") or "producto"


def matches_file_signature(media_type: str, content_type: str, contents: bytes) -> bool:
    if media_type == "document":
        return contents.startswith(b"%PDF-")
    if content_type == "image/jpeg":
        return contents.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return contents.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return (
            len(contents) >= 12
            and contents[:4] == b"RIFF"
            and contents[8:12] == b"WEBP"
        )
    return False


def save_storage_object(
    prefix: str,
    contents: bytes,
    extension: str,
    content_type: str,
    metadata: dict[str, str],
) -> str:
    object_name = f"{prefix}/{uuid4().hex}{extension}"
    return put_object(
        object_name,
        BytesIO(contents),
        len(contents),
        content_type,
        metadata=metadata,
    )


def save_product_media_object(
    product: models.Product,
    folder: str,
    contents: bytes,
    extension: str,
    content_type: str,
    original_filename: str,
) -> str:
    return save_storage_object(
        f"products/{safe_path_segment(product.sku)}/{folder}",
        contents,
        extension,
        content_type,
        {
            "original-filename": original_filename,
            "product-sku": product.sku,
        },
    )


def build_product_image(
    product: models.Product,
    storage_uri: str,
    *,
    sort_order: int,
    alt: str | None = None,
    fallback_blank_alt: bool = False,
) -> models.ProductImage:
    resolved_alt = (
        (alt or "").strip() or product.name
        if fallback_blank_alt
        else (alt or product.name).strip()
    )
    return models.ProductImage(
        product_id=product.id,
        url=storage_uri,
        alt=resolved_alt[:200],
        sort_order=sort_order,
    )


def build_product_document(
    product: models.Product,
    storage_uri: str,
    *,
    original_filename: str,
    size_bytes: int,
    title: str = "Ficha técnica",
    document_type: str = "datasheet",
    is_official: bool = False,
    sort_order: int = 0,
) -> models.ProductDocument:
    return models.ProductDocument(
        product_id=product.id,
        title=(title.strip() or "Ficha técnica")[:200],
        document_type=document_type[:40],
        storage_uri=storage_uri,
        original_filename=original_filename,
        mime_type="application/pdf",
        size_bytes=size_bytes,
        is_official=is_official,
        sort_order=sort_order,
    )
