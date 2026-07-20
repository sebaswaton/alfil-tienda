"""Synchronize reviewed official sources and media with PostgreSQL/MinIO.

Run from ``backend`` with ``python -m app.import_official_media``. The command
is idempotent: a PDF is only registered once per product and source URL.
"""

from __future__ import annotations

import argparse
import certifi
import hashlib
import mimetypes
import re
import ssl
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Product, ProductDocument, ProductImage, ProductSource
from app.official_sources import CORRECTIONS, OFFICIAL_SOURCES, RETIRED_SOURCE_URLS
from app.storage import media_uri, put_object, storage_client, MINIO_BUCKET

MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_IMAGE_BYTES = 12 * 1024 * 1024
USER_AGENT = "AlfilCatalogPartner/1.0 (+official product media import)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
OFFICIAL_HOST_SUFFIXES = (
    "hp.com", "www2.hp.com", "hpe.com", "cisco.com", "huawei.com",
    "salicru.com", "canon.com", "broadcom.com", "ibm.com",
)


class OpenGraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "meta" or self.image:
            return
        values = {str(k).lower(): str(v) for k, v in attrs if k and v}
        key = values.get("property", values.get("name", "")).lower()
        if key in {"og:image", "twitter:image", "twitter:image:src"}:
            self.image = values.get("content", "")


def fetch(url: str, limit: int) -> tuple[bytes, str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
            content_length = int(response.headers.get("Content-Length", "0") or 0)
            if content_length > limit:
                raise ValueError(f"archivo supera el límite ({content_length} bytes)")
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("archivo supera el límite")
            return data, response.headers.get_content_type(), response.geturl()
    except Exception as exc:
        # Some legacy manufacturer CDNs present an incomplete certificate chain
        # to Python/OpenSSL while macOS curl validates it correctly. Curl remains
        # strict (no -k) and is only used for reviewed official domains.
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc) or not is_official_url(url):
            raise
        result = subprocess.run(
            [
                "curl", "--fail", "--location", "--silent", "--show-error",
                "--max-time", "45", "--max-filesize", str(limit),
                "--user-agent", USER_AGENT, url,
            ],
            check=True,
            capture_output=True,
        )
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
        else:
            content_type = "text/html"
        return data, content_type, url


def is_official_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES)


def object_exists(object_name: str) -> bool:
    try:
        storage_client.stat_object(MINIO_BUCKET, object_name)
        return True
    except Exception:
        return False


def sync_source(db, product: Product, data: dict) -> ProductSource:
    source = db.scalar(
        select(ProductSource).where(
            ProductSource.product_id == product.id,
            ProductSource.url == data["url"],
        )
    )
    values = {
        "source_type": data.get("source_type", "product_page"),
        "title": data["title"],
        "is_official": True,
        "match_scope": data.get("match_scope", "exact"),
        "notes": data.get("notes", ""),
        "verified_at": datetime.now(),
    }
    if source is None:
        source = ProductSource(product_id=product.id, url=data["url"], **values)
        db.add(source)
    else:
        for key, value in values.items():
            setattr(source, key, value)
    return source


def sync_pdf(db, product: Product, source: dict, cache_dir: Path) -> str:
    url = source["url"]
    fingerprint = hashlib.sha256(url.encode()).hexdigest()[:16]
    filename = f"{product.sku.lower()}-{fingerprint}.pdf"
    object_name = f"products/{product.sku.lower()}/documents/{filename}"
    existing = db.scalar(
        select(ProductDocument).where(
            ProductDocument.product_id == product.id,
            ProductDocument.storage_uri == media_uri(object_name),
        )
    )
    if existing and object_exists(object_name):
        return "existing"

    contents, _, final_url = fetch(url, MAX_PDF_BYTES)
    if not contents.startswith(b"%PDF-"):
        raise ValueError(f"la respuesta no es PDF ({final_url})")
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / filename).write_bytes(contents)
    storage_uri = put_object(
        object_name,
        BytesIO(contents),
        len(contents),
        "application/pdf",
        metadata={"product-sku": product.sku, "official-source": url},
    )
    if existing is None:
        db.add(ProductDocument(
            product_id=product.id,
            title=source["title"],
            document_type=source.get("source_type", "datasheet"),
            storage_uri=storage_uri,
            original_filename=filename,
            mime_type="application/pdf",
            size_bytes=len(contents),
            is_official=True,
            sort_order=10,
        ))
    return "uploaded"


