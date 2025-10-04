from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional
import mimetypes

from minio import Minio

from ..config import settings


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_file(client: Minio, bucket: str, object_name: str, file_path: str, *, content_type: Optional[str] = None) -> None:
    ensure_bucket(client, bucket)
    guessed, _ = mimetypes.guess_type(object_name)
    ct = content_type or guessed or "application/octet-stream"
    client.fput_object(bucket, object_name, file_path, content_type=ct)


def presigned_get_url(
    client: Minio,
    bucket: str,
    object_name: str,
    expires: int = 3600,
    response_headers: dict | None = None,
) -> str:
    return client.presigned_get_object(
        bucket,
        object_name,
        expires=timedelta(seconds=expires),
        response_headers=response_headers,
    )


