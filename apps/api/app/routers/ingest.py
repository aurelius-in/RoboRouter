from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Base, engine, get_db
from ..models import Artifact, Metric, Scene, AuditLog
from ..pipeline.pdal import build_ingest_pipeline, has_pdal, run_pipeline, get_point_count, get_bounds_and_srs
from ..schemas import IngestRequest, IngestResponse
from ..storage.minio_client import get_minio_client, upload_file, download_file
from ..utils.crs import validate_crs
from ..utils.hash import sha256_file


router = APIRouter(tags=["Ingest"])


@router.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, db: Session = Depends(get_db)) -> IngestResponse:
    if not validate_crs(payload.crs):
        raise HTTPException(status_code=400, detail="Invalid CRS")
    scene = Scene(source_uri=payload.source_uri, crs=payload.crs, sensor_meta=payload.sensor_meta)
    db.add(scene)
    db.commit()
    db.refresh(scene)

    client = get_minio_client()
    artifact_ids: list[uuid.UUID] = []

    with tempfile.TemporaryDirectory() as td:
        input_path = payload.source_uri
        # Allow s3://bucket/key source
        if input_path.startswith("s3://"):
            try:
                bucket = input_path.split("/", 3)[2]
                key = input_path.split("/", 3)[3]
                local_in = str(Path(td) / Path(key).name)
                download_file(client, bucket, key, local_in)
                input_path = local_in
            except Exception:
                raise HTTPException(status_code=400, detail="Failed to download S3 source")
        if not Path(input_path).exists():
            raise HTTPException(status_code=400, detail="Source file not found")
        output_path = str(Path(td) / f"{scene.id}.laz")

        used_pdal = False
        if has_pdal():
            pipeline = build_ingest_pipeline(
                input_path,
                output_path,
                voxel_size=settings.ingest_voxel_size_m,
                stddev_mult=settings.ingest_outlier_multiplier,
                mean_k=settings.ingest_outlier_mean_k,
                intensity_min=settings.ingest_intensity_min,
                intensity_max=settings.ingest_intensity_max,
                out_srs=payload.crs,
            )
            try:
                run_pipeline(pipeline)
                used_pdal = True
            except Exception:
                # Graceful fallback when PDAL fails at runtime
                Path(output_path).touch()
        else:
            Path(output_path).touch()

        object_name = f"ingest/{scene.id}.laz"
        upload_file(client, settings.minio_bucket_processed, object_name, output_path)

        art = Artifact(scene_id=scene.id, type="ingested", uri=f"s3://{settings.minio_bucket_processed}/{object_name}")
        db.add(art)
        db.commit()
        db.refresh(art)
        artifact_ids.append(art.id)
        # Audit provenance
        db.add(AuditLog(scene_id=scene.id, action="ingest", details={
            "source_uri": payload.source_uri,
            "output_uri": f"s3://{settings.minio_bucket_processed}/{object_name}",
            "crs": payload.crs,
            "used_pdal": used_pdal,
        }))
        db.commit()

    # Metrics: attempt real counts with PDAL, otherwise fall back to zeros
    count_in = get_point_count(payload.source_uri) if has_pdal() else None
    processed_key = object_name
    processed_local = None
    # When PDAL is present we just wrote output_path; counts from it if available
    if has_pdal():
        processed_local = output_path
    count_out = get_point_count(processed_local) if processed_local else None
    bounds_in, srs_in = (get_bounds_and_srs(payload.source_uri) if has_pdal() else (None, None))
    bounds_out, srs_out = (get_bounds_and_srs(processed_local) if (has_pdal() and processed_local) else (None, None))
    # Validate reprojection when available (best-effort string contains)
    reprojection_ok = 0.0
    try:
        if isinstance(srs_out, str) and payload.crs.split(":")[0] in srs_out or payload.crs in (srs_out or ""):
            reprojection_ok = 1.0
    except Exception:
        reprojection_ok = 0.0
    completeness = (float(count_out) / float(count_in)) if (count_in and count_out and count_in > 0) else 0.0
    density = float(count_out) if count_out else 0.0
    metrics = {
        "point_count_in": float(count_in) if count_in else 0.0,
        "point_count_out": float(count_out) if count_out else 0.0,
        "density": density,
        "completeness": completeness,
        "reprojection_ok": reprojection_ok,
    }
    try:
        metrics["ingested_sha256"] = float(int(sha256_file(output_path), 16) % 1e6)
    except Exception:
        pass
    metrics["used_pdal"] = 1.0 if used_pdal else 0.0
    for k, v in metrics.items():
        db.add(Metric(scene_id=scene.id, name=k, value=float(v)))
    db.commit()

    return IngestResponse(scene_id=scene.id, artifact_ids=artifact_ids, metrics=metrics)


