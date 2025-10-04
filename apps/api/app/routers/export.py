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
from ..exporters.exporters import export_potree, export_laz, export_gltf, export_webm
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

        # Export using tool-specific handlers (with fallbacks)
        client = get_minio_client()
        with tempfile.TemporaryDirectory() as td:
            # For now, simulate having a LAZ input by creating a tiny placeholder
            input_laz = f"{td}/input_{scene_id}.laz"
            with open(input_laz, "w", encoding="utf-8") as f:
                f.write("input placeholder\n")

            if type.lower() == "potree":
                out_dir = f"{td}/potree_{scene_id}"
                export_potree(input_laz, out_dir)
                obj = f"exports/potree/{scene_id}"
                # Upload directory contents (placeholder file) – here we upload a marker
                marker = f"{out_dir}/README.txt"
                upload_file(client, "roborouter-processed", f"{obj}/README.txt", marker)
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "laz":
                out_laz = f"{td}/{scene_id}.laz"
                export_laz(input_laz, out_laz)
                obj = f"exports/laz/{scene_id}.laz"
                upload_file(client, "roborouter-processed", obj, out_laz)
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "gltf":
                out_gltf = f"{td}/{scene_id}.gltf"
                export_gltf(input_laz, out_gltf)
                obj = f"exports/gltf/{scene_id}.gltf"
                upload_file(client, "roborouter-processed", obj, out_gltf)
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "webm":
                out_webm = f"{td}/{scene_id}.webm"
                export_webm(input_laz, out_webm)
                obj = f"exports/webm/{scene_id}.webm"
                upload_file(client, "roborouter-processed", obj, out_webm)
                uri = f"s3://roborouter-processed/{obj}"
            else:
                raise HTTPException(status_code=400, detail="Unsupported export type")
        art = Artifact(scene_id=scene_id, type=f"export_{type}", uri=uri)
        db.add(art)
        db.add(AuditLog(scene_id=scene_id, action="export_allowed", details={"type": type, "uri": uri}))
        db.commit()

        return {"scene_id": str(scene_id), "type": type, "uri": uri}
    finally:
        db.close()


