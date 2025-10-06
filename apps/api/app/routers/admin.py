from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal
from ..models import Artifact, Metric, AuditLog, Scene
from ..storage.minio_client import get_minio_client
from ..storage.utils import parse_s3_uri


from ..deps import require_api_key, require_role, require_oidc_user


router = APIRouter(dependencies=[Depends(require_api_key), Depends(require_role("admin")), Depends(require_oidc_user)])


@router.post("/admin/cleanup")
def cleanup_old_records() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=int(settings.retention_days))
        # Find scenes older than cutoff
        scenes = db.execute(select(Scene).where(Scene.created_at < cutoff)).scalars().all()
        # Best-effort S3 cleanup for their artifacts
        try:
            client = get_minio_client()
            for s in scenes:
                arts = db.execute(select(Artifact).where(Artifact.scene_id == s.id)).scalars().all()
                for a in arts:
                    if a.uri and a.uri.startswith("s3://"):
                        try:
                            bucket, key = parse_s3_uri(a.uri)
                            client.remove_object(bucket, key)
                        except Exception:
                            pass
        except Exception:
            pass

        a = db.execute(delete(Artifact).where(Artifact.created_at < cutoff)).rowcount or 0
        m = db.execute(delete(Metric).where(Metric.created_at < cutoff)).rowcount or 0
        l = db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff)).rowcount or 0
        s_del = db.execute(delete(Scene).where(Scene.created_at < cutoff)).rowcount or 0
        db.commit()
        return {"deleted": {"scenes": int(s_del), "artifacts": int(a), "metrics": int(m), "audit_logs": int(l)}, "cutoff": cutoff.isoformat(), "retention_days": settings.retention_days}
    finally:
        db.close()


@router.delete("/admin/cleanup")
def cleanup_old_records_delete() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    return cleanup_old_records()


