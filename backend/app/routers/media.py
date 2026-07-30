from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.storage import STORAGE_BACKEND

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/{token}")
def get_media(token: str):
    """Serve a locally-stored file after validating its signed, short-lived token.

    Only active when STORAGE_BACKEND=local; the MinIO backend serves files
    directly from its own presigned URLs and never reaches this route.
    """
    if STORAGE_BACKEND != "local":
        raise HTTPException(status_code=404, detail="No encontrado")

    from app.storage_local import verify_token

    try:
        path, download_name = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=404, detail="Enlace inválido o expirado")

    return FileResponse(path, filename=download_name)
