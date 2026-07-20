import logging
import os
from datetime import timedelta
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error


logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", MINIO_ENDPOINT)
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "change-this-minio-user")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "change-this-minio-password")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "alfil-catalog")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_PUBLIC_SECURE = os.getenv(
    "MINIO_PUBLIC_SECURE", str(MINIO_SECURE)
).lower() == "true"
MEDIA_URL_EXPIRY_HOURS = int(os.getenv("MEDIA_URL_EXPIRY_HOURS", "4"))


class StorageUnavailableError(RuntimeError):
    pass


def _client(endpoint: str, secure: bool) -> Minio:
    return Minio(
        endpoint,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=secure,
        region=MINIO_REGION,
    )


storage_client = _client(MINIO_ENDPOINT, MINIO_SECURE)
public_signing_client = _client(MINIO_PUBLIC_ENDPOINT, MINIO_PUBLIC_SECURE)


def ensure_bucket() -> bool:
    """Create the private catalog bucket when MinIO is available."""
    try:
        if not storage_client.bucket_exists(MINIO_BUCKET):
            storage_client.make_bucket(MINIO_BUCKET)
        return True
    except (S3Error, OSError, ValueError) as exc:
        logger.warning("MinIO is not available yet: %s", exc)
        return False


def media_uri(object_name: str, bucket: str = MINIO_BUCKET) -> str:
    """Internal URI stored in PostgreSQL; it is never sent directly to browsers."""
    return f"minio://{bucket}/{object_name.lstrip('/')}"


def _parse_media_uri(value: str) -> tuple[str, str] | None:
    parsed = urlparse(value)
    if parsed.scheme != "minio" or not parsed.netloc or not parsed.path.lstrip("/"):
        return None
    return parsed.netloc, parsed.path.lstrip("/")


def resolve_media_url(value: str, download_name: str | None = None) -> str:
    """Turn a private MinIO URI into a short-lived browser URL.

    Legacy public and local URLs are returned unchanged, which makes the storage
    migration incremental.
    """
    location = _parse_media_uri(value)
    if not location:
        return value

    bucket, object_name = location
    response_headers = None
    if download_name:
        safe_name = download_name.replace('"', "").replace("\r", "").replace("\n", "")
        response_headers = {
            "response-content-disposition": f'attachment; filename="{safe_name}"'
        }

    return public_signing_client.presigned_get_object(
        bucket,
        object_name,
        expires=timedelta(hours=MEDIA_URL_EXPIRY_HOURS),
        response_headers=response_headers,
    )


def put_object(
    object_name: str,
    data,
    length: int,
    content_type: str,
    metadata: dict[str, str] | None = None,
) -> str:
    if not ensure_bucket():
        raise StorageUnavailableError("No se pudo conectar con MinIO")
    try:
        storage_client.put_object(
            MINIO_BUCKET,
            object_name,
            data,
            length,
            content_type=content_type,
            metadata=metadata,
        )
    except (S3Error, OSError, ValueError) as exc:
        raise StorageUnavailableError("No se pudo guardar el archivo en MinIO") from exc
    return media_uri(object_name)


def remove_object(value: str) -> None:
    location = _parse_media_uri(value)
    if not location:
        return
    bucket, object_name = location
    try:
        storage_client.remove_object(bucket, object_name)
    except (S3Error, OSError, ValueError):
        logger.exception("Could not remove orphaned object %s", value)
