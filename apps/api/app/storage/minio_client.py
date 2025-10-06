from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional
import mimetypes

from minio import Minio
import time

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


def upload_file(client: Minio, bucket: str, object_name: str, file_path: str, *, content_type: Optional[str] = None, max_retries: int = 3) -> None:
    ensure_bucket(client, bucket)
    guessed, _ = mimetypes.guess_type(object_name)
    ct = content_type or guessed or "application/octet-stream"
    attempt = 0
    delay = 0.5
    while True:
        try:
            client.fput_object(bucket, object_name, file_path, content_type=ct)
            return
        except Exception:
            attempt += 1
            if attempt > max_retries:
                raise
            time.sleep(delay)
            delay = min(4.0, delay * 2)


def upload_file_stream(client: Minio, bucket: str, object_name: str, file_path: str, *, content_type: Optional[str] = None, part_size: int = 5 * 1024 * 1024, max_retries: int = 3) -> None:
    ensure_bucket(client, bucket)
    guessed, _ = mimetypes.guess_type(object_name)
    ct = content_type or guessed or "application/octet-stream"
    size = Path(file_path).stat().st_size
    attempt = 0
    delay = 0.5
    while True:
        try:
            with open(file_path, "rb") as data:
                client.put_object(bucket, object_name, data, length=size, part_size=part_size, content_type=ct)
            return
        except Exception:
            attempt += 1
            if attempt > max_retries:
                raise
            time.sleep(delay)
            delay = min(4.0, delay * 2)


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


def download_file(client: Minio, bucket: str, object_name: str, dest_path: str) -> None:
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    client.fget_object(bucket, object_name, dest_path)


