from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact, AuditLog, Metric, Scene
from ..schemas import SceneDetail, ArtifactDTO, MetricDTO, AuditDTO


router = APIRouter(tags=["Scene"])


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


@router.get("/scenes")
def list_scenes(offset: int = 0, limit: int = 50, q: Optional[str] = None) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    """List recent scenes with basic metadata (paginated)."""
    db: Session = SessionLocal()
    try:
        base = select(Scene)
        if q:
            # Filter by source_uri substring (case-insensitive)
            base = base.where(Scene.source_uri.ilike(f"%{q}%"))  # type: ignore[attr-defined]
        base = base.order_by(Scene.created_at.desc())
        total = db.execute(select(func.count(Scene.id)).select_from(base.subquery())).scalar_one()
        scenes = db.execute(base.offset(max(0, offset)).limit(min(200, max(1, limit)))).scalars().all()
        items = [
            {"id": str(s.id), "source_uri": s.source_uri, "crs": s.crs, "created_at": s.created_at.isoformat()}
            for s in scenes
        ]
        return {"items": items, "offset": offset, "limit": limit, "total": total}
    finally:
        db.close()


@router.delete("/scene/{scene_id}")
def delete_scene(scene_id: uuid.UUID) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        db.delete(scene)
        db.commit()
        return {"deleted": str(scene_id)}
    finally:
        db.close()


@router.get("/scene/{scene_id}/metrics/csv", response_class=PlainTextResponse)
def metrics_csv(scene_id: uuid.UUID) -> str:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        rows = db.execute(select(Metric).where(Metric.scene_id == scene_id).order_by(Metric.created_at.asc())).scalars().all()
        out = ["name,value,created_at"]
        for m in rows:
            out.append(f"{m.name},{float(m.value)},{m.created_at.isoformat()}")
        return "\n".join(out) + "\n"
    finally:
        db.close()


@router.get("/scene/{scene_id}/artifacts")
def list_scene_artifacts(scene_id: uuid.UUID, offset: int = 0, limit: int = 50, type: Optional[str] = None, exports_only: bool = False) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        q = select(Artifact).where(Artifact.scene_id == scene_id)
        if type:
            q = q.where(Artifact.type == type)
        if exports_only:
            from sqlalchemy import literal
            q = q.where(Artifact.type.like("export_%"))
        q = q.order_by(Artifact.created_at.desc())
        total = db.execute(select(func.count(Artifact.id)).select_from(q.subquery())).scalar_one()
        rows = db.execute(q.offset(max(0, offset)).limit(min(200, max(1, limit)))).scalars().all()
        items = [
            {"id": str(a.id), "type": a.type, "uri": a.uri, "created_at": a.created_at.isoformat()} for a in rows
        ]
        return {"items": items, "offset": offset, "limit": limit, "total": total}
    finally:
        db.close()

