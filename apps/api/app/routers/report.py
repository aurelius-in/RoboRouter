from __future__ import annotations

import tempfile
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Base, SessionLocal, engine
from ..models import Artifact, AuditLog, Metric, Scene
from ..report.builder import build_html_report, html_to_pdf
from ..report.why import top_reasons
from ..storage.minio_client import get_minio_client, upload_file
from ..utils.sign import sign_dict


router = APIRouter()


@router.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@router.post("/report/generate")
def generate_report(scene_id: uuid.UUID) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        # Collect metrics
        metric_rows = db.execute(select(Metric).where(Metric.scene_id == scene_id)).scalars().all()
        metrics = {m.name: m.value for m in metric_rows}

        # Collect overlays (pick latest per type)
        overlay_types = [
            "residuals",
            "segmentation_classes",
            "segmentation_confidence",
            "segmentation_entropy",
            "change_mask",
            "change_delta",
        ]
        overlays: Dict[str, str] = {}
        for t in overlay_types:
            row = db.execute(
                select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == t).order_by(Artifact.created_at.desc())
            ).scalars().first()
            if row:
                overlays[t] = row.uri

        # Build HTML
        params = {"scene": str(scene_id)}
        html = build_html_report(str(scene_id), metrics, overlays, params)

        # PDF
        client = get_minio_client()
        with tempfile.TemporaryDirectory() as td:
            html_path = f"{td}/report_{scene_id}.html"
            pdf_path = f"{td}/report_{scene_id}.pdf"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            html_ok = True
            pdf_ok = html_to_pdf(html, pdf_path)

            # Upload
            html_obj = f"reports/{scene_id}.html"
            pdf_obj = f"reports/{scene_id}.pdf"
            if html_ok:
                upload_file(client, "roborouter-processed", html_obj, html_path)
            if pdf_ok:
                upload_file(client, "roborouter-processed", pdf_obj, pdf_path)

        # Persist artifacts and audit
        if html_ok:
            db.add(Artifact(scene_id=scene_id, type="report_html", uri=f"s3://roborouter-processed/{html_obj}"))
        if pdf_ok:
            db.add(Artifact(scene_id=scene_id, type="report_pdf", uri=f"s3://roborouter-processed/{pdf_obj}"))
        details = {"metrics": metrics, "overlays": list(overlays.keys())}
        sig = sign_dict({"scene_id": str(scene_id), **{k: str(v) for k, v in metrics.items()}})
        if sig:
            details["signature"] = sig
        db.add(AuditLog(scene_id=scene_id, action="report_generated", details=details))
        db.commit()

        return {
            "scene_id": str(scene_id),
            "html": f"s3://roborouter-processed/{html_obj}" if html_ok else None,
            "pdf": f"s3://roborouter-processed/{pdf_obj}" if pdf_ok else None,
            "reasons": top_reasons(metrics),
        }
    finally:
        db.close()


