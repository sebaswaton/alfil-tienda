import logging
import os
from io import BytesIO
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import admin_schemas, models
from app.routers.products import (
    IMAGE_MAX_BYTES,
    IMAGE_TYPES,
    PDF_MAX_BYTES,
    matches_file_signature,
    safe_filename,
    safe_path_segment,
)
from app.services import product_service
from app.storage import (
    StorageUnavailableError,
    put_object,
    remove_object_strict,
    resolve_media_url,
)


logger = logging.getLogger(__name__)


def _images(db: Session, product_id: int) -> list[models.ProductImage]:
    return (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.sort_order, models.ProductImage.id)
        .all()
    )


def _documents(db: Session, product_id: int) -> list[models.ProductDocument]:
    return (
        db.query(models.ProductDocument)
        .filter(models.ProductDocument.product_id == product_id)
        .order_by(models.ProductDocument.sort_order, models.ProductDocument.id)
        .all()
    )


def _image_out(image: models.ProductImage, *, is_primary: bool) -> admin_schemas.AdminProductImageOut:
    return admin_schemas.AdminProductImageOut(
        id=image.id,
        product_id=image.product_id,
        url=resolve_media_url(image.url),
        alt=image.alt,
        sort_order=image.sort_order,
        is_primary=is_primary,
    )


def _document_out(document: models.ProductDocument) -> admin_schemas.AdminProductDocumentOut:
    return admin_schemas.AdminProductDocumentOut(
        id=document.id,
        product_id=document.product_id,
        title=document.title,
        document_type=document.document_type,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        size_bytes=document.size_bytes,
        is_official=document.is_official,
        sort_order=document.sort_order,
        created_at=document.created_at,
        download_url=resolve_media_url(document.storage_uri, document.original_filename),
    )


def _normalize_order(items) -> None:
    for index, item in enumerate(items):
        item.sort_order = index


def _get_image(db: Session, product_id: int, image_id: int) -> models.ProductImage:
    product_service.get_product(db, product_id)
    image = (
        db.query(models.ProductImage)
        .filter(
            models.ProductImage.id == image_id,
            models.ProductImage.product_id == product_id,
        )
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return image


def _get_document(db: Session, product_id: int, document_id: int) -> models.ProductDocument:
    product_service.get_product(db, product_id)
    document = (
        db.query(models.ProductDocument)
        .filter(
            models.ProductDocument.id == document_id,
            models.ProductDocument.product_id == product_id,
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return document


async def _read_upload(file: UploadFile, media_type: str):
    original_name = safe_filename(file.filename or "archivo", "archivo")
    extension = os.path.splitext(original_name)[1].lower()
    content_type = (file.content_type or "").lower()

    if media_type == "image":
        expected_extension = IMAGE_TYPES.get(content_type)
        if not expected_extension or extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="La imagen debe ser JPG, PNG o WebP",
            )
        max_bytes = IMAGE_MAX_BYTES
        final_extension = expected_extension
    else:
        if content_type != "application/pdf" or extension != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="El documento debe ser un archivo PDF",
            )
        max_bytes = PDF_MAX_BYTES
        final_extension = ".pdf"

    contents = await file.read(max_bytes + 1)
    await file.close()
    if len(contents) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {limit_mb} MB",
        )
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if not matches_file_signature(media_type, content_type, contents):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="El contenido del archivo no coincide con su formato declarado",
        )
    return contents, original_name, content_type, final_extension


def _store(product: models.Product, folder: str, extension: str, contents: bytes, content_type: str, original_name: str) -> str:
    object_name = (
        f"products/{safe_path_segment(product.sku)}/{folder}/"
        f"{uuid4().hex}{extension}"
    )
    try:
        return put_object(
            object_name,
            BytesIO(contents),
            len(contents),
            content_type,
            metadata={"original-filename": original_name, "product-sku": product.sku},
        )
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _store_taxonomy_asset(
    resource: str,
    item_id: int,
    extension: str,
    contents: bytes,
    content_type: str,
    original_name: str,
) -> str:
    object_name = f"{resource}/{item_id}/{uuid4().hex}{extension}"
    try:
        return put_object(
            object_name,
            BytesIO(contents),
            len(contents),
            content_type,
            metadata={
                "original-filename": original_name,
                "resource": resource,
                "resource-id": str(item_id),
            },
        )
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _discard_new_object(storage_uri: str) -> None:
    try:
        remove_object_strict(storage_uri)
    except StorageUnavailableError:
        logger.exception("No se pudo compensar el objeto nuevo %s", storage_uri)


