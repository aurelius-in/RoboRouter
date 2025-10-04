from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Scene, Artifact, Metric


router = APIRouter(tags=["Stats"])


@router.get("/stats")
def get_stats() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scenes = db.execute(select(func.count(Scene.id))).scalar() or 0
        artifacts = db.execute(select(func.count(Artifact.id))).scalar() or 0
        metrics = db.execute(select(func.count(Metric.id))).scalar() or 0
        exports = db.execute(
            select(func.count(Artifact.id)).where(Artifact.type.like("export_%"))
        ).scalar() or 0

        # Breakdown of exports by type
        rows = db.execute(
            select(Artifact.type, func.count(Artifact.id)).where(Artifact.type.like("export_%")).group_by(Artifact.type)
        ).all()
        exports_by_type = {str(t): int(c) for (t, c) in rows}
        # Compute pass/fail counts using latest overall_pass metric per scene if present
        latest_overall = (
            select(
                Metric.scene_id,
                Metric.value.label("val"),
                func.rank().over(partition_by=Metric.scene_id, order_by=Metric.created_at.desc()).label("rn"),
            )
            .where(Metric.name == "overall_pass")
            .subquery()
        )
        passed = db.execute(select(func.count()).select_from(latest_overall).where(latest_overall.c.rn == 1, latest_overall.c.val == 1.0)).scalar() or 0
        failed = db.execute(select(func.count()).select_from(latest_overall).where(latest_overall.c.rn == 1, latest_overall.c.val == 0.0)).scalar() or 0
        total_scenes = int(scenes)
        pass_rate = (float(passed) / float(passed + failed)) if (passed + failed) > 0 else 0.0
        return {
            "scenes": int(scenes),
            "artifacts": int(artifacts),
            "metrics": int(metrics),
            "exports": int(exports),
            "exports_by_type": exports_by_type,
            "passed": int(passed),
            "failed": int(failed),
            "pass_rate": pass_rate,
        }
    finally:
        db.close()


