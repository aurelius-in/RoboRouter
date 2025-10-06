# RoboRouter Operations Runbook (Stub)

## Overview
- Components: API, MinIO, Postgres, UI
- Optional deps: PDAL, Open3D, Ray, Grafana/Prometheus

## Common Tasks
- Ingest: POST /ingest
- Pipeline: POST /pipeline/run?scene_id=...
- Exports: POST /export (potree, potree_zip, gltf, laz, webm)

## Cleanup
- Admin cleanup: POST /admin/cleanup (requires API key and X-Role: admin)

## Observability
- Metrics: GET /metrics (Prometheus)
- Tracing: set ROBOROUTER_OTEL_ENABLED=true and ROBOROUTER_OTEL_OTLP_URL

## Troubleshooting
- Check /health for PDAL/Open3D availability
- Review /runs, /stats, and /gates for outcomes
