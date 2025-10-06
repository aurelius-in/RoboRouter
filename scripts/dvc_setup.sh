#!/usr/bin/env bash
set -euo pipefail

if ! command -v dvc >/dev/null 2>&1; then
  echo "dvc not found. Install from https://dvc.org/doc/install and re-run."
  exit 1
fi

# Initialize DVC if needed
if [ ! -d .dvc ]; then
  dvc init -q
fi

# Configure a local remote (can be swapped to S3/MinIO later)
REMOTE_NAME=${1:-local}
REMOTE_URL=${2:-./.dvcstore}

mkdir -p "$REMOTE_URL"
dvc remote add -f "$REMOTE_NAME" "$REMOTE_URL"
dvc remote default "$REMOTE_NAME"

echo "DVC configured with remote '$REMOTE_NAME' at '$REMOTE_URL'"

