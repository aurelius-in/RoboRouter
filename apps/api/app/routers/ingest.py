from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Any, Dict

from ..config import settings
from ..db import Base, engine, get_db
from ..models import Artifact, Metric, Scene, AuditLog
from ..pipeline.pdal import build_ingest_pipeline, has_pdal, run_pipeline, get_point_count, get_bounds_and_srs
from ..schemas import IngestRequest, IngestResponse
from ..storage.minio_client import get_minio_client, upload_file, upload_file_stream, download_file
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
        # Use streaming for large files
        try:
            if Path(output_path).stat().st_size > 64 * 1024 * 1024:
                upload_file_stream(client, settings.minio_bucket_processed, object_name, output_path)
            else:
                upload_file(client, settings.minio_bucket_processed, object_name, output_path)
        except Exception:
            upload_file(client, settings.minio_bucket_processed, object_name, output_path)

        art = Artifact(scene_id=scene.id, type="ingested", uri=f"s3://{settings.minio_bucket_processed}/{object_name}")
        db.add(art)
        db.commit()
        db.refresh(art)
        artifact_ids.append(art.id)
        # Audit provenance with basic metadata when available
        in_bounds, in_srs = (get_bounds_and_srs(input_path) if has_pdal() else (None, None))
        out_bounds, out_srs = (get_bounds_and_srs(output_path) if has_pdal() else (None, None))
        provenance: Dict[str, Any] = {
            "source_uri": payload.source_uri,
            "output_uri": f"s3://{settings.minio_bucket_processed}/{object_name}",
            "crs": payload.crs,
            "used_pdal": used_pdal,
            "input_bounds": in_bounds,
            "input_srs": in_srs,
            "output_bounds": out_bounds,
            "output_srs": out_srs,
        }
        db.add(AuditLog(scene_id=scene.id, action="ingest", details=provenance))
        db.commit()

    # Metrics: attempt real counts with PDAL, otherwise fall back to zeros
    count_in = get_point_count(payload.source_uri) if has_pdal() else None
    processed_local = output_path if has_pdal() else None
    count_out = get_point_count(processed_local) if processed_local else None
    _, srs_in = (get_bounds_and_srs(payload.source_uri) if has_pdal() else (None, None))
    _, srs_out = (get_bounds_and_srs(processed_local) if (has_pdal() and processed_local) else (None, None))
    # Validate reprojection when available (best-effort)
    reprojection_ok = 0.0
    try:
        if isinstance(srs_out, str) and (payload.crs in srs_out or payload.crs.split(":")[0] in srs_out):
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
        "used_pdal": 1.0 if used_pdal else 0.0,
        "reprojection_ok": reprojection_ok,
    }
    # Hash and dedupe detection (best-effort)
    try:
        ing_sha = int(sha256_file(output_path), 16) % 1_000_000
        metrics["ingested_sha256"] = float(ing_sha)
        existing = db.execute(select(Metric).where(Metric.name == "ingested_sha256", Metric.scene_id != scene.id)).scalars().all()
        hit = any(int(m.value) == ing_sha for m in existing)
        metrics["dedupe_hit"] = 1.0 if hit else 0.0
    except Exception:
        metrics.setdefault("dedupe_hit", 0.0)
    for k, v in metrics.items():
        db.add(Metric(scene_id=scene.id, name=k, value=float(v)))
    db.commit()

    return IngestResponse(scene_id=scene.id, artifact_ids=artifact_ids, metrics=metrics)


