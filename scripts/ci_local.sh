#!/usr/bin/env bash
set -euo pipefail

# Local CI helper: lint, format check, types, tests

echo "== Ruff =="
ruff check apps/api

echo "== Black (check) =="
black --check apps/api

echo "== mypy =="
mypy apps/api

echo "== pytest =="
pytest -q --cov=apps/api --cov-fail-under=70