async def replace_taxonomy_asset(
    db: Session,
    item,
    *,
    attribute: str,
    resource: str,
    file: UploadFile,
) -> None:
    contents, original_name, content_type, extension = await _read_upload(file, "image")
    new_uri = _store_taxonomy_asset(
        resource,
        item.id,
        extension,
        contents,
        content_type,
        original_name,
    )
    old_uri = getattr(item, attribute)
    setattr(item, attribute, new_uri)
    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        _discard_new_object(new_uri)
        raise

    try:
        remove_object_strict(old_uri)
    except StorageUnavailableError as exc:
        setattr(item, attribute, old_uri)
        db.commit()
        _discard_new_object(new_uri)
        raise HTTPException(
            status_code=503,
            detail="No se pudo reemplazar el archivo; se conservó el anterior",
        ) from exc


def delete_taxonomy_asset(db: Session, item, *, attribute: str) -> None:
    old_uri = getattr(item, attribute)
    if not old_uri:
        raise HTTPException(status_code=404, detail="El archivo no existe")

    setattr(item, attribute, "")
    db.commit()
    db.refresh(item)
    try:
        remove_object_strict(old_uri)
    except StorageUnavailableError as exc:
        setattr(item, attribute, old_uri)
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="No se pudo eliminar el archivo; se restauró el registro",
        ) from exc


def list_images(db: Session, product_id: int):
    product_service.get_product(db, product_id)
    images = _images(db, product_id)
    return [_image_out(image, is_primary=index == 0) for index, image in enumerate(images)]


async def upload_image(
    db: Session,
    product_id: int,
    file: UploadFile,
    *,
    alt: str,
    is_primary: bool,
):
    product = product_service.get_product(db, product_id)
    contents, original_name, content_type, extension = await _read_upload(file, "image")
    storage_uri = _store(
        product, "images", extension, contents, content_type, original_name
    )
    existing = _images(db, product_id)
    image = models.ProductImage(
        product_id=product.id,
        url=storage_uri,
        alt=(alt.strip() or product.name)[:200],
        sort_order=len(existing),
    )
    db.add(image)
    try:
        db.flush()
        _normalize_order(([image] + existing) if is_primary else (existing + [image]))
        db.commit()
        db.refresh(image)
    except Exception:
        db.rollback()
        _discard_new_object(storage_uri)
        raise
    return _image_out(image, is_primary=is_primary or not existing)


def update_image(
    db: Session,
    product_id: int,
    image_id: int,
    payload: admin_schemas.AdminProductImageUpdate,
):
    image = _get_image(db, product_id, image_id)
    values = payload.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=422, detail="Debes enviar al menos un campo")
    if "alt" in values:
        image.alt = (values["alt"] or "").strip()
    if values.get("is_primary"):
        images = _images(db, product_id)
        _normalize_order([image] + [item for item in images if item.id != image.id])
    db.commit()
    db.refresh(image)
    return _image_out(image, is_primary=_images(db, product_id)[0].id == image.id)


async def replace_image(db: Session, product_id: int, image_id: int, file: UploadFile):
    image = _get_image(db, product_id, image_id)
    product = product_service.get_product(db, product_id)
    contents, original_name, content_type, extension = await _read_upload(file, "image")
    new_uri = _store(product, "images", extension, contents, content_type, original_name)
    old_uri = image.url
    image.url = new_uri
    try:
        db.commit()
        db.refresh(image)
    except Exception:
        db.rollback()
        _discard_new_object(new_uri)
        raise

    try:
        remove_object_strict(old_uri)
    except StorageUnavailableError as exc:
        image.url = old_uri
        db.commit()
        _discard_new_object(new_uri)
        raise HTTPException(
            status_code=503,
            detail="No se pudo reemplazar la imagen; se conservó el archivo anterior",
        ) from exc
    return _image_out(image, is_primary=_images(db, product_id)[0].id == image.id)


