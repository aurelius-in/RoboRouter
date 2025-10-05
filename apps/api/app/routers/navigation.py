from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException


router = APIRouter(tags=["Navigation"])


@router.get("/nav/map")
def build_map(scene_id: str, type: str = "occupancy") -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    if type not in ("occupancy", "esdf"):
        raise HTTPException(status_code=400, detail="Unsupported map type")
    # Stub response with minimal metadata; a real impl would generate rasters or grids
    return {"scene_id": scene_id, "type": type, "size": [256, 256], "resolution_m": 0.1}


@router.get("/nav/plan")
def plan_path(scene_id: str, start: str, goal: str, planner: str = "astar") -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    if planner not in ("astar", "teb"):
        raise HTTPException(status_code=400, detail="Unsupported planner")
    # Stub polyline path with two points
    return {"scene_id": scene_id, "planner": planner, "path": [[0, 0, 0], [1, 1, 0]], "cost": 1.414}

from __future__ import annotations

import json
import tempfile
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Artifact, AuditLog, Scene
from ..schemas import NavigationMapResponse, NavigationPlanRequest, NavigationPlanResponse
from ..storage.minio_client import get_minio_client, upload_file
from ..utils.tracing import span


router = APIRouter(tags=["Navigation"])


@router.get("/nav/map/{scene_id}", response_model=NavigationMapResponse)
def nav_map(scene_id: uuid.UUID) -> NavigationMapResponse:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        with span("nav.map.stub"):
            # Stub occupancy/ESDF summary
            metadata = {
                "grid": {"resolution_m": 0.25, "width": 128, "height": 128},
                "extents": {"xmin": 0.0, "ymin": 0.0, "xmax": 32.0, "ymax": 32.0},
                "esdf": {"min": 0.0, "max": 5.0, "mean": 1.2},
            }

            client = get_minio_client()
            with tempfile.TemporaryDirectory() as td:
                out_path = f"{td}/nav_map_{scene_id}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f)
                obj = f"nav/maps/{scene_id}.json"
                upload_file(client, "roborouter-processed", obj, out_path)

            uri = f"s3://roborouter-processed/{obj}"
            art = Artifact(scene_id=scene_id, type="nav_map", uri=uri)
            db.add(art)
            db.add(AuditLog(scene_id=scene_id, action="nav_map_generated", details=metadata))
            db.commit()
            db.refresh(art)

        return NavigationMapResponse(scene_id=scene_id, artifact_id=art.id, metadata=metadata)
    finally:
        db.close()


@router.post("/nav/plan", response_model=NavigationPlanResponse)
def nav_plan(payload: NavigationPlanRequest) -> NavigationPlanResponse:  # type: ignore[no-untyped-def]
    db: Session = SessionLocal()
    try:
        scene = db.get(Scene, payload.scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        # Ensure we have some input artifact
        has_source = db.execute(
            select(Artifact).where(Artifact.scene_id == payload.scene_id).limit(1)
        ).scalars().first()
        if not has_source:
            raise HTTPException(status_code=400, detail="No artifacts available for planning")

        with span("nav.plan.stub"):
            # Simple straight-line path with 5 waypoints
            x0, y0 = payload.start[0], payload.start[1]
            x1, y1 = payload.goal[0], payload.goal[1]
            waypoints: List[List[float]] = []
            for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                waypoints.append([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t])

            # Guardian checks (stubbed)
            slope_est = 5.0  # deg
            clearance_est = 0.5  # m
            uncertainty_est = 0.2  # unitless

            costs = {
                "length_m": ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5,
                "slope_deg": slope_est,
                "clearance_m": clearance_est,
                "uncertainty": uncertainty_est,
            }

            reasons: List[str] = []
            allowed = True
            if slope_est > 15.0:
                allowed = False
                reasons.append("slope exceeds threshold")
            if clearance_est < 0.2:
                allowed = False
                reasons.append("clearance below minimum")
            if uncertainty_est > 0.7:
                allowed = False
                reasons.append("uncertainty too high")

            db.add(AuditLog(scene_id=payload.scene_id, action="nav_plan", details={
                "start": payload.start,
                "goal": payload.goal,
                "allowed": allowed,
                "reasons": reasons,
                "costs": costs,
            }))
            db.commit()

        return NavigationPlanResponse(
            scene_id=payload.scene_id,
            route=waypoints,
            allowed=allowed,
            reasons=reasons,
            costs=costs,
        )
    finally:
        db.close()


