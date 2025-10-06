#!/usr/bin/env bash
set -euo pipefail

if ! command -v syft >/dev/null 2>&1; then
  echo "syft not found; install from https://github.com/anchore/syft"
  exit 1
fi

syft packages dir:. -o cyclonedx-json > sbom.cdx.json
echo "SBOM written to sbom.cdx.json"
