"""Object storage dispatcher.

Alfil deploys on two independent targets that must keep working from the same
codebase: Docker/MinIO on the vSphere VMs, and local disk on cPanel hosting.
`STORAGE_BACKEND` picks which implementation the rest of the app talks to;
both expose the exact same function signatures so no caller needs to know
which one is active.
"""

import os

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "minio").strip().lower()

if STORAGE_BACKEND == "local":
    from app.storage_local import (
        StorageUnavailableError,
        ensure_bucket,
        media_uri,
        put_object,
        remove_object,
        remove_object_strict,
        resolve_media_url,
    )
elif STORAGE_BACKEND == "minio":
    from app.storage_minio import (
        StorageUnavailableError,
        ensure_bucket,
        media_uri,
        put_object,
        remove_object,
        remove_object_strict,
        resolve_media_url,
    )
else:
    raise RuntimeError(
        f"STORAGE_BACKEND desconocido: {STORAGE_BACKEND!r} (usa 'minio' o 'local')"
    )

__all__ = [
    "STORAGE_BACKEND",
    "StorageUnavailableError",
    "ensure_bucket",
    "media_uri",
    "put_object",
    "remove_object",
    "remove_object_strict",
    "resolve_media_url",
]
