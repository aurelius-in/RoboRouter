from __future__ import annotations

import os
from typing import Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    HAS_OTEL = True
except Exception:  # pragma: no cover
    HAS_OTEL = False


def setup_otel(service_name: str = "roborouter-api") -> None:
    if not HAS_OTEL:
        return
    if os.getenv("ROBOROUTER_OTEL_ENABLED", "false").lower() != "true":
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    # Console exporter by default (air-gapped friendly). Users can swap to OTLP via env.
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


