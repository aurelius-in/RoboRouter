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


def test_pipeline_run_missing_scene() -> None:
    r = client.post('/pipeline/run?scene_id=00000000-0000-0000-0000-000000000000', json={"steps": ["registration"]})
    assert r.status_code in (400, 404)


def test_export_gltf_with_draco_missing_scene() -> None:
    r = client.post('/export?scene_id=00000000-0000-0000-0000-000000000000&type=gltf&crs=EPSG:3857&draco=true')
    assert r.status_code in (400, 404)


