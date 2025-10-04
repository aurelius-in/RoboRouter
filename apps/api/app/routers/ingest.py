from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Base, engine, get_db
from ..models import Artifact, Metric, Scene
from ..pipeline.pdal import build_ingest_pipeline, has_pdal, run_pipeline
from ..schemas import IngestRequest, IngestResponse
from ..storage.minio_client import get_minio_client, upload_file


router = APIRouter()


@router.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, db: Session = Depends(get_db)) -> IngestResponse:
    scene = Scene(source_uri=payload.source_uri, crs=payload.crs, sensor_meta=payload.sensor_meta)
    db.add(scene)
    db.commit()
    db.refresh(scene)

    client = get_minio_client()
    artifact_ids: list[uuid.UUID] = []

    with tempfile.TemporaryDirectory() as td:
        input_path = payload.source_uri  # For now assume local path; S3 support later
        output_path = str(Path(td) / f"{scene.id}.laz")

        if has_pdal():
            pipeline = build_ingest_pipeline(
                input_path,
                output_path,
                voxel_size=0.05,
                stddev_mult=1.0,
                intensity_min=0.0,
                intensity_max=1.0,
            )
            run_pipeline(pipeline)
        else:
            Path(output_path).touch()

        object_name = f"ingest/{scene.id}.laz"
        upload_file(client, settings.minio_bucket_processed, object_name, output_path)

        art = Artifact(scene_id=scene.id, type="ingested", uri=f"s3://{settings.minio_bucket_processed}/{object_name}")
        db.add(art)
        db.commit()
        db.refresh(art)
        artifact_ids.append(art.id)

    # Stub metrics; replace with real counts/density later
    metrics = {"point_count_in": 0.0, "point_count_out": 0.0, "density": 0.0, "completeness": 0.0}
    for k, v in metrics.items():
        db.add(Metric(scene_id=scene.id, name=k, value=float(v)))
    db.commit()

    return IngestResponse(scene_id=scene.id, artifact_ids=artifact_ids, metrics=metrics)


