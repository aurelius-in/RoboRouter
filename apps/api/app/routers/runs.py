from __future__ import annotations

from typing import Any, Dict, List
from fastapi.responses import PlainTextResponse

from fastapi import APIRouter
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Scene, Metric


router = APIRouter(tags=["Runs"])


@router.get("/runs")
def list_runs(limit: int = 50, offset: int = 0, only_failed: bool = False, only_passed: bool = False) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scenes = db.execute(
            select(Scene).order_by(Scene.created_at.desc()).offset(offset).limit(limit)
        ).scalars().all()
        items: List[Dict[str, Any]] = []
        for s in scenes:
            metrics = db.execute(select(Metric).where(Metric.scene_id == s.id)).scalars().all()
            m = {mm.name: float(mm.value) for mm in metrics}
            reg_pass = bool(int(m.get("registration_pass", 0.0)))
            seg_pass = bool(int(m.get("segmentation_pass", 0.0)))
            chg_pass = bool(int(m.get("change_detection_pass", 0.0)))
            overall_pass = reg_pass and seg_pass and chg_pass
            if only_failed and overall_pass:
                continue
            if only_passed and not overall_pass:
                continue
            items.append(
                {
                    "id": str(s.id),
                    "created_at": s.created_at.isoformat(),
                    "rmse": m.get("rmse"),
                    "miou": m.get("miou"),
                    "change_f1": m.get("change_f1"),
                    "change_drift": m.get("change_drift"),
                    "registration_pass": reg_pass,
                    "segmentation_pass": seg_pass,
                    "change_detection_pass": chg_pass,
                    "overall_pass": overall_pass,
                }
            )
        total = db.execute(select(func.count(Scene.id))).scalar() or 0
        return {"items": items, "offset": offset, "limit": limit, "total": int(total)}
    finally:
        db.close()


@router.get("/runs/csv", response_class=PlainTextResponse)
def runs_csv(limit: int = 1000, offset: int = 0, only_failed: bool = False, only_passed: bool = False) -> str:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scenes = db.execute(
            select(Scene).order_by(Scene.created_at.desc()).offset(offset).limit(min(5000, max(1, limit)))
        ).scalars().all()
        rows = ["id,created_at,overall_pass,rmse,miou,change_f1,change_drift"]
        for s in scenes:
            metrics = db.execute(select(Metric).where(Metric.scene_id == s.id)).scalars().all()
            m = {mm.name: float(mm.value) for mm in metrics}
            reg_pass = bool(int(m.get("registration_pass", 0.0)))
            seg_pass = bool(int(m.get("segmentation_pass", 0.0)))
            chg_pass = bool(int(m.get("change_detection_pass", 0.0)))
            overall_pass = reg_pass and seg_pass and chg_pass
            if only_failed and overall_pass:
                continue
            if only_passed and not overall_pass:
                continue
            rows.append(
                f"{s.id},{s.created_at.isoformat()},{int(overall_pass)},{m.get('rmse','')},{m.get('miou','')},{m.get('change_f1','')},{m.get('change_drift','')}"
            )
        return "\n".join(rows) + "\n"
    finally:
        db.close()


