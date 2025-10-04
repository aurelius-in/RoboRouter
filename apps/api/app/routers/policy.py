from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..policy.opa import evaluate_export_policy


router = APIRouter(tags=["Policy"])


@router.get("/policy/check")
def policy_check(type: str | None = None, export_type: str | None = None, crs: str | None = None) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    t = export_type or type or ""
    c = crs or ""
    allowed, reason = evaluate_export_policy({"type": t, "crs": c})
    return {"allowed": allowed, "reason": reason}


@router.post("/policy/check")
def policy_check_post(payload: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    t = payload.get("export_type") or payload.get("type") or ""
    c = payload.get("crs") or ""
    allowed, reason = evaluate_export_policy({"type": t, "crs": c})
    return {"allowed": allowed, "reason": reason}


