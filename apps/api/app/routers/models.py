from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter


router = APIRouter(tags=["Models"])


@router.get("/models")
def list_models() -> Dict[str, List[Dict[str, Any]]]:  # type: ignore[no-untyped-def]
    return {
        "segmentation": [
            {"name": "kpconv_baseline", "device": "cpu", "status": "available"},
            {"name": "minkowski_kpconv", "device": "cuda", "status": "unavailable"},
        ],
        "registration": [
            {"name": "open3d_fgr_icp", "device": "cpu", "status": "available"},
        ],
        "change_detection": [
            {"name": "voxel_diff_stub", "device": "cpu", "status": "available"},
        ],
        "exporters": [
            {"name": "potree", "device": "cpu", "status": "available"},
            {"name": "laz", "device": "cpu", "status": "available"},
            {"name": "gltf", "device": "cpu", "status": "available"},
            {"name": "webm", "device": "cpu", "status": "available"},
        ],
    }


