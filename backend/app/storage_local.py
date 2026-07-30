import base64
import hashlib
import hmac
import json
import logging
import os
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)

LOCAL_MEDIA_ROOT = Path(os.getenv("LOCAL_MEDIA_ROOT", "./media")).resolve()
MEDIA_SIGNING_SECRET = os.getenv(
    "MEDIA_SIGNING_SECRET", "change-this-media-signing-secret"
)
MEDIA_URL_EXPIRY_HOURS = int(os.getenv("MEDIA_URL_EXPIRY_HOURS", "4"))
MEDIA_URL_PREFIX = os.getenv("MEDIA_URL_PREFIX", "/api/media")


class StorageUnavailableError(RuntimeError):
    pass


def ensure_bucket() -> bool:
    """Create the private media root directory when the disk is available."""
    try:
        LOCAL_MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as exc:
        logger.warning("Local media root is not available yet: %s", exc)
        return False


def media_uri(object_name: str, bucket: str | None = None) -> str:
    """Internal URI stored in PostgreSQL; it is never sent directly to browsers."""
    return f"local://{object_name.lstrip('/')}"


def _parse_media_uri(value: str) -> str | None:
    if not value.startswith("local://"):
        return None
    object_name = value[len("local://") :].lstrip("/")
    return object_name or None


def _object_path(object_name: str) -> Path:
    candidate = (LOCAL_MEDIA_ROOT / object_name).resolve()
    if candidate != LOCAL_MEDIA_ROOT and LOCAL_MEDIA_ROOT not in candidate.parents:
        raise ValueError("Ruta de objeto inválida")
    return candidate


def _sign(payload_b64: str) -> str:
    return hmac.new(
        MEDIA_SIGNING_SECRET.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()[:32]


def resolve_media_url(value: str, download_name: str | None = None) -> str:
    """Turn a private local-disk URI into a short-lived, tamper-proof browser URL.

    Legacy MinIO/public URLs are returned unchanged, which makes the storage
    migration incremental.
    """
    object_name = _parse_media_uri(value)
    if not object_name:
        return value

    expires_at = int(time.time()) + MEDIA_URL_EXPIRY_HOURS * 3600
    payload: dict[str, str | int] = {"o": object_name, "e": expires_at}
    if download_name:
        safe_name = download_name.replace('"', "").replace("\r", "").replace("\n", "")
        payload["d"] = safe_name

    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    signature = _sign(payload_b64)
    return f"{MEDIA_URL_PREFIX}/{payload_b64}.{signature}"


def verify_token(token: str) -> tuple[Path, str | None]:
    """Validate a signed media token and return the resolved file path.

    Raises ValueError for any invalid, tampered, expired or missing token/file,
    so callers can uniformly answer with a 404.
    """
    try:
        payload_b64, signature = token.rsplit(".", 1)
    except ValueError as exc:
        raise ValueError("Token inválido") from exc

    if not hmac.compare_digest(signature, _sign(payload_b64)):
        raise ValueError("Firma inválida")

    padding = "=" * (-len(payload_b64) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Token inválido") from exc

    if int(payload["e"]) < int(time.time()):
        raise ValueError("Enlace expirado")

    path = _object_path(payload["o"])
    if not path.is_file():
        raise ValueError("Archivo no encontrado")

    return path, payload.get("d")


def put_object(
    object_name: str,
    data,
    length: int,
    content_type: str,
    metadata: dict[str, str] | None = None,
) -> str:
    if not ensure_bucket():
        raise StorageUnavailableError("No se pudo acceder al almacenamiento local")
    try:
        destination = _object_path(object_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as fh:
            shutil.copyfileobj(data, fh)
    except (OSError, ValueError) as exc:
        raise StorageUnavailableError("No se pudo guardar el archivo en disco") from exc
    return media_uri(object_name)


def remove_object(value: str) -> None:
    object_name = _parse_media_uri(value)
    if not object_name:
        return
    try:
        path = _object_path(object_name)
        path.unlink(missing_ok=True)
    except (OSError, ValueError):
        logger.exception("Could not remove orphaned object %s", value)


def remove_object_strict(value: str) -> bool:
    object_name = _parse_media_uri(value)
    if not object_name:
        return False
    try:
        _object_path(object_name).unlink(missing_ok=True)
    except (OSError, ValueError) as exc:
        raise StorageUnavailableError("No se pudo eliminar el archivo") from exc
    return True
