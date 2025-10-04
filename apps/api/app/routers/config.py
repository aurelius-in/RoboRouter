from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..config import settings
from ..utils.thresholds import load_thresholds
from ..utils.crs import allowed_crs


router = APIRouter(tags=["Config"])


@router.get("/config")
def get_config() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    return {
        "thresholds": load_thresholds(),
        "allowed_crs": sorted(list(allowed_crs())),
        "presign_expires_seconds": settings.presign_expires_seconds,
        "cors_origins": settings.cors_origins,
        "rate_limit_rpm": settings.rate_limit_rpm,
        "retention_days": settings.retention_days,
    }


