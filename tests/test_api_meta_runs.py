from __future__ import annotations

import os
import sys


def _ensure_path() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_path()

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.app.main import app  # type: ignore  # noqa: E402


client = TestClient(app)


def test_meta_contains_orchestrator() -> None:
    r = client.get('/meta')
    assert r.status_code == 200
    body = r.json()
    assert 'orchestrator' in body
    assert 'orchestrator_max_retries' in body


def test_runs_endpoint_ok() -> None:
    r = client.get('/runs')
    assert r.status_code == 200
    body = r.json()
    assert 'items' in body and isinstance(body['items'], list)


