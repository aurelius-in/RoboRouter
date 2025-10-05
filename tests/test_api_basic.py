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


def test_health_ok() -> None:
    r = client.get('/health')
    assert r.status_code == 200
    body = r.json()
    assert body.get('status') == 'ok'
    assert 'deps' in body


def test_policy_check_has_version() -> None:
    r = client.get('/policy/check?type=potree&crs=EPSG:3857')
    assert r.status_code == 200
    body = r.json()
    assert 'allowed' in body and 'reason' in body
    # version may be None if no policy file; ensure key exists
    assert 'policy_version' in body