@router.post("/ingest/stream", response_model=IngestResponse)
async def ingest_stream(file: UploadFile = File(...), crs: str = "EPSG:3857", db: Session = Depends(get_db)) -> IngestResponse:  # type: ignore[no-untyped-def]
    if not validate_crs(crs):
        raise HTTPException(status_code=400, detail="Invalid CRS")

    scene = Scene(source_uri=f"stream://{file.filename}", crs=crs, sensor_meta={"content_type": file.content_type})
    db.add(scene)
    db.commit()
    db.refresh(scene)

    client = get_minio_client()
    artifact_ids: list[uuid.UUID] = []

    with tempfile.TemporaryDirectory() as td:
        temp_input_path = Path(td) / file.filename
        with open(temp_input_path, "wb") as f:
            while True:
                chunk = await file.read(8 * 1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        output_path = str(Path(td) / f"{scene.id}.laz")

        used_pdal = False
        if has_pdal():
            pipeline = build_ingest_pipeline(
                str(temp_input_path),
                output_path,
                voxel_size=settings.ingest_voxel_size_m,
                stddev_mult=settings.ingest_outlier_multiplier,
                mean_k=settings.ingest_outlier_mean_k,
                intensity_min=settings.ingest_intensity_min,
                intensity_max=settings.ingest_intensity_max,
                out_srs=crs,
            )
            try:
                run_pipeline(pipeline)
                used_pdal = True
            except Exception:
                Path(output_path).touch()
        else:
            Path(output_path).touch()

        object_name = f"ingest/{scene.id}.laz"
        try:
            if Path(output_path).stat().st_size > 64 * 1024 * 1024:
                upload_file_stream(client, settings.minio_bucket_processed, object_name, output_path)
            else:
                upload_file(client, settings.minio_bucket_processed, object_name, output_path)
        except Exception:
            upload_file(client, settings.minio_bucket_processed, object_name, output_path)

        art = Artifact(scene_id=scene.id, type="ingested", uri=f"s3://{settings.minio_bucket_processed}/{object_name}")
        db.add(art)
        db.commit()
        db.refresh(art)
        artifact_ids.append(art.id)

        # Audit provenance
        in_bounds, in_srs = (get_bounds_and_srs(str(temp_input_path)) if has_pdal() else (None, None))
        out_bounds, out_srs = (get_bounds_and_srs(output_path) if has_pdal() else (None, None))
        provenance: Dict[str, Any] = {
            "source_uri": scene.source_uri,
            "original_filename": file.filename,
            "output_uri": f"s3://{settings.minio_bucket_processed}/{object_name}",
            "crs": crs,
            "used_pdal": used_pdal,
            "input_bounds": in_bounds,
            "input_srs": in_srs,
            "output_bounds": out_bounds,
            "output_srs": out_srs,
        }
        db.add(AuditLog(scene_id=scene.id, action="ingest", details=provenance))
        db.commit()

    # Metrics
    count_in = get_point_count(str(temp_input_path)) if has_pdal() else None  # type: ignore[arg-type]
    count_out = get_point_count(output_path) if has_pdal() else None  # type: ignore[arg-type]
    # Reprojection check best-effort
    _, srs_in2 = (get_bounds_and_srs(str(temp_input_path)) if has_pdal() else (None, None))
    _, srs_out2 = (get_bounds_and_srs(output_path) if has_pdal() else (None, None))
    reprojection_ok2 = 0.0
    try:
        if isinstance(srs_out2, str) and (crs in srs_out2 or crs.split(":")[0] in srs_out2):
            reprojection_ok2 = 1.0
    except Exception:
        reprojection_ok2 = 0.0
    completeness = (float(count_out) / float(count_in)) if (count_in and count_out and count_in > 0) else 0.0
    density = float(count_out) if count_out else 0.0
    metrics = {
        "point_count_in": float(count_in) if count_in else 0.0,
        "point_count_out": float(count_out) if count_out else 0.0,
        "density": density,
        "completeness": completeness,
        "used_pdal": 1.0 if used_pdal else 0.0,  # type: ignore[name-defined]
        "reprojection_ok": reprojection_ok2,
    }
    try:
        ing_sha = int(sha256_file(output_path), 16) % 1_000_000
        metrics["ingested_sha256"] = float(ing_sha)
        existing = db.execute(select(Metric).where(Metric.name == "ingested_sha256", Metric.scene_id != scene.id)).scalars().all()
        hit = any(int(m.value) == ing_sha for m in existing)
        metrics["dedupe_hit"] = 1.0 if hit else 0.0
    except Exception:
        metrics.setdefault("dedupe_hit", 0.0)
    for k, v in metrics.items():
        db.add(Metric(scene_id=scene.id, name=k, value=float(v)))
    db.commit()

    return IngestResponse(scene_id=scene.id, artifact_ids=artifact_ids, metrics=metrics)