def reorder_images(db: Session, product_id: int, ordered_ids: list[int]):
    product_service.get_product(db, product_id)
    images = _images(db, product_id)
    by_id = {image.id: image for image in images}
    if set(ordered_ids) != set(by_id):
        raise HTTPException(
            status_code=422,
            detail="El orden debe incluir exactamente todas las imágenes del producto",
        )
    ordered = [by_id[image_id] for image_id in ordered_ids]
    _normalize_order(ordered)
    db.commit()
    return [_image_out(image, is_primary=index == 0) for index, image in enumerate(ordered)]


def delete_image(db: Session, product_id: int, image_id: int) -> None:
    image = _get_image(db, product_id, image_id)
    snapshot = {
        "id": image.id,
        "product_id": image.product_id,
        "url": image.url,
        "alt": image.alt,
        "sort_order": image.sort_order,
    }
    previous_orders = {item.id: item.sort_order for item in _images(db, product_id)}
    db.delete(image)
    db.flush()
    _normalize_order(_images(db, product_id))
    db.commit()
    try:
        remove_object_strict(snapshot["url"])
    except StorageUnavailableError as exc:
        restored = models.ProductImage(**snapshot)
        db.add(restored)
        db.flush()
        for item in _images(db, product_id):
            item.sort_order = previous_orders[item.id]
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="No se pudo eliminar la imagen; se restauró el registro",
        ) from exc


def list_documents(db: Session, product_id: int):
    product_service.get_product(db, product_id)
    return [_document_out(document) for document in _documents(db, product_id)]


async def upload_document(
    db: Session,
    product_id: int,
    file: UploadFile,
    *,
    title: str,
    document_type: str,
    is_official: bool,
):
    product = product_service.get_product(db, product_id)
    contents, original_name, content_type, extension = await _read_upload(file, "document")
    storage_uri = _store(
        product, "documents", extension, contents, content_type, original_name
    )
    existing = _documents(db, product_id)
    document = models.ProductDocument(
        product_id=product.id,
        title=(title.strip() or "Ficha técnica")[:200],
        document_type=document_type,
        storage_uri=storage_uri,
        original_filename=original_name,
        mime_type=content_type,
        size_bytes=len(contents),
        is_official=is_official,
        sort_order=len(existing),
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        _discard_new_object(storage_uri)
        raise
    return _document_out(document)


async def replace_document(
    db: Session,
    product_id: int,
    document_id: int,
    file: UploadFile,
):
    document = _get_document(db, product_id, document_id)
    product = product_service.get_product(db, product_id)
    contents, original_name, content_type, extension = await _read_upload(file, "document")
    new_uri = _store(
        product, "documents", extension, contents, content_type, original_name
    )
    snapshot = {
        "storage_uri": document.storage_uri,
        "original_filename": document.original_filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
    }
    document.storage_uri = new_uri
    document.original_filename = original_name
    document.mime_type = content_type
    document.size_bytes = len(contents)
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        _discard_new_object(new_uri)
        raise

    try:
        remove_object_strict(snapshot["storage_uri"])
    except StorageUnavailableError as exc:
        for field, value in snapshot.items():
            setattr(document, field, value)
        db.commit()
        _discard_new_object(new_uri)
        raise HTTPException(
            status_code=503,
            detail="No se pudo reemplazar el documento; se conservó el archivo anterior",
        ) from exc
    return _document_out(document)


def delete_document(db: Session, product_id: int, document_id: int) -> None:
    document = _get_document(db, product_id, document_id)
    snapshot = {
        "id": document.id,
        "product_id": document.product_id,
        "title": document.title,
        "document_type": document.document_type,
        "storage_uri": document.storage_uri,
        "original_filename": document.original_filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "is_official": document.is_official,
        "sort_order": document.sort_order,
        "created_at": document.created_at,
    }
    db.delete(document)
    db.commit()
    try:
        remove_object_strict(snapshot["storage_uri"])
    except StorageUnavailableError as exc:
        db.add(models.ProductDocument(**snapshot))
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="No se pudo eliminar el documento; se restauró el registro",
        ) from exc
