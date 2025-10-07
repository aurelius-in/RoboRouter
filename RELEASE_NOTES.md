# RoboRouter v0.1.0

## Highlights
- On‑prem multi‑agent 3D perception pipeline with explainable outputs
- Orchestration (stub/Ray/LangGraph), retriable steps, cancel/resume
- Ingest (PDAL autodetect, QA, S3/MinIO upload, reprojection checks)
- Registration (Open3D stubs) with residual overlays and gates
- Segmentation (KPConv/Minkowski scaffolding; CPU fallback) with overlays
- Change detection (voxel diff + learned stub) with class deltas and drift
- Policy/OPA gating with decision logging and versioned policy info
- Exporters: Potree(+ZIP+manifest/progress), LAZ, glTF (Draco/simplify), WebM
- UI (React/Vite): overlays, artifacts, runs, gates, exports, keyboard shortcuts
- Observability: Prometheus metrics; OpenTelemetry (HTTP exporter opt‑in)
- Storage: MinIO client with robust retries/backoff; presigned URL cache
- Reliability: resumable chunked uploads; lineage/audit with signatures
- Security: API key, quotas, optional OIDC + role/scene AuthZ for sensitive ops
- CI: Lint/type/test workflows and GPU CI (self‑hosted runner support)
- Docs: README with diagrams, ops runbook, policy cookbook, troubleshooting

## Breaking/Notes
- Some features are stubs/placeholders (e.g., true KPConv on GPU, full Ray/LangGraph graphs)
- PDAL/Open3D/ffmpeg presence toggles functionality; fallbacks provided
- OIDC and scene AuthZ are opt‑in via config; default is permissive for local dev

## Getting Started
- API: `docker compose up` (see infra/compose) and open `http://localhost:8000/health`
- UI: `http://localhost:5173` (Vite dev)
- Upload/ingest via UI or `POST /ingest`; run pipeline via `POST /pipeline/run`

## Thanks
- Initial release with end‑to‑end flow, strong test coverage, and GPU‑ready paths.
