from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import time
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact
from ..storage.minio_client import get_minio_client, presigned_get_url
from ..config import settings
from ..storage.utils import parse_s3_uri
from sqlalchemy import select


router = APIRouter(tags=["Artifacts"])


@router.get("/artifacts/{artifact_id}")
def get_artifact_url(artifact_id: uuid.UUID, filename: str | None = None, as_attachment: bool = False) -> Dict[str, Any]:
    db: Session = SessionLocal()
    try:
        art = db.get(Artifact, artifact_id)
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")
        client = get_minio_client()
        size_bytes: int | None = None
        content_type: str | None = None
        last_modified: float | None = None
        if art.uri.startswith("s3://"):
            bucket, key = parse_s3_uri(art.uri)
            # Simple in-process cache for presigned URLs
            url = _get_cached_url(str(artifact_id))
            if not url:
                headers = None
                if filename or as_attachment:
                    disp = f"attachment; filename=\"{filename or key.split('/')[-1]}\"" if as_attachment else f"inline; filename=\"{filename or key.split('/')[-1]}\""
                    headers = {"response-content-disposition": disp}
                url = presigned_get_url(client, bucket, key, expires=settings.presign_expires_seconds, response_headers=headers)
                _cache_url(str(artifact_id), url, settings.presign_expires_seconds)
            expires_in = _ttl_remaining(str(artifact_id))
            try:
                stat = client.stat_object(bucket, key)
                size_bytes = getattr(stat, "size", None)
                content_type = getattr(stat, "content_type", None)
                # stat.last_modified is datetime
                lm = getattr(stat, "last_modified", None)
                if lm is not None:
                    last_modified = lm.timestamp()
                etag = getattr(stat, "etag", None)
            except Exception:
                etag = None
        else:
            url = art.uri
            expires_in = None
        return {
            "artifact_id": str(artifact_id),
            "type": art.type,
            "url": url,
            "uri": art.uri,
            "expires_in_seconds": expires_in,
            "size_bytes": size_bytes,
            "content_type": content_type,
            "last_modified": last_modified,
            "etag": etag if 'etag' in locals() else None,
        }
    finally:
        db.close()


_URL_CACHE: Dict[str, tuple[str, float]] = {}


def _cache_url(artifact_id: str, url: str, ttl_s: int) -> None:
    _URL_CACHE[artifact_id] = (url, time.time() + float(ttl_s) * 0.9)


def _get_cached_url(artifact_id: str) -> str | None:
    rec = _URL_CACHE.get(artifact_id)
    if not rec:
        return None
    url, expires_at = rec
    if time.time() >= expires_at:
        _URL_CACHE.pop(artifact_id, None)
        return None
    return url


def _ttl_remaining(artifact_id: str) -> int | None:
    rec = _URL_CACHE.get(artifact_id)
    if not rec:
        return None
    url, expires_at = rec
    import time as _t
    left = int(max(0, expires_at - _t.time()))
    return left


@router.get("/artifacts/latest")
def get_latest_artifact(scene_id: uuid.UUID, type: str) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        row = db.execute(
            select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == type).order_by(Artifact.created_at.desc())
        ).scalars().first()
        if not row:
            raise HTTPException(status_code=404, detail="Artifact not found")
        # Reuse existing handler
        return get_artifact_url(row.id)
    finally:
        db.close()


@router.post("/artifacts/refresh/{artifact_id}")
def refresh_artifact_url(artifact_id: uuid.UUID) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    """Invalidate local presign cache and return a fresh URL."""
    _URL_CACHE.pop(str(artifact_id), None)
    return get_artifact_url(artifact_id)


@router.get("/artifacts/{artifact_id}/csv", response_class=PlainTextResponse)
def artifact_as_csv(artifact_id: uuid.UUID) -> str:  # type: ignore[no-untyped-def]
    """For change_delta artifacts containing a JSON object, return CSV of key,count."""
    db: Session = SessionLocal()
    try:
        art = db.get(Artifact, artifact_id)
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")
        if art.type != "change_delta":
            raise HTTPException(status_code=400, detail="CSV view only supported for change_delta")
        # Fetch JSON over presigned URL
        info = get_artifact_url(artifact_id)
        import json, urllib.request
        with urllib.request.urlopen(info["url"]) as resp:  # type: ignore
            text = resp.read().decode("utf-8")
        try:
            data = json.loads(text)
        except Exception:
            raise HTTPException(status_code=400, detail="Artifact is not valid JSON")
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Unexpected JSON format")
        rows = ["type,count"]
        for k, v in data.items():
            rows.append(f"{k},{v}")
        return "\n".join(rows) + "\n"
    finally:
        db.close()

