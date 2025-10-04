from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Scene, Artifact, Metric


router = APIRouter()


@router.get("/stats")
def get_stats() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scenes = db.execute(select(func.count(Scene.id))).scalar() or 0
        artifacts = db.execute(select(func.count(Artifact.id))).scalar() or 0
        metrics = db.execute(select(func.count(Metric.id))).scalar() or 0
        exports = db.execute(
            select(func.count(Artifact.id)).where(Artifact.type.like("export_%"))
        ).scalar() or 0
        return {
            "scenes": int(scenes),
            "artifacts": int(artifacts),
            "metrics": int(metrics),
            "exports": int(exports),
        }
    finally:
        db.close()


