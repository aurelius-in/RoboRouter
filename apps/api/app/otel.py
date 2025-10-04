from __future__ import annotations

import os
from typing import Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHTTPExporter  # type: ignore
        HAS_OTLP = True
    except Exception:
        HAS_OTLP = False
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
    otlp_url = os.getenv("ROBOROUTER_OTEL_OTLP_URL")
    if otlp_url and HAS_OTLP:
        try:
            exporter = OTLPHTTPExporter(endpoint=otlp_url)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


