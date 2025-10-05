from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import SessionLocal
from ..models import AuditLog, Scene

from ..policy.opa import evaluate_export_policy


router = APIRouter(tags=["Policy"])


@router.get("/policy/check")
def policy_check(type: str | None = None, export_type: str | None = None, crs: str | None = None, scene_id: str | None = None) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    t = export_type or type or ""
    c = crs or ""
    allowed, reason = evaluate_export_policy({"type": t, "crs": c})
    # Best-effort decision log
    if scene_id:
        db: Session = SessionLocal()
        try:
            try:
                sid = __import__("uuid").UUID(scene_id)
            except Exception:
                sid = None
            if sid is not None:
                db.add(AuditLog(scene_id=sid, action="policy_check", details={"type": t, "crs": c, "allowed": allowed, "reason": reason}))
                db.commit()
        finally:
            db.close()
    return {"allowed": allowed, "reason": reason}


@router.post("/policy/check")
def policy_check_post(payload: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    t = payload.get("export_type") or payload.get("type") or ""
    c = payload.get("crs") or ""
    allowed, reason = evaluate_export_policy({"type": t, "crs": c})
    # Best-effort decision log
    scene_id = payload.get("scene_id")
    if scene_id:
        db: Session = SessionLocal()
        try:
            try:
                sid = __import__("uuid").UUID(scene_id)
            except Exception:
                sid = None
            if sid is not None:
                db.add(AuditLog(scene_id=sid, action="policy_check", details={"type": t, "crs": c, "allowed": allowed, "reason": reason}))
                db.commit()
        finally:
            db.close()
    return {"allowed": allowed, "reason": reason}


