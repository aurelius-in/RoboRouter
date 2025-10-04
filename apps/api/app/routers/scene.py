from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact, AuditLog, Metric, Scene
from ..schemas import SceneDetail, ArtifactDTO, MetricDTO, AuditDTO


router = APIRouter()


@router.get("/scene/{scene_id}", response_model=SceneDetail)
def get_scene(scene_id: uuid.UUID) -> SceneDetail:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        metrics = db.execute(select(Metric).where(Metric.scene_id == scene_id).order_by(Metric.created_at.asc())).scalars().all()
        artifacts = db.execute(select(Artifact).where(Artifact.scene_id == scene_id).order_by(Artifact.created_at.asc())).scalars().all()
        audits = db.execute(select(AuditLog).where(AuditLog.scene_id == scene_id).order_by(AuditLog.created_at.asc())).scalars().all()

        return SceneDetail(
            id=scene.id,
            source_uri=scene.source_uri,
            crs=scene.crs,
            sensor_meta=scene.sensor_meta,
            created_at=scene.created_at.isoformat(),
            metrics=[MetricDTO(name=m.name, value=float(m.value), created_at=m.created_at.isoformat()) for m in metrics],
            artifacts=[ArtifactDTO(id=a.id, type=a.type, uri=a.uri, created_at=a.created_at.isoformat()) for a in artifacts],
            audit=[AuditDTO(id=a.id, action=a.action, details=a.details, created_at=a.created_at.isoformat()) for a in audits],
        )
    finally:
        db.close()


