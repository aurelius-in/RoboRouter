#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-airgap_bundle}
mkdir -p "$OUT"

# Save docker images (placeholder list)
IMAGES=( "roborouter-api:latest" )
for img in "${IMAGES[@]}"; do
  if docker image inspect "$img" >/dev/null 2>&1; then
    docker save "$img" -o "$OUT/${img//[:/]/_}.tar"
  fi
done

# Copy configs and scripts
cp -r configs "$OUT/configs"
cp -r scripts "$OUT/scripts"

echo "Airgap bundle prepared at $OUT"
