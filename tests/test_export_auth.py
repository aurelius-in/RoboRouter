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


def test_export_requires_api_key() -> None:
    r = client.post('/export?scene_id=00000000-0000-0000-0000-000000000000&type=gltf&crs=EPSG:3857')
    assert r.status_code == 401


