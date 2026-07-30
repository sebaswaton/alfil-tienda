"""Import manually reviewed images and secondary PDFs into MinIO/PostgreSQL.

The importer is intentionally conservative: it accepts only registry entries,
validates signatures and image dimensions, records provenance, and never marks
a distributor/mirror document as official.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from PIL import Image
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.import_official_media import (
    MAX_IMAGE_BYTES,
    MAX_PDF_BYTES,
    is_official_url,
    object_exists,
    TLS_CONTEXT,
)
from app.models import Product, ProductDocument, ProductImage, ProductSource
from app.reviewed_media_sources import REVIEWED_MEDIA_SOURCES
from app.storage import STORAGE_BACKEND, media_uri, put_object

REVIEWED_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
)


def fetch_reviewed(url: str, limit: int, referer: str | None = None) -> tuple[bytes, str, str]:
    """Fetch reviewed public media with browser-like negotiation.

    Several distributor CDNs reject non-browser user agents or require the
    product page as referer. Curl is a strict fallback; TLS verification stays
    enabled and content is still validated after download.
    """
    headers = {
        "User-Agent": REVIEWED_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9,en;q=0.7",
    }
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
            content_length = int(response.headers.get("Content-Length", "0") or 0)
            if content_length > limit:
                raise ValueError(f"archivo supera el límite ({content_length} bytes)")
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("archivo supera el límite")
            return data, response.headers.get_content_type(), response.geturl()
    except Exception:
        command = [
            "curl", "--fail", "--location", "--silent", "--show-error",
            "--max-time", "45", "--max-filesize", str(limit),
            "--user-agent", REVIEWED_USER_AGENT,
            "--header", "Accept-Language: es-PE,es;q=0.9,en;q=0.7",
        ]
        if referer:
            command.extend(["--referer", referer])
        command.append(url)
        result = subprocess.run(command, check=True, capture_output=True)
        data = result.stdout
        if len(data) > limit:
            raise ValueError("archivo supera el límite")
        if data.startswith(b"%PDF-"):
            content_type = "application/pdf"
        elif data.startswith(b"\xff\xd8\xff"):
            content_type = "image/jpeg"
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            content_type = "image/png"
        elif len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            content_type = "image/webp"
        elif data.lstrip().startswith((b"{", b"[")):
            content_type = "application/json"
        else:
            content_type = "text/html"
        return data, content_type, url


class MediaPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[str] = []
        self.pdfs: list[str] = []
        self.json_ld: list[str] = []
        self._json_ld = False

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {str(k).lower(): str(v) for k, v in attrs if k and v}
        if tag.lower() == "meta":
            key = values.get("property", values.get("name", "")).lower()
            if key in {"og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"}:
                self.images.append(values.get("content", ""))
        elif tag.lower() == "img":
            for key in ("data-zoom-image", "data-src", "data-original", "src"):
                if values.get(key):
                    self.images.append(values[key])
                    break
        elif tag.lower() == "a" and values.get("href"):
            if ".pdf" in values["href"].lower():
                self.pdfs.append(values["href"])
        elif tag.lower() == "script" and values.get("type", "").lower() == "application/ld+json":
            self._json_ld = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script":
            self._json_ld = False

    def handle_data(self, data: str) -> None:
        if self._json_ld:
            self.json_ld.append(data)


def _json_images(value) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() == "image":
                if isinstance(item, str):
                    found.append(item)
                elif isinstance(item, list):
                    found.extend(str(entry) for entry in item if isinstance(entry, str))
                elif isinstance(item, dict):
                    for image_key in ("url", "contentUrl"):
                        if isinstance(item.get(image_key), str):
                            found.append(item[image_key])
            found.extend(_json_images(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_json_images(item))
    return found


def page_candidates(page_url: str) -> tuple[list[str], list[str]]:
    body, content_type, final_url = fetch_reviewed(page_url, 6 * 1024 * 1024)
    if body.startswith(b"%PDF-"):
        return [], [final_url]
    if "json" in content_type:
        text = body.decode("utf-8", errors="ignore")
        urls = re.findall(r'https?[^"\\ ]+?\.(?:jpe?g|png|webp)(?:\?[^"\\ ]*)?', text, re.I)
        return [url.replace("\\/", "/") for url in urls], []
    if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
        return [], []
    parser = MediaPageParser()
    parser.feed(body.decode("utf-8", errors="ignore"))
    for raw in parser.json_ld:
        try:
            parser.images.extend(_json_images(json.loads(raw)))
        except (json.JSONDecodeError, TypeError):
            continue
    images = list(dict.fromkeys(urljoin(final_url, item) for item in parser.images if item))
    pdfs = list(dict.fromkeys(urljoin(final_url, item) for item in parser.pdfs if item))
    return images, pdfs


def validated_image(candidates: list[str], page_url: str) -> tuple[bytes, str, str, int, int]:
    errors: list[str] = []
    for url in candidates[:30]:
        lower = url.lower()
        if any(token in lower for token in ("logo", "favicon", "sprite", "icon-", "placeholder")):
            continue
        try:
            contents, mime_type, final_url = fetch_reviewed(url, MAX_IMAGE_BYTES, page_url)
            with Image.open(BytesIO(contents)) as image:
                image.verify()
            with Image.open(BytesIO(contents)) as image:
                width, height = image.size
                detected_format = (image.format or "").upper()
            expected = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(detected_format)
            if expected is None or width < 300 or height < 250 or len(contents) < 12_000:
                continue
            return contents, expected, final_url, width, height
        except Exception as exc:
            errors.append(str(exc))
    raise ValueError("no se encontró una imagen de producto válida" + (f": {errors[-1]}" if errors else ""))


def sync_source(db, product: Product, *, title: str, url: str, source_type: str,
                is_official: bool, match_scope: str, notes: str) -> None:
    source = db.scalar(select(ProductSource).where(
        ProductSource.product_id == product.id, ProductSource.url == url
    ))
    values = dict(title=title, source_type=source_type, is_official=is_official,
                  match_scope=match_scope, notes=notes, verified_at=datetime.now())
    if source is None:
        db.add(ProductSource(product_id=product.id, url=url, **values))
    else:
        for key, value in values.items():
            setattr(source, key, value)


def sync_image(db, product: Product, source: dict, cache_dir: Path) -> str:
    page_url = source["image_page_url"]
    candidates = [source["image_url"]] if source.get("image_url") else page_candidates(page_url)[0]
    contents, mime_type, image_url, width, height = validated_image(candidates, page_url)
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[mime_type]
    fingerprint = hashlib.sha256(image_url.encode()).hexdigest()[:16]
    filename = f"{product.sku.lower()}-{fingerprint}{extension}"
    object_name = f"products/{product.sku.lower()}/images/{filename}"
    storage_uri = media_uri(object_name)
    existing = db.scalar(select(ProductImage).where(
        ProductImage.product_id == product.id, ProductImage.url == storage_uri
    ))
    if existing is not None and object_exists(object_name):
        return "existing"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / filename).write_bytes(contents)
    put_object(object_name, BytesIO(contents), len(contents), mime_type, metadata={
        "product-sku": product.sku,
        "source-page": page_url,
        "source-image": image_url,
        "match-scope": source.get("match_scope", "exact"),
    })
    if existing is None:
        db.add(ProductImage(
            product_id=product.id,
            url=storage_uri,
            alt=source["image_title"][:200],
            sort_order=20,
        ))
    official = bool(source.get("image_is_official", is_official_url(page_url)))
    sync_source(
        db, product, title=source["image_title"], url=page_url,
        source_type="image", is_official=official,
        match_scope=source.get("match_scope", "exact"),
        notes=f"Imagen almacenada en MinIO desde la fuente revisada. Archivo original: {image_url}. Dimensiones: {width}x{height}.",
    )
    return "uploaded"


def sync_pdf(db, product: Product, source: dict, cache_dir: Path) -> str:
    source_url = source.get("pdf_url")
    if not source_url:
        _, candidates = page_candidates(source["pdf_page_url"])
        if not candidates:
            raise ValueError("la página revisada no expone un enlace PDF")
        source_url = candidates[0]
    contents, _, final_url = fetch_reviewed(
        source_url, MAX_PDF_BYTES, source.get("pdf_page_url")
    )
    if not contents.startswith(b"%PDF-"):
        raise ValueError(f"la respuesta no es PDF ({final_url})")
    fingerprint = hashlib.sha256(source_url.encode()).hexdigest()[:16]
    filename = f"{product.sku.lower()}-{fingerprint}.pdf"
    object_name = f"products/{product.sku.lower()}/documents/{filename}"
    storage_uri = media_uri(object_name)
    existing = db.scalar(select(ProductDocument).where(
        ProductDocument.product_id == product.id,
        ProductDocument.storage_uri == storage_uri,
    ))
    if existing is not None and object_exists(object_name):
        return "existing"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / filename).write_bytes(contents)
    official = bool(source.get("pdf_is_official", is_official_url(source_url)))
    put_object(object_name, BytesIO(contents), len(contents), "application/pdf", metadata={
        "product-sku": product.sku,
        "source-url": source_url,
        "match-scope": source.get("match_scope", "exact"),
    })
    if existing is None:
        db.add(ProductDocument(
            product_id=product.id,
            title=source["pdf_title"][:200],
            document_type="manual" if "manual" in source["pdf_title"].lower() else "datasheet",
            storage_uri=storage_uri,
            original_filename=filename,
            mime_type="application/pdf",
            size_bytes=len(contents),
            is_official=official,
            sort_order=20,
        ))
    sync_source(
        db, product, title=source["pdf_title"], url=source_url,
        source_type="manual" if "manual" in source["pdf_title"].lower() else "datasheet",
        is_official=official, match_scope=source.get("match_scope", "exact"),
        notes="PDF almacenado en MinIO desde una fuente secundaria revisada." if not official else "PDF oficial almacenado en MinIO.",
    )
    return "uploaded"


def run(*, include_images: bool, include_pdfs: bool) -> int:
    if STORAGE_BACKEND != "minio":
        raise RuntimeError("La importación revisada requiere STORAGE_BACKEND=minio")
    Base.metadata.create_all(bind=engine)
    failures = 0
    cache_root = Path("tmp/reviewed-media")
    with SessionLocal() as db:
        products = {product.sku: product for product in db.scalars(select(Product)).all()}
        for sku, source in REVIEWED_MEDIA_SOURCES.items():
            product = products.get(sku)
            if product is None:
                print(f"SKIP {sku}: no existe en la base de datos")
                continue
            if include_images and source.get("image_page_url"):
                try:
                    print(f"IMG {sync_image(db, product, source, cache_root / 'images')}: {sku}")
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    print(f"ERROR IMG {sku}: {exc}")
                    failures += 1
            if include_pdfs and (source.get("pdf_url") or source.get("pdf_page_url")):
                try:
                    print(f"PDF {sync_pdf(db, product, source, cache_root / 'pdfs')}: {sku}")
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    print(f"ERROR PDF {sku}: {exc}")
                    failures += 1
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-images", action="store_true")
    parser.add_argument("--only-pdfs", action="store_true")
    args = parser.parse_args()
    include_images = not args.only_pdfs
    include_pdfs = not args.only_images
    raise SystemExit(1 if run(include_images=include_images, include_pdfs=include_pdfs) else 0)
