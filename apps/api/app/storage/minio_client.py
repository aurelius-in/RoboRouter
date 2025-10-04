from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional

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


def upload_file(client: Minio, bucket: str, object_name: str, file_path: str) -> None:
    ensure_bucket(client, bucket)
    client.fput_object(bucket, object_name, file_path)


def presigned_get_url(client: Minio, bucket: str, object_name: str, expires: int = 3600) -> str:
    return client.presigned_get_object(bucket, object_name, expires=timedelta(seconds=expires))


