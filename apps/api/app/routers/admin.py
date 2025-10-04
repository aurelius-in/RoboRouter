from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal
from ..models import Artifact, Metric, AuditLog


from ..deps import require_api_key


router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/admin/cleanup")
def cleanup_old_records() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=int(settings.retention_days))
        a = db.execute(delete(Artifact).where(Artifact.created_at < cutoff)).rowcount or 0
        m = db.execute(delete(Metric).where(Metric.created_at < cutoff)).rowcount or 0
        l = db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff)).rowcount or 0
        db.commit()
        return {"deleted": {"artifacts": int(a), "metrics": int(m), "audit_logs": int(l)}, "cutoff": cutoff.isoformat(), "retention_days": settings.retention_days}
    finally:
        db.close()


@router.delete("/admin/cleanup")
def cleanup_old_records_delete() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    return cleanup_old_records()


