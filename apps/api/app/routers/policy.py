from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..policy.opa import evaluate_export_policy


router = APIRouter(tags=["Policy"])


@router.get("/policy/check")
def policy_check(type: str, crs: str) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    allowed, reason = evaluate_export_policy({"type": type, "crs": crs})
    return {"allowed": allowed, "reason": reason}


