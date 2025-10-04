from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List

from fastapi import FastAPI

from .routers.ingest import router as ingest_router
from .routers.pipeline import router as pipeline_router
from .routers.artifacts import router as artifacts_router
from .routers.report import router as report_router


app = FastAPI(title="RoboRouter API", version="0.1.0")


def _get_gpu_inventory() -> List[Dict[str, Any]]:
    try:
        # Prefer nvidia-smi if available; avoid outbound calls.
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        gpus: List[Dict[str, Any]] = []
        for line in result.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                gpus.append({"name": parts[0], "memory_total": parts[1]})
        return gpus
    except Exception:
        return []


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "api",
        "gpu": _get_gpu_inventory(),
        "env": {
            "ROBOROUTER_PROFILE": os.getenv("ROBOROUTER_PROFILE", "default"),
        },
    }


app.include_router(ingest_router)
app.include_router(pipeline_router)
app.include_router(artifacts_router)
app.include_router(report_router)


