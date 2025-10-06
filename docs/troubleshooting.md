# Troubleshooting

## Common Issues

- PDAL missing: Install PDAL or run the provided Docker stack; ingest will fallback to stubs.
- Open3D missing: Registration uses stubs if Open3D is unavailable.
- 403 on export: Policy likely blocked the request; check `/policy/check` and `configs/opa/policy.yaml`.
- 429 rate limit: Respect `Retry-After` header; adjust `ROBOROUTER_RATE_LIMIT_RPM`.
- Presigned URL expired: Call `/artifacts/refresh/{artifact_id}` and retry.

## Logs & Tracing

- Decisions: `_decision_log.jsonl` contains policy decisions.
- Traces: enable with `ROBOROUTER_OTEL_ENABLED=true` and set `ROBOROUTER_OTEL_OTLP_URL`.

## Storage

- MinIO credentials: `ROBOROUTER_MINIO_*` env vars must match docker-compose settings.
- Retries: Uploads/downloads have built-in retries/backoff; see `apps/api/app/storage/minio_client.py`.
