from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

from .routers.ingest import router as ingest_router
from .routers.pipeline import router as pipeline_router
from .routers.artifacts import router as artifacts_router
from .routers.report import router as report_router
from .routers.export import router as export_router
from .routers.navigation import router as navigation_router
from .routers.scene import router as scene_router
from .observability import setup_metrics
from .otel import setup_otel
from .routers.stats import router as stats_router
from .routers.admin import router as admin_router
from .routers.config import router as config_router
from .routers.policy import router as policy_router
from .routers.auth import router as auth_router
from .routers.runs import router as runs_router
from .routers.models import router as models_router
from .routers.gates import router as gates_router
from .routers.upload import router as upload_router


app = FastAPI(
    title="RoboRouter API",
    version="0.1.0",
    description="On-prem, multi-agent 3D point-cloud perception and explainable autonomy API.",
    contact={"name": "RoboRouter", "url": "https://github.com/aurelius-in/RoboRouter"},
    license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
)
setup_otel("roborouter-api")

# Allow local Vite UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional API key protection for non-GET requests
@app.middleware("http")
async def api_key_guard(request, call_next):  # type: ignore[no-untyped-def]
    try:
        from fastapi import Request, Response
    except Exception:
        return await call_next(request)

    if settings.api_key and request.method not in ("GET", "OPTIONS"):
        key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
        if key != settings.api_key:
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)


# Simple in-memory rate limiter (best-effort, per-process)
_RL_BUCKET: dict[str, tuple[float, int]] = {}
_KEY_QUOTA: dict[str, tuple[float, int]] = {}


@app.middleware("http")
async def rate_limiter(request, call_next):  # type: ignore[no-untyped-def]
    import time as _t
    key = request.client.host if getattr(request, "client", None) else "anon"
    window = 60.0
    limit = max(1, int(settings.rate_limit_rpm))
    now = _t.time()
    ts, count = _RL_BUCKET.get(key, (now, 0))
    if now - ts > window:
        ts, count = now, 0
    count += 1
    _RL_BUCKET[key] = (ts, count)
    if count > limit:
        from fastapi.responses import JSONResponse

        resp = JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        retry_after = int(max(1, 60 - int(now - ts)))
        resp.headers["Retry-After"] = str(retry_after)
        return resp
    # Optional per-API-key quota
    try:
        if settings.quota_rpm_per_key and settings.api_key:
            k = request.headers.get("x-api-key") or request.headers.get("X-API-Key") or "anon"
            if k and k != "anon":
                ts2, c2 = _KEY_QUOTA.get(k, (now, 0))
                if now - ts2 > window:
                    ts2, c2 = now, 0
                c2 += 1
                _KEY_QUOTA[k] = (ts2, c2)
                if c2 > int(settings.quota_rpm_per_key):
                    from fastapi.responses import JSONResponse as _JR
                    r2 = _JR({"detail": "Quota exceeded for API key"}, status_code=429)
                    r2.headers["Retry-After"] = str(int(max(1, 60 - int(now - ts2))))
                    return r2
    except Exception:
        pass
    return await call_next(request)


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


def _get_pdal_info() -> Dict[str, Any]:
    try:
        result = subprocess.run(["pdal", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
        return {"available": True, "version": version}
    except Exception:
        return {"available": False, "version": None}


def _get_open3d_info() -> Dict[str, Any]:
    try:
        import open3d as o3d  # type: ignore

        return {"available": True, "version": getattr(o3d, "__version__", None)}
    except Exception:
        return {"available": False, "version": None}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "api",
        "gpu": _get_gpu_inventory(),
        "deps": {
            "pdal": _get_pdal_info(),
            "open3d": _get_open3d_info(),
        },
        "env": {
            "ROBOROUTER_PROFILE": os.getenv("ROBOROUTER_PROFILE", "default"),
        },
    }


@app.get("/meta")
def meta() -> Dict[str, Any]:
    return {
        "version": app.version,
        "name": app.title,
        "cors": settings.cors_origins,
        "api_key_required": settings.api_key is not None,
        "rate_limit_per_minute": settings.rate_limit_rpm,
        "presign_expires_seconds": settings.presign_expires_seconds,
        "orchestrator": getattr(settings, "orchestrator", "stub"),
        "orchestrator_max_retries": getattr(settings, "orchestrator_max_retries", 1),
        "perf": {
            "batching": getattr(settings, "perf_enable_batching", True),
            "seg_batch_points": getattr(settings, "perf_segmentation_batch_points", 5000),
            "change_tiles": getattr(settings, "perf_change_tiles", 8),
        },
    }


app.include_router(ingest_router)
app.include_router(pipeline_router)
app.include_router(artifacts_router)
app.include_router(report_router)
app.include_router(export_router)
app.include_router(navigation_router)
app.include_router(scene_router)
app.include_router(stats_router)
app.include_router(admin_router)
app.include_router(config_router)
app.include_router(policy_router)
app.include_router(auth_router)
app.include_router(runs_router)
app.include_router(models_router)
app.include_router(gates_router)
app.include_router(upload_router)

# Observability
setup_metrics(app)


