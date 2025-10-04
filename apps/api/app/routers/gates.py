from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Scene, Metric
from ..utils.thresholds import load_thresholds


router = APIRouter(tags=["Gates"])


@router.get("/gates")
def golden_gates(scene_id: uuid.UUID) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        # Load thresholds
        th = load_thresholds()
        rmse_max = float(th.get("rmse_max", 0.10))
        miou_min = float(th.get("miou_min", 0.70))
        f1_min = float(th.get("change_f1_min", 0.70))

        # Get latest metrics per key
        rows = db.execute(
            select(Metric).where(Metric.scene_id == scene_id).order_by(Metric.created_at.desc())
        ).scalars().all()
        latest: Dict[str, float] = {}
        for m in rows:
            if m.name not in latest:
                latest[m.name] = float(m.value)

        rmse = latest.get("rmse")
        miou = latest.get("miou")
        change_f1 = latest.get("change_f1")

        registration_pass = rmse is not None and rmse <= rmse_max
        segmentation_pass = miou is not None and miou >= miou_min
        change_pass = change_f1 is not None and change_f1 >= f1_min
        overall_pass = bool(registration_pass and segmentation_pass and change_pass)

        return {
            "scene_id": str(scene_id),
            "thresholds": {"rmse_max": rmse_max, "miou_min": miou_min, "change_f1_min": f1_min},
            "metrics": {"rmse": rmse, "miou": miou, "change_f1": change_f1},
            "registration_pass": registration_pass,
            "segmentation_pass": segmentation_pass,
            "change_pass": change_pass,
            "overall_pass": overall_pass,
        }
    finally:
        db.close()


