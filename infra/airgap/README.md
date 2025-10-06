# Air-Gapped Installation (Stub)

## Overview
This guide outlines a high-level flow to install RoboRouter in an air-gapped environment.

## Steps
1. Fetch container images on a connected host and save as tar archives.
2. Mirror Python wheels and NPM packages to a local registry or file store.
3. Transfer artifacts via removable media.
4. Load images on the target and run `docker compose` (use `infra/compose`).
5. Configure `ROBOROUTER_OTEL_ENABLED=false` and disable external exporters.

## Notes
- Ensure `configs/opa/policy.yaml` is present locally.
- Use `scripts/sbom.sh` to generate SBOMs for compliance.
- Prefer local MinIO for artifacts and Postgres for metadata.
