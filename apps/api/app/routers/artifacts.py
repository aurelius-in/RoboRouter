from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact
from ..storage.minio_client import get_minio_client, presigned_get_url
from ..config import settings
from ..storage.utils import parse_s3_uri


router = APIRouter(tags=["Artifacts"])


@router.get("/artifacts/{artifact_id}")
def get_artifact_url(artifact_id: uuid.UUID) -> Dict[str, Any]:
    db: Session = SessionLocal()
    try:
        art = db.get(Artifact, artifact_id)
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")
        client = get_minio_client()
        if art.uri.startswith("s3://"):
            bucket, key = parse_s3_uri(art.uri)
            url = presigned_get_url(client, bucket, key, expires=settings.presign_expires_seconds)
        else:
            url = art.uri
        return {"artifact_id": str(artifact_id), "type": art.type, "url": url, "uri": art.uri}
    finally:
        db.close()


