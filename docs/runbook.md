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
- DVC: run `scripts/dvc_setup.sh` to initialize a local remote for datasets and models.

## Observability
- Metrics: GET /metrics (Prometheus)
- Tracing: set ROBOROUTER_OTEL_ENABLED=true and ROBOROUTER_OTEL_OTLP_URL

## Security
- Per-key quotas: configure `ROBOROUTER_QUOTA_RPM_PER_KEY`.
- OIDC: set `ROBOROUTER_OIDC_ENABLED=true` and issuer/client settings; use `Authorization: Bearer <token>`.

## Backups
- MinIO: use `mc mirror` to back up buckets `roborouter-processed` and `roborouter-raw`.
- Postgres: `pg_dump` of the `roborouter` database.

## Troubleshooting
- Check /health for PDAL/Open3D availability
- Review /runs, /stats, and /gates for outcomes