def sync_embedded_pdf_image(db, product: Product, source: dict, cache_dir: Path) -> str:
    """Extract a reviewed product image embedded in an official PDF page."""
    index = int(source["extract_image_index"])
    page = int(source.get("extract_image_page", 1))
    url = source["url"]
    fingerprint = hashlib.sha256(url.encode()).hexdigest()[:16]
    pdf_path = Path("tmp/official-media/pdfs") / f"{product.sku.lower()}-{fingerprint}.pdf"
    if not pdf_path.exists():
        contents, _, _ = fetch(url, MAX_PDF_BYTES)
        if not contents.startswith(b"%PDF-"):
            raise ValueError("la fuente de imagen no es un PDF")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(contents)

    extract_dir = cache_dir / f"{product.sku.lower()}-{fingerprint}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    prefix = extract_dir / "image"
    subprocess.run(
        ["pdfimages", "-f", str(page), "-l", str(page), "-png", str(pdf_path), str(prefix)],
        check=True,
        capture_output=True,
    )
    image_path = extract_dir / f"image-{index:03d}.png"
    if not image_path.exists():
        raise ValueError(f"no existe la imagen embebida {index}")
    raw_contents = image_path.read_bytes()
    if not raw_contents.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("la imagen extraída no es PNG")
    image = Image.open(BytesIO(raw_contents)).convert("RGBA")
    mask_path = extract_dir / f"image-{index + 1:03d}.png"
    alpha_composited = False
    if mask_path.exists():
        mask = Image.open(mask_path)
        if mask.size == image.size and mask.mode in {"1", "L"}:
            image.putalpha(mask.convert("L"))
            alpha_composited = True
    output = BytesIO()
    image.save(output, "PNG", optimize=True)
    contents = output.getvalue()

    object_name = (
        f"products/{product.sku.lower()}/images/"
        f"{product.sku.lower()}-{fingerprint}-pdfimage-{index:03d}.png"
    )
    storage_uri = media_uri(object_name)
    existing = db.scalar(
        select(ProductImage).where(
            ProductImage.product_id == product.id,
            ProductImage.url == storage_uri,
        )
    )
    put_object(
        object_name,
        BytesIO(contents),
        len(contents),
        "image/png",
        metadata={
            "product-sku": product.sku,
            "official-source": url,
            "alpha-composited": str(alpha_composited).lower(),
        },
    )
    if existing is None:
        db.add(ProductImage(
            product_id=product.id,
            url=storage_uri,
            alt=f"{product.name} — imagen referencial oficial",
            sort_order=0,
        ))
    sync_source(db, product, {
        "title": f"Imagen oficial de {product.name}",
        "url": f"{url}#embedded-image-page-{page}-{index}",
        "source_type": "image",
        "match_scope": source.get("match_scope", "exact"),
        "notes": "Imagen técnica extraída de la documentación oficial del fabricante.",
    })
    return "uploaded"


def sync_og_image(db, product: Product, source: dict, cache_dir: Path) -> str:
    page_url = source["url"]
    html, content_type, final_page = fetch(page_url, 4 * 1024 * 1024)
    if content_type not in {"text/html", "application/xhtml+xml"}:
        return "not-html"
    parser = OpenGraphParser()
    parser.feed(html.decode("utf-8", errors="ignore"))
    image_url = urljoin(final_page, parser.image)
    if not image_url or not is_official_url(image_url):
        return "no-official-og-image"
    contents, mime_type, _ = fetch(image_url, MAX_IMAGE_BYTES)
    signatures = {
        "image/jpeg": contents.startswith(b"\xff\xd8\xff"),
        "image/png": contents.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP",
    }
    if not signatures.get(mime_type, False):
        return f"unsupported-image:{mime_type}"
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[mime_type]
    fingerprint = hashlib.sha256(image_url.encode()).hexdigest()[:16]
    filename = f"{product.sku.lower()}-{fingerprint}{extension}"
    object_name = f"products/{product.sku.lower()}/images/{filename}"
    storage_uri = media_uri(object_name)
    existing = db.scalar(
        select(ProductImage).where(
            ProductImage.product_id == product.id,
            ProductImage.url == storage_uri,
        )
    )
    if existing and object_exists(object_name):
        return "existing"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / filename).write_bytes(contents)
    put_object(
        object_name,
        BytesIO(contents),
        len(contents),
        mime_type,
        metadata={"product-sku": product.sku, "official-source": image_url},
    )
    if existing is None:
        db.add(ProductImage(
            product_id=product.id,
            url=storage_uri,
            alt=f"{product.name} — imagen referencial oficial",
            sort_order=10,
        ))
    sync_source(db, product, {
        "title": f"Imagen oficial de {product.name}",
        "url": image_url,
        "source_type": "image",
        "match_scope": source.get("match_scope", "exact"),
        "notes": "Imagen Open Graph obtenida desde la página oficial del fabricante.",
    })
    return "uploaded"


def run(include_images: bool) -> int:
    Base.metadata.create_all(bind=engine)
    cache_root = Path("tmp/official-media")
    failures = 0
    with SessionLocal() as db:
        for retired_url in RETIRED_SOURCE_URLS:
            for retired in db.scalars(
                select(ProductSource).where(ProductSource.url == retired_url)
            ).all():
                db.delete(retired)
        products = {product.sku: product for product in db.scalars(select(Product)).all()}
        for sku, changes in CORRECTIONS.items():
            product = products.get(sku)
            if product:
                for key, value in changes.items():
                    setattr(product, key, value)

        for sku, sources in OFFICIAL_SOURCES.items():
            product = products.get(sku)
            if product is None:
                print(f"SKIP {sku}: no existe en la base de datos")
                continue
            for source in sources:
                if not is_official_url(source["url"]):
                    print(f"ERROR {sku}: dominio no autorizado: {source['url']}")
                    failures += 1
                    continue
                sync_source(db, product, source)
                try:
                    if source.get("source_type") in {"datasheet", "safety_sheet", "manual"}:
                        result = sync_pdf(db, product, source, cache_root / "pdfs")
                        print(f"PDF {result}: {sku} — {source['title']}")
                        if include_images and "extract_image_index" in source:
                            image_result = sync_embedded_pdf_image(
                                db, product, source, cache_root / "extracted"
                            )
                            print(f"IMG {image_result}: {sku} — imagen de ficha técnica")
                    elif include_images and source.get("import_og_image", False):
                        result = sync_og_image(db, product, source, cache_root / "images")
                        print(f"IMG {result}: {sku} — {source['title']}")
                except Exception as exc:
                    print(f"ERROR {sku} — {source['title']}: {exc}")
                    failures += 1
            db.commit()
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", action="store_true", help="Importar imágenes OG oficiales")
    args = parser.parse_args()
    raise SystemExit(1 if run(args.images) else 0)
