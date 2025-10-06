from __future__ import annotations

import tempfile
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact, AuditLog, Scene
from ..policy.opa import evaluate_export_policy, _load_policy
from ..deps import require_api_key
from ..utils.decision_log import write_decision
from ..utils.crs import validate_crs
from ..observability import EXPORT_COUNT, EXPORT_LATENCY, SERVICE_NAME
from ..exporters.exporters import export_potree, export_laz, export_gltf, export_webm
from ..storage.minio_client import get_minio_client, upload_file
from ..utils.sign import sign_dict


router = APIRouter(tags=["Export"], dependencies=[Depends(require_api_key)])


@router.post("/export")
def export_artifact(scene_id: uuid.UUID, type: str, crs: str = "EPSG:3857", draco: bool = False) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        if not validate_crs(crs):
            raise HTTPException(status_code=400, detail=f"Invalid or unsupported CRS: {crs}")

        allowed, reason = evaluate_export_policy({"type": type, "crs": crs, "rounding_mm": 5})
        _, _, policy_version = _load_policy()
        if not allowed:
            db.add(AuditLog(scene_id=scene_id, action="export_blocked", details={"type": type, "reason": reason, "policy_version": policy_version}))
            db.commit()
            try:
                write_decision("export_blocked", {"scene_id": str(scene_id), "type": type, "crs": crs, "reason": reason})
            except Exception:
                pass
            EXPORT_COUNT.labels(SERVICE_NAME, type, "blocked").inc()
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
            import time as _t
            _t0 = _t.time()
            # For now, simulate having a LAZ input by creating a tiny placeholder
            input_laz = f"{td}/input_{scene_id}.laz"
            with open(input_laz, "w", encoding="utf-8") as f:
                f.write("input placeholder\n")

            if type.lower() == "potree":
                out_dir = f"{td}/potree_{scene_id}"
                export_potree(input_laz, out_dir)
                obj_prefix = f"exports/potree/{scene_id}"
                index_local = f"{out_dir}/index.html"
                obj = f"{obj_prefix}/index.html"
                upload_file(client, "roborouter-processed", obj, index_local, content_type="text/html; charset=utf-8")
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "potree_zip":
                out_dir = f"{td}/potree_{scene_id}"
                export_potree(input_laz, out_dir)
                # Create a zip archive of the directory
                import shutil as _shutil
                zip_base = f"{td}/potree_{scene_id}"
                zip_path = _shutil.make_archive(zip_base, 'zip', out_dir)
                obj = f"exports/potree/{scene_id}.zip"
                upload_file(client, "roborouter-processed", obj, zip_path, content_type="application/zip")
                # Upload manifest alongside
                try:
                    manifest_obj = f"exports/potree/{scene_id}.manifest.json"
                    upload_file(client, "roborouter-processed", manifest_obj, f"{out_dir}/manifest.json", content_type="application/json")
                except Exception:
                    pass
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "laz":
                out_laz = f"{td}/{scene_id}.laz"
                export_laz(input_laz, out_laz)
                obj = f"exports/laz/{scene_id}.laz"
                upload_file(client, "roborouter-processed", obj, out_laz, content_type="application/octet-stream")
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "gltf":
                out_gltf = f"{td}/{scene_id}.gltf"
                export_gltf(input_laz, out_gltf, draco=bool(draco))
                obj = f"exports/gltf/{scene_id}.gltf"
                upload_file(client, "roborouter-processed", obj, out_gltf, content_type="model/gltf+json")
                uri = f"s3://roborouter-processed/{obj}"
            elif type.lower() == "webm":
                out_webm = f"{td}/{scene_id}.webm"
                export_webm(input_laz, out_webm)
                obj = f"exports/webm/{scene_id}.webm"
                upload_file(client, "roborouter-processed", obj, out_webm, content_type="video/webm")
                uri = f"s3://roborouter-processed/{obj}"
            else:
                raise HTTPException(status_code=400, detail="Unsupported export type")
        art = Artifact(scene_id=scene_id, type=f"export_{type}", uri=uri)
        db.add(art)
        # Include a policy "version" hint in audit to support decision provenance
        policy_ver = {"source": "config", "path": "OPA/inline", "version": policy_version}
        # Record export hash for traceability (best-effort)
        export_hash = None
        try:
            from ..utils.hash import sha256_file
            local_path = locals().get('out_laz') or locals().get('out_gltf') or locals().get('out_webm') or locals().get('index_local') or locals().get('zip_path')
            if local_path:
                export_hash = sha256_file(local_path)
        except Exception:
            export_hash = None
        details = {"type": type, "uri": uri, "crs": crs, "policy": policy_ver, **({"sha256": export_hash} if export_hash else {})}
        sig = sign_dict({"scene_id": str(scene_id), "type": type, "crs": crs})
        if sig:
            details["signature"] = sig
        db.add(AuditLog(scene_id=scene_id, action="export_allowed", details=details))
        try:
            write_decision("export_allowed", {"scene_id": str(scene_id), "type": type, "crs": crs, "uri": uri})
        except Exception:
            pass
        db.commit()
        EXPORT_COUNT.labels(SERVICE_NAME, type, "allowed").inc()
        try:
            EXPORT_LATENCY.labels(SERVICE_NAME, type).observe(_t.time() - _t0)
        except Exception:
            pass
        return {"scene_id": str(scene_id), "type": type, "uri": uri, "artifact_id": str(art.id)}
    finally:
        db.close()


