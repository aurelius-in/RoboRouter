from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, CollectorRegistry, generate_latest
from starlette.responses import Response


import os

SERVICE_NAME = os.getenv("ROBOROUTER_SERVICE", "api")

REQUEST_COUNT = Counter(
    "roborouter_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "roborouter_request_latency_seconds",
    "Request latency in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def setup_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):  # type: ignore[no-untyped-def]
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        path = request.url.path
        REQUEST_COUNT.labels(SERVICE_NAME, request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(SERVICE_NAME, request.method, path).observe(duration)
        return response

    @app.get("/metrics")
    def metrics() -> Response:  # type: ignore[override]
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)


