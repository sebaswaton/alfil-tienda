"""Export a private MinIO bucket into cPanel's local-media directory layout."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[2]
    load_dotenv(repository / ".env")
    load_dotenv(repository / "backend" / ".env", override=True)

    endpoint = os.environ["MINIO_ENDPOINT"]
    bucket = os.getenv("MINIO_BUCKET", "alfil-catalog")
    access_key = os.getenv("MINIO_ACCESS_KEY") or os.environ["MINIO_ROOT_USER"]
    secret_key = os.getenv("MINIO_SECRET_KEY") or os.environ["MINIO_ROOT_PASSWORD"]
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )

    manifest = []
    for item in client.list_objects(bucket, recursive=True):
        target = (destination / item.object_name).resolve()
        if destination not in target.parents:
            raise RuntimeError(f"Nombre de objeto inseguro: {item.object_name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        client.fget_object(bucket, item.object_name, str(target))
        manifest.append(
            {
                "object": item.object_name,
                "size": target.stat().st_size,
                "sha256": sha256(target),
            }
        )

    manifest.sort(key=lambda row: row["object"])
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exportados {len(manifest)} objetos a {destination}")


if __name__ == "__main__":
    main()
