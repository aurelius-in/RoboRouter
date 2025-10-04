from __future__ import annotations

import tempfile
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact, Metric, Scene
from ..pipeline.registration import register_clouds
from ..storage.minio_client import get_minio_client, upload_file


router = APIRouter()


@router.post("/pipeline/run")
def pipeline_run(scene_id: uuid.UUID, steps: Optional[List[str]] = None, config_overrides: Optional[Dict[str, Any]] = None):  # type: ignore[no-untyped-def]
    steps = steps or ["registration"]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        out: Dict[str, Any] = {"scene_id": str(scene_id), "steps": steps, "artifacts": [], "metrics": {}}

        if "registration" in steps:
            ingest_art = db.execute(
                select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "ingested").order_by(Artifact.created_at.desc())
            ).scalars().first()
            if not ingest_art:
                raise HTTPException(status_code=400, detail="No ingested artifact found for scene")

            client = get_minio_client()
            bucket = ingest_art.uri.split("/")[2] if ingest_art.uri.startswith("s3://") else None
            key = "/".join(ingest_art.uri.split("/")[3:]) if bucket else None

            # In a full impl, download artifact. Here we simulate using a temp path.
            with tempfile.TemporaryDirectory() as td:
                input_path = str((__import__("pathlib").Path(td) / "input.laz"))
                open(input_path, "wb").close()
                aligned_path = str((__import__("pathlib").Path(td) / "aligned.laz"))
                result = register_clouds(input_path, aligned_path)

                aligned_obj = f"registration/aligned_{scene_id}.laz"
                upload_file(client, "roborouter-processed", aligned_obj, result.aligned_path)
                art_aligned = Artifact(scene_id=scene_id, type="aligned", uri=f"s3://roborouter-processed/{aligned_obj}")
                db.add(art_aligned)
                db.add(Metric(scene_id=scene_id, name="rmse", value=float(result.rmse)))
                db.add(Metric(scene_id=scene_id, name="inlier_ratio", value=float(result.inlier_ratio)))

                resid_obj = f"overlays/residuals_{scene_id}.json"
                upload_file(client, "roborouter-processed", resid_obj, result.residuals_path)
                art_resid = Artifact(scene_id=scene_id, type="residuals", uri=f"s3://roborouter-processed/{resid_obj}")
                db.add(art_resid)

                db.commit()
                db.refresh(art_aligned)
                db.refresh(art_resid)
                out["artifacts"].extend([str(art_aligned.id), str(art_resid.id)])
                out["metrics"].update({"rmse": result.rmse, "inlier_ratio": result.inlier_ratio})

        return out
    finally:
        db.close()


