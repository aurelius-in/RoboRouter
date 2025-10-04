from __future__ import annotations

import tempfile
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact, AuditLog, Scene
from ..policy.opa import evaluate_export_policy
from ..storage.minio_client import get_minio_client, upload_file


router = APIRouter()


@router.post("/export")
def export_artifact(scene_id: uuid.UUID, type: str, crs: str = "EPSG:3857") -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        allowed, reason = evaluate_export_policy({"type": type, "crs": crs, "rounding_mm": 5})
        if not allowed:
            db.add(AuditLog(scene_id=scene_id, action="export_blocked", details={"type": type, "reason": reason}))
            db.commit()
            raise HTTPException(status_code=403, detail=reason)

        # Choose a source artifact to export (prioritize aligned)
        src = db.execute(
            select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "aligned").order_by(Artifact.created_at.desc())
        ).scalars().first()
        if not src:
            src = db.execute(
                select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "ingested").order_by(Artifact.created_at.desc())
            ).scalars().first()
        if not src:
            raise HTTPException(status_code=400, detail="No source artifact available for export")

        # Stub export: create tiny file and upload
        client = get_minio_client()
        with tempfile.TemporaryDirectory() as td:
            out_path = f"{td}/export_{scene_id}.{type}"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"export {type} for scene {scene_id}\n")
            obj = f"exports/{scene_id}.{type}"
            upload_file(client, "roborouter-processed", obj, out_path)

        uri = f"s3://roborouter-processed/{obj}"
        art = Artifact(scene_id=scene_id, type=f"export_{type}", uri=uri)
        db.add(art)
        db.add(AuditLog(scene_id=scene_id, action="export_allowed", details={"type": type, "uri": uri}))
        db.commit()

        return {"scene_id": str(scene_id), "type": type, "uri": uri}
    finally:
        db.close()


