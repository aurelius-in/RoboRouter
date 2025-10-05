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
from ..pipeline.segmentation import run_segmentation
from ..pipeline.change_detection import run_change_detection
from ..storage.minio_client import get_minio_client, upload_file
from ..observability import REQUEST_COUNT, REQUEST_LATENCY, SERVICE_NAME
import time
from ..utils.hash import sha256_file
from ..mlflow_stub import log_metrics as mlflow_log_metrics
from ..utils.thresholds import load_thresholds
from ..orchestrator.stub import OrchestratorStub
from ..orchestrator.ray_orch import RayOrchestrator
from ..config import settings
from ..utils.settings_override import temporary_settings


router = APIRouter(tags=["Pipeline"])


@router.post("/pipeline/run")
def pipeline_run(scene_id: uuid.UUID, steps: Optional[List[str]] = None, config_overrides: Optional[Dict[str, Any]] = None):  # type: ignore[no-untyped-def]
    steps = steps or ["registration"]
    db: Session = SessionLocal()
    try:
        orch = RayOrchestrator() if settings.orchestrator == "ray" else OrchestratorStub()
        with __import__('contextlib').ExitStack() as _:
            # Record stub plan (no behavior change)
            out: Dict[str, Any] = {"scene_id": str(scene_id), "steps": steps, "artifacts": [], "metrics": {}, "orchestrator": orch.run(str(scene_id), steps)}
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        # Apply config overrides temporarily
        if config_overrides:
            with temporary_settings(settings, config_overrides):
                thr = load_thresholds()
        else:
            thr = load_thresholds()

        # out already declared with orchestrator stub
        

        if "registration" in steps:
            _t0 = time.time()
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
                try:
                    db.add(Metric(scene_id=scene_id, name="aligned_sha256", value=float(int(sha256_file(result.aligned_path), 16) % 1e6)))
                except Exception:
                    pass

                resid_obj = f"overlays/residuals_{scene_id}.json"
                upload_file(client, "roborouter-processed", resid_obj, result.residuals_path)
                art_resid = Artifact(scene_id=scene_id, type="residuals", uri=f"s3://roborouter-processed/{resid_obj}")
                db.add(art_resid)

                db.commit()
                db.refresh(art_aligned)
                db.refresh(art_resid)
                out["artifacts"].extend([str(art_aligned.id), str(art_resid.id)])
                out["metrics"].update({"rmse": result.rmse, "inlier_ratio": result.inlier_ratio})
            dur = time.time() - _t0
            REQUEST_COUNT.labels(SERVICE_NAME, "PIPELINE", "registration", "200").inc()
            REQUEST_LATENCY.labels(SERVICE_NAME, "PIPELINE", "registration").observe(dur)
            out["metrics"]["registration_ms"] = round(dur * 1000.0, 2)
            try:
                mlflow_log_metrics({"registration_ms": out["metrics"]["registration_ms"], "rmse": float(out["metrics"]["rmse"]), "inlier_ratio": float(out["metrics"]["inlier_ratio"])})
            except Exception:
                pass
            # Pass/fail gate
            try:
                out["metrics"]["registration_pass"] = float((out["metrics"]["rmse"] <= thr.get("rmse_max", 0.10)) and (out["metrics"]["inlier_ratio"] >= 0.70))
            except Exception:
                out["metrics"]["registration_pass"] = 0.0

        if "segmentation" in steps:
            _t0 = time.time()
            # Prefer aligned artifact if available
            aligned_art = db.execute(
                select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "aligned").order_by(Artifact.created_at.desc())
            ).scalars().first()
            source_art = aligned_art
            if not source_art:
                source_art = db.execute(
                    select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "ingested").order_by(Artifact.created_at.desc())
                ).scalars().first()
            if not source_art:
                raise HTTPException(status_code=400, detail="No input artifact found for segmentation")

            client = get_minio_client()
            with tempfile.TemporaryDirectory() as td:
                # Simulate segmentation with temp input
                input_path = str((__import__("pathlib").Path(td) / "input_aligned.laz"))
                open(input_path, "wb").close()
                seg_out = run_segmentation(input_path, td)

                classes_obj = f"segmentation/classes_{scene_id}.json"
                conf_obj = f"segmentation/confidence_{scene_id}.json"
                ent_obj = f"segmentation/entropy_{scene_id}.json"
                upload_file(client, "roborouter-processed", classes_obj, seg_out["classes_path"])  # type: ignore[index]
                upload_file(client, "roborouter-processed", conf_obj, seg_out["confidence_path"])  # type: ignore[index]
                upload_file(client, "roborouter-processed", ent_obj, seg_out["entropy_path"])  # type: ignore[index]

                art_classes = Artifact(scene_id=scene_id, type="segmentation_classes", uri=f"s3://roborouter-processed/{classes_obj}")
                art_conf = Artifact(scene_id=scene_id, type="segmentation_confidence", uri=f"s3://roborouter-processed/{conf_obj}")
                art_ent = Artifact(scene_id=scene_id, type="segmentation_entropy", uri=f"s3://roborouter-processed/{ent_obj}")
                db.add_all([art_classes, art_conf, art_ent])
                db.add(Metric(scene_id=scene_id, name="miou", value=float(seg_out["miou"])) )  # type: ignore[index]
                if "seg_used_minkowski" in seg_out:
                    db.add(Metric(scene_id=scene_id, name="seg_used_minkowski", value=float(seg_out["seg_used_minkowski"])) )  # type: ignore[index]
                if "seg_used_cuda" in seg_out:
                    db.add(Metric(scene_id=scene_id, name="seg_used_cuda", value=float(seg_out["seg_used_cuda"])) )  # type: ignore[index]
                db.commit()
                for a in (art_classes, art_conf, art_ent):
                    db.refresh(a)
                    out["artifacts"].append(str(a.id))
                out["metrics"]["miou"] = float(seg_out["miou"])  # type: ignore[index]
            dur = time.time() - _t0
            REQUEST_COUNT.labels(SERVICE_NAME, "PIPELINE", "segmentation", "200").inc()
            REQUEST_LATENCY.labels(SERVICE_NAME, "PIPELINE", "segmentation").observe(dur)
            out["metrics"]["segmentation_ms"] = round(dur * 1000.0, 2)
            try:
                mlflow_log_metrics({"segmentation_ms": out["metrics"]["segmentation_ms"], "miou": float(out["metrics"]["miou"])})
            except Exception:
                pass
            # Pass/fail gate
            try:
                out["metrics"]["segmentation_pass"] = float(out["metrics"].get("miou", 0.0) >= thr.get("miou_min", 0.70))
            except Exception:
                out["metrics"]["segmentation_pass"] = 0.0

        if "change_detection" in steps:
            _t0 = time.time()
            # Choose baseline (ingested) and current (aligned if available, else ingested)
            baseline_art = db.execute(
                select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "ingested").order_by(Artifact.created_at.asc())
            ).scalars().first()
            current_art = db.execute(
                select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "aligned").order_by(Artifact.created_at.desc())
            ).scalars().first()
            if not current_art:
                current_art = db.execute(
                    select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "ingested").order_by(Artifact.created_at.desc())
                ).scalars().first()

            if not baseline_art or not current_art:
                raise HTTPException(status_code=400, detail="No suitable baseline/current artifacts for change detection")

            client = get_minio_client()
            with tempfile.TemporaryDirectory() as td:
                # Simulate change detection with temp inputs
                base_path = str((__import__("pathlib").Path(td) / "baseline.laz"))
                curr_path = str((__import__("pathlib").Path(td) / "current.laz"))
                open(base_path, "wb").close()
                open(curr_path, "wb").close()
                cd_out = run_change_detection(base_path, curr_path, td)

                mask_obj = f"change/mask_{scene_id}.json"
                delta_obj = f"change/delta_{scene_id}.json"
                try:
                    upload_file(client, "roborouter-processed", mask_obj, cd_out["change_mask_path"])  # type: ignore[index]
                    upload_file(client, "roborouter-processed", delta_obj, cd_out["delta_table_path"])  # type: ignore[index]
                except Exception as exc:  # noqa: BLE001
                    # Log and proceed to record metrics even if uploads fail
                    import logging
                    logging.getLogger(__name__).exception("Upload failed: %s", exc)

                art_mask = Artifact(scene_id=scene_id, type="change_mask", uri=f"s3://roborouter-processed/{mask_obj}")
                art_delta = Artifact(scene_id=scene_id, type="change_delta", uri=f"s3://roborouter-processed/{delta_obj}")
                db.add_all([art_mask, art_delta])
                db.add(Metric(scene_id=scene_id, name="change_precision", value=float(cd_out["precision"])) )  # type: ignore[index]
                db.add(Metric(scene_id=scene_id, name="change_recall", value=float(cd_out["recall"])) )  # type: ignore[index]
                db.add(Metric(scene_id=scene_id, name="change_f1", value=float(cd_out["f1"])) )  # type: ignore[index]
                if "drift" in cd_out:
                    db.add(Metric(scene_id=scene_id, name="change_drift", value=float(cd_out["drift"])) )  # type: ignore[index]
                db.commit()
                for a in (art_mask, art_delta):
                    db.refresh(a)
                    out["artifacts"].append(str(a.id))
                out["metrics"].update({
                    "change_precision": float(cd_out["precision"]),  # type: ignore[index]
                    "change_recall": float(cd_out["recall"]),      # type: ignore[index]
                    "change_f1": float(cd_out["f1"]),              # type: ignore[index]
                })
                if "drift" in cd_out:
                    out["metrics"]["change_drift"] = float(cd_out["drift"])  # type: ignore[index]
            dur = time.time() - _t0
            REQUEST_COUNT.labels(SERVICE_NAME, "PIPELINE", "change_detection", "200").inc()
            REQUEST_LATENCY.labels(SERVICE_NAME, "PIPELINE", "change_detection").observe(dur)
            out["metrics"]["change_detection_ms"] = round(dur * 1000.0, 2)
            try:
                mlflow_log_metrics({
                    "change_detection_ms": out["metrics"]["change_detection_ms"],
                    "change_precision": float(out["metrics"]["change_precision"]),
                    "change_recall": float(out["metrics"]["change_recall"]),
                    "change_f1": float(out["metrics"]["change_f1"]),
                    **({"change_drift": float(out["metrics"]["change_drift"])} if "change_drift" in out["metrics"] else {}),
                })
            except Exception:
                pass
            # Pass/fail gate
            try:
                out["metrics"]["change_detection_pass"] = float(out["metrics"].get("change_f1", 0.0) >= thr.get("change_f1_min", 0.70))
            except Exception:
                out["metrics"]["change_detection_pass"] = 0.0

        # Compute overall pass from step gates when available
        try:
            reg_pass = bool(int(out["metrics"].get("registration_pass", 0.0)))
            seg_pass = bool(int(out["metrics"].get("segmentation_pass", 0.0)))
            chg_pass = bool(int(out["metrics"].get("change_detection_pass", 0.0)))
            overall_pass = float(reg_pass and seg_pass and chg_pass)
            out["metrics"]["overall_pass"] = overall_pass
            # persist overall_pass metric
            db.add(Metric(scene_id=scene_id, name="overall_pass", value=float(overall_pass)))
            db.commit()
        except Exception:
            pass

        return out
    finally:
        db.close()


